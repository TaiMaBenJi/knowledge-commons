#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
extract_taskbooks.py —— 从国赛/省赛真题中抽取「模块 + 任务 + 分值」结构
--------------------------------------------------------------------
输入：study-data/c/examcn.f57bcd.js（154 篇国赛真题）
输出：
  docs/cloud/race-2026/taskbooks.json  结构化任务书（模块 / 任务 / 分值，原文值）
  docs/cloud/race-2026/taskbooks.md    人读版汇总

口径声明：
  · 分值均为**真题原文里的括号值**，不做归一化、不做补全。
  · 同一篇里原文可能重复罗列（PDF 提取常见），按「模块+任务名」去重。
  · 某些卷子摘录不全（各模块分值之和 < 100），这是**原文如此**，不是抽取错误。
"""
import io, json, os, re, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "study-data", "c", "examcn.f57bcd.js")
OUTD = os.path.join(ROOT, "docs", "cloud", "race-2026")
os.makedirs(OUTD, exist_ok=True)

CN = "一二三四五六七八九十"
MOD_RE = re.compile(r"^\s*模块\s*([%s\d]+)\s*(.{0,40}?)\s*[（(]?\s*(\d{1,3}(?:\.\d+)?)\s*分?\s*[%%％]?\s*[）)]?\s*$" % CN)
TASK_RE = re.compile(r"^\s*(?:任务|作业|子任务)\s*([%s\d]+)\s*(.{0,60}?)\s*[（(]?\s*(\d{1,3}(?:\.\d+)?)\s*分?\s*[%%％]?\s*[）)]?\s*$" % CN)


def strip_html(h):
    h = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", h, flags=re.S | re.I)
    h = re.sub(r"<br\s*/?>", "\n", h, flags=re.I)
    h = re.sub(r"</(p|div|li|tr|h[1-6]|td)>", "\n", h, flags=re.I)
    h = re.sub(r"<[^>]+>", "", h)
    for a, b in [("&nbsp;", " "), ("&amp;", "&"), ("&lt;", "<"), ("&gt;", ">"),
                 ("&quot;", '"'), ("&#39;", "'")]:
        h = h.replace(a, b)
    h = re.sub(r"[ \t　]+", " ", h)
    return re.sub(r"\n{3,}", "\n\n", h).strip()


s = io.open(SRC, encoding="utf-8").read()
i = s.index('window.__kcChunk("examcn",') + len('window.__kcChunk("examcn",')
chunks = json.JSONDecoder().raw_decode(s[i:])[0]

books = []
for k, html in chunks.items():
    t = strip_html(html)
    lines = [l.strip() for l in t.split("\n") if l.strip()]
    mods, cur = [], None
    for l in lines:
        mm = MOD_RE.match(l)
        if mm:
            name0 = mm.group(2).strip("：:、.（）() ")
            # 「任务 1. xxx」这类行会被模块正则误吃，这里显式排除
            if re.match(r"^(任务|作业|子任务)\s*\d*\s*[.、:：]?", name0):
                mt0 = TASK_RE.match(l)
                if mt0 and cur is not None:
                    nm = re.sub(r"[（(]\s*\d+\s*分?\s*[)）]", "", mt0.group(2)).strip("：:、.（）() ")
                    if nm and not any(x["t"] == nm for x in cur["tasks"]):
                        cur["tasks"].append({"id": mt0.group(1), "t": nm, "p": float(mt0.group(3))})
                continue
            nm = re.sub(r"[（(]\s*\d+\s*分?\s*[)）]", "", name0)
            nm = re.sub(r"^(任务|作业|子任务)\s*\d*\s*[.、:：]\s*", "", nm).strip("：:、. ")
            mid = mm.group(1)
            if not re.match(r"^([%s]|\d+)$" % CN, mid):
                mid = re.sub(r"\d+$", "", mid) or mid
            cur = {"id": mid, "t": nm, "p": float(mm.group(3)), "tasks": []}
            if not any(x["id"] == cur["id"] and x["t"] == cur["t"] for x in mods):
                mods.append(cur)
            continue
        mt = TASK_RE.match(l)
        if mt and cur is not None:
            name = re.sub(r"[（(]\s*\d+\s*分?\s*[)）]", "", mt.group(2)).strip("：:、.（）() ")
            if not name:
                continue
            if not any(x["t"] == name for x in cur["tasks"]):
                cur["tasks"].append({"id": mt.group(1), "t": name, "p": float(mt.group(3))})
    if not mods:
        continue
    yrs = re.findall(r"(20[12]\d)", k)
    prov = re.findall(r"(\d{2,3})省|北京市|上海市|天津市|重庆市|内蒙古|广西|西藏|宁夏|新疆|贵州|云南|辽宁|山东|河南|河北|湖南|湖北|江苏|浙江|安徽|福建|江西|四川|云南|陕西|甘肃|青海|吉林|黑龙江|山西|内蒙古", k)
    books.append({
        "id": k,
        "title": re.sub(r"^中国国赛真题.*?篇\s*", "", t.split("\n")[0])[:140],
        "year": yrs[0] if yrs else None,
        "region": prov[0] if prov else None,
        "modules": mods,
        "sum_mod": round(sum(m["p"] for m in mods), 1),
        "n_mod": len(mods),
        "n_task": sum(len(m["tasks"]) for m in mods),
    })

# 跨卷聚合：同名模块的分值分布
mod_agg = collections.defaultdict(list)
task_agg = collections.defaultdict(list)
for b in books:
    for m in b["modules"]:
        mod_agg[(m["id"], m["t"])].append(m["p"])
        for tk in m["tasks"]:
            task_agg[tk["t"]].append(tk["p"])

data = {
    "generated": "2026-10-16",
    "source": "study-data/c/examcn.f57bcd.js",
    "disclaimer": "分值均为真题原文括号值，未归一化；部分卷子为节选，模块分值之和可能不足 100。",
    "total_books": len(books),
    "books": books,
    "module_agg": [{"id": k[0], "t": k[1], "hits": len(v), "p_min": min(v), "p_max": max(v),
                    "p_avg": round(sum(v) / len(v), 1)} for k, v in mod_agg.items()],
    "task_agg": [{"t": k, "hits": len(v), "p_min": min(v), "p_max": max(v),
                  "p_avg": round(sum(v) / len(v), 1)} for k, v in task_agg.items()],
}
io.open(os.path.join(OUTD, "taskbooks.json"), "w", encoding="utf-8").write(
    json.dumps(data, ensure_ascii=False, indent=1))

L = ["# 国赛 / 省赛真题「任务书」结构汇总", "",
     "> 生成 2026-10-16　来源 `study-data/c/examcn.f57bcd.js`",
     "> 分值均为**真题原文括号里的数字**，未归一化、未补全。部分卷子是节选，模块分值之和可能不足 100。", "",
     "## 概览", "",
     f"- 抽出结构化任务书的真题：**{len(books)}** 篇",
     f"- 涉及模块：**{len(mod_agg)}** 种；任务条目：**{len(task_agg)}** 种", ""]

L += ["## 一、模块分值（跨卷同名模块的取值范围）", "",
      "| 模块 | 出现卷数 | 分值范围 | 均值 |", "|---|---:|---|---:|"]
for m in sorted(data["module_agg"], key=lambda x: -x["hits"])[:60]:
    rng = ("%g" % m["p_min"]) if m["p_min"] == m["p_max"] else ("%g ~ %g" % (m["p_min"], m["p_max"]))
    L.append("| %s %s | %d | %s | %g |" % (m["id"], m["t"], m["hits"], rng, m["p_avg"]))

L += ["", "## 二、高频任务（跨卷同名任务）", "",
      "| 任务 | 出现卷数 | 分值范围 | 均值 |", "|---|---:|---|---:|"]
for m in sorted(data["task_agg"], key=lambda x: -x["hits"])[:60]:
    rng = ("%g" % m["p_min"]) if m["p_min"] == m["p_max"] else ("%g ~ %g" % (m["p_min"], m["p_max"]))
    L.append("| %s | %d | %s | %g |" % (m["t"], m["hits"], rng, m["p_avg"]))

L += ["", "## 三、逐篇任务书", ""]
for b in sorted(books, key=lambda x: (x["year"] or "", x["title"])):
    L.append("### %s%s" % ((b["year"] + "　") if b["year"] else "", b["title"][:80]))
    L.append("")
    L.append("> %d 个模块 · %d 个任务 · 模块分值合计 %g"
             % (b["n_mod"], b["n_task"], b["sum_mod"]))
    L.append("")
    L.append("| 模块 | 模块分 | 任务 | 任务分 |")
    L.append("|---|---:|---|---|")
    for m in b["modules"]:
        if not m["tasks"]:
            L.append("| %s %s | %g | （原文未列任务明细） | — |" % (m["id"], m["t"], m["p"]))
        else:
            L.append("| %s %s | %g | %s | %s |" % (
                m["id"], m["t"], m["p"],
                " / ".join(tk["t"] for tk in m["tasks"]),
                " / ".join("%g" % tk["p"] for tk in m["tasks"])))
    L.append("")

io.open(os.path.join(OUTD, "taskbooks.md"), "w", encoding="utf-8").write("\n".join(L))

print("抽出任务书 %d 篇；模块种类 %d；任务种类 %d" % (len(books), len(mod_agg), len(task_agg)))
print("\n模块分值 Top 20：")
for m in sorted(data["module_agg"], key=lambda x: -x["hits"])[:20]:
    print("  %2d. %s %-28s %2d 卷  %g~%g 分" % (len(m["t"]), m["id"], m["t"][:28], m["hits"], m["p_min"], m["p_max"]))
print("\n高频任务 Top 20：")
for m in sorted(data["task_agg"], key=lambda x: -x["hits"])[:20]:
    print("  %2d. %-34s %2d 卷  %g~%g 分" % (len(m["t"]), m["t"][:34], m["hits"], m["p_min"], m["p_max"]))
