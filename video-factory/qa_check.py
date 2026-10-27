#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""QA 质检：批量检查 12 集视频的完整性"""
import os, sys
from pathlib import Path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vf_safe import sh, sh_err, under

ROOT = '/opt/tmbj/room-video'

report = []
ok = fail = 0
for i in range(1, 13):
    no = f'{i:02d}'
    mp4 = under(ROOT, 'out', f'ep{no}.mp4')
    if not os.path.exists(mp4):
        report.append(f'EP{no}: MISSING'); fail += 1; continue
    size = os.path.getsize(mp4)
    dur = float(sh(['ffprobe', '-v', 'quiet', '-show_entries', 'format=duration',
                    '-of', 'csv=p=0', mp4]) or 0)
    v = sh(['ffprobe', '-v', 'error', '-select_streams', 'v:0',
            '-show_entries', 'stream=width,height,codec_name', '-of', 'csv=p=0', mp4])
    a = sh(['ffprobe', '-v', 'error', '-select_streams', 'a:0',
            '-show_entries', 'stream=codec_name', '-of', 'csv=p=0', mp4])
    # 音频非静音检查（volumedetect 写 stderr，原 shell 管道 grep 改为 Python 解析）
    vol_stream = sh_err(['ffmpeg', '-i', mp4, '-af', 'volumedetect', '-f', 'null', '-'])
    vol = next((ln.strip() for ln in vol_stream.splitlines() if 'mean_volume' in ln), '')
    volv = vol.split(':')[-1].strip() if vol else '?'
    # 抽帧像素检查
    tmp = f'/tmp/qa_{no}.png'
    sh(['ffmpeg', '-y', '-v', 'error', '-ss', '%.0f' % (dur / 2), '-i', mp4,
        '-frames:v', '1', tmp])
    px = '?'
    if os.path.exists(tmp):
        try:
            from PIL import Image
            im = Image.open(tmp).convert('L')
            hist = im.histogram()
            total = sum(hist)
            main = max(hist)
            px = f'非主色像素{100*(1-main/total):.0f}%'
        except Exception as e:
            px = f'ERR {e}'
    status = 'OK' if (dur > 300 and size > 3e6 and a) else 'CHECK'
    if status == 'OK': ok += 1
    else: fail += 1
    report.append(f'EP{no}: {status} | {dur/60:.1f}min | {size/1e6:.1f}MB | {v} | audio={a} | {volv} | {px}')

print('\n'.join(report))
print(f'\n== QA 汇总: OK={ok} / 12, PROBLEM={fail} ==')
