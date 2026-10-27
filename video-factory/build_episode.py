#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""单集视频构建流水线: 渲染帧 -> 配音 -> 合成 MP4"""
import sys, os, asyncio
from pathlib import Path
sys.path.insert(0, '/opt/tmbj/room-video/lib')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from render import render_slide
import edge_tts
from vf_safe import sh, under

ROOT = os.environ.get('VIDEO_ROOT', '/opt/tmbj/room-video')
VOICE = 'zh-CN-YunxiNeural'
PAD = 0.72

def dur_of(path):
    out = sh(['ffprobe', '-v', 'quiet', '-show_entries', 'format=duration',
              '-of', 'csv=p=0', path])
    return float(out.strip())

async def tts_all(jobs):
    sem = asyncio.Semaphore(3)
    async def one(text, out):
        async with sem:
            last = None
            for attempt in range(10):
                try:
                    c = edge_tts.Communicate(text, VOICE)
                    await asyncio.wait_for(c.save(out), timeout=25)
                    await asyncio.sleep(1.2)
                    return
                except Exception as e:
                    last = e
                    await asyncio.sleep(1 + attempt * 1.2)
            raise last
    await asyncio.gather(*[one(t, o) for t, o in jobs])

def build(ep):
    ep_no = ep['id']
    sid = ep.get('sid', '')
    sub = f'{sid}/' if sid else ''
    if ep.get('series'):
        import render as _render
        _render.SERIES = ep['series']
    fdir = under(ROOT, 'frames', sub, f'ep{ep_no}')
    adir = under(ROOT, 'audio', sub, f'ep{ep_no}')
    os.makedirs(fdir, exist_ok=True); os.makedirs(adir, exist_ok=True)
    os.makedirs(under(ROOT, 'out', sub), exist_ok=True)
    slides = ep['slides']; total = len(slides)
    meta_base = {'ep_no': ep.get('disp', ep_no), 'ep_title': ep['title'], 'total': total}
    print(f'== EP{ep_no} {ep["title"]} | {total} slides ==', flush=True)
    # 1) 渲染帧（跳过已存在，除非 REBUILD=1）
    rebuild = os.environ.get('REBUILD') == '1'
    for i, s in enumerate(slides):
        fp = under(fdir, f'slide_{i:02d}.png')
        if rebuild or not os.path.exists(fp):
            img = render_slide(s, dict(meta_base, page=i))
            img.save(fp)
        print(f'[frame] {i+1}/{total}', flush=True)
    # 2) TTS
    jobs = []
    for i, s in enumerate(slides):
        raw = under(adir, f's{i:02d}.mp3')
        if rebuild or not (os.path.exists(raw) and os.path.getsize(raw) > 1000):
            jobs.append((s.get('narration', ''), raw))
    if jobs:
        asyncio.run(tts_all(jobs))
    # 3) pad + 时长
    durations = []; plist = []
    for i in range(total):
        raw = under(adir, f's{i:02d}.mp3'); padf = under(adir, f's{i:02d}_pad.mp3')
        if rebuild or not os.path.exists(padf):
            sh(['ffmpeg', '-y', '-v', 'error', '-i', raw, '-af', f'apad=pad_dur={PAD}',
                '-ar', '44100', '-ac', '1', '-b:a', '96k', padf])
        durations.append(dur_of(padf)); plist.append(padf)
    # 4) 音频总轨（写文件走 pathlib write_text + under() 收容）
    alist = under(adir, 'alist.txt')
    Path(alist).write_text(''.join("file '%s'\n" % p for p in plist), encoding='utf-8')
    full = under(adir, 'full.mp3')
    sh(['ffmpeg', '-y', '-v', 'error', '-f', 'concat', '-safe', '0',
        '-i', alist, '-c', 'copy', full])
    # 5) 图片时间轴
    imgs = under(fdir, 'imgs.txt')
    lines = []
    for i in range(total):
        lines.append("file '%s'\nduration %.3f\n" % (under(fdir, f'slide_{i:02d}.png'), durations[i]))
    lines.append("file '%s'\n" % under(fdir, f'slide_{total-1:02d}.png'))
    Path(imgs).write_text(''.join(lines), encoding='utf-8')
    # 6) 编码
    out = under(ROOT, 'out', sub, f'ep{ep_no}.mp4')
    sh(['ffmpeg', '-y', '-v', 'error', '-f', 'concat', '-safe', '0',
        '-i', imgs, '-i', full,
        '-c:v', 'libx264', '-preset', 'veryfast', '-tune', 'stillimage',
        '-crf', '23', '-pix_fmt', 'yuv420p', '-r', '10',
        '-c:a', 'aac', '-b:a', '128k', '-shortest', out])
    d = dur_of(out); size = os.path.getsize(out)
    print(f'== DONE ep{ep_no}: {d/60:.1f} min, {size/1e6:.1f} MB ==', flush=True)

if __name__ == '__main__':
    import importlib.util
    spec = importlib.util.spec_from_file_location('ep', sys.argv[1])
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    build(m.EPISODE)
