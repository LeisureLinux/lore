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
from pathlib import Path
from datetime import datetime

LORE_DIR = Path(__file__).parent
ARTICLES_DIR = LORE_DIR / "articles"
DOCS_DIR = LORE_DIR / "docs"

# 站点基础配置（SEO 用）
SITE_URL = "https://leisurelinux.github.io/lore"
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
    .article-tags span {{
      background: #ECFDF5; color: #059669; padding: 2px 8px;
      border-radius: 4px; font-size: 11px; font-weight: 600;
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
      <p>© 2026 LeisureLinux · <a href="https://github.com/LeisureLinux/lore">GitHub</a></p>
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
    nav .brand {{ font-weight: 800; color: #111827; font-size: 15px; }}
    
    .post-header {{ padding: 48px 0 32px; border-bottom: 1px solid #E5E7EB; margin-bottom: 32px; }}
    .post-date {{ font-size: 13px; color: #9CA3AF; font-weight: 600; letter-spacing: 1px; margin-bottom: 12px; }}
    .post-title {{ font-size: 28px; font-weight: 900; color: #111827; line-height: 1.3; letter-spacing: -0.5px; margin-bottom: 16px; }}
    .post-tags {{ display: flex; gap: 6px; flex-wrap: wrap; }}
    .post-tags span {{
      background: #ECFDF5; color: #059669; padding: 3px 10px;
      border-radius: 4px; font-size: 12px; font-weight: 600;
    }}
    
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
      <span class="brand">📜 LeisureLinux Lore</span>
      <a href="../../">← 返回列表</a>
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
      <p>© 2026 LeisureLinux · <a href="https://github.com/LeisureLinux/lore">GitHub</a></p>
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
        
        tags_html = ''.join([f'<span>{tag}</span>' for tag in tags])
        
        article_html = f"""      <li class="article-item">
        <a href="articles/{slug}/">
          <div class="article-date">{date}</div>
          <div class="article-title">{title}</div>
          <div class="article-summary">{summary}</div>
          <div class="article-tags">{tags_html}</div>
        </a>
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
    
    tags_html = ''.join([f'<span itemprop="keywords">{tag}</span>' for tag in tags])
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


def generate_sitemap(articles):
    """生成 sitemap.xml（SEO 核心文件）"""
    urls = []
    
    # 首页
    urls.append({
        'loc': f"{SITE_URL}/",
        'changefreq': 'weekly',
        'priority': '1.0'
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
# https://leisurelinux.github.io/lore/robots.txt

User-agent: *
Allow: /
Disallow: /articles/*/draft/

# Sitemap 位置
Sitemap: {SITE_URL}/sitemap.xml

# LLM 语义索引入口（GEO 优化）
# 参考 https://llmstxt.org 规范
LLMs: {SITE_URL}/llms.txt
""".strip()


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
    
    # 生成文章页面
    articles_dir = DOCS_DIR / "articles"
    articles_dir.mkdir(parents=True)
    
    for article in articles:
        article_html = build_article_page(article)
        article_output_dir = articles_dir / article['slug']
        article_output_dir.mkdir(parents=True, exist_ok=True)
        (article_output_dir / "index.html").write_text(article_html, encoding='utf-8')
        print(f"✅ 生成文章：docs/articles/{article['slug']}/index.html")
    
    # 生成 sitemap.xml
    sitemap_xml = generate_sitemap(articles)
    (DOCS_DIR / "sitemap.xml").write_text(sitemap_xml, encoding='utf-8')
    print("✅ 生成站点地图：docs/sitemap.xml")
    
    # 生成 robots.txt
    robots_txt = generate_robots_txt()
    (DOCS_DIR / "robots.txt").write_text(robots_txt, encoding='utf-8')
    print("✅ 生成爬虫规则：docs/robots.txt")
    
    # 复制 llms.txt 到 docs 目录（供 GitHub Pages 访问）
    llms_src = LORE_DIR / "llms.txt"
    if llms_src.exists():
        (DOCS_DIR / "llms.txt").write_text(llms_src.read_text(encoding='utf-8'), encoding='utf-8')
        print("✅ 复制 LLM 索引：docs/llms.txt")
    
    total_files = len(articles) + 3  # 首页 + 文章 + sitemap + robots
    print(f"\n🎉 构建完成！共生成 {total_files} 个文件（含 SEO/GEO 优化）")


if __name__ == "__main__":
    main()
