#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
extract_cn_corpus.py —— 中国国赛真题语料分析
--------------------------------------------------------------------
输入：study-data/c/examcn.f57bcd.js（154 篇国赛真题正文）
输出：
  docs/cloud/race-2026/cn-corpus.json   结构化语料（技术栈命中 / 赛项 / 年份 / 竞赛时长）
  docs/cloud/race-2026/cn-corpus.md     人读版：考点热度矩阵 + 分布统计

诚实声明（重要）：
  · 「技术栈命中」= 全文出现该关键词的篇数，**不等于**该考点占多少分
  · 国赛真题绝大多数是**题面 + 技术栈描述**，**没有**像世赛里昂那样的官方
    `task_XXX_XX` 评分编号体系；全库仅 2 篇带「模块 + 权重」分布
  · 因此本脚本**不编造**任何权重数字，只统计可验证的文本命中
"""
import io, json, os, re, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "study-data", "c", "examcn.f57bcd.js")
OUTD = os.path.join(ROOT, "docs", "cloud", "race-2026")
os.makedirs(OUTD, exist_ok=True)

STACK = {
    "OpenStack 私有云": r"OpenStack|openstack|nova\b|neutron|cinder|keystone|glance|swift",
    "Docker 容器": r"docker|Docker|容器化|dockerfile|compose",
    "Kubernetes 编排": r"kubernetes|Kubernetes|k8s|K8s|kubectl|helm|部署清单|deployment\.yaml",
    "Ansible 自动化": r"ansible|Ansible|playbook|自动化运维|批量配置",
    "Nginx / Web 服务": r"nginx|Nginx|apache|httpd|web ?服务|网站部署",
    "MySQL / 数据库": r"mysql|MySQL|mariadb|数据库|psql|postgresql",
    "负载均衡 / HA": r"haproxy|HAProxy|keepalived|负载均衡|高可用|双机热备|lvs",
    "Python 脚本": r"python|Python|python3|脚本编程",
    "网络基础": r"vlan|VLAN|子网|ospf|OSPF|路由|交换机|防火墙|acl|ACL",
    "云平台运维": r"云平台|公有云|私有云|混合云|云主机|云桌面|对象存储",
    "监控 / 日志": r"zabbix|Zabbix|prometheus|监控|日志分析|巡检",
    "综合布线": r"综合布线|线缆|跳线|机柜|配线架",
    "存储": r"ceph|CEPH|san\b|存储|nas\b|共享存储",
    "备份 / 容灾": r"备份|容灾|恢复|rsync",
    "GIT / 版本管理": r"git\b|Git|GIT|版本管理",
    "Windows Server / AD": r"Windows Server|Active Directory|域控|ADDS|GPO",
    "Linux 基础": r"linux|Linux|centos|CentOS|ubuntu|Ubuntu|命令行",
}
STRUCT = {
    "模块+权重分布": r'模块[一二三四五六七八九十\d]+\s*[：:].*?\d+\s*[%％]',
    "评分标准/评分细则": r"评分标准|评分细则|评分点|配分",
    "任务书": r"任务书|Task\s*\d|任务\s*\d",
    "环境/拓扑说明": r"环境说明|网络拓扑|拓扑图|设备清单|逻辑拓扑",
    "解题步骤": r"解题步骤|操作步骤|命令如下|实施步骤|参考步骤",
}
SKILL_HINT = [
    ("云计算应用", r"云计算应用"),
    ("云计算", r"云计算"),
    ("网络应用", r"网络应用|计算机网络"),
    ("OpenStack", r"OpenStack"),
    ("大数据", r"大数据|hadoop|Hadoop|spark|Spark"),
    ("信息安全管理", r"信息安全|网络安全|渗透"),
    ("其他/未判定", r"$^"),
]


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


def load():
    s = io.open(SRC, encoding="utf-8").read()
    i = s.index('window.__kcChunk("examcn",') + len('window.__kcChunk("examcn",')
    return json.JSONDecoder().raw_decode(s[i:])[0]


TIME_RE = re.compile(r"竞赛时间[为是]?\s*(\d+(?:\.\d+)?)\s*个?\s*小时")
TIME_RE2 = re.compile(r"(\d+(?:\.\d+)?)\s*小时")
MOD_RE = re.compile(r'^\s*模块\s*([一二三四五六七八九十\d]+)\s*[：:]\s*(.{0,60}?)\s*[（(]?\s*(\d{1,2}(?:\.\d+)?)\s*[%％]')

docs = []
for k, html in load().items():
    t = strip_html(html)
    yrs = re.findall(r"(20[12]\d)", k)
    skill = next((n for n, p in SKILL_HINT if n != "其他/未判定" and re.search(p, k + " " + t[:300])), "其他/未判定")
    tm = TIME_RE.search(t) or TIME_RE2.search(t[:3000])
    mods = []
    for line in t.split("\n"):
        mm = MOD_RE.match(line.strip())
        if mm:
            mods.append({"id": mm.group(1), "t": mm.group(2).strip("：:、. "), "w": float(mm.group(3))})
    docs.append({
        "id": k,
        "title": re.sub(r"^中国国赛真题.*?篇\s*", "", t.split("\n")[0])[:140],
        "year": yrs[0] if yrs else None,
        "skill": skill,
        "duration_h": float(tm.group(1)) if tm else None,
        "chars": len(t),
        "stack": [n for n, p in STACK.items() if re.search(p, t)],
        "struct": [n for n, p in STRUCT.items() if re.search(p, t)],
        "modules": mods,
    })

n = len(docs)
stack_hit = {k: sum(1 for d in docs if k in d["stack"]) for k in STACK}
struct_hit = {k: sum(1 for d in docs if k in d["struct"]) for k in STRUCT}
skill_cnt = collections.Counter(d["skill"] for d in docs)
year_cnt = collections.Counter(d["year"] or "未标年份" for d in docs)
dur = collections.Counter(d["duration_h"] for d in docs if d["duration_h"])
rich = [d for d in docs if d["modules"]]

data = {
    "generated": "2026-10-16",
    "source": "study-data/c/examcn.f57bcd.js",
    "disclaimer": ("技术栈命中＝全文出现该关键词的篇数，不代表该考点分值；"
                   "国赛真题无世赛里昂那样的官方 task_XXX_XX 评分编号体系，本数据不编造权重。"),
    "total": n,
    "stack_hits": stack_hit,
    "struct_hits": struct_hit,
    "skill_dist": dict(skill_cnt),
    "year_dist": dict(sorted(year_cnt.items())),
    "duration_dist": {str(k): v for k, v in sorted(dur.items())},
    "with_module_weights": [{"title": d["title"], "year": d["year"], "modules": d["modules"]} for d in rich],
    "docs": docs,
}
io.open(os.path.join(OUTD, "cn-corpus.json"), "w", encoding="utf-8").write(
    json.dumps(data, ensure_ascii=False, indent=1))

L = ["# 中国国赛真题语料分析（154 篇）", "",
     "> 生成 2026-10-16　来源 `study-data/c/examcn.f57bcd.js`", "",
     "> ⚠️ **口径声明**：「技术栈命中」指该关键词在全文出现，**不等于**该考点占多少分。",
     "> 国赛真题以**题面 + 技术栈描述**为主，**没有**世赛里昂那样的官方 `task_XXX_XX` 评分编号体系；",
     f"> 154 篇里只有 **{len(rich)} 篇**带「模块 + 权重」分布。本页不编造任何权重数字。", "",
     "## 1. 技术栈出现频次（%d 篇中）" % n, "",
     "| 排名 | 技术栈 | 命中篇数 | 占比 |", "|---:|---|---:|---:|"]
for i, (k, v) in enumerate(sorted(stack_hit.items(), key=lambda kv: -kv[1]), 1):
    L.append("| %d | %s | %d | %.0f%% |" % (i, k, v, v * 100.0 / n))
L += ["", "## 2. 结构性内容覆盖", "",
      "| 内容 | 篇数 | 说明 |", "|---|---:|---|"]
EXPL = {"模块+权重分布": "唯一能拿到官方权重的类型，但极少",
        "评分标准/评分细则": "国赛卷多数不给评分表",
        "任务书": "部分省赛样题按任务书形式给分",
        "环境/拓扑说明": "含拓扑或设备清单的卷子",
        "解题步骤": "附答案解析的卷子"}
for k, v in sorted(struct_hit.items(), key=lambda kv: -kv[1]):
    L.append("| %s | %d | %s |" % (k, v, EXPL.get(k, "")))
L += ["", "## 3. 赛项方向分布", "", "| 方向 | 篇数 |", "|---|---:|"]
for k, v in skill_cnt.most_common():
    L.append("| %s | %d |" % (k, v))
L += ["", "## 4. 年份分布", "", "| 年份 | 篇数 |", "|---|---:|"]
for k, v in sorted(year_cnt.items()):
    L.append("| %s | %d |" % (k, v))
L += ["", "## 5. 竞赛时长分布（原文抽到）", "", "| 时长 | 篇数 |", "|---|---:|"]
for k, v in sorted(dur.items()):
    L.append("| %s 小时 | %d |" % (k, v))
L += ["", "## 6. 带「模块 + 权重」的真题（全部 %d 篇）" % len(rich), ""]
if rich:
    L += ["| 年份 | 篇名 | 模块权重 |", "|---|---|---|"]
    for d in rich:
        ms = "；".join("%s %s %g%%" % (m["id"], m["t"], m["w"]) for m in d["modules"])
        L.append("| %s | %s | %s |" % (d["year"] or "", d["title"][:60], ms))
else:
    L.append("（无）")
L += ["", "## 7. 该怎么用这份数据", "",
      "· **备考选题**：出现频次最高的技术栈（OpenStack / Docker / Kubernetes / Ansible）就是国赛真题最常落地的地方，",
      "  对着这四项练性价比最高。",
      "· **别误解**：频次高 ≠ 分值高。国赛各卷的「竞赛内容分布」只有极少数卷子写明，",
      "  剩下的无法从原文推出权重——<b>不要拿频次当分值用</b>。",
      "· **想要真正的官方评分编号**，只有世赛里昂 2024 那一套（52 个 `task_XXX_XX`），",
      "  已在 <a href=\"../cloud-series.md\">课程第 2 讲</a> 与作战台仿真场中落地。", ""]

io.open(os.path.join(OUTD, "cn-corpus.md"), "w", encoding="utf-8").write("\n".join(L))

print("扫描 %d 篇" % n)
print("\n技术栈命中 Top 10：")
for i, (k, v) in enumerate(sorted(stack_hit.items(), key=lambda kv: -kv[1])[:10], 1):
    print("  %2d. %-22s %3d 篇 (%.0f%%)" % (i, k, v, v * 100.0 / n))
print("\n结构覆盖：", dict(struct_hit))
print("带模块权重：", len(rich), "篇")
print("赛项分布：", dict(skill_cnt.most_common()))
print("\n输出：cn-corpus.json / cn-corpus.md")
