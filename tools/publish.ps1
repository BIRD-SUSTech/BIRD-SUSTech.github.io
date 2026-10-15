# BIRD Lab 网站一键发布（PowerShell 版）—— 转调 bash 版，行为与 Git Bash 完全一致
#
# 用法：
#   powershell -NoProfile -ExecutionPolicy Bypass -File tools/publish.ps1 -Message "日常推送"
#
# 若本机没有 Git Bash：请打开 Git Bash，进入仓库目录后运行 bash tools/publish.sh

param(
    [string]$Message = "",
    [switch]$SkipCheck,
    [switch]$NoPush,
    [switch]$Rebase
)

$ErrorActionPreference = "Continue"

$bash = @(
    "C:\Program Files\Git\bin\bash.exe",
    "C:\Program Files\Git\usr\bin\bash.exe",
    "C:\Program Files (x86)\Git\bin\bash.exe",
    "$env:LOCALAPPDATA\Programs\Git\bin\bash.exe"
) | Where-Object { Test-Path $_ } | Select-Object -First 1

if (-not $bash) {
    Write-Host "X 没找到 Git Bash（bash.exe）" -ForegroundColor Red
    Write-Host "  请打开 Git Bash，进入仓库目录后运行：bash tools/publish.sh"
    Read-Host "按回车关闭"
    exit 1
}

$root = Split-Path $PSScriptRoot -Parent
$unix = "/" + $root.Substring(0, 1).ToLower() + ($root.Substring(2) -replace '\\', '/')

$extra = ""
if ($Message)   { $extra = $extra + " '" + $Message + "'" }
if ($SkipCheck) { $extra = $extra + " --skip-check" }
if ($NoPush)    { $extra = $extra + " --no-push" }
if ($Rebase)    { $extra = $extra + " --rebase" }

$cmd = "cd '$unix' && bash tools/publish.sh" + $extra
Write-Host ("调用: " + $cmd) -ForegroundColor DarkGray
& $bash -lc $cmd
Read-Host "按回车关闭"
