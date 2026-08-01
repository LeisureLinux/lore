#!/usr/bin/env python3
"""
LeisureLinux Lore 静态站点构建脚本
从 articles/ 目录读取 Markdown 文件，生成 docs/ 目录的 HTML 页面
"""

import os
import re
import yaml
from pathlib import Path
from datetime import datetime

LORE_DIR = Path(__file__).parent
ARTICLES_DIR = LORE_DIR / "articles"
DOCS_DIR = LORE_DIR / "docs"

# HTML 模板
INDEX_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>LeisureLinux Lore — 技术传说</title>
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

ARTICLE_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title} — LeisureLinux Lore</title>
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
    <div class="post-header">
      <div class="post-date">{date}</div>
      <h1 class="post-title">{title}</h1>
      <div class="post-tags">{tags}</div>
    </div>

    <div class="post-content">
{content}
    </div>
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


def build_index(articles):
    """生成首页 HTML"""
    articles_html = []
    
    for article in sorted(articles, key=lambda x: x['metadata'].get('date', ''), reverse=True):
        meta = article['metadata']
        slug = article['slug']
        title = meta.get('title', slug)
        date = meta.get('date', '')
        summary = meta.get('summary', '')
        tags = meta.get('tags', [])
        
        if isinstance(date, datetime):
            date = date.strftime('%Y-%m-%d')
        
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
    
    return INDEX_TEMPLATE.format(articles='\n'.join(articles_html))


def build_article_page(article):
    """生成文章页面 HTML"""
    meta = article['metadata']
    title = meta.get('title', article['slug'])
    date = meta.get('date', '')
    tags = meta.get('tags', [])
    
    if isinstance(date, datetime):
        date = date.strftime('%Y-%m-%d')
    
    tags_html = ''.join([f'<span>{tag}</span>' for tag in tags])
    content_html = markdown_to_html(article['content'])
    
    return ARTICLE_TEMPLATE.format(
        title=title,
        date=date,
        tags=tags_html,
        content=content_html
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
    
    # 生成文章页面
    articles_dir = DOCS_DIR / "articles"
    articles_dir.mkdir(parents=True)
    
    for article in articles:
        article_html = build_article_page(article)
        article_output_dir = articles_dir / article['slug']
        article_output_dir.mkdir(parents=True, exist_ok=True)
        (article_output_dir / "index.html").write_text(article_html, encoding='utf-8')
        print(f"✅ 生成文章：docs/articles/{article['slug']}/index.html")
    
    print(f"\n 构建完成！共生成 {len(articles) + 1} 个 HTML 文件")


if __name__ == "__main__":
    main()
