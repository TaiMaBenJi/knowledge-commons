#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
seo_inject.py · 知识公社全站 SEO / 社交分享 / 结构化数据元信息注入

设计目标
--------
· 无构建步骤的纯静态站，导航与 <head> 在各页面自行维护；本脚本把
  「每个页面都该有的 SEO 元信息」一次性、幂等地补齐，避免手改几十个文件。
· 纯标准库实现（无需第三方依赖），可在任意环境跑。
· 幂等：已存在 <meta name="description"> 的页面自动跳过；可反复运行。
· 不改动页面原有结构、导航、脚本与 PWA 标记，仅在 </head> 前插入一块。

注入内容
--------
  - <meta name="description">         （自动从首段正文抽取，缺省回退到标题）
  - Open Graph（og:type/site_name/title/description/locale/url）
  - Twitter Card（summary）
  - <link rel="canonical">
  - JSON-LD WebSite + SearchAction（助力搜索引擎站点内搜索框）

用法
----
  python tools/seo_inject.py                 # 扫描全仓库 .html
  python tools/seo_inject.py path/to/a.html  # 只处理单个文件
  python tools/seo_inject.py --dry           # 仅打印将插入的块，不写盘
"""
import os
import re
import sys
import html as htmlmod

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://taimabenji.github.io/knowledge-commons/"
SKIP_DIRS = {".git", "node_modules", "videos"}
# 已是 noindex / 跳转兼容层的页面不需要公开 SEO 元信息
NOINDEX_RE = re.compile(r'name=["\']robots["\'][^>]*content=["\']noindex', re.I)


def strip_tags(s):
    s = re.sub(r"<[^>]+>", "", s)
    s = htmlmod.unescape(s)
    return re.sub(r"\s+", " ", s).strip()


def get_title(text):
    m = re.search(r"<title[^>]*>(.*?)</title>", text, re.I | re.S)
    return strip_tags(m.group(1)) if m else "知识公社"


def get_description(text):
    # 先去掉脚本与样式，避免把代码当正文
    body = re.sub(r"<script[\s\S]*?</script>", " ", text, flags=re.I)
    body = re.sub(r"<style[\s\S]*?</style>", " ", body, flags=re.I)
    cands = re.findall(r"<p[^>]*>([\s\S]*?)</p>", body, re.I)
    for c in cands:
        t = strip_tags(c)
        if len(t) >= 12:
            return t[:120]
    # 退回：取首个带文本的 div.desc / blockquote
    for tag in (r'div[^>]*class=["\'][^"\']*desc', r'blockquote'):
        m = re.search(r"<%s[^>]*>([\s\S]*?)</%s>" % (tag, tag.split()[0]), body, re.I)
        if m:
            t = strip_tags(m.group(1))
            if len(t) >= 12:
                return t[:120]
    return ""


def canonical(relpath):
    rel = relpath.replace(os.sep, "/")
    if rel.endswith("index.html"):
        return SITE + rel[: -len("index.html")]
    return SITE + rel


def build_block(title, desc, url):
    if not desc:
        desc = title + " · 知识公社 · 完全离线、完全开源的免费学习资源总站"
    desc = htmlmod.escape(desc)
    title_esc = htmlmod.escape(title)
    ld = (
        '{'
        '"@context":"https://schema.org",'
        '"@type":"WebSite",'
        '"name":"知识公社 · Knowledge Commons",'
        '"url":"%s",'
        '"potentialAction":{"@type":"SearchAction",'
        '"target":"%slearn/search.html?q={search_term_string}",'
        '"query-input":"required name=search_term_string"}'
        '}' % (SITE, SITE)
    )
    return (
        '\n<!-- kc-seo (auto) -->\n'
        '<meta name="description" content="%s">\n'
        '<meta property="og:type" content="website">\n'
        '<meta property="og:site_name" content="知识公社 · Knowledge Commons">\n'
        '<meta property="og:title" content="%s">\n'
        '<meta property="og:description" content="%s">\n'
        '<meta property="og:locale" content="zh_CN">\n'
        '<meta property="og:url" content="%s">\n'
        '<meta name="twitter:card" content="summary">\n'
        '<meta name="twitter:title" content="%s">\n'
        '<meta name="twitter:description" content="%s">\n'
        '<link rel="canonical" href="%s">\n'
        '<script type="application/ld+json">%s</script>\n'
        '<!-- /kc-seo -->\n'
        % (desc, title_esc, desc, url, title_esc, desc, url, ld)
    )


def process_file(path, dry=False):
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    if NOINDEX_RE.search(text):
        return False, "noindex, skipped"
    if re.search(r'<meta\s+name=["\']description["\']', text, re.I):
        return False, "already has description, skipped"
    if "</head>" not in text and "</HEAD>" not in text:
        return False, "no </head>, skipped"
    title = get_title(text)
    desc = get_description(text)
    url = canonical(os.path.relpath(path, ROOT))
    block = build_block(title, desc, url)
    if dry:
        print("=== %s ===\n%s" % (os.path.relpath(path, ROOT), block))
        return True, "dry"
    new = re.sub(r"</head>", block + "</head>", text, count=1, flags=re.I)
    with open(path, "w", encoding="utf-8") as f:
        f.write(new)
    return True, "injected (desc=%d chars)" % len(desc)


def main():
    dry = "--dry" in sys.argv
    targets = [a for a in sys.argv[1:] if not a.startswith("--")]
    files = []
    if targets:
        for t in targets:
            files.append(t if os.path.isabs(t) else os.path.join(ROOT, t))
    else:
        for dirpath, dirnames, filenames in os.walk(ROOT):
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
            for fn in filenames:
                if fn.lower().endswith(".html"):
                    files.append(os.path.join(dirpath, fn))
    done = skip = 0
    for fp in files:
        if not os.path.isfile(fp):
            continue
        ok, msg = process_file(fp, dry)
        rel = os.path.relpath(fp, ROOT)
        if ok:
            done += 1
            if not dry:
                print("+ %s  %s" % (rel, msg))
        else:
            skip += 1
            if not dry:
                print(". %s  %s" % (rel, msg))
    print("\nSummary: injected=%d skipped=%d total=%d" % (done, skip, len(files)))


if __name__ == "__main__":
    main()
