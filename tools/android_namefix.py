#!/usr/bin/env python3
# android_namefix.py v2 <src.apk> <dst.apk> [mapping_out.json]
# ① 双重编码修复；② 全部非 ASCII 资源名 ASCII 化（_uXXXX）；
# ③ study.html 的多技能库引用改写（跳过 jsdelivr 在线链接）；
# ④ 其它文本条目（html/js/css/md/txt/json/svg）内按路径分段做同样改写；
# ⑤ 跳过 META-INF。退出码：3=断言失败（防静默发坏包）
import sys, zipfile, time, json
from pathlib import Path

src, dst = sys.argv[1], sys.argv[2]
mapout = sys.argv[3] if len(sys.argv) > 3 else None
zin = zipfile.ZipFile(src)
infos = zin.infolist()


def raw_of(info):
    return info.filename.encode('utf-8') if (info.flag_bits & 0x800) else info.filename.encode('cp437')


def undouble(name, raw):
    try:
        return raw.decode('utf-8').encode('cp437').decode('utf-8')
    except Exception:
        return name


def esc(s):
    return ''.join(('_u%04x' % ord(c)) if ord(c) > 127 else c for c in s)


entries = []
pairs = {}
seg_map = {}
for info in infos:
    if info.filename.startswith('META-INF/'):
        continue
    name = info.filename
    fixed = undouble(name, raw_of(info))
    final = esc(fixed)
    if final != fixed and fixed.startswith('assets/multiskill/'):
        pairs[fixed[len('assets/'):]] = final[len('assets/'):]
    if final != fixed:
        for seg in fixed.split('/'):
            if any(ord(c) > 127 for c in seg):
                seg_map[seg] = esc(seg)
    entries.append((info, fixed, final))
sys.stderr.write('namefix: pairs=%d seg_map=%d\n' % (len(pairs), len(seg_map)))

# 读入全部文本条目（需改写的）
TEXT_EXT = ('.html', '.htm', '.js', '.css', '.md', '.txt', '.json', '.svg', '.xml')
texts = {}
for info, fixed, final in entries:
    if final.startswith('res/'):
        continue
    if final.lower().endswith(TEXT_EXT):
        data = zin.read(info.filename)
        try:
            texts[info.filename] = data.decode('utf-8')
        except Exception:
            pass
sys.stderr.write('namefix: text entries=%d\n' % len(texts))

# ① study.html：完整路径替换（跳过在线链接）
html = texts.pop('assets/study.html', None)
repl_html = 0
if html is not None:
    for old, new in sorted(pairs.items(), key=lambda x: -len(x[0])):
        idx = 0
        while True:
            k = html.find(old, idx)
            if k < 0:
                break
            pre = html[max(0, k - 90):k]
            if 'jsdelivr.net' in pre or 'github.io' in pre or 'github.com' in pre:
                idx = k + 1
                continue
            html = html[:k] + new + html[k + len(old):]
            repl_html += 1
            idx = k + len(new)
sys.stderr.write('namefix: study.html replacements=%d\n' % repl_html)

# ② 其它文本条目：先全路径替换，再分段替换（仅路径上下文，保护正文与文档 id）
import re as _re
repl_other = 0
for fn, txt in list(texts.items()):
    orig = txt
    for old, new in sorted(pairs.items(), key=lambda x: -len(x[0])):
        if old in txt:
            txt = txt.replace(old, new)
    for old, new in seg_map.items():
        if old not in txt:
            continue
        pat = '(?<=[=/"\'(,\\s+`])' + _re.escape(old) + '(?=[/"\')\\s#?,+`]|$)'
        txt = _re.sub(pat, lambda m, n=new: n, txt)
    texts[fn] = txt
    if txt != orig:
        repl_other += 1
sys.stderr.write('namefix: other text files changed=%d\n' % repl_other)

# 写包
with zipfile.ZipFile(dst, 'w', allowZip64=True) as zo:
    for info, fixed, final in entries:
        if info.filename == 'assets/study.html' and html is not None:
            data = html.encode('utf-8')
        elif info.filename in texts:
            data = texts[info.filename].encode('utf-8')
        else:
            data = zin.read(info.filename)
        zi = zipfile.ZipInfo(final, date_time=info.date_time)
        zi.compress_type = info.compress_type
        zi.external_attr = info.external_attr
        zo.writestr(zi, data)

if mapout:
    Path(mapout).write_text(
        json.dumps({'pairs': pairs, 'seg_map': seg_map}, ensure_ascii=False, indent=1),
        encoding='utf-8')
bad = [f for _, _, f in entries if any(ord(c) > 127 for c in f)]
sys.stderr.write('namefix: done entries=%d nonascii-left=%d html_repl=%d other_repl=%d\n'
                 % (len(entries), len(bad), repl_html, repl_other))
if len(bad) > 0 or len(pairs) < 90 or repl_html < 90:
    sys.stderr.write('namefix: ASSERT FAILED\n')
    sys.exit(3)
print('namefix OK ->', dst)
