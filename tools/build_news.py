#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
由 data/news.json 生成两处新闻内容：
  1) news.html 的新闻列表   （锚点 <!-- NEWS_LIST:START --> … <!-- NEWS_LIST:END -->）
  2) index.html 首页 Latest News 卡片区（锚点 <!-- HOME_NEWS:START --> … <!-- HOME_NEWS:END -->）

用法：
    python tools/build_news.py            # 生成并写入
    python tools/build_news.py --check    # 只比较，不写文件

首页卡片可用 home_title_* / home_body_* / home_link 覆盖新闻页文案（留空则沿用）。
"""
import json
import re
import sys
from pathlib import Path

import sys as _sys
if hasattr(_sys.stdout, "reconfigure"):
    _sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "news.json"

PIN = '<span class="pin-badge">📌 <span class="i18n"><span data-lang="en">Pinned</span><span data-lang="zh">置顶</span></span></span>'


def write_lf(path, text):
    with path.open("w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def i18n(en, zh):
    return f'<span class="i18n"><span data-lang="en">{en}</span><span data-lang="zh">{zh}</span></span>'


def link_html(link, indent):
    if not link or not link.get("url"):
        return ""
    return f'{indent}<a href="{link["url"]}" class="btn news-btn">{i18n(link["en"], link["zh"])}</a>'


def tag_html(tag_en, tag_zh, indent):
    if not tag_en and not tag_zh:
        return ""
    return f'{indent}<span class="tag"># {i18n(tag_en, tag_zh)}</span>'


def build_news_list(items):
    """news.html 的新闻列表（含配图的条目用 news-body / news-media 两栏结构）。"""
    blocks = []
    for it in items:
        if not it.get("in_news"):
            continue
        cls = "news-card reveal"
        if it["reveal_delay"]:
            cls += f' reveal-delay-{it["reveal_delay"]}'
        if it["image"]:
            cls += " with-image"
        inner = []
        if not it["image"] and it["pinned"]:
            inner.append(f"                    {PIN}")
        inner.append(f'                    <div class="date"><span class="dot"></span> {it["date"]}</div>')
        inner.append(f'                    <h4>\n                        {i18n(it["title_en"], it["title_zh"])}\n                    </h4>')
        inner.append(f'                    <p>\n                        {i18n(it["body_en"], it["body_zh"])}\n                    </p>')
        lk = link_html(it["link"], "                    ")
        if lk:
            inner.append(lk)
        tg = tag_html(it["tag_en"], it["tag_zh"], "                    ")
        if tg:
            inner.append(tg)
        if it["image"]:
            body = "\n".join(inner)
            blocks.append(f"""                <!-- 新闻：{it['date']} -->
                <article class="{cls}">
                    <div class="news-body">
{body}
                    </div>
                    <div class="news-media"><img src="{it['image']}" alt="{it['date']}" /></div>
                </article>""")
        else:
            blocks.append(f"""                <!-- 新闻：{it['date']} -->
                <article class="{cls}">
{chr(10).join(inner)}
                </article>""")
    body = "\n\n".join(blocks)
    return ("                <!-- NEWS_LIST:START （由 tools/build_news.py 生成，勿手工编辑） -->\n"
            f"{body}\n"
            "                <!-- NEWS_LIST:END -->")


def build_home_grid(items):
    """index.html 首页 Latest News 卡片（无配图，使用 home_* 文案覆盖）。"""
    blocks = []
    for it in items:
        if not it.get("on_home"):
            continue
        delay = it.get("home_reveal_delay") or 1
        inner = []
        if it["pinned"]:
            inner.append(f"                    {PIN}")
        inner.append(f'                    <div class="date"><span class="dot"></span> {it["date"]}</div>')
        t_en = it.get("home_title_en") or it["title_en"]
        t_zh = it.get("home_title_zh") or it["title_zh"]
        b_en = it.get("home_body_en") or it["body_en"]
        b_zh = it.get("home_body_zh") or it["body_zh"]
        inner.append(f'                    <h4>\n                        {i18n(t_en, t_zh)}\n                    </h4>')
        inner.append(f'                    <p>\n                        {i18n(b_en, b_zh)}\n                    </p>')
        lk = link_html(it.get("home_link") or it["link"], "                    ")
        if lk:
            inner.append(lk)
        tg = tag_html(it["tag_en"], it["tag_zh"], "                    ")
        if tg:
            inner.append(tg)
        blocks.append(f"""                <article class="news-card reveal reveal-delay-{delay}">
{chr(10).join(inner)}
                </article>""")
    body = "\n\n".join(blocks)
    return ("                        <!-- HOME_NEWS:START （由 tools/build_news.py 生成，勿手工编辑） -->\n"
            f"{body}\n"
            "                        <!-- HOME_NEWS:END -->")


def replace_block(html, start, end, new_block, legacy_re, check):
    pattern = re.compile(r"[ \t]*" + start + r".*?" + end, re.S)
    if pattern.search(html):
        return pattern.sub(lambda _: new_block, html, count=1), "替换"
    m = re.search(legacy_re, html, re.S)
    if not m:
        raise SystemExit(f"找不到 {start} 的插入位置")
    return html[:m.start(1)] + "\n" + new_block + html[m.end(1):], "替换旧内容"


def main():
    check = "--check" in sys.argv
    items = json.loads(DATA.read_text(encoding="utf-8"))["items"]

    targets = [
        ("news.html", "<!-- NEWS_LIST:START", "<!-- NEWS_LIST:END -->", build_news_list(items),
         r'(<div class="news-list">)(.*?)(\s*</div>\s*</div>\s*</section>)'),
        ("index.html", "<!-- HOME_NEWS:START", "<!-- HOME_NEWS:END -->", build_home_grid(items),
         r'(<div class="news-grid">)(.*?)(\s*</div>\s*</div>\s*</section>)'),
    ]

    for name, start, end, block, legacy in targets:
        path = ROOT / name
        html = path.read_text(encoding="utf-8")
        # 旧内容中若已含上一次生成的块，正则需容忍
        m = re.search(legacy, html, re.S)
        if not m:
            print(f"[warn] {name}: 找不到容器")
            continue
        new_html = html[:m.start(2)] + "\n" + block + html[m.end(2):]
        action = "重写容器"
        if new_html == html:
            print(f"  {name:14s} 未变")
            continue
        if check:
            print(f"  {name:14s} 将会更新（{action}）")
            continue
        write_lf(path, new_html)
        print(f"  {name:14s} 已更新（{action}）")


if __name__ == "__main__":
    main()
