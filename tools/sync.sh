#!/usr/bin/env bash
# BIRD Lab 网站：开工前同步（把本地工作分支对齐到最新 main）
#
# 用法：bash tools/sync.sh
#
# 要求：工作区必须干净（有未提交改动会提示你先发布）
# 逻辑：本地提交都已被 main 吸收 -> 本地直接对齐 main
#       仍有未合并提交        -> 用 merge 同步（不改写历史）

set -u
cd "$(dirname "$0")/.." || exit 1
pause() { read -r -p "按回车关闭" _ ; }
fail() { echo ""; echo "X $1"; pause; exit 1; }

echo "=== 开工前同步 ==="
echo "目录: $(pwd)"
git rev-parse --git-dir >/dev/null 2>&1 || fail "不是 Git 仓库"
branch=$(git rev-parse --abbrev-ref HEAD)
echo "分支: $branch"
if [ "$branch" != "update-tianqi" ]; then
  read -r -p "! 建议在 update-tianqi 上操作（当前 $branch），继续？(y/N) " a
  case "$a" in y|Y) ;; *) echo "已取消"; exit 0 ;; esac
fi

echo ""
echo "[1/4] 检查工作区 ..."
if [ -n "$(git status --porcelain)" ]; then
  echo "! 工作区有未提交改动，无法安全同步。请先发布它们："
  git status --short | head -15
  echo ""
  echo "    bash tools/publish.sh \"日常推送\""
  pause; exit 1
fi
echo "  干净 ok"

echo ""
echo "[2/4] 拉取远程最新 ..."
git fetch origin --prune || fail "fetch 失败（网络或权限），未做任何改动"

echo ""
echo "[3/4] 与 main 的差距 ..."
counts=$(git rev-list --left-right --count origin/main...HEAD 2>/dev/null || printf '0\t0')
behind=$(printf '%s' "$counts" | cut -f1)
ahead=$(printf '%s' "$counts" | cut -f2)
echo "  落后 main: ${behind} ｜ 本地领先: ${ahead}"
echo "  main 最新: $(git log --oneline origin/main -1)"
echo "  本地最近: $(git log --oneline -1)"

if [ "${behind:-0}" = "0" ]; then
  echo ""
  echo "OK 已包含 main 全部提交，无需同步。"
  pause; exit 0
fi

unmerged=$(git cherry origin/main HEAD 2>/dev/null | grep -c '^+')
echo ""
echo "[4/4] 同步 main（本地未合并提交数: ${unmerged:-0}）..."
if [ "${unmerged:-0}" = "0" ]; then
  echo "  本地提交都已被 main 吸收 -> 直接对齐 main"
  git reset --hard origin/main || fail "reset 失败"
  echo "  已对齐到 main 最新（本地已合并的旧提交被清理）"
else
  echo "  本地有未合并提交 -> merge 同步（不改写历史）"
  if ! git merge --no-edit origin/main; then
    echo ""
    echo "! merge 冲突，处理办法："
    echo "    1) 改好冲突文件（搜索 <<<<<<<）-> git add <文件> -> git commit --no-edit"
    echo "    2) 再跑 bash tools/sync.sh"
    pause; exit 1
  fi
  echo "  已同步"
fi
echo ""
echo "OK 可以开始工作了（收工时用 bash tools/publish.sh）。"
pause
