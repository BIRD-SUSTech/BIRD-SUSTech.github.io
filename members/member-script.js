(function() {
    'use strict';

    // 导航栏滚动磨砂
    const navbar = document.getElementById('navbar');
    window.addEventListener('scroll', function() {
        navbar.classList.toggle('scrolled', window.pageYOffset > 20);
    }, { passive: true });

    // 汉堡菜单
    const hamburger = document.getElementById('hamburger');
    const navLinks = document.getElementById('navLinks');
    hamburger.addEventListener('click', function() {
        const isOpen = navLinks.classList.toggle('open');
        hamburger.classList.toggle('active');
        hamburger.setAttribute('aria-expanded', isOpen);
    });
    navLinks.querySelectorAll('a').forEach(function(link) {
        link.addEventListener('click', function() {
            navLinks.classList.remove('open');
            hamburger.classList.remove('active');
            hamburger.setAttribute('aria-expanded', 'false');
        });
    });

    // Intersection Observer: 滚动淡入上浮
    const revealElements = document.querySelectorAll('.reveal');
    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(function(entry) {
            if (entry.isIntersecting) entry.target.classList.add('visible');
        });
    }, { threshold: 0.12, rootMargin: '0px 0px -40px 0px' });
    revealElements.forEach(function(el) { observer.observe(el); });

    // 语言切换（默认英文，localStorage 记忆）
    const KEY = 'birdlab-lang';
    const htmlEl = document.documentElement;
    let lang = 'en';
    try { lang = (localStorage.getItem(KEY) === 'zh') ? 'zh' : 'en'; } catch (e) {}
    htmlEl.classList.toggle('lang-zh', lang === 'zh');
    const titleEl = document.querySelector('title');
    function syncTitle() {
        if (titleEl && titleEl.getAttribute('data-en') && titleEl.getAttribute('data-zh')) {
            document.title = (lang === 'zh') ? titleEl.getAttribute('data-zh') : titleEl.getAttribute('data-en');
        }
    }
    syncTitle();
    const langBtn = document.getElementById('langToggle');
    if (langBtn) {
        langBtn.addEventListener('click', function() {
            lang = (lang === 'zh') ? 'en' : 'zh';
            try { localStorage.setItem(KEY, lang); } catch (e) {}
            htmlEl.classList.toggle('lang-zh', lang === 'zh');
            syncTitle();
        });
    }

    // 小红书二维码模态框
    const qrModal = document.getElementById('qrModal');
    const qrLink = document.getElementById('qrLink');
    if (qrModal && qrLink) {
        qrLink.addEventListener('click', function(e) {
            e.preventDefault();
            qrModal.classList.add('open');
        });
        qrModal.addEventListener('click', function(e) {
            if (e.target === qrModal) { qrModal.classList.remove('open'); }
        });
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') { qrModal.classList.remove('open'); }
        });
    }
})();
