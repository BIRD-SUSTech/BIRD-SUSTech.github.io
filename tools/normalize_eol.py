#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
把仓库内文本文件的换行统一为 LF（对应 .gitattributes 的 `* text=auto eol=lf`）。

用法：
    python tools/normalize_eol.py            # 转换并写入
    python tools/normalize_eol.py --check    # 只列出含 CRLF 的文件

说明：git 在 index 层已按 .gitattributes 规范化，因此本操作通常不产生 diff 噪音；
      统一为 LF 只是让工作区文件与脚本/编辑器行为一致，避免多行替换失败。
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEXT_SUFFIXES = {".html", ".css", ".js", ".json", ".md", ".py", ".txt", ".xml", ".yml", ".yaml", ".gitattributes"}
SKIP_DIRS = {".git", "node_modules", "dsh-acl-recovery"}


def main():
    check = "--check" in sys.argv
    targets = []
    for p in sorted(ROOT.rglob("*")):
        if not p.is_file():
            continue
        if any(part in SKIP_DIRS for part in p.relative_to(ROOT).parts):
            continue
        if p.name == ".gitattributes" or p.suffix.lower() in TEXT_SUFFIXES:
            data = p.read_bytes()
            if b"\r\n" in data or (b"\r" in data and b"\n" not in data):
                targets.append((p, data))

    if not targets:
        print("所有文本文件已是 LF，无需处理。")
        return 0

    for p, data in targets:
        rel = p.relative_to(ROOT)
        if check:
            print(f"[CRLF] {rel}")
            continue
        new = data.replace(b"\r\n", b"\n")
        p.write_bytes(new)
        print(f"[fixed] {rel}")
    print(f"\n共 {len(targets)} 个文件" + ("（--check：未写入）" if check else "已统一为 LF"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
