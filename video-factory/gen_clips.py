#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""关键帧 → I2V 素材：上传首帧 + 提交 H3 任务 + 轮询 + 下载（可并行、可断点续跑）"""
import json, os, subprocess, sys, time, urllib.request, shutil

BUILD = '/workspace/build'
KF = f'{BUILD}/kf'
MODEL = os.environ.get('VID_MODEL', 'MiniMax-H3-Max')
RES = os.environ.get('VID_RES', '768P')
DUR = int(os.environ.get('VID_DUR', '13'))
DEST = f'{BUILD}/clips/{MODEL}_{RES}'
os.makedirs(DEST, exist_ok=True)

MOTION = {
    'dc_corridor': "Slow cinematic dolly push forward down the corridor, camera glides forward with medium amplitude at a very slow speed, server indicator LEDs blink and shimmer, cold haze drifts slowly through the ceiling light beams, reflections slide across the polished floor. Single continuous shot, no cuts, no camera shake.",
    'city_phone': "Slow cinematic push in toward the glowing phone screen with medium amplitude at a slow speed, the hand stays steady, city lights bokeh slowly shift, warm lens flare drifts across the frame. Single continuous shot, no cuts.",
    'cloud_particles': "Particles stream and swirl slowly, converging into a slowly rotating luminous cloud form, fine light trails drift across the frame, gentle pulsing glow. Camera drifts forward with small amplitude at a slow speed. Single continuous shot, no cuts.",
    'rack_wall': "Slow cinematic dolly forward along the server rack wall with medium amplitude at a slow speed, hundreds of status LEDs blink in waves, haze rolls softly through the aisle. Single continuous shot, no cuts.",
    'virtualization': "The central monolithic block slowly splits apart into many smaller luminous blocks that drift outward and hover, thin energy lines stretch and reconnect between them. Camera pushes in with medium amplitude at a slow speed. Single continuous shot, no cuts.",
    'containers': "The grid of glowing blocks slowly rearranges itself, blocks slide into new positions with staggered motion, cyan edges pulse in sequence across the floor. Camera glides forward with medium amplitude at a slow speed. Single continuous shot, no cuts.",
    'elasticity': "A soft gradient of warm light slowly travels from the dim side toward the lit side, the illuminated racks brighten progressively one by one, haze drifts. Camera tracks right with medium amplitude at a slow speed. Single continuous shot, no cuts.",
    'earth_nodes': "Earth rotates very slowly, glowing node arcs pulse and travel along the connections, atmospheric rim light shimmers. Camera drifts forward with small amplitude at a very slow speed. Single continuous shot, no cuts.",
    'dawn_server': "Warm golden sunrise light slowly floods through the glass wall, light beams sweep across the server racks, dust motes drift slowly in the beams, lens flare blooms gently. Camera pushes in with medium amplitude at a slow speed. Single continuous shot, no cuts.",
}
AUDIO = " Ambient room tone only, subtle machinery hum, no speech, no voice, no human sound, no music, no lyrics."


def sh(cmd, timeout=300):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
    if r.returncode != 0:
        raise RuntimeError(f'CMD FAIL: {cmd[:140]}\n{r.stderr[-800:]}')
    return r.stdout


def upload(path):
    out = sh(f'mcode-tools upload_temp_url "{path}"')
    d = json.loads(out)
    return d.get('temp_url') or d.get('url') or d.get('data', {}).get('temp_url')


def submit(name, url):
    args = {'model': MODEL, 'prompt': MOTION[name] + AUDIO, 'duration': DUR,
            'resolution': RES, 'reference_type': 'first_frame', 'input_image': {'url': url}}
    out = sh(f'mcode-tools connector call connector__matrix__submit_video_generation --args {json.dumps(json.dumps(args, ensure_ascii=False))}')
    return json.loads(out)


def query(task_id):
    out = sh(f'mcode-tools connector call connector__matrix__query_video_generation --args {json.dumps(json.dumps({"task_id": task_id, "model": MODEL}))}')
    return json.loads(out)


def download(url, dest):
    for a in range(4):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=300) as r, open(dest, 'wb') as f:
                shutil.copyfileobj(r, f, 1024*256)
            return os.path.getsize(dest)
        except Exception as e:
            print('   dl retry', a, e, flush=True); time.sleep(4)
    raise RuntimeError('download fail')


def main():
    names = sys.argv[1:] or list(MOTION.keys())
    state_p = f'{BUILD}/vid_state_{MODEL}_{RES}.json'
    state = json.load(open(state_p)) if os.path.exists(state_p) else {}
    for name in names:
        dest = f'{DEST}/{name}.mp4'
        if os.path.exists(dest) and os.path.getsize(dest) > 100000:
            print(f'[skip] {name}', flush=True); continue
        if name in state and state[name].get('done'):
            print(f'[done-state] {name}', flush=True); continue
        try:
            url = upload(f'{KF}/{name}.png')
        except Exception as e:
            print(f'[upload-fail] {name}: {e}', flush=True); continue
        try:
            r = submit(name, url)
        except Exception as e:
            print(f'[submit-fail] {name}: {e}', flush=True); continue
        tid = r.get('task_id') or r.get('data', {}).get('task_id')
        print(f'[submitted] {name} task={tid} status={r.get("status")}', flush=True)
        if not tid:
            print('   raw:', json.dumps(r, ensure_ascii=False)[:400], flush=True); continue
        state[name] = {'task_id': tid, 'model': MODEL, 'res': RES, 'dur': DUR, 'done': False}
        json.dump(state, open(state_p, 'w'), indent=1)
        for attempt in range(120):
            time.sleep(15)
            try:
                q = query(tid)
            except Exception as e:
                print(f'  [poll-err] {e}', flush=True); continue
            st = (q.get('status') or '').lower()
            if st in ('succeeded', 'success', 'completed'):
                vu = q.get('video_url')
                if vu:
                    sz = download(vu, dest)
                    state[name]['done'] = True
                    json.dump(state, open(state_p, 'w'), indent=1)
                    print(f'[done] {name} -> {dest} {sz//1024}KB', flush=True)
                break
            elif st in ('failed', 'error', 'cancelled'):
                print(f'[failed] {name}: {json.dumps(q, ensure_ascii=False)[:300]}', flush=True)
                break
            else:
                if attempt % 4 == 0:
                    print(f'  {name} status={st} attempt={attempt}', flush=True)


if __name__ == '__main__':
    main()
