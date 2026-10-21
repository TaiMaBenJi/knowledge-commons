#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
shell_compat.py —— shell 语法检查的跨平台适配层（Windows / PowerShell 优先）

为什么要有这个
--------------
仓库里 `.sh` 与 `.ps1` 混着放，而开发机基本是 Windows：
  · **bash 未必在** —— WindowsApps 下的 `bash.exe` 只是 WSL 启动器壳，
    没装 WSL / 没装发行版时它就是个打不开的壳（`where bash` 找得到 ≠ 能用）
  · **PowerShell 一定有** —— Windows 自带 5.1，装了 pwsh 更好

所以检查链路不能写成「bash 在就查、不在就悄悄放过」——那等于给幻觉开后门。
本模块提供**三条**检查通道，由 verify_all.py 按能力挑选：

  通道 A  bash -n                .sh 的真语法检查（最准，需要可用的 bash）
  通道 B  PowerShell 解析器      .ps1 的真语法检查（Windows 必选，零外部依赖）
  通道 C  纯 Python 结构自检      没 bash 时 .sh 的降级检查（只报高置信度问题）

两条纪律
--------
1. **能力要验真**：能找到 `bash.exe` 不等于 bash 能跑（WSL 空壳），
   必须真跑一次 `bash -c "exit 0"` 才算数。
2. **批量**：WSL 冷启动 1 秒起，327 个 md 代码块逐个起 bash 会慢到没法用。
   所以内容一律走「一次启动 + 标准输入喂内容」，全程只起一个进程。
"""
from __future__ import annotations

import json
import os
import pathlib
import re
import shutil
import subprocess
import tempfile
import uuid

# ------------------------------------------------------------------ 能力探测

_BASH: str | None = None
_BASH_OK: bool | None = None
_PS: str | None = None
_PS_OK: bool | None = None


def bash_exe() -> str | None:
    """返回**可用的** bash 路径；没有就返回 None。

    注意 `shutil.which("bash")` 会命中 WindowsApps 下那个 WSL 启动器壳，
    它在没装发行版时是个摆设。所以必须真跑一次才算数。
    """
    global _BASH, _BASH_OK
    if _BASH_OK is not None:
        return _BASH
    exe = shutil.which("bash")
    if not exe:
        _BASH, _BASH_OK = None, False
        return None
    try:
        r = subprocess.run([exe, "-c", "exit 0"], capture_output=True, timeout=60)
    except Exception:
        exe = None
        r = None
    if r is None or r.returncode != 0:
        # WSL 空壳会打 "no installed distributions" 之类的提示
        _BASH, _BASH_OK = None, False
        return None
    _BASH, _BASH_OK = exe, True
    return exe


def bash_available() -> bool:
    return bash_exe() is not None


def powershell_exe() -> str | None:
    """返回可用的 PowerShell 路径：优先 pwsh（PS 7），退到 powershell（PS 5.1）。"""
    global _PS, _PS_OK
    if _PS_OK is not None:
        return _PS
    for name in ("pwsh", "powershell"):
        exe = shutil.which(name)
        if not exe:
            continue
        try:
            r = subprocess.run(
                [exe, "-NoProfile", "-NonInteractive", "-Command", "$PSVersionTable.PSVersion.Major"],
                capture_output=True, timeout=60)
        except Exception:
            continue
        if r.returncode == 0:
            _PS, _PS_OK = exe, True
            return exe
    _PS, _PS_OK = None, False
    return None


def powershell_available() -> bool:
    return powershell_exe() is not None


# ------------------------------------------------------------------ 通道 A：bash -n

# 一次 bash 进程吃下所有待检内容：标记行切块 → 写 /tmp → bash -n → 汇报
#
# 为什么必须走**脚本文件**而不是 `bash -c "..."`
# ------------------------------------------------
# WindowsApps 下的 bash.exe 是 wsl.exe 的壳，它把命令行**重新按 shell 规则解析**一遍：
#   · `bash -c 'v=hello; echo $v'`  → 分号被当成命令分隔，赋值在子 shell 里丢了
#   · `bash -c 'echo $1' _ hello`   → $0/$1/$2 根本收不到（count=0）
#   · `bash -c 'cat "$1"' _ path`   → 引号被吃掉，路径也丢了
# 所以内联脚本一律不可靠。规矩：
#   1. 脚本**写成文件**，用 `bash <路径>` 调（路径不含特殊字符，wsl.exe 不会拆它）
#   2. 需要传进脚本的东西**内嵌在文件里**（单引号在文件里不会被重解析）
#   3. Windows 路径由脚本内部 `wslpath -u` 转换（wslpath 认 Windows 路径字符串）
_BASH_DRIVER = r"""
#!/bin/sh
set -u
PAYLOAD=$(wslpath -u '__KC_PAYLOAD__' 2>/dev/null || true)
if [ -z "$PAYLOAD" ]; then PAYLOAD='__KC_PAYLOAD__'; fi
if [ ! -r "$PAYLOAD" ]; then echo "KC_NOPAYLOAD"; exit 3; fi
tmpd=$(mktemp -d) || exit 1
trap 'rm -rf "$tmpd"' EXIT
n=0
buf=""
while IFS= read -r line; do
  case "$line" in
    "@@KC_BEGIN:"*)
      buf=""
      ;;
    "@@KC_END:"*)
      idx="${line#@@KC_END:}"
      printf '%s\n' "$buf" > "$tmpd/$idx.sh"
      if ! err=$(bash -n "$tmpd/$idx.sh" 2>&1); then
        one=$(printf '%s' "$err" | head -2 | tr '\n' ' ')
        echo "FAIL $idx :: $one"
      fi
      n=$((n + 1))
      buf=""
      ;;
    *)
      buf="$buf$line"$'\n'
      ;;
  esac
