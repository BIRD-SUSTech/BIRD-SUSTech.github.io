#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
全站公共区块（导航栏 / 页脚 / 二维码弹窗）的唯一模板。

所有页面（主页面 + 成员页）的这三块内容都由本模块生成：
  - 主页面：tools/build_chrome.py
  - 成员页：tools/build_members.py

修改导航项、页脚链接、页脚文案时，只改本文件，然后跑上面两个生成器。
"""

# (key, href, en, zh) —— 导航与页脚共用同一份顺序
NAV_ITEMS = [
    ("home", "index.html", "Home", "首页"),
    ("people", "people.html", "People", "成员"),
    ("research", "research.html", "Research", "研究"),
    ("publications", "publications.html", "Publications", "论文"),
    ("news", "news.html", "News", "动态"),
    ("join", "join.html", "Join Us", "加入我们"),
]

COPYRIGHT = "&copy; 2026 BIRD Lab, SUSTech. All rights reserved."
FOOTER_BRAND = ('<img src="{p}images/logos/birdlab-logo.png" alt="BIRD Lab" '
                'class="footer-logo" /><small>SUSTech · Bioinspired Intelligent Robotic Design Lab</small>')
CONTACT_EMAIL = "yuetq@sustech.edu.cn"


def i18n(en, zh):
    return f'<span class="i18n"><span data-lang="en">{en}</span><span data-lang="zh">{zh}</span></span>'


def navbar(active, prefix=""):
    """active: home/people/research/publications/news/join；prefix: 成员页用 '../'"""
    items = []
    for key, href, en, zh in NAV_ITEMS:
        cls = ' class="active"' if key == active else ""
        items.append(f'                <li><a href="{prefix}{href}"{cls}>{i18n(en, zh)}</a></li>')
    lis = "\n".join(items)
    return f"""    <nav class="navbar" id="navbar" role="navigation" aria-label="主导航">
        <div class="container">
            <div class="navbar-brand"><a href="{prefix}index.html" class="navbar-brand-link" aria-label="BIRD Lab Home"><img src="{prefix}images/logos/sustech-logo.png" alt="SUSTech" class="navbar-logo" /><span class="logo-text">BIRD</span> Lab</a></div>
            <ul class="nav-links" id="navLinks">
{lis}
            </ul>
            <button class="lang-toggle" id="langToggle" aria-label="Switch language / 切换语言">{i18n('中文', 'EN')}</button>
            <button class="hamburger" id="hamburger" aria-label="切换菜单" aria-expanded="false"><span></span><span></span><span></span></button>
        </div>
    </nav>"""


def footer(prefix=""):
    links = "\n".join(
        f'                    <a href="{prefix}{href}">{i18n(en, zh)}</a>' for _, href, en, zh in NAV_ITEMS
    )
    return f"""    <footer class="footer">
        <div class="container">
            <div class="footer-top">
                <div class="footer-brand">{FOOTER_BRAND.format(p=prefix)}</div>
                <div class="footer-links">
{links}
                </div>
            </div>
            <div class="footer-bottom">
                <span>{COPYRIGHT}</span>
                <div class="social">
                    <a href="#" id="qrLink" class="social-link">{i18n('Xiaohongshu', '小红书')}</a>
                    <a href="mailto:{CONTACT_EMAIL}" class="social-link">{i18n('Email', '邮箱')}</a>
                </div>
            </div>
        </div>
    </footer>"""


def qr_modal(prefix=""):
    return f"""    <!-- ===== 小红书二维码模态框 ===== -->
    <div class="qr-modal" id="qrModal">
        <div class="qr-modal-content">
            <img src="{prefix}images/social/xiaohongshu.jpg" alt="Xiaohongshu QR Code / 小红书二维码" />
        </div>
    </div>"""
