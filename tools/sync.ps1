# BIRD Lab 网站：开工前同步（PowerShell 版）—— 转调 bash 版
#
# 用法：powershell -NoProfile -ExecutionPolicy Bypass -File tools/sync.ps1

$ErrorActionPreference = "Continue"

$bash = @(
    "C:\Program Files\Git\bin\bash.exe",
    "C:\Program Files\Git\usr\bin\bash.exe",
    "C:\Program Files (x86)\Git\bin\bash.exe",
    "$env:LOCALAPPDATA\Programs\Git\bin\bash.exe"
) | Where-Object { Test-Path $_ } | Select-Object -First 1

if (-not $bash) {
    Write-Host "X 没找到 Git Bash（bash.exe）" -ForegroundColor Red
    Write-Host "  请打开 Git Bash，进入仓库目录后运行：bash tools/sync.sh"
    Read-Host "按回车关闭"
    exit 1
}

$root = Split-Path $PSScriptRoot -Parent
$unix = "/" + $root.Substring(0, 1).ToLower() + ($root.Substring(2) -replace '\\', '/')

$cmd = "cd '$unix' && bash tools/sync.sh"
Write-Host ("调用: " + $cmd) -ForegroundColor DarkGray
& $bash -lc $cmd
Read-Host "按回车关闭"
