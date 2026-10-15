#!/usr/bin/env bash
# BIRD Lab 网站一键发布（Git Bash 版）
#
# 一行命令搞定：自动生成页面 → 全站自检 → 提交 → 推送 → 打印给管理员的话术
#
# 用法（Git Bash 中）：
#   cd "/d/BIRD Lab - Tianqi Yue/working path/DeepSeek Harness/BIRD Lab Web"
#   bash tools/publish.sh "日常推送"
#
# 可选参数：
#   --skip-check   跳过自动生成与自检（不推荐）
#   --no-push      只提交，不推送

set -u
cd "$(dirname "$0")/.." || exit 1

SKIP_CHECK=0; NO_PUSH=0; msg=""
for a in "$@"; do
  case "$a" in
    --skip-check) SKIP_CHECK=1 ;;
    --no-push)    NO_PUSH=1 ;;
    *) [ -z "$msg" ] && msg="$a" ;;
  esac
done

pause() { read -r -p "按回车关闭" _ ; }

echo "=== 发布前检查 ==="
echo "目录: $(pwd)"
git rev-parse --git-dir >/dev/null 2>&1 || { echo "X 不是 Git 仓库"; pause; exit 1; }

branch=$(git rev-parse --abbrev-ref HEAD)
echo "当前分支: $branch"
if [ "$branch" != "update-tianqi" ]; then
  read -r -p "! 建议在 update-tianqi 上发布（当前 $branch），继续？(y/N) " a
  case "$a" in y|Y) ;; *) echo "已取消"; exit 0 ;; esac
fi

echo ""
echo "[1/6] 检查是否有改动 ..."
if [ -z "$(git status --porcelain)" ]; then
  echo "没有可提交的改动（工作区干净）。"
  pause; exit 0
fi
git status --short | head -20

echo ""
echo "[2/6] 拉取远程最新 ..."
git fetch origin --prune || echo "! fetch 失败（网络？）继续尝试"
echo ""
echo "[2.5/6] 同步 main（落后则变基）..."
counts=$(git rev-list --left-right --count origin/main...HEAD 2>/dev/null || printf '0\t0')
behind=$(printf '%s' "$counts" | cut -f1)
if [ "${behind:-0}" != "0" ]; then
  echo "  落后 main ${behind} 个提交，执行 rebase ..."
  if ! git rebase origin/main; then
    echo ""
    echo "X rebase 遇到冲突，已停止（未提交）。处理办法："
    echo "   1) 改好冲突文件 -> git add <文件> -> git rebase --continue"
    echo "   2) 放弃本次变基：git rebase --abort"
    echo "   拿不准就找助手，不要硬来。"
    pause; exit 1
  fi
  echo "  已变基到 main 最新"
else
  echo "  已包含 main 全部提交，无需变基"
fi

# 找 python（优先 PATH，其次 DSH 自带运行时）
PY=""
if command -v python >/dev/null 2>&1; then
  PY="python"
elif [ -x "/c/Users/Administrator/.dsh/dsh-runtimes/dsh-primary-runtime/dependencies/python/python.exe" ]; then
  PY="/c/Users/Administrator/.dsh/dsh-runtimes/dsh-primary-runtime/dependencies/python/python.exe"
fi

if [ -z "$PY" ]; then
  echo "! 没找到 python，无法自动生成页面与自检。"
  if [ "$SKIP_CHECK" = "0" ]; then
    read -r -p "跳过生成与自检、直接提交？(y/N) " a
    case "$a" in y|Y) SKIP_CHECK=1 ;; *) echo "已取消（建议让助手处理 python 路径）"; pause; exit 0 ;; esac
  fi
fi

if [ -n "$PY" ] && [ "$SKIP_CHECK" = "0" ]; then
  echo ""
  echo "[3/6] 由数据源重新生成页面 ..."
  for s in build_members.py build_news.py build_publications.py build_chrome.py; do
    out=$("$PY" "tools/$s" 2>&1); rc=$?
    echo "  $s -> $(printf '%s' "$out" | tail -1)"
    if [ $rc -ne 0 ]; then
      echo ""
      echo "X $s 运行出错，已停止（未提交）："
      printf '%s\n' "$out" | tail -20
      echo "请把上面的信息发给助手。"
      pause; exit 1
    fi
  done

  echo ""
  echo "[4/6] 全站自检 ..."
  out=$("$PY" tools/check_site.py 2>&1); rc=$?
  printf '%s\n' "$out" | tail -8
  if [ $rc -ne 0 ]; then
    echo ""
    echo "X 自检未通过，已停止提交（请把上面的问题清单发给助手）。"
    pause; exit 1
  fi
else
  echo ""
  echo "[3-4/6] 已跳过生成与自检"
fi

echo ""
echo "[5/6] 暂存并提交 ..."
git add --renormalize .
git add .
if git diff --cached --quiet; then
  echo "暂存区没有改动，结束。"
  pause; exit 0
fi
if [ -z "$msg" ]; then
  echo "常用写法（简短，仓库公开可见）：增加了成员 / 增加了新闻 / 修改了信息 / 更新了论文"
  read -r -p "提交说明（回车使用「更新了网页」）: " msg
  [ -z "$msg" ] && msg="更新了网页"
fi
if ! git commit -m "$msg"; then
  echo "X 提交失败"; pause; exit 1
fi

if [ "$NO_PUSH" = "1" ]; then
  echo ""
  echo "已提交但未推送（--no-push）。"
  pause; exit 0
fi

echo ""
echo "[6/6] 推送到远程 ..."
if ! git push; then
  echo "! 普通推送失败，尝试 --force-with-lease ..."
  if ! git push --force-with-lease; then
    echo "X 推送失败（网络或权限）"; pause; exit 1
  fi
fi

hash=$(git rev-parse --short HEAD)
echo ""
echo "完成：已推送 $branch（commit $hash）"
echo ""
echo "请把下面这段话发给仓库管理员（复制即可）："
echo "------------------------------------------------------------"
echo "Hi，我把最新更新推到了 update-tianqi 分支（commit $hash），麻烦合并到 main 并发布，谢谢！"
echo "------------------------------------------------------------"
pause
