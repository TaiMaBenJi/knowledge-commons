#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""bundle_full_study.py · 把拆分的 study.html 反向重组为全量内联单文件

学习中心在网页端采用「shell + manifest + 按组内容块」的懒加载架构；
但桌面/移动客户端是「单文件释放后直接打开」，相对路径的 study-data/
不存在，懒加载必然 404 —— 客户端必须用自包含的全量单文件。

做法（split_study.py 的逆操作）：
  1) 把 <script src="study-data/manifest.*.js"></script> 换成内联 manifest；
  2) 把 study-data/c/*.js 的每个内容块以 <script> 内联追加到 </body> 前——
     加载器 load() 对已注册块走 `if(loaded[name]) return` 快速路径，
     不会发起任何网络/文件请求，file:// 下同样工作。

用法：
  python tools/bundle_full_study.py [输出路径，默认 clients/_full/study.html]
"""
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SHELL = ROOT / 'study.html'
DATA = ROOT / 'study-data'


def _inline_safe(js: str) -> str:
    """内联 <script> 安全化：JS 字符串/JSON 里的 </script 会提前终止脚本块，
    转成 <\\/script（在 JS 字符串与 JSON 中 \/ 等价于 /，语义不变）。"""
    return js.replace('</script', r'<\/script')


def main():
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / 'clients/_full/study.html'
    shell = SHELL.read_text(encoding='utf-8')

    m = re.search(r'<script src="study-data/(manifest\.[a-f0-9]+\.js)"></script>', shell)
    if not m:
        raise SystemExit('FATAL: study.html 里找不到 manifest script 引用（是否已是内联单文件？）')
    man_name = m.group(1)
    man_path = DATA / man_name
    if not man_path.is_file():
        raise SystemExit('FATAL: 缺少 %s' % man_path)
    manifest = man_path.read_text(encoding='utf-8')

    chunk_files = sorted((DATA / 'c').glob('*.js'))
    if not chunk_files:
        raise SystemExit('FATAL: study-data/c/ 下没有内容块')
    chunks = []
    for f in chunk_files:
        body = f.read_text(encoding='utf-8')
        if 'window.__kcChunk(' not in body:
            raise SystemExit('FATAL: %s 不是内容块格式' % f.name)
        chunks.append(body)

    # 1) manifest 内联（保留原始注释头）
    page = shell.replace(m.group(0), '<script>\n' + _inline_safe(manifest) + '\n</script>', 1)
    # 2) 内容块内联：追加到「最后一个」</body> 之前——shell 正文里还有
    #    16 个 </body> 是 JS 字符串中的 HTML 示例，绝不能注入到那里
    block = '<script>\n' + '\n</script>\n<script>\n'.join(_inline_safe(c) for c in chunks) + '\n</script>\n'
    cut = page.rfind('</body>')
    if cut < 0:
        raise SystemExit('FATAL: study.html 缺少 </body>')
    page = page[:cut] + block + page[cut:]

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page, encoding='utf-8')
    print('bundled →', out)
    print('  manifest:', man_name, len(manifest), 'bytes')
    print('  chunks:', len(chunks), 'files')
    print('  total:', len(page), 'bytes')


if __name__ == '__main__':
    main()
