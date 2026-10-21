<#
.SYNOPSIS
    知识公社全仓库质量门禁 —— PowerShell 入口。

.DESCRIPTION
    直接 `python tools/verify_all.py` 在 Windows PowerShell 5.1 上有两个坑：
      1. 控制台默认 GBK（代码页 936），Python 吐出来的 UTF-8 中文全是乱码；
      2. 路径与换行习惯不同，脚本里凡是写死 bash 的地方都跑不通。
    这个入口先把控制台切到 UTF-8，再调**同一个**门禁入口 ——
    检查逻辑只有一份，Windows / Linux / CI 跑的是同一套，
    不会出现「本地过、CI 挂」。

    门禁本身也不依赖 bash：.sh 走 bash -n（没有就降级成纯 Python 结构自检），
    .ps1 走 PowerShell 自带的 AST 解析器，md 代码块按语言分派。
    详见 tools/shell_compat.py。

.EXAMPLE
    .\tools\verify_all.ps1
    .\tools\verify_all.ps1 --fast
    .\tools\verify_all.ps1 --only mdpy,manifest
#>
[CmdletBinding()]
param(
    # 直接透传给 verify_all.py 的参数（--fast / --only / --list）
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$GateArgs
)

$ErrorActionPreference = 'Stop'

# 1) 控制台切 UTF-8 —— 否则中文全是「����」
try {
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
    $OutputEncoding = [System.Text.Encoding]::UTF8
} catch {
    Write-Warning "控制台编码切换失败（中文可能显示为乱码）：$($_.Exception.Message)"
}
$env:PYTHONIOENCODING = 'utf-8'
$env:PYTHONUTF8 = '1'

# 2) 找 python（py -3 也能用）
$pyExe = $null
$pyArgs = @()
foreach ($cmd in @('python', 'python3', 'py')) {
    $c = Get-Command $cmd -ErrorAction SilentlyContinue
    if (-not $c) { continue }
    if ($cmd -eq 'py') {
        $pyExe = $c.Source
        $pyArgs = @('-3')
    } else {
        $pyExe = $c.Source
    }
    break
}
if (-not $pyExe) {
    Write-Error '找不到 python —— 装一个（winget install Python.Python.3.12）或把 python 加进 PATH'
    exit 2
}

# 3) 跑门禁（仓库根由 verify_all.py 自己按 __file__ 推，cwd 只影响日志可读性）
$repoRoot = Split-Path -Parent $PSScriptRoot
$gate = Join-Path $repoRoot 'tools\verify_all.py'
if (-not (Test-Path $gate)) {
    Write-Error "找不到门禁脚本：$gate"
    exit 2
}

Push-Location $repoRoot
try {
    & $pyExe @pyArgs $gate @GateArgs
    $code = $LASTEXITCODE
} finally {
    Pop-Location
}
exit $code
