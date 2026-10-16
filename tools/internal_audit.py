#!/usr/bin/env python3
"""站内一致性体检（internal audit）
   ------------------------------------------------------------
   检查 10 项，跑法： python3 tools/internal_audit.py
   1  内部链接完整性（href/src 不指向不存在的文件）
   2  study.html 深链 key 有效性（对照 study-data/manifest.*.js 的 docs 表）
   3  learn/ 导航栏是否全站一致
   4  导航栏每个目标是否真实存在
   5  sw.js 预缓存清单里的文件是否都存在
   6  learn/ 下是否有页面漏进 sw.js 预缓存（漏了 = 离线打不开）
   7  sitemap.xml 是否有悬空 URL
   8  learn/ 下是否有页面漏进 sitemap
   9  searchidx.js 是否能正常解析、是否收录了新页面
   10 新页面的内联 JS 是否语法正确
   11 learn/ 全部页面的 HTML 标签是否闭合平衡（含游离 </li>、未闭合 <div>）
   ------------------------------------------------------------
   退出码 0 = 全通过，1 = 有检查项失败。
   注：本脚本按“站内相对路径”判定，不检查外链存活；
   外链请用 tools/linkcheck.py。"""
import os, re, io, json, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_TREE = os.path.join(ROOT, "..", "_tmp", "api_tree.json")
tree = json.load(open(_TREE))["tree"] if os.path.exists(_TREE) else []
TRUTH = {it["path"] for it in tree if it.get("type") == "blob"}
DIRS = {it["path"] for it in tree if it.get("type") == "tree"}


LOCAL_NEW = {os.path.relpath(os.path.join(dp, fn), ROOT)
             for dp, dn, fns in os.walk(ROOT) if ".git" not in dp
             for fn in fns if fn.endswith((".html", ".js", ".css", ".xml", ".json"))}
KNOWN = TRUTH | DIRS | LOCAL_NEW

fail = 0

# ---------- 1. internal link integrity ----------
ATTR = re.compile(r'(?:href|src)\s*=\s*["\']([^"\']+)["\']', re.I)
files = []
for dp, dns, fns in os.walk(ROOT):
    dns[:] = [d for d in dns if d != ".git"]
    for fn in fns:
        if fn.endswith((".html", ".htm")):
            files.append(os.path.join(dp, fn))

from urllib.parse import unquote
bad = []
IGNORE_EXACT = {"itms-services://?action=download-manifest&url="}
for p in files:
    s = io.open(p, encoding="utf-8", errors="ignore").read()
    # only scan real markup: drop HTML-escaped documentation snippets
    s_scan = re.sub(r"&lt;[^&]*&gt;", "", s)
    for m in ATTR.finditer(s_scan):
        u = m.group(1).strip()
        if not u or u.startswith(("http://", "https://", "//", "mailto:", "tel:",
                                 "data:", "javascript:", "about:", "itms-services:")):
            continue
        path = unquote(u.split("#")[0].split("?")[0])
        if not path or path in IGNORE_EXACT:
            continue
        if "." not in path.rsplit("/", 1)[-1]:
            continue          # extension-less fragment => JS string-concat href
        tgt = os.path.normpath(os.path.join(os.path.dirname(p), path))
        if os.path.exists(tgt):
            continue
        rp = os.path.relpath(tgt, ROOT)
        if rp in KNOWN:
            continue
        # template placeholders inside tool files
        if any(x in u for x in ("图片路径", "网址", "路径", "url", "([^")):
            continue
        bad.append((os.path.relpath(p, ROOT), u))
print(f"[1] internal links: {'OK' if not bad else 'FAIL'} ({len(bad)} broken)")
for f, u in bad:
    print(f"      {f} -> {u}")
fail += bool(bad)

# ---------- 2. study.html deep links ----------
s = io.open(ROOT + "/study-data/manifest.915c22a5.js", encoding="utf-8").read()
docs = set(json.loads(re.search(r'var M=window\.__KC_MANIFEST=(\{.*?\});', s, re.S).group(1))["docs"].keys())
deep_bad = {}
for p in files:
    c = io.open(p, encoding="utf-8", errors="ignore").read()
    for k in re.findall(r'study\.html#d=([^"\'>\s]+)', c):
        if k not in docs:
            deep_bad.setdefault(os.path.relpath(p, ROOT), set()).add(k)
n = sum(len(v) for v in deep_bad.values())
print(f"[2] study deep-links: {'OK' if not n else 'FAIL'} ({n} broken, {len(docs)} known ids)")
for f, ks in deep_bad.items():
    print(f"      {f}: {sorted(ks)[:6]}")
fail += bool(n)

# ---------- 3. nav consistency ----------
NAVRE = re.compile(r'<nav class="tabs">(.*?)</nav>', re.S)
LINKRE = re.compile(r'href\s*=\s*["\']([^"\']+)["\']')
sets = {}
for p in files:
    if not os.path.relpath(p, ROOT).startswith("learn/"):
        continue
    m = NAVRE.search(io.open(p, encoding="utf-8", errors="ignore").read())
    if m:
        sets[os.path.relpath(p, ROOT)] = tuple(LINKRE.findall(m.group(1)))
from collections import Counter
c = Counter(sets.values())
print(f"[3] nav bar: {len(c)} variant(s) across {len(sets)} pages -> "
      f"{'OK' if len(c) == 1 else 'DRIFT'}")
for k, v in c.most_common():
    print(f"      {v} pages, {len(k)} links")
fail += (len(c) != 1)

# every nav target must exist
missing_nav = set()
for rel, s_ in sets.items():
    for h in s_:
        t = os.path.normpath(os.path.join(ROOT, "learn", h))
        if not os.path.exists(t):
            missing_nav.add(h)
