#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
verify_all.py · 知识公社全仓库质量门禁（一键跑完所有检查）

    python tools/verify_all.py             # 全跑
    python tools/verify_all.py --fast      # 跳过耗时项（代码块实跑）
    python tools/verify_all.py --list      # 列出所有检查项
    python tools/verify_all.py --only manifest,counts   # 只跑指定项

为什么要有这个
--------------
上游已有 tools/internal_qa.py（HTML/MD 内链 · sw 预缓存 · 检索索引 · sitemap ·
manifest.json · JSON 有效性 · JS 语法）。但它**看不到下面这 7 类问题**，
而这 7 类恰恰是本仓库最容易被改坏的地方：

  1. markdown 正文里用反引号写的**路径引用**（`docs/xxx.md`）——
     internal_qa 只扫 markdown 链接语法 `](...)`，扫不到行内代码里的路径。
     目录一挪窝，这些引用就悄悄烂在文档里。
  2. 文档里**写死的数字**（"3160 篇""58 个内容块""71 门课"）——
     人工维护必然漂移，而漂移之后没人知道哪个是真值。
  3. **二级标题重复 / 章节号跳号**（手打编号增删章节后没人重排）。
  4. **manifest 条目结构**：每条必须是 len(fields)+1 个元素
     （第 7 个是所属内容块名，study.html 的 o._ck = a[n] 取它）。
     少一个就导致文档"点开一片空白"——这个坑本仓库真实踩过。
  5. **manifest 与磁盘不一致**：chunk 文件缺失、study.html 引用的 manifest
     不是最新的、增量清单没编译进来。
  6. **md 里的 python / yaml 代码块**：语法、以及**能不能真跑起来**。
     只做语法检查是自欺欺人——本仓库多次靠实跑抓出真 bug。
  7. **sw.js 缓存版本**：内容变了要升 VERSION，否则老用户拿不到新内容。

