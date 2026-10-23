#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 AI 生成的 I2V 片段装配成成片镜头段（与静帧段同一套视觉语言）

流程：拆帧 → ping-pong 序列（正放+倒放，末帧首帧天然相接，可无缝循环）
      → 按目标时长裁切/变速 → 调色 + 叠标题卡 → 10fps 静帧风格编码
"""
import importlib.util, os, subprocess, sys, glob, shutil, time

BUILD = '/workspace/build'
FPS, W, H = 10, 1920, 1080
SEG = f'{BUILD}/seg'
TMP = '/tmp/pp'
os.makedirs(SEG, exist_ok=True)

spec = importlib.util.spec_from_file_location('b', f'{BUILD}/build_ep18.py')
b = importlib.util.module_from_spec(spec); spec.loader.exec_module(b)
SLIDES = b.SLIDES
sys.path.insert(0, BUILD)
import render as R
import render_ext  # noqa
from clip_overlay import clip_overlay

R.SERIES = b.EP['series']
TOTAL = len(SLIDES)

# 视频可用素材（按优先级：2K > 768P > 1080P）
VID = {
    'dc_corridor': f'{BUILD}/clips/MiniMax-H3_2K/dc_corridor.mp4',
    'city_phone':  f'{BUILD}/clips/MiniMax-H3-Max_768P/city_phone.mp4',
    'cloud_particles': f'{BUILD}/clips/MiniMax-Hailuo-2.3_1080P/cloud_particles.mp4',
}

GRADE = ("curves=all='0/0 0.5/0.5 1/1',eq=saturation=0.94:contrast=1.045:brightness=-0.012,"
         "unsharp=5:5:0.4,noise=alls=4:allf=u,vignette=PI/4.6")
# 近似 render_ext._grade 的冷调（与静帧镜头的 PIL 调色对齐）
VIDPRE = "colorbalance=rs=-0.045:bs=0.045:rm=-0.02:bm=0.02,eq=contrast=1.03:saturation=0.96"


def sh(cmd, timeout=2400):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
    if r.returncode != 0:
        raise RuntimeError(f'CMD FAIL: {cmd[:200]}\n{r.stderr[-1500:]}')
    return r.stdout


def dur_of(p):
    o = subprocess.run(['ffprobe', '-v', 'quiet', '-show_entries', 'format=duration',
                        '-of', 'csv=p=0', p], capture_output=True, text=True)
    try:
        return float(o.stdout.strip())
    except Exception:
        return 0.0


def build_pingpong(src, workdir):
    """拆帧 → 建正放+倒放的符号链接序列 → 编码成无缝循环"""
    fwd = f'{workdir}/f'
    seq = f'{workdir}/s'
    loop = f'{workdir}/loop.mp4'
    if os.path.exists(loop):
        try:
            d = float(open(f'{workdir}/loop.dur').read().strip())
            return loop, d
        except Exception:
            pass
    shutil.rmtree(f'{workdir}/f', ignore_errors=True)
    shutil.rmtree(f'{workdir}/s', ignore_errors=True)
    os.makedirs(fwd); os.makedirs(seq)
    sh(f'ffmpeg -y -v error -i "{src}" -vsync 0 "{fwd}/%05d.png"')
    frames = sorted(glob.glob(f'{fwd}/*.png'))
    n = len(frames)
    if n < 4:
        raise RuntimeError('frames too few')
    order = list(range(n)) + list(range(n - 2, 0, -1))      # 1..N, N-1..2
    for i, k in enumerate(order, 1):
        os.symlink(os.path.abspath(frames[k]), f'{seq}/{i:05d}.png')
    if not os.path.exists(loop):
        sh(f'ffmpeg -y -v error -framerate 24 -i "{seq}/%05d.png" -c:v libx264 -preset veryfast '
           f'-crf 16 -pix_fmt yuv420p "{loop}"')
    shutil.rmtree(fwd, ignore_errors=True)
    open(f'{workdir}/loop.dur', 'w').write(str(len(order) / 24.0))
    return loop, len(order) / 24.0


def build_vid_segment(i, target_dur):
    """AI 片段直接慢放拉满该镜头的时长：源镜头都是「推近/漂移」，慢放后反而更自然，
    而且单次编码，不必走拆帧 + ping-pong 的重流程。"""
    s = SLIDES[i]
    name = s['clip']
    src = VID.get(name)
    if not src or not os.path.exists(src):
        return None
    work = f'{TMP}/{name}'
    os.makedirs(work, exist_ok=True)
    src_dur = dur_of(src)
    factor = target_dur / max(src_dur, 0.1)     # >1 = 放慢（时间戳被拉长）
    nframes = int(round(target_dur * FPS))
    ov = f'{work}/overlay.png'
    meta = {'ep_no': b.EP.get('disp', b.EP['id']), 'ep_title': b.EP['title'],
            'total': TOTAL, 'page': i}
    clip_overlay(s, meta, ov)
    out = f'{SEG}/seg_{i:02d}.mp4'
    cmd = (f'ffmpeg -y -v error -i "{src}" -i "{ov}" '
           f'-filter_complex "[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,'
           f'crop={W}:{H},setsar=1,setpts={factor:.5f}*PTS,{VIDPRE}[bg];'
           f'[bg][1:v]overlay=0:0:format=auto,{GRADE},fps={FPS},format=yuv420p[v]" '
           f'-map "[v]" -frames:v {nframes} -r {FPS} -c:v libx264 -preset veryfast '
           f'-tune stillimage -crf 20 -pix_fmt yuv420p "{out}"')
    sh(cmd)
    d = dur_of(out)
    print(f'[vid-seg] {i:02d} {name:16s} 目标 {target_dur:6.2f}s 实得 {d:6.2f}s '
          f'源 {src_dur:.1f}s 放慢至 {src_dur/target_dur:.2f}x -> {os.path.getsize(out)//1024}KB', flush=True)
    return out


if __name__ == '__main__':
    tl = b.compute_timeline()
    t0 = time.time()
    for row in tl:
        if SLIDES[row['i']]['type'] != 'clip':
            continue
        i = row['i']
        if SLIDES[i]['clip'] not in VID:
            print(f'[vid-skip] {i:02d} {SLIDES[i]["clip"]} 无 AI 素材，用静帧运镜', flush=True)
            continue
        build_vid_segment(i, row['dur'])
    print('video segments done', round(time.time() - t0, 1), 's')
