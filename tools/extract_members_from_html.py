#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
一次性迁移脚本：从现有 HTML 反向提取成员数据 -> data/members.json

- 成员顺序取自 people.html 中 member-grid 的卡片顺序
- 单页字段取自 members/<slug>.html（姓名/角色/邮箱/meta/简介/研究方向/教育/论文）
- PI（tianqi-yue）单独识别，附带 head_css 与 faculty 按钮等特殊片段
之后所有成员信息都由 data/members.json 维护，页面由 build_members.py 生成。
"""
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "members.json"

I18N = re.compile(
    r'<span class="i18n">\s*<span data-lang="en">(.*?)</span>\s*'
    r'<span data-lang="zh">(.*?)</span>\s*</span>',
    re.S,
)
SECTION = re.compile(r'<section class="section">(.*?)</section>', re.S)
META_ITEM = re.compile(r'<div class="meta-item">(.*?)</div>\s*(?=<div class="meta-item">|</div>)', re.S)
LI = re.compile(r"<li>(.*?)</li>", re.S)
PUB_ITEM = re.compile(r'<div class="pub-item">(.*?)</div>\s*</div>', re.S)

# 现有页面的角色用语不统一，统一映射到标准用语（用户已确认）
ROLE_CANON = {
    "Principal Investigator (PI)": ("Principal Investigator (PI)", "课题组组长 (PI)", "pi"),
    "Postdoctoral Researcher": ("Postdoctoral Fellow", "博士后", "postdoc"),
    "Postdoctoral Fellow": ("Postdoctoral Fellow", "博士后", "postdoc"),
    "PhD Student": ("PhD Student", "博士研究生", "phd"),
    "Master's Student": ("Master Student", "硕士研究生", "master"),
    "Master Student": ("Master Student", "硕士研究生", "master"),
    "Visiting Student": ("Visiting Student", "访问学生", "visiting"),
    "Undergraduate Student": ("Undergraduate Student", "本科生", "undergraduate"),
    "Lab Administrator": ("Lab Administrator", "行政人员", "admin"),
}


def write_lf(path, text):
    """以 LF 换行写文件（Windows 下 text mode 会写成 CRLF，故显式指定）。"""
    with path.open("w", encoding="utf-8", newline="\n") as f:
        f.write(text)

def pair(fragment):
    """从片段中取第一组 i18n 中英文本，返回 (en, zh)。"""
    m = I18N.search(fragment)
    if not m:
        return "", ""
    return m.group(1).strip(), m.group(2).strip()


def sections_of(html):
    """返回 {类型: 片段} —— 类型取自 h2 的英文标题。"""
    out = {}
    for block in SECTION.findall(html):
        m = re.search(r"<h2>.*?</h2>", block, re.S)
        if not m:
            continue
        head = m.group(0)
        en, zh = pair(head)
        key = None
        if "About Me" in en:
            key = "about"
        elif "Research Interests" in en:
            key = "research"
        elif en.startswith("Education"):
            key = "education"
        elif "Publications" in en:
            key = "publications"
        if key:
            out[key] = block
    return out


def load_member_html(slug, from_git=False):
    """读取成员页 HTML；from_git=True 时从 git HEAD 读取（重建数据源时用）。"""
    if from_git:
        out = subprocess.run(["git", "show", f"HEAD:members/{slug}.html"],
                             cwd=ROOT, capture_output=True)
        if out.returncode == 0:
            return out.stdout.decode("utf-8")
        print(f"[warn] git show 失败，改用工作区文件: {slug}")
    return (ROOT / "members" / f"{slug}.html").read_text(encoding="utf-8")


def parse_member(slug, from_git=False):
    html = load_member_html(slug, from_git)
    rec = {"slug": slug}

    # 姓名
    m = re.search(r"<h1>(.*?)</h1>", html, re.S)
    if m:
        h1 = m.group(1).strip()
        if " / " in h1:
            rec["name_en"], rec["name_zh"] = [x.strip() for x in h1.split(" / ", 1)]
        else:
            rec["name_en"], rec["name_zh"] = h1, h1

    # 角色（统一为标准用语）
    m = re.search(r'<div class="role">(.*?)</div>', html, re.S)
    if m:
        rec["role_en"], rec["role_zh"] = pair(m.group(1))
    canon = ROLE_CANON.get(rec.get("role_en", ""))
    if canon:
        rec["role_en"], rec["role_zh"], rec["group"] = canon
    else:
        rec["group"] = "undergraduate"
        print(f"[warn] 未识别的角色用语 '{rec.get('role_en')}' -> {slug}")

    # 照片
    m = re.search(r'<div class="profile-photo reveal"><img src="\.\./images/people/([^"]+)"', html)
    rec["photo"] = m.group(1) if m else ""

    # 邮箱 + 第二条 meta
    rec["email"] = ""
    rec["meta_label_en"] = rec["meta_label_zh"] = ""
    rec["meta_value_en"] = rec["meta_value_zh"] = ""
    metas = re.findall(r'<div class="meta-item">(.*?)</div>\s*(?=<div class="meta-item">|</div>|\s*</div>)', html, re.S)
    for item in metas:
        if "mailto:" in item:
            m = re.search(r'mailto:([^"]+)"', item)
            if m:
                rec["email"] = m.group(1).strip()
        else:
            rec["meta_label_en"], rec["meta_label_zh"] = pair(item)
            m = re.search(r"</span>\s*(?:<span class=\"i18n\">.*?</span>)\s*</div>", item, re.S)
            en, zh = "", ""
            pairs = I18N.findall(item)
            if len(pairs) >= 2:
                en, zh = pairs[1][0].strip(), pairs[1][1].strip()
            rec["meta_value_en"], rec["meta_value_zh"] = en, zh

    # 特殊片段（PI 页的教师主页按钮 / 自定义样式）
    ms = re.search(r"<style>(.*?)</style>", html, re.S)
    mb = re.search(r'<div class="breadcrumb">.*?<a href="([^"]+)"', html, re.S)
    rec["back_link"] = mb.group(1) if mb else "../people.html"
    rec["head_css"] = ms.group(1).strip("\n").rstrip() if ms else ""
    m = re.search(r'(<a[^>]*class="faculty-btn".*?</a>)', html, re.S)
    rec["profile_extra_html"] = m.group(1) if m else ""

    secs = sections_of(html)

    rec["bio_en"] = rec["bio_zh"] = ""
    if "about" in secs:
        m = re.search(r"<p>(.*?)</p>", secs["about"], re.S)
        if m:
            rec["bio_en"], rec["bio_zh"] = pair(m.group(1))

    rec["research_en"] = rec["research_zh"] = ""
    if "research" in secs:
        m = re.search(r"<p>(.*?)</p>", secs["research"], re.S)
        if m:
            rec["research_en"], rec["research_zh"] = pair(m.group(1))

    rec["education"] = []
    if "education" in secs:
        for li in LI.findall(secs["education"]):
            en, zh = pair(li)
            if en or zh:
                rec["education"].append({"en": en, "zh": zh})

    rec["publications"] = []
    if "publications" in secs:
        for block in re.findall(r'<div class="pub-item">(.*?)(?=<div class="pub-item">|\Z)', secs["publications"], re.S):
            title_en, title_zh = pair(block)
            m = re.search(r'<div class="pub-venue">(.*?)</div>', block, re.S)
            venue = m.group(1).strip() if m else ""
            badge_en = badge_zh = ""
            m = re.search(r'<span class="badge">(.*?)</div>', block, re.S)
            if m:
                badge_en, badge_zh = pair(m.group(1))
            if title_en or title_zh:
                rec["publications"].append(
                    {"title_en": title_en, "title_zh": title_zh, "venue": venue,
                     "badge_en": badge_en, "badge_zh": badge_zh}
                )
    return rec


def card_order():
    people = (ROOT / "people.html").read_text(encoding="utf-8")
    slugs = re.findall(r'<a href="members/([a-z0-9\-]+)\.html" class="member-card', people)
    pi = re.findall(r'<a href="members/([a-z0-9\-]+)\.html" title=', people)
    return pi + slugs


def main():
    from_git = "--from-git" in sys.argv
    slugs = card_order()
    records = []
    for slug in slugs:
        path = ROOT / "members" / f"{slug}.html"
        if not path.exists():
            print(f"[skip] 页面不存在: {slug}")
            continue
        rec = parse_member(slug, from_git)
        records.append(rec)
        missing = [k for k in ("name_en", "name_zh", "email", "bio_en", "bio_zh", "research_en", "education") if not rec.get(k)]
        flag = ("  缺: " + ",".join(missing)) if missing else ""
        print(f"[ok] {slug:20s} group={rec['group']:14s} edu={len(rec['education'])} pub={len(rec['publications'])}{flag}")

    DATA.parent.mkdir(parents=True, exist_ok=True)
    write_lf(DATA, json.dumps({"members": records}, ensure_ascii=False, indent=2) + "\n")
    print(f"\n写入 {DATA} —— 共 {len(records)} 位成员")


if __name__ == "__main__":
    sys.exit(main())
