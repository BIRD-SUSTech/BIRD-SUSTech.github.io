# BIRD Lab 网站一键发布（PowerShell 版）
# 一行命令搞定：自动生成页面 → 全站自检 → 提交 → 推送 → 打印给管理员的话术
#
# 推荐运行方式（能看到输出，出错会停下）：
#   powershell -NoProfile -ExecutionPolicy Bypass -File tools/publish.ps1 -Message "日常推送"
# 不要用「右键 → 使用 PowerShell 运行」（窗口可能一闪而过）。
#
# 可选：-SkipCheck 跳过生成与自检；-NoPush 只提交不推送

param(
    [string]$Message = "",
    [switch]$SkipCheck,
    [switch]$NoPush
)

$ErrorActionPreference = "Continue"
Set-Location -Path (Join-Path $PSScriptRoot "..")

function Fail($msg) {
    Write-Host ""
    Write-Host "X $msg" -ForegroundColor Red
    Write-Host "（已停止，未提交。请把上面完整信息发给助手）" -ForegroundColor Yellow
    Read-Host "按回车关闭"
    exit 1
}
function Pause-End { Read-Host "按回车关闭" | Out-Null }

Write-Host "=== 发布前检查 ===" -ForegroundColor Cyan
Write-Host "PowerShell: $($PSVersionTable.PSVersion)  目录: $((Get-Location).Path)"
if (-not (Test-Path ".git")) { Fail "当前目录不是 Git 仓库" }
$branch = (git rev-parse --abbrev-ref HEAD).Trim()
if (-not $branch) { Fail "读不到当前分支（git 可用吗？）" }
Write-Host "当前分支: $branch"
if ($branch -ne "update-tianqi") {
    Write-Host "! 建议在 update-tianqi 分支上发布（当前 $branch）" -ForegroundColor Yellow
    $a = Read-Host "仍要继续？(y/N)"
    if ($a -ne "y" -and $a -ne "Y") { Write-Host "已取消"; exit 0 }
}

Write-Host "`n[1/6] 检查是否有改动 ..." -ForegroundColor Cyan
if (-not (git status --porcelain)) { Write-Host "没有可提交的改动。"; Pause-End; exit 0 }
git status --short | Select-Object -First 20

Write-Host "`n[2/6] 拉取远程最新 ..." -ForegroundColor Cyan
git fetch origin --prune
if ($LASTEXITCODE -ne 0) { Write-Host "! fetch 失败（网络？）继续尝试" -ForegroundColor Yellow }
Write-Host "`n[2.5/6] 同步 main（落后则变基）..." -ForegroundColor Cyan
$revCounts = (git rev-list --left-right --count "origin/main...HEAD" 2>$null) -split "\s+"
$behind = 0
if ($revCounts.Count -gt 0) { [void][int]::TryParse($revCounts[0], [ref]$behind) }
if ($behind -gt 0) {
    Write-Host "  落后 main $behind 个提交，执行 rebase ..."
    git rebase origin/main
    if ($LASTEXITCODE -ne 0) {
        Write-Host "X rebase 遇到冲突，已停止（未提交）。处理办法：" -ForegroundColor Red
        Write-Host "   1) 改好冲突文件 -> git add <文件> -> git rebase --continue"
        Write-Host "   2) 放弃本次变基：git rebase --abort"
        Fail "rebase 冲突未解决"
    }
    Write-Host "  已变基到 main 最新" -ForegroundColor Green
} else {
    Write-Host "  已包含 main 全部提交，无需变基" -ForegroundColor Green
}

$py = $null
if (Get-Command python -ErrorAction SilentlyContinue) { $py = "python" }
elseif (Test-Path "C:\Users\Administrator\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe") {
    $py = "C:\Users\Administrator\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe"
}
if (-not $py -and -not $SkipCheck) {
    Write-Host "! 没找到 python，无法自动生成与自检。" -ForegroundColor Yellow
    $a = Read-Host "跳过生成与自检、直接提交？(y/N)"
    if ($a -eq "y" -or $a -eq "Y") { $SkipCheck = $true } else { Write-Host "已取消"; Pause-End; exit 0 }
}

if ($py -and -not $SkipCheck) {
    Write-Host "`n[3/6] 由数据源重新生成页面 ..." -ForegroundColor Cyan
    foreach ($s in @("build_members.py", "build_news.py", "build_publications.py", "build_chrome.py")) {
        $out = & $py "tools/$s" 2>&1
        Write-Host ("  {0} -> {1}" -f $s, ($out | Select-Object -Last 1))
        if ($LASTEXITCODE -ne 0) {
            Write-Host ($out | Select-Object -Last 20 | Out-String)
            Fail "$s 运行出错"
        }
    }
    Write-Host "`n[4/6] 全站自检 ..." -ForegroundColor Cyan
    $out = & $py "tools/check_site.py" 2>&1
    Write-Host ($out | Select-Object -Last 8 | Out-String)
    if ($LASTEXITCODE -ne 0) { Fail "自检未通过" }
    Write-Host "自检通过" -ForegroundColor Green
} else {
    Write-Host "`n[3-4/6] 已跳过生成与自检" -ForegroundColor Yellow
}

Write-Host "`n[5/6] 暂存并提交 ..." -ForegroundColor Cyan
git add --renormalize .
git add .
git diff --cached --quiet
if ($LASTEXITCODE -eq 0) { Write-Host "暂存区没有改动，结束。"; Pause-End; exit 0 }

if ([string]::IsNullOrWhiteSpace($Message)) {
    $default = "更新了网页"
    Write-Host "常用写法（简短，仓库公开可见）：增加了成员 / 增加了新闻 / 修改了信息 / 更新了论文" -ForegroundColor DarkGray
    try { $Message = Read-Host "提交说明（直接回车使用：$default）" } catch { $Message = "" }
    if ([string]::IsNullOrWhiteSpace($Message)) { $Message = $default }
}
git commit -m "$Message"
if ($LASTEXITCODE -ne 0) { Fail "提交失败" }

if ($NoPush) { Write-Host "`n已提交但未推送（-NoPush）。" -ForegroundColor Yellow; Pause-End; exit 0 }

Write-Host "`n[6/6] 推送到远程 ..." -ForegroundColor Cyan
git push
if ($LASTEXITCODE -ne 0) {
    Write-Host "! 普通推送失败，尝试 --force-with-lease ..." -ForegroundColor Yellow
    git push --force-with-lease
    if ($LASTEXITCODE -ne 0) { Fail "推送失败（网络或权限）" }
}

$hash = (git rev-parse --short HEAD).Trim()
Write-Host "`n完成：已推送 $branch（commit $hash）" -ForegroundColor Green
Write-Host "`n请把下面这段话发给仓库管理员（复制即可）：" -ForegroundColor Cyan
Write-Host "------------------------------------------------------------"
Write-Host "Hi，我把最新更新推到了 update-tianqi 分支（commit $hash），麻烦合并到 main 并发布，谢谢！"
Write-Host "------------------------------------------------------------"
Pause-End
