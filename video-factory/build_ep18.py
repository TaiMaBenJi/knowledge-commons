#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第 18 集《云计算从零到精通》成片装配

流程：渲染帧 → 分镜视频段（zoompan 运镜 + 电影感调色）→ 旁白对轨 →
      配乐/音效混合 → 字幕烧录 → 响度归一 → 成片
"""
import os, sys, json, subprocess, importlib.util, math, shutil, time

BUILD = '/workspace/build'
FR = f'{BUILD}/frames'
SEG = f'{BUILD}/seg'
AU = f'{BUILD}/audio'
SU = f'{BUILD}/subs'
OUT = f'{BUILD}/out'
for d in (FR, SEG, AU, SU, OUT):
    os.makedirs(d, exist_ok=True)

FPS = 10
W, H = 1920, 1080
PAD = 0.55          # 每段旁白后静音留白
LEAD = 0.0          # 片头留白

spec = importlib.util.spec_from_file_location("ep18", f'{BUILD}/scripts/course-t18.py')
_m = importlib.util.module_from_spec(spec); spec.loader.exec_module(_m)
EP = _m.EPISODE
SLIDES = EP['slides']
TOTAL = len(SLIDES)

sys.path.insert(0, BUILD)
import render as R
import render_ext  # noqa: F401  注册 ladder / clip 版式


def sh(cmd, timeout=1200):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
    if r.returncode != 0:
        raise RuntimeError(f'CMD FAIL: {cmd[:200]}\n{r.stderr[-1500:]}')
    return r.stdout


def dur_of(p):
    out = subprocess.run(['ffprobe', '-v', 'quiet', '-show_entries', 'format=duration',
                          '-of', 'csv=p=0', p], capture_output=True, text=True)
    try:
        return float(out.stdout.strip())
    except Exception:
        return 0.0


# ---------------------------------------------------------------- 1. 渲染帧
def render_frames():
    R.SERIES = EP['series']
    meta_base = {'ep_no': EP.get('disp', EP['id']), 'ep_title': EP['title'], 'total': TOTAL}
    for i, s in enumerate(SLIDES):
        fp = f'{FR}/slide_{i:02d}.png'
        if os.path.exists(fp):
            continue
        img = R.render_slide(s, dict(meta_base, page=i))
        img.save(fp)
        print(f'[frame] {i+1}/{TOTAL} {s["type"]}', flush=True)


# ---------------------------------------------------------------- 2. 分镜时长
def compute_timeline():
    rows = json.load(open(f'{AU}/timing.json'))
    tl = []
    t = LEAD
    for i, s in enumerate(SLIDES):
        nd = rows[i]['dur']
        # 镜头/封面/金句/结尾多给一点呼吸
        extra = 0.0
        if s['type'] == 'cover':
            extra = 0.9
        elif s['type'] == 'clip':
            extra = 0.5
        elif s['type'] == 'note':
            extra = 1.2
        elif s['type'] == 'end':
            extra = 1.2
        d = nd + PAD + extra
        tl.append({'i': i, 'type': s['type'], 'clip': s.get('clip'), 'nar': nd,
                   'dur': round(d, 3), 'start': round(t, 3), 'text': s.get('narration', '')})
        t += d
    json.dump(tl, open(f'{AU}/timeline.json', 'w'), ensure_ascii=False, indent=1)
    return tl


# ---------------------------------------------------------------- 3. 分镜视频段
GRADE = ("curves=all='0/0 0.5/0.5 1/1',eq=saturation=0.94:contrast=1.045:brightness=-0.012,"
         "unsharp=5:5:0.4,noise=alls=4:allf=u,vignette=PI/4.6")


def motion_for(i, s, nframes):
    """每个镜头的运镜：类型 + 幅度 + 速度，方向错开，不重复。
    zoompan 没有 N 变量，这里把总帧数直接写进表达式。"""
    k = i % 4
    N = max(1, nframes)
    # 放大倍率 1.0 -> 1.085 左右；x/y 缓慢位移
    if k == 0:      # 推近
        z = f"1+0.085*on/{N}"
        x = "iw/2-(iw/zoom/2)"
        y = "ih/2-(ih/zoom/2)"
    elif k == 1:    # 缓拉 + 轻微右移
        z = f"1.085-0.075*on/{N}"
        x = f"iw/2-(iw/zoom/2)+(on/{N})*26"
        y = "ih/2-(ih/zoom/2)"
    elif k == 2:    # 横移
        z = f"1+0.06*on/{N}"
        x = f"iw/2-(iw/zoom/2)+(on/{N}-0.5)*44"
        y = "ih/2-(ih/zoom/2)"
    else:           # 斜向推
        z = f"1+0.07*on/{N}"
        x = f"iw/2-(iw/zoom/2)+(on/{N})*18"
        y = f"ih/2-(ih/zoom/2)+(on/{N})*12"
    return (f"zoompan=z='{z}':x='{x}':y='{y}':d=1:s={W}x{H}:fps={FPS},"
            f"crop=iw-2:ih-2:(iw-ow)/2+sin(t/2.3)*3:(ih-oh)/2+cos(t/3.1)*3,"
            f"scale={W}:{H},"
            f"{GRADE},format=yuv420p")


def build_segments(tl):
    for row in tl:
        i = row['i']
        outp = f'{SEG}/seg_{i:02d}.mp4'
        if os.path.exists(outp) and abs(dur_of(outp) - row['dur']) < 0.6:
            print(f'[seg skip] {i:02d}'); continue
        src = f'{FR}/slide_{i:02d}.png'
        nframes = int(round(row['dur'] * FPS))
        vf = motion_for(i, SLIDES[i], nframes)
        cmd = (f"ffmpeg -y -v error -loop 1 -framerate {FPS} -i \"{src}\" -frames:v {nframes} "
               f"-vf \"{vf}\" -c:v libx264 -preset veryfast -tune stillimage -crf 20 "
               f"-pix_fmt yuv420p -r {FPS} \"{outp}\"")
        sh(cmd)
        print(f'[seg] {i:02d} {row["type"]:8s} {row["dur"]:6.2f}s -> {os.path.getsize(outp)//1024}KB', flush=True)


# ---------------------------------------------------------------- 4. 旁白总轨
def build_narration(tl):
    """每段旁白先转 PCM 并补足到该段总长，再统一 concat（同一编码才能拼）"""
    for row in tl:
        i = row['i']
        seg = f"{AU}/nseg_{i:02d}.wav"
        if os.path.exists(seg) and abs(dur_of(seg) - row['dur']) < 0.15:
            continue
        src = f"{AU}/s{i:02d}.mp3"
        tgt = row['dur']
        sh(f'ffmpeg -y -v error -i "{src}" -af "aresample=44100,apad=pad_dur=4" '
           f'-t {tgt:.3f} -c:a pcm_s16le -ar 44100 -ac 1 "{seg}"')
    lst = f'{AU}/nlist.txt'
    with open(lst, 'w') as f:
        for row in tl:
            f.write(f"file '{AU}/nseg_{row['i']:02d}.wav'\n")
    sh(f'ffmpeg -y -v error -f concat -safe 0 -i "{lst}" -c:a pcm_s16le '
       f'-ar 44100 -ac 1 "{AU}/narr.wav"')
    return dur_of(f'{AU}/narr.wav')


# ---------------------------------------------------------------- 5. 字幕
def split_sents(text, maxlen=24):
    text = text.replace('\n', '')
    parts, buf = [], ''
    for ch in text:
        buf += ch
        if ch in '。！？；' and len(buf) >= 4:
            parts.append(buf); buf = ''
        elif len(buf) >= maxlen and ch in '，、,—':
            parts.append(buf); buf = ''
        elif len(buf) >= maxlen + 8:
            parts.append(buf); buf = ''
    if buf.strip():
        parts.append(buf)
    return [p for p in parts if p.strip()]


def build_subs(tl):
    def ts(sec):
        h = int(sec // 3600); m = int((sec % 3600) // 60); s = sec % 60
        return f'{h:d}:{m:02d}:{s:05.2f}'
    lines = [
        '[Script Info]',
        'ScriptType: v4.00+',
        'PlayResX: 1920', 'PlayResY: 1080',
        'WrapStyle: 0', 'ScaledBorderAndShadow: yes',
        '',
        '[V4+ Styles]',
        'Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, '
        'BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, '
        'BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding',
        'Style: Main,Noto Sans CJK SC,54,&H00FFFFFF,&H000000FF,&H00101010,&H80000000,'
        '-1,0,0,0,100,100,0,0,1,3.4,1.6,2,90,90,66,1',
        'Style: Note,Noto Sans CJK SC,46,&H00E8EFFA,&H000000FF,&H00101010,&H80000000,'
        '0,0,0,0,100,100,0,0,1,3,1.4,2,120,120,60,1',
        '',
        '[Events]',
        'Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text',
    ]
    for row in tl:
        sents = split_sents(row['text'])
        if not sents:
            continue
        total_c = sum(len(s) for s in sents)
        t = row['start']
        avail = row['nar']
        for k, s in enumerate(sents):
            dur = avail * (len(s) / total_c)
            st, en = t, t + dur
            style = 'Main'
            if row['type'] in ('note',):
                style = 'Note'
            txt = s.replace('\n', ' ')
            lines.append(f'Dialogue: 0,{ts(st)},{ts(en)},{style},,0,0,0,,{txt}')
            t = en
    open(f'{SU}/ep18.ass', 'w', encoding='utf-8').write('\n'.join(lines) + '\n')
    return f'{SU}/ep18.ass'


# ---------------------------------------------------------------- 6. 音效
def build_sfx_mix(tl):
    """把 whoosh / click / impact / blip 铺到时间轴上，输出混音 wav"""
    total = tl[-1]['start'] + tl[-1]['dur'] + 1.5
    n = int(total * 44100)
    from scipy.signal import fftconvolve
    acc = np.zeros(n)

    def add(path, at, gain=1.0):
        x, sr = read_wav(path)
        if sr != 44100:
            return
        i = int(at * 44100)
        e = min(n, i + len(x))
        if e > i:
            acc[i:e] += x[:e - i] * gain

    for row in tl:
        t = row['start']
        if row['type'] == 'clip':
            add(f'{BUILD}/music/whoosh.wav', max(t - 0.28, 0), 0.55)
        else:
            add(f'{BUILD}/music/click.wav', max(t - 0.06, 0), 0.30)
        if row['type'] == 'ladder':
            add(f'{BUILD}/music/impact.wav', max(t - 0.2, 0), 0.42)
        if row['type'] == 'bignums':
            add(f'{BUILD}/music/blip.wav', max(t + 0.5, 0), 0.22)
            add(f'{BUILD}/music/blip2.wav', max(t + 1.1, 0), 0.16)
        if row['type'] == 'note':
            add(f'{BUILD}/music/blip2.wav', max(t - 0.1, 0), 0.20)
    write_wav(f'{AU}/sfx.wav', acc, 44100)
    return f'{AU}/sfx.wav'


def read_wav(path):
    import wave
    with wave.open(path, 'rb') as w:
        sr = w.getframerate()
        n = w.getnframes()
        raw = w.readframes(n)
    dt = np.frombuffer(raw, dtype='<i2').astype(np.float64) / 32768.0
    return dt, sr


def write_wav(path, x, sr):
    import wave
    x = np.clip(x, -1, 1)
    pcm = (x * 32767).astype('<i2')
    with wave.open(path, 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes(pcm.tobytes())


import numpy as np  # noqa: E402


# ---------------------------------------------------------------- 7. 总装
def assemble(tl, narr_dur, ass_path, sfx_path):
    seg_list = f'{SEG}/list.txt'
    with open(seg_list, 'w') as f:
        for row in tl:
            f.write(f"file '{SEG}/seg_{row['i']:02d}.mp4'\n")
    total = tl[-1]['start'] + tl[-1]['dur']
    # 旁白音量 + 配乐 + 音效
    bgm_gain = 0.16
    cmd = (
        f'ffmpeg -y -v error -f concat -safe 0 -i "{seg_list}" '
        f'-i "{AU}/narr.wav" -i "{BUILD}/music/bgm.wav" -i "{sfx_path}" '
        f'-filter_complex "'
        f'[1:a]aformat=sample_fmts=fltp:sample_rates=44100:channel_layouts=mono,'
        f'volume=1.0[n];'
        f'[2:a]aformat=sample_fmts=fltp:sample_rates=44100:channel_layouts=mono,'
        f'volume={bgm_gain},atrim=0:{total:.3f},afade=t=in:st=0:d=2.5,'
        f'afade=t=out:st={max(total-4.5,0):.3f}:d=4.5[b];'
        f'[3:a]aformat=sample_fmts=fltp:sample_rates=44100:channel_layouts=mono[s];'
        f'[n][b][s]amix=inputs=3:duration=first:normalize=0[mix];'
        f'[mix]loudnorm=I=-15:TP=-4.5:LRA=11:print_format=summary[outa]" '
        f'-map 0:v -map "[outa]" -c:v copy -c:a aac -b:a 192k -ar 44100 -ac 2 '
        f'-shortest "{OUT}/ep18_silent.mp4"'
    )
    sh(cmd)
    # 烧字幕
    crf = os.environ.get('FINAL_CRF', '24')
    sh(f'ffmpeg -y -v error -i "{OUT}/ep18_silent.mp4" -vf "ass=\'{ass_path}\'" '
       f'-c:v libx264 -preset veryfast -tune stillimage -crf {crf} -pix_fmt yuv420p -r {FPS} '
       f'-c:a copy "{OUT}/ep18.mp4"')
    return f'{OUT}/ep18.mp4'


if __name__ == '__main__':
    import numpy as np  # noqa
    t0 = time.time()
    render_frames()
    tl = compute_timeline()
    print('总时长', tl[-1]['start'] + tl[-1]['dur'], 's')
    build_segments(tl)
    nd = build_narration(tl)
    print('旁白轨', nd, 's')
    ass = build_subs(tl)
    sfx = build_sfx_mix(tl)
    out = assemble(tl, nd, ass, sfx)
    print('DONE ->', out, os.path.getsize(out) // 1024, 'KB', f'{time.time()-t0:.0f}s')
