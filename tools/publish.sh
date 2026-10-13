#!/usr/bin/env bash
# BIRD Lab 网站一键发布（Git Bash 版；和你平时手动提交一样，只是自动化）
#
# 用法（Git Bash 里）：
#   cd "/d/BIRD Lab - Tianqi Yue/working path/DeepSeek Harness/BIRD Lab Web"
#   bash tools/publish.sh "增加了成员"
#
# 不传说明则用默认「更新了网页」

set -u
cd "$(dirname "$0")/.." || exit 1

echo "=== 发布前检查 ==="
echo "目录: $(pwd)"
git rev-parse --git-dir >/dev/null 2>&1 || { echo "X 不是 Git 仓库"; read -r -p "按回车关闭" _; exit 1; }

branch=$(git rev-parse --abbrev-ref HEAD)
echo "当前分支: $branch"
if [ "$branch" != "update-tianqi" ]; then
  read -r -p "! 建议在 update-tianqi 上发布（当前 $branch），继续？(y/N) " a
  case "$a" in y|Y) ;; *) echo "已取消"; exit 0 ;; esac
fi

echo ""
echo "[1/4] 拉取远程最新 + 规范化换行 ..."
git fetch origin --prune || echo "! fetch 失败（网络？）继续尝试"
git add --renormalize .
git add .
git status --short

if git diff --cached --quiet; then
  echo "没有可提交的改动（工作区干净）。"
  read -r -p "按回车关闭" _
  exit 0
fi

msg="${1:-}"
if [ -z "$msg" ]; then
  echo "常用写法（简短，仓库公开可见）：增加了成员 / 增加了新闻 / 修改了信息 / 更新了论文"
  read -r -p "提交说明（回车使用「更新了网页」）: " msg
  [ -z "$msg" ] && msg="更新了网页"
fi

echo ""
echo "[2/4] 提交 ..."
if ! git commit -m "$msg"; then
  echo "X 提交失败"; read -r -p "按回车关闭" _; exit 1
fi

echo ""
echo "[3/4] 推送 ..."
if ! git push; then
  echo "! 普通推送失败，尝试 --force-with-lease ..."
  if ! git push --force-with-lease; then
    echo "X 推送失败（网络或权限）"; read -r -p "按回车关闭" _; exit 1
  fi
fi

hash=$(git rev-parse --short HEAD)
echo ""
echo "[4/4] 完成：已推送 $branch（commit $hash）"
echo ""
echo "请把下面这段话发给仓库管理员（复制即可）："
echo "------------------------------------------------------------"
echo "Hi，我把最新更新推到了 update-tianqi 分支（commit $hash），麻烦合并到 main 并发布，谢谢！"
echo "------------------------------------------------------------"
read -r -p "按回车关闭" _
