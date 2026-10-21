#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
add_study_docs.py · 往资料中心增量插入新文档（不动既有 3160 篇）

为什么需要这个工具
------------------
本仓库的资料中心是**生成物**：study.html 拆成 study-data/manifest.<hash>.js +
study-data/c/<组>.<hash>.js 两层，manifest 的每条记录是
    [t, g, gk, m, c, f, chunkSlug]      ← 7 个元素，第 7 个是所属内容块
（tools/split_study.py 的 o._ck = a[n] 就是取它。）

全量重建的入口是 tools/build_liquid.py，但**它复现不出当前这 3160 篇**：
其中约 2900 篇来自 github-repos/ 与 test-projects/ 两个目录，
而这两个目录在 2026-10-16 的 learn/ 目录整理中已不再随仓库分发，
它们的正文只剩下 study-data/c/*.js 里的 HTML 成品。
换句话说：**全量重建 = 静默删掉 2900 篇文档**。

所以这里提供增量通道：只把新增文档追加进既有 manifest 与内容块，
既有 3160 篇一个字节都不动。约定完全对齐上游：
  · 文档 id      = rel.replace('/', '_').replace('.', '_')
  · 阅读时长 m   = max(3, round(len(raw) / 400))
  · 组 slug      = slugify(gk)，与 tools/split_study.py 同一套去重规则
  · manifest 文件名 = 内容哈希前 8 位，study.html 的 <script src> 同步改名
    （URL 不变就会一直吃 CDN / 浏览器旧缓存 —— 这是本仓库踩过的坑）

用法
----
    python tools/add_study_docs.py --spec tools/study_additions.json
    python tools/add_study_docs.py --spec tools/study_additions.json --check
    python tools/add_study_docs.py --spec ... --dry-run

spec 格式（JSON）:
{
  "groups": {
    "deep": {"title": "专家级深度", "color": "#7c3aed"}
  },
  "docs": [
    {"rel": "docs/deep/21-xxx.md", "title": "显示标题", "group": "deep",
     "sub": "副标题（可省）"}
  ]
}
rel 相对**仓库根**。id 由 rel 机械推导，因此同一文件永远得到同一个 id。
"""
from __future__ import annotations

import argparse
import hashlib
import html as htmlmod
import io
import json
import os
import pathlib
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = pathlib.Path(__file__).resolve().parent.parent
STUDY = ROOT / "study-data"
STUDY_HTML = ROOT / "study.html"
SW = ROOT / "sw.js"

FIELDS = ["t", "g", "gk", "m", "c", "f"]


# ------------------------------------------------------------------ 小工具

def h(b: bytes) -> str:
    return hashlib.sha1(b).hexdigest()


def slugify(name: str) -> str:
    """与 tools/split_study.py 完全一致。"""
    s = re.sub(r"[^A-Za-z0-9._-]+", "_", name).strip("_")
    return (s or "grp")[:80]


def sanitize_html(s: str) -> str:
    """与上游 build_liquid.sanitize_html 同规则：文档里不允许出现可执行内容。"""
    s = re.sub(r"<script\b[\s\S]*?</script>", lambda m: htmlmod.escape(m.group(0)), s, flags=re.I)
    s = re.sub(r"<script\b[^>]*>", lambda m: htmlmod.escape(m.group(0)), s, flags=re.I)
    s = re.sub(r"</script>", "&lt;/script&gt;", s, flags=re.I)
    s = re.sub(r"<iframe\b[\s\S]*?</iframe>", lambda m: htmlmod.escape(m.group(0)), s, flags=re.I)
    s = re.sub(r"<iframe\b[^>]*>", lambda m: htmlmod.escape(m.group(0)), s, flags=re.I)
    s = re.sub(r"<(object|embed|form|base)\b[^>]*>", lambda m: htmlmod.escape(m.group(0)), s, flags=re.I)
    s = re.sub(r"\son(click|error|load|mouseover|focus|submit|change|input|keydown|keyup|dblclick)\s*=",
               " data-ev=", s, flags=re.I)
    return s


def doc_id(rel: str) -> str:
    """与上游 build_liquid 的 did 规则一致。"""
    return rel.replace("/", "_").replace(".", "_")


def nav_group_html(gk: str, title: str, color: str, n: int) -> str:
    """生成一个侧栏分组块，格式与 study.html 里既有的完全一致。"""
    return (
        f'<div class="nav-group closed" data-g="{gk}">\n'
        f'  <button class="group-head" onclick="toggleGroup(this)">'
        f'<span class="g-dot" style="background:{color}"></span>{title}'
        f'<span class="cnt">{n}</span>'
        f'<svg viewBox="0 0 24 24" class="chev"><path d="M6 9l6 6 6-6" fill="none" '
        f'stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg></button>\n'
        f'  <div class="group-body" data-built="0"></div>\n'
        f'</div>'
    )


def nav_section_html(sec: str, title: str, sub: str, groups_html: str, n: int) -> str:
    return (
        f'<div class="nav-sec" data-sec="{sec}">'
        f'<button class="sec-head" onclick="toggleSec(this)">{title}'
        f'<span class="cnt">{n} 组</span><span class="sub">{sub}</span></button>'
        f'<div class="sec-body">{groups_html}</div></div>'
    )


def patch_nav(html: str, mdocs: dict, new_groups: dict, sections: dict) -> str:
    """侧栏手术：
    1) 插入新分组（必要时新建分区）
    2) **按 manifest 重算所有分组的篇数** —— 手写的 cnt 必然漂移，自愈最省事
    """
    # 每个 gk 的篇数
    cnt_by_gk: dict[str, int] = {}
    for v in mdocs.values():
        gk = v[2] if len(v) > 2 else None
        if gk:
            cnt_by_gk[gk] = cnt_by_gk.get(gk, 0) + 1

    # 2) 自愈既有分组的 cnt
    def fix_group(m):
        gk = m.group(1)
        n = cnt_by_gk.get(gk)
        if not n:
            return m.group(0)
        head = m.group(0)
        return re.sub(r'(<span class="cnt">)\d+(</span>)',
                      lambda mm: mm.group(1) + str(n) + mm.group(2), head, count=1)

    html = re.sub(
        r'<div class="nav-group closed" data-g="([^"]+)">.*?</div></div>',
        fix_group, html, flags=re.S)

    # 1) 插入新分组
    for gk, info in new_groups.items():
        if f'data-g="{gk}"' in html:
            continue
        sec = info.get("section")
        title = info.get("title", gk)
        color = info.get("color", "#6b7280")
        blk = nav_group_html(gk, title, color, cnt_by_gk.get(gk, 0))
        if sec and f'data-sec="{sec}"' in html:
            # 插到该分区 sec-body 的最后
            m = re.search(r'(<div class="nav-sec" data-sec="%s">.*?<div class="sec-body">)(.*?)(</div></div>)'
                          % re.escape(sec), html, re.S)
            if not m:
                print(f"!! 找不到分区 {sec}，新分组 {gk} 未插入")
                continue
            html = html[:m.end(2)] + blk + html[m.end(2):]
            # 该分区组数 +1
            def bump(mm):
                return f'<span class="cnt">{int(mm.group(1)) + 1} 组</span>'
            html = re.sub(r'(<div class="nav-sec" data-sec="%s">.*?<span class="cnt">)(\d+)( 组</span>)'
                          % re.escape(sec), bump, html, count=1, flags=re.S)
        else:
            # 新建分区，插到 nav 末尾
            sec_id = info.get("new_section", gk)
            sec_title = info.get("section_title", title)
            sec_sub = info.get("section_sub", "")
            blk2 = nav_section_html(sec_id, sec_title, sec_sub, blk, 1)
            k = html.rfind("</nav>")
            if k < 0:
                print("!! 找不到 </nav>，新分区未插入")
                continue
            html = html[:k] + blk2 + html[k:]
    return html


def read_manifest() -> tuple[pathlib.Path, dict, str]:
    """读当前 manifest（以 study.html 的 <script src> 为准，兜底取最新文件）。"""
    m = re.search(r"study-data/manifest\.([0-9a-f]+)\.js", STUDY_HTML.read_text(encoding="utf-8"))
    if m:
        p = STUDY / f"manifest.{m.group(1)}.js"
        if p.exists():
            return p, *parse_manifest(p)
    cands = sorted(STUDY.glob("manifest.*.js"), key=lambda x: x.stat().st_mtime)
    if not cands:
        raise SystemExit("!! 找不到 study-data/manifest.*.js")
    return cands[-1], *parse_manifest(cands[-1])


def parse_manifest(p: pathlib.Path) -> tuple[dict, str]:
    t = p.read_text(encoding="utf-8")
    i = t.index("var M=window.__KC_MANIFEST=") + len("var M=window.__KC_MANIFEST=")
    M, _ = json.JSONDecoder().raw_decode(t[i:])
    j = t.index("var H=") + len("var H=")
    H, _ = json.JSONDecoder().raw_decode(t[j:])
    return M, H


def read_chunk(slug_file: pathlib.Path) -> dict:
    """从内容块文件里取出 {id: html}。"""
    t = slug_file.read_text(encoding="utf-8")
    i = t.index("{", t.index("__kcChunk("))
    # 找到与开括号配对的结尾
    depth, instr, esc = 0, False, False
    for k in range(i, len(t)):
        c = t[k]
        if instr:
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == '"':
                instr = False
            continue
        if c == '"':
            instr = True
        elif c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                obj, _ = json.JSONDecoder().raw_decode(t[i:k + 1])
                return obj
    raise SystemExit(f"!! 内容块 {slug_file} 解析失败")


def render_md(path: pathlib.Path) -> str:
    import markdown
    raw = path.read_text(encoding="utf-8", errors="replace")
    html = markdown.markdown(raw, extensions=["tables", "fenced_code"])
    return sanitize_html(html)


def reading_flags(rel: str, html: str) -> dict:
    """与上游一致的阅读辅助标记：韩文原文 / 英文原文 / 代码文件。"""
    _ext = rel.rsplit(".", 1)[-1].lower() if "." in rel.rsplit("/", 1)[-1] else ""
    _plain = re.sub(r"<[^>]+>", "", html)
    _pns = re.sub(r"\s", "", _plain)
    _ko = len(re.findall(r"[\uac00-\ud7af]", _plain))
    _cn = len(re.findall(r"[\u4e00-\u9fff]", _plain))
    f = {}
    if _ko >= 250 and _cn < 600:
        f["ko"] = 1
    elif _ext in ("md", "txt", "html") and _cn < 150 and _ko < 60 and len(_pns) >= 300:
        f["en"] = 1
    if _ext in ("py", "sh", "tf", "yaml", "yml", "json", "go", "ps1", "conf", "ini",
                "hcl", "toml", "service", "rb", "lua", "pl", "sql", "c", "h",
                "java", "cs", "rs", "php"):
        f["code"] = 1
    return f


# ------------------------------------------------------------------ 主流程

def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", required=True, help="增量清单 JSON")
    ap.add_argument("--check", action="store_true", help="只校验：manifest 是否已含这些文档")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)

    spec = json.loads(pathlib.Path(args.spec).read_text(encoding="utf-8"))
    groups = spec.get("groups", {})
    docs_spec = spec.get("docs", [])

    mpath, M, H = read_manifest()
    fields = M.get("fields", FIELDS)
    mdocs = dict(M["docs"])
    ch_entries = dict(M["chunks"])

    # gk -> slug：既有映射直接抄 manifest 的 chunks[].src
    gk2slug = {v.get("src", k): k for k, v in ch_entries.items()}
    gk2slug_before = set(gk2slug)
    used_slugs = set(ch_entries)

    def slug_for(gk: str) -> str:
        if gk in gk2slug:
            return gk2slug[gk]
        s, i = slugify(gk), 2
        while s in used_slugs:
            s = "%s_%d" % (slugify(gk), i)
            i += 1
        used_slugs.add(s)
        gk2slug[gk] = s
        return s

    # 1) 渲染新增文档
    new_docs: dict[str, list] = {}   # slug -> [(id, html)]
    added, skipped = [], []
    for d in docs_spec:
        rel = d["rel"]
        did = doc_id(rel)
        if did in mdocs:
            skipped.append((rel, "已在 manifest 中"))
            continue
        src = ROOT / rel
        if not src.exists():
            skipped.append((rel, "源文件不存在"))
            continue
        gk = d["group"]
        html = render_md(src)
        raw = src.read_text(encoding="utf-8", errors="replace")
        mins = max(3, round(len(raw) / 400))
        gtitle = groups.get(gk, {}).get("title", gk)
        gcolor = groups.get(gk, {}).get("color", "#6b7280")
        t = d.get("title") or src.stem
        if d.get("sub"):
            t = f"{t} · {d['sub']}"
        f = reading_flags(rel, html)
        slug = slug_for(gk)
        meta = [t, gtitle, gk, mins, gcolor, f]
        new_docs.setdefault(slug, []).append((did, html))
        mdocs[did] = meta + [slug]
        added.append((did, rel, slug, mins))

    if args.check:
        missing = [r for r, _ in skipped if not mdocs.get(doc_id(r))]
        print(f"manifest : {mpath.name}  docs={len(mdocs)}  chunks={len(ch_entries)}")
        if not added and not missing:
            print(f"PASS  增量文档          {len(skipped)} 篇全部已收录")
            return 0
        for did, rel, slug, mins in added:
            print(f"   待收录 {rel}  -> {did}  ({mins}min, 块 {slug})")
        print(f"FAIL  增量文档          {len(added)} 篇未收录")
        return 1

    if not added:
        print("无新增，无需编译。")
        return 0

    if args.dry_run:
        print(f"[dry-run] 将新增 {len(added)} 篇，涉及 {len(new_docs)} 个内容块")
        for did, rel, slug, mins in added:
            print(f"    + {rel}  -> {did}  ({mins}min, 块 {slug})")
        return 0

    # 2) 合并内容块：旧块内容 + 新内容，重算哈希，写新文件名，删旧文件
    old_chunk_files = []
    for slug, items in new_docs.items():
        meta = ch_entries.get(slug)
        docsmap = {}
        if meta:
            cf = STUDY / meta["u"]
            if cf.exists():
                docsmap = read_chunk(cf)
                old_chunk_files.append(cf)
        for did, html in items:
            docsmap[did] = html
        body = json.dumps(docsmap, ensure_ascii=False, separators=(",", ":"))
        hb = h(body.encode("utf-8"))[:6]
        fname = f"{slug}.{hb}.js"
        (STUDY / "c" / fname).write_text(
            "/* kc study chunk %s · %d docs */\nwindow.__kcChunk(%s,%s);"
            % (slug, len(docsmap), json.dumps(slug), body), encoding="utf-8")
        ch_entries[slug] = {"u": "c/" + fname, "n": len(docsmap),
                            "src": meta.get("src") if meta else slug}

    for cf in old_chunk_files:
        rel = cf.relative_to(STUDY).as_posix()
        if rel != ch_entries[slug]["u"] and rel not in [v["u"] for v in ch_entries.values()]:
            cf.unlink(missing_ok=True)

    # 3) 重算 manifest 哈希并落盘（文件名 = 哈希前 8 位 → URL 变 → 不会吃旧缓存）
    mh = json.dumps({"schema": 3, "chunks": ch_entries, "docs": mdocs, "fields": fields},
                    ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    mh8 = h(mh)[:8]
    manifest_js = (
        "/* kc study manifest · gen %s · %d docs · %d chunks · 由 tools/split_study.py 生成 */\n"
        "(function(){\n"
        "var M=window.__KC_MANIFEST=%s;\n"
        "var D=window.DOCS={},F=M.fields;\n"
        "var H=%s;\n"
        "D.__home__={};for(var i=0;i<F.length;i++)D.__home__[F[i]]=H[F[i]];D.__home__.html=H.html;\n"
        "for(var id in M.docs){var a=M.docs[id],o={},n=F.length;for(var i=0;i<n;i++)o[F[i]]=a[i];o._ck=a[n];D[id]=o;}\n"
        "})();"
        % (mh8, len(mdocs), len(ch_entries),
           json.dumps({"v": mh8, "base": "study-data/", "fields": fields,
                       "chunks": ch_entries, "docs": mdocs},
                      ensure_ascii=False, separators=(",", ":")),
           json.dumps(H, ensure_ascii=False, separators=(",", ":")))
    )
    new_manifest = STUDY / f"manifest.{mh8}.js"
    new_manifest.write_text(manifest_js, encoding="utf-8")

    # 4) study.html 同步 <script src>（URL 必须变，否则浏览器/CDN 会一直吐旧缓存）
    s = STUDY_HTML.read_text(encoding="utf-8")
    s2 = re.sub(r"study-data/manifest\.[0-9a-f]+\.js", f"study-data/manifest.{mh8}.js", s, count=1)
    if s2 == s:
        print("!! study.html 里没找到 manifest 引用，需人工检查")
        return 1

    # 4b) 侧栏手术：插入新分组 + 按 manifest 自愈所有分组的篇数
    new_groups = {}
    for gk in {d["group"] for d in docs_spec}:
        if gk not in gk2slug_before:
            new_groups[gk] = groups.get(gk, {})
    s2 = patch_nav(s2, mdocs, new_groups, {})
    STUDY_HTML.write_text(s2, encoding="utf-8")
    if new_groups:
        print("  侧栏已插入新分组：" + "、".join(new_groups))

    # 5) sw.js 预缓存清单里若有旧内容块路径，同步换成新的
    if SW.exists():
        w = SW.read_text(encoding="utf-8")
        w2 = w
        for slug in new_docs:
            old_u = None
            for v in ch_entries.values():
                if v.get("src") == slug:
                    old_u = v["u"]
            if old_u and f"study-data/{old_u}" in w2:
                w2 = w2.replace(f"study-data/{old_u}",
                                f"study-data/{ch_entries[slug]['u']}")
        for slug in new_docs:
            if f"study-data/{ch_entries[slug]['u']}" not in w2:
                continue
        if w2 != w:
            SW.write_text(w2, encoding="utf-8")
            print("  sw.js 预缓存路径已同步")

    mpath.unlink(missing_ok=True)

    print(f"已写入 manifest : manifest.{mh8}.js   docs {len(mdocs)} · chunks {len(ch_entries)}")
    for did, rel, slug, mins in added:
        print(f"    + {rel}  -> {did}  ({mins}min, 块 {slug})")
    print(f"study.html 的 <script src> 已同步到 manifest.{mh8}.js")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())