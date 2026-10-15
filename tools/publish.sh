#!/usr/bin/env bash
# BIRD Lab 网站一键发布（Git Bash 版）——一行命令完成：
#   检查改动 -> 拉取远程 -> 重新生成页面 -> 全站自检 -> 提交 -> 同步 main -> 推送 -> 打印话术
#
# 用法：
#   cd "/d/BIRD Lab - Tianqi Yue/working path/DeepSeek Harness/BIRD Lab Web"
#   bash tools/publish.sh "日常推送"
#
# 可选：--no-push（只提交）｜--skip-check（跳过生成与自检）｜--rebase（用 rebase 同步）

set -u
export PYTHONIOENCODING=utf-8
export PYTHONUTF8=1
cd "$(dirname "$0")/.." || exit 1

SKIP_CHECK=0; NO_PUSH=0; USE_REBASE=0; msg=""
for a in "$@"; do
  case "$a" in
    --skip-check) SKIP_CHECK=1 ;;
    --no-push)    NO_PUSH=1 ;;
    --rebase)     USE_REBASE=1 ;;
    *) [ -z "$msg" ] && msg="$a" ;;
  esac
done
pause() { read -r -p "按回车关闭" _ ; }
fail() {
  echo ""
  echo "X $1"
  echo "（已停止，未提交。请把上面的完整信息发给助手）"
  pause; exit 1
}

echo "=== 发布流程 ==="
echo "目录: $(pwd)"
git rev-parse --git-dir >/dev/null 2>&1 || fail "不是 Git 仓库"
branch=$(git rev-parse --abbrev-ref HEAD)
echo "分支: $branch"
if [ "$branch" != "update-tianqi" ]; then
  read -r -p "! 建议在 update-tianqi 上发布（当前 $branch），继续？(y/N) " a
  case "$a" in y|Y) ;; *) echo "已取消"; exit 0 ;; esac
fi

echo ""
echo "[1/7] 检查改动 ..."
if [ -z "$(git status --porcelain)" ]; then
  echo "没有可提交的改动（工作区干净）。"
  pause; exit 0
fi
git status --short | head -20

echo ""
echo "[2/7] 拉取远程最新 ..."
git fetch origin --prune || echo "! fetch 失败（网络？）继续尝试"

PY=""
if command -v python >/dev/null 2>&1; then
  PY="python"
elif [ -x "/c/Users/Administrator/.dsh/dsh-runtimes/dsh-primary-runtime/dependencies/python/python.exe" ]; then
  PY="/c/Users/Administrator/.dsh/dsh-runtimes/dsh-primary-runtime/dependencies/python/python.exe"
fi

if [ -n "$PY" ] && [ "$SKIP_CHECK" = "0" ]; then
  echo ""
  echo "[3/7] 由数据源重新生成页面 ..."
  for s in build_members.py build_news.py build_publications.py build_chrome.py; do
    out=$("$PY" "tools/$s" 2>&1); rc=$?
    echo "  $s -> $(printf '%s' "$out" | tail -1)"
    if [ $rc -ne 0 ]; then
      printf '%s\n' "$out" | tail -20
      fail "$s 运行出错"
    fi
  done
  echo ""
  echo "[4/7] 全站自检 ..."
  out=$("$PY" tools/check_site.py 2>&1); rc=$?
  printf '%s\n' "$out" | tail -20
  if [ $rc -ne 0 ]; then
    echo ""
    echo "--- 自检完整输出（请把这部分发给助手）---"
    printf '%s\n' "$out"
    fail "自检未通过"
  fi
else
  echo ""
  echo "[3-4/7] 已跳过生成与自检（--skip-check 或没有 python）"
fi

echo ""
echo "[5/7] 暂存并提交 ..."
git add -A
if git diff --cached --quiet; then
  echo "暂存区没有改动，结束。"
  pause; exit 0
fi
if [ -z "$msg" ]; then
  echo "常用写法（简短，仓库公开可见）：增加了成员 / 增加了新闻 / 修改了信息 / 更新了论文"
  read -r -p "提交说明（回车使用「更新了网页」）: " msg
  [ -z "$msg" ] && msg="更新了网页"
fi
git commit -m "$msg" || fail "提交失败"

echo ""
echo "[6/7] 同步 main ..."
behind=$(git rev-list --left-right --count origin/main...HEAD 2>/dev/null | cut -f1)
if [ "${behind:-0}" = "0" ]; then
  echo "  已包含 main 全部提交，无需同步"
elif [ "$USE_REBASE" = "1" ]; then
  echo "  落后 main ${behind} 个提交 -> rebase（--rebase）..."
  if ! git rebase origin/main; then
    echo ""
    echo "! rebase 冲突。若该分支刚被管理员合并过，rebase 必然冲突，请改用 merge："
    echo "    git rebase --abort"
    echo "    bash tools/publish.sh \"$msg\""
    pause; exit 1
  fi
  echo "  已 rebase 到 main 最新"
else
  echo "  落后 main ${behind} 个提交 -> merge（不改写已推送历史，最安全）..."
  if ! git merge --no-edit origin/main; then
    echo ""
    echo "! merge 冲突，需要手工解决："
    echo "    1) 打开冲突文件，搜索 <<<<<<< 改成你要的内容"
    echo "    2) git add <文件>"
    echo "    3) git commit --no-edit"
    echo "    4) 再跑 bash tools/publish.sh \"$msg\""
    pause; exit 1
  fi
  echo "  已与 main 同步"
fi

if [ "$NO_PUSH" = "1" ]; then
  echo ""
  echo "已提交但未推送（--no-push）。"
  pause; exit 0
fi

echo ""
echo "[7/7] 推送到远程 ..."
git push || fail "推送失败（网络或权限）"

hash=$(git rev-parse --short HEAD)
echo ""
echo "完成：已推送 $branch（commit $hash）"
echo ""
echo "请把下面这段话发给仓库管理员（复制即可）："
echo "------------------------------------------------------------"
echo "Hi，我把最新更新推到了 update-tianqi 分支（commit $hash），麻烦合并到 main 并发布，谢谢！"
echo "------------------------------------------------------------"
pause
