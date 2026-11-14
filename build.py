#!/usr/bin/env python3
"""
FreeLAMP.com 静态站点构建脚本
从 articles/ 目录读取 Markdown 文件，生成 docs/ 目录的 HTML 页面
包含 SEO/GEO 优化：JSON-LD 结构化数据、Open Graph、Canonical URL、Sitemap、Robots.txt
"""

import os
import html
import re
import json
import sys
import unicodedata
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
# 站点统一署名（文章 metadata.author 优先；公众号规范为 FreeLAMP.com）
SEO_AUTHOR_NAME = "FreeLAMP.com"
SEO_AUTHOR_URL = f"{SITE_URL}/about-freelamp.html"
SEO_PUBLISHER_LOGO = f"{SITE_URL}/favicon.ico"
DEFAULT_OG_IMAGE = f"{SITE_URL}/tc-promotion-banner-1200x400.png"

# 标签页最小文章数：低于阈值的旧标签页仍会生成（保住历史 URL 与站内链接），
# 但加 noindex,follow，且不写入 sitemap，让爬虫把预算留给文章与合格专题页。
MIN_TAG_PAGE_ARTICLES = 3
# 首页及分页每页文章数
PAGE_SIZE = 12


def esc(value) -> str:
    """HTML 文本/属性值转义。用于所有从 metadata 插入模板的动态字符串。"""
    return html.escape(str(value if value is not None else ''), quote=True)


def tag_slug(tag) -> str:
    """把标签转成稳定、单层、可读的 URL slug。

    中文/日文保留，拉丁字母小写，空格与斜杠等分隔符统一成连字符。
    例：AI/LLM -> ai-llm，TCP/IP -> tcp-ip，小 I/O 简单 DIO -> 小-io-简单-dio。
    纯符号标签回退为 URL 编码，保证 slug 非空且不会产生额外路径层级。
    """
    text = unicodedata.normalize('NFKC', str(tag)).strip()
    text = re.sub(r'\s+', '-', text)
    text = re.sub(r'[^\w\-一-鿿぀-ヿ]+', '-', text, flags=re.UNICODE)
    text = re.sub(r'-{2,}', '-', text).strip('-').lower()
    if not text:
        text = quote(str(tag), safe='') or 'tag'
    return text


def tag_url_for(tag) -> str:
    """返回标签页绝对路径。

    保守策略：历史上已有约 2,600 个 /tags/<URL-encoded 原标签>/ 页面和外链，
    绝大多数 URL 保持不变；仅对含斜杠、会产生额外路径层级的 10 个标签改用
    单层 slug（如 AI/LLM -> ai-llm），并为旧路径输出 meta refresh 过渡页。
    """
    raw = str(tag)
    if '/' in raw:
        return f"/tags/{tag_slug(raw)}/"
    return f"/tags/{quote(raw)}/"


def tag_disk_dir(tag) -> str:
    """返回 docs/tags/ 下的真实目录名（用原文，不是 percent-encoding）。

    GitHub Pages 会把 URL 中的 %E8%AF%91%E6%96%87 解码后在磁盘上查找
    `tags/译文/index.html`；若把目录直接命名成 `%E8%AF%91...` 会导致 404。
    """
    raw = str(tag)
    if '/' in raw:
        return tag_slug(raw)
    return raw


def truncate_seo_description(value, limit: int = 158) -> str:
    """按中文/英文句子边界生成 150–160 字的 meta description。

    避免原来 [:160] 在英文专名或引号中间硬截；返回值已适合 HTML 属性转义前使用。
    """
    text = re.sub(r'\s+', ' ', str(value or '')).strip()
    if len(text) <= limit:
        return text
    window = text[:limit + 1]
    candidates = [window.rfind(ch) for ch in '。！？；!?;：:，,、 ']
    cut = max(candidates)
    if cut < limit * 0.6:
        cut = limit
    result = window[:cut].rstrip('，,、：:；; ')
    if result and result[-1] not in '。！？!?':
        result += '…'
    return result


def collect_tag_map(articles):
    """返回全部 {tag: [article, ...]}，按首次出现顺序（保持旧 URL 稳定）。"""
    from collections import OrderedDict
    tag_map = OrderedDict()
    for article in articles:
        for tag in (article['metadata'].get('tags') or []):
            tag_map.setdefault(str(tag), []).append(article)
    return tag_map


def collect_indexable_tags(articles):
    """返回达到 MIN_TAG_PAGE_ARTICLES 的标签，按文章数降序。"""
    from collections import OrderedDict
    eligible = OrderedDict(
        (tag, tagged) for tag, tagged in collect_tag_map(articles).items()
        if len(tagged) >= MIN_TAG_PAGE_ARTICLES
    )
    return OrderedDict(sorted(eligible.items(), key=lambda kv: (-len(kv[1]), kv[0])))


COVERS_DIR = LORE_DIR / "covers"


def article_cover_webp(slug: str):
    """返回文章的 WebP 封面源文件（由 tools/ 或 maintainers 生成后纳入 git）。"""
    p = COVERS_DIR / f"{slug}.webp"
    return p if p.is_file() else None


def find_article_cover(slug: str, meta: dict):
    """返回文章封面 URL 路径：metadata.cover 优先，其次 covers/<slug>.webp。

    WebP 文件是构建输入而非构建产物：GitHub Actions 只安装 pyyaml，不装 Pillow，
    因此 build.py 不能在 CI 里临时转换图片；生成/更新封面是独立的维护步骤。
    """
    configured = str(meta.get('cover') or '').strip()
    if configured:
        return configured
    if article_cover_webp(slug):
        return f"/covers/{slug}.webp"
    return None

# ================= 京东联盟 CPS 推广（可选） =================
# 1) 在 https://union.jd.com/ 登录联盟后台，选商品「获取推广链接」得到 jdc 长链。
# 2) 每篇文章 front-matter 可用 jd_url: 指定该文的京东推广链接（覆盖全局默认）。
# 3) 未指定时回退到全局 JD_BUY_URL；两者都留空则该文不显示「京东购买」卡片。
JD_BUY_URL = "https://u.jd.com/4DxNxMi"
JD_BUY_TITLE = "农合天下 内蒙古赤峰敖汉黄小米 五谷杂粮 5斤"
# 商品图：京东商品主图缩方，经 static_files 复制到 docs/，
# 线上地址 https://freelamp.com/jd-aohan-xiaomi.jpg（92x92 object-fit:cover 展示）
JD_BUY_IMG = "https://freelamp.com/jd-aohan-xiaomi.jpg"

# ================= 腾讯云 CPS 广告位（可选） =================
# 在每篇文章正文第一个 </blockquote> 后插入推广横幅；TC_AD_URL 留空则全文不插入。
TC_AD_URL = "https://curl.qcloud.com/P0rebqgV"
TC_AD_TITLE = "【腾讯云】2核2G4M 服务器新客99元/年起"
# 横幅物料：仓库根目录 tc-promotion-banner-1200x400.png，经 static_files 复制到 docs/
TC_AD_IMG = "https://freelamp.com/tc-promotion-banner-1200x400.png"


