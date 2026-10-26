#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""程序化配乐与音效（纯 numpy 合成，零授权问题）

- BGM：Am - F - C - G 循环，4 小节一循环；层次 = 低频衬底 drone + 暖 pad +
  五声音阶玻璃铃点缀 + 空气噪声。带 Schroeder 混响。
- SFX：转场 whoosh、UI click、数据 blip、章节落点 impact。
"""
import numpy as np, os, json, struct, wave

SR = 44100
BUILD = '/workspace/build'
MUS = f'{BUILD}/music'
os.makedirs(MUS, exist_ok=True)

rng = np.random.default_rng(20261023)


# ---------------- 基础工具 ----------------
def midi_hz(n):
    return 440.0 * (2 ** ((n - 69) / 12.0))


def adsr(n, a=0.01, d=0.1, s=0.7, r=0.3):
    """a/d/r 单位是「秒」，s 是持续电平（0~1）。
    注意：早期版本把 a/d/r 当成 n 的比例，i2 会越过 n 导致 broadcasting 报错。"""
    i1 = int(min(max(a * SR, 1), n))
    i2 = int(min(max(i1 + d * SR, i1 + 1), n))
    i3 = int(min(max(n - r * SR, i2), n))
    env = np.zeros(n)
    env[:i1] = np.linspace(0, 1, i1)
    env[i1:i2] = np.linspace(1, s, max(i2 - i1, 1))
    env[i2:i3] = s
    env[i3:] = np.linspace(s, 0, max(n - i3, 1))
    return env


def pad_voice(freq, dur, detune=0.004, n_harm=5, seed=0):
    """暖 pad：多谐波 + 微失谐 + 缓慢颤音"""
    r = np.random.default_rng(seed)
    n = int(dur * SR)
    t = np.arange(n) / SR
    out = np.zeros(n)
    for h in range(1, n_harm + 1):
        amp = 1.0 / (h ** 1.35)
        for det in (-detune, 0.0, detune):
            f = freq * h * (1 + det)
            out += amp * np.sin(2 * np.pi * f * t + r.random() * 6.28)
    out /= n_harm * 3
    lfo = 0.5 + 0.5 * np.sin(2 * np.pi * (0.055 + 0.02 * seed % 0.1) * t)
    out *= (0.72 + 0.28 * lfo)
    return out


def bell(freq, dur, seed=0):
    """玻璃铃：非谐波正弦叠加 + 快衰减"""
    r = np.random.default_rng(seed)
    n = int(dur * SR)
    t = np.arange(n) / SR
    out = np.zeros(n)
    for f, a, d in ((1.0, 1.0, 2.2), (2.76, 0.42, 3.1), (5.4, 0.20, 4.4), (8.9, 0.09, 6.0)):
        env = np.exp(-d * t)
        out += a * env * np.sin(2 * np.pi * freq * f * t + r.random() * 6.28)
    out *= adsr(n, 0.002, 0.05, 0.6, 0.5) * 0.9
    return out * np.exp(-1.1 * t)


def noise_wash(dur, seed=0, lp=0.16, hp=0.004):
    """一阶低通 + 一阶高通（环形缓冲，O(n)）"""
    r = np.random.default_rng(seed)
    n = int(dur * SR)
    x = r.normal(0, 1, n)
    y = np.empty(n)
    acc = 0.0
    for i in range(n):
        acc += lp * (x[i] - acc)
        y[i] = acc
    y = y - np.mean(y)
    out = np.empty(n)
    acc = 0.0
    for i in range(n):
        acc += hp * (y[i] - acc)
        out[i] = acc
    return out * 2.4


def _fb(x, d, g):
    """带反馈的梳状滤波 y[n] = x[n] + g*y[n-d]，环形缓冲 O(n)"""
    n = len(x)
    buf = np.zeros(d)
    out = np.empty(n)
    idx = 0
    for i in range(n):
        v = x[i] + g * buf[idx]
        buf[idx] = v
        idx = (idx + 1) % d
        out[i] = v
    return out


def reverb(x, size=0.72, mix=0.32):
    """Schroeder: 4 combs + 2 allpass"""
    n = len(x)
    out = np.zeros(n)
    for d_ms, g in ((29.7, 0.86), (37.1, 0.82), (41.1, 0.80), (43.7, 0.78)):
        out += _fb(x, int(SR * d_ms / 1000), g)
    out /= 4
    for d_ms, g in ((5.0, 0.7), (1.7, 0.7)):
        out = _fb(out, int(SR * d_ms / 1000), g)
    return x * (1 - mix) + out * mix


def soft_clip(x, drive=1.0):
    return np.tanh(x * drive) / np.tanh(drive)


def to_wav(path, x, peak=0.92):
    x = np.asarray(x, dtype=np.float64)
    m = np.max(np.abs(x)) or 1.0
    x = x / m * peak
    pcm = (np.clip(x, -1, 1) * 32767).astype('<i2')
    with wave.open(path, 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    return path


# ---------------- BGM ----------------
def build_bgm(total_sec, path):
    """Am - F - C - G，每段 16s，带变奏：第二遍加铃与更亮 pad"""
    bar = 8.0                      # 每和弦 8 秒
    n_total = int(total_sec * SR) + SR
    # 声部编排
    CHORDS = [
        {'root': 45, 'notes': [57, 60, 64, 67]},   # Am
        {'root': 41, 'notes': [53, 57, 60, 65]},   # F
        {'root': 48, 'notes': [52, 55, 60, 64]},   # C
        {'root': 43, 'notes': [55, 59, 62, 67]},   # G
    ]
    drone = np.zeros(n_total)
    bed = np.zeros(n_total)
    sparkle = np.zeros(n_total)

    n_chords = int(np.ceil(total_sec / bar)) + 1
    for ci in range(n_chords):
        ch = CHORDS[ci % 4]
        t0 = ci * bar
        seg_len = min(bar + 2.5, total_sec - t0)
        if seg_len <= 0:
            break
        n = int(seg_len * SR)
        s0 = int(t0 * SR)
        # 低频 drone（带轻微 8 分音符脉冲感）
        d = pad_voice(midi_hz(ch['root'] - 12), seg_len, detune=0.002, n_harm=3, seed=ci)
        d *= 0.55
        # 和弦 pad
        p = np.zeros(n)
        for k, nt in enumerate(ch['notes']):
            p += pad_voice(midi_hz(nt), seg_len, detune=0.005, n_harm=4, seed=ci * 10 + k)
        p /= len(ch['notes'])
        env = adsr(n, 0.9, 0.6, 0.78, 0.9)
        mix = 0.62 * d + 0.38 * p
        mix *= env
        # 第二遍（ci>=4）加亮：加一层高八度
        if ci >= 4:
            bright = np.zeros(n)
            for k, nt in enumerate(ch['notes']):
                bright += pad_voice(midi_hz(nt + 12), seg_len, detune=0.006, n_harm=3, seed=ci * 20 + k)
            bright /= len(ch['notes'])
            mix += 0.14 * bright * env
        e = min(n_total - s0, n)
        if e > 0:
            drone[s0:s0 + e] += mix[:e] * 0.5
            bed[s0:s0 + e] += mix[:e]
        # 铃：每段随机落点，第二遍更密
        density = 0.55 if ci < 4 else 0.95
        if rng.random() < density:
            k_bells = 2 if ci < 4 else 3
            for b in range(k_bells):
                nt = ch['notes'][int(rng.integers(0, len(ch['notes'])))] + 12
                off = rng.uniform(0.4, max(0.6, seg_len - 2.2))
                bl = bell(midi_hz(nt), 3.2, seed=int(rng.integers(1, 9999)))
                pos = int((t0 + off) * SR)
                e2 = min(n_total - pos, len(bl))
                if e2 > 0:
                    sparkle[pos:pos + e2] += bl[:e2] * 0.10

    air = np.zeros(n_total)
    _a = noise_wash(total_sec, seed=7, lp=0.10) * 0.055
    air[:len(_a)] = _a[:n_total]
    # 缓慢的呼吸感
    t = np.arange(n_total) / SR
    swell = 0.72 + 0.28 * np.sin(2 * np.pi * t / 32.0)
    x = (drone * 0.62 + bed * 0.22 + sparkle + air) * swell
    x = reverb(x, mix=0.34)
    x = soft_clip(x, 1.15)
    to_wav(path, x, peak=0.78)
    return path


# ---------------- SFX ----------------
def sfx_whoosh(dur=0.85, path=None):
    n = int(dur * SR)
    t = np.arange(n) / SR
    r = np.random.default_rng(11)
    x = r.normal(0, 1, n)
    # 带通扫频：用简单 FIR 近似（移动平均 = 低通，中心频率随时间下降）
    out = np.zeros(n)
    w = 1
    for i in range(n):
        k = max(2, int(1 + 900 * (1 - i / n) ** 2))
        w = w * (1 - 1 / k) + x[i] / k
        out[i] = x[i] - w
    env = np.sin(np.pi * np.clip((t - 0.05) / (dur - 0.1), 0, 1)) ** 1.5
    out *= env * 0.5
    out = reverb(out, mix=0.22)
    to_wav(path, out, peak=0.6)
    return path


def sfx_click(path=None):
    n = int(0.09 * SR)
    t = np.arange(n) / SR
    r = np.random.default_rng(3)
    x = (r.normal(0, 1, n) * 0.5 + np.sin(2 * np.pi * 2200 * t) * 0.5)
    x *= np.exp(-58 * t)
    to_wav(path, x, peak=0.42)
    return path


def sfx_blip(freq=880, dur=0.16, path=None):
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = (np.sin(2 * np.pi * freq * t) + 0.35 * np.sin(4 * np.pi * freq * t))
    x *= np.exp(-16 * t) * adsr(n, 0.01, 0.1, 0.5, 0.4)
    to_wav(path, x, peak=0.35)
    return path


def sfx_impact(path=None):
    dur = 1.5
    n = int(dur * SR)
    t = np.arange(n) / SR
    r = np.random.default_rng(21)
    low = np.sin(2 * np.pi * 58 * t) * np.exp(-3.2 * t)
    air = r.normal(0, 1, n) * np.exp(-9 * t) * 0.3
    x = low * 0.8 + air
    x = reverb(x, mix=0.3)
    to_wav(path, x, peak=0.65)
    return path


if __name__ == '__main__':
    total = float(os.environ.get('BGM_SEC', '620'))
    p = build_bgm(total, f'{MUS}/bgm.wav')
    print('bgm ->', p, os.path.getsize(p))
    sfx_whoosh(path=f'{MUS}/whoosh.wav')
    sfx_click(path=f'{MUS}/click.wav')
    sfx_blip(880, path=f'{MUS}/blip.wav')
    sfx_blip(1320, path=f'{MUS}/blip2.wav')
    sfx_impact(path=f'{MUS}/impact.wav')
    print('sfx ok')
