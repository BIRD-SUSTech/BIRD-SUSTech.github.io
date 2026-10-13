#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
把 6 个主页面的导航栏 / 页脚 / 二维码弹窗统一为 tools/chrome.py 中的模板。

用法：
    python tools/build_chrome.py            # 生成并写入
    python tools/build_chrome.py --check    # 只比较，不写文件

成员页的这三块由 tools/build_members.py 生成（同样取自 chrome.py）。
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import chrome  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent

PAGES = {
    "index.html": "home",
    "people.html": "people",
    "research.html": "research",
    "publications.html": "publications",
    "news.html": "news",
    "join.html": "join",
}

NAV_RE = re.compile(r'[ \t]*<nav class="navbar".*?</nav>', re.S)
FOOT_RE = re.compile(r'[ \t]*<footer class="footer">.*?</footer>', re.S)
QR_RE = re.compile(r'[ \t]*<!-- ===== 小红书二维码模态框 ===== -->\s*'
                   r'<div class="qr-modal" id="qrModal">.*?</div>\s*</div>', re.S)


def write_lf(path, text):
    with path.open("w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def main():
    check = "--check" in sys.argv
    changed = []
    for name, active in PAGES.items():
        path = ROOT / name
        html = path.read_text(encoding="utf-8")
        original = html

        if not NAV_RE.search(html):
            print(f"[warn] {name}: 找不到导航栏")
            continue
        if not FOOT_RE.search(html):
            print(f"[warn] {name}: 找不到页脚")
            continue

        html = NAV_RE.sub(lambda _: chrome.navbar(active), html, count=1)
        html = FOOT_RE.sub(lambda _: chrome.footer(), html, count=1)
        if QR_RE.search(html):
            html = QR_RE.sub(lambda _: chrome.qr_modal(), html, count=1)
        else:
            print(f"[warn] {name}: 找不到二维码弹窗")

        if html == original:
            print(f"  {name:22s} 未变")
            continue
        changed.append(name)
        if check:
            print(f"  {name:22s} 将会更新")
        else:
            write_lf(path, html)
            print(f"  {name:22s} 已更新")

    print(f"\n共 {len(changed)} 个页面需要变更" + ("（--check：未写入）" if check else ""))


if __name__ == "__main__":
    main()