def jd_buy_html(url: str, title: str = "", img: str = "") -> str:
    """生成文章底部「京东购买」CPS 推广卡片；url 为空时返回空串（不渲染）。
    提供 title+img 时渲染带商品图与标题的卡片，否则回退纯文字卡片。"""
    url = (url or "").strip()
    if not url:
        return ""
    title = (title or "").strip()
    img = (img or "").strip()
    href = url.replace('&', '&amp;')
    if title and img:
        t = html.escape(title)
        im = html.escape(img)
        return (
            '\n    <!-- 京东购买卡片（CPS 推广，带商品图） -->\n'
            '    <div class="buy-card buy-card-prod">\n'
            f'      <a class="buy-prod-img" href="{href}" target="_blank" rel="nofollow noopener sponsored" aria-hidden="true" tabindex="-1"><img src="{im}" alt="{t}" loading="lazy" decoding="async"></a>\n'
            '      <div class="buy-info">\n'
            '        <span class="buy-label">支持作者</span>\n'
            '        <div class="buy-text">本文有帮助？可看看下方这款相关商品，通过京东下单给作者一点小支持。</div>\n'
            f'        <div class="buy-prod-title">{t}</div>\n'
            '      </div>\n'
            f'      <a class="buy-btn" href="{href}" target="_blank" rel="nofollow noopener sponsored">京东购买 ↗</a>\n'
            '    </div>\n'
        )
    return (
        '\n    <!-- 京东购买卡片（CPS 推广） -->\n'
        '    <div class="buy-card">\n'
        '      <div class="buy-info">\n'
        '        <span class="buy-label">支持作者</span>\n'
        '        <div class="buy-text">本文有帮助？可通过京东下单相关书籍或商品，给作者一点小支持。</div>\n'
        '      </div>\n'
        f'      <a class="buy-btn" href="{href}" target="_blank" rel="nofollow noopener sponsored">京东购买 ↗</a>\n'
        '    </div>\n'
    )


def tc_ad_html() -> str:
    """生成腾讯云 CPS 推广横幅 div；TC_AD_URL 为空时返回空串（不插入）。"""
    url = (TC_AD_URL or "").strip()
    if not url:
        return ""
    t = html.escape((TC_AD_TITLE or "").strip())
    im = html.escape((TC_AD_IMG or "").strip())
    href = url.replace('&', '&amp;')
    return (
        '\n    <!-- 腾讯云 CPS 推广横幅 -->\n'
        '    <div class="tc-ad">\n'
        '      <span class="tc-ad-label">推广</span>\n'
        f'      <a href="{href}" target="_blank" rel="nofollow noopener sponsored" title="{t}">\n'
        f'        <img src="{im}" alt="{t}" loading="lazy" decoding="async">\n'
        '      </a>\n'
        '    </div>\n'
    )


# ================= 腾讯云 WorkBuddy footer 广告位（可选） =================
# 所有页面 footer 顶部插入推广条；WB_FOOTER_AD_URL 留空则全站不插入。
WB_FOOTER_AD_URL = "https://cloud.tencent.com/act/cps/redirect?redirect=6871&cps_key=67b706032429841cde38a5f27b3aca89&from=console&cps_promotion_id=103055"
WB_FOOTER_AD_TITLE = "【腾讯云】WorkBuddy 全场景 AI 办公工作台，团队旗舰版低至198元/月"
# 物料：仓库根目录 workbuddy-logo.jpg（800x800 方形 logo），经 static_files 复制到 docs/
WB_FOOTER_AD_IMG = "https://freelamp.com/workbuddy-logo.jpg"


def footer_ad_html() -> str:
    """生成 footer 腾讯云 WorkBuddy CPS 推广条（内联样式，自包含）；URL 为空时返回空串。"""
    url = (WB_FOOTER_AD_URL or "").strip()
    if not url:
        return ""
    t = html.escape((WB_FOOTER_AD_TITLE or "").strip())
    im = html.escape((WB_FOOTER_AD_IMG or "").strip())
    href = url.replace('&', '&amp;')
    return (
        '\n      <!-- 腾讯云 WorkBuddy CPS footer 推广条 -->\n'
        '      <div style="max-width:640px;margin:0 auto 22px;padding:12px 16px;'
        'border:1px solid #E5E7EB;border-radius:12px;background:#F9FAFB;'
        'display:flex;align-items:center;gap:12px;">\n'
        f'        <a href="{href}" target="_blank" rel="nofollow noopener sponsored" aria-hidden="true" tabindex="-1">'
        f'<img src="{im}" alt="" loading="lazy" decoding="async" '
        'style="width:44px;height:44px;border-radius:10px;object-fit:cover;flex-shrink:0;"></a>\n'
        f'        <a href="{href}" target="_blank" rel="nofollow noopener sponsored" title="{t}" '
        f'style="flex:1;min-width:0;color:#374151;text-decoration:none;font-size:13px;'
        f'font-weight:600;line-height:1.55;text-align:left;">{t}</a>\n'
        f'        <a href="{href}" target="_blank" rel="nofollow noopener sponsored" '
        'style="flex-shrink:0;padding:6px 14px;border-radius:999px;background:#059669;color:#fff;'
        'font-size:12px;font-weight:600;text-decoration:none;">了解详情 ↗</a>\n'
        '      </div>\n'
    )


# 预生成 footer 推广条 HTML，供四个页面模板的 footer 复用
WB_FOOTER_AD = footer_ad_html()


def inject_footer_ad(html_text: str) -> str:
    """把 footer 推广条插到单行 <footer> 标签前（用于导航页与公众号全文镜像页）。
    已含推广条或未配置 URL 时原样返回。"""
    ad = WB_FOOTER_AD.strip()
    if not ad or "<footer>" not in html_text or "WorkBuddy CPS footer" in html_text:
        return html_text
    return html_text.replace("<footer>", ad + "\n    <footer>", 1)


def inject_tc_ad(content_html: str) -> str:
    """在正文第一个 </blockquote> 后插入腾讯云推广横幅；无 blockquote 或未配置则原样返回。
    只插一次：多数 blockquote 是引言后的「译自…」来源注，插在其后位于正文上部；
    避免在多引用文章里重复堆叠广告。"""
    ad = tc_ad_html()
    if not ad:
        return content_html
    marker = '</blockquote>'
    idx = content_html.find(marker)
    if idx == -1:
        return content_html
    end = idx + len(marker)
    return content_html[:end] + ad + content_html[end:]


# ============ 三方交叉引用（网站 → 公众号 + B站）============
# 方案①（2026-09-29 用户确立）：只写渠道名，纯文本，不放可点击外链。
# 原因：微信公众号正文不能放可点击外链；B站简介外链权重极低且会拦截/降权。
# 网站是自己的站，可放真实链接。
WX_NAME = "LeisureLinux"                       # 公众号名
BILI_NAME = "LeisureLinux"                     # B站频道名
BILI_URL = "https://space.bilibili.com/517298151"

CROSS_REF_HTML = (
    '    <aside class="cross-ref" style="margin:40px 0 8px;padding:18px 20px;'
    'border:1px solid var(--border,#e5e7eb);border-radius:10px;'
    'background:var(--bg-soft,#fafafa);font-size:14px;line-height:1.9;color:var(--text-muted,#555);">\n'
    '      <p style="margin:0 0 6px;font-weight:600;color:var(--text,#222);">📌 本文同步发布于</p>\n'
    f'      <p style="margin:0;">微信公众号 <strong>{WX_NAME}</strong> ｜ '
    f'B站视频频道 <a href="{BILI_URL}" target="_blank" rel="noopener">{BILI_NAME}</a> '
    '（图文深度版与视频版同步更新）</p>\n'
    '    </aside>\n'
)


def inject_cross_ref(content_html: str) -> str:
    """在文章正文末尾插入「本文同步发布于」交叉引用块（幂等）。"""
    if 'class="cross-ref"' in content_html:
        return content_html
    return content_html + "\n" + CROSS_REF_HTML


