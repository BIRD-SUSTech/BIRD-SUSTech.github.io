#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
由 data/publications.json 生成 publications.html 中的：
  1) 论文列表区块（锚点 <!-- PUBLICATIONS:START --> ... <!-- PUBLICATIONS:END -->）
  2) 三个筛选下拉的选项（yearFilter / researchFilter / keywordFilter）

用法：
    python tools/build_publications.py            # 生成并写入
    python tools/build_publications.py --check    # 只比较，不写文件

页面其余部分（标题区、页脚、脚本）仍按现状手工维护。
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "publications.json"
PAGE = ROOT / "publications.html"

LABELS = {
    "year": ("All Years", "全部年份"),
    "research": ("All Research", "全部研究方向"),
    "keyword": ("All Keywords", "全部关键词"),
}


def write_lf(path, text):
    with path.open("w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def i18n(en, zh):
    return f'<span class="i18n"><span data-lang="en">{en}</span><span data-lang="zh">{zh}</span></span>'


def build_items(items, empty_note):
    blocks = []
    for n, it in enumerate(items, start=1):
        attrs = f'class="publication-item reveal reveal-delay-{it["reveal_delay"] or n}"'
        if it.get("id"):
            attrs += f' id="{it["id"]}"'
        attrs += f' data-year="{it["year"]}" data-research="{it["research"]}"'
        attrs += f' data-keywords="{",".join(it["keywords"])}"'

        tags = "\n".join(
            f'                    <a href="publications.html?keyword={t["slug"]}">{i18n(t["en"], t["zh"])}</a>'
            for t in it["tags"]
        )
        blocks.append(f"""            <!-- ====== 论文 {n} ====== -->
            <div {attrs}>
                <div class="title">
                    <a href="{it['url']}" target="_blank" rel="noopener">
                        {i18n(it['title_en'], it['title_zh'])}
                    </a>
                </div>
                <div class="authors">{it['authors_html']}</div>
                <div class="venue">{it['venue']}</div>
                <div class="tags">
{tags}
                </div>
            </div>""")
    body = "\n\n".join(blocks)
    note_en = (empty_note or {}).get("en") or "No publications match the selected filters."
    note_zh = (empty_note or {}).get("zh") or "没有符合筛选条件的论文。"
    return (
        "            <!-- PUBLICATIONS:START （由 tools/build_publications.py 生成，勿手工编辑） -->\n"
        f"{body}\n"
        '            <p class="pub-empty" id="noResults" style="display:none;">\n'
        f"                {i18n(note_en, note_zh)}\n"
        "            </p>\n"
        "            <!-- PUBLICATIONS:END -->"
    )


def build_options(kind, options):
    en_all, zh_all = LABELS[kind]
    lines = [f'                <option value="all" data-en="{en_all}" data-zh="{zh_all}">{en_all}</option>']
    for o in options:
        if kind == "year":
            lines.append(f'                <option value="{o["slug"]}">{o["slug"]}</option>')
            continue
        lines.append(
            f'                <option value="{o["slug"]}" data-en="{o["en"]}" data-zh="{o["zh"]}">{o["en"]}</option>'
        )
    return "\n".join(lines)


def update_block(html, start_marker, end_marker, new_block, anchor_re=None):
    """用锚点替换区块；首次运行时用 anchor_re（第 2 组为旧内容）替换旧区块。"""
    pattern = re.compile(r"[ \t]*" + start_marker + r".*?" + end_marker)
    if pattern.search(html):
        return pattern.sub(lambda _: new_block, html, count=1), "替换"
    m = re.search(anchor_re, html, re.S)
    if not m:
        raise SystemExit("找不到插入位置")
    return html[:m.start(2)] + "\n" + new_block + html[m.end(2):], "替换旧列表"


def main():
    check = "--check" in sys.argv
    data = json.loads(DATA.read_text(encoding="utf-8"))
    items = data["items"]
    if "--from-git" in sys.argv:
        import subprocess
        out = subprocess.run(["git", "show", "HEAD:publications.html"], cwd=ROOT, capture_output=True)
        html = out.stdout.decode("utf-8") if out.returncode == 0 else PAGE.read_text(encoding="utf-8")
        print("[from-git] 以 git HEAD 版本为基础")
    else:
        html = PAGE.read_text(encoding="utf-8")
    original = html

    # 1) 论文列表
    html, action_items = update_block(
        html,
        "<!-- PUBLICATIONS:START",
        "<!-- PUBLICATIONS:END -->",
        build_items(items, data.get("empty_note", {})),
        r'(<section class="publications-section" id="publications">\s*<div class="container">)(.*?)(\s*</div>\s*</section>)',
    )

    # 2) 三个下拉
    years = sorted({i["year"] for i in items if i["year"]}, reverse=True)
    selects = [
        ("yearFilter", "year", [{"slug": y, "en": y, "zh": y} for y in years]),
        ("researchFilter", "research", data["research_options"]),
        ("keywordFilter", "keyword", data["keyword_options"]),
    ]
    actions = []
    for select_id, kind, options in selects:
        body = build_options(kind, options)
        new_select = f'<select id="{select_id}" class="year-select">\n{body}\n            </select>'
        pat = re.compile(r'<select id="%s".*?</select>' % select_id, re.S)
        if not pat.search(html):
            raise SystemExit(f"找不到 {select_id}")
        html = pat.sub(lambda _: new_select, html, count=1)
        actions.append(f"{select_id}: {len(options)} 项")

    changed = html != original
    print(f"论文列表：{action_items}；" + "；".join(actions))
    if not changed:
        print("publications.html 未变")
        return
    if check:
        print("publications.html 将会更新")
        return
    write_lf(PAGE, html)
    print("publications.html 已更新")


if __name__ == "__main__":
    main()
