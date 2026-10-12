#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
一次性迁移脚本：从 publications.html 反向提取论文数据 -> data/publications.json

支持 --from-git：从 git HEAD:publications.html 读取（重建数据源时用）。
提取内容：
  - 每条 publication-item（id / 年份 / 研究方向 / 关键词 / 标题中英 / DOI 链接 / 作者 / 期刊 / 标签）
  - 三个筛选下拉的选项（research_options / keyword_options）
"""
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "publications.json"

I18N = re.compile(
    r'<span class="i18n">\s*<span data-lang="en">(.*?)</span>\s*'
    r'<span data-lang="zh">(.*?)</span>\s*</span>',
    re.S,
)
ITEM = re.compile(r'<div class="publication-item ([^"]*)"([^>]*)>(.*?)(?=<div class="publication-item |\Z)', re.S)
DELAY = re.compile(r"reveal-delay-(\d+)")
OPTION = re.compile(r'<option value="([^"]*)"(?:\s+data-en="([^"]*)"\s+data-zh="([^"]*)")?\s*>([^<]*)</option>')


def write_lf(path, text):
    """以 LF 换行写文件（Windows 下 text mode 会写成 CRLF，故显式指定）。"""
    with path.open("w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def pair(fragment):
    m = I18N.search(fragment)
    return (m.group(1).strip(), m.group(2).strip()) if m else ("", "")


def load_html(from_git):
    if from_git:
        out = subprocess.run(["git", "show", "HEAD:publications.html"], cwd=ROOT, capture_output=True)
        if out.returncode == 0:
            return out.stdout.decode("utf-8")
        print("[warn] git show 失败，改用工作区文件")
    return (ROOT / "publications.html").read_text(encoding="utf-8")


def select_options(html, select_id):
    m = re.search(r'<select id="%s".*?</select>' % select_id, html, re.S)
    if not m:
        return []
    out = []
    for slug, en, zh, text in OPTION.findall(m.group(0)):
        if slug == "all":
            continue
        out.append({"slug": slug, "en": en or text.strip(), "zh": zh or text.strip()})
    return out


def parse_items(html):
    # 只取出版物列表区块
    m = re.search(r'<section class="publications-section".*?</section>', html, re.S)
    section = m.group(0) if m else html
    items = []
    for cls, attrs, body in ITEM.findall(section):
        rec = {}
        for key, tag in (("id", "id"), ("year", "data-year"), ("research", "data-research")):
            mm = re.search(r'%s="([^"]*)"' % tag, attrs)
            rec[key] = mm.group(1) if mm else ""
        mm = re.search(r'data-keywords="([^"]*)"', attrs)
        rec["keywords"] = [k.strip() for k in (mm.group(1) if mm else "").split(",") if k.strip()]
        d = DELAY.search(cls)
        rec["reveal_delay"] = int(d.group(1)) if d else 0

        mm = re.search(r'<div class="title">\s*<a href="([^"]*)"', body, re.S)
        rec["url"] = mm.group(1) if mm else ""
        title_block = re.search(r'<div class="title">(.*?)</div>', body, re.S)
        rec["title_en"], rec["title_zh"] = pair(title_block.group(1) if title_block else "")

        mm = re.search(r'<div class="authors">(.*?)</div>', body, re.S)
        rec["authors_html"] = mm.group(1).strip() if mm else ""
        mm = re.search(r'<div class="venue">(.*?)</div>', body, re.S)
        rec["venue"] = mm.group(1).strip() if mm else ""

        tags = []
        tag_block = re.search(r'<div class="tags">(.*?)</div>', body, re.S)
        if tag_block:
            for tslug, tbody in re.findall(r'<a href="publications\.html\?keyword=([^"]*)">(.*?)</a>', tag_block.group(1), re.S):
                en, zh = pair(tbody)
                tags.append({"slug": tslug, "en": en, "zh": zh})
        rec["tags"] = tags
        items.append(rec)
    return items


def main():
    from_git = "--from-git" in sys.argv
    html = load_html(from_git)
    items = parse_items(html)
    m = re.search(r'<p class="pub-empty"[^>]*>(.*?)</p>', html, re.S)
    empty_en, empty_zh = pair(m.group(1)) if m else (
        "No publications match the selected filters.",
        "没有符合筛选条件的论文。",
    )
    data = {
        "empty_note": {"en": empty_en, "zh": empty_zh},
        "items": items,
        "research_options": select_options(html, "researchFilter"),
        "keyword_options": select_options(html, "keywordFilter"),
    }
    print(f"论文 {len(items)} 篇；研究方向选项 {len(data['research_options'])} 个；关键词选项 {len(data['keyword_options'])} 个")
    years = sorted({i["year"] for i in items if i["year"]}, reverse=True)
    print("年份:", ", ".join(years))
    for i in items:
        flag = "" if (i["title_en"] and i["title_zh"] and i["url"] and i["authors_html"]) else "  [缺字段]"
        print(f"  {i['id']:28s} {i['year']} {i['research']:18s} tags={len(i['tags'])}{flag}")
    # 检查 tags 是否都能在 keyword_options 中找到
    known = {o["slug"] for o in data["keyword_options"]}
    unknown = sorted({t["slug"] for i in items for t in i["tags"]} - known)
    if unknown:
        print("[注意] 以下标签不在关键词下拉中：", ", ".join(unknown))
    write_lf(DATA, json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    print(f"\n写入 {DATA}")


if __name__ == "__main__":
    sys.exit(main())