# ================= 百度统计 (Baidu Tongji) 配置 =================
# 1) 打开 https://tongji.baidu.com/ 用百度账号登录，新增一个站点，
#    站点信息填：网站名称 + URL（https://freelamp.com 或 https://read.freelamp.com）。
# 2) 百度会生成一段统计代码，形如：
#      <script>
#      var _hmt = _hmt || [];
#      (function() {
#        var hm = document.createElement("script");
#        hm.src = "https://hm.baidu.com/hm.js?5c5bxxxxxxxxxxxxxxxxxxxxxxx";
#        ...
#      })();
#      </script>
# 3) 把 hm.js? 后面那串哈希值（HM 代码）填到下面的 BAIDU_TONGJI_ID。
#    留空（""）时不会输出任何统计脚本，站点保持纯净、不引入额外请求。
BAIDU_TONGJI_ID = "aa427f018a2cbb4f12e8b81eda96de51"

def analytics_html() -> str:
    """返回注入到每页 </head> 前的百度统计脚本（异步加载，不阻塞渲染）。
    未配置 BAIDU_TONGJI_ID 时返回空串。"""
    tid = (BAIDU_TONGJI_ID or "").strip()
    if not tid:
        return ""
    return (
        '  <!-- 百度统计（异步加载，不阻塞渲染） -->\n'
        '  <script>\n'
        '  var _hmt = _hmt || [];\n'
        '  (function() {\n'
        f'    var hm = document.createElement("script");\n'
        f'    hm.src = "https://hm.baidu.com/hm.js?{tid}";\n'
        '    var s = document.getElementsByTagName("script")[0];\n'
        '    s.parentNode.insertBefore(hm, s);\n'
        '  })();\n'
        '  </script>\n'
    )

