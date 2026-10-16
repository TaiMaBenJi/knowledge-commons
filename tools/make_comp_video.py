#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
make_comp_video.py —— 竞赛课程视频生成器（中文配音 + 硬字幕）
=====================================================================
用真实赛制内容生成「有声音、有字幕、离线可看」的课程视频：

  · 配音：edge-tts 神经网络中文语音（zh-CN-YunxiNeural），逐句合成并按句切片
  · 画面：PIL 渲染 1280x720（标题 / 要点 / 角标 / 进度条 / 硬字幕）
  · 合成：ffmpeg 拼帧 + 拼音频
  · 字幕：直接烧进画面（不依赖 ffmpeg 字体配置，中文永不出方块）

用法：
  python3 tools/make_comp_video.py <content.json> <out.mp4>

content.json 格式：
  {"title":"...","subtitle":"...","theme":"red|blue|gold|green",
   "scenes":[{"h":"小标题","b":["要点1","要点2"],"n":"旁白文本（可多句，用 \n 分句）"}]}

依赖：pillow、edge-tts、ffmpeg/ffprobe、Noto Sans CJK
"""
import asyncio, json, os, re, ssl, subprocess, sys, tempfile, shutil

# ---- 沙箱/内网环境常用自签 CA 做 HTTPS 中间人，这里统一放开校验 ----
# 仅影响本脚本自身的网络调用（edge-tts 取音频），不改动系统证书库。
def _relax_ssl():
    try:
        ssl._create_default_https_context = ssl._create_unverified_context
    except Exception:
        pass
    try:
        import aiohttp
        _orig = aiohttp.TCPConnector.__init__

        def _patched(self, *a, **kw):
            kw.setdefault("ssl", False)
            return _orig(self, *a, **kw)

        aiohttp.TCPConnector.__init__ = _patched
    except Exception:
        pass


_relax_ssl()

from PIL import Image, ImageDraw, ImageFont

FONT_DIRS = ["/usr/share/fonts/opentype/noto", "/usr/share/fonts/truetype/noto",
             "/usr/share/fonts/opentype/noto-cjk", "/mnt/sysfonts"]


def find_font(bold=False):
    names = ["NotoSansCJK-Bold.ttc", "NotoSansCJK-Regular.ttc"] if bold else \
            ["NotoSansCJK-Regular.ttc", "NotoSansCJK-Bold.ttc"]
    for d in FONT_DIRS:
        for n in names:
            p = os.path.join(d, n)
            if os.path.exists(p):
                return p
    # 兜底：任意 CJK
    for d in FONT_DIRS:
        if not os.path.isdir(d):
            continue
        for f in os.listdir(d):
            if f.lower().endswith((".ttc", ".ttf", ".otf")) and ("cjk" in f.lower() or "wqy" in f.lower() or "noto" in f.lower()):
                return os.path.join(d, f)
    raise SystemExit("找不到中文字体")


FONT_R = find_font(False)
FONT_B = find_font(True)
W, H = 1280, 720
FPS = 25

THEMES = {
    "red":   ((19, 42, 82), (158, 43, 37), (240, 232, 216)),
    "blue":  ((14, 34, 62), (31, 93, 140), (226, 238, 248)),
    "gold":  ((46, 34, 14), (150, 108, 30), (247, 238, 214)),
    "green": ((14, 40, 26), (60, 110, 72), (228, 242, 230)),
}


def F(size, bold=False):
    return ImageFont.truetype(FONT_B if bold else FONT_R, size)


def wrap(draw, text, font, maxw):
    """按像素宽度折行（中英混排安全）"""
    lines, cur = [], ""
    for ch in text:
        t = cur + ch
        if draw.textlength(t, font=font) <= maxw:
            cur = t
        else:
            if cur:
                lines.append(cur)
            cur = ch
    if cur:
        lines.append(cur)
    return lines


def split_sentences(text):
    parts = [p.strip() for p in re.split(r"(?<=[。！？；!?;\n])", str(text)) if p.strip()]
    return parts or [str(text)]


# ---------------------------------------------------------------- TTS
# 双引擎：优先 edge-tts（神经网络音色最好），不可用时自动回落到百度翻译 TTS。
# 两者都走公网；若两者皆不可用，会明确报错而不是静默生成无声视频。
BAIDU_TTS = "https://fanyi.baidu.com/gettts?lan=zh&text=%s&spd=%d&source=web"
ENGINE = {"name": None}


def _ssl_ctx():
    import ssl as _s
    c = _s.create_default_context()
    c.check_hostname = False
    c.verify_mode = _s.CERT_NONE
    return c


async def _tts_edge(parts, work, voice, rate):
    import edge_tts
    import edge_tts.communicate as C
    import aiohttp
    C._SSL_CTX = _ssl_ctx()          # edge-tts 硬编码了 _SSL_CTX，必须替换
    out = []
    for i, p in enumerate(parts):
        f = os.path.join(work, "t%03d.mp3" % i)
        last = None
        for _ in range(3):
            try:
                c = edge_tts.Communicate(p, voice, rate=rate)
                await c.save(f)
                if os.path.getsize(f) > 800:
                    out.append(f)
                    return out
                last = "返回体过小"
            except Exception as e:
                last = "%s: %s" % (type(e).__name__, str(e)[:70])
        raise RuntimeError(last or "edge-tts 失败")
    return out


def _tts_baidu(text, spd=5):
    import urllib.parse, urllib.request
    url = BAIDU_TTS % (urllib.parse.quote(text), spd)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    d = urllib.request.urlopen(req, timeout=40, context=_ssl_ctx()).read()
    return d


def _tts_baidu_sync(parts, work):
    out = []
    for i, p in enumerate(parts):
        f = os.path.join(work, "t%03d.mp3" % i)
        data = _tts_baidu(p)
        with open(f, "wb") as fh:
            fh.write(data)
        # 用 ffprobe 验证确实是可解码的音频，而不是一段错误页
        if os.path.getsize(f) < 600 or mp3_dur(f) <= 0.05:
            raise RuntimeError("百度 TTS 第 %d 段无效（%d 字节 / 时长 %s）"
                               % (i, os.path.getsize(f), mp3_dur(f)))
        out.append(f)
    return out


async def synth(parts, work, voice="zh-CN-YunxiNeural", rate="-8%"):
    if ENGINE["name"] in (None, "edge-tts"):
        try:
            files = await _tts_edge(parts, work, voice, rate)
            ENGINE["name"] = "edge-tts（%s）" % voice
            return files
        except Exception as e:
            print("    ! edge-tts 不可用（%s），回落到百度翻译 TTS" % str(e)[:70])
    files = await asyncio.get_event_loop().run_in_executor(None, _tts_baidu_sync, parts, work)
    ENGINE["name"] = "百度翻译 TTS"
    return files


def mp3_dur(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "default=nw=1:nk=1", path], capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except Exception:
        return 0.0


# ---------------------------------------------------------------- 画面
def draw_scene(draw, im, data, idx, total, t_in_scene, dur):
    bg, accent, panel = THEMES[data.get("theme", "red")]
    draw.rectangle([0, 0, W, H], fill=bg)

    # 顶部标题条
    draw.rectangle([0, 0, W, 92], fill=accent)
    draw.text((46, 24), data["title"], font=F(34, True), fill="#fdf8ef")
    st = data.get("subtitle", "")
    if st:
        draw.text((W - 46 - draw.textlength(st, font=F(20)), 38), st,
                  font=F(20), fill="#f3e2cf")

    # 章节小标题
    sc = data["scenes"][idx]
    draw.rounded_rectangle([46, 128, 46 + draw.textlength(sc["h"], font=F(30, True)) + 40,
                            128 + 54], radius=8, fill=accent)
    draw.text((66, 140), sc["h"], font=F(30, True), fill="#fdf8ef")

    # 要点卡
    y = 216
    fB = F(25)
    for b in sc.get("b", []):
        lines = wrap(draw, b, fB, W - 190)
        hgt = 34 * len(lines) + 30
        draw.rounded_rectangle([46, y, W - 46, y + hgt], radius=10, fill=panel)
        draw.ellipse([70, y + hgt // 2 - 7, 84, y + hgt // 2 + 7], fill=accent)
        yy = y + 15
        for ln in lines:
            draw.text((104, yy), ln, font=fB, fill=(30, 26, 22))
            yy += 34
        y += hgt + 14
        if y > H - 190:
            break

    # 进度条
    draw.rectangle([46, H - 34, W - 46, H - 28], fill=(255, 255, 255, 40))
    p = (idx + (t_in_scene / dur if dur else 0)) / total
    draw.rectangle([46, H - 34, 46 + int((W - 92) * min(1, p)), H - 28], fill=accent)

    # 页码
    pg = "%d / %d" % (idx + 1, total)
    draw.text((W - 46 - draw.textlength(pg, font=F(19)), H - 66), pg, font=F(19), fill=(210, 198, 180))

    # 角标
    tag = "知识公社 · 云计算备赛"
    draw.text((46, H - 66), tag, font=F(19), fill=(150, 138, 120))


def draw_sub(draw, im, text):
    """底部硬字幕（烧进画面，中文永不出方块）"""
    if not text:
        return
    f = F(30, True)
    lines = wrap(draw, text, f, W - 220)
    if len(lines) > 2:
        lines = lines[:2]
    bh = 16 + 40 * len(lines)
    y0 = H - bh - 74
    draw.rectangle([0, y0, W, H - 74], fill=(0, 0, 0))
    yy = y0 + 8
    for ln in lines:
        x = (W - draw.textlength(ln, font=f)) / 2
        # 描边提升可读性
        for dx, dy in ((-2, 0), (2, 0), (0, -2), (0, 2)):
            draw.text((x + dx, yy + dy), ln, font=f, fill=(0, 0, 0))
        draw.text((x, yy), ln, font=f, fill=(255, 255, 255))
        yy += 40


# ---------------------------------------------------------------- 主流程
async def build(content_path, out_path):
    data = json.load(open(content_path, encoding="utf-8"))
    scenes = data["scenes"]
    work = tempfile.mkdtemp(prefix="compvid_")
    try:
        # 1) 逐场景合成旁白
        print("  · 合成配音（%d 个场景）" % len(scenes))
        all_durs, all_files = [], []
        for i, sc in enumerate(scenes):
            sents = split_sentences(sc.get("n", ""))
            files = await synth(sents, work, rate=data.get("rate", "-8%"))
            durs = [mp3_dur(f) for f in files]
            all_files.append(files)
            all_durs.append(durs)
            print("    [%d/%d] %s — %d 句 / %.1fs"
                  % (i + 1, len(scenes), sc["h"], len(sents), sum(durs)))

        # 2) 渲染：每个「场景 × 句子」只渲一张静帧，再由 ffmpeg 按秒数复制。
        #    （逐帧渲染 1280x720 极慢；本项目总时长可达数分钟，帧级渲染会拖到分钟级）
        print("  · 渲染静帧（PIL 1280x720）")
        fdir = os.path.join(work, "f")
        os.makedirs(fdir)
        segs = []
        for i, sc in enumerate(scenes):
            files, durs = all_files[i], all_durs[i]
            sents = split_sentences(sc.get("n", ""))
            idle = 0.9
            segs.append((files, durs, idle))
            im = Image.new("RGB", (W, H), (0, 0, 0))
            d = ImageDraw.Draw(im)
            seg = 0
            while seg <= len(sents):
                dur = durs[seg] if seg < len(durs) else idle
                text = sents[seg] if seg < len(sents) else ""
                t0 = sum(durs[:seg]) if seg < len(durs) else sum(durs)
                draw_scene(d, im, data, i, len(scenes), t0, (sum(durs) + idle))
                draw_sub(d, im, text)
                name = "%04d.png" % len(os.listdir(fdir))
                im.save(os.path.join(fdir, name))
                seg += 1
        print("    静帧 %d 张" % len(os.listdir(fdir)))

        # 3) 拼帧：concat 清单 + 每张图的停留时长
        vdir = os.path.join(work, "v.mp4")
        pngs = sorted(os.listdir(fdir))
        clist = []
        k = 0
        for i, (files, durs, idle) in enumerate(segs):
            n = len(scenes) and len(split_sentences(scenes[i].get("n", ""))) or 1
            n += 1
            for j in range(n):
                dur = durs[j] if j < len(durs) else idle
                clist.append("file '%s'" % os.path.join(fdir, pngs[k]))
                clist.append("duration %.3f" % dur)
                k += 1
        clist.append("file '%s'" % os.path.join(fdir, pngs[-1]))   # concat 末帧需重复
        _tot = sum(float(d.split()[1]) for d in clist if d.startswith("duration "))
        _files = sum(1 for d in clist if d.startswith("file "))
        print("    concat 清单：%d 张图 / %d 条 file / 标注总时长 %.1fs" % (len(pngs), _files, _tot))
        with open(os.path.join(work, "vlist.txt"), "w") as f:
            f.write("\n".join(clist) + "\n")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
                        "-i", os.path.join(work, "vlist.txt"),
                        "-vf", "scale=%d:%d:force_original_aspect_ratio=decrease,"
                               "pad=%d:%d:(ow-iw)/2:(oh-ih)/2,setsar=1" % (W, H, W, H),
                        "-r", str(FPS), "-c:v", "libx264", "-preset", "medium",
                        "-crf", "23", "-pix_fmt", "yuv420p", vdir], check=True)
        print("  · 配音引擎：%s" % (ENGINE["name"] or "未知"))

        # 4) 拼音频：每场景（多句顺序 + 尾部静默垫片）各自成段，再 concat
        apath = os.path.join(work, "a.m4a")
        parts = []
        for i, (files, durs, idle) in enumerate(segs):
            cmd = ["ffmpeg", "-y", "-loglevel", "error"]
            for f in files:
                cmd += ["-i", f]
            # 注意：这里必须用「有界」的 aevalsrc，不能用 anullsrc。
            # anullsrc 是无限流，进 concat filter 后整段音频会塌成静音垫片的长度。
            cmd += ["-f", "lavfi", "-i", "aevalsrc=0:d=%.3f:s=44100" % idle]
            AF = "aresample=44100,aformat=sample_fmts=fltp:sample_rates=44100:channel_layouts=mono"
            chains = ["[%d:a]%s,apad,atrim=0:%.3f[a%d]" % (k, AF, durs[k], k)
                      for k in range(len(files))]
            chains.append("[%d:a]%s,atrim=0:%.3f[s%d]" % (len(files), AF, idle, len(files)))
            labels = ["[a%d]" % k for k in range(len(files))] + ["[s%d]" % len(files)]
            # 关键：必须把各段真正串起来，只映射最后一段会导致其余滤镜输出悬空而报错
            chains.append("%sconcat=n=%d:v=0:a=1[out]" % ("".join(labels), len(labels)))
            fl = ";".join(chains)
            out = os.path.join(work, "p%03d.m4a" % i)
            cmd += ["-filter_complex", fl, "-map", "[out]",
                    "-c:a", "aac", "-b:a", "96k", out]
            subprocess.run(cmd, check=True)
            parts.append(out)
        with open(os.path.join(work, "list.txt"), "w") as f:
            for p in parts:
                f.write("file '%s'\n" % p)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
                        "-i", os.path.join(work, "list.txt"),
                        "-c:a", "aac", "-b:a", "128k", apath], check=True)

        # 5) 合成
        os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", vdir, "-i", apath,
                        "-c:v", "copy", "-c:a", "aac", "-b:a", "128k", "-shortest",
                        "-movflags", "+faststart", out_path], check=True)

        # 6) 质检
        r = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                            "format=duration,size:stream=codec_name,width,height,nb_frames",
                            "-of", "default=nw=1", out_path], capture_output=True, text=True)
        print("  · 质检输出：\n" + "\n".join("      " + l for l in r.stdout.strip().split("\n")))
        return out_path
    finally:
        if os.environ.get("KEEP_WORK"):
            print("  · 中间产物保留于 %s" % work)
        else:
            shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        raise SystemExit(__doc__)
    src, dst = sys.argv[1], sys.argv[2]
    print("生成视频：%s -> %s" % (src, dst))
    asyncio.run(build(src, dst))
    print("✅ 完成：%s（%.1f MB）" % (dst, os.path.getsize(dst) / 1024 / 1024))
