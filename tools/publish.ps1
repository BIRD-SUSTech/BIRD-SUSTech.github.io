# BIRD Lab 网站一键发布（由你本人运行）
#
# 推荐运行方式（能看到输出，出错会停下来等你看）：
#   Git Bash 里：  powershell -NoProfile -ExecutionPolicy Bypass -File tools/publish.ps1 -Message "增加了成员"
#   PowerShell 里： cd 到仓库根后   .\tools\publish.ps1 -Message "增加了成员"
#
# 不要用「右键 → 使用 PowerShell 运行」：窗口可能一闪而过，看不到报错。
#
# 它会：拉取远程 → 规范化换行 → 暂存 → 提交 → 推送 → 打印给管理员的话术

param([string]$Message = "")

$ErrorActionPreference = "Continue"
Set-Location -Path (Join-Path $PSScriptRoot "..")

function Fail($msg) {
    Write-Host ""
    Write-Host "X $msg" -ForegroundColor Red
    Write-Host "（本次未完成。请把上面的完整信息发给助手）" -ForegroundColor Yellow
    Read-Host "按回车关闭"
    exit 1
}

Write-Host "=== 发布前检查 ===" -ForegroundColor Cyan
Write-Host "PowerShell 版本: $($PSVersionTable.PSVersion)"
Write-Host "工作目录: $((Get-Location).Path)"
if (-not (Test-Path ".git")) { Fail "当前目录不是 Git 仓库" }

$branch = (git rev-parse --abbrev-ref HEAD).Trim()
if (-not $branch) { Fail "读不到当前分支（git 命令可用吗？）" }
Write-Host "当前分支: $branch"

if ($branch -ne "update-tianqi") {
    Write-Host "! 建议在 update-tianqi 分支上发布（当前是 $branch）" -ForegroundColor Yellow
    $a = Read-Host "仍要继续？(y/N)"
    if ($a -ne "y" -and $a -ne "Y") { Write-Host "已取消"; exit 0 }
}

Write-Host "`n[1/4] 拉取远程最新并规范化换行 ..." -ForegroundColor Cyan
git fetch origin --prune
if ($LASTEXITCODE -ne 0) { Write-Host "! fetch 失败（网络？），继续尝试" -ForegroundColor Yellow }
git add --renormalize .
git add .
git status --short

git diff --cached --quiet
if ($LASTEXITCODE -eq 0) {
    Write-Host "`n没有可提交的改动（工作区是干净的）。" -ForegroundColor Yellow
    Read-Host "按回车关闭"
    exit 0
}

Write-Host "`n[2/4] 提交 ..." -ForegroundColor Cyan
if ([string]::IsNullOrWhiteSpace($Message)) {
    $default = "更新了网页"
    Write-Host "常用写法（简短，仓库公开可见）：增加了成员 / 增加了新闻 / 修改了信息 / 更新了论文" -ForegroundColor DarkGray
    try { $Message = Read-Host "提交说明（直接回车使用：$default）" } catch { $Message = "" }
    if ([string]::IsNullOrWhiteSpace($Message)) { $Message = $default }
}
git commit -m "$Message"
if ($LASTEXITCODE -ne 0) { Fail "提交失败" }

Write-Host "`n[3/4] 推送到远程 ..." -ForegroundColor Cyan
git push
if ($LASTEXITCODE -ne 0) {
    Write-Host "! 普通推送失败，尝试 --force-with-lease（刚 rebase 过时属正常）" -ForegroundColor Yellow
    git push --force-with-lease
    if ($LASTEXITCODE -ne 0) { Fail "推送失败（网络或权限问题）" }
}

$hash = (git rev-parse --short HEAD).Trim()
Write-Host "`n[4/4] 完成：已推送 $branch（commit $hash）" -ForegroundColor Green
Write-Host "`n请把下面这段话发给仓库管理员（复制即可）：" -ForegroundColor Cyan
Write-Host "------------------------------------------------------------"
Write-Host "Hi，我把最新更新推到了 update-tianqi 分支（commit $hash），麻烦合并到 main 并发布，谢谢！"
Write-Host "------------------------------------------------------------"
Read-Host "`n按回车关闭"