# ============================================================
# HTML 模板 — 首页（含 SEO meta）
# ============================================================
INDEX_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{page_title}</title>
  <meta name="description" content="{page_description}">
  <meta name="keywords" content="Linux, 内核, DevSecOps, TLS, PKI, 网络安全, CVE, eBPF, systemd, SRE, 基础架构, DevOps">
  <meta name="author" content="{site_author}">
  <link rel="canonical" href="{canonical_url}">
  {rel_prev}{rel_next}
  <link rel="icon" type="image/x-icon" href="/favicon.ico">
  <link rel="alternate" type="application/rss+xml" title="FreeLAMP.com RSS 订阅" href="/rss.xml">

  <!-- Open Graph -->
  <meta property="og:type" content="website">
  <meta property="og:title" content="{page_title}">
  <meta property="og:description" content="{page_description}">
  <meta property="og:url" content="{canonical_url}">
  <meta property="og:image" content="{og_image}">
  <meta property="og:site_name" content="{site_name}">
  <meta property="og:locale" content="zh_CN">

  <!-- Twitter Card -->
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{page_title}">
  <meta name="twitter:description" content="{page_description}">
  <meta name="twitter:image" content="{og_image}">
  <meta name="twitter:site" content="@LeisureLinux">
  <meta name="twitter:creator" content="@LeisureLinux">

  <!-- JSON-LD 结构化数据：WebSite（站点名称；SearchAction 已由 Google 退役） -->
{website_json_ld}
  <!-- JSON-LD：ItemList（文章列表） -->
  <script type="application/ld+json">
  {item_list_json_ld}
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
    
    .site-intro {{
      background: #fff; border: 1px solid #E5E7EB; border-radius: 12px;
      padding: 20px 24px; margin-bottom: 24px; font-size: 14px; line-height: 1.9;
      color: #4B5563;
    }}
    .site-intro h2 {{ font-size: 18px; color: #111827; margin-bottom: 8px; }}
    .topic-nav {{ display: flex; flex-wrap: wrap; gap: 8px; margin-top: 14px; }}
    .topic-nav a {{
      background: #ECFDF5; color: #059669; padding: 5px 11px; border-radius: 999px;
      font-size: 12px; font-weight: 700; text-decoration: none;
    }}
    .topic-nav a:hover {{ background: #D1FAE5; }}
    .article-list {{ list-style: none; }}
    .article-item {{
      background: #fff; border-radius: 12px; padding: 24px 28px;
      background: #fff; border: 1px solid #E5E7EB; border-radius: 12px;
      padding: 20px 24px; margin-bottom: 24px; font-size: 14px; line-height: 1.9;
      color: #4B5563;
    }}
    .site-intro h2 {{ font-size: 18px; color: #111827; margin-bottom: 8px; }}
    .topic-nav {{ display: flex; flex-wrap: wrap; gap: 8px; margin-top: 14px; }}
    .topic-nav a {{
      background: #ECFDF5; color: #059669; padding: 5px 11px; border-radius: 999px;
      font-size: 12px; font-weight: 700; text-decoration: none;
    }}
    .topic-nav a:hover {{ background: #D1FAE5; }}
    .article-list {{ list-style: none; }}
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
{analytics_snippet}</head>
<body>
  <header>
    <div class="container">
      <h1><a href="/" style="color:#fff; text-decoration:none;">FreeLAMP.com：Linux 底层机制与 DevSecOps 知识库</a></h1>
      <p>像风一样自由 · 禅道须在生活中修，在日常言语、形式里面契合、印证</p>
      <div class="projects">
        <a class="project-btn" href="https://repo.freelamp.com" target="_blank" rel="noopener"><b>FreeLAMP Repo</b><span>FreeLAMP 代码仓库</span></a>
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
    <section class="site-intro">
      <h2>关于这个技术知识库</h2>
      <p>FreeLAMP.com 记录 Linux 内核、发行版、安全漏洞、TLS/PKI、自托管与开源工具的工程实践。文章以官方公告、源码与本地复现为依据，标注一手来源、版本范围与修订记录；同步发布于微信公众号「LeisureLinux」。</p>
      <h2>按主题浏览</h2>
      <nav class="topic-nav" aria-label="核心主题">
{topics_html}
      </nav>
    </section>
    <h2>最新文章</h2>
    <ul class="article-list">
{articles}
    </ul>
    {pager_html}
  </main>

  <footer>
    <div class="container">
{WB_FOOTER_AD}
      <p>© 2026 LeisureLinux · <a href="https://github.com/LeisureLinux/lore">GitHub</a> · <a href="/about-freelamp.html">关于 FreeLAMP</a> · <a href="/rss.xml">RSS 订阅</a> · <a href="/leisurelinux.html">LeisureLinux</a></p>
      <p style="margin-top: 8px; font-size: 12px;">本文以 <a href="https://creativecommons.org/licenses/by-sa/4.0/">CC BY-SA 4.0</a> 协议开源</p>
      <!-- 备案号占位:ICP 备案已按要求移除;需要时在此处加回 <p class="beian">…</p>
      公安备案号待补充:把下方链接里的 recordcode 与文案替换成实际值
      <a href="http://www.beian.gov.cn/portal/registerSystemInfo?recordcode=待补充" target="_blank" rel="nofollow" style="margin-left: 12px;">沪公网安备 待补充号</a>
      -->
    </div>
  </footer>

  <script>
    // 动态拉取 GitHub Discussions 评论数，显示到首页"参与讨论"按钮
    (function () {{
      var KEY = 'freelamp_discussions';
      var map = {{}};
      try {{ map = JSON.parse(localStorage.getItem(KEY) || '{{}}') || {{}}; }} catch (e) {{}}

      function norm(p) {{ return String(p || '').replace(/^[/]+|[/]+$/g, ''); }}

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
  <title>{title_html} | FreeLAMP.com</title>
  <meta name="description" content="{meta_description_html}">
  <meta name="keywords" content="{meta_keywords_html}">
  <meta name="author" content="{author_html}">
  <meta name="date" content="{date_iso_html}">
  <link rel="canonical" href="{canonical_url_html}">
  <link rel="icon" type="image/x-icon" href="/favicon.ico">

  <link rel="alternate" type="application/rss+xml" title="FreeLAMP.com RSS 订阅" href="/rss.xml">
  <!-- Open Graph：文章页 -->
  <meta property="og:type" content="article">
  <meta property="og:title" content="{title_html}">
  <meta property="og:description" content="{meta_description_html}">
  <meta property="og:url" content="{canonical_url_html}">
  <meta property="og:image" content="{og_image_html}">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="675">
  <meta property="og:site_name" content="{site_name_html}">
  <meta property="og:locale" content="zh_CN">
  <meta property="article:published_time" content="{date_iso_html}">
  <meta property="article:modified_time" content="{date_modified_html}">
  <meta property="article:author" content="{author_html}">
  <meta property="article:section" content="{article_section_html}">
  {og_tags}

  <!-- Twitter Card -->
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{title_html}">
  <meta name="twitter:description" content="{meta_description_html}">
  <meta name="twitter:image" content="{og_image_html}">
  <meta name="twitter:site" content="@LeisureLinux">
  <meta name="twitter:creator" content="@LeisureLinux">

  <!-- JSON-LD：TechArticle 结构化数据（SEO 核心） -->
  <script type="application/ld+json">
  {json_ld}
  </script>

  <!-- JSON-LD：BreadcrumbList 面包屑（由 json.dumps 生成，避免引号破坏） -->
  <script type="application/ld+json">
  {breadcrumb_json_ld}
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
    
    .buy-card {{
      display: flex; align-items: center; justify-content: space-between; gap: 16px;
      margin: 8px 0 24px; padding: 16px 20px;
      background: #FFF7F7; border: 1px solid #FFD9D9; border-radius: 12px;
    }}
    .buy-card .buy-label {{ color: #E6373A; font-weight: 600; font-size: 13px; }}
    .buy-card .buy-text {{ color: #6B7280; font-size: 13px; line-height: 1.6; margin-top: 4px; }}
    .buy-card .buy-btn {{
      flex-shrink: 0; display: inline-block; background: #E6373A; color: #fff;
      padding: 10px 18px; border-radius: 8px; font-size: 14px; font-weight: 600;
      text-decoration: none; white-space: nowrap;
    }}
    .buy-card .buy-btn:hover {{ background: #cf2c2f; }}
    .buy-card.buy-card-prod {{ align-items: stretch; }}
    .buy-prod-img {{
      flex-shrink: 0; display: block; width: 92px; height: 92px;
      border-radius: 8px; overflow: hidden; border: 1px solid #FFD9D9;
      background: #fff;
    }}
    .buy-prod-img img {{ width: 100%; height: 100%; object-fit: cover; display: block; }}
    .buy-info {{ flex: 1; min-width: 0; }}
    .buy-card .buy-prod-title {{
      margin-top: 6px; color: #111827; font-size: 13px; font-weight: 600;
      line-height: 1.5; display: -webkit-box; -webkit-line-clamp: 2;
      -webkit-box-orient: vertical; overflow: hidden;
    }}
    @media (max-width: 520px) {{
      .buy-card.buy-card-prod {{ flex-wrap: wrap; }}
      .buy-card.buy-card-prod .buy-btn {{ width: 100%; text-align: center; }}
    }}
    .tc-ad {{ margin: 20px 0 24px; }}
    .tc-ad .tc-ad-label {{
      display: block; text-align: right; font-size: 11px;
      color: #9CA3AF; line-height: 1; margin-bottom: 3px;
    }}
    .tc-ad a {{ display: block; border-radius: 8px; overflow: hidden; }}
    .tc-ad a:hover {{ opacity: 0.92; }}
    .tc-ad img {{
      width: 100%; height: auto; display: block;
      border: 1px solid #E5E7EB; border-radius: 8px; background: #fff;
    }}
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
{analytics_snippet}</head>
<body>
  <nav>
    <div class="container">
      <a class="brand" href="/">FreeLAMP.com 像风一样自由</a>
    </div>
  </nav>

  <main class="container">
    <article itemscope itemtype="https://schema.org/TechArticle">
      <div class="post-header">
        <div class="post-date" itemprop="datePublished" content="{date_iso_html}">{date}</div>
        <h1 class="post-title" itemprop="headline">{title_html}</h1>
        <div class="post-tags">{tags}</div>
        <meta itemprop="author" content="{author_html}">
        <meta itemprop="license" content="https://creativecommons.org/licenses/by-sa/4.0/">
      </div>

      <div class="post-content" itemprop="articleBody">
{content}
      </div>
    </article>
{jd_buy_html}

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
{WB_FOOTER_AD}
      <p>© 2026 LeisureLinux · <a href="https://github.com/LeisureLinux/lore">GitHub</a> · <a href="/about-freelamp.html">关于 FreeLAMP</a> · <a href="/rss.xml">RSS 订阅</a> · <a href="/leisurelinux.html">LeisureLinux</a></p>
      <p style="margin-top: 8px; font-size: 12px;">本文以 <a href="https://creativecommons.org/licenses/by-sa/4.0/">CC BY-SA 4.0</a> 协议开源</p>
      <!-- 备案号占位:ICP 备案已按要求移除;需要时在此处加回 <p class="beian">…</p>
      公安备案号待补充:把下方链接里的 recordcode 与文案替换成实际值
      <a href="http://www.beian.gov.cn/portal/registerSystemInfo?recordcode=待补充" target="_blank" rel="nofollow" style="margin-left: 12px;">沪公网安备 待补充号</a>
      -->
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
  <title>{title_html}</title>
  <link rel="alternate" type="application/rss+xml" title="FreeLAMP.com RSS 订阅" href="/rss.xml">
  <meta name="description" content="{description_html}">
{robots_meta}  <link rel="canonical" href="{canonical_url_html}">
  <meta property="og:type" content="website">
  <meta property="og:title" content="{title_html}">
  <meta property="og:description" content="{description_html}">
  <meta property="og:url" content="{canonical_url_html}">
  <meta property="og:image" content="{og_image_html}">
  <meta property="og:site_name" content="FreeLAMP.com">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{title_html}">
  <meta name="twitter:description" content="{description_html}">
  <meta name="twitter:image" content="{og_image_html}">
{collection_json_ld}  <style>
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
{analytics_snippet}</head>
<body>
  <nav>
    <div class="container">
      <a class="brand" href="/">FreeLAMP.com 像风一样自由</a>
    </div>
  </nav>

  <main class="container">
    <div class="tag-header">
      <h1>{tag_html} — FreeLAMP.com 技术文章</h1>
      <p>{intro_html}</p>
    </div>
    <ul class="article-list">
{articles}
    </ul>
  </main>

  <footer>
    <div class="container">
{WB_FOOTER_AD}
      <p>© 2026 LeisureLinux · <a href="https://github.com/LeisureLinux/lore">GitHub</a> · <a href="/about-freelamp.html">关于 FreeLAMP</a> · <a href="/rss.xml">RSS 订阅</a> · <a href="/leisurelinux.html">LeisureLinux</a></p>
      <p style="margin-top: 8px; font-size: 12px;">本文以 <a href="https://creativecommons.org/licenses/by-sa/4.0/">CC BY-SA 4.0</a> 协议开源</p>
      <!-- 备案号占位:ICP 备案已按要求移除;需要时在此处加回 <p class="beian">…</p>
      公安备案号待补充:把下方链接里的 recordcode 与文案替换成实际值
      <a href="http://www.beian.gov.cn/portal/registerSystemInfo?recordcode=待补充" target="_blank" rel="nofollow" style="margin-left: 12px;">沪公网安备 待补充号</a>
      -->
    </div>
  </footer>
</body>
</html>"""



# Markdown 渲染：实现在 tools/md_render.py（块级 + 行内两阶段解析）。
# 旧的实现是一串顺序正则替换，存在几个结构性问题：
#   - 图片前的多余 "!"（靠「链接规则先转成 <a>、再用正则换回 <img>」实现，必然漏字符）
#   - 代码块 / 行内代码里的 Markdown 标记被当成真语法处理
#   - 代码块里的 < > & 未转义
#   - 有序列表编号重复（<li>1. 第一</li>）
#   - 多级列表被拆散
#   - 表格单元格里 \| 转义竖线丢失
# 新的实现见 tools/md_render.py 的模块文档。
sys.path.insert(0, str(LORE_DIR / "tools"))
from md_render import markdown_to_html  # noqa: E402


def load_article(article_dir):
    """加载文章目录中的 Markdown 和 metadata"""
    article_md = article_dir / "article.md"
    metadata_yaml = article_dir / "metadata.yaml"
    
    if not article_md.exists():
        return None
    
    content = article_md.read_text(encoding='utf-8')

    # 剥离正文顶部的 YAML front matter。
    # 权威元数据一律以 metadata.yaml 为准；部分历史文章在 article.md 顶部
    # 冗余重复了一份 front matter，若不剥离会被当成正文渲染到页面上
    # （形如 <p>--- title: ... published: true ---</p>）。
    # 仅在开头确实是「--- 包裹、且内容能解析为 YAML 映射」时才剥离，
    # 避免误伤以水平线开头的正文。
    _fm = re.match(r'^\s*---[ \t]*\n(.*?)\n---[ \t]*$', content, re.S | re.MULTILINE)
    if _fm:
        try:
            _fm_data = yaml.safe_load(_fm.group(1))
        except Exception:
            _fm_data = None
        if isinstance(_fm_data, dict):
            content = content[_fm.end():].lstrip('\n')
    
    metadata = {}
    if metadata_yaml.exists():
        # 历史文件中有 195 个含多余 YAML 文档分隔符；safe_load 会在第一处
        # `---` 截断，因此按 `---` 分段解析，忽略空文档，避免后半段 tags 丢失。
        raw_yaml = metadata_yaml.read_text(encoding='utf-8')
        for chunk in re.split(r'^---\s*$', raw_yaml, flags=re.MULTILINE):
            if not chunk.strip():
                continue
            try:
                doc = yaml.safe_load(chunk)
            except yaml.YAMLError:
                continue
            if isinstance(doc, dict):
                metadata.update(doc)
    
    return {
        'slug': article_dir.name,
        'content': content,
        'metadata': metadata or {}
    }


def build_json_ld(meta, canonical_url, content_plain, og_image=None, date_modified=None):
    """生成 TechArticle JSON-LD 结构化数据（始终用 json.dumps 序列化）"""
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
        "dateModified": date_modified or meta.get('modified') or date_iso,
        "author": {
            "@type": "Organization",
            "name": SEO_AUTHOR_NAME,
            "url": SEO_AUTHOR_URL
        },
        "publisher": {
            "@type": "Organization",
            "name": SITE_NAME,
            "url": SITE_URL,
            "logo": {
                "@type": "ImageObject",
                "url": SEO_PUBLISHER_LOGO
            }
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
        schema["keywords"] = ", ".join(str(t) for t in tags)
        schema["about"] = [str(t) for t in tags[:5]]

    # 社交卡片 / 富媒体图片
    if og_image:
        schema["image"] = [og_image]

    # 一手来源与译介出处：技术文章 E-E-A-T 的重要信号
    citations = []
    for key in ('original_url', 'source_url'):
        url = str(meta.get(key) or '').strip()
        if url and url.startswith(('http://', 'https://')):
            citations.append({"@type": "CreativeWork", "url": url})
    source_name = str(meta.get('original_source') or '').strip()
    if source_name:
        for item in citations[:1]:
            item['name'] = source_name
    if citations:
        schema["citation"] = citations
    
    # 如果有 wechat_media_id，添加分发信息
    if meta.get('wechat_media_id'):
        schema["isPartOf"] = {
            "@type": "PublicationIssue",
            "issueNumber": meta.get('wechat_media_id', '')
        }
    
    return json.dumps(schema, ensure_ascii=False, indent=2)


def page_url(n):
    """返回第 n 页的绝对 URL（第 1 页即首页）"""
    if n <= 1:
        return f"{SITE_URL}/"
    return f"{SITE_URL}/page/{n}/"


def render_article_items(articles):
    """渲染一页文章列表的 <li>，同时返回对应 ItemList 结构（position 从 1 起）"""
    articles_html = []
    item_list_elements = []
    sorted_articles = sorted(articles, key=lambda x: str(x['metadata'].get('date', '') or ''), reverse=True)
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
        tag_links = []
        for tag in tags[:5]:
            tag_links.append(
                f'<a href="{tag_url_for(tag)}" aria-label="标签：{esc(tag)}">{esc(tag)}</a>'
            )
        tags_html = ''.join(tag_links)
        article_html = f"""      <li class="article-item">
        <a href="/articles/{slug}/">
          <div class="article-date">{esc(date)}</div>
          <div class="article-title">{esc(title)}</div>
          <div class="article-summary">{esc(summary)}</div>
        </a>
        <div class="article-tags">{tags_html}</div>
        <div class="article-meta">
          <a class="comment-link" href="/articles/{slug}/#comments" data-path="articles/{slug}/">💬 参与讨论</a>
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
    """渲染分页导航"""
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
    return f'<nav class="page-links">{" ".join(parts)}</nav>'


def build_index_pages(articles):
    """生成首页(index.html) + 分页页(page/N/index.html)，返回 [(相对路径, html), ...]"""
    sorted_articles = sorted(articles, key=lambda x: str(x['metadata'].get('date', '') or ''), reverse=True)
    total_pages = max(1, (len(sorted_articles) + PAGE_SIZE - 1) // PAGE_SIZE)
    pages = []
    # 首页主题导航只链接达到阈值的标签，避免制造薄标签入口
    indexable_tags = collect_indexable_tags(articles)
    topic_tags = list(indexable_tags)[:12]
    topics_html = '\n'.join(
        f'        <a href="{tag_url_for(tag)}">{esc(tag)}</a>' for tag in topic_tags
    )
    for page_num in range(1, total_pages + 1):
        start = (page_num - 1) * PAGE_SIZE
        slice_ = sorted_articles[start:start + PAGE_SIZE]
        articles_html, item_list_elements = render_article_items(slice_)
        item_list_json = json.dumps(item_list_elements, ensure_ascii=False, indent=6)
        pager_html = render_pager(page_num, total_pages)
        first_date = str(sorted_articles[start]['metadata'].get('date', '') or '')
        last_date = str(sorted_articles[min(start + PAGE_SIZE, len(sorted_articles)) - 1]['metadata'].get('date', '') or '')
        if page_num == 1:
            canonical_url = f"{SITE_URL}/"
            rel_prev = ''
            rel_next = f'<link rel="next" href="{page_url(2)}">' if total_pages > 1 else ''
            relpath = "index.html"
            page_title = "FreeLAMP.com — Linux 底层机制与 DevSecOps 技术知识库"
            page_description = (
                "FreeLAMP.com 记录 Linux 内核、发行版、安全漏洞、TLS/PKI、自托管与开源工具的"
                "工程实践；以官方公告、源码与本地复现为依据，附一手来源与版本细节。"
            )
        else:
            canonical_url = page_url(page_num)
            rel_prev = f'<link rel="prev" href="{page_url(page_num - 1)}">'
            rel_next = f'<link rel="next" href="{page_url(page_num + 1)}">' if page_num < total_pages else ''
            relpath = f"page/{page_num}/index.html"
            page_title = f"FreeLAMP.com 技术文章 · 第 {page_num} 页 — Linux / DevSecOps"
            page_description = (
                f"FreeLAMP.com 第 {page_num} 页技术文章归档，覆盖 {last_date} 至 {first_date} 的"
                " Linux、安全漏洞、PKI、自托管与开源工具解读。"
            )
        website_json_ld = ''
        if page_num == 1:
            website_schema = {
                "@context": "https://schema.org",
                "@type": "WebSite",
                "name": SITE_NAME,
                "url": f"{SITE_URL}/",
                "description": SITE_DESCRIPTION,
                "inLanguage": "zh-CN",
                "publisher": {
                    "@type": "Organization",
                    "name": SITE_NAME,
                    "url": SITE_URL,
                    "logo": {"@type": "ImageObject", "url": SEO_PUBLISHER_LOGO},
                },
            }
            website_json_ld = (
                '  <script type="application/ld+json">\n'
                + json.dumps(website_schema, ensure_ascii=False, indent=2)
                + '\n  </script>\n'
            )
        item_list_schema = {
            "@context": "https://schema.org",
            "@type": "ItemList",
            "name": f"FreeLAMP.com 技术文章 · 第 {page_num} 页",
            "itemListElement": item_list_elements,
        }
        item_list_json_ld = json.dumps(item_list_schema, ensure_ascii=False, indent=2)
        html = INDEX_TEMPLATE.format(
            WB_FOOTER_AD=WB_FOOTER_AD,
            analytics_snippet=analytics_html(),
            site_url=SITE_URL,
            site_name=SITE_NAME,
            site_description=SITE_DESCRIPTION,
            site_author=SITE_AUTHOR,
            page_title=esc(page_title),
            page_description=esc(page_description),
            og_image=esc(DEFAULT_OG_IMAGE),
            canonical_url=esc(canonical_url),
            rel_prev=rel_prev,
            rel_next=rel_next,
            articles='\n'.join(articles_html),
            topics_html=topics_html,
            website_json_ld=website_json_ld,
            item_list_json_ld=item_list_json_ld,
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

    tags_html = ''.join([
        f'<a itemprop="keywords" href="{tag_url_for(tag)}">{esc(tag)}</a>' for tag in tags
    ])

    # 去掉正文开头的重复标题（页面顶部 post-title 已展示标题）
    article_content = re.sub(r'^\s*#\s+[^\n]*\n?', '', article['content'], count=1, flags=re.MULTILINE)
    content_html = inject_tc_ad(markdown_to_html(article_content))
    content_html = inject_cross_ref(content_html)

    # 封面：metadata.cover 或 covers/<slug>.webp（WebP 源文件已纳入 git）
    cover_url = find_article_cover(article['slug'], meta) or ''
    if cover_url.startswith('http://') or cover_url.startswith('https://'):
        og_image = cover_url
    elif cover_url:
        og_image = f"{SITE_URL}{cover_url}"
    else:
        og_image = DEFAULT_OG_IMAGE

    # 生成 JSON-LD
    date_modified = str(meta.get('modified') or date_iso)
    json_ld = build_json_ld(meta, canonical_url, article['content'], og_image, date_modified)
    breadcrumb_schema = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "FreeLAMP.com", "item": f"{SITE_URL}/"},
            {"@type": "ListItem", "position": 2, "name": str(title), "item": canonical_url},
        ],
    }
    breadcrumb_json_ld = json.dumps(breadcrumb_schema, ensure_ascii=False, indent=2)

    # 生成 OG article:tag 标签（属性值必须转义）
    og_tags = '\n  '.join([
        f'<meta property="article:tag" content="{esc(tag)}">' for tag in tags
    ])

    # 确定文章分类（取第一个 tag）
    article_section = tags[0] if tags else "Linux"

    # meta description：独立 seo_description 优先，按句边界截断，避免英文专名被切断
    raw_description = (
        meta.get('seo_description') or meta.get('description') or meta.get('summary') or ''
    )
    if not raw_description:
        plain = re.sub(r'[#*`\[\]()>|]', '', article['content'])
        raw_description = re.sub(r'\n+', ' ', plain).strip()
    meta_description = truncate_seo_description(raw_description)
    
    # meta keywords
    meta_keywords = ", ".join(tags) if tags else "Linux, DevOps, 技术"
    
    # 京东购买卡片：优先文章 front-matter 的 jd_url/jd_title/jd_img，
    # 否则用全局默认 JD_BUY_URL/JD_BUY_TITLE/JD_BUY_IMG（均可留空）
    jd_url = (meta.get('jd_url') or JD_BUY_URL or '').strip()
    jd_title = (meta.get('jd_title') or JD_BUY_TITLE or '').strip()
    jd_img = (meta.get('jd_img') or JD_BUY_IMG or '').strip()

    return ARTICLE_TEMPLATE.format(
        WB_FOOTER_AD=WB_FOOTER_AD,
        analytics_snippet=analytics_html(),
        jd_buy_html=jd_buy_html(jd_url, jd_title, jd_img),
        title_html=esc(title),
        date=esc(date_display),
        date_iso_html=esc(date_iso),
        date_modified_html=esc(date_modified),
        tags=tags_html,
        content=content_html,
        canonical_url_html=esc(canonical_url),
        json_ld=json_ld,
        breadcrumb_json_ld=breadcrumb_json_ld,
        author_html=esc(author),
        site_url=SITE_URL,
        site_name_html=esc(SITE_NAME),
        meta_description_html=esc(meta_description),
        meta_keywords_html=esc(meta_keywords),
        article_section_html=esc(article_section),
        og_image_html=esc(og_image),
        og_tags=og_tags,
        share_url=json.dumps(canonical_url),
        share_title=json.dumps(str(title))
    )


def build_tag_pages(articles):
    """只为达到文章数阈值的标签生成 /tags/<slug>/ 索引页。

    低于阈值的细粒度标签仍显示在文章页，但不再生成独立 URL / sitemap 条目。
    标签目录采用 slug 化单层路径，并为保留页输出 CollectionPage + ItemList JSON-LD。
    """
    tag_map = collect_tag_map(articles)
    written = []
    for tag, tagged_articles in tag_map.items():
        tag_url = tag_url_for(tag)
        rel_dir = tag_disk_dir(tag)
        indexable = len(tagged_articles) >= MIN_TAG_PAGE_ARTICLES
        items = []
        item_list_elements = []
        for idx, article in enumerate(sorted(tagged_articles, key=lambda x: str(x['metadata'].get('date', '') or ''), reverse=True), 1):
            meta = article['metadata']
            article_slug = article['slug']
            date = meta.get('date', '')
            if isinstance(date, datetime):
                date = date.strftime('%Y-%m-%d')
            title = meta.get('title', article_slug)
            summary = meta.get('summary', '')
            items.append(f"""      <li class="article-item">
        <a href="/articles/{article_slug}/">
          <div class="article-date">{esc(date)}</div>
          <div class="article-title">{esc(title)}</div>
          <div class="article-summary">{esc(summary)}</div>
        </a>
      </li>""")
            item_list_elements.append({
                "@type": "ListItem",
                "position": idx,
                "name": str(title),
                "url": f"{SITE_URL}/articles/{article_slug}/",
            })
        page_title = f"{tag} — FreeLAMP.com 技术文章专题"
        page_description = (
            f"「{tag}」专题收录 {len(tagged_articles)} 篇 FreeLAMP.com 技术文章，"
            "覆盖相关漏洞、版本变化、配置实践与工程复盘，附文章来源与发布时间。"
        )
        intro_html = (
            f"本专题汇总 {len(tagged_articles)} 篇与「{esc(tag)}」相关的 FreeLAMP.com 文章，"
            "按发布时间排列；点击标题查看完整分析、官方来源与复现细节。"
        )
        canonical_url = f"{SITE_URL}{tag_url}"
        robots_meta = '' if indexable else '  <meta name="robots" content="noindex,follow">\n'
        collection_json_ld = ''
        if indexable:
            collection_schema = {
                "@context": "https://schema.org",
                "@type": "CollectionPage",
                "name": page_title,
                "description": page_description,
                "url": canonical_url,
                "inLanguage": "zh-CN",
                "isPartOf": {"@type": "WebSite", "name": SITE_NAME, "url": f"{SITE_URL}/"},
                "mainEntity": {
                    "@type": "ItemList",
                    "numberOfItems": len(item_list_elements),
                    "itemListElement": item_list_elements,
                },
            }
            collection_json_ld = (
                '  <script type="application/ld+json">\n'
                + json.dumps(collection_schema, ensure_ascii=False, indent=2)
                + '\n  </script>\n'
            )
        else:
            # 薄标签页保留文章链接供爬虫发现正文，但不声明结构化专题
            item_list_elements = []
        html = TAG_TEMPLATE.format(
            WB_FOOTER_AD=WB_FOOTER_AD,
            analytics_snippet=analytics_html(),
            title_html=esc(page_title),
            description_html=esc(page_description),
            canonical_url_html=esc(canonical_url),
            og_image_html=esc(DEFAULT_OG_IMAGE),
            robots_meta=robots_meta,
            collection_json_ld=collection_json_ld,
            tag_html=esc(tag),
            intro_html=intro_html,
            articles='\n'.join(items),
        )
        out_dir = DOCS_DIR / "tags" / rel_dir
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "index.html").write_text(html, encoding='utf-8')
        assert out_dir.resolve().is_relative_to((DOCS_DIR / 'tags').resolve()), tag

        # 含斜杠的旧标签 URL（如 /tags/AI/LLM/）保留一个轻量跳转页，
        # 避免已收录/外链 URL 变成 404；新 URL 进 canonical 与 sitemap。
        if '/' in str(tag):
            legacy_dir = DOCS_DIR / "tags" / str(tag)
            legacy_dir.mkdir(parents=True, exist_ok=True)
            legacy_html = (
                '<!DOCTYPE html>\n<html lang="zh-CN">\n<head>\n'
                '  <meta charset="UTF-8">\n'
                f'  <meta http-equiv="refresh" content="0;url={esc(tag_url)}">\n'
                '  <meta name="robots" content="noindex,follow">\n'
                f'  <link rel="canonical" href="{esc(canonical_url)}">\n'
                f'  <title>{esc(tag)} — 页面已迁移</title>\n'
                '</head>\n<body>\n'
                f'  <p>本标签页已迁移到 <a href="{esc(tag_url)}">{esc(canonical_url)}</a>。</p>\n'
                '</body>\n</html>\n'
            )
            (legacy_dir / "index.html").write_text(legacy_html, encoding='utf-8')
        if indexable:
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

def generate_sitemap(articles, tag_urls=None, mirror_urls=None):
    """生成 sitemap.xml：文章/分页/合格标签 + 可选的公众号全文镜像。"""
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
    for article in sorted(articles, key=lambda x: str(x['metadata'].get('date', '') or ''), reverse=True):
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

    # 标签目录页：只包含 build_tag_pages() 真正生成、达到阈值的专题页
    for tag_url in (tag_urls or []):
        urls.append({
            'loc': f"{SITE_URL}{tag_url}",
            'changefreq': 'weekly',
            'priority': '0.6'
        })

    # LeisureLinux 公众号全文镜像页（GEO：让 Bot 能发现并抓取全文）
    for mirror_url in (mirror_urls or []):
        urls.append({
            'loc': f"{SITE_URL}{mirror_url['loc']}",
            'lastmod': mirror_url.get('lastmod'),
            'changefreq': 'monthly',
            'priority': '0.5'
        })

    # 构建 XML
    xml_lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
    ]
    
    for url_entry in urls:
        xml_lines.append('  <url>')
        xml_lines.append(f'    <loc>{url_entry["loc"]}</loc>')
        if url_entry.get('lastmod'):
            xml_lines.append(f'    <lastmod>{_xml_escape(url_entry["lastmod"])}</lastmod>')
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
      "name": "FreeLAMP.com / LeisureLinux",
      "alternateName": ["FreeLAMP.com", "LeisureLinux", "老徐"],
      "url": "{site_url}/about-freelamp.html",
      "email": "albertxu@freelamp.com",
      "knowsAbout": ["Linux", "自由软件", "开源", "系统管理", "DevSecOps"],
      "sameAs": [
        "https://github.com/LeisureLinux",
        "{site_url}/",
        "https://space.bilibili.com/517298151"
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
{analytics_snippet}</head>
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
      <h2>五、关注与联系方式</h2>
      <ul>
        <li>微信公众号：<strong>LeisureLinux</strong>（搜索关注，深度技术图文）</li>
        <li>B站视频频道：<a href="https://space.bilibili.com/517298151">LeisureLinux</a>（同名视频版）</li>
        <li>GitHub：<a href="https://github.com/LeisureLinux">LeisureLinux</a></li>
        <li>博客：<a href="{site_url}/">https://freelamp.com/</a></li>
        <li>RSS 订阅：<a href="{site_url}/rss.xml">rss.xml</a></li>
      </ul>
      <p>自我的觉醒却是光阴偷不走，人拿不走的。愿我们永远保持对技术的热爱与自由。🕊️</p>

    </article>
  </main>

  <footer>
    <div class="container">
{WB_FOOTER_AD}
      <p>© 2026 LeisureLinux · <a href="https://github.com/LeisureLinux/lore">GitHub</a> · <a href="/about-freelamp.html">关于 FreeLAMP</a> · <a href="/rss.xml">RSS 订阅</a> · <a href="/leisurelinux.html">LeisureLinux</a></p>
      <p style="margin-top: 8px; font-size: 12px;">本文以 <a href="https://creativecommons.org/licenses/by-sa/4.0/">CC BY-SA 4.0</a> 协议开源</p>
      <!-- 备案号占位:ICP 备案已按要求移除;需要时在此处加回 <p class="beian">…</p>
      公安备案号待补充:把下方链接里的 recordcode 与文案替换成实际值
      <a href="http://www.beian.gov.cn/portal/registerSystemInfo?recordcode=待补充" target="_blank" rel="nofollow" style="margin-left: 12px;">沪公网安备 待补充号</a>
      -->
    </div>
  </footer>
</body>
</html>"""


def build_about_page():
    """生成「关于 FreeLAMP」页面（网站历史 + 作者介绍）"""
    return ABOUT_TEMPLATE.format(
        WB_FOOTER_AD=WB_FOOTER_AD,
        analytics_snippet=analytics_html(),
        site_url=SITE_URL,
        site_name=SITE_NAME,
        site_author=SITE_AUTHOR,
    )



def discover_mirror_urls():
    """扫描公众号全文镜像页，提取 sitemap 所需的路径与 lastmod。"""
    src = LORE_DIR / "leisurelinux" / "articles"
    entries = []
    if not src.is_dir():
        return entries
    for f in sorted(src.glob('*.html')):
        text = f.read_text(encoding='utf-8', errors='ignore')
        m = re.search(r'"datePublished"\s*:\s*"(\d{4}-\d{2}-\d{2})', text)
        entries.append({
            'loc': f"/leisurelinux/articles/{f.name}",
            'lastmod': m.group(1) if m else None,
        })
    return entries


def validate_generated_html():
    """遍历 docs/**/*.html，校验 meta 属性与 JSON-LD；返回错误列表。"""
    from html.parser import HTMLParser

    class Validator(HTMLParser):
        def __init__(self, rel):
            super().__init__(convert_charrefs=True)
            self.rel = rel
            self.errors = []
            self.in_ld = False
            self.ld_buf = []
            self.metas = {}

        def handle_starttag(self, tag, attrs):
            d = dict(attrs)
            if tag == 'meta':
                key = d.get('name') or d.get('property')
                if key and 'content' not in d:
                    self.errors.append(f"{self.rel}: <meta {key}> 缺 content")
                if key in ('description', 'og:title', 'twitter:title'):
                    self.metas[key] = d.get('content', '')
            if tag == 'script' and d.get('type', '').lower() == 'application/ld+json':
                self.in_ld = True
                self.ld_buf = []

        def handle_data(self, data):
            if self.in_ld:
                self.ld_buf.append(data)

        def handle_endtag(self, tag):
            if tag == 'script' and self.in_ld:
                self.in_ld = False
                raw = ''.join(self.ld_buf).strip()
                if raw:
                    try:
                        json.loads(raw)
                    except Exception as exc:
                        self.errors.append(f"{self.rel}: JSON-LD 解析失败 {exc}")
            if tag == 'head':
                for key in ('og:title', 'twitter:title'):
                    v = self.metas.get(key, '')
                    if v and len(v) < 8:
                        self.errors.append(f"{self.rel}: {key} 疑似被截断：{v!r}")

    errors = []
    for f in sorted(DOCS_DIR.rglob('*.html')):
        rel = f.relative_to(DOCS_DIR).as_posix()
        if rel == 'googlec29651f57d804644.html':
            continue  # Google 站点验证文件刻意保持极简
        v = Validator(rel)
        try:
            v.feed(f.read_text(encoding='utf-8', errors='ignore'))
        except Exception as exc:
            errors.append(f"{rel}: HTML 解析异常 {exc}")
        errors.extend(v.errors)
    return errors


def main():
    import shutil
    print("🔨 开始构建 FreeLAMP.com 静态站点...")
    
    # 清理 docs 目录
    if DOCS_DIR.exists():
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
    
    # 生成标签页：全部历史 URL 保留；仅合格专题返回到 sitemap
    tag_urls = build_tag_pages(articles)
    print(f"✅ 生成标签页：{len(tag_urls)} 个可索引专题（阈值 ≥{MIN_TAG_PAGE_ARTICLES} 篇），薄标签页已标记 noindex,follow")

    # 生成 sitemap.xml（含标签专题 + 公众号全文镜像）
    mirror_urls = discover_mirror_urls()
    sitemap_xml = generate_sitemap(articles, tag_urls, mirror_urls)
    (DOCS_DIR / "sitemap.xml").write_text(sitemap_xml, encoding='utf-8')
    print("✅ 生成站点地图：docs/sitemap.xml")
    
    # 生成 rss.xml
    rss_xml = generate_rss(articles)
    (DOCS_DIR / "rss.xml").write_text(rss_xml, encoding='utf-8')
    print("✅ 生成 RSS 订阅：docs/rss.xml")
    
    # 复制已有 WebP 封面到 docs/covers/（CI 无需 Pillow）
    src_covers = LORE_DIR / "covers"
    dst_covers = DOCS_DIR / "covers"
    dst_covers.mkdir(parents=True, exist_ok=True)
    copied_covers = 0
    if src_covers.is_dir():
        for f in src_covers.glob('*.webp'):
            shutil.copy2(f, dst_covers / f.name)
            copied_covers += 1
    print(f"✅ 复制文章封面：docs/covers/（{copied_covers} 张 WebP）")

    # 生成 robots.txt（本次 P1 不改内容；线上 Cloudflare 托管策略由用户复核）
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
        "leisurelinux-qrcode.jpeg",  # LeisureLinux 公众号关注二维码
        "jd_root.txt",  # 京东联盟域名验证
        "jd-aohan-xiaomi.jpg",  # 京东购买卡片商品图（农合天下敖汉黄小米）
        "tc-promotion-banner-1200x400.png",  # 腾讯云 CPS 推广横幅（双十一大促）
        "workbuddy-logo.jpg",  # 腾讯云 WorkBuddy CPS footer 推广条 logo
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

    # 复制各文章目录内的静态资源（图片/SVG 等），供文章内相对路径引用
    copied_assets = 0
    asset_exts = {'.svg', '.png', '.jpg', '.jpeg', '.gif', '.webp'}
    for article_dir in ARTICLES_DIR.iterdir():
        if not article_dir.is_dir() or article_dir.name.startswith('.'):
            continue
        dst_dir = DOCS_DIR / "articles" / article_dir.name
        if not dst_dir.is_dir():
            continue
        for f in article_dir.iterdir():
            if f.is_file() and f.suffix.lower() in asset_exts:
                shutil.copy2(f, dst_dir / f.name)
                copied_assets += 1
        # ⭐ 递归复制文章内的子目录资源（如 images/），保持相对路径 images/xxx.png 可用
        for sub in article_dir.iterdir():
            if not sub.is_dir() or sub.name.startswith('.'):
                continue
            sub_dst = dst_dir / sub.name
            if sub_dst.exists():
                shutil.rmtree(sub_dst)
            shutil.copytree(sub, sub_dst)
            copied_assets += sum(1 for _ in sub_dst.rglob('*') if _.is_file())
    if copied_assets:
        print(f"✅ 复制文章内静态资源：{copied_assets} 个文件（svg/图片）")

    # 复制 LeisureLinux 公众号导航页（若存在）到 docs/，使其在站点中可访问
    import shutil as _shutil
    src_nav = LORE_DIR / "leisurelinux.html"
    if src_nav.exists():
        nav_text = src_nav.read_text(encoding="utf-8")
        (DOCS_DIR / "leisurelinux.html").write_text(
            inject_footer_ad(nav_text), encoding="utf-8")
        print("✅ 复制导航页：docs/leisurelinux.html（含 footer 推广条）")
        total_files += 1
    else:
        print("ℹ️  未找到 lore/leisurelinux.html，跳过导航页复制（运行更新脚本后会生成）")

    # 复制公众号全文镜像页目录（若有）到 docs/，供 Bot 抓取（GEO 全文可读）
    src_art = LORE_DIR / "leisurelinux" / "articles"
    if src_art.is_dir():
        dst_art = DOCS_DIR / "leisurelinux" / "articles"
        if dst_art.exists():
            _shutil.rmtree(dst_art)
        _shutil.copytree(src_art, dst_art)
        cnt = 0
        for p in dst_art.glob("*.html"):
            p.write_text(inject_footer_ad(p.read_text(encoding="utf-8")),
                         encoding="utf-8")
            cnt += 1
        print(f"✅ 复制全文镜像页：docs/leisurelinux/articles/（{cnt} 篇，含 footer 推广条）")
        total_files += cnt
    else:
        print("ℹ️  未找到 lore/leisurelinux/articles/，跳过全文镜像页复制（运行 build_articles.py 后会生成）")

    # 构建后自检：HTML meta 可解析、所有 JSON-LD 可被 json.loads
    errors = validate_generated_html()
    if errors:
        print("\n❌ 构建自检失败：", file=sys.stderr)
        for err in errors[:20]:
            print(f"  - {err}", file=sys.stderr)
        sys.exit(1)
    print("✅ 构建自检通过：meta 属性与 JSON-LD 均可解析")

    print(f"\n🎉 构建完成！共生成 {total_files} 个文件（含 SEO/GEO 优化）")


if __name__ == "__main__":
    main()