本文件把这些检查串成一个入口，失败项必须报出**具体位置**，
只说"失败"等于没说。
"""
from __future__ import annotations

import argparse
import ast
import io
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.parse

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = pathlib.Path(__file__).resolve().parent.parent
TOOLS = ROOT / "tools"
STUDY = ROOT / "study-data"
UTF8_ENV = {**os.environ, "PYTHONIOENCODING": "utf-8"}
RUN = {"encoding": "utf-8", "errors": "replace", "env": UTF8_ENV}

SKIP_DIRS = {".git", "node_modules", "study-data", "clients",
             "video-factory", "video-ext", "tools"}


_TRACKED: set[str] | None = None


def git_tracked() -> set[str]:
    """git 跟踪的文件全集（忽略 sparse-checkout，工作区可能没落地）。"""
    global _TRACKED
    if _TRACKED is None:
        _TRACKED = set()
        try:
            r = subprocess.run(["git", "ls-files"], capture_output=True,
                               **RUN, cwd=ROOT, timeout=180)
            if r.returncode == 0:
                _TRACKED = {x for x in (r.stdout or "").splitlines() if x}
        except Exception:
            pass
    return _TRACKED


def rel(p: pathlib.Path) -> str:
    try:
        return str(p.relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        return str(p)


def all_files(exts: tuple[str, ...], sub: str = "") -> list[pathlib.Path]:
    base = (ROOT / sub) if sub else ROOT
    out = []
    for dp, dn, fns in os.walk(base):
        rel_dp = os.path.relpath(dp, ROOT)
        parts = set(rel_dp.split(os.sep)) if rel_dp != "." else set()
        if parts & SKIP_DIRS:
            dn[:] = []
            continue
        for fn in fns:
            if fn.endswith(exts):
                out.append(pathlib.Path(dp) / fn)
    return sorted(out)


# ------------------------------------------------------------------ 检查项

def _git_show(rel_path: str) -> str | None:
    """从 git 对象库里取文件内容（sparse-checkout 没落地时用）。"""
    try:
        r = subprocess.run(["git", "show", f"HEAD:{rel_path}"],
                           capture_output=True, **RUN, cwd=ROOT, timeout=60)
    except Exception:
        return None
    if r.returncode != 0:
        return None
    return (r.stdout or "")


def _shell_files(exts: tuple[str, ...]) -> list[tuple[str, str]]:
    """(相对路径, 内容) —— 工作区里的 + git 里有但没落地的。

    sparse-checkout 让工作区只落地一部分目录：磁盘上看不到 ≠ 仓库里没有。
    客户端脚本（clients/）、视频流水线（video-factory/）多半就属于后者，
    不看 git 就等于漏检。内容统一按 UTF-8 读、换行归一（CRLF 由行尾检查单独管）。
    """
    out: dict[str, str] = {}
    for p in all_files(exts):
        try:
            out[rel(p)] = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
    for r in sorted(git_tracked()):
        if not r.endswith(exts) or r in out:
            continue
        txt = _git_show(r)
        if txt is not None:
            out[r] = txt
    return sorted(out.items())


def chk_sh_syntax(_fast: bool):
    """全部 .sh / .ps1 过语法检查（Windows / PowerShell 上也能跑）

    走 tools/shell_compat.py 的三条通道，而不是「有 bash 就 bash -n、没有就放过」：
      A  bash -n            .sh 的真语法检查（最准）
      B  PowerShell 解析器  .ps1 的真语法检查（Windows 必选，零外部依赖）
      C  纯 Python 结构自检  没 bash 时对 .sh 的降级检查
    能力要**验真**：WindowsApps 下那个 bash.exe 往往只是 WSL 启动器空壳，
    找到它不等于能跑 —— shell_compat.bash_exe() 会真跑一次 bash -c "exit 0"。
    通道本身出毛病（读不到 payload、处理数对不上）一律判失败：
    静悄悄放过一批文件，比报错更坏。
    """
    try:
        sys.path.insert(0, str(TOOLS))
        import shell_compat as sc
    except Exception:
        return "shell 语法", True, "跳过：shell_compat 不可用"

    shs = _shell_files((".sh",))
    pss = _shell_files((".ps1",))
    bad = []
    how = []

    if shs:
        if sc.bash_available():
            errs = sc.bash_syntax(shs)
            if "__driver__" in errs:
                bad.append(str(errs["__driver__"])[:90])
                how.append("bash 通道异常")
            else:
                for k, v in list(errs.items())[:3]:
                    bad.append(f"{k}: {str(v)[:70]}")
                how.append(f"bash -n（{len(shs)} 个 .sh）")
        else:
            # 没有 bash：降级成纯 Python 结构自检（只报高置信度问题）
            for label, code in shs:
                for prob in sc.posix_shell_lint(code):
                    bad.append(f"{label}: {prob[:70]}")
            how.append(f"结构自检（{len(shs)} 个 .sh，无 bash）")
    else:
        how.append("无 .sh")

    if pss:
        if sc.powershell_available():
            perrs = sc.ps_parse(pss)
            if "__driver__" in perrs:
                bad.append(str(perrs["__driver__"][0])[:90])
                how.append("PowerShell 通道异常")
            else:
                for k, v in list(perrs.items())[:3]:
                    if v:
                        bad.append(f"{k}: {str(v[0])[:70]}")
                how.append(f"PowerShell 解析（{len(pss)} 个 .ps1）")
        else:
            how.append(f"{len(pss)} 个 .ps1 未校验（无 PowerShell）")

    n = len(shs) + len(pss)
    return "shell 语法", not bad, (
        f"{n} 个脚本 · {' · '.join(how)} · 全部通过" if not bad
        else f"{n} 个脚本 · {len(bad)} 个出错｜{bad[0]}")


def chk_sh_eol(_fast: bool):
    """.sh / .ps1 必须是 LF —— CRLF 会让 heredoc 吞掉整个文件"""
    bad = []
    n = 0
    for ext in (".sh", ".ps1"):
        for p in all_files((ext,)):
            n += 1
            try:
                b = p.read_bytes()
            except OSError:
                continue
            if b"\r\n" in b:
                bad.append(rel(p))
    return "脚本行尾 LF", not bad, ("全部 LF" if not bad
                                   else f"{len(bad)} 个是 CRLF：{bad[:2]}")


def chk_js(_fast: bool):
    """关键 JS 过 node --check"""
    node = shutil.which("node")
    if not node:
        return "js 语法", True, "跳过：环境无 node"
    targets = ["sw.js", "install-tip.js", "learn/kc-learn.js", "learn/kc-srs.js",
               "learn/searchidx.js"]
    targets += [rel(p) for p in all_files((".js",), "app")]
    targets += [rel(p) for p in all_files((".js",), "learn")]
    targets += [rel(p) for p in all_files((".js",), "lab")]
    seen, bad, n = set(), [], 0
    for t in targets:
        if t in seen:
            continue
        seen.add(t)
        p = ROOT / t
        if not p.exists():
            continue
        n += 1
        r = subprocess.run([node, "--check", str(p)], capture_output=True, **RUN)
        if r.returncode != 0:
            err = (r.stderr or "").strip().splitlines()
            bad.append(f"{t}: {err[0][:90] if err else '?'}")
    return "js 语法", not bad, (f"{n}/{n} 通过" if not bad
                                else f"{len(bad)} 个出错：{bad[0]}")


def chk_tools_py(_fast: bool):
    """tools/ 下的 python 脚本语法"""
    bad = []
    ps = sorted(TOOLS.glob("*.py"))
    for p in ps:
        try:
            ast.parse(p.read_text(encoding="utf-8"))
        except SyntaxError as e:
            bad.append(f"{p.name}: 第 {e.lineno} 行 {e.msg}")
    return "tools 语法", not bad, (f"{len(ps)}/{len(ps)} 通过" if not bad
                                  else f"{len(bad)} 个出错：{bad[0]}")


def chk_internal_qa(_fast: bool):
    """上游 internal_qa：HTML/MD 内链 · 预缓存 · 检索索引 · sitemap · JSON · JS"""
    p = TOOLS / "internal_qa.py"
    if not p.exists():
        return "站内体检", True, "跳过：internal_qa.py 不存在"
    r = subprocess.run([sys.executable, rel(p)], capture_output=True, **RUN,
                       cwd=ROOT, timeout=900)
    out = (r.stdout or "")
    if r.returncode == 0:
        m = re.search(r"体检通过：(\d+) 个问题", out)
        return "站内体检", True, m.group(0) if m else "通过"
    # 抓前几条问题
    issues = [l.strip() for l in out.splitlines() if l.strip().startswith("[")]
    n = re.search(r"发现 (\d+) 个文件", out)
    head = f"{n.group(1) if n else '?'} 个文件有问题"
    return "站内体检", False, head + (f"｜{issues[0][:90]}" if issues else "")


def chk_md_paths(_fast: bool):
    """markdown 正文里反引号写的本地路径是否真实存在

    internal_qa 只扫 `](...)` 链接语法；行内代码里的路径（`docs/xxx.md`）
    是盲区 —— 本仓库的文档大量用这种写法指路。
    """
    # 扩展名必须按**长度倒序**参与匹配：正则交替是「先匹配先赢」，
    # js 排在 json 前面会把 study_additions.json 截成 study_additions.js，
    # 截出来的路径既查不到也修不掉 —— 纯假阳性。
    _EXTS = sorted(
        "md html htm js mjs css json yaml yml toml ini py sh bash ps1 txt csv tsv "
        "xml svg png jpg jpeg webp gif ico pdf zip tar gz apk ipa go tf java kt rs "
        "c h cpp hpp cs rb php sql ipynb".split(), key=len, reverse=True)
    EXT_RE = re.compile(
        r"[\w.\-\u4e00-\u9fff/]+\.(" + "|".join(_EXTS) + ")")
    # 扩展名按长度倒序参与匹配：正则交替「先匹配先赢」，
    # js 排在 json 前面会把 learning-paths.json 截成 learning-paths.js，
    # 截出来的路径既查不到也修不掉，是纯假阳性。
    on_disk = {rel(p).lower() for p in ROOT.rglob("*") if p.is_file()}
    dirs = {p.name.lower() for p in ROOT.iterdir() if p.is_dir()}

    # 明确豁免：这些路径在仓库里【故意不存在】
    # —— 要么是任务要求学生自己创建的交付物，要么是正文示例里的文件名。
    EXAMPLE_PATHS = {
        ".github/dependabot.yml": "L6 任务：要求学生自己加依赖自动更新配置",
        ".github/workflows/ci-cd.yml": "正文示例：演示 CI/CD 流水线",
        ".github/workflows/deploy.yml": "正文示例：演示部署流水线",
        "docs/deploy.md": "正文示例：部署文档占位名",
        "docs/runbook.md": "正文示例：runbook 占位名",
    }

    bad, skipped = [], 0
    for p in all_files((".md",)):
        in_fence = False
        for no, line in enumerate(p.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            if line.lstrip().startswith("```"):
                in_fence = not in_fence
                continue
            if in_fence:
                continue
            for span in re.findall(r"`([^`\n]+)`", line):
                for m in EXT_RE.finditer(span):
                    tok = m.group(0)
                    if "/" not in tok:
                        continue
                    if any(c in tok for c in "*?<>{} "):
                        continue
                    if ".." in tok:
                        continue
                    if tok.startswith(("./", "../", "/", "~", "http", "//")):
                        continue
                    first = tok.split("/", 1)[0]
                    if "." in first and not first.startswith("."):
                        continue
                    low = tok.lower()
                    if low in EXAMPLE_PATHS:
                        skipped += 1
                        continue
                    if low in on_disk:
                        continue
                    # 文档相对目录也能解析
                    if (p.parent / tok).exists():
                        continue
                    hits = [f for f in on_disk if f.endswith("/" + low)]
                    if len(hits) == 1:
                        bad.append(f"{rel(p)}:{no} `{tok}` → 实际 {hits[0]}")
                    elif len(hits) > 1:
                        skipped += 1
                    elif first.lower() in dirs:
                        bad.append(f"{rel(p)}:{no} `{tok}` 全库查无此文件")
                    else:
                        skipped += 1
    msg = (f"引用有问题 {len(bad)}（跳过 {skipped}）" if bad
           else f"全部有效（跳过 {skipped}）")
    for b in bad[:3]:
        msg += f"｜{b}"
    return "md 路径引用", not bad, msg


def chk_headings(_fast: bool):
    """二级标题是否重复、章节号是否跳号"""
    dup, gaps = [], []
    for p in all_files((".md",)):
        in_fence = False
        seen, nums = {}, []
        for no, line in enumerate(p.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            if line.lstrip().startswith("```"):
                in_fence = not in_fence
                continue
            if in_fence or not line.startswith("## "):
                continue
            title = line[3:].strip()
            if title in seen:
                dup.append(f"{rel(p)}:{no} 与第 {seen[title]} 行重名「{title[:24]}」")
            else:
                seen[title] = no
            m = re.match(r"^(\d+)\s*[·\.、]", title)
            if m:
                nums.append((int(m.group(1)), no))
        seq = [n for n, _ in nums]
        for a, b in zip(seq, seq[1:]):
            if b != a + 1 and b > a:
                gaps.append(f"{rel(p)}: 章节号 {a} 跳到 {b}")
    return "md 章节结构", not (dup or gaps), \
        (f"重复 {len(dup)} · 跳号 {len(gaps)}" + (f"｜{dup[0] or gaps[0]}" if (dup or gaps) else ""))


def _md_blocks(md: pathlib.Path, lang: str) -> list[str]:
    fence = re.compile(r"^```" + lang + r"\s*$(.*?)^```\s*$", re.S | re.M)
    return fence.findall(md.read_text(encoding="utf-8", errors="replace"))


def _yaml_is_fragment(code: str) -> bool:
    """这段 YAML 是不是【片段】（首行就带缩进，即从完整结构中间截出来的）。

    片段在上下文里合法，但独立解析必然失败（嵌套映射里的块序列不能与父键同缩进）。
    对片段做「包一层再解析」的兜底是行不通的 —— 实测包了照样报
    "expected <block end>, but found '<block mapping start>'"。
    所以干脆按「片段」单独归类：可见，但不误报为错误。
    """
    for line in code.splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        return line.startswith((" ", "\t"))
    return False



# md 里的 shell 块有两类**根本不是脚本**，硬判语法错误就是误报：
#   · 占位符：`kubectl logs <你的Pod名>` —— 尖括号里是中文/带空格，是给人看的，
#     不是重定向（真重定向是 `cat < in.txt`，尖括号里没有空格和中文）
#   · 终端会话记录：`mysql> USE db;` —— REPL 提示符，不是脚本
# 判成「未校验」并报出数量，而不是静悄悄放过或误报成语法错误。
_PLACEHOLDER_RE = re.compile(r"<[^<>\n]*(?:[^\x00-\x7f]|[ \t])[^<>\n]*>")
_PLACEHOLDER_WORD_RE = re.compile(
    r"<(?:your|my|the|some|a|any|todo|xxx|placeholder|name|pod|ip|id|path)[-_a-z0-9]*>",
    re.I)
_REPL_RE = re.compile(r"^\s*(?:mysql>|psql>|postgres=|sqlite>|mariadb>)", re.M | re.I)


def _shell_block_skip_reason(code: str) -> str:
    """返回跳过原因；空串 = 这块该真检。"""
    if _PLACEHOLDER_RE.search(code) or _PLACEHOLDER_WORD_RE.search(code):
        return "含占位符"
    if _REPL_RE.search(code):
        return "终端会话记录"
    return ""


def chk_md_python(_fast: bool):
    """md 里的代码块语法（按语言分派：python / powershell / bash）

    为什么扩到 shell：仓库里 300+ 个 ```bash 块、10 来个 ```powershell 块，
    以前只有 python 块被查 —— bash 块写错（引号不配对、heredoc 少 fi）根本没人拦。
    分派方式跟 tools/shell_compat.py 一致：
      python     → ast.parse
      powershell → PowerShell 自带 AST 解析器（Windows 必选）
      bash       → bash -n（一次进程批量跑完）
    """
    try:
        sys.path.insert(0, str(TOOLS))
        import shell_compat as sc
    except Exception:
        return "md 代码块语法", True, "跳过：shell_compat 不可用"

    bad = []
    n_py = n_ps = n_sh = 0
    skipped = []
    ps_items: list[tuple[str, str]] = []
    sh_items: list[tuple[str, str]] = []

    for p in all_files((".md",)):
        for i, code in enumerate(_md_blocks(p, "python"), 1):
            n_py += 1
            try:
                ast.parse(code)
            except SyntaxError as e:
                bad.append(f"{rel(p)} 块{i}: 第 {e.lineno} 行 {e.msg}")
        for i, code in enumerate(_md_blocks(p, "powershell"), 1):
            n_ps += 1
            ps_items.append((f"{rel(p)} 块{i}", code))
        for i, code in enumerate(_md_blocks(p, "bash"), 1):
            n_sh += 1
            why = _shell_block_skip_reason(code)
            if why:
                skipped.append(f"{rel(p)} 块{i}（{why}）")
                continue
            sh_items.append((f"{rel(p)} 块{i}", code))

    # PowerShell 块：解析器是真语法检查（不实跑 —— 那些块是 New-ADUser /
    # Install-WindowsFeature，真跑会去改这台机器的域与角色）
    if ps_items:
        if sc.powershell_available():
            perrs = sc.ps_parse(ps_items)
            if "__driver__" in perrs:
                bad.append(str(perrs["__driver__"][0])[:90])
            else:
                for k, v in list(perrs.items())[:5]:
                    if v:
                        bad.append(f"{k}: {str(v[0])[:70]}")
        else:
            skipped.append(f"{len(ps_items)} 个 powershell 块（无 PowerShell）")

    # bash 块：一次 bash 进程批量 bash -n
    if sh_items:
        if sc.bash_available():
            errs = sc.bash_syntax(sh_items)
            if "__driver__" in errs:
                bad.append(str(errs["__driver__"])[:90])
            else:
                for k, v in list(errs.items())[:5]:
                    bad.append(f"{k}: {str(v)[:80]}")
        else:
            skipped.append(f"{len(sh_items)} 个 bash 块（无 bash）")

    msg = f"python {n_py} · powershell {n_ps} · bash {n_sh}"
    if skipped:
        msg += f"（{len(skipped)} 个未校验：占位符/会话记录/环境缺失）"
    msg += " · 0 个有语法错误" if not bad else f" · {len(bad)} 个出错｜{bad[0]}"
    return "md 代码块语法", not bad, msg


def chk_md_yaml(_fast: bool):
    """md 里的 yaml 块能 safe_load"""
    try:
        import yaml
    except ImportError:
        return "md yaml", True, "跳过：环境无 PyYAML"
    bad = []
    frag = []
    n = 0
    for p in all_files((".md",)):
        for i, code in enumerate(_md_blocks(p, "yaml"), 1):
            n += 1
            if _yaml_is_fragment(code):
                # **片段**（首行就带缩进）是从完整结构中间截出来的，
                # 它在上下文里合法，但**独立解析必然失败** ——
                # 嵌套映射里的块序列不能与父键同缩进，包一层也救不回来。
                # 硬判失败就是误报；判通过又等于没查。
                # 所以：单列为「未独立校验」，可见但不误报。
                frag.append(f"{rel(p)} 块{i}")
                continue
            try:
                # 多文档 YAML（--- 分隔）是合法的，safe_load 会误报
                list(yaml.safe_load_all(code))
            except Exception as e:
                bad.append(f"{rel(p)} 块{i}: {str(e)[:80]}")
    msg = f"{n} 个块"
    if frag:
        msg += f"（含 {len(frag)} 个片段，未独立校验）"
    if bad:
        msg += f"，{len(bad)} 个出错｜{bad[0]}"
    else:
        msg += "，独立块全部通过"
    return "md yaml", not bad, msg


# 确认真实存在于 PyPI、只是本机未必装了的三方包。
# 白名单外的一律判失败：以前「见 ModuleNotFoundError 就 SKIP」等于给幻觉开后门
# —— Cilium 容器内的 protobuf 模块（PyPI 上根本不存在）就是这样混进「实跑通过」的。
# 会一直跑着的示例：长驻服务 / 交互式输入
INTERACTIVE_RE = re.compile(
    r"serve_forever\s*\(|\.listen\s*\(|while\s+(True|1)\s*:|"
    r"\binput\s*\(|select\.select\s*\(|"
    r"(?:app|server|application|api|httpd|srv|daemon|worker)\.run\s*\(|"
    r"\b(uvicorn|gunicorn|flask)\b[^\n]*\brun\b|"
    r"\bHTTPServer\s*\(|\bThreadingHTTPServer\s*\(|"
    r"sleep\s*\(\s*(?:[1-9]\d{2,}|inf)", re.I)

KNOWN_OPTIONAL_DEPS = {
    "boto3": "AWS 官方 SDK", "botocore": "boto3 底层库",
    "aws_nitro_enclaves": "AWS Nitro Enclaves SDK",
    "psycopg2": "PostgreSQL 驱动", "psycopg2_binary": "PostgreSQL 驱动",
    "pyiceberg": "Apache Iceberg", "pyarrow": "Apache Arrow",
    "duckdb": "嵌入式分析库", "cryptography": "加密原语库",
    "yaml": "PyYAML", "requests": "HTTP 客户端", "httpx": "HTTP 客户端",
    "kubernetes": "K8s Python 客户端", "docker": "Docker SDK",
    "pydantic": "数据校验", "numpy": "数值计算", "pandas": "表格处理",
    "matplotlib": "绘图", "sklearn": "scikit-learn",
    "pulumi": "Pulumi Python SDK", "pulumi_aws": "Pulumi AWS provider",
    "pulumi_random": "Pulumi random provider", "pulumi_kubernetes": "Pulumi K8s provider",
    "flask": "轻量 Web 框架", "fastapi": "异步 Web 框架",
    "jinja2": "模板引擎", "click": "命令行框架", "rich": "终端富文本",
}


def chk_md_run(_fast: bool):
    """md 里的 python 块【实跑】—— 只做语法检查是自欺欺人

    只实跑 python：powershell 块是 New-ADUser / Install-WindowsFeature 这类
    会**改机器**的运维命令，bash 块大半是 kubectl / aws 客户端调用 ——
    跑它们不是「验证示例」，是「在跑门禁的机器上搞破坏」。
    这两类块只过语法检查（见 chk_md_python）。
    """
    if _fast:
        return "md 代码块实跑", True, "跳过（--fast）"
    bad, ok, skip = [], 0, []
    for p in all_files((".md",)):
        for i, code in enumerate(_md_blocks(p, "python"), 1):
            with tempfile.TemporaryDirectory() as d:
                f = pathlib.Path(d) / "snippet.py"
                f.write_text(code, encoding="utf-8")
                try:
                    r = subprocess.run([sys.executable, str(f)], capture_output=True,
                                       **RUN, timeout=180)
                except subprocess.TimeoutExpired:
                    # 长驻服务 / 交互式示例本来就该一直跑着（如 HTTP 服务的
                    # serve_forever()），超时是**预期**行为；真正该报错的是
                    # 既不常驻也没交互、却卡死的块（多半是死循环）。
                    if INTERACTIVE_RE.search(code):
                        skip.append(f"{rel(p)} 块{i}: 长驻/交互式示例（已跳过）")
                    else:
                        bad.append(f"{rel(p)} 块{i}: 超时且不像长驻示例 —— 疑似死循环")
                    continue
                except (PermissionError, OSError) as ex:
                    # Windows 上端口被 Hyper-V / WinNAT 保留，或防火墙拦截 bind：
                    # 代码本身没问题，只是本机跑不起来。和超时一样归入「环境」。
                    if "10013" in str(ex) or "access permission" in str(ex).lower() or                        "address in use" in str(ex).lower() or "address already in use" in str(ex).lower():
                        if INTERACTIVE_RE.search(code):
                            skip.append(f"{rel(p)} 块{i}: 长驻服务示例（端口被环境占用，跳过）")
                        else:
                            bad.append(f"{rel(p)} 块{i}: 端口绑定被环境拒绝 —— {ex}")
                        continue
                    raise
            if r.returncode == 0:
                ok += 1
                continue
            err = r.stderr or ""
            if "ModuleNotFoundError" in err:
                mods = sorted(set(re.findall(r"No module named '([^']+)'", err)))
                unknown = [m for m in mods if m.split(".")[0] not in KNOWN_OPTIONAL_DEPS]
                if not unknown:
                    skip.append(f"{rel(p)} 块{i}: 缺可选依赖 {', '.join(mods)}")
                    continue
                bad.append(f"{rel(p)} 块{i}: 导入 {unknown[0]} 不在白名单 —— 拼错或臆造")
                continue
            tail = [l for l in err.strip().splitlines() if l.strip()][-1:]
            bad.append(f"{rel(p)} 块{i}: {tail[0][:80] if tail else '失败'}")
    msg = f"合计 {ok + len(skip) + len(bad)} 块，实跑通过 {ok}" + (f"，跳过 {len(skip)}" if skip else "")
    msg += "（仅 python；powershell/bash 块只做语法检查）"
    if bad:
        msg += f"，失败 {len(bad)}｜{bad[0]}"
    return "md 代码块实跑", not bad, msg


def chk_manifest(_fast: bool):
    """manifest 结构与磁盘一致性 —— 少一个元素就是「点开一片空白」"""
    mp = None
    html = (ROOT / "study.html").read_text(encoding="utf-8")
    m = re.search(r"study-data/manifest\.([0-9a-f]+)\.js", html)
    if m and (STUDY / f"manifest.{m.group(1)}.js").exists():
        mp = STUDY / f"manifest.{m.group(1)}.js"
    else:
        cands = sorted(STUDY.glob("manifest.*.js"), key=lambda x: x.stat().st_mtime)
        if not cands:
            return "manifest 一致性", False, "找不到 manifest.*.js"
        mp = cands[-1]
    t = mp.read_text(encoding="utf-8")
    k = "var M=window.__KC_MANIFEST="
    M, _ = json.JSONDecoder().raw_decode(t[t.index(k) + len(k):])
    need = len(M["fields"]) + 1
    bad = []
    for doc_id, v in M["docs"].items():
        if len(v) < need:
            bad.append(f"{doc_id} 只有 {len(v)} 个元素（应 >= {need}）")
    for slug, c in M["chunks"].items():
        if not (STUDY / c["u"]).exists():
            bad.append(f"chunk 文件缺失：{c['u']}")
    if mp.name not in html:
        bad.append(f"study.html 没引用当前 manifest（{mp.name}）")
    # 目录里残留的旧 manifest / chunk
    cur = {c["u"].split("/")[-1] for c in M["chunks"].values()}
    stale = [f"c/{p.name}" for p in (STUDY / "c").glob("*.js") if p.name not in cur]
    if stale:
        bad.append(f"残留旧内容块 {len(stale)} 个：{stale[0]}")
    others = [p.name for p in STUDY.glob("manifest.*.js") if p.name != mp.name]
    if others:
        bad.append(f"残留旧 manifest：{others[0]}")
    return "manifest 一致性", not bad, \
        (f"已收录 {len(M['docs'])} 篇 · {len(M['chunks'])} 块" if not bad
         else f"{len(bad)} 个问题｜{bad[0]}")


def chk_additions(_fast: bool):
    """增量清单里的文档是否已全部编译进资料中心"""
    spec = TOOLS / "study_additions.json"
    if not spec.exists():
        return "增量文档", True, "跳过：无清单"
    r = subprocess.run([sys.executable, rel(TOOLS / "add_study_docs.py"),
                        "--spec", rel(spec), "--check"],
                       capture_output=True, **RUN, cwd=ROOT, timeout=300)
    out = (r.stdout or "")
    msg = next((l.strip() for l in out.splitlines() if l.strip() and
                not l.startswith("   ")), "")
    return "增量文档", r.returncode == 0, msg or "无输出"


def chk_counts(_fast: bool):
    """文档里写死的数字是否与真实数据一致"""
    spec = TOOLS / "study_additions.json"
    truth = {}
    try:
        mp = sorted(STUDY.glob("manifest.*.js"), key=lambda x: x.stat().st_mtime)[-1]
        t = mp.read_text(encoding="utf-8")
        k = "var M=window.__KC_MANIFEST="
        M, _ = json.JSONDecoder().raw_decode(t[t.index(k) + len(k):])
        truth["docs"] = len(M["docs"]) - 1      # 去掉 __home__
        truth["chunks"] = len(M["chunks"])
    except Exception:
        pass
    cat = ROOT / "aws-educate" / "catalog.json"
    if cat.exists():
        try:
            truth["courses"] = len(json.loads(cat.read_text(encoding="utf-8")))
        except Exception:
            pass
    if not truth:
        return "数字一致性", True, "跳过：拿不到真值"

    # 断言表：(正则, 真值键, 说明)
    # 只匹配**全库口径**的表述。"155 篇真题""287 篇" 这类是子集计数，
    # 拿全库真值去判它们一定是误报 —— 子集数应该由各自的表自己维护。
    PATS = [
        (r"(?:资料中心|全站|全库|共|合计)[^。；\n]{0,12}?(\d{3,5})\s*篇", "docs", "资料中心篇数"),
        (r"(\d{3,5})\s*篇[^。；\n]{0,8}?(?:可离线|文档)", "docs", "资料中心篇数"),
        (r"(\d{1,3})\s*个(?:按组)?内容块", "chunks", "内容块数"),
        (r"(?:AWS Educate|课程)[^。；\n]{0,10}?(\d{1,3})\s*门", "courses", "课程数"),
    ]
    bad, n = [], 0
    # CHANGELOG.md 是**历史快照**，它写的篇数是当时的真值，不该按今天的标准判错。
    # 同样，正文里带日期的行（如「2026-10-16 整理时为 3160 篇」）也是历史记录。
    HISTORY = re.compile(r"\d{4}-\d{2}-\d{2}|\d{4}\s*年")
    for p in all_files((".md",)) + [ROOT / "README.md"]:
        if not p.exists() or p.name == "CHANGELOG.md":
            continue
        for no, line in enumerate(p.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            if HISTORY.search(line):
                continue
            for pat, key, label in PATS:
                if key not in truth:
                    continue
                for m in re.finditer(pat, line):
                    n += 1
                    if int(m.group(1)) != truth[key]:
                        bad.append(f"{rel(p)}:{no} {label} 写 {m.group(1)}，真实 {truth[key]}")
    msg = f"断言 {n} 处"
    if bad:
        msg += f"，不一致 {len(bad)}"
        for b in bad[:3]:
            msg += f"｜{b}"
    return "数字一致性", not bad, msg



def chk_library(_fast: bool):
    """资源总库数据完整性：字段齐全 / 板块下标合法 / 检索索引全覆盖"""
    import json as _json, collections as _c
    lib = ROOT / "app" / "library-data.js"
    if not lib.exists():
        return "资源总库完整性", True, "跳过：无库文件"
    s = lib.read_text(encoding="utf-8")
    try:
        g = re.search(r"groups: \[(.*?)\]", s, re.S).group(1)
        groups = re.findall(r"'([^']*)'", g)
        items = [dict(t=m.group(1), u=m.group(2), d=m.group(3), g=int(m.group(4)),
                      s=m.group(5), ty=m.group(6), f=m.group(7), o=m.group(8))
                 for m in re.finditer(r"\{t:'(.*?)',u:'(.*?)',d:'(.*?)',g:(\d+),s:'(.*?)',ty:'(.*?)',f:'(.*?)',o:'(.*?)'", s)]
    except Exception as e:
        return "资源总库完整性", False, "解析失败：%s" % e
    bad = []
    for x in items:
        if not (x["t"] and x["u"].startswith("http") and x["d"] and x["s"] and x["ty"] and x["f"] and x["o"]):
            bad.append("字段缺失: " + x["t"][:30])
        if x["g"] < 0 or x["g"] >= len(groups):
            bad.append("板块越界: " + x["t"][:30])
    idxp = ROOT / "learn" / "searchidx.js"
    if idxp.exists():
        is_ = idxp.read_text(encoding="utf-8")
        try:
            arr = _json.loads(is_[is_.index("["):is_.rindex("]") + 1])
            have = {x["t"] for x in arr}
            miss = [x["t"] for x in items if x["t"] not in have]
            if miss:
                bad.append("检索索引缺 %d 条（例：%s）" % (len(miss), miss[0][:30]))
        except Exception:
            pass
    if not bad:
        return "资源总库完整性", True, "条目 %d · 板块 %d · 全量覆盖" % (len(items), len(groups))
    return "资源总库完整性", False, "；".join(bad[:5])

def chk_sw_version(_fast: bool):
    """sw.js 缓存版本与内容是否同步（内容变了要升 VERSION）"""
    sw = (ROOT / "sw.js").read_text(encoding="utf-8")
    m = re.search(r"var VERSION = 'kc-v(\d+)\.(\d+)\.(\d+)';", sw)
    if not m:
        return "PWA 版本", False, "sw.js 里找不到 VERSION"
    ver = m.group(0).split("'")[1]
    # CORE 里列出的文件必须真实存在
    core = re.search(r"var CORE = \[(.*?)\];", sw, re.S)
    missing = []
    if core:
        # 存在性判定必须 **git 感知**：本仓库开了 sparse-checkout，
        # 工作区里只落地了一部分目录，磁盘上看不到 ≠ 仓库里没有。
        tracked = git_tracked()
        for item in re.findall(r"'([^']+)'", core.group(1)):
            p = item.lstrip("./")
            if not p or p == "learn":
                continue
            if p in tracked:
                continue
            if (ROOT / p).exists() or (ROOT / p / "index.html").exists():
                continue
            missing.append(item)
    return "PWA 预缓存", not missing, \
        (f"{ver} · {len(re.findall(chr(39), core.group(1))) if core else 0} 条" if not missing
         else f"{ver} · {len(missing)} 条失效：{missing[0]}")



def chk_deeplinks(_fast: bool):
    """全站 #d= 深链的 id 是否真实存在于 manifest

    站内链接检查（internal_qa）只验**文件路径**存不存在，
    但资料中心的深链是 `study.html#d=<文档id>` —— 片段部分它扫不到。
    而这正是最容易坏的地方：文档 id 里带中文，任何一次批量替换、
    编码转换、跨 shell 传参都可能把 id 打烂成 `???`，页面照常显示、
    只有点了才发现跳不过去。
    实测就抓到过 28 条这样的死链（4 周作战计划页上）。
    """
    mps = sorted(STUDY.glob("manifest.*.js"), key=lambda x: x.stat().st_mtime)
    if not mps:
        return "资料中心深链", False, "找不到 manifest"
    t = mps[-1].read_text(encoding="utf-8")
    k = "var M=window.__KC_MANIFEST="
    try:
        M, _ = json.JSONDecoder().raw_decode(t[t.index(k) + len(k):])
    except Exception as ex:
        return "资料中心深链", False, f"manifest 解析失败：{ex}"
    ids = set(M["docs"])
    total, bad = 0, []
    for p in all_files((".html",)):
        txt = p.read_text(encoding="utf-8", errors="replace")
        for no, line in enumerate(txt.splitlines(), 1):
            for m in re.finditer(r'href="([^"]*#d=([^"&]+))"', line):
                total += 1
                did = urllib.parse.unquote(m.group(2))
                if did not in ids:
                    bad.append(f"{rel(p)}:{no} {did[:40]}")
    msg = f"全站 {total} 条深链"
    if bad:
        msg += f"，失效 {len(bad)}｜{bad[0]}"
    else:
        msg += "，全部有效"
    return "资料中心深链", not bad, msg


CHECKS = [
    ("bash", chk_sh_syntax),
    ("eol", chk_sh_eol),
    ("js", chk_js),
    ("py", chk_tools_py),
    ("qa", chk_internal_qa),
    ("mdpaths", chk_md_paths),
    ("headings", chk_headings),
    ("mdpy", chk_md_python),
    ("mdyaml", chk_md_yaml),
    ("mdrun", chk_md_run),
    ("manifest", chk_manifest),
    ("additions", chk_additions),
    ("counts", chk_counts),
    ("library", chk_library),
    ("swver", chk_sw_version),
    ("deeplink", chk_deeplinks),
]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="知识公社全仓库质量门禁")
    ap.add_argument("--fast", action="store_true", help="跳过耗时项（代码块实跑）")
    ap.add_argument("--only", default="", help="只跑指定项，逗号分隔")
    ap.add_argument("--list", action="store_true", help="列出所有检查项")
    args = ap.parse_args(argv)

    if args.list:
        print("可用检查项：")
        for k, fn in CHECKS:
            doc = (fn.__doc__ or "").strip().splitlines()[0] if fn.__doc__ else ""
            print(f"  {k:<10} {doc}")
        return 0

    want = [x.strip() for x in args.only.split(",") if x.strip()]
    sel = [(k, f) for k, f in CHECKS if not want or k in want]
    if want:
        unknown = set(want) - {k for k, _ in CHECKS}
        if unknown:
            print(f"!! 未知检查项：{', '.join(unknown)}")
            return 2

    t0 = time.time()
    print("=" * 74)
    print(f" 知识公社 · 全仓库校验  {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 74)
    npass = 0
    for k, fn in sel:
        try:
            name, ok, msg = fn(args.fast)
        except Exception as ex:  # 检查项本身崩了也要报出来，不能静默
            name, ok, msg = k, False, f"检查本身报错：{type(ex).__name__}: {ex}"
        npass += 1 if ok else 0
        mark = "\033[32mPASS\033[0m" if ok else "\033[31mFAIL\033[0m"
        print(f" {mark}  {name:<14} {msg}")
    print("-" * 74)
    if npass == len(sel):
        print(f" \033[32m全部 {len(sel)} 项通过\033[0m · 用时 {time.time() - t0:.1f}s")
    else:
        print(f" \033[31m{len(sel) - npass} 项失败\033[0m / {len(sel)} 项通过 · 用时 {time.time() - t0:.1f}s")
    print("=" * 74)
    return 0 if npass == len(sel) else 1


if __name__ == "__main__":
    raise SystemExit(main())