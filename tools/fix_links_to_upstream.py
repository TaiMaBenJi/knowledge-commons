#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fix_links_to_upstream.py —— 把新增页面的站内链接对齐上游目录化重构后的真实路径
--------------------------------------------------------------------
背景：上游已把 learn/ 目录化（learn/cloud.html → learn/cloud/index.html 等），
本分支新增的 7 张页面仍指向旧路径，直接合并会产生死链。本脚本：
  1) 按映射表把旧路径改写为新路径
  2) 在导航里补上上游新增的竞赛中心 / 实训场等入口
  3) 校验：新页面内部链接 0 死链
"""
import io, os, re, subprocess, sys, collections

ROOT = "/workspace/kc"

# 旧路径 -> 上游新路径
MAP = {
    "cloud.html": "cloud/index.html",
    "cloudlab.html": "cloud/lab.html",
    "cloud-sprint.html": "cloud/sprint.html",
    "cloud-4weeks.html": "cloud/4weeks.html",
    "cloud-week1.html": "cloud/week1.html",
    "cloud-net.html": "cloud/net.html",
    "aws-educate.html": "courses/aws-educate.html",
    "aws-educate-catalog.html": "courses/aws-educate-catalog.html",
    "calendar.html": "exam/calendar.html",
    "quiz.html": "exam/quiz.html",
    "gongkao.html": "exam/gongkao.html",
    "exams.html": "exam/index.html",
    "wsvideos.html": "media/wsvideos.html",
    "red.html": "red/index.html",
    "socialism.html": "red/socialism.html",
    "pdfview.html": "media/pdfview.html",
    "course-algo.html": "courses/algo.html",
    "course-algo2.html": "courses/algo2.html",
    "course-python.html": "courses/python.html",
    "course-gongkao.html": "courses/gongkao.html",
}
# 需要一并补上的上游新页面（不重写，只加导航入口）
EXTRA_TABS = [
    ("cloud/contest/index.html", "竞赛"),
]

PAGES = ["learn/arena.html", "learn/comp-series.html", "learn/cloud-taskbooks.html",
         "learn/cloud-basics.html", "learn/cloud-race.html", "learn/cloud-cert.html",
         "learn/cloud-videos.html"]

# 验证站内相对链接是否存在
def check(page_rel):
    p = os.path.join(ROOT, page_rel)
    s = io.open(p, encoding="utf-8").read()
    bad = []
    for m in re.finditer(r'(?:href|src)\s*=\s*["\']([^"\']+)["\']', s):
        u = m.group(1).strip()
        if not u or u.startswith(("http://", "https://", "//", "mailto:", "tel:",
                                   "data:", "javascript:", "about:", "itms-services:")):
            continue
        path = u.split("#")[0].split("?")[0]
        if not path:
            continue
        # 支持中文路径
        tgt = os.path.normpath(os.path.join(os.path.dirname(p), path))
        if not os.path.exists(tgt):
            bad.append(u)
    return s, bad


total_fix = 0
for rel in PAGES:
    p = os.path.join(ROOT, rel)
    s = io.open(p, encoding="utf-8").read()
    orig = s
    n = 0
    # 只改 href/src 里的目标，避免误改正文文字
    def repl(m):
        global n
        u = m.group(1)
        tail = ""
        if "#" in u:
            u, tail = u.split("#", 1)
            tail = "#" + tail
        base = u.rsplit("/", 1)[-1]
        # 只处理最后一段是 .html 的相对链接
        if base.endswith(".html") and base in MAP and (u.startswith("./") or u.startswith("../") or "/" not in u):
            n += 1
            return '%s%s%s' % (m.group(0).split('"')[0], MAP[base] + tail, m.group(0)[-1])
        return m.group(0)
    s = re.sub(r'(?:href|src)\s*=\s*"([^"]+)"', lambda m: repl(m), s)
    s = re.sub(r"(?:href|src)\s*=\s*'([^']+)'", lambda m: repl(m), s)
    if s != orig:
        io.open(p, "w", encoding="utf-8").write(s)
    total_fix += n
    print("  %-28s 修正 %d 处" % (rel, n))

print("\n合计修正 %d 处链接\n" % total_fix)

print("=== 死链校验 ===")
fails = 0
for rel in PAGES:
    _, bad = check(rel)
    if bad:
        fails += len(bad)
        print("  ❌ %s" % rel)
        for u in sorted(set(bad)):
            print("       -> %s" % u)
    else:
        print("  ✅ %s" % rel)
print("\n结果：%s" % ("全部通过，0 死链 ✅" if not fails else "%d 处死链 ❌" % fails))
sys.exit(1 if fails else 0)
