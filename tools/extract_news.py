#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
一次性迁移脚本：从 news.html 与 index.html 反向提取新闻数据 -> data/news.json

- news.html 提供新闻列表条目（含配图、置顶、按钮、标签）
- index.html 提供首页 Latest News 卡片（文案通常更短，单独保存为 home_* 字段）
- 两处按日期合并为同一批条目，用 in_news / on_home 标记出现位置
"""
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "news.json"

I18N = re.compile(
    r'<span class="i18n">\s*<span data-lang="en">(.*?)</span>\s*'
    r'<span data-lang="zh">(.*?)</span>\s*</span>',
    re.S,
)
ARTICLE = re.compile(r'<article class="news-card ([^"]*)">(.*?)</article>', re.S)


def write_lf(path, text):
    with path.open("w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def pair(fragment):
    m = I18N.search(fragment)
    return (m.group(1).strip(), m.group(2).strip()) if m else ("", "")


def load(name, from_git):
    if from_git:
        out = subprocess.run(["git", "show", f"HEAD:{name}"], cwd=ROOT, capture_output=True)
        if out.returncode == 0:
            return out.stdout.decode("utf-8")
        print(f"[warn] git show {name} 失败，改用工作区文件")
    return (ROOT / name).read_text(encoding="utf-8")


def parse_cards(html, grid_only=False):
    """解析 news-card 条目。grid_only=True 时只取 news-grid 区块（首页）。"""
    if grid_only:
        m = re.search(r'<div class="news-grid">(.*?)</div>\s*</section>', html, re.S)
        html = m.group(1) if m else html
    cards = []
    for cls, body in ARTICLE.findall(html):
        rec = {
            "pinned": "pin-badge" in body,
            "with_image": "with-image" in cls,
            "reveal_delay": int(re.search(r"reveal-delay-(\d+)", cls).group(1))
            if re.search(r"reveal-delay-(\d+)", cls) else 0,
        }
        m = re.search(r'<div class="date"><span class="dot"></span>\s*([^<]+?)\s*</div>', body)
        rec["date"] = m.group(1) if m else ""
        rec["title_en"], rec["title_zh"] = pair(re.search(r"<h4>(.*?)</h4>", body, re.S).group(1)
                                                if re.search(r"<h4>(.*?)</h4>", body, re.S) else "")
        rec["body_en"], rec["body_zh"] = pair(re.search(r"<p>(.*?)</p>", body, re.S).group(1)
                                              if re.search(r"<p>(.*?)</p>", body, re.S) else "")
        m = re.search(r'<a href="([^"]+)" class="btn news-btn">(.*?)</a>', body, re.S)
        if m:
            en, zh = pair(m.group(2))
            rec["link"] = {"url": m.group(1), "en": en, "zh": zh}
        else:
            rec["link"] = None
        mi = body.find('<span class="tag">')
        rec["tag_en"], rec["tag_zh"] = pair(body[mi:]) if mi >= 0 else ("", "")
        m = re.search(r'<div class="news-media"><img src="([^"]+)"', body)
        rec["image"] = m.group(1) if m else ""
        cards.append(rec)
    return cards


def main():
    from_git = "--from-git" in sys.argv
    news_cards = parse_cards(load("news.html", from_git))
    home_cards = parse_cards(load("index.html", from_git), grid_only=True)
    print(f"news.html 条目 {len(news_cards)} 条；index.html 首页卡片 {len(home_cards)} 条")

    items = []
    for c in news_cards:
        it = {
            "id": c["date"].replace(".", "-"),
            "date": c["date"],
            "pinned": c["pinned"],
            "image": c["image"],
            "reveal_delay": c["reveal_delay"],
            "title_en": c["title_en"], "title_zh": c["title_zh"],
            "body_en": c["body_en"], "body_zh": c["body_zh"],
            "link": c["link"],
            "tag_en": c["tag_en"], "tag_zh": c["tag_zh"],
            "in_news": True,
            "on_home": False,
            "home_reveal_delay": 0,
            "home_title_en": "", "home_title_zh": "",
            "home_body_en": "", "home_body_zh": "",
            "home_link": None,
        }
        items.append(it)

    # 首页卡片按日期并入
    for h in home_cards:
        target = next((i for i in items if i["date"] == h["date"]), None)
        if target is None:
            target = {
                "id": h["date"].replace(".", "-"), "date": h["date"], "pinned": h["pinned"],
                "image": "", "reveal_delay": 0,
                "title_en": h["title_en"], "title_zh": h["title_zh"],
                "body_en": "", "body_zh": "", "link": None,
                "tag_en": h["tag_en"], "tag_zh": h["tag_zh"],
                "in_news": False,
            }
            items.append(target)
            print(f"  [新增] 仅首页有的条目：{h['date']}")
        target.update({
            "on_home": True,
            "home_title_en": h["title_en"], "home_title_zh": h["title_zh"],
            "home_reveal_delay": h["reveal_delay"],
            "home_body_en": h["body_en"], "home_body_zh": h["body_zh"],
            "home_link": h["link"],
        })
        if h["title_en"] and h["title_en"] != target["title_en"]:
            print(f"  [注意] {h['date']} 首页标题与新闻页不同")

    for it in items:
        print(f"  {it['id']:12s} news={'Y' if it['in_news'] else 'n'} home={'Y' if it['on_home'] else 'n'} "
              f"img={'Y' if it['image'] else 'n'} pinned={'Y' if it['pinned'] else 'n'} tag={it['tag_en']}")

    write_lf(DATA, json.dumps({"items": items}, ensure_ascii=False, indent=2) + "\n")
    print(f"\n写入 {DATA}（{len(items)} 条）")


if __name__ == "__main__":
    sys.exit(main())
