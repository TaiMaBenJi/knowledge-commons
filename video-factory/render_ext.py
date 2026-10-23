# -*- coding: utf-8 -*-
"""在仓库 render.py 设计系统之上补两个专属版式：
   1) ladder —— 全片脊柱「五级台阶」总览图
   2) clip   —— AI 电影级镜头 + 统一标题卡（把生成素材并入项目视觉语言）
"""
import os, sys
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render as R
from render import (W, H, C_BG1, C_BG2, C_PANEL, C_PANEL_L, C_LINE, C_TEXT, C_SUB, C_DIM,
                    C_CYAN, C_ORANGE, C_GREEN, C_RED, C_PURPLE, F, new_slide, wrap,
                    rrect, dot, draw_chrome, title_block)

LADDER_LEVELS = [
    ('L1', '地基层', 'Linux · 网络 · 存储 · 机房', C_CYAN),
    ('L2', '虚拟化层', '一台物理机切成很多台', C_GREEN),
    ('L3', '服务模型层', 'IaaS / PaaS / SaaS', C_ORANGE),
    ('L4', '容器编排层', 'Docker + Kubernetes', C_PURPLE),
    ('L5', '云原生层', '无服务器 · 微服务 · 弹性', C_RED),
]


def slide_ladder(meta, s):
    """五级台阶：从下到上 L1→L5，逐级缩进，读起来就是一段楼梯"""
    img = new_slide(); d = ImageDraw.Draw(img)
    body_y = title_block(d, s['title'], C_CYAN)
    if s.get('subtitle'):
        d.text((130, body_y - 46), s['subtitle'], font=F(30), fill=C_SUB)
    # 台阶几何：从左下到右上
    x0, x1 = 130, W - 130
    n = len(LADDER_LEVELS)
    bottom = H - 150
    row_h = 118
    gap = 14
    for i, (tag, name, desc, accent) in enumerate(LADDER_LEVELS):
        # L1 在最下（i=0），L5 在最上
        y = bottom - (i + 1) * row_h - i * gap
        indent = i * 62
        bx0 = x0 + indent
        bx1 = x1
        rrect(d, [bx0, y, bx1, y + row_h], 16, fill=C_PANEL, outline=accent, width=2)
        rrect(d, [bx0, y, bx0 + 7, y + row_h], 3, fill=accent)
        # 等级标签
        rrect(d, [bx0 + 26, y + 30, bx0 + 118, y + 88], 12, fill=(18, 30, 52), outline=accent, width=2)
        d.text((bx0 + 72, y + 59), tag, font=F(32, True), fill=accent, anchor='mm')
        # 名称
        d.text((bx0 + 142, y + 28), name, font=F(40, True), fill=C_TEXT)
        # 描述
        d.text((bx0 + 142, y + 76), desc, font=F(27), fill=C_SUB)
        # 右侧「你管到哪」提示
        d.text((bx1 - 26, y + 59), '→', font=F(30, True), fill=accent, anchor='rm')
    # 左侧上升箭头
    ax = 92
    d.line([(ax, bottom - row_h * 0.6), (ax, bottom - (n - 0.5) * (row_h + gap))],
           fill=C_LINE, width=4)
    d.polygon([(ax - 9, bottom - (n - 0.5) * (row_h + gap)),
               (ax + 9, bottom - (n - 0.5) * (row_h + gap)),
               (ax, bottom - (n - 0.6) * (row_h + gap))], fill=C_CYAN)
    d.text((ax, bottom + 12), '精通', font=F(24, True), fill=C_DIM, anchor='ma')
    d.text((ax, bottom - (n - 0.2) * (row_h + gap)), '零基础', font=F(24, True),
           fill=C_DIM, anchor='ma')
    draw_chrome(d, meta['ep_no'], meta['ep_title'], meta['page'], meta['total'])
    return img


