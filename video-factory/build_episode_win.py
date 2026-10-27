#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Windows/本机版单集构建：渲染帧 -> edge-tts 配音 -> ffmpeg 合成 MP4
与 build_episode.py 的 EPISODE 格式完全一致，可直接吃 scripts/ 下的分镜脚本。
区别：字体走 Windows 微软雅黑（可用环境变量 KC_FONT_B / KC_FONT_R 覆盖），
ffmpeg 用 imageio-ffmpeg 自带静态版（无 ffprobe，时长用 ffmpeg -i 解析）。
用法：python build_episode_win.py scripts/beginner-b01.py [输出目录]
"""
import sys, os, re, subprocess, asyncio
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import render  # noqa: E402
import edge_tts  # noqa: E402
from vf_safe import sh, sh_err, under  # noqa: E402

from imageio_ffmpeg import get_ffmpeg_exe
FF = get_ffmpeg_exe()
VOICE = os.environ.get('KC_VOICE', 'zh-CN-YunxiNeural')
PAD = 0.72
ROOT = os.environ.get('VIDEO_ROOT', os.path.join(HERE, '_build'))
OUT_OVERRIDE = sys.argv[2] if len(sys.argv) > 2 else None

# 字体：优先环境变量，其次 Windows 雅黑，最后回落 Linux Noto
if os.environ.get('KC_FONT_B'):
    render.FONT_B = os.environ['KC_FONT_B']
elif os.path.exists('C:/Windows/Fonts/msyhbd.ttc'):
    render.FONT_B = 'C:/Windows/Fonts/msyhbd.ttc'
if os.environ.get('KC_FONT_R'):
    render.FONT_R = os.environ['KC_FONT_R']
elif os.path.exists('C:/Windows/Fonts/msyh.ttc'):
    render.FONT_R = 'C:/Windows/Fonts/msyh.ttc'
render._fonts = {}


def dur_of(path):
    """无 ffprobe 时用 ffmpeg 解析总时长（容忍非零退出，只解析输出）"""
    r = sh_err([FF, '-i', path, '-f', 'null', '-'], check=False)
    m = re.findall(r'time=(\d+):(\d+):([\d.]+)', r)
    if not m:
        raise RuntimeError('cannot parse duration: ' + path)
    h, mi, s = m[-1]
    return int(h) * 3600 + int(mi) * 60 + float(s)


async def tts_all(jobs):
    sem = asyncio.Semaphore(3)

    async def one(text, out):
        async with sem:
            last = None
            for attempt in range(10):
                try:
                    c = edge_tts.Communicate(text, VOICE)
                    await asyncio.wait_for(c.save(out), timeout=40)
                    await asyncio.sleep(1.0)
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
        render.SERIES = ep['series']
    fdir = os.path.join(ROOT, 'frames', sub, 'ep' + ep_no)
    adir = os.path.join(ROOT, 'audio', sub, 'ep' + ep_no)
    outdir = OUT_OVERRIDE or os.path.join(ROOT, 'out', sub)
    for p in (fdir, adir, outdir):
        os.makedirs(p, exist_ok=True)
    slides = ep['slides']
    total = len(slides)
    meta_base = {'ep_no': ep.get('disp', ep_no), 'ep_title': ep['title'], 'total': total}
    print(f'== EP{ep_no} {ep["title"]} | {total} slides ==', flush=True)
    rebuild = os.environ.get('REBUILD') == '1'
    # 1) 渲染帧
    for i, s in enumerate(slides):
        fp = os.path.join(fdir, 'slide_%02d.png' % i)
        if rebuild or not os.path.exists(fp):
            render.render_slide(s, dict(meta_base, page=i)).save(fp)
        print(f'[frame] {i+1}/{total}', flush=True)
    # 2) TTS
    jobs = []
    for i, s in enumerate(slides):
        raw = os.path.join(adir, 's%02d.mp3' % i)
        if rebuild or not (os.path.exists(raw) and os.path.getsize(raw) > 800):
            jobs.append((s.get('narration', ''), raw))
    if jobs:
        asyncio.run(tts_all(jobs))
    # 3) pad + 时长
    durations = []; plist = []
    for i in range(total):
        raw = os.path.join(adir, 's%02d.mp3' % i)
        padf = os.path.join(adir, 's%02d_pad.mp3' % i)
        if rebuild or not os.path.exists(padf):
            sh([FF, '-y', '-v', 'error', '-i', raw, '-af', 'apad=pad_dur=%s' % PAD,
                '-ar', '44100', '-ac', '1', '-b:a', '96k', padf])
        durations.append(dur_of(padf)); plist.append(padf)
    # 4) 音频总轨（写文件走 pathlib + 收容校验）
    alist = under(adir, 'alist.txt')
    Path(alist).write_text(''.join(
        "file '%s'\n" % p.replace('\\', '/') for p in plist), encoding='utf-8')
    full = under(adir, 'full.mp3')
    sh([FF, '-y', '-v', 'error', '-f', 'concat', '-safe', '0', '-i', alist, '-c', 'copy', full])
    # 5) 图片时间轴
    imgs = under(fdir, 'imgs.txt')
    lines = []
    for i in range(total):
        lines.append("file '%s'\nduration %.3f\n" % (
            os.path.join(fdir, 'slide_%02d.png' % i).replace('\\', '/'), durations[i]))
    lines.append("file '%s'\n" % os.path.join(fdir, 'slide_%02d.png' % (total - 1)).replace('\\', '/'))
    Path(imgs).write_text(''.join(lines), encoding='utf-8')
    # 6) 编码
    out = under(outdir, 'ep%s.mp4' % ep_no)
    sh([FF, '-y', '-v', 'error', '-f', 'concat', '-safe', '0', '-i', imgs, '-i', full,
        '-c:v', 'libx264', '-preset', 'veryfast', '-tune', 'stillimage', '-crf', '23',
        '-pix_fmt', 'yuv420p', '-r', '10', '-c:a', 'aac', '-b:a', '128k', '-shortest', out])
    d = dur_of(out); size = os.path.getsize(out)
    print(f'== DONE ep{ep_no}: {d/60:.1f} min, {size/1e6:.1f} MB -> {out} ==', flush=True)


if __name__ == '__main__':
    import importlib.util
    spec = importlib.util.spec_from_file_location('ep', sys.argv[1])
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    build(m.EPISODE)
