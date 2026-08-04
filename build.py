#!/usr/bin/env python3
"""
LeisureLinux Lore 静态站点构建脚本
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
SITE_NAME = "LeisureLinux Lore"
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
  <title>LeisureLinux Lore — Linux 底层机制与 DevSecOps 深度技术知识库</title>
  <meta name="description" content="{site_description}。涵盖 Linux 内核调优、TLS/PKI 信任链、网络协议安全、CVE 漏洞分析、DevOps 工具链。">
  <meta name="keywords" content="Linux, 内核, DevSecOps, TLS, PKI, 网络安全, CVE, eBPF, systemd, SRE, 基础架构, DevOps">
  <meta name="author" content="{site_author}">
  <link rel="canonical" href="{site_url}/">
  <link rel="icon" type="image/x-icon" href="/favicon.ico">
  <link rel="alternate" type="application/rss+xml" title="LeisureLinux Lore RSS 订阅" href="/rss.xml">

  <!-- Open Graph -->
  <meta property="og:type" content="website">
  <meta property="og:title" content="LeisureLinux Lore — Linux 底层机制与 DevSecOps 深度技术知识库">
  <meta property="og:description" content="{site_description}">
  <meta property="og:url" content="{site_url}/">
  <meta property="og:site_name" content="{site_name}">
  <meta property="og:locale" content="zh_CN">

  <!-- Twitter Card -->
  <meta name="twitter:card" content="summary">
  <meta name="twitter:title" content="LeisureLinux Lore — 技术传说">
  <meta name="twitter:description" content="{site_description}">

  <!-- JSON-LD 结构化数据：WebSite + SearchAction -->
  <script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@type": "WebSite",
    "name": "{site_name}",
    "url": "{site_url}/",
    "description": "{site_description}",
    "author": {{
      "@type": "Person",
      "name": "{site_author}",
      "url": "https://github.com/LeisureLinux"
    }},
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
    "name": "LeisureLinux Lore 技术文章",
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
      <h1>📜 LeisureLinux Lore</h1>
      <p>技术传说，记录于此。</p>
      <div class="tags">
        <span>Linux</span><span>内核</span><span>安全</span><span>开源</span>
      </div>
    </div>
  </header>

  <main class="container">
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

# ============================================================
# HTML 模板 — 文章页（含完整 SEO/GEO 结构化数据）
# ============================================================
ARTICLE_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title} — LeisureLinux Lore</title>
  <meta name="description" content="{meta_description}">
  <meta name="keywords" content="{meta_keywords}">
  <meta name="author" content="{author}">
  <meta name="date" content="{date_iso}">
  <link rel="canonical" href="{canonical_url}">
  <link rel="icon" type="image/x-icon" href="/favicon.ico">

  <link rel="alternate" type="application/rss+xml" title="LeisureLinux Lore RSS 订阅" href="/rss.xml">
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
        "name": "LeisureLinux Lore",
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
  </main>

  <footer>
    <div class="container">
      <p>© 2026 LeisureLinux · <a href="https://github.com/LeisureLinux/lore">GitHub</a> · <a href="/about-freelamp.html">关于 FreeLAMP</a> · <a href="/rss.xml">RSS 订阅</a></p>
      <p style="margin-top: 8px; font-size: 12px;">本文以 <a href="https://creativecommons.org/licenses/by-sa/4.0/">CC BY-SA 4.0</a> 协议开源</p>
    </div>
  </footer>
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


def markdown_to_html(md_content):
    """简单的 Markdown 转 HTML（支持基本语法）"""
    html = md_content
    
    # 代码块
    html = re.sub(r'```(\w*)\n(.*?)```', r'<pre><code class="\1">\2</code></pre>', html, flags=re.DOTALL)
    
    # 行内代码
    html = re.sub(r'`([^`]+)`', r'<code>\1</code>', html)
    
    # 标题
    html = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
    html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
    html = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)
    
    # 粗体
    html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
    
    # 斜体
    html = re.sub(r'\*(.+?)\*', r'<em>\1</em>', html)
    
    # 链接
    html = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', html)
    
    # 列表
    html = re.sub(r'^- (.+)$', r'<li>\1</li>', html, flags=re.MULTILINE)
    html = re.sub(r'(<li>.*</li>\n?)+', lambda m: '<ul>\n' + m.group(0) + '</ul>', html)
    
    # 段落
    html = re.sub(r'\n\n', '</p>\n<p>', html)
    html = '<p>' + html + '</p>'
    
    # 清理空段落
    html = re.sub(r'<p>\s*</p>', '', html)
    html = re.sub(r'<p>(<h[123]>.*?</h[123]>)</p>', r'\1', html)
    html = re.sub(r'<p>(<pre>.*?</pre>)</p>', r'\1', html, flags=re.DOTALL)
    html = re.sub(r'<p>(<ul>.*?</ul>)</p>', r'\1', html, flags=re.DOTALL)
    html = re.sub(r'<p>(<blockquote>.*?</blockquote>)</p>', r'\1', html, flags=re.DOTALL)
    
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


def build_index(articles):
    """生成首页 HTML（含 SEO 结构化数据）"""
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
      </li>"""
        articles_html.append(article_html)
        
        # 构建 ItemList JSON-LD 元素
        item_list_elements.append({
            "@type": "ListItem",
            "position": idx,
            "name": title,
            "url": article_url
        })
    
    # 格式化 ItemList JSON
    item_list_json = json.dumps(item_list_elements, ensure_ascii=False, indent=6)
    
    return INDEX_TEMPLATE.format(
        site_url=SITE_URL,
        site_name=SITE_NAME,
        site_description=SITE_DESCRIPTION,
        site_author=SITE_AUTHOR,
        articles='\n'.join(articles_html),
        item_list_json=item_list_json
    )


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
    content_html = markdown_to_html(article['content'])
    
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
        og_tags=og_tags
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
        out_dir = DOCS_DIR / "tags" / quote(tag)
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
        "    <title>LeisureLinux Lore — RSS 订阅</title>",
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
    return f"""# LeisureLinux Lore - Robots.txt
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
  <title>关于 FreeLAMP — LeisureLinux Lore</title>
  <meta name="description" content="FreeLAMP.com 由徐永久（LeisureLinux）于 2001 年创立，是一个宣讲自由软件、供系统管理员和开放源码爱好者交流技术的网站。这里记录了这个域名二十多年的历史、作者介绍，以及重开博客的初心。">
  <meta name="author" content="{site_author}">
  <link rel="canonical" href="{site_url}/about-freelamp.html">
  <link rel="icon" type="image/x-icon" href="/favicon.ico">
  <link rel="alternate" type="application/rss+xml" title="LeisureLinux Lore RSS 订阅" href="/rss.xml">
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
    "author": {{
      "@type": "Person",
      "name": "{site_author}",
      "url": "https://github.com/LeisureLinux",
      "email": "albertxu@freelamp.com",
      "knowsAbout": ["Linux", "自由软件", "开源", "系统管理", "DevSecOps"]
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
      <span class="brand">📜 LeisureLinux Lore</span>
      <a href="/">← 返回首页</a>
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

      <p>你好，我是 <strong>徐永久（LeisureLinux / Albert Xu）</strong>，系统管理员出身，自由软件的忠实信徒，爱折腾。这个网站叫 <strong>FreeLAMP.com</strong>，它比很多人的 QQ 号还老。借着这次用现代工具把它重新点亮，我想把这个域名的故事、我自己，以及为什么要重新开这个博客，好好写一写。</p>

      <h2>一、这个网站的历史</h2>
      <ul class="timeline">
        <li><span class="yr">2001 年 3 月</span>我（徐永久）在宁波电信创立了 FreeLAMP.com，最初托管于宁波电信。它是系统管理员和开放源码爱好者交流技术的早期中文站点之一。</li>
        <li><span class="yr">2001–2007</span>期间站点搬迁到北京网通。</li>
        <li><span class="yr">2008 年底</span>托管于上海某电信机房。</li>
        <li><span class="yr">2009 年</span>搬迁至上海浦东沈家弄机房。</li>
        <li><span class="yr">2010 年 12 月</span>搬迁到 GoDaddy。</li>
        <li><span class="yr">2016 年 11 月</span>搬迁到免费的 AWS 云端。</li>
        <li><span class="yr">2020 年 1 月</span>以个人身份完成备案，搬迁到杭州阿里云服务器。</li>
        <li><span class="yr">2026 年</span>迁移到 GitHub Pages，用静态站点 + 自定义域名 <strong>freelamp.com</strong> 重新上线，也就是你现在看到的这个站点。</li>
      </ul>
      <blockquote>旧版「关于本站」页面，因当年 GoDaddy 服务器不支持 Zope 而无法访问了。幸运的是，网站的核心精神——自由与分享——一直保留到了今天。</blockquote>

      <h2>二、FreeLAMP 是什么意思？</h2>
      <p>FreeLAMP 这个名字里，<strong>Free</strong> 是「自由」，不是「免费」；<strong>LAMP</strong> 是 Linux + Apache + MySQL + PHP/Perl/Python，但这里的 LAMP 也绝不是「灯」。</p>
      <p>所以本站不是免费提供灯泡的地方（笑）。<strong>「FreeLAMP，像风一样自由」</strong>，是 FreeLAMP.com 作为宣传自由软件的口号。FreeLAMP.com 是一个宣讲计算机软件的网站，是系统管理员和开放源码爱好者学习和交流技术的场所。</p>

      <h2>三、作者：一个爱折腾的系统管理员</h2>
      <p>我在 IT 一线做了三十来年：管过大规模银行终端网络（几万台端点，当时只有三个工程师），写 Perl 和 Shell，研究 Linux 内核、DNS、TLS、虚拟化，也一路看着开源从一个「圈子」长成整个数字世界的基石。我写过不少代码，也踩过无数坑，而我很早就养成了一个习惯——<strong>把踩过的坑、想明白的道理，用文字沉淀下来。</strong></p>
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
        <li>邮箱：<a href="mailto:albertxu@freelamp.com">albertxu@freelamp.com</a></li>
        <li>GitHub：<a href="https://github.com/LeisureLinux">LeisureLinux</a></li>
        <li>博客：<a href="{site_url}/">https://freelamp.com/</a></li>
        <li>RSS 订阅：<a href="{site_url}/rss.xml">rss.xml</a></li>
      </ul>
      <p>愿我们永远保持对技术的热爱与自由。🕊️</p>

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
    print("🔨 开始构建 LeisureLinux Lore 静态站点...")
    
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
    
    # 生成首页
    index_html = build_index(articles)
    (DOCS_DIR / "index.html").write_text(index_html, encoding='utf-8')
    print("✅ 生成首页：docs/index.html")

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