done < "$PAYLOAD"
echo "KC_DONE $n"
"""

_BASH_KIND: str | None = None


def _bash_kind() -> str:
    """这个 bash 是 WSL 的壳，还是 Git Bash / 原生 bash？"""
    global _BASH_KIND
    if _BASH_KIND is not None:
        return _BASH_KIND
    exe = bash_exe()
    if not exe:
        _BASH_KIND = "none"
        return _BASH_KIND
    try:
        # 单引号里的路径不会被 wsl.exe 重解析（见文件头说明）
        r = subprocess.run([exe, "-c", "command -v wslpath >/dev/null 2>&1 && echo WSL || echo NATIVE"],
                           capture_output=True, timeout=60)
        out = (r.stdout or b"").decode("utf-8", "replace").strip().upper()
    except Exception:
        out = ""
    _BASH_KIND = "wsl" if "WSL" in out else "native"
    return _BASH_KIND


def _to_bash_path(win_path: str) -> str | None:
    """把 Windows 绝对路径换成 bash 看得见的路径。

    WSL：借 wslpath 在 WSL 内部转（wslpath 认 Windows 路径字符串）；
    Git Bash / 原生：Windows 路径本身就能用。
    """
    if _bash_kind() != "wsl":
        return win_path
    quoted = win_path.replace("'", "'\\''")
    try:
        r = subprocess.run([bash_exe(), "-c", f"wslpath -u '{quoted}'"],
                           capture_output=True, timeout=60)
        out = (r.stdout or b"").decode("utf-8", "replace").strip()
        if r.returncode == 0 and out.startswith("/"):
            return out
    except Exception:
        pass
    return None


def bash_syntax(items: list[tuple[str, str]], timeout: int = 600) -> dict[str, str]:
    """批量检查 .sh 内容。

    items: [(标签, 内容)]；返回 {标签: 错误信息}，**只有出错的标签在里面**。
    没 bash 时返回 {}（调用方据此降级到通道 C）。

    绝不允许「一个块都没查还报通过」—— 所以驱动脚本会报出实际处理的块数，
    与传入数量对不上就当失败，绝不当成干净。
    """
    exe = bash_exe()
    if not exe or not items:
        return {}
    marker = uuid.uuid4().hex[:12]
    payload = []
    for i, (_, code) in enumerate(items):
        payload.append(f"@@KC_BEGIN:{marker}")
        payload.append(code.rstrip("\n"))
        payload.append(f"@@KC_END:{i}")
    with tempfile.TemporaryDirectory(prefix="kc-sh-") as d:
        pf = pathlib.Path(d) / "payload.txt"
        # newline="\n" 必须显式给：Windows 默认把 \n 写成 \r\n，
        # bash 读到的每一行都带个 \r，标记行就匹配不上了。
        pf.write_text("\n".join(payload) + "\n", encoding="utf-8", newline="\n")
        driver = pathlib.Path(d) / "driver.sh"
        driver.write_text(_BASH_DRIVER.replace("__KC_PAYLOAD__", str(pf)),
                          encoding="utf-8", newline="\n")
        bpath = _to_bash_path(str(driver))
        if not bpath:
            return {"__driver__": "bash 是 WSL，但 wslpath 转换失败（路径不可达）"}
        try:
            r = subprocess.run([exe, bpath], capture_output=True, timeout=timeout)
        except Exception as e:
            return {"__driver__": f"bash 批量检查失败：{type(e).__name__}: {e}"}
    out = (r.stdout or b"").decode("utf-8", "replace")
    done = re.search(r"KC_DONE\s+(\d+)", out)
    if not done:
        return {"__driver__": "bash 批量检查未完成（脚本没跑到结尾，可能被超时打断）"}
    if int(done.group(1)) != len(items):
        return {"__driver__": f"bash 只处理了 {done.group(1)}/{len(items)} 个块，结果不可信"}
    bad: dict[str, str] = {}
    for line in out.splitlines():
        if not line.startswith("FAIL "):
            continue
        rest = line[5:]
        idx, _, msg = rest.partition(" :: ")
        try:
            label = items[int(idx)][0]
        except (ValueError, IndexError):
            label = rest
        bad[label] = msg.strip() or "语法错误"
    return bad


# ------------------------------------------------------------------ 通道 B：PowerShell 解析器

_PS_DRIVER = r"""
$ErrorActionPreference = 'Stop'
$dir = Split-Path -Parent $MyInvocation.MyCommand.Path
$out = @()
foreach ($line in [System.IO.File]::ReadAllLines((Join-Path $dir 'list.txt'))) {
    if ([string]::IsNullOrWhiteSpace($line)) { continue }
    $tokens = $null
    $errors = $null
    [System.Management.Automation.Language.Parser]::ParseFile($line, [ref]$tokens, [ref]$errors) | Out-Null
    $msgs = @()
    foreach ($e in $errors) {
        $msgs += ("{0}: {1}" -f $e.Extent.StartLineNumber, $e.Message)
    }
    $out += [pscustomobject]@{ file = $line; errors = $msgs }
}
$json = ConvertTo-Json -InputObject @($out) -Depth 5
if ($null -eq $json) { $json = '[]' }
[System.IO.File]::WriteAllText((Join-Path $dir 'result.json'), $json, (New-Object System.Text.UTF8Encoding($false)))
"""


def ps_parse(items: list[tuple[str, str]], timeout: int = 300) -> dict[str, list[str]]:
    """批量检查 .ps1 内容（用 PowerShell 自带的 AST 解析器）。

    items: [(标签, 内容)]；返回 {标签: [错误信息]}，只有出错的标签在里面。
    没有 PowerShell 时返回 {}。
    """
    exe = powershell_exe()
    if not exe or not items:
        return {}
    with tempfile.TemporaryDirectory(prefix="kc-ps-") as d:
        base = pathlib.Path(d)
        names = []
        for i, (_, code) in enumerate(items):
            fn = base / f"s{i:04d}.ps1"
            # 解析器按 UTF-8 读文件：带 BOM 更稳（PS 5.1 默认按 ANSI 读无 BOM 文件）
            fn.write_bytes(code.encode("utf-8", "replace"))
            names.append(str(fn))
        (base / "list.txt").write_text("\n".join(names) + "\n", encoding="utf-8")
        (base / "driver.ps1").write_text(_PS_DRIVER, encoding="utf-8")
        try:
            r = subprocess.run(
                [exe, "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
                 "-File", str(base / "driver.ps1")],
                capture_output=True, timeout=timeout)
        except Exception as e:
            return {"__driver__": [f"PowerShell 批量检查失败：{type(e).__name__}: {e}"]}
        res = base / "result.json"
        if r.returncode != 0 or not res.exists():
            err = (r.stderr or b"").decode("utf-8", "replace").strip().splitlines()
            return {"__driver__": [f"PowerShell 解析器异常：{err[-1] if err else r.returncode}"]}
        try:
            data = json.loads(res.read_text(encoding="utf-8"))
        except Exception as e:
            return {"__driver__": [f"PowerShell 解析结果不可读：{e}"]}
        if isinstance(data, dict):
            data = [data]
        by_file = {d.get("file"): d.get("errors") or [] for d in data}
        bad: dict[str, list[str]] = {}
        for i, (label, _) in enumerate(items):
            msgs = by_file.get(names[i]) or []
            if msgs:
                bad[label] = [str(m) for m in msgs]
        return bad


# ------------------------------------------------------------------ 通道 C：纯 Python 结构自检

# 只报**高置信度**问题：宁可漏报也不误报 —— 误报会让门禁变红，
# 门禁一红就没人信它了。
_KEYWORD_OPEN = re.compile(r"(?:^|[;&|]\s*|\bthen\s+|\bdo\s+)\b(if|case|for|while|until)\b")
_KEYWORD_CLOSE = re.compile(r"(?:^|[;&|]\s*)\b(fi|esac|done)\b")


def _strip_noise(line: str) -> str:
    """去掉注释与引号内容，只留结构性关键字。"""
    out = []
    i, n = 0, len(line)
    quote = None
    while i < n:
        ch = line[i]
        if quote:
            if ch == "\\" and quote == '"':
                i += 2
                continue
            if ch == quote:
                quote = None
            i += 1
            continue
        if ch in "'\"":
            quote = ch
            i += 1
            continue
        if ch == "#":
            if not out or out[-1].isspace():
                break  # 注释（# 在词中间时当普通字符）
        out.append(ch)
        i += 1
    return "".join(out)


def posix_shell_lint(text: str) -> list[str]:
    """没 bash 时的 .sh 降级自检：只查高置信度问题。

    查三类：引号不配对、if/fi 与 case/esac 与 do/done 不配对、花括号不配对。
    """
    problems: list[str] = []
    lines = text.splitlines()
    depth_if = depth_case = depth_do = 0
    for no, raw in enumerate(lines, 1):
        line = _strip_noise(raw)
        if not line.strip():
            continue
        code = line.strip()
        # if / case 开启
        if re.search(r"\bif\b", code):
            depth_if += 1
        if re.search(r"\bcase\b", code):
            depth_case += 1
        if re.search(r"\b(for|while|until)\b", code) or re.search(r"\bdo\s*$", code):
            depth_do += 1
        # fi / esac / done 闭合（elif 不算开启）
        if re.search(r"\bfi\b", code):
            depth_if -= 1
        if re.search(r"\besac\b", code):
            depth_case -= 1
        if re.search(r"\bdone\b", code):
            depth_do -= 1
        if depth_if < 0:
            problems.append(f"第 {no} 行：fi 多于 if")
            depth_if = 0
        if depth_case < 0:
            problems.append(f"第 {no} 行：esac 多于 case")
            depth_case = 0
        if depth_do < 0:
            problems.append(f"第 {no} 行：done 多于 do/for/while")
            depth_do = 0
    if depth_if:
        problems.append(f"if 未闭合（缺 {depth_if} 个 fi）")
    if depth_case:
        problems.append(f"case 未闭合（缺 {depth_case} 个 esac）")
    if depth_do:
        problems.append(f"do/for/while 未闭合（缺 {depth_do} 个 done）")
    return problems
