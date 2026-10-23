# -*- coding: utf-8 -*-
"""把 render_ext.slide_clip 的「压暗 scrim + 标题卡」单独渲染成透明 PNG，
   供 AI 视频段叠加使用（保证视频镜头与静帧镜头的视觉语言完全一致）。"""
import os, sys
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render as R
import render_ext
from render import (W, H, C_TEXT, C_SUB, C_DIM, C_CYAN, C_LINE, F, wrap, dot)


def clip_overlay(s, meta, path):
    accent = s.get('accent', C_CYAN)
    ov = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(ov)
    # 底部压暗
    for y in range(int(H * 0.42), H):
        t = max(0.0, min(1.0, (y - H * 0.42) / (H * 0.58)))
        sd.line([(0, y), (W, y)], fill=(3, 6, 14, int(215 * (t ** 1.25))))
    # 左侧竖向压暗
    for x in range(0, int(W * 0.52)):
        t = max(0.0, min(1.0, 1 - x / (W * 0.52)))
        sd.line([(x, 0), (x, H)], fill=(3, 6, 14, int(120 * (t ** 2.0))))
    # 标题卡
    tx, ty = 130, H - 300
    f_t = F(54, True)
    lines = wrap(s.get('title', ''), f_t, 1250)[:2]
    sd.line([(tx, ty - 26), (tx + 92, ty - 26)], fill=accent, width=8)
    for ln in lines:
        sd.text((tx, ty), ln, font=f_t, fill=C_TEXT)
        ty += 72
    dot(sd, 130, 66, 9, accent)
    sd.text((158, 50), R.SERIES, font=F(26), fill=C_SUB)
    sd.text((W - 130, 50), f"第 {meta['ep_no']} 讲 · {meta['ep_title']}",
            font=F(26, True), fill=C_DIM, anchor='ra')
    # 进度条
    sd.line([(130, H - 58), (W - 130, H - 58)], fill=C_LINE, width=2)
    prog = 0 if meta['total'] <= 1 else meta['page'] / (meta['total'] - 1)
    sd.line([(130, H - 58), (130 + (W - 260) * prog, H - 58)], fill=accent, width=4)
    sd.text((130, H - 48), f"{meta['page']+1:02d} / {meta['total']:02d}", font=F(24), fill=C_DIM)
    sd.text((W - 130, H - 48), '配套图文教程 + 真机训练场', font=F(22), fill=C_DIM, anchor='ra')
    ov.save(path)
    return path
