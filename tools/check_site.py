#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
全站自检：一次性发现常见的低级问题，替代人工逐页检查。

检查项：
  1. 内部链接：href="xxx.html" 指向的文件是否存在
  2. 图片：img src 指向的文件是否存在（跳过 http(s) 外链）
  3. 双语成对：每个页面 data-lang="en" 与 data-lang="zh" 数量是否相等
  4. 标签配对：<a> 与 </a>、<div> 与 </div> 数量是否平衡（粗略启发式）
  5. 生成区块锚点：members 页与 people.html 的卡片区、publications 列表锚点是否成对

用法：
    python tools/check_site.py          # 输出问题清单
    python tools/check_site.py --all    # 连正常信息一起输出
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKIP_DIRS = {".git", "node_modules", "tools", "data", "inbox", "member materials"}

HREF = re.compile(r'href="([^"#?]+?\.html)(?:[#?][^"]*)?"')
SRC = re.compile(r'src="([^"]+)"')


def pages():
    for p in sorted(ROOT.rglob("*.html")):
        rel = p.relative_to(ROOT)
        if any(part in SKIP_DIRS for part in rel.parts):
            continue
        yield p, rel


def strip_noise(html):
    """去掉注释与 script/style 内容，避免其中出现的标签影响统计。"""
    html = re.sub(r"<!--.*?-->", "", html, flags=re.S)
    html = re.sub(r"<script\b.*?</script>", "", html, flags=re.S)
    html = re.sub(r"<style\b.*?</style>", "", html, flags=re.S)
    return html


def check_page(path, rel):
    raw = path.read_text(encoding="utf-8")
    html = strip_noise(raw)
    problems = []

    # 1) 内部链接
    for target in set(HREF.findall(html)):
        if target.startswith(("http://", "https://", "mailto:", "//")):
            continue
        resolved = (path.parent / target).resolve()
        if not resolved.exists():
            problems.append(f"链接失效: {target}")

    # 2) 图片
    for src in set(SRC.findall(html)):
        if src.startswith(("http://", "https://", "data:", "//")):
            continue
        resolved = (path.parent / src).resolve()
        if not resolved.exists():
            problems.append(f"图片缺失: {src}")

    # 3) 双语成对
    en = html.count('data-lang="en"')
    zh = html.count('data-lang="zh"')
    if en != zh:
        problems.append(f"双语不配对: en={en} zh={zh}")

    # 4) 标签配对（粗略）
    open_a = len(re.findall(r"<a[\s>]", html))
    close_a = html.count("</a>")
    if open_a != close_a:
        problems.append(f"<a> 标签不配对: 开={open_a} 闭={close_a}")
    open_div = len(re.findall(r"<div[\s>]", html))
    close_div = html.count("</div>")
    if open_div != close_div:
        problems.append(f"<div> 标签不配对: 开={open_div} 闭={close_div}")

    # 5) 生成区块锚点（注释形式，用未剥离的原文统计）
    for start, end in (("MEMBER_GRID:START", "MEMBER_GRID:END"), ("PUBLICATIONS:START", "PUBLICATIONS:END")):
        if start in raw or end in raw:
            if raw.count(start) != raw.count(end):
                problems.append(f"生成锚点不配对: {start}/{end}")

    return problems


def main():
    show_all = "--all" in sys.argv
    total = 0
    bad = 0
    for path, rel in pages():
        total += 1
        problems = check_page(path, rel)
        if problems:
            bad += 1
            print(f"\n[{rel}]")
            for p in problems:
                print("   ✗", p)
        elif show_all:
            print(f"[{rel}] ✓")
    print(f"\n检查 {total} 个页面，{bad} 个页面有问题" if bad else f"\n检查 {total} 个页面，全部通过 ✓")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
