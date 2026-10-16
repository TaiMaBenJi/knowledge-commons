#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
wire_upstream_links.py —— 把上游新增的竞赛中心 / 实训场接入本分支新页面
--------------------------------------------------------------------
上游在本分支基线之后新增了若干页面（learn/cloud/contest/、learn/cloud/lab.html、
learn/exam/、learn/media/）。本脚本：
  1) 在 7 张新页的导航里补上「竞赛中心」「实训场」入口
  2) 在作战台与赛情页加一张「两条路线」说明卡，讲清浏览器仿真 vs 真机环境的分工
  3) 校验 0 死链
"""
import io, os, re, sys

ROOT = "/workspace/kc"
PAGES = ["learn/arena.html", "learn/comp-series.html", "learn/cloud-taskbooks.html",
         "learn/cloud-basics.html", "learn/cloud-race.html", "learn/cloud-cert.html",
         "learn/cloud-videos.html"]

NAV_ADD = ('  <a href="cloud/contest/index.html">竞赛中心</a>\n'
           '  <a href="cloud/lab.html">实训场</a>\n')

TWO_ROUTES_CARD = '''
  <div class="goal"><b>两条路线，分工不同：</b>
  <a href="cloud/contest/index.html"><b>竞赛中心</b></a>是<b>真机路线</b>——7 套全真卷（国赛 / 广东 / 韩国 / 金砖 / 世赛 / 世职赛）配
  <a href="cloud/contest/env/README.md">OpenStack allinone 与 K8s 集群环境脚本</a>，要你手上有真集群，适合赛前集训；
  <a href="arena.html"><b>作战台</b></a>是<b>零依赖路线</b>——浏览器内虚拟服务器，<b>不用装任何东西、断网可跑</b>，
  判分由函数自动判定（含世赛里昂 2024 的 52 个官方 task 编号），适合随时随地刷分与复盘。
  <b>两条不冲突，建议先作战台、再竞赛中心。</b></div>
'''

changed = []
for rel in PAGES:
    p = os.path.join(ROOT, rel)
    s = io.open(p, encoding="utf-8").read()
    orig = s
    # 1) 导航补入口（幂等）
    if "cloud/contest/index.html" not in s:
        m = re.search(r'(<nav class="tabs">\n)', s)
        if m:
            s = s[:m.end()] + NAV_ADD + s[m.end():]
    # 2) 说明卡：只加在两个关键页
    if rel in ("learn/arena.html", "learn/cloud-race.html") and "两条路线，分工不同" not in s:
        m = re.search(r'(<div class="wrap">\n)', s)
        if m:
            s = s[:m.end()] + TWO_ROUTES_CARD + s[m.end():]
    if s != orig:
        io.open(p, "w", encoding="utf-8").write(s)
        changed.append(rel)

print("更新 %d 个页面：%s\n" % (len(changed), "、".join(os.path.basename(c) for c in changed)))

print("=== 死链校验 ===")
fails = 0
for rel in PAGES:
    p = os.path.join(ROOT, rel)
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
        tgt = os.path.normpath(os.path.join(os.path.dirname(p), path))
        if not os.path.exists(tgt):
            bad.append(u)
    if bad:
        fails += len(bad)
        print("  ❌ %s" % rel)
        for u in sorted(set(bad)):
            print("       -> %s" % u)
    else:
        print("  ✅ %s" % rel)
print("\n结果：%s" % ("0 死链 ✅" if not fails else "%d 处死链 ❌" % fails))
sys.exit(1 if fails else 0)
