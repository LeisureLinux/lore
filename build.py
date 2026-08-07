import json
#!/usr/bin/env python3
"""
FreeLAMP.com 静态站点构建脚本
从 articles/ 目录读取 Markdown 文件，生成 docs/ 目录的 HTML 页面
包含 SEO/GEO 优化：JSON-LD 结构化数据、Open Graph、Canonical URL、Sitemap、Robots.txt
"""

import os
import re
import json
import yaml
from urllib.parse import quote
from pathlib import Path
from datetime import datetime

LORE_DIR = Path(__file__).parent
ARTICLES_DIR = LORE_DIR / "articles"
DOCS_DIR = LORE_DIR / "docs"

# 站点基础配置（SEO 用）
SITE_URL = "https://freelamp.com"
SITE_NAME = "FreeLAMP.com"
SITE_DESCRIPTION = "Linux 底层机制、DevSecOps 安全加固与基础架构深度技术知识库"
SITE_AUTHOR = "LeisureLinux"

# ============================================================
# HTML 模板 — 首页（含 SEO meta）
# ============================================================
INDEX_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>FreeLAMP.com — Linux 底层机制与 DevSecOps 深度技术知识库</title>
  <meta name="description" content="{site_description}。涵盖 Linux 内核调优、TLS/PKI 信任链、网络协议安全、CVE 漏洞分析、DevOps 工具链。">
  <meta name="keywords" content="Linux, 内核, DevSecOps, TLS, PKI, 网络安全, CVE, eBPF, systemd, SRE, 基础架构, DevOps">
  <meta name="author" content="{site_author}">
  <link rel="canonical" href="{canonical_url}">
  {rel_prev}{rel_next}
  <link rel="icon" type="image/x-icon" href="/favicon.ico">
  <link rel="alternate" type="application/rss+xml" title="FreeLAMP.com RSS 订阅" href="/rss.xml">

  <!-- Open Graph -->
  <meta property="og:type" content="website">
  <meta property="og:title" content="FreeLAMP.com — Linux 底层机制与 DevSecOps 深度技术知识库">
  <meta property="og:description" content="{site_description}">
  <meta property="og:url" content="{site_url}/">
  <meta property="og:site_name" content="{site_name}">
  <meta property="og:locale" content="zh_CN">

  <!-- Twitter Card -->
  <meta name="twitter:card" content="summary">
  <meta name="twitter:title" content="FreeLAMP.com — 技术传说">
  <meta name="twitter:description" content="{site_description}">
  <meta name="twitter:site" content="@LeisureLinux">
  <meta name="twitter:creator" content="@LeisureLinux">

  <!-- JSON-LD 结构化数据：WebSite + SearchAction -->
  <script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@type": "WebSite",
    "name": "{site_name}",
    "url": "{site_url}/",
    "description": "{site_description}",
    "potentialAction": {{
      "@type": "SearchAction",
      "target": "{site_url}/?q={{search_term_string}}",
      "query-input": "required name=search_term_string"
    }}
  }}
  </script>

  <!-- JSON-LD：ItemList（文章列表） -->
  <script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@type": "ItemList",
    "name": "FreeLAMP.com 技术文章",
    "itemListElement": {item_list_json}
  }}
  </script>

  <style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif;
      background: #F9FAFB; color: #374151; line-height: 1.75;
    }}
    .container {{ max-width: 720px; margin: 0 auto; padding: 0 24px; }}
    
    header {{
      background: linear-gradient(135deg, #059669, #10B981);
      padding: 48px 0 40px; color: #fff; margin-bottom: 40px;
    }}
    header h1 {{ font-size: 32px; font-weight: 900; letter-spacing: -1px; margin-bottom: 8px; }}
    header p {{ font-size: 15px; opacity: 0.85; letter-spacing: 0.5px; }}
    header .tags {{ margin-top: 16px; display: flex; gap: 6px; flex-wrap: wrap; }}
    header .tags span {{
      background: rgba(255,255,255,0.2); padding: 2px 10px; border-radius: 12px;
      font-size: 12px; font-weight: 600;
    }}

    header .projects {{
      margin-top: 20px; display: flex; gap: 10px; flex-wrap: wrap;
    }}
    header .project-btn {{
      display: flex; flex-direction: column; gap: 2px;
      background: rgba(255,255,255,0.14); border: 1px solid rgba(255,255,255,0.35);
      color: #fff; text-decoration: none; border-radius: 10px;
      padding: 9px 14px; transition: background .15s, transform .15s;
      min-width: 0;
    }}
    header .project-btn:hover {{
      background: rgba(255,255,255,0.28); transform: translateY(-1px);
    }}
    header .project-btn b {{
      font-size: 13px; font-weight: 800; letter-spacing: 0.3px;
    }}
    header .project-btn span {{
      font-size: 11px; opacity: 0.85; font-weight: 500;
    }}
    
    .article-list {{ list-style: none; }}
    .article-item {{
      background: #fff; border-radius: 12px; padding: 24px 28px;
      margin-bottom: 16px; border: 1px solid #E5E7EB;
      transition: box-shadow 0.2s, transform 0.2s;
    }}
    .article-item:hover {{
      box-shadow: 0 4px 20px rgba(5,150,105,0.12);
      transform: translateY(-2px);
    }}
    .article-item a {{ text-decoration: none; color: inherit; }}
    .article-date {{
      font-size: 12px; color: #9CA3AF; font-weight: 600;
      letter-spacing: 1px; margin-bottom: 8px;
    }}
    .article-title {{
      font-size: 18px; font-weight: 800; color: #111827;
      margin-bottom: 8px; line-height: 1.4;
    }}
    .article-summary {{
      font-size: 14px; color: #6B7280; line-height: 1.7;
    }}
    .article-tags {{ margin-top: 12px; display: flex; gap: 6px; flex-wrap: wrap; }}
    .article-tags a {{
      background: #ECFDF5; color: #059669; padding: 2px 8px;
      border-radius: 4px; font-size: 11px; font-weight: 600; text-decoration: none;
    }}
    .article-tags a:hover {{ background: #D1FAE5; }}
    .article-meta {{
      margin-top: 14px; padding-top: 14px;
      border-top: 1px dashed #E5E7EB;
      display: flex; align-items: center; justify-content: flex-end;
    }}
    .comment-link {{
      font-size: 12px; font-weight: 700; color: #059669;
      text-decoration: none; background: #ECFDF5;
      padding: 5px 12px; border-radius: 999px;
      transition: background .15s, transform .15s;
    }}
    .comment-link:hover {{ background: #D1FAE5; transform: translateY(-1px); }}

    .pagination {{
      text-align: center; margin: 8px 0 16px;
    }}
    .load-more {{
      display: inline-block; background: #059669; color: #fff;
      border: none; padding: 12px 32px; border-radius: 999px;
      font-size: 14px; font-weight: 700; cursor: pointer;
      transition: background .15s, transform .15s; margin-bottom: 14px;
    }}
    .load-more:hover {{ background: #047857; transform: translateY(-1px); }}
    .load-more:disabled {{ opacity: 0.6; cursor: default; transform: none; }}
    .page-links {{ display: flex; justify-content: center; align-items: center; gap: 8px; flex-wrap: wrap; }}
    .page-links .pg {{
      color: #059669; text-decoration: none; font-weight: 600;
      padding: 6px 12px; border: 1px solid #D1FAE5; border-radius: 8px;
      background: #fff; font-size: 13px; min-width: 32px; text-align: center;
    }}
    .page-links .pg:hover {{ background: #ECFDF5; }}
    .page-links .pg.current {{
      background: #059669; color: #fff; border-color: #059669; cursor: default;
    }}
    
    footer {{
      text-align: center; padding: 32px 0; color: #9CA3AF;
      font-size: 13px; border-top: 1px solid #E5E7EB; margin-top: 40px;
    }}
    footer a {{ color: #059669; text-decoration: none; }}
  </style>
</head>
<body>
  <header>
    <div class="container">
      <h1><a href="/" style="color:#fff; text-decoration:none;">FreeLAMP.com 像风一样自由</a></h1>
      <p>禅道须在生活中修，在日常言语、形式里面契合、印证</p>
      <div class="projects">
        <a class="project-btn" href="https://github.com/LeisureLinux/ghdeb" target="_blank" rel="noopener"><b>ghdeb</b><span>从 GitHub 安装 deb 包</span></a>
        <a class="project-btn" href="https://github.com/LeisureLinux/unbound-dashboard" target="_blank" rel="noopener"><b>unbound-dashboard</b><span>轻量的 unbound DNS 查询日志仪表板</span></a>
        <a class="project-btn" href="https://github.com/LeisureLinux/adhole" target="_blank" rel="noopener"><b>adhole</b><span>用自建 DNS 阻拦广告</span></a>
        <a class="project-btn" href="https://read.freelamp.com/" target="_blank" rel="noopener"><b>Readings</b><span>我的阅读人生</span></a>
      </div>
      <div class="tags">
        <span>Linux</span><span>内核</span><span>安全</span><span>开源</span>
      </div>
    </div>
  </header>

  <main class="container">
    <ul class="article-list">
{articles}
    </ul>
    {pager_html}
  </main>

  <footer>
    <div class="container">
      <p>© 2026 LeisureLinux · <a href="https://github.com/LeisureLinux/lore">GitHub</a> · <a href="/about-freelamp.html">关于 FreeLAMP</a> · <a href="/rss.xml">RSS 订阅</a></p>
      <p style="margin-top: 8px; font-size: 12px;">本文以 <a href="https://creativecommons.org/licenses/by-sa/4.0/">CC BY-SA 4.0</a> 协议开源</p>
    </div>
  </footer>

  <script>
    // 动态拉取 GitHub Discussions 评论数，显示到首页"参与讨论"按钮
    (function () {{
      var KEY = 'freelamp_discussions';
      var map = {{}};
      try {{ map = JSON.parse(localStorage.getItem(KEY) || '{{}}') || {{}}; }} catch (e) {{}}

      function norm(p) {{ return String(p || '').replace(/^\/+|\/+$/g, ''); }}

      function apply() {{
        document.querySelectorAll('.comment-link').forEach(function (btn) {{
          var path = norm(btn.getAttribute('data-path'));
          var n = map[path];
          if (typeof n === 'number' && n > 0) {{
            btn.textContent = '💬 ' + n;
            btn.title = '已有 ' + n + ' 条点评，点击参与讨论';
          }}
        }});
      }}
      window.__applyComments = apply;
      apply();

      fetch('https://api.github.com/repos/LeisureLinux/lore/discussions?per_page=100')
        .then(function (r) {{ if (!r.ok) throw new Error(r.status); return r.json(); }})
        .then(function (list) {{
          if (!Array.isArray(list)) return;
          map = {{}};
          list.forEach(function (d) {{
            if (d && typeof d.title === 'string' && typeof d.comments === 'number') {{
              map[norm(d.title)] = d.comments;
            }}
          }});
          try {{ localStorage.setItem(KEY, JSON.stringify(map)); }} catch (e) {{}}
          apply();
        }})
        .catch(function () {{}});
    }})();
  <script>
    // 「加载更多」渐进增强：抓取下一页分页页的 .article-item 追加到列表
    (function () {{
      var btn = document.getElementById('load-more');
      if (!btn) return;
      var list = document.querySelector('.article-list');
      btn.addEventListener('click', function () {{
        var next = btn.getAttribute('data-next');
        if (!next) {{ btn.remove(); return; }}
        btn.disabled = true; btn.textContent = '加载中…';
        fetch(next)
          .then(function (r) {{ return r.text(); }})
          .then(function (html) {{
            var doc = new DOMParser().parseFromString(html, 'text/html');
            doc.querySelectorAll('.article-item').forEach(function (li) {{ list.appendChild(li); }});
            var nb = doc.getElementById('load-more');
            var nn = nb ? nb.getAttribute('data-next') : '';
            if (nn) {{ btn.setAttribute('data-next', nn); btn.textContent = '加载更多'; btn.disabled = false; }}
            else {{ btn.remove(); }}
            if (window.__applyComments) window.__applyComments();
          }})
          .catch(function () {{ btn.textContent = '加载失败，点击重试'; btn.disabled = false; }});
      }});
    }})();
  </script>
</body>
</html>"""


# ============================================================
# HTML 模板 — 文章页（含完整 SEO/GEO 结构化数据）
# ============================================================
ARTICLE_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title} — FreeLAMP.com</title>
  <meta name="description" content="{meta_description}">
  <meta name="keywords" content="{meta_keywords}">
  <meta name="author" content="{author}">
  <meta name="date" content="{date_iso}">
  <link rel="canonical" href="{canonical_url}">
  <link rel="icon" type="image/x-icon" href="/favicon.ico">

  <link rel="alternate" type="application/rss+xml" title="FreeLAMP.com RSS 订阅" href="/rss.xml">
  <!-- Open Graph：文章页 -->
  <meta property="og:type" content="article">
  <meta property="og:title" content="{title}">
  <meta property="og:description" content="{meta_description}">
  <meta property="og:url" content="{canonical_url}">
  <meta property="og:site_name" content="{site_name}">
  <meta property="og:locale" content="zh_CN">
  <meta property="article:published_time" content="{date_iso}">
  <meta property="article:author" content="{author}">
  <meta property="article:section" content="{article_section}">
  {og_tags}

  <!-- Twitter Card -->
  <meta name="twitter:card" content="summary">
  <meta name="twitter:title" content="{title}">
  <meta name="twitter:description" content="{meta_description}">
  <meta name="twitter:site" content="@LeisureLinux">
  <meta name="twitter:creator" content="@LeisureLinux">

  <!-- JSON-LD：TechArticle 结构化数据（SEO 核心） -->
  <script type="application/ld+json">
  {json_ld}
  </script>

  <!-- JSON-LD：BreadcrumbList 面包屑 -->
  <script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    "itemListElement": [
      {{
        "@type": "ListItem",
        "position": 1,
        "name": "FreeLAMP.com",
        "item": "{site_url}/"
      }},
      {{
        "@type": "ListItem",
        "position": 2,
        "name": "{title}",
        "item": "{canonical_url}"
      }}
    ]
  }}
  </script>

  <style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif;
      background: #F9FAFB; color: #374151; line-height: 1.75;
    }}
    .container {{ max-width: 720px; margin: 0 auto; padding: 0 24px; }}
    
    nav {{
      background: #fff; border-bottom: 1px solid #E5E7EB;
      padding: 12px 0; position: sticky; top: 0; z-index: 10;
    }}
    nav .container {{ display: flex; align-items: center; justify-content: space-between; }}
    nav a {{ color: #059669; text-decoration: none; font-weight: 600; font-size: 14px; }}
    nav .brand {{ font-weight: 800; color: #111827; font-size: 15px; text-decoration: none; }}
    
    .post-header {{ padding: 48px 0 32px; border-bottom: 1px solid #E5E7EB; margin-bottom: 32px; }}
    .post-date {{ font-size: 13px; color: #9CA3AF; font-weight: 600; letter-spacing: 1px; margin-bottom: 12px; }}
    .post-title {{ font-size: 28px; font-weight: 900; color: #111827; line-height: 1.3; letter-spacing: -0.5px; margin-bottom: 16px; }}
    .post-tags {{ display: flex; gap: 6px; flex-wrap: wrap; }}
    .post-tags a {{
      background: #ECFDF5; color: #059669; padding: 3px 10px;
      border-radius: 4px; font-size: 12px; font-weight: 600; text-decoration: none;
    }}
    .post-tags a:hover {{ background: #D1FAE5; }}
    
    .post-content {{ padding-bottom: 48px; }}
    .post-content h2 {{
      font-size: 22px; font-weight: 800; color: #111827;
      margin: 40px 0 16px; padding-bottom: 8px;
      border-bottom: 2px solid #059669;
    }}
    .post-content h3 {{
      font-size: 17px; font-weight: 700; color: #111827;
      margin: 28px 0 12px;
    }}
    .post-content h4 {{
      font-size: 15px; font-weight: 700; color: #374151;
      margin: 20px 0 10px;
    }}
    .post-content p {{ margin-bottom: 16px; font-size: 15px; line-height: 1.9; }}
    .post-content ul, .post-content ol {{ margin: 0 0 16px 24px; }}
    .post-content li {{ margin-bottom: 8px; font-size: 15px; line-height: 1.8; }}
    .post-content strong {{ color: #059669; }}
    .post-content code {{
      background: #F3F4F6; color: #1F2937; padding: 2px 6px;
      border-radius: 4px; font-size: 13px; font-family: 'SF Mono', Consolas, Monaco, monospace;
    }}
    .post-content pre {{
      background: #1E293B; color: #E2E8F0; padding: 16px 20px;
      border-radius: 8px; overflow-x: auto; margin-bottom: 20px;
      font-size: 13px; line-height: 1.6;
    }}
    .post-content pre code {{
      background: none; color: inherit; padding: 0; font-size: inherit;
    }}
    .post-content table {{
      width: 100%; border-collapse: collapse; margin-bottom: 20px;
      font-size: 13px;
    }}
    .post-content th {{
      background: #059669; color: #fff; padding: 10px 12px;
      text-align: left; font-weight: 700;
    }}
    .post-content td {{
      padding: 8px 12px; border-bottom: 1px solid #E5E7EB;
    }}
    .post-content tr:nth-child(even) td {{ background: #F9FAFB; }}
    .post-content blockquote {{
      border-left: 4px solid #059669; background: #ECFDF5;
      padding: 12px 20px; margin: 0 0 20px; border-radius: 0 8px 8px 0;
    }}
    .post-content hr {{ border: none; border-top: 1px solid #E5E7EB; margin: 32px 0; }}
    
    .share-bar {{
      display: flex; flex-wrap: wrap; align-items: center; gap: 14px;
      padding: 22px 0 26px; margin-top: 8px;
      border-top: 1px dashed #E5E7EB;
    }}
    .share-btn {{
      display: inline-flex; align-items: center; justify-content: center;
      width: 44px; height: 44px; border-radius: 50%;
      border: none; cursor: pointer; padding: 0;
      color: #fff; transition: transform .15s ease, box-shadow .15s ease;
      box-shadow: 0 2px 6px rgba(0,0,0,.14);
    }}
    .share-btn:hover {{ transform: translateY(-3px); box-shadow: 0 6px 16px rgba(0,0,0,.20); }}
    .share-btn:active {{ transform: translateY(-1px); }}
    .share-btn svg {{ width: 24px; height: 24px; fill: #fff; }}
    .ico-wx {{ background: #07C160; }}
    .ico-weibo {{ background: #E6162D; }}
    .ico-x {{ background: #000; }}

    .post-comments {{
      margin-top: 40px; padding: 28px 28px 40px;
      border: 1px solid #D1FAE5; border-radius: 16px;
      background: #FFFFFF; box-shadow: 0 4px 24px rgba(5,150,105,0.08);
    }}
    .comments-head {{
      display: flex; align-items: center; gap: 10px; margin-bottom: 6px;
    }}
    .comments-head .comments-badge {{
      font-size: 12px; font-weight: 800; color: #fff; background: #059669;
      padding: 3px 10px; border-radius: 999px; letter-spacing: .5px;
    }}
    .comments-title {{
      font-size: 20px; font-weight: 900; color: #059669;
      margin: 0;
    }}
    .comments-sub {{
      font-size: 13px; color: #6B7280; margin-bottom: 20px;
      padding-bottom: 16px; border-bottom: 1px solid #E5E7EB;
    }}
    .giscus {{ min-height: 320px; }}

    footer {{
      text-align: center; padding: 32px 0; color: #9CA3AF;
      font-size: 13px; border-top: 1px solid #E5E7EB;
    }}
    footer a {{ color: #059669; text-decoration: none; }}
  </style>
</head>
<body>
  <nav>
    <div class="container">
      <a class="brand" href="/">FreeLAMP.com 像风一样自由</a>
    </div>
  </nav>

  <main class="container">
    <article itemscope itemtype="https://schema.org/TechArticle">
      <div class="post-header">
        <div class="post-date" itemprop="datePublished" content="{date_iso}">{date}</div>
        <h1 class="post-title" itemprop="headline">{title}</h1>
        <div class="post-tags">{tags}</div>
        <meta itemprop="author" content="{author}">
        <meta itemprop="license" content="https://creativecommons.org/licenses/by-sa/4.0/">
      </div>

      <div class="post-content" itemprop="articleBody">
{content}
      </div>
    </article>

    <!-- 社交媒体分享栏：文章结尾、评论区上方（品牌小图标） -->
    <div class="share-bar">
      <button type="button" class="share-btn ico-wx" onclick="shareWechat()" title="微信扫码分享" aria-label="分享到微信">
        <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path d="M8.691 2.188C3.891 2.188 0 5.476 0 9.53c0 2.212 1.17 4.203 3.002 5.55a.59.59 0 0 1 .213.665l-.39 1.48c-.019.07-.048.141-.048.213 0 .163.13.295.29.295a.326.326 0 0 0 .167-.054l1.903-1.114a.864.864 0 0 1 .718-.098 11.223 11.223 0 0 0 2.836.379c.276 0 .543-.027.811-.05-.03-.21-.049-.424-.049-.642 0-3.893 3.567-7.05 7.964-7.05.158 0 .313.012.469.02C17.367 5.119 13.484 2.188 8.691 2.188zm-2.51 4.925c.653 0 1.182.523 1.182 1.168 0 .645-.529 1.168-1.182 1.168-.653 0-1.182-.523-1.182-1.168 0-.645.529-1.168 1.182-1.168zm5.925 0c.653 0 1.182.523 1.182 1.168 0 .645-.529 1.168-1.182 1.168-.653 0-1.182-.523-1.182-1.168 0-.645.529-1.168 1.182-1.168zM20.985 12.242c0 3.542-3.319 6.414-7.414 6.414-.72 0-1.416-.09-2.064-.256a.63.63 0 0 0-.524.07l-1.386.81a.28.28 0 0 1-.122.04.215.215 0 0 1-.212-.215c0-.052.021-.104.035-.154l.285-1.079a.43.43 0 0 0-.156-.485C8.082 16.811 7.1 15.548 7.1 14.057c0-3.542 3.319-6.414 7.414-6.414 4.095 0 6.471 2.872 6.471 6.414zm-2.894-.646c-.476 0-.862-.382-.862-.852 0-.47.386-.852.862-.852.476 0 .862.382.862.852 0 .47-.386.852-.862.852zm-3.517 0c-.476 0-.862-.382-.862-.852 0-.47.386-.852.862-.852.476 0 .862.382.862.852 0 .47-.386.852-.862.852z"/></svg>
      </button>
      <button type="button" class="share-btn ico-weibo" onclick="openShare('https://service.weibo.com/share/share.php?url='+encodeURIComponent(SHARE.url)+'&title='+encodeURIComponent(SHARE.title))" title="分享到微博" aria-label="分享到微博">
        <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path d="M10.996 1.885c-4.944.047-9.071 3.731-9.993 8.484-.984 5.069 3.143 9.193 8.787 9.193 4.832 0 8.752-3.375 9.755-7.884.505-2.274.05-4.487-1.537-6.033-1.37-1.336-3.36-1.947-5.506-1.761h-1.506zM9.173 16.142c-3.227.013-5.84-1.826-5.84-4.107 0-2.281 2.614-4.119 5.84-4.107 3.227.011 5.84 1.849 5.84 4.13 0 2.281-2.613 4.071-5.84 4.084zm0-1.554c2.42.011 4.38-1.14 4.38-2.546 0-1.406-1.96-2.548-4.38-2.548-2.42 0-4.38 1.142-4.38 2.548 0 1.406 1.96 2.535 4.38 2.546zm0-3.826c1.091 0 1.975.573 1.975 1.28s-.884 1.28-1.975 1.28-1.975-.573-1.975-1.28.884-1.28 1.975-1.28zm4.631-5.902c-1.396-.527-1.093-2.264.411-2.348 1.504-.084 2.331 1.546.913 2.213-.354.166-.763.225-1.324.135zm-1.324 1.544c2.279.15 3.536 1.782 2.829 3.549-.707 1.768-3.195 2.484-5.475 2.335-2.279-.15-3.536-1.782-2.829-3.549.708-1.768 3.196-2.484 5.475-2.335zM14.972 3.394c.694.055 1.224.223 1.59.504.366.28.502.651.407 1.112-.095.461-.489.648-.783.701-.295.054-.747-.014-1.356-.203-.609-.188-.799-.642-.569-1.361.23-.72.447-1.065.711-1.002zm-3.977.238c-2.273.022-4.576 1.112-6.205 2.827-1.319 1.388-2.102 3.085-2.178 4.88-.077 1.795.585 3.617 1.738 5.124 1.153 1.506 2.841 2.511 4.709 2.858 1.868.348 3.876-.042 5.533-1.065 1.656-1.022 2.884-2.559 3.421-4.369.537-1.81.417-3.791-.211-5.344-.629-1.554-1.846-2.832-3.476-3.602-1.233-.583-2.549-.847-3.834-.841z"/></svg>
      </button>
      <button type="button" class="share-btn ico-x" onclick="openShare('https://twitter.com/intent/tweet?text='+encodeURIComponent(SHARE.title+' '+SHARE.url))" title="分享到 X" aria-label="分享到 X">
        <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path d="M18.901 1.153h3.68l-8.04 9.19L24 22.846h-7.406l-5.8-7.584-6.638 7.584H.474l8.6-9.83L0 1.154h7.594l5.243 6.932ZM17.61 20.644h2.039L6.486 3.24H4.298Z"/></svg>
      </button>
    </div>

    <!-- giscus 点评（GitHub Discussions 驱动） -->
    <section class="post-comments" id="comments">
      <div class="comments-head">
        <h2 class="comments-title">点评与讨论</h2>
        <span class="comments-badge">GITHUB 账号登录</span>
      </div>
      <p class="comments-sub">有疑问、有补充、有不同看法？欢迎留下你的点评，一起把技术聊透。👇</p>
      <div class="giscus" id="giscus">
        <script src="https://giscus.app/client.js"
          data-repo="LeisureLinux/lore"
          data-repo-id="R_kgDOTpxbbg"
          data-category="General"
          data-category-id="DIC_kwDOTpxbbs4DCp0C"
          data-mapping="pathname"
          data-strict="0"
          data-reactions-enabled="1"
          data-emit-metadata="0"
          data-input-position="top"
          data-theme="preferred_color_scheme"
          data-lang="zh-CN"
          data-loading="lazy"
          crossorigin="anonymous"
          async>
        </script>
      </div>
    </section>
  </main>

  <footer>
    <div class="container">
      <p>© 2026 LeisureLinux · <a href="https://github.com/LeisureLinux/lore">GitHub</a> · <a href="/about-freelamp.html">关于 FreeLAMP</a> · <a href="/rss.xml">RSS 订阅</a></p>
      <p style="margin-top: 8px; font-size: 12px;">本文以 <a href="https://creativecommons.org/licenses/by-sa/4.0/">CC BY-SA 4.0</a> 协议开源</p>
    </div>
  </footer>

  <script>
    var SHARE = {{
      url: {share_url},
      title: {share_title}
    }};
    function openShare(u) {{ window.open(u, '_blank', 'noopener,width=680,height=560'); }}
    function shareWechat() {{ window.open('https://api.qrserver.com/v1/create-qr-code/?size=320x320&margin=10&data=' + encodeURIComponent(SHARE.url), 'wechat_qr', 'width=380,height=420,noopener'); }}
  </script>
</body>
</html>"""


TAG_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>#{tag} — FreeLAMP.com 像风一样自由</title>
  <link rel="alternate" type="application/rss+xml" title="FreeLAMP.com RSS 订阅" href="/rss.xml">
  <meta name="description" content="标签「{tag}」下的全部 FreeLAMP.com 技术文章">
  <link rel="canonical" href="{SITE_URL}{tag_url}">
  <style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif; background: #fff; color: #1F2937; line-height: 1.6; }}
    .container {{ max-width: 860px; margin: 0 auto; padding: 0 20px; }}
    nav {{ background: #fff; border-bottom: 1px solid #E5E7EB; padding: 12px 0; position: sticky; top: 0; z-index: 10; }}
    nav .container {{ display: flex; align-items: center; }}
    nav .brand {{ font-weight: 800; color: #111827; font-size: 15px; text-decoration: none; }}
    .tag-header {{ padding: 40px 0 24px; border-bottom: 1px solid #E5E7EB; margin-bottom: 24px; }}
    .tag-header h1 {{ font-size: 26px; font-weight: 900; color: #111827; }}
    .tag-header p {{ color: #6B7280; font-size: 14px; margin-top: 8px; }}
    .article-list {{ list-style: none; }}
    .article-item {{ border-bottom: 1px solid #F3F4F6; padding: 16px 0; }}
    .article-item a {{ text-decoration: none; color: inherit; display: block; }}
    .article-date {{ font-size: 12px; color: #9CA3AF; font-weight: 600; margin-bottom: 4px; }}
    .article-title {{ font-size: 17px; font-weight: 800; color: #111827; }}
    .article-summary {{ font-size: 14px; color: #6B7280; margin-top: 6px; line-height: 1.7; }}
    footer {{ text-align: center; padding: 32px 0; color: #9CA3AF; font-size: 13px; border-top: 1px solid #E5E7EB; margin-top: 40px; }}
    footer a {{ color: #059669; text-decoration: none; }}
  </style>
</head>
<body>
  <nav>
    <div class="container">
      <a class="brand" href="/">FreeLAMP.com 像风一样自由</a>
    </div>
  </nav>

  <main class="container">
    <div class="tag-header">
      <h1># {tag}</h1>
      <p>共 {count} 篇文章</p>
    </div>
    <ul class="article-list">
{articles}
    </ul>
  </main>

  <footer>
    <div class="container">
      <p>© 2026 LeisureLinux · <a href="https://github.com/LeisureLinux/lore">GitHub</a> · <a href="/about-freelamp.html">关于 FreeLAMP</a> · <a href="/rss.xml">RSS 订阅</a></p>
      <p style="margin-top: 8px; font-size: 12px;">本文以 <a href="https://creativecommons.org/licenses/by-sa/4.0/">CC BY-SA 4.0</a> 协议开源</p>
    </div>
  </footer>
</body>
</html>"""



def _convert_tables(html):
    """把 GFM 风格 Markdown 表格（连续以 | 开头的行）转换为 HTML <table>"""
    def _sep(ln):
        return bool(re.match(r'^\|?[\s:|-]+\|?$', ln)) and '-' in ln

    def _cells(ln):
        ln = ln.strip()
        if ln.startswith('|'): ln = ln[1:]
        if ln.endswith('|'): ln = ln[:-1]
        return [c.strip() for c in ln.split('|')]

    def _convert(block):
        lines = block.strip('\n').split('\n')
        # 找出分隔行（---）索引
        sep_idx = next((i for i, ln in enumerate(lines) if _sep(ln)), None)
        rows = [ln for i, ln in enumerate(lines) if i != sep_idx]
        out = ['<table>']
        for ri, ln in enumerate(rows):
            if not ln.strip():
                continue
            tag = 'th' if (sep_idx is not None and ri < sep_idx) else 'td'
            cells_html = ''.join(f'<{tag}>{c}</{tag}>' for c in _cells(ln))
            out.append(f'<tr>{cells_html}</tr>')
        out.append('</table>')
        return '\n'.join(out)

    # 匹配连续以 | 开头的行组成的表格块
    return re.sub(r'(?:^\|.*\n)+', lambda m: _convert(m.group(0)) + '\n', html, flags=re.MULTILINE)


def markdown_to_html(md_content):
    """简单的 Markdown 转 HTML（支持基本语法）"""
    html = md_content
    
    # 代码块
    html = re.sub(r'```(\w*)\n(.*?)```', r'<pre><code class="\1">\2</code></pre>', html, flags=re.DOTALL)
    
    # 行内代码
    html = re.sub(r'`([^`]+)`', r'<code>\1</code>', html)
    
    # 标题（h1-h6）
    html = re.sub(r'^###### (.+)$', r'<h6>\1</h6>', html, flags=re.MULTILINE)
    html = re.sub(r'^##### (.+)$', r'<h5>\1</h5>', html, flags=re.MULTILINE)
    html = re.sub(r'^#### (.+)$', r'<h4>\1</h4>', html, flags=re.MULTILINE)
    html = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
    html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
    html = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)
    
    # 表格（GFM 风格）
    html = _convert_tables(html)
    
    # 粗体
    html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
    
    # 斜体
    html = re.sub(r'\*(.+?)\*', r'<em>\1</em>', html)
    
    # 链接
    html = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', html)
    
    # 列表（无序 `- ` 与有序 `1. `）
    html = re.sub(r'^- (.+)$', r'<U>\1</U>', html, flags=re.MULTILINE)
    html = re.sub(r'^(\d+)\.\s+(.+)$', r'<O>\1. \2</O>', html, flags=re.MULTILINE)
    html = re.sub(r'(<U>.*?</U>\n?)+', lambda m: '<ul>\n' + ''.join('<li>'+x+'</li>\n' for x in re.findall(r'<U>(.*?)</U>', m.group(0))) + '</ul>', html, flags=re.DOTALL)
    html = re.sub(r'(<O>.*?</O>\n?)+', lambda m: '<ol>\n' + ''.join('<li>'+x+'</li>\n' for x in re.findall(r'<O>(.*?)</O>', m.group(0))) + '</ol>', html, flags=re.DOTALL)
    
    # 引用块（支持连续多行，内容保留行内格式）
    html = re.sub(
        r'(?:^> (.+)$(?:\n|\Z))+',
        lambda m: '<blockquote>' + '<br>\n'.join(re.sub(r'^> ', '', ln) for ln in m.group(0).strip().split('\n')) + '</blockquote>',
        html, flags=re.MULTILINE)

    # 段落：按空行切分，仅将纯文本块包裹为 <p>，块级元素不包裹
    _BLOCK = ('<h1','<h2','<h3','<h4','<h5','<h6','<pre','<ul','<ol','<table','<blockquote')
    html = '\n'.join(
        (b if b.lstrip().startswith(_BLOCK) else '<p>' + b + '</p>')
        for b in re.split(r'\n\s*\n', html) if b.strip()
    )
    html = re.sub(r'<p>\s*</p>', '', html)

    return html


def load_article(article_dir):
    """加载文章目录中的 Markdown 和 metadata"""
    article_md = article_dir / "article.md"
    metadata_yaml = article_dir / "metadata.yaml"
    
    if not article_md.exists():
        return None
    
    content = article_md.read_text(encoding='utf-8')
    
    metadata = {}
    if metadata_yaml.exists():
        with open(metadata_yaml, 'r', encoding='utf-8') as f:
            metadata = list(yaml.safe_load_all(f))[0]
    
    return {
        'slug': article_dir.name,
        'content': content,
        'metadata': metadata or {}
    }


def build_json_ld(meta, canonical_url, content_plain):
    """生成 TechArticle JSON-LD 结构化数据"""
    date_val = meta.get('date', '')
    if isinstance(date_val, datetime):
        date_iso = date_val.strftime('%Y-%m-%d')
    else:
        date_iso = str(date_val)
    
    # 从正文提取前 200 字作为 body 摘要（供搜索引擎索引）
    body_excerpt = re.sub(r'[#*`\[\]()>|]', '', content_plain)
    body_excerpt = re.sub(r'\n+', ' ', body_excerpt).strip()[:500]
    
    schema = {
        "@context": "https://schema.org",
        "@type": "TechArticle",
        "headline": meta.get('title', ''),
        "description": meta.get('summary', body_excerpt[:200]),
        "datePublished": date_iso,
        "dateModified": date_iso,
        "author": {
            "@type": "Person",
            "name": meta.get('author', SITE_AUTHOR),
            "url": "https://github.com/LeisureLinux"
        },
        "publisher": {
            "@type": "Organization",
            "name": SITE_NAME,
            "url": SITE_URL
        },
        "mainEntityOfPage": {
            "@type": "WebPage",
            "@id": canonical_url
        },
        "license": "https://creativecommons.org/licenses/by-sa/4.0/",
        "proficiencyLevel": "Expert",
        "inLanguage": "zh-CN"
    }
    
    # 添加关键词（tags）
    tags = meta.get('tags', [])
    if tags:
        schema["keywords"] = ", ".join(tags)
    
    # 如果有 wechat_media_id，添加分发信息
    if meta.get('wechat_media_id'):
        schema["isPartOf"] = {
            "@type": "PublicationIssue",
            "issueNumber": meta.get('wechat_media_id', '')
        }
    
    return json.dumps(schema, ensure_ascii=False, indent=2)


PAGE_SIZE = 12


def page_url(n):
    """返回第 n 页的绝对 URL（第 1 页即首页）"""
    if n <= 1:
        return f"{SITE_URL}/"
    return f"{SITE_URL}/page/{n}/"


def render_article_items(articles):
    """渲染一页文章列表的 <li>，同时返回对应 ItemList 结构（position 从 1 起）"""
    articles_html = []
    item_list_elements = []
    sorted_articles = sorted(articles, key=lambda x: x['metadata'].get('date', ''), reverse=True)
    for idx, article in enumerate(sorted_articles, 1):
        meta = article['metadata']
        slug = article['slug']
        title = meta.get('title', slug)
        date = meta.get('date', '')
        summary = meta.get('summary', '')
        tags = meta.get('tags', [])
        if isinstance(date, datetime):
            date = date.strftime('%Y-%m-%d')
        article_url = f"{SITE_URL}/articles/{slug}/"
        tags_html = ''.join([f'<a href="/tags/{quote(tag)}/">{tag}</a>' for tag in tags])
        article_html = f"""      <li class="article-item">
        <a href="articles/{slug}/">
          <div class="article-date">{date}</div>
          <div class="article-title">{title}</div>
          <div class="article-summary">{summary}</div>
        </a>
        <div class="article-tags">{tags_html}</div>
        <div class="article-meta">
          <a class="comment-link" href="articles/{slug}/#comments" data-path="articles/{slug}/">💬 参与讨论</a>
        </div>
      </li>"""
        articles_html.append(article_html)
        item_list_elements.append({
            "@type": "ListItem",
            "position": idx,
            "name": title,
            "url": article_url
        })
    return articles_html, item_list_elements


def render_pager(page_num, total_pages):
    """渲染分页导航（含首页的「加载更多」渐进增强按钮）"""
    if total_pages <= 1:
        return ''
    parts = []
    if page_num > 1:
        parts.append(f'<a class="pg" href="{page_url(page_num - 1)}">← 上一页</a>')
    window = [p for p in range(page_num - 2, page_num + 3) if 1 <= p <= total_pages]
    for p in window:
        if p == page_num:
            parts.append(f'<span class="pg current">{p}</span>')
        else:
            parts.append(f'<a class="pg" href="{page_url(p)}">{p}</a>')
    if page_num < total_pages:
        parts.append(f'<a class="pg" href="{page_url(page_num + 1)}">下一页 →</a>')
    nav = f'<nav class="page-links">{" ".join(parts)}</nav>'
    load_more = ''
    if page_num == 1 and total_pages > 1:
        load_more = f'<button id="load-more" class="load-more" data-next="{page_url(2)}">加载更多</button>'
    return f'<div class="pagination">{load_more}{nav}</div>'


def build_index_pages(articles):
    """生成首页(index.html) + 分页页(page/N/index.html)，返回 [(相对路径, html), ...]"""
    sorted_articles = sorted(articles, key=lambda x: x['metadata'].get('date', ''), reverse=True)
    total_pages = max(1, (len(sorted_articles) + PAGE_SIZE - 1) // PAGE_SIZE)
    pages = []
    for page_num in range(1, total_pages + 1):
        start = (page_num - 1) * PAGE_SIZE
        slice_ = sorted_articles[start:start + PAGE_SIZE]
        articles_html, item_list_elements = render_article_items(slice_)
        item_list_json = json.dumps(item_list_elements, ensure_ascii=False, indent=6)
        pager_html = render_pager(page_num, total_pages)
        if page_num == 1:
            canonical_url = f"{SITE_URL}/"
            rel_prev = ''
            rel_next = f'<link rel="next" href="{page_url(2)}">' if total_pages > 1 else ''
            relpath = "index.html"
        else:
            canonical_url = page_url(page_num)
            rel_prev = f'<link rel="prev" href="{page_url(page_num - 1)}">'
            rel_next = f'<link rel="next" href="{page_url(page_num + 1)}">' if page_num < total_pages else ''
            relpath = f"page/{page_num}/index.html"
        html = INDEX_TEMPLATE.format(
            site_url=SITE_URL,
            site_name=SITE_NAME,
            site_description=SITE_DESCRIPTION,
            site_author=SITE_AUTHOR,
            canonical_url=canonical_url,
            rel_prev=rel_prev,
            rel_next=rel_next,
            articles='\n'.join(articles_html),
            item_list_json=item_list_json,
            pager_html=pager_html,
        )
        pages.append((relpath, html))
    return pages


def build_article_page(article):
    """生成文章页面 HTML（含完整 SEO/GEO 结构化数据）"""
    meta = article['metadata']
    title = meta.get('title', article['slug'])
    date = meta.get('date', '')
    tags = meta.get('tags', [])
    author = meta.get('author', SITE_AUTHOR)
    
    if isinstance(date, datetime):
        date_iso = date.strftime('%Y-%m-%d')
        date_display = date.strftime('%Y-%m-%d')
    else:
        date_iso = str(date)
        date_display = str(date)
    
    canonical_url = f"{SITE_URL}/articles/{article['slug']}/"
    
    tags_html = ''.join([f'<a itemprop="keywords" href="/tags/{quote(tag)}/">{tag}</a>' for tag in tags])

    # 去掉正文开头的重复标题（页面顶部 post-title 已展示标题）
    article_content = re.sub(r'^\s*#\s+[^\n]*\n?', '', article['content'], count=1, flags=re.MULTILINE)
    content_html = markdown_to_html(article_content)
    
    # 生成 JSON-LD
    json_ld = build_json_ld(meta, canonical_url, article['content'])
    
    # 生成 OG article:tag 标签
    og_tags = '\n  '.join([
        f'<meta property="article:tag" content="{tag}">' for tag in tags
    ])
    
    # 确定文章分类（取第一个 tag）
    article_section = tags[0] if tags else "Linux"
    
    # meta description（优先用 summary，截断到 160 字符）
    meta_description = meta.get('description', meta.get('summary', ''))[:160]
    if not meta_description:
        # 从正文提取
        plain = re.sub(r'[#*`\[\]()>|]', '', article['content'])
        meta_description = re.sub(r'\n+', ' ', plain).strip()[:160]
    
    # meta keywords
    meta_keywords = ", ".join(tags) if tags else "Linux, DevOps, 技术"
    
    return ARTICLE_TEMPLATE.format(
        title=title,
        date=date_display,
        date_iso=date_iso,
        tags=tags_html,
        content=content_html,
        canonical_url=canonical_url,
        json_ld=json_ld,
        author=author,
        site_url=SITE_URL,
        site_name=SITE_NAME,
        meta_description=meta_description,
        meta_keywords=meta_keywords,
        article_section=article_section,
        og_tags=og_tags,
        share_url=json.dumps(canonical_url),
        share_title=json.dumps(title)
    )


def build_tag_pages(articles):
    """为每个标签生成 docs/tags/<tag>/index.html 目录页，文章经标签相互关联"""
    from collections import OrderedDict
    tag_map = OrderedDict()
    for article in articles:
        for tag in (article['metadata'].get('tags') or []):
            tag_map.setdefault(tag, []).append(article)

    written = []
    for tag, tagged_articles in tag_map.items():
        tag_url = f"/tags/{quote(tag)}/"
        items = []
        for article in sorted(tagged_articles, key=lambda x: x['metadata'].get('date', ''), reverse=True):
            meta = article['metadata']
            slug = article['slug']
            date = meta.get('date', '')
            if isinstance(date, datetime):
                date = date.strftime('%Y-%m-%d')
            title = meta.get('title', slug)
            summary = meta.get('summary', '')
            items.append(f"""      <li class="article-item">
        <a href="/articles/{slug}/">
          <div class="article-date">{date}</div>
          <div class="article-title">{title}</div>
          <div class="article-summary">{summary}</div>
        </a>
      </li>""")
        html = TAG_TEMPLATE.format(
            tag=tag,
            count=len(tagged_articles),
            tag_url=tag_url,
            articles='\n'.join(items),
            SITE_URL=SITE_URL,
        )
        out_dir = DOCS_DIR / "tags" / tag
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "index.html").write_text(html, encoding='utf-8')
        written.append(tag_url)
    return written


def _xml_escape(text):
    """转义 XML 特殊字符"""
    return (str(text)
            .replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;')
            .replace('"', '&quot;')
            .replace("'", '&apos;'))


def _rfc822(date_val):
    """转 RFC 822 格式（RSS pubDate），如 Thu, 04 Aug 2026 00:00:00 +0000"""
    import datetime as _dt
    from email.utils import format_datetime
    if isinstance(date_val, _dt.datetime):
        d = date_val
    elif isinstance(date_val, _dt.date):
        d = _dt.datetime(date_val.year, date_val.month, date_val.day)
    else:
        try:
            d = _dt.datetime.strptime(str(date_val), '%Y-%m-%d')
        except (ValueError, TypeError):
            return ''
    # format_datetime(usegmt=True) 要求 UTC-aware datetime
    if d.tzinfo is None:
        d = d.replace(tzinfo=_dt.timezone.utc)
    return format_datetime(d, usegmt=True)


def generate_rss(articles):
    """生成 rss.xml（RSS 2.0，含 Atom 自引用，便于 RSS 插件识别）"""
    items = []
    for article in sorted(articles, key=lambda x: str(x['metadata'].get('date', '')), reverse=True):
        meta = article['metadata']
        url = f"{SITE_URL}/articles/{article['slug']}/"
        title = meta.get('title', article['slug'])
        description = meta.get('description') or meta.get('summary') or title
        author = meta.get('author', SITE_AUTHOR)
        cat_lines = [f"      <category>{_xml_escape(c)}</category>" for c in (meta.get('tags') or [])]
        lines = (
            ["    <item>",
             f"      <title>{_xml_escape(title)}</title>",
             f"      <link>{url}</link>",
             f'      <guid isPermaLink="true">{url}</guid>',
             f"      <pubDate>{_rfc822(meta.get('date'))}</pubDate>",
             f"      <author>{_xml_escape(author)}</author>",
             f"      <description><![CDATA[{description}]]></description>"]
            + cat_lines
            + ["    </item>"]
        )
        items.append("\n".join(lines))

    body = "\n\n".join(items)
    channel_lines = [
        "    <title>FreeLAMP.com — RSS 订阅</title>",
        f"    <link>{SITE_URL}/</link>",
        f"    <description>{_xml_escape(SITE_DESCRIPTION)}</description>",
        "    <language>zh-CN</language>",
        f'    <atom:link href="{SITE_URL}/rss.xml" rel="self" type="application/rss+xml"/>',
    ]
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">\n'
        "  <channel>\n"
        + "\n".join(channel_lines)
        + "\n"
        + body
        + "\n  </channel>\n</rss>\n"
    )

def generate_sitemap(articles):
    """生成 sitemap.xml（SEO 核心文件）"""
    urls = []
    
    # 首页
    urls.append({
        'loc': f"{SITE_URL}/",
        'changefreq': 'weekly',
        'priority': '1.0'
    })
    
    # 关于 FreeLAMP 页
    urls.append({
        'loc': f"{SITE_URL}/about-freelamp.html",
        'changefreq': 'monthly',
        'priority': '0.5'
    })

    # 文章页
    for article in sorted(articles, key=lambda x: x['metadata'].get('date', ''), reverse=True):
        meta = article['metadata']
        date = meta.get('date', '')
        if isinstance(date, datetime):
            lastmod = date.strftime('%Y-%m-%d')
        else:
            lastmod = str(date)
        
        urls.append({
            'loc': f"{SITE_URL}/articles/{article['slug']}/",
            'lastmod': lastmod,
            'changefreq': 'monthly',
            'priority': '0.8'
        })
    
    # 分页页（首页已在上面，page/2/ 起）
    num_pages = max(1, (len(articles) + PAGE_SIZE - 1) // PAGE_SIZE)
    for p in range(2, num_pages + 1):
        urls.append({
            'loc': f"{SITE_URL}/page/{p}/",
            'changefreq': 'weekly',
            'priority': '0.6'
        })

    # 标签目录页
    seen_tags = set()
    for article in articles:
        for tag in (article['metadata'].get('tags') or []):
            if tag not in seen_tags:
                seen_tags.add(tag)
                urls.append({
                    'loc': f"{SITE_URL}/tags/{quote(tag)}/",
                    'changefreq': 'weekly',
                    'priority': '0.6'
                })

    # 构建 XML
    xml_lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
    ]
    
    for url_entry in urls:
        xml_lines.append('  <url>')
        xml_lines.append(f'    <loc>{url_entry["loc"]}</loc>')
        if 'lastmod' in url_entry:
            xml_lines.append(f'    <lastmod>{url_entry["lastmod"]}</lastmod>')
        xml_lines.append(f'    <changefreq>{url_entry["changefreq"]}</changefreq>')
        xml_lines.append(f'    <priority>{url_entry["priority"]}</priority>')
        xml_lines.append('  </url>')
    
    xml_lines.append('</urlset>')
    return '\n'.join(xml_lines)


def generate_robots_txt():
    """生成 robots.txt"""
    return f"""# FreeLAMP.com - Robots.txt
# https://freelamp.com/robots.txt

User-agent: *
Allow: /
Disallow: /articles/*/draft/

# Sitemap 位置
Sitemap: {SITE_URL}/sitemap.xml

# LLM 语义索引入口（GEO 优化）
# 参考 https://llmstxt.org 规范
LLMs: {SITE_URL}/llms.txt
""".strip()


# ============================================================
# HTML 模板 — 关于 FreeLAMP（网站历史 + 作者）
# ============================================================
ABOUT_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>关于 FreeLAMP — FreeLAMP.com</title>
  <meta name="description" content="FreeLAMP.com 于 2001 年创立，是一个宣讲自由软件、供系统管理员和开放源码爱好者交流技术的网站。这里记录了这个域名二十多年的历史、作者介绍，以及重开博客的初心。">
  <meta name="author" content="{site_author}">
  <link rel="canonical" href="{site_url}/about-freelamp.html">
  <link rel="icon" type="image/x-icon" href="/favicon.ico">
  <link rel="alternate" type="application/rss+xml" title="FreeLAMP.com RSS 订阅" href="/rss.xml">
  <!-- Open Graph -->
  <meta property="og:type" content="profile">
  <meta property="og:title" content="关于 FreeLAMP — 一个域名，二十多年的故事">
  <meta property="og:description" content="FreeLAMP.com 的历史、作者介绍与重开博客的初心。">
  <meta property="og:url" content="{site_url}/about-freelamp.html">
  <meta property="og:site_name" content="{site_name}">
  <meta property="og:locale" content="zh_CN">
  <!-- JSON-LD -->
  <script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@type": "ProfilePage",
    "name": "关于 FreeLAMP",
    "url": "{site_url}/about-freelamp.html",
    "mainEntity": {{
      "@type": "Person",
      "name": "{site_author}",
      "url": "https://github.com/LeisureLinux",
      "email": "albertxu@freelamp.com",
      "knowsAbout": ["Linux", "自由软件", "开源", "系统管理", "DevSecOps"],
      "sameAs": [
        "https://github.com/LeisureLinux"
      ]
    }}
  }}
  </script>
  <style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif;
      background: #F9FAFB; color: #374151; line-height: 1.8;
    }}
    .container {{ max-width: 720px; margin: 0 auto; padding: 0 24px; }}
    nav {{
      background: #fff; border-bottom: 1px solid #E5E7EB;
      padding: 12px 0; position: sticky; top: 0; z-index: 10;
    }}
    nav .container {{ display: flex; align-items: center; justify-content: space-between; }}
    nav a {{ color: #059669; text-decoration: none; font-weight: 600; font-size: 14px; }}
    nav .brand {{ font-weight: 800; color: #111827; font-size: 15px; }}
    .page-header {{
      background: linear-gradient(135deg, #059669, #10B981);
      padding: 56px 0 44px; color: #fff; text-align: center;
    }}
    .page-header h1 {{ font-size: 30px; font-weight: 900; letter-spacing: -1px; margin-bottom: 12px; }}
    .page-header p {{ font-size: 15px; opacity: 0.9; max-width: 560px; margin: 0 auto; }}
    main {{ padding: 40px 0 24px; }}
    .post-content {{ padding-bottom: 24px; }}
    .post-content h2 {{
      font-size: 22px; font-weight: 800; color: #111827;
      margin: 40px 0 16px; padding-bottom: 8px;
      border-bottom: 2px solid #059669;
    }}
    .post-content h3 {{ font-size: 17px; font-weight: 700; color: #111827; margin: 24px 0 12px; }}
    .post-content p {{ margin-bottom: 16px; font-size: 15px; line-height: 1.9; }}
    .post-content strong {{ color: #059669; }}
    .post-content blockquote {{
      border-left: 4px solid #059669; background: #ECFDF5;
      padding: 12px 20px; margin: 0 0 20px; border-radius: 0 8px 8px 0;
      font-size: 15px;
    }}
    .timeline {{ list-style: none; margin: 0 0 24px; }}
    .timeline li {{
      position: relative; padding: 0 0 18px 28px; font-size: 15px;
    }}
    .timeline li::before {{
      content: ""; position: absolute; left: 4px; top: 8px;
      width: 10px; height: 10px; border-radius: 50%;
      background: #059669;
    }}
    .timeline .yr {{
      font-weight: 800; color: #059669; margin-right: 6px; letter-spacing: 0.5px;
    }}
    .post-content ul {{ margin: 0 0 16px 24px; }}
    .post-content li {{ margin-bottom: 8px; font-size: 15px; line-height: 1.8; }}
    .post-content hr {{ border: none; border-top: 1px solid #E5E7EB; margin: 32px 0; }}
    footer {{
      text-align: center; padding: 32px 0; color: #9CA3AF;
      font-size: 13px; border-top: 1px solid #E5E7EB;
    }}
    footer a {{ color: #059669; text-decoration: none; }}
  </style>
</head>
<body>
  <nav>
    <div class="container">
      <a class="brand" href="/">📜 FreeLAMP.com</a>
    </div>
  </nav>

  <div class="page-header">
    <div class="container">
      <h1>关于 FreeLAMP</h1>
      <p>一个注册于 2001 年的域名，和它背后的二十多年故事。</p>
    </div>
  </div>

  <main class="container">
    <article class="post-content">

      <p>你好，我是 <strong>老徐</strong>，系统管理员出身，自由软件的忠实信徒，爱折腾。这个网站叫 <strong>FreeLAMP.com</strong>，它比很多人的 QQ 号还老。借着这次用现代工具把它重新点亮，我想把这个域名的故事、我自己，以及为什么要重新开这个博客，好好写一写。</p>

      <h2>一、这个网站的历史</h2>
      <ul class="timeline">
        <li><span class="yr">2001 年 3 月</span>我注册了 FreeLAMP.com，最初托管于宁波电信。它是系统管理员和开放源码爱好者交流技术的早期中文站点之一。域名创意起源于 O'Reilly 的 <a href="https://onlamp.com">OnLAMP.com</a>——当年那正是专门介绍 LAMP 技术与相关图书的网站。</li>
        <li><span class="yr">2001–2007</span>期间站点搬迁到北京网通。</li>
        <li><span class="yr">2008 年底</span>托管于上海某电信机房。</li>
        <li><span class="yr">2009 年</span>搬迁至上海浦东沈家弄机房。</li>
        <li><span class="yr">2010 年 12 月</span>搬迁到 GoDaddy。</li>
        <li><span class="yr">2016 年 11 月</span>搬迁到 AWS 云端。</li>
        <li><span class="yr">2020 年 1 月</span>以个人身份完成备案，搬迁到杭州阿里云服务器。</li>
        <li><span class="yr">2026 年</span>迁移到 GitHub Pages，用静态站点 + 自定义域名 <strong>freelamp.com</strong> 重新上线，也就是你现在看到的这个站点。</li>
      </ul>
      <blockquote>旧版「关于本站」页面，因当年 GoDaddy 服务器不支持 Zope 而无法访问了。幸运的是，网站的核心精神——自由与分享——一直保留到了今天。</blockquote>

      <h2>二、FreeLAMP 是什么意思？</h2>
      <p>FreeLAMP 这个名字里，<strong>Free</strong> 是「自由」，不是「免费」；<strong>LAMP</strong> 是 Linux + Apache + MySQL + PHP/Perl/Python，但这里的 LAMP 也绝不是「灯」。</p>
      <p>所以本站不是免费提供灯泡的地方（笑）。<strong>「FreeLAMP，像风一样自由」</strong>，是 FreeLAMP.com 作为宣传自由软件的口号。FreeLAMP.com 是一个宣讲计算机软件的网站，是系统管理员和开放源码爱好者学习和交流技术的场所。</p>

      <h2>三、作者：一个爱折腾的系统管理员</h2>
      <p>我在 IT 一线做了三十来年：管过大规模银行终端网络，写 Perl 和 Shell，研究 Linux 内核、DNS、虚拟化，也一路看着开源从一个「圈子」长成整个数字世界的基石。我写过不少代码，也踩过无数坑，而我很早就养成了一个习惯——<strong>把踩过的坑、想明白的道理，用文字沉淀下来。</strong></p>
      <p>这也是为什么这些年我一直叫自己 LeisureLinux：闲下来，就折腾 Linux。</p>

      <h2>四、为什么重新开这个博客？</h2>
      <p>重开 FreeLAMP.com，不是为了流量，也不为别的什么——说到底，还是<strong>当年的初心</strong>。</p>
      <ul>
        <li>当年开站，是想给中文世界里的系统管理员一个交流技术、宣传自由软件的地方；</li>
        <li>现在重新开，是希望用今天更好用的工具（GitHub Pages、静态站点、甚至 AI 写代码的搭档），继续把这份「像风一样自由」的折腾精神传下去；</li>
        <li>这里写的每一篇，都是能拿去落地的真实经验与思考，而不是转述与搬运。</li>
      </ul>
      <p>时代变了，工具变了，但「把自己会的、懂的、踩过的坑，认真地讲给别人听」这件事，从来没有变过。</p>

      <hr>
      <h2>五、联系方式</h2>
      <ul>
        <li>同名公众号和B站频道<a href="#">Leisure Linux</a></li>
        <li>GitHub：<a href="https://github.com/LeisureLinux">LeisureLinux</a></li>
        <li>博客：<a href="{site_url}/">https://freelamp.com/</a></li>
        <li>RSS 订阅：<a href="{site_url}/rss.xml">rss.xml</a></li>
      </ul>
      <p>自我的觉醒却是光阴偷不走，人拿不走的。愿我们永远保持对技术的热爱与自由。🕊️</p>

    </article>
  </main>

  <footer>
    <div class="container">
      <p>© 2026 LeisureLinux · <a href="https://github.com/LeisureLinux/lore">GitHub</a> · <a href="/about-freelamp.html">关于 FreeLAMP</a> · <a href="/rss.xml">RSS 订阅</a></p>
      <p style="margin-top: 8px; font-size: 12px;">本文以 <a href="https://creativecommons.org/licenses/by-sa/4.0/">CC BY-SA 4.0</a> 协议开源</p>
    </div>
  </footer>
</body>
</html>"""


def build_about_page():
    """生成「关于 FreeLAMP」页面（网站历史 + 作者介绍）"""
    return ABOUT_TEMPLATE.format(
        site_url=SITE_URL,
        site_name=SITE_NAME,
        site_author=SITE_AUTHOR,
    )



def main():
    print("🔨 开始构建 FreeLAMP.com 静态站点...")
    
    # 清理 docs 目录
    if DOCS_DIR.exists():
        import shutil
        shutil.rmtree(DOCS_DIR)
    DOCS_DIR.mkdir(parents=True)
    
    # 扫描文章
    articles = []
    if ARTICLES_DIR.exists():
        for article_dir in ARTICLES_DIR.iterdir():
            if article_dir.is_dir() and not article_dir.name.startswith('.'):
                article = load_article(article_dir)
                if article:
                    articles.append(article)
                    print(f"   📄 加载文章：{article['slug']}")
    
    print(f"\n📊 共找到 {len(articles)} 篇文章")
    
    # 生成首页 + 分页页（page/2/ ...）
    index_pages = build_index_pages(articles)
    for relpath, html in index_pages:
        out = DOCS_DIR / relpath
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(html, encoding='utf-8')
    print(f"✅ 生成首页及分页页：共 {len(index_pages)} 页")

    # 生成「关于 FreeLAMP」页面
    about_html = build_about_page()
    (DOCS_DIR / "about-freelamp.html").write_text(about_html, encoding='utf-8')
    print("✅ 生成关于页：docs/about-freelamp.html")
    
    # 生成文章页面
    articles_dir = DOCS_DIR / "articles"
    articles_dir.mkdir(parents=True)
    
    for article in articles:
        article_html = build_article_page(article)
        article_output_dir = articles_dir / article['slug']
        article_output_dir.mkdir(parents=True, exist_ok=True)
        (article_output_dir / "index.html").write_text(article_html, encoding='utf-8')
        print(f"✅ 生成文章：docs/articles/{article['slug']}/index.html")
    
    # 生成标签目录页
    tag_urls = build_tag_pages(articles)
    print(f"✅ 生成标签页：共 {len(tag_urls)} 个")

    # 生成 sitemap.xml
    sitemap_xml = generate_sitemap(articles)
    (DOCS_DIR / "sitemap.xml").write_text(sitemap_xml, encoding='utf-8')
    print("✅ 生成站点地图：docs/sitemap.xml")
    
    # 生成 rss.xml
    rss_xml = generate_rss(articles)
    (DOCS_DIR / "rss.xml").write_text(rss_xml, encoding='utf-8')
    print("✅ 生成 RSS 订阅：docs/rss.xml")
    
    # 生成 robots.txt
    robots_txt = generate_robots_txt()
    (DOCS_DIR / "robots.txt").write_text(robots_txt, encoding='utf-8')
    print("✅ 生成爬虫规则：docs/robots.txt")
    
    # 复制 llms.txt 到 docs 目录（供 GitHub Pages 访问）
    llms_src = LORE_DIR / "llms.txt"
    if llms_src.exists():
        (DOCS_DIR / "llms.txt").write_text(llms_src.read_text(encoding='utf-8'), encoding='utf-8')
        print("✅ 复制 LLM 索引：docs/llms.txt")
    
    # 写入 CNAME：自定义域名 freelamp.com（GitHub Pages 保持绑定）
    (DOCS_DIR / "CNAME").write_text("freelamp.com\n", encoding="utf-8")
    print("✅ 生成 CNAME：docs/CNAME (freelamp.com)")

    # 复制静态验证文件到 docs 目录（Google/Bing 等搜索引擎验证）
    static_files = [
        "googlec29651f57d804644.html",  # Google Search Console 验证
        "favicon.ico",  # 站点图标
        # 可在此添加其他验证文件，如：
        # "BingSiteAuth.xml",  # Bing 验证
    ]
    
    copied_static = 0
    for filename in static_files:
        src_file = LORE_DIR / filename
        if src_file.exists():
            shutil.copy2(src_file, DOCS_DIR / filename)
            print(f"✅ 复制静态文件：docs/{filename}")
            copied_static += 1
    
    total_files = len(articles) + 4 + copied_static  # 首页 + 文章 + sitemap + robots + rss
    print(f"\n🎉 构建完成！共生成 {total_files} 个文件（含 SEO/GEO 优化）")


if __name__ == "__main__":
    main()
