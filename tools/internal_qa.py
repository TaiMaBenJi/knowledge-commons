#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
internal_qa.py · 知识公社全站内部体检
检查项：HTML 内链/资源引用 · Markdown 相对链接 · sw.js PWA 预缓存 ·
        learn/searchidx.js 索引路径 · sitemap.xml 映射 · manifest.json · JSON 有效性 · JS 语法
存在性判定：本地工作区 ∪ 远端 main 文件集（GitHub Trees API，公开仓库免认证）。
用法：python3 tools/internal_qa.py [--remote owner/repo]
"""
import os, re, json, subprocess, urllib.request, urllib.error, urllib.parse, argparse

# 远端文件集只查 GitHub 官方 API（固定主机），用 opener 对象执行请求
_OPENER = urllib.request.build_opener()

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SKIP_DIRS = {'.git', 'study-data', 'clients', 'video-factory', 'video-ext', 'dist'}
# 动态构链页面（链接在 JS 里生成/404 跳转页），整页跳过扫描：
SKIP_PATHS = {
    '404.html', 'study.html', 'viewer.html',
    'learn/beginner.html', 'learn/search.html', 'learn/sleep.html', 'library.html',
    'learn/media/videos-cloud.html', 'learn/media/course-videos.html',
    'learn/cloud/start.html', 'learn/files/tuxing/index.html', 'learn/files/zsb/index.html',
}
remote = set()

def walk(exts, sub=''):
    out = []
    base = os.path.join(ROOT, sub) if sub else ROOT
    for dirpath, dirnames, filenames in os.walk(base):
        rel = os.path.relpath(dirpath, ROOT)
        parts = set(rel.split(os.sep)) if rel != '.' else set()
        if parts & SKIP_DIRS:
            dirnames[:] = []
            continue
        for fn in filenames:
            if fn.endswith(exts):
                out.append(os.path.relpath(os.path.join(dirpath, fn), ROOT))
    return out

def resolve(base_file, link):
    link = link.split('#', 1)[0].split('?', 1)[0].strip()
    if not link:
        return None
    if re.match(r'^(https?:|mailto:|tel:|data:|javascript:)', link, re.I):
        return None
    link = urllib.parse.unquote(link)
    if link.startswith('/'):
        p = link.lstrip('/')
    else:
        p = os.path.normpath(os.path.join(os.path.dirname(base_file), link))
    if p.startswith('..') or p == '.':
        return None
    return p.replace(os.sep, '/')

def exists(p):
    return os.path.isfile(os.path.join(ROOT, p)) or (p in remote)

def exists_dir(p):
    return any(exists(p + '/index.' + ext) for ext in ('html', 'md', 'htm'))

def fetch_remote_tree(repo):
    url = f'https://api.github.com/repos/{repo}/git/trees/main?recursive=1'
    # 主机边界校验：只允许 GitHub 官方 API（https + 固定域名）
    if urllib.parse.urlparse(url).hostname != 'api.github.com':
        raise ValueError(f'只允许 GitHub 官方 API：{url}')
    r = urllib.request.Request(url, headers={'User-Agent': 'kc-qa'})
    with _OPENER.open(r, timeout=60) as resp:
        data = json.loads(resp.read().decode())
    if data.get('truncated'):
        print('⚠️ 远端树被截断，判定可能不全')
    for e in data.get('tree', []):
        if e['type'] == 'blob':
            remote.add(e['path'])
    print(f'✓ 远端文件集：{len(remote)} 个文件')

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--remote', default='TaiMaBenJi/knowledge-commons')
    args = ap.parse_args()
    try:
        fetch_remote_tree(args.remote)
    except Exception as ex:
        print(f'⚠️ 远端树获取失败（仅按本地判定）：{ex}')

    issues = {}
    def add(path, kind, link):
        issues.setdefault(path, []).append((kind, link))

    # ---- 1) HTML ----
    js_str_re = re.compile(r'''['"]([A-Za-z0-9_\-./]+\.(?:html|js|md|css|json|mp4|png|svg|webp|ico))(?:[?#][^'"]*)?['"]''')
    script_re = re.compile(r'<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>', re.S | re.I)
    htmls = [f for f in walk(('.html',))
             if f.replace(os.sep, '/') not in SKIP_PATHS]   # walk 产出系统分隔符，SKIP_PATHS 统一用 /
    for f in htmls:
        s = open(os.path.join(ROOT, f), encoding='utf-8', errors='replace').read()
        links = set()
        for m in re.finditer(r'(?:href|src|poster)="([^"]+)"', s):
            v = m.group(1)
            # JS 模板拼串（h+='<a href="'+L.u+'">…）里出现的引号/加号，不是静态引用
            if any(ch in v for ch in ('+', "'", '"')):
                continue
            links.add(v)
        for sm in script_re.finditer(s):
            for jm in js_str_re.finditer(sm.group(1)):
                jv = jm.group(1)
                if not any(ch in jv for ch in ('+', "'", '"', '(', ')', ' ')):
                    links.add(jv)
        for link in links:
            p = resolve(f, link)
            if p and not exists(p) and not exists_dir(p):
                add(f, 'html-ref', link)

    # ---- 2) Markdown ----
    for f in walk(('.md',), 'docs') + walk(('.md',), 'learn'):
        s = open(os.path.join(ROOT, f), encoding='utf-8', errors='replace').read()
        for m in re.finditer(r'\]\(([^)\s]+)\)', s):
            link = m.group(1).strip('<>')
            if link.startswith(('http://', 'https://', 'mailto:', '#')):
                continue
            p = resolve(f, link)
            if p and not exists(p) and not exists_dir(p):
                add(f, 'md-link', link)

    # ---- 3) sw.js CORE ----
    if os.path.exists(os.path.join(ROOT, 'sw.js')):
        s = open(os.path.join(ROOT, 'sw.js'), encoding='utf-8').read()
        m = re.search(r'var CORE = \[(.*?)\];', s, re.S)
        if m:
            for item in re.findall(r"'([^']+)'", m.group(1)):
                p = item.lstrip('./')
                if p and p != 'learn' and not exists(p) and not exists_dir(p):
                    add('sw.js', 'sw-core', item)

    # ---- 4) searchidx ----
    sip = 'learn/searchidx.js'
    if os.path.exists(os.path.join(ROOT, sip)):
        s = open(os.path.join(ROOT, sip), encoding='utf-8').read()
        for u in re.findall(r'"u":\s*"([^"]+)"', s):
            p = u.split('#', 1)[0].split('?', 1)[0]
            if not p or p.startswith('http'):
                continue
            full = os.path.normpath(os.path.join('learn', p))
            if not exists(full):
                add(sip, 'searchidx', u)

    # ---- 5) sitemap ----
    if os.path.exists(os.path.join(ROOT, 'sitemap.xml')):
        s = open(os.path.join(ROOT, 'sitemap.xml'), encoding='utf-8').read()
        for loc in re.findall(r'<loc>([^<]+)</loc>', s):
            rel = loc.split('knowledge-commons/', 1)[-1] if 'knowledge-commons/' in loc else ''
            p = rel if rel else 'index.html'
            if not exists(p) and not exists_dir(p):
                add('sitemap.xml', 'sitemap', loc)

    # ---- 6) manifest ----
    mp = 'manifest.json'
    if os.path.exists(os.path.join(ROOT, mp)):
        try:
            mf = json.loads(open(os.path.join(ROOT, mp), encoding='utf-8').read())
            for ic in mf.get('icons', []):
                p = ic.get('src', '').lstrip('/')
                if p and not exists(p):
                    add(mp, 'manifest-icon', p)
            for sc in mf.get('shortcuts', []):
                su = sc.get('url', '').split('#')[0].lstrip('/')
                if su and not exists(su):
                    add(mp, 'manifest-shortcut', su)
        except Exception as ex:
            add(mp, 'json-parse', str(ex)[:80])

    # ---- 7) JSON 有效性 ----
    for f in walk(('.json',)):
        if f.startswith('clients/'):
            continue
        try:
            json.loads(open(os.path.join(ROOT, f), encoding='utf-8').read())
        except Exception as ex:
            add(f, 'json-parse', str(ex)[:80])

    # ---- 8) JS 语法 ----
    js_targets = ['sw.js', 'install-tip.js', 'learn/kc-learn.js', 'learn/kc-srs.js',
                  'learn/media/data/course-scripts.js', 'learn/searchidx.js']
    js_targets += walk(('.js',), 'learn/cloud/contest/data')
    js_targets += walk(('.js',), 'lab')
    js_targets += walk(('.js',), 'app')
    for f in js_targets:
        fp = os.path.join(ROOT, f)
        if not os.path.exists(fp):
            continue
        try:
            r = subprocess.run(['node', '--check', fp], capture_output=True, text=True, timeout=30)
            if r.returncode != 0:
                add(f, 'js-syntax', (r.stderr or r.stdout).strip().split('\n')[0][:120])
        except Exception as ex:
            add(f, 'js-check-fail', str(ex)[:80])

    # ---- 报告 ----
    if not issues:
        print('\n✅ 体检通过：0 个问题')
        return
    total = sum(len(v) for v in issues.values())
    print(f'\n❌ 发现 {len(issues)} 个文件、{total} 处问题：')
    for f in sorted(issues):
        for kind, link in issues[f]:
            print(f'  [{kind}] {f} → {link}')

if __name__ == '__main__':
    main()
