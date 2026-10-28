# -*- coding: utf-8 -*-
"""从 lore 文章的 article.md 自动生成公众号「石墨极简风」HTML。

为什么存在这个脚本
------------------
仓库里有两条公众号排版路线：

1. ``wechat-articles/_build_<slug>.py`` —— 手写 spec（含 lead / nav / sections /
   facts / closer / related），交给 ``_gzh_graphite.build(cfg)`` 渲染。
   优点：排版最贴合官方主题；缺点：**每篇都要手写上千行**，容易漏引号、
   串稿（本号曾因此发生过 OpenBSD Wine 文章里混入 HackiOS 功能表的串稿）。

2. 本脚本 —— 从 ``article.md`` 自动解析出 spec，再交给**同一个**
   ``_gzh_graphite.build(cfg)`` 渲染。
   优点：零手写、不会串稿、与文章正文严格一致；缺点：排版是「自动」的，
   没有人工微调的余地。

关键设计：**渲染层完全复用官方主题**（``_gzh_graphite.build``），
本脚本只负责「Markdown → spec」。所以样式不会随时间漂移 ——
这与早期那个手搓 HTML 的临时版本有本质区别。

用法
----
命令行::

    python3 lore/tools/md2gzh.py <article.md> [-o 输出.html] [--spec spec.json]

也可以在 Python 里当库用::

    from md2gzh import build_from_article
    html = build_from_article(
        "articles/<slug>/article.md",
        "gzh/<slug>/排版_石墨极简风(graphite-minimal).html",
        quote="...", quote_by="...",
        facts=[("项目", "内容"), ...],
        related=["相关文章标题", ...],
        closer="结尾金句",
    )

``facts`` / ``quote`` / ``closer`` 这几项**必须人工给** ——
它们是文章的「观点提要」，Markdown 原文里没有可靠的对应物，
自动猜出来的质量还不如不写。

代码块与表格
------------
石墨主题的官方 ``_gzh_graphite.py`` 只实现了 p / h3 / quote / note / ul
五种 block，**没有代码块，也没有通用表格**。但文章里这两种元素很常见
（尤其技术文章）。本脚本为它们提供了符合主题规范的实现：

- 代码块：按 ``gzh-design-skill/references/common-components.md`` 的
  「1a 深色代码块」实现 —— 顶栏三色圆点 + 语言名，
  **每行代码一个 ``<p style="margin:0">``**，缩进用全角空格（不用 ``white-space:pre``）。
- 表格：按 ``theme-graphite-minimal.md`` 的「组件 12 表格」实现 ——
  偶数行极浅灰底（``#FAFAFA``）。

为了让这两个 block 能走官方渲染路径，本脚本**运行时给 ``_gzh_graphite``
动态注册** ``code`` / ``table`` 两种 kind（不修改源文件）。
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
WRITINGS = os.path.dirname(os.path.dirname(HERE))
WECHAT_DIR = os.path.join(WRITINGS, "wechat-articles")

if WECHAT_DIR not in sys.path:
    sys.path.insert(0, WECHAT_DIR)

import _gzh_graphite as G  # noqa: E402


# ============================================================
# 1. 主题扩展：给官方渲染器补上 code / table 两种 block
# ============================================================

_CODE_COLORS = {"#FF5F56", "#FFBD2E", "#27C93F"}


def _code_block(body, lang=""):
    """石墨主题「1a 深色代码块」。

    规范要点（common-components.md）：
    - 每行代码一个 ``<p style="margin:0">``，**不用 white-space:pre**
    - 缩进用全角空格，因为源码空格会被原样渲染成大左缩进
    - 顶栏三色圆点 + 语言名（无语言可删）
    """
    lines = body.split("\n")
    # 去掉首尾空行
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    if not lines:
        return ""

    dots = "".join(
        f'<span style="display:inline-block;width:10px;height:10px;border-radius:50%;'
        f'background:{c};margin-right:7px;font-size:0;line-height:0;overflow:hidden;">.</span>'
        for c in _CODE_COLORS
    )
    lang_span = ""
    if lang:
        lang_span = (
            f'<span style="margin-left:12px;font-size:12px;color:#64748B;'
            f'font-family:Consolas,Monaco,monospace;letter-spacing:1px;">'
            f'{G.leaf(G.esc(lang))}</span>'
        )

    code_lines = []
    for ln in lines:
        # 源码里的普通空格缩进 → 全角空格，避免渲染出大左缩进
        stripped = ln.lstrip(" ")
        indent = len(ln) - len(stripped)
        text = "　" * indent + stripped
        text = text.replace("\t", "　")
        code_lines.append(
            f'      <p style="margin:0;font-family:\'SF Mono\',Consolas,Monaco,monospace;'
            f'font-size:13px;line-height:1.6;color:#E2E8F0;">{G.leaf(G.esc(text))}</p>\n'
        )

    return (
        f'    <section style="margin:0 0 20px;border-radius:8px;overflow:hidden;'
        f'background:#1E293B;box-shadow:0 4px 16px -8px rgba(15,23,42,0.4);">\n'
        f'      <section style="display:flex;align-items:center;padding:9px 14px;background:#0F172A;">\n'
        f'        {dots}{lang_span}\n'
        f'      </section>\n'
        f'      <section style="padding:11px 14px;">\n'
        + "".join(code_lines) +
        f'      </section>\n'
        f'    </section>\n'
    )


def _table_block(rows):
    """石墨主题「组件 12 表格」—— 偶数行极浅灰底。

    ⚠️ 与官方 ``table_block`` 同名但用途不同：官方那个是**两列**的
    「关键事实速查」专用表（带 KEY FACTS 标签）。这个是**通用**表格，
    支持任意列数，用于正文里的 Markdown 表格。
    所以在扩展模块里把它改名为 ``md_table_block``，避免覆盖官方版本。
    """
    if not rows:
        return ""
    hdr = rows[0]
    body = rows[1:]
    ncols = max(len(r) for r in rows)

    ths = "".join(
        f'          <th style="background:#27272A;color:#fff;font-weight:700;'
        f'padding:8px 12px;text-align:left;">{G.leaf(G.esc(c))}</th>\n'
        for c in (hdr + [""] * (ncols - len(hdr)))
    )
    trs = []
    for i, r in enumerate(body):
        bg = 'background:#FAFAFA;' if i % 2 == 1 else ''
        tds = "".join(
            f'        <td style="padding:8px 12px;border-bottom:1px solid #E4E4E7;'
            f'color:#52525B;{bg}vertical-align:top;">{G.render_inline(c)}</td>\n'
            for c in (r + [""] * (ncols - len(r)))
        )
        trs.append(f"      <tr>\n{tds}      </tr>\n")

    return (
        f'    <section style="margin:0 10px 24px;overflow-x:auto;">\n'
        f'      <table style="width:100%;border-collapse:collapse;font-size:14px;">\n'
        f'        <thead>\n          <tr>\n{ths}          </tr>\n        </thead>\n'
        f'        <tbody>\n' + "".join(trs) + f'        </tbody>\n'
        f'      </table>\n    </section>\n'
    )


def _ol_block(items):
    """有序列表（石墨圆标编号）。"""
    if not items:
        return ""
    ps = "".join(
        f'      <p style="margin:0 0 8px;font-size:15px;line-height:1.8;color:{G.GREY};'
        f'text-align:justify;">'
        f'<span style="color:{G.DARK};font-weight:800;">{i + 1}.</span> '
        f'{G.render_inline(t)}</p>\n'
        for i, t in enumerate(items)
    )
    return f'    <section style="margin:0 0 24px;padding-left:4px;">\n{ps}    </section>\n'


def _h4_block(text):
    return (
        f'    <p style="font-size:14px;font-weight:700;color:{G.MID};margin:22px 0 10px;">'
        f'{G.render_inline(text)}</p>\n'
    )


def _install_theme_extensions():
    """给官方 ``_gzh_graphite.build()`` 动态补上 code / table / ol / h4 四种 block。

    做法：读入官方源码，在 build() 的 kind 分支里插入处理，再 exec 成新模块。
    这样**渲染逻辑（样式、分节、END、签名等）全部来自官方主题**，
    本脚本只负责「Markdown → spec」和这几个缺失组件。

    不修改 ``_gzh_graphite.py`` 本体。
    """
    import types

    src = open(os.path.join(WECHAT_DIR, "_gzh_graphite.py"), encoding="utf-8").read()

    anchor = """            elif kind == 'ul':
                o.append(ul_block(payload))"""
    if anchor not in src:
        raise RuntimeError(
            "无法定位 _gzh_graphite.build 的 ul 分支 —— 主题文件结构可能已变化，"
            "需要更新 lore/tools/md2gzh.py 的扩展注入点")

    injected = anchor + """
            elif kind == 'code':
                o.append(code_block(payload))
            elif kind == 'table':
                o.append(md_table_block(payload))
            elif kind == 'ol':
                o.append(ol_block(payload))
            elif kind == 'h4':
                o.append(h4_block(payload))"""

    src = src.replace(anchor, injected, 1)

    mod = types.ModuleType("_gzh_graphite_ext")
    mod.__dict__.update(G.__dict__)
    mod.code_block = _code_block
    mod.md_table_block = _table_block
    mod.ol_block = _ol_block
    mod.h4_block = _h4_block
    mod.__dict__["__file__"] = os.path.join(WECHAT_DIR, "_gzh_graphite.py")

    exec(compile(src, mod.__dict__["__file__"], "exec"), mod.__dict__)

    # ⚠️ exec 重新定义了官方的 table_block（两列版），会覆盖我们注入的三件套。
    # 所以要在 exec 之后重新挂回去。注意我们注入的是 ``md_table_block``，
    # 官方两列版 ``table_block`` 保持不动（关键事实速查表要用它）。
    mod.code_block = _code_block
    mod.md_table_block = _table_block
    mod.ol_block = _ol_block
    mod.h4_block = _h4_block
    return mod


# 扩展后的主题模块（延迟构建，避免 import 时的副作用）
_EXT = None


def theme():
    """返回带 code/table/ol/h4 支持的主题模块。"""
    global _EXT
    if _EXT is None:
        _EXT = _install_theme_extensions()
    return _EXT


# ============================================================
# 2. Markdown 解析
# ============================================================

RE_FENCE = re.compile(r"^```(\w*)\s*$")
RE_H = re.compile(r"^(#{1,6})\s+(.*)$")
RE_UL = re.compile(r"^\s*[-*+]\s+(.*)$")
RE_OL = re.compile(r"^\s*\d+[.)]\s+(.*)$")
RE_HR = re.compile(r"^-{3,}\s*$")


def parse_markdown(md):
    """把 Markdown 解析成 block 列表。

    返回的 block 是 ``(kind, payload)``，kind ∈
    ``p / h3 / h4 / quote / note / ul / ol / code / table / hr``。

    约定：
    - ``> `` 开头 → quote
    - 以 ``**⭐`` 或 ``⚠️`` 开头的段落 → note（石墨主题的「辅助竖条旁注」）
    - 表格 → table
    """
    lines = md.split("\n")
    blocks = []
    i = 0
    buf = []

    def flush():
        """段落落盘：⭐ / ⚠️ 开头的段落归为 note（石墨主题的辅助竖条旁注）。"""
        if not buf:
            return
        t = "\n".join(buf).strip()
        buf.clear()
        if not t:
            return
        if re.match(r"^[⭐⚠️★☆]\s*", t) or re.match(r"^\*\*[⭐⚠️★☆]", t):
            blocks.append(("note", t))
        else:
            blocks.append(("p", t))

    while i < len(lines):
        line = lines[i]
        s = line.strip()

        # 代码块
        m = RE_FENCE.match(s)
        if m:
            flush()
            lang = m.group(1)
            i += 1
            code = []
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code.append(lines[i])
                i += 1
            i += 1
            blocks.append(("code", "\n".join(code)))
            continue

        # 标题
        m = RE_H.match(s)
        if m:
            flush()
            level = len(m.group(1))
            text = m.group(2).strip()
            if level <= 3:
                blocks.append(("h3", text))
            else:
                blocks.append(("h4", text))
            i += 1
            continue

        # 分割线
        if RE_HR.match(s):
            flush()
            blocks.append(("hr", ""))
            i += 1
            continue

        # 引用
        if s.startswith(">"):
            flush()
            q = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                q.append(re.sub(r"^>\s?", "", lines[i]).rstrip())
                i += 1
            blocks.append(("quote", "\n".join(q).strip()))
            continue

        # 无序列表
        if RE_UL.match(line):
            flush()
            items = []
            while i < len(lines) and RE_UL.match(lines[i]):
                items.append(RE_UL.match(lines[i]).group(1).strip())
                i += 1
            blocks.append(("ul", items))
            continue

        # 有序列表
        if RE_OL.match(line):
            flush()
            items = []
            while i < len(lines) and (RE_OL.match(lines[i]) or
                                      (items and lines[i].strip() and not RE_UL.match(lines[i]) and
                                       lines[i].startswith("  "))):
                mm = RE_OL.match(lines[i])
                if mm:
                    items.append(mm.group(1).strip())
                elif items:
                    items[-1] += " " + lines[i].strip()
                i += 1
            blocks.append(("ol", items))
            continue

        # 表格
        if s.startswith("|") and i + 1 < len(lines) and \
                re.match(r"^\|[\s:|-]+\|$", lines[i + 1].strip()):
            flush()
            i += 2
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                rows.append(cells)
                i += 1
            blocks.append(("table", rows))
            continue

        if not s:
            flush()
            i += 1
            continue

        buf.append(line)
        i += 1

    flush()
    return blocks


# ============================================================
# 3. spec 组装
# ============================================================

def split_front_matter(md):
    m = re.match(r"^---\n.*?\n---\n", md, re.S)
    if not m:
        return "", md
    return m.group(0), md[m.end():]


def read_meta(fm):
    """从 front matter 里取几个字段。"""
    out = {}
    m = re.search(r'^title:\s*"(.*)"\s*$', fm, re.M)
    if m:
        out["title"] = m.group(1)
    m = re.search(r"^date:\s*(\S+)", fm, re.M)
    if m:
        out["date"] = m.group(1)
    return out


def _nav_title(zh_title):
    """导航栏标题：去掉 emoji 和中文序号前缀，避免导读区过于拥挤。"""
    t = zh_title.strip()
    t = re.sub(r"^[⭐⚠️★☆\s]+", "", t)
    t = re.sub(r"^[一二三四五六七八九十]+、\s*", "", t)
    t = re.sub(r"^[⭐⚠️★☆\s]+", "", t)
    if len(t) > 14:
        t = t[:13].rstrip("：:，,。 ") + "…"
    return t


def _section_en_title(zh_title):
    """从中文小标题猜一个英文 section 名（主题模板是「编号 + 英文 + 中文」）。"""
    head = re.split(r"[：:]", zh_title)[0].strip()
    head = re.sub(r"[^\w\s]", "", head)
    head = re.sub(r"\s+", " ", head).strip()
    if not head:
        return "SECTION"
    # 已是英文则直接大写；中文则给一个通用占位
    if re.match(r"^[\x00-\x7F]+$", head):
        return head.upper()[:22]
    return "SECTION"


def build_spec(md, quote, quote_by, facts, related, closer,
               lead=None, nav=None, facts_num=None):
    """从 Markdown 组装出 ``_gzh_graphite.build()`` 需要的 cfg。"""
    fm, body = split_front_matter(md)
    meta = read_meta(fm)

    # 按 "## " 切分成章节
    parts = re.split(r"^## ", body, flags=re.M)
    preamble = parts[0]
    chapters = []
    for p in parts[1:]:
        title, _, rest = p.partition("\n")
        chapters.append((title.strip(), rest))

    pre_blocks = parse_markdown(preamble)

    # lead：正文第一个非引用、非标题、非表格的段落
    if lead is None:
        lead = ""
        for k, v in pre_blocks:
            if k == "p":
                lead = v
                break
        # 回退：有些文章的引言区全是引用块（如「来源：…」），则取全文第一个段落
        if not lead:
            for _, rest in chapters:
                for k, v in parse_markdown(rest):
                    if k == "p":
                        lead = v
                        break
                if lead:
                    break
        # 再回退：取引言区的第一个引用块（去掉「来源：」这类前缀标签）
        if not lead:
            for k, v in pre_blocks:
                if k == "quote":
                    lead = v
                    break
    # 从 preamble 中剔除 lead 本身，避免重复
    filtered = []
    dropped = False
    for k, v in pre_blocks:
        if k == "p" and not dropped and v.strip() == lead.strip():
            dropped = True
            continue
        filtered.append((k, v))

    # 导航
    if nav is None:
        nav = []
        for idx, (t, _) in enumerate(chapters):
            if t.lower().startswith("sources"):
                continue
            nav.append((f"{idx + 1:02d}", _nav_title(t)))
            if len(nav) >= 6:
                break

    sections = []
    for idx, (t, rest) in enumerate(chapters):
        blocks = parse_markdown(rest)
        if not blocks:
            continue
        en = _section_en_title(t)
        sections.append((f"{idx + 1:02d}", en, t, blocks))

    # 关键事实速查
    facts_num = facts_num or f"{len(sections) + 1:02d}"

    return {
        "quote": quote,
        "quote_by": quote_by,
        "lead": lead,
        "nav": nav,
        "sections": sections,
        "facts": facts,
        "facts_num": facts_num,
        "facts_en": "KEY FACTS",
        "facts_zh": "关键事实速查",
        "closer": closer,
        "related": related or [],
        "_meta": meta,
    }


# ============================================================
# 4. 渲染
# ============================================================

def _render_blocks(blocks):
    """把 block 列表渲染成主题 HTML 片段（用扩展后的主题模块）。"""
    T = theme()
    o = []
    for kind, payload in blocks:
        if kind == "p":
            o.append("    " + T.P(T.render_inline(payload), mb="22px"))
        elif kind == "h3":
            o.append(
                f'    <p style="font-size:15px;font-weight:800;color:{T.DARK};margin:28px 0 14px;'
                f'padding-left:12px;border-left:3px solid {T.GREY};line-height:1.4;">'
                f'{T.render_inline(payload)}</p>\n'
            )
        elif kind == "h4":
            o.append(T.h4_block(payload))
        elif kind == "quote":
            o.append(T.quote_block(payload))
        elif kind == "note":
            o.append(T.note_block(payload))
        elif kind == "ul":
            o.append(T.ul_block(payload))
        elif kind == "ol":
            o.append(T.ol_block(payload))
        elif kind == "code":
            o.append(T.code_block(payload))
        elif kind == "table":
            o.append(T.md_table_block(payload))
        elif kind == "hr":
            o.append(T.hr())
    return "".join(o)


def render_html(cfg):
    """用官方主题渲染 spec → 完整 HTML。

    ⭐ 这里直接调用扩展后的 ``_gzh_graphite.build(cfg)`` ——
    分节、END 线、签名、相关阅读等全部走官方逻辑，本脚本不重复实现。
    """
    return theme().build(cfg)


def build_from_article(article_md, out_path=None, quote="", quote_by="",
                       facts=None, related=None, closer="", lead=None,
                       nav=None, facts_num=None, spec_path=None):
    """主入口：从 article.md 生成公众号 HTML。

    返回 ``(html, cfg)``。
    """
    md = open(article_md, encoding="utf-8").read()
    cfg = build_spec(md, quote, quote_by, facts or [], related or [], closer,
                     lead=lead, nav=nav, facts_num=facts_num)

    if spec_path:
        os.makedirs(os.path.dirname(spec_path), exist_ok=True)
        json.dump(cfg, open(spec_path, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=2)

    html = render_html(cfg)
    if out_path:
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        open(out_path, "w", encoding="utf-8").write(html)
        print(f"{len(html):7d} 字节  {out_path}")
    return html, cfg


def main():
    ap = argparse.ArgumentParser(
        description="从 lore article.md 生成公众号石墨极简风 HTML")
    ap.add_argument("article", help="article.md 路径")
    ap.add_argument("-o", "--out", help="输出 HTML 路径")
    ap.add_argument("--spec", help="同时导出 JSON spec（便于人工微调后重渲染）")
    ap.add_argument("--quote", default="", help="引言金句")
    ap.add_argument("--quote-by", default="", help="金句出处")
    ap.add_argument("--facts", help="关键事实 JSON 文件")
    ap.add_argument("--related", help="相关阅读 JSON 文件（字符串数组）")
    ap.add_argument("--closer", default="", help="结尾金句")
    args = ap.parse_args()

    facts = []
    if args.facts and os.path.isfile(args.facts):
        facts = json.load(open(args.facts, encoding="utf-8"))
    related = []
    if args.related and os.path.isfile(args.related):
        related = json.load(open(args.related, encoding="utf-8"))

    out = args.out
    if not out:
        slug = os.path.basename(os.path.dirname(os.path.abspath(args.article)))
        out = os.path.join(WRITINGS, "lore", "gzh", slug,
                           "排版_石墨极简风(graphite-minimal).html")

    build_from_article(args.article, out, quote=args.quote, quote_by=args.quote_by,
                       facts=facts, related=related, closer=args.closer,
                       spec_path=args.spec)


if __name__ == "__main__":
    main()
