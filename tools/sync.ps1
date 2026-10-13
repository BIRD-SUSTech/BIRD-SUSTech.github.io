# BIRD Lab 网站：开工前同步（把本地工作分支对齐到最新的 main）
#
# 用法：  .\tools\sync.ps1
#
# 它按顺序做：拉取远程最新 → 检查工作区是否干净 → 显示领先/落后情况 → rebase 到 origin/main
# 遇到冲突会停下来给出提示，不会自动处理冲突。

$ErrorActionPreference = "Continue"
Set-Location -Path (Join-Path $PSScriptRoot "..")

if (-not (Test-Path ".git")) {
    Write-Host "X 当前目录不是 Git 仓库：$((Get-Location).Path)" -ForegroundColor Red
    exit 1
}

$branch = (git rev-parse --abbrev-ref HEAD).Trim()
Write-Host "当前分支：$branch" -ForegroundColor Cyan
if ($branch -ne "update-tianqi") {
    Write-Host "! 建议在 update-tianqi 分支上操作（当前是 $branch）" -ForegroundColor Yellow
    $a = Read-Host "仍要继续？(y/N)"
    if ($a -ne "y" -and $a -ne "Y") { exit 0 }
}

Write-Host "`n[1/4] 拉取远程最新 ..." -ForegroundColor Cyan
git fetch origin --prune
if ($LASTEXITCODE -ne 0) {
    Write-Host "X fetch 失败（网络或权限问题），未做任何改动。" -ForegroundColor Red
    exit 1
}

Write-Host "`n[2/4] 检查工作区 ..." -ForegroundColor Cyan
$dirty = git status --porcelain
if ($dirty) {
    Write-Host "! 有未提交的改动，无法安全变基。请先提交它们（跑 publish.ps1）后再同步：" -ForegroundColor Yellow
    git status --short | Select-Object -First 15
    exit 1
}
Write-Host "    工作区干净 ✓"

Write-Host "`n[3/4] 与 origin/main 的差距 ..." -ForegroundColor Cyan
$counts = (git rev-list --left-right --count "origin/main...HEAD") -split "\s+"
Write-Host ("    落后 main：{0} 个提交 ｜ 本地领先：{1} 个提交" -f $counts[0], $counts[1])
git log --oneline origin/main -1 | ForEach-Object { Write-Host "    main 最新：$_" }
git log --oneline -3 | ForEach-Object { Write-Host "    本地最近：$_" }

if ($counts[0] -eq "0") {
    Write-Host "`nOK 本地已经包含 main 的全部提交，无需变基。" -ForegroundColor Green
    exit 0
}

Write-Host "`n[4/4] 变基到 origin/main ..." -ForegroundColor Cyan
git rebase origin/main
if ($LASTEXITCODE -ne 0) {
    Write-Host "`n! rebase 遇到冲突，已暂停。处理办法：" -ForegroundColor Yellow
    Write-Host "   1) 按提示改好冲突文件 → git add <文件> → git rebase --continue"
    Write-Host "   2) 放弃这次变基：git rebase --abort"
    Write-Host "   拿不准就找管理员或助手，不要硬来。"
    exit 1
}
Write-Host "`nOK 已与 origin/main 对齐，可以开始工作了。" -ForegroundColor Green
Write-Host "提示：如果本地提交曾推送过，下次推送请用  git push --force-with-lease" -ForegroundColor DarkGray
