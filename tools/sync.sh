#!/usr/bin/env bash
# BIRD Lab 网站：同步 main
#
# 两种模式：
#   bash tools/sync.sh          手动模式：工作区必须干净；智能选择 merge（还有未合并提交）或 reset（旧提交已被合并）
#   bash tools/sync.sh --auto   安全自动模式：只 fetch + merge，绝不 reset；工作区不干净就跳过；供助手在任务开始时调用

set -u
cd "$(dirname "$0")/.." || exit 1

AUTO=0
for a in "$@"; do
  case "$a" in
    --auto) AUTO=1 ;;
  esac
done
pause() { read -r -p "按回车关闭" _ ; }
fail() { echo ""; echo "X $1"; pause; exit 1; }

echo "=== 同步 main（$([ "$AUTO" = "1" ] && echo 自动模式 || echo 手动模式)）==="
echo "目录: $(pwd)"
git rev-parse --git-dir >/dev/null 2>&1 || { echo "X 不是 Git 仓库"; [ "$AUTO" = "1" ] && exit 1; pause; exit 1; }

branch=$(git rev-parse --abbrev-ref HEAD)
echo "分支: $branch"
if [ "$branch" != "update-tianqi" ]; then
  if [ "$AUTO" = "1" ]; then
    echo "! 当前不在 update-tianqi，跳过自动同步"
    exit 0
  fi
  read -r -p "! 建议在 update-tianqi 上操作（当前 $branch），继续？(y/N) " a
  case "$a" in y|Y) ;; *) echo "已取消"; exit 0 ;; esac
fi

echo ""
echo "[1/4] 检查工作区 ..."
if [ -n "$(git status --porcelain)" ]; then
  if [ "$AUTO" = "1" ]; then
    echo "! 工作区有未提交改动，跳过自动同步（不影响你的任务，收工时 publish.sh 还会再同步一次）"
    exit 0
  fi
  echo "! 工作区有未提交改动，无法安全同步。请先发布它们："
  git status --short | head -15
  echo ""
  echo "    bash tools/publish.sh \"日常推送\""
  pause; exit 1
fi
echo "  干净 ok"

echo ""
echo "[2/4] 拉取远程最新 ..."
if ! git fetch origin --prune; then
  if [ "$AUTO" = "1" ]; then
    echo "! fetch 失败（网络？），跳过自动同步"
    exit 0
  fi
  fail "fetch 失败（网络或权限），未做任何改动"
fi

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
  [ "$AUTO" = "1" ] && exit 0
  pause; exit 0
fi

if [ "$AUTO" = "1" ]; then
  echo ""
  echo "[4/4] 自动同步：merge main（不改写历史，不 reset）..."
  if ! git merge --no-edit origin/main; then
    echo ""
    echo "! merge 冲突：请把上面的输出发给助手，由助手判断；不要自己乱改。"
    exit 1
  fi
  echo "  已与 main 同步 ok"
  exit 0
fi

unmerged=$(git cherry origin/main HEAD 2>/dev/null | grep -c '^+')
echo ""
echo "[4/4] 同步 main（本地未合并提交数: ${unmerged:-0}）..."
if [ "${unmerged:-0}" = "0" ]; then
  echo "  本地提交都已被 main 吸收 -> 直接对齐 main（会清理掉这些已合并的旧提交）"
  git reset --hard origin/main || fail "reset 失败"
  echo "  已对齐到 main 最新"
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
