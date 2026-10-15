#!/usr/bin/env bash
# BIRD Lab 网站：开工前同步（把本地工作分支对齐到最新的 main）
#
# 用法（Git Bash 中）：
#   cd "/d/BIRD Lab - Tianqi Yue/working path/DeepSeek Harness/BIRD Lab Web"
#   bash tools/sync.sh
#
# 依次：拉取远程 -> 检查工作区是否干净 -> 显示领先/落后 -> rebase 到 origin/main
# 遇到冲突会停下提示，不会自动处理。

set -u
cd "$(dirname "$0")/.." || exit 1
pause() { read -r -p "按回车关闭" _ ; }

echo "=== 开工前同步 ==="
echo "目录: $(pwd)"
git rev-parse --git-dir >/dev/null 2>&1 || { echo "X 不是 Git 仓库"; pause; exit 1; }

branch=$(git rev-parse --abbrev-ref HEAD)
echo "当前分支: $branch"
if [ "$branch" != "update-tianqi" ]; then
  read -r -p "! 建议在 update-tianqi 上操作（当前 $branch），继续？(y/N) " a
  case "$a" in y|Y) ;; *) echo "已取消"; exit 0 ;; esac
fi

echo ""
echo "[1/4] 拉取远程最新 ..."
git fetch origin --prune || { echo "X fetch 失败（网络或权限），未做任何改动。"; pause; exit 1; }

echo ""
echo "[2/4] 检查工作区 ..."
if [ -n "$(git status --porcelain)" ]; then
  echo "! 有未提交的改动，无法安全变基。"
  echo "  请先提交它们（bash tools/publish.sh \"日常推送\"），再回来同步："
  git status --short | head -15
  pause; exit 1
fi
echo "    工作区干净 ok"

echo ""
echo "[3/4] 与 origin/main 的差距 ..."
counts=$(git rev-list --left-right --count origin/main...HEAD 2>/dev/null || printf '0\t0')
behind=$(printf '%s' "$counts" | cut -f1)
ahead=$(printf '%s' "$counts" | cut -f2)
echo "    落后 main: ${behind} 个提交 ｜ 本地领先: ${ahead} 个提交"
echo "    main 最新: $(git log --oneline origin/main -1)"
echo "    本地最近: $(git log --oneline -1)"

if [ "${behind:-0}" = "0" ]; then
  echo ""
  echo "OK 本地已包含 main 全部提交，无需变基。"
  pause; exit 0
fi

echo ""
echo "[4/4] 变基到 origin/main ..."
if ! git rebase origin/main; then
  echo ""
  echo "! rebase 遇到冲突，已暂停。处理办法："
  echo "   1) 改好冲突文件 -> git add <文件> -> git rebase --continue"
  echo "   2) 放弃本次变基：git rebase --abort"
  echo "   拿不准就找助手，不要硬来。"
  pause; exit 1
fi
echo ""
echo "OK 已与 origin/main 对齐，可以开始工作了。"
echo "（推送时用 bash tools/publish.sh，它内部还会再同步一次）"
pause
