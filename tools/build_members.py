#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
由 data/members.json 生成：
  1) members/<slug>.html        全部成员个人页
  2) people.html 的成员卡片区   （锚点 <!-- MEMBER_GRID:START --> ... <!-- MEMBER_GRID:END -->）

用法：
    python tools/build_members.py            # 生成并写入
    python tools/build_members.py --check    # 只比较，不写文件（打印将会变化的文件）

约定（详见 AGENTS.md）：
  - 不要手工编辑 members/*.html 与 people.html 的卡片区
  - 角色用语、页脚、区块标题均由本脚本统一
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "members.json"
PEOPLE = ROOT / "people.html"

GROUP_ORDER = ["postdoc", "phd", "master", "visiting", "undergraduate", "admin"]

NAVBAR = """    <nav class="navbar" id="navbar" role="navigation" aria-label="主导航">
        <div class="container">
            <div class="navbar-brand"><a href="../index.html" class="navbar-brand-link" aria-label="BIRD Lab Home"><img src="../images/logos/sustech-logo.png" alt="SUSTech" class="navbar-logo" /><span class="logo-text">BIRD</span> Lab</a></div>
            <ul class="nav-links" id="navLinks">
                <li><a href="../index.html"><span class="i18n"><span data-lang="en">Home</span><span data-lang="zh">首页</span></span></a></li>
                <li><a href="../people.html" class="active"><span class="i18n"><span data-lang="en">People</span><span data-lang="zh">成员</span></span></a></li>
                <li><a href="../research.html"><span class="i18n"><span data-lang="en">Research</span><span data-lang="zh">研究</span></span></a></li>
                <li><a href="../publications.html"><span class="i18n"><span data-lang="en">Publications</span><span data-lang="zh">论文</span></span></a></li>
                <li><a href="../news.html"><span class="i18n"><span data-lang="en">News</span><span data-lang="zh">动态</span></span></a></li>
                <li><a href="../join.html"><span class="i18n"><span data-lang="en">Join Us</span><span data-lang="zh">加入我们</span></span></a></li>
            </ul>
            <button class="lang-toggle" id="langToggle" aria-label="Switch language / 切换语言"><span class="i18n"><span data-lang="en">中文</span><span data-lang="zh">EN</span></span></button>
            <button class="hamburger" id="hamburger" aria-label="切换菜单" aria-expanded="false"><span></span><span></span><span></span></button>
        </div>
    </nav>"""

FOOTER = """    <footer class="footer">
        <div class="container">
            <div class="footer-top">
                <div class="footer-brand"><img src="../images/logos/birdlab-logo.png" alt="BIRD Lab" class="footer-logo" /><small>SUSTech</small></div>
                <div class="footer-links">
                    <a href="../index.html"><span class="i18n"><span data-lang="en">Home</span><span data-lang="zh">首页</span></span></a>
                    <a href="../people.html"><span class="i18n"><span data-lang="en">People</span><span data-lang="zh">成员</span></span></a>
                    <a href="../research.html"><span class="i18n"><span data-lang="en">Research</span><span data-lang="zh">研究</span></span></a>
                    <a href="../publications.html"><span class="i18n"><span data-lang="en">Publications</span><span data-lang="zh">论文</span></span></a>
                    <a href="../news.html"><span class="i18n"><span data-lang="en">News</span><span data-lang="zh">动态</span></span></a>
                    <a href="../join.html"><span class="i18n"><span data-lang="en">Join Us</span><span data-lang="zh">加入我们</span></span></a>
                </div>
            </div>
            <div class="footer-bottom">
                <span>&copy; 2026 BIRD Lab, SUSTech. All rights reserved.</span>
                <div class="social">
                    <a href="#" id="qrLink" class="social-link"><span class="i18n"><span data-lang="en">Xiaohongshu</span><span data-lang="zh">小红书</span></span></a>
                    <a href="mailto:yuetq@sustech.edu.cn" class="social-link"><span class="i18n"><span data-lang="en">Email</span><span data-lang="zh">邮箱</span></span></a>
                </div>
            </div>
        </div>
    </footer>
    <!-- ===== 小红书二维码模态框 ===== -->
    <div class="qr-modal" id="qrModal">
        <div class="qr-modal-content">
            <img src="../images/social/xiaohongshu.jpg" alt="Xiaohongshu QR Code / 小红书二维码" />
        </div>
    </div>"""


def write_lf(path, text):
    """以 LF 换行写文件（Windows 下 text mode 会写成 CRLF，故显式指定）。"""
    with path.open("w", encoding="utf-8", newline="\n") as f:
        f.write(text)

def i18n(en, zh):
    return f'<span class="i18n"><span data-lang="en">{en}</span><span data-lang="zh">{zh}</span></span>'


def section(icon, title_en, title_zh, body):
    return f"""    <section class="section">
        <div class="container reveal">
            <h2><span class="sec-icon">{icon}</span> {i18n(title_en, title_zh)}</h2>
{body}
        </div>
    </section>"""


def build_page(m):
    is_pi = m["group"] == "pi"

    # 教育区块标题：PI 用「教育及工作经历」
    edu_en, edu_zh = ("Education &amp; Experience", "教育及工作经历") if is_pi else ("Education", "教育经历")

    parts = []
    parts.append(f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <link rel="icon" href="../images/logos/favicon.png" type="image/png" />
    <link rel="apple-touch-icon" href="../images/logos/favicon.png" />
    <title data-en="{m['name_en']} · BIRD Lab" data-zh="{m['name_zh']} · BIRD Lab">{m['name_en']} · BIRD Lab</title>
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
    <link href="https://fonts.googleapis.com/css2?family=Inter:opsz,wght@14..32,400;14..32,500;14..32,600;14..32,700&display=swap" rel="stylesheet" />
    <link rel="stylesheet" href="member-style.css" />""")
    if m.get("head_css"):
        parts.append(f"    <style>\n{m['head_css']}\n    </style>")
    parts.append("</head>\n<body>\n")
    parts.append(NAVBAR)
    parts.append(f"""
    <div class="breadcrumb">
        <div class="container">
            <a href="{m.get('back_link') or '../people.html'}"><span class="i18n"><span data-lang="en">← Back to People</span><span data-lang="zh">← 返回成员页</span></span></a>
        </div>
    </div>

    <header class="profile">
        <div class="container">
            <div class="profile-grid">
                <div class="profile-photo reveal"><img src="../images/people/{m['photo']}" alt="{m['name_en']} / {m['name_zh']}" /></div>
                <div class="profile-info reveal">
                    <h1>{m['name_en']} / {m['name_zh']}</h1>
                    <div class="role">{i18n(m['role_en'], m['role_zh'])}</div>
                    <div class="profile-meta">""")

    if m.get("email"):
        parts.append(f"""                        <div class="meta-item">📧 {i18n('Email:', '邮箱：')} <a href="mailto:{m['email']}">{m['email']}</a></div>""")
    if m.get("meta_label_en"):
        parts.append(f"""                        <div class="meta-item">🎓 {i18n(m['meta_label_en'], m['meta_label_zh'])} {i18n(m['meta_value_en'], m['meta_value_zh'])}</div>""")
    parts.append("""                    </div>""")
    if m.get("profile_extra_html"):
        parts.append(f"                    {m['profile_extra_html']}")
    parts.append("""                </div>
            </div>
        </div>
    </header>
""")

    # 个人简介（PI 用教师图标）
    about_icon = "🧑‍🏫" if is_pi else "🧑‍🎓"
    parts.append(section(about_icon, "About Me", "个人简介", f"""            <p>
                {i18n(m['bio_en'], m['bio_zh'])}
            </p>"""))
    parts.append("")

    # 研究方向
    if m.get("research_en") or m.get("research_zh"):
        parts.append(section("🔬", "Research Interests", "研究方向",
                             f"""            <p>{i18n(m['research_en'], m['research_zh'])}</p>"""))
        parts.append("")

    # 教育经历
    if m.get("education"):
        lis = "\n".join(f"                <li>{i18n(e['en'], e['zh'])}</li>" for e in m["education"])
        parts.append(section("🎓", edu_en, edu_zh, f"""            <ul>
{lis}
            </ul>"""))
        parts.append("")

    # 论文发表
    if m.get("publications"):
        items = []
        for p in m["publications"]:
            badge = ""
            if p.get("badge_en") or p.get("badge_zh"):
                badge = f"""
                    <span class="badge">{i18n(p['badge_en'], p['badge_zh'])}</span>"""
            items.append(f"""            <div class="pub-item">
                <div class="pub-title">
                    {i18n(p['title_en'], p['title_zh'])}{badge}
                </div>
                <div class="pub-venue">{p['venue']}</div>
            </div>""")
        parts.append(section("📄", "Publications", "论文发表", "\n".join(items)))
        parts.append("")

    parts.append(FOOTER)
    parts.append("""

    <script src="member-script.js"></script>
</body>
</html>
""")
    return "\n".join(parts) if False else "".join(
        (p if p.endswith("\n") or p == "" else p + "\n") for p in parts
    )


def build_grid(members):
    cards = []
    ordered = sorted(
        [m for m in members if m["group"] != "pi"],
        key=lambda m: (GROUP_ORDER.index(m["group"]) if m["group"] in GROUP_ORDER else 99,
                       members.index(m)),
    )
    for m in ordered:
        cards.append(f"""                <a href="members/{m['slug']}.html" class="member-card reveal">
                        <div class="avatar"><img src="images/people/{m['photo']}" alt="{m['name_en']} / {m['name_zh']}" /></div>
                        <div class="role">{i18n(m['role_en'], m['role_zh'])}</div>
                        <div class="name">{m['name_en']} / {m['name_zh']}</div>
                    </a>""")
    return "\n".join(cards)


def update_people(members, check):
    html = PEOPLE.read_text(encoding="utf-8")
    grid = build_grid(members)

    pattern = re.compile(r'<div class="member-grid">.*?\n(\s*)</div>', re.S)
    if not pattern.search(html):
        raise SystemExit("people.html 中找不到成员卡片区（member-grid）")
    new_html = pattern.sub(
        lambda mo: '<div class="member-grid">\n' + grid + '\n' + mo.group(1) + '</div>', html, count=1
    )

    if new_html == html:
        print("people.html         未变")
        return
    if check:
        print("people.html         将会更新")
        return
    write_lf(PEOPLE, new_html)
    print("people.html         已更新")


def main():
    check = "--check" in sys.argv
    members = json.loads(DATA.read_text(encoding="utf-8"))["members"]
    print(f"数据源：{len(members)} 位成员" + ("（--check：不写入）" if check else ""))

    changed = 0
    for m in members:
        path = ROOT / "members" / f"{m['slug']}.html"
        content = build_page(m)
        old = path.read_text(encoding="utf-8") if path.exists() else None
        old_bytes = path.read_bytes() if path.exists() else b""
        if old == content and b"\r\n" not in old_bytes:
            print(f"  {m['slug']:20s} 未变")
            continue
        changed += 1
        state = "新建" if old is None else "更新"
        if check:
            print(f"  {m['slug']:20s} 将会{state}")
        else:
            write_lf(path, content)
            print(f"  {m['slug']:20s} {state}")

    update_people(members, check)
    print(f"\n共 {changed} 个成员页需要变更")


if __name__ == "__main__":
    main()
