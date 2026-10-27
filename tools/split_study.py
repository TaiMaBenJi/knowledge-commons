#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
知识公社 · study.html 数据拆分器
================================
把 study.html 内联的 14MB `const DOCS = {...}` 拆成：
  study-data/manifest.<mh8>.js   全量元数据（t/g/gk/m/c/f，3161 篇）+ __home__ 全量
  study-data/c/<组slug>.<h6>.js  按组懒加载内容块（仅 html）
并对 study.html 做四处微创手术：
  1) DOCS 行 → 外置 manifest <script>
  2) 注入懒加载 loader（ensure / prefetch / 全量标志）
  3) show() 内容门控（未加载 → 占位 → 块就绪后渲染）
  4) 搜索改用预计算 _ix；collectVideos 缓存改挂全量标志

再生成安全：tools/build_liquid.py 已接入本模块（build 时自动拆分）。
用法：python3 tools/split_study.py study.html
"""
import json, os, re, sys, hashlib
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))

FIELDS = ["t", "g", "gk", "m", "c", "f"]   # 元数据字段（html 永远进 chunk）


def h(b):
    return hashlib.sha1(b).hexdigest()


def slugify(name):
    s = re.sub(r"[^A-Za-z0-9._-]+", "_", name).strip("_")
    return (s or "grp")[:80]


def split_docs(docs):
    """→ (manifest dict, chunks dict, field list)"""
    fields = list(FIELDS)
    for k, v in docs.items():
        for f in v:
            if f not in fields and f != "html":
                fields.append(f)
    manifest, chunks = {}, {}
    slug_used = {}
    for k, v in docs.items():
        if k == "__home__":
            continue
        meta = [v.get(f) for f in fields]
        html = v.get("html")
        ck = v.get("gk") or "_core"
        manifest[k] = {"meta": meta, "ck": ck, "html": html}
        if html is not None:
            chunks.setdefault(ck, {})[k] = html
    return manifest, chunks, fields


def build_assets(docs, fields, manifest, chunks):
    """→ (manifest_js, chunk_files{name:content}, mh8)"""
    mdocs = {}
    for k, rec in manifest.items():
        ckslug = "_core" if rec["ck"] == "_core" else SLUGS[rec["ck"]]
        mdocs[k] = rec["meta"] + [ckslug]
    ch_entries = {}
    files = {}
    for ck, docsmap in chunks.items():
        body = json.dumps(docsmap, ensure_ascii=False, separators=(",", ":"))
        hb = h(body.encode("utf-8"))[:6]
        slug = "_core" if ck == "_core" else SLUGS[ck]
        fname = "%s.%s.js" % (slug, hb)
        ch_entries[slug] = {"u": "c/" + fname, "n": len(docsmap), "src": ck}
        files[fname] = (
            "/* kc study chunk %s · %d docs */\nwindow.__kcChunk(%s,%s);"
            % (slug, len(docsmap), json.dumps(slug), body)
        )
    mh = json.dumps(
        {"schema": 3, "chunks": ch_entries, "docs": mdocs, "fields": fields}, ensure_ascii=False,
        separators=(",", ":")).encode("utf-8")
    mh8 = h(mh)[:8]
    home = dict(docs["__home__"])
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
           json.dumps(home, ensure_ascii=False, separators=(",", ":")))
    )
    return manifest_js, files, mh8


LOADER = """<script>
/* kc 懒加载 loader（tools/split_study.py 生成） */
(function(){
var M=window.__KC_MANIFEST,D=window.DOCS;
var pend={},loaded=M.loaded={};
window.__kcAllLoaded=false;
window.__kcChunk=function(name,obj){
  loaded[name]=1;
  for(var id in obj){ var d=D[id]; if(d) d.html=obj[id]; }
  var q=pend[name]; delete pend[name];
  if(q) for(var i=0;i<q.length;i++){ try{q[i]();}catch(e){} }
};
function load(name){
  if(loaded[name]) return Promise.resolve();
  if(pend[name]) return pend[name];
  return pend[name]=new Promise(function(res,rej){
    var s=document.createElement('script');
    s.src=M.base+M.chunks[name].u;
    s.onload=function(){ if(!loaded[name]){ delete pend[name]; } res(); };
    s.onerror=function(){ delete pend[name]; rej(new Error('chunk '+name)); };
    document.head.appendChild(s);
  });
}
window.__kcEnsure=function(d){ return (d && d._ck && !d.html) ? load(d._ck) : Promise.resolve(); };
var last=null;
try{ last=D[localStorage.getItem('wg.lastDoc')]||null; }catch(e){}
var order=[],i;
if(last&&last._ck) order.push(last._ck);
for(i in M.chunks) if(order.indexOf(i)<0) order.push(i);
var p=0;
function step(){
  if(p>=order.length){ window.__kcAllLoaded=true; return; }
  load(order[p++]).then(function(){ setTimeout(step,120); },function(){ setTimeout(step,400); });
}
if((location.search||'').indexOf('noprefetch')<0) setTimeout(step,2500);
})();
</script>"""


def patch_show(code):
    anchor = ("function show(id, push){\n"
              "  if(!DOCS[id]) return;\n"
              "  current=id;\n"
              "  const d=DOCS[id];\n"
              "  content.classList.remove('card-in');")
    assert code.count(anchor) == 1, "show() 锚点不唯一"
    repl = ("function show(id, push){\n"
            "  if(!DOCS[id]) return;\n"
            "  current=id;\n"
            "  const d=DOCS[id];\n"
            "  if(d._ck && !d.html){\n"
            "    content.classList.remove('card-in'); void content.offsetWidth;\n"
            "    content.innerHTML='<div style=\"padding:42px 18px;text-align:center;color:var(--dim)\">正在加载「'+String(d.t||'').replace(/[<>&\\\"']/g,'')+'」…</div>';\n"
            "    try{ document.getElementById('doc-title').textContent=d.t; }catch(e){}\n"
            "    window.__kcEnsure(d).then(function(){ if(current===id) show(id, push); }, function(){\n"
            "      if(current!==id) return;\n"
            "      content.innerHTML='<div style=\"padding:42px 18px;text-align:center\"><button class=\"tool-btn\" data-kcretry=\"1\">加载失败 · 点击重试</button></div>';\n"
            "      content.querySelector('[data-kcretry]').onclick=function(){ show(id, push); };\n"
            "    });\n"
            "    return;\n"
            "  }\n"
            "  _renderDoc(id, push);\n"
            "}\n"
            "function _renderDoc(id, push){\n"
            "  const d=DOCS[id];\n"
            "  content.classList.remove('card-in');")
    return code.replace(anchor, repl)


def patch_search(code):
    anchor = "      if(d.html && d.html.toLowerCase().indexOf(q)>=0) out.push("
    assert code.count(anchor) == 1, "搜索锚点不唯一"
    repl = ("      var ix=d._ix; if(ix===undefined) ix=d._ix=(typeof d.html==='string')?d.html.replace(/<[^>]*>/g,' ').toLowerCase():null;\n"
            "      if(ix && ix.indexOf(q)>=0) out.push(")
    return code.replace(anchor, repl)


def patch_check(code):
    anchor = "  if(_vidsCache) return _vidsCache;"
    assert code.count(anchor) == 1, "collectVideos 锚点不唯一"
    return code.replace(anchor, "  if(_vidsCache && window.__kcAllLoaded) return _vidsCache;")


def split_study(html_path, write=True):
    raw = open(html_path, encoding="utf-8").read()
    base = os.path.dirname(os.path.abspath(html_path))

    li = raw.find("const DOCS = ")
    assert li >= 0, "未找到 const DOCS"
    ls = raw.rfind("<script", 0, li)
    assert ls >= 0, "未找到主 script 开标签"
    le_end = raw.find("\n", li)
    line = raw[li:le_end]
    js = line[len("const DOCS = "):].rstrip()
    assert js.endswith(";"), "DOCS 行结尾异常"
    docs = json.loads(js[:-1])

    # 往返断言：重组后与原文档逐字段一致
    manifest, chunks, fields = split_docs(docs)
    rebuilt = {"__home__": docs["__home__"]}
    for k, rec in manifest.items():
        d = {f: val for f, val in zip(fields, rec["meta"]) if val is not None}
        d["html"] = chunks.get(rec["ck"], {}).get(k)
        rebuilt[k] = d
    a = json.dumps(docs, sort_keys=True, ensure_ascii=False)
    b = json.dumps(rebuilt, sort_keys=True, ensure_ascii=False)
    assert a == b, "往返校验失败！"

    global SLUGS
    SLUGS = {}
    for ck in chunks:
        if ck == "_core":
            continue
        s, i = slugify(ck), 2
        while s in SLUGS.values():
            s = "%s_%d" % (slugify(ck), i); i += 1
        SLUGS[ck] = s

    manifest_js, files, mh8 = build_assets(docs, fields, manifest, chunks)

    shell = raw[:ls] + '<script src="study-data/manifest.%s.js"></script>\n' % mh8 + \
        LOADER + "\n" + raw[ls:li] + raw[le_end + 1:]
    shell = patch_show(shell)
    shell = patch_search(shell)
    shell = patch_check(shell)

    if write:
        ddir = os.path.join(base, "study-data")
        os.makedirs(os.path.join(ddir, "c"), exist_ok=True)
        Path(os.path.join(ddir, "manifest.%s.js" % mh8)).write_text(manifest_js, encoding="utf-8")
        for fname, content in files.items():
            Path(os.path.join(ddir, "c", fname)).write_text(content, encoding="utf-8")
        Path(html_path).write_text(shell, encoding="utf-8")
    return {"docs": len(docs), "chunks": len(chunks), "mh8": mh8,
            "shell_bytes": len(shell.encode("utf-8")),
            "manifest_bytes": len(manifest_js.encode("utf-8")),
            "chunk_bytes": sum(len(c.encode("utf-8")) for c in files.values())}


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "study.html")
    st = split_study(target)
    print("split ok:", st)