def _grade(img):
    """电影感调色：冷调 + 暗角 + 轻微颗粒（与项目深色科技风统一）"""
    from PIL import ImageEnhance
    import numpy as np
    img = img.convert('RGB')
    a = np.asarray(img).astype(np.float32) / 255.0
    # 冷调：压红提蓝
    a[..., 0] *= 0.94
    a[..., 2] *= 1.045
    # S 曲线
    a = np.clip(a, 0, 1)
    a = a * a * (3 - 2 * a) * 0.42 + a * 0.58
    out = Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8))
    out = ImageEnhance.Color(out).enhance(0.94)
    # 暗角
    vig = Image.new('L', (W, H), 0)
    vd = ImageDraw.Draw(vig)
    vd.ellipse([-W * 0.32, -H * 0.42, W * 1.32, H * 1.42], fill=255)
    vig = vig.filter(ImageFilter.GaussianBlur(190))
    dark = Image.new('RGB', (W, H), (4, 7, 16))
    out = Image.composite(out, dark, vig)
    return out


def slide_clip(meta, s, kf_dir='/workspace/build/kf'):
    """AI 电影级镜头 + 统一标题卡：把生成素材并入项目视觉语言"""
    name = s['clip']
    path = f'{kf_dir}/{name}.png'
    if not os.path.exists(path):
        img = new_slide(); d = ImageDraw.Draw(img)
        d.text((W / 2, H / 2), s.get('title', ''), font=F(56, True), fill=C_TEXT, anchor='mm')
        draw_chrome(d, meta['ep_no'], meta['ep_title'], meta['page'], meta['total'])
        return img
    base = Image.open(path).convert('RGB').resize((W, H), Image.LANCZOS)
    base = _grade(base)
    # 底部压暗 scrim，让字幕可读
    scrim = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(scrim)
    for y in range(int(H * 0.42), H):
        t = (y - H * 0.42) / (H * 0.58)
        t = max(0.0, min(1.0, t))
        sd.line([(0, y), (W, y)], fill=(3, 6, 14, int(215 * (t ** 1.25))))
    # 左侧竖向压暗
    for x in range(0, int(W * 0.52)):
        t = max(0.0, min(1.0, 1 - x / (W * 0.52)))
        sd.line([(x, 0), (x, H)], fill=(3, 6, 14, int(120 * (t ** 2.0))))
    base = Image.alpha_composite(base.convert('RGBA'), scrim).convert('RGB')
    d = ImageDraw.Draw(base)
    accent = s.get('accent', C_CYAN)
    # 标题：左下
    tx, ty = 130, H - 300
    f_t = F(54, True)
    lines = wrap(s.get('title', ''), f_t, 1250)[:2]
    d.line([(tx, ty - 26), (tx + 92, ty - 26)], fill=accent, width=8)
    for ln in lines:
        d.text((tx, ty), ln, font=f_t, fill=C_TEXT)
        ty += 72
    # 顶部：系列名 + 集数
    dot(d, 130, 66, 9, accent)
    d.text((158, 50), R.SERIES, font=F(26), fill=C_SUB)
    d.text((W - 130, 50), f"第 {meta['ep_no']} 讲 · {meta['ep_title']}",
           font=F(26, True), fill=C_DIM, anchor='ra')
    # 底部进度线
    d.line([(130, H - 58), (W - 130, H - 58)], fill=C_LINE, width=2)
    prog = 0 if meta['total'] <= 1 else meta['page'] / (meta['total'] - 1)
    d.line([(130, H - 58), (130 + (W - 260) * prog, H - 58)], fill=accent, width=4)
    d.text((130, H - 48), f"{meta['page']+1:02d} / {meta['total']:02d}", font=F(24), fill=C_DIM)
    d.text((W - 130, H - 48), '配套图文教程 + 真机训练场', font=F(22), fill=C_DIM, anchor='ra')
    return base


R.RENDERERS['ladder'] = slide_ladder
R.RENDERERS['clip'] = slide_clip
