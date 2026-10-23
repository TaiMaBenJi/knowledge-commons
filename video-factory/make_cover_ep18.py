#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""封面（640x360）与图解截图（1280x720）"""
import os, sys
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance
import numpy as np

BUILD = '/workspace/build'
sys.path.insert(0, BUILD)
import render as R
import render_ext
from render import F, C_TEXT, C_SUB, C_CYAN, C_ORANGE, C_DIM, C_PANEL, C_LINE

os.makedirs(f'{BUILD}/gallery', exist_ok=True)
C_OVER = f'{BUILD}/cover.png'


def grade(img, W, H):
    a = np.asarray(img.convert('RGB')).astype(np.float32) / 255.0
    a[..., 0] *= 0.93
    a[..., 2] *= 1.05
    a = np.clip(a, 0, 1)
    a = a * a * (3 - 2 * a) * 0.44 + a * 0.56
    out = Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8))
    out = ImageEnhance.Color(out).enhance(0.95)
    vig = Image.new('L', (W, H), 0)
    ImageDraw.Draw(vig).ellipse([-W * 0.34, -H * 0.44, W * 1.34, H * 1.44], fill=255)
    vig = vig.filter(ImageFilter.GaussianBlur(int(W * 0.09)))
    dark = Image.new('RGB', (W, H), (3, 6, 14))
    return Image.composite(out, dark, vig)


def make_cover():
    W, H = 640, 360
    kf = Image.open(f'{BUILD}/kf/dc_corridor.png').convert('RGB').resize((W, H), Image.LANCZOS)
    kf = grade(kf, W, H)
    # 底部暗场
    scrim = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(scrim)
    for y in range(int(H * 0.40), H):
        t = (y - H * 0.40) / (H * 0.60)
        sd.line([(0, y), (W, y)], fill=(4, 8, 18, int(232 * (t ** 1.15))))
    img = Image.alpha_composite(kf.convert('RGBA'), scrim).convert('RGB')
    d = ImageDraw.Draw(img)
    # 系列标
    d.ellipse([26, 26, 36, 36], fill=C_CYAN)
    d.text((44, 21), '云计算保姆级教程 · 从零到精通', font=F(15), fill=C_SUB)
    # 主标题
    d.text((26, 168), '云计算', font=F(54, True), fill=C_TEXT)
    d.text((26, 224), '从零到精通', font=F(54, True), fill=C_TEXT)
    d.line([(26, 162), (66, 162)], fill=C_CYAN, width=5)
    # 副标
    d.text((26, 300), '第 18 集 · 总纲片', font=F(19, True), fill=C_ORANGE)
    d.text((200, 302), '一张地图讲清整条路', font=F(17), fill=C_DIM)
    # 右侧大号数字
    d.text((W - 18, H - 12), '18', font=F(150, True), fill=(34, 50, 86), anchor='rs')
    img.save(C_OVER)
    print('cover ->', C_OVER, img.size)


def make_gallery():
    picks = [(0, 'slide_08.png'), (1, 'slide_01.png'), (2, 'slide_16.png')]
    for n, src in picks:
        im = Image.open(f'{BUILD}/frames/{src}').convert('RGB').resize((1280, 720), Image.LANCZOS)
        im.save(f'{BUILD}/gallery/course-ep18-{n}.jpg', quality=88)
        print(f'gallery course-ep18-{n}.jpg -> {src}')


if __name__ == '__main__':
    make_cover()
    make_gallery()
