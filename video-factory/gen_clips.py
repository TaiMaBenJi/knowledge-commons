#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""关键帧 → I2V 素材：上传首帧 + 提交 H3 任务 + 轮询 + 下载（可并行、可断点续跑）"""
import json, os, subprocess, sys, time, urllib.request, urllib.parse, ipaddress, socket
from pathlib import Path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vf_safe import sh, under

BUILD = '/workspace/build'
KF = under(BUILD, 'kf')
MODEL = os.environ.get('VID_MODEL', 'MiniMax-H3-Max')
RES = os.environ.get('VID_RES', '768P')
DUR = int(os.environ.get('VID_DUR', '13'))
DEST = under(BUILD, 'clips', f'{MODEL}_{RES}')
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


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """禁止跟随重定向——防服务端 30x 跳到内网/云元数据地址。"""
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


_OPENER = urllib.request.build_opener(_NoRedirect)


_BLOCKED_NETS = tuple(
    ipaddress.ip_network(n) for n in (
        '0.0.0.0/8', '10.0.0.0/8', '100.64.0.0/10', '127.0.0.0/8',
        '169.254.0.0/16', '172.16.0.0/12', '192.168.0.0/16', '224.0.0.0/4',
        '::/128', '::1/128', 'fc00::/7', 'fe80::/10', 'ff00::/8'))


def _is_blocked_ip(hip):
    """显式私网/环回/链路本地/CGNAT/组播黑名单——不用 is_private，
    因为它把 198.18.0.0/15（RFC2544 基准段，代理 fake-IP 常用）也当内网，会误杀正常下载。"""
    nets = [n for n in _BLOCKED_NETS if n.version == hip.version]
    return any(hip in n for n in nets)


def _safe_url(url):
    """SSRF 三重校验：https 协议 + 主机黑名单 + 解析后 IP 私网/环回/链路本地边界。"""
    u = urllib.parse.urlparse(str(url))
    if u.scheme != 'https':
        raise ValueError('只允许 https 下载：%s' % url)
    host = (u.hostname or '').lower()
    if not host or host == 'localhost' or host.endswith(('.local', '.internal')):
        raise ValueError('禁止环回/内网主机：%s' % host)
    try:
        literal = ipaddress.ip_address(host)
    except ValueError:
        literal = None
        # 域名：解析出的每个地址都要过黑名单校验（防 DNS 指向内网）
        for info in socket.getaddrinfo(host, None):
            hip = ipaddress.ip_address(info[4][0])
            if _is_blocked_ip(hip):
                raise ValueError('域名解析到内网地址：%s -> %s' % (host, hip))
    if literal is not None and _is_blocked_ip(literal):
        raise ValueError('禁止内网地址下载：%s' % host)
    return url


def upload(path):
    out = sh(['mcode-tools', 'upload_temp_url', path], timeout=300)
    d = json.loads(out)
    return d.get('temp_url') or d.get('url') or d.get('data', {}).get('temp_url')


def submit(name, url):
    args = {'model': MODEL, 'prompt': MOTION[name] + AUDIO, 'duration': DUR,
            'resolution': RES, 'reference_type': 'first_frame', 'input_image': {'url': url}}
    out = sh(['mcode-tools', 'connector', 'call',
              'connector__matrix__submit_video_generation',
              '--args', json.dumps(args, ensure_ascii=False)], timeout=300)
    return json.loads(out)


def query(task_id):
    out = sh(['mcode-tools', 'connector', 'call',
              'connector__matrix__query_video_generation',
              '--args', json.dumps({"task_id": task_id, "model": MODEL})], timeout=300)
    return json.loads(out)


def download(url, dest):
    """下载生成结果：_safe_url 三重校验 + 禁重定向，产物写入已收容的 dest。"""
    safe = _safe_url(url)
    for a in range(4):
        try:
            req = urllib.request.Request(safe, headers={'User-Agent': 'Mozilla/5.0'})
            with _OPENER.open(req, timeout=300) as r:
                data = r.read()
            Path(dest).write_bytes(data)
            return len(data)
        except Exception as e:
            print('   dl retry', a, e, flush=True); time.sleep(4)
    raise RuntimeError('download fail')


def main():
    names = sys.argv[1:] or list(MOTION.keys())
    state_p = under(BUILD, f'vid_state_{MODEL}_{RES}.json')
    state = json.loads(Path(state_p).read_text(encoding='utf-8')) if os.path.exists(state_p) else {}

    def save_state():
        Path(state_p).write_text(json.dumps(state, indent=1), encoding='utf-8')

    for name in names:
        dest = under(DEST, f'{name}.mp4')
        if os.path.exists(dest) and os.path.getsize(dest) > 100000:
            print(f'[skip] {name}', flush=True); continue
        if name in state and state[name].get('done'):
            print(f'[done-state] {name}', flush=True); continue
        try:
            url = upload(under(KF, f'{name}.png'))
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
        save_state()
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
                    save_state()
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