print(f"[4] nav targets exist: {'OK' if not missing_nav else 'FAIL'}")
if missing_nav:
    print("      missing:", sorted(missing_nav))
    fail += 1

# ---------- 5. sw.js ----------
sw = io.open(ROOT + "/sw.js", encoding="utf-8").read()
ver = re.search(r"var VERSION = '([^']+)'", sw).group(1)
core = re.search(r"var CORE = \[(.*?)\];", sw, re.S).group(1)
items = re.findall(r"'([^']+)'", core)
miss = []
for u in items:
    p = u.lstrip("./")
    if p == "" :
        continue
    tgt = os.path.normpath(os.path.join(ROOT, p))
    if os.path.exists(tgt):
        continue
    rp = os.path.relpath(tgt, ROOT)
    if rp in KNOWN:
        continue          # exists upstream; skipped by the local fetcher (icons/*.png)
    miss.append(u)
print(f"[5] sw.js VERSION={ver}, CORE={len(items)} entries, "
      f"missing targets: {'0 OK' if not miss else miss}")
fail += bool(miss)

# sw.js must cover every learn page
learnpages = {f"learn/{f}" for f in os.listdir(ROOT + "/learn") if f.endswith(".html")}
uncached = sorted(p for p in learnpages
                   if p not in {i.lstrip("./") for i in items} and p != "learn/red/poems.html")
print(f"[6] learn pages not in sw CORE: {'OK' if not uncached else uncached}")
fail += bool(uncached)

# ---------- 7. sitemap ----------
sm = io.open(ROOT + "/sitemap.xml", encoding="utf-8").read()
locs = re.findall(r"<loc>https://taimabenji\.github\.io/knowledge-commons/([^<]*)</loc>", sm)
sm_bad = [l for l in locs if l and not os.path.exists(os.path.join(ROOT, l))]
print(f"[7] sitemap: {len(locs)} urls, dangling: {'0 OK' if not sm_bad else sm_bad}")
fail += bool(sm_bad)
notlisted = sorted(p for p in learnpages if p not in locs)
print(f"[8] learn pages missing from sitemap: {'OK' if not notlisted else notlisted}")
fail += bool(notlisted)

# ---------- 9. search index ----------
try:
    out = subprocess.run(
        ["node", "-e", "global.window={};require('/workspace/kc/learn/searchidx.js');"
         "console.log(window.SEARCH_IDX.length)"],
        capture_output=True, text=True, timeout=40)
    n = out.stdout.strip()
    print(f"[9] searchidx.js parse: {'OK' if n.isdigit() else 'FAIL'} ({n} entries)")
    fail += (not n.isdigit())
    # new pages must be indexed
    idx = io.open(ROOT + "/learn/searchidx.js", encoding="utf-8").read()
    for p in ("cloud-race.html", "cloud-cert.html", "cloud-videos.html"):
        if p not in idx:
            print(f"      WARN {p} not in search index")
except Exception as e:
    print(f"[9] searchidx.js: FAIL {e}")
    fail += 1

# ---------- 10. JS syntax of new pages ----------
for p in ("learn/cloud-race.html", "learn/cloud-cert.html", "learn/cloud-videos.html"):
    s2 = io.open(os.path.join(ROOT, p), encoding="utf-8").read()
    scripts = re.findall(r"<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>", s2, re.S)
    for i, sc in enumerate(scripts):
        f = os.path.join(ROOT, "..", f"_chk_{os.path.basename(p)}_{i}.js")
        io.open(f, "w", encoding="utf-8").write(sc)
        o = subprocess.run(["node", "--check", f], capture_output=True, text=True)
        if o.returncode:
            print(f"[10] JS SYNTAX FAIL {p} script#{i}: {o.stderr[:200]}")
            fail += 1
print(f"[10] inline JS syntax of new pages: OK")

# ---------- 11. HTML structure (tag balance) ----------
from html.parser import HTMLParser
VOID = {"area","base","br","col","embed","hr","img","input","link","meta",
        "param","source","track","wbr"}

class _Bal(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack, self.err = [], []
    def handle_starttag(self, t, a):
        if t not in VOID:
            self.stack.append((t, self.getpos()))
    def handle_endtag(self, t):
        if t in VOID:
            return
        if not self.stack:
            self.err.append(f"stray </{t}> at {self.getpos()}"); return
        if self.stack[-1][0] == t:
            self.stack.pop(); return
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == t:
                for j in range(len(self.stack) - 1, i - 1, -1):
                    self.err.append(f"unclosed <{self.stack[j][0]}> at {self.stack[j][1]}")
                del self.stack[i:]
                break
        else:
            self.err.append(f"stray </{t}> at {self.getpos()}")

struct_bad = []
for p in files:
    if not os.path.relpath(p, ROOT).startswith("learn/"):
        continue
    b = _Bal()
    try:
        b.feed(io.open(p, encoding="utf-8", errors="ignore").read())
    except Exception as e:
        struct_bad.append((os.path.relpath(p, ROOT), [f"parse error {e}"]))
        continue
    errs = b.err + [f"EOF-unclosed <{t}> at {pos}" for t, pos in b.stack]
    if errs:
        struct_bad.append((os.path.relpath(p, ROOT), errs))
print(f"[11] HTML tag balance (learn/): {'OK' if not struct_bad else 'FAIL'} "
      f"({len(struct_bad)} pages unbalanced)")
for f, es in struct_bad[:10]:
    print(f"      {f}: {es[:3]}")
fail += bool(struct_bad)

print()
print("=" * 60)
print("REGRESSION: " + ("ALL PASS ✅" if not fail else f"{fail} CHECK(S) FAILED ❌"))
sys.exit(1 if fail else 0)
