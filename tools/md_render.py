# -*- coding: utf-8 -*-
"""Markdown → HTML 渲染器（站点正文用）。

为什么要自己写
--------------
`build.py` 最初用一串正则顺序替换来做 Markdown 转换。那种写法有几个
结构性问题，正则再调也调不掉：

1. **没有「先保护代码」这一步** —— 代码块里的 ``**``、`<b>`、``![x](y)``
   会被后面的规则当成真语法处理，代码内容被改坏。
2. **规则之间互相污染** —— 图片规则要靠「链接规则先跑、把
   ``[alt](x.png)`` 变成 ``<a>``、再用正则把 ``<a>`` 换回 ``<img>``」来实现，
   于是 ``!`` 被漏在��面（``!<img>``）。
3. **顺序敏感且不可测** —— 加一条规则就可能推翻另一条规则的结果。

所以这里改成**块级（block）解析 + 行内（inline）解析**两阶段：
先把 Markdown 切成块（代码块 / 标题 / 表格 / 列表 / 引用 / 段落），
块内再单独走行内解析。代码块的内容在这一步就原样保护下来，
行内规则根本碰不到它。

保持与旧渲染器的 HTML 结构一致
--------------------------------
站点 CSS 按 ``.post-content p / ul / ol / li / table / blockquote / pre /
code / strong / em / h2..h6`` 选择器排版，所以生成的标签名、class
（``<pre><code class="lang">``）和包裹规则都沿用旧版，避免改完要重调 CSS。

支持
----
- ATX 标题 ``#`` ~ ``######``
- 围栏代码块 ```` ```lang ````（内容 HTML 转义）
- 行内代码 `` ` ``（内容 HTML 转义）
- GFM 表格（含 ``\\|`` 转义竖线、单元格内行内格式）
- 无序 / 有序列表（含嵌套、任务列表 ``- [ ]``）
- 引用块 ``> ``（支持多行、行内格式）
- 分隔线 ``---``
- 段落
- 图片 ``![alt](src "title")``
- 链接 ``[text](url)``、裸链接 ``<https://...>``、裸 URL
- 粗体 ``**``、斜体 ``*`` / ``_``、删除线 ``~~``、下划线 ``==``
- 原始 HTML 块级标签透传（``<br>`` ``<a>`` ``<div>`` 等）

用法::

    from md_render import markdown_to_html
    html = markdown_to_html(md_text)
"""
from __future__ import annotations

import html as _html
import re

__all__ = ["markdown_to_html", "render_inline"]

# --------------------------------------------------------------------
# 行内解析
# --------------------------------------------------------------------

# 行内代码优先：它内部的任何标记都只是字面量
_RE_INLINE_CODE = re.compile(r"(`+)(.+?)\1", re.S)

# 原文里允许透传的 HTML 标签
_RE_HTML_TAG = re.compile(
    r"</?(?:a|br|b|i|em|strong|u|s|del|ins|code|pre|kbd|sub|sup|small|mark|"
    r"span|div|p|ul|ol|li|dl|dt|dd|blockquote|hr|img|figure|figcaption|"
    r"table|thead|tbody|tfoot|tr|th|td|details|summary|section|article|"
    r"h[1-6]|picture|source|video|audio|iframe)\b[^<>]*>",
    re.I,
)

# 下划线（本站标记约定，**优先于**斜体判断）
_RE_UNDERLINE = re.compile(r"==([^=]+)==")

# 图片：**必须**在链接之前处理，且独立于链接
_RE_IMAGE = re.compile(
    r"!\[([^\]]*)\]\(\s*([^)\s]+)(?:\s+&quot;([^&]*)&quot;|\s+\"([^\"]*)\"|\s+'([^']*)')?\s*\)"
)

# 链接
_RE_LINK = re.compile(r"\[([^\]]*)\]\(\s*([^)\s]+)(?:\s+&quot;([^&]*)&quot;|\s+\"([^\"]*)\"|\s+'([^']*)')?\s*\)")

# 裸链接（尖括号包裹）
_RE_AUTOLINK = re.compile(r"<((?:https?|ftp|mailto):[^>\s]+)>")

# 裸 URL（不在尖括号、也不在已有链接的 href 里）
# 前面不能紧跟 " ' = 或 ASCII 单词字符（否则会命中 href="..." 里的值）。
# ★ 允许前面是 ">"（强调标记的闭合标签）—— 否则 `<em>https://x</em>` 里的 URL 不会被识别。
# 结尾不吞句末标点（中英文）、右括号，也**不吞强调标记**（* =）——
# 否则 `*文字 https://x.com/a*` 里的 URL 会把结尾的 `*` 一起吃掉。
# _ 和 ~ 允许出现在 URL 里（https://x.com/a_b_c 很常见）。
_RE_BARE_URL = re.compile(
    r"(?<![\"'=(A-Za-z0-9_])((?:https?://)[^\s<>\"'*~=]*[^\s<>\"'*~=。，、；：？！）】」』"
    r".,;:!?)\]}])(?![<\w])")

_RE_STRONG = re.compile(r"\*\*(.+?)\*\*", re.S)
# 粗斜体 ***text***：必须在粗体之前处理，否则会被拆成 **<em>text</em>**
_RE_STRONG_EM = re.compile(r"\*\*\*(?=\S)(.+?)(?<=\S)\*\*\*", re.S)
# ⭐ 嵌套粗体 **a *b **c** d* e**：
#    朴素的 ``\*\*(.+?)\*\*`` 会先匹配到「**a *b **」，
#    剩下「c** d* e**」变成两个孤立片段。
#    这里用一个「配平扫描」来找**最外层**的粗体区间：
#    从第一个 ** 开始，扫描到**配平的** ** 为止（跳过内部的 *）。
_RE_EM = re.compile(r"(?<![*A-Za-z0-9_])\*(?!\s)([^*\n]+?)(?<!\s)\*(?![*A-Za-z0-9_])")
_RE_EM_U = re.compile(r"(?<![A-Za-z0-9_])_(?!\s)([^_\n]+?)(?<!\s)_(?![A-Za-z0-9_])")
_RE_STRIKE = re.compile(r"~~([^~]+)~~")


def _find_balanced_strong(text: str):
    """找出最外层 ``**...**`` 的区间（配平扫描）。

    返回 ``(start, end)`` —— ``end`` 是闭合 ``**`` 之后的位置；
    找不到配平时返回 ``None``。
    """
    i = 0
    n = len(text)
    while i < n:
        start = text.find("**", i)
        if start < 0:
            return None
        # 跳过成对的 ***（粗斜体）
        if text.startswith("***", start):
            end = text.find("***", start + 3)
            if end < 0:
                return None
            i = end + 3
            continue
        # 扫描内部：遇到单 * 跳过（可能是嵌套斜体），遇到 ** 则是闭合
        j = start + 2
        while j < n:
            if text.startswith("**", j):
                return (start, j + 2)
            if text[j] == "*":
                j += 2                 # 跳过一对嵌套的 *
                continue
            j += 1
        return None
    return None


def _replace_balanced_strong(text: str, repl) -> str:
    """把配平的 ``**...**`` 替换掉，保留未配平的字面 ``**``。"""
    out = []
    i = 0
    while i < len(text):
        if text.startswith("**", i):
            span = _find_balanced_strong(text[i:])
            if span:
                start, end = span
                inner = text[i + start + 2:i + end - 2]
                out.append(repl(inner))
                i += end
                continue
        out.append(text[i])
        i += 1
    return "".join(out)

# ⭐ 强调标记不能跨 HTML 标签边界匹配。
#    否则 `*文字 https://x.com/a*` 会变成
#    `<em>文字 <a href="https://x.com/a</em>">…</a>` —— 标签被插进了属性里。
# 占位符：用 Unicode 私有区码点，不会出现在正文里，也不会被 html.escape 改写。
_PH_STASH = "\ue000"
_PH_END = "\ue003"


# 各类占位符（行内代码 / 原样 HTML / 裸链接）
# ⭐ 必须带捕获组 —— _apply_emphasis 用 re.split，捕获组才是被分隔的部分。
# 占位符格式：\ue000<depth>:<序号>\ue003
_RE_PLACEHOLDER = re.compile(
    "(" + re.escape(_PH_STASH) + r"\d+:\d+" + re.escape(_PH_END) + ")")


def _apply_emphasis(text: str, keep) -> str:
    """只对**纯文本部分**应用强调标记。

    强调不能跨占位符匹配，否则
    ``*文字 [链接](x)*`` 会被拆成两个半截的 ``<em>``。
    生成的 ``<strong>`` / ``<em>`` 等标签通过 ``keep`` 存进 stash，
    避免它们自己被后续规则当成要转义的文本。
    """
    parts = _RE_PLACEHOLDER.split(text)
    out = []
    for idx, part in enumerate(parts):
        if idx % 2 == 1:
            out.append(part)          # 占位符原样
            continue
        part = _RE_STRONG.sub(lambda m: keep(f"<strong>{m.group(1)}</strong>"), part)
        part = _RE_EM.sub(lambda m: keep(f"<em>{m.group(1)}</em>"), part)
        part = _RE_EM_U.sub(lambda m: keep(f"<em>{m.group(1)}</em>"), part)
        part = _RE_STRIKE.sub(lambda m: keep(f"<del>{m.group(1)}</del>"), part)
        part = _RE_UNDERLINE.sub(lambda m: keep(f"<u>{m.group(1)}</u>"), part)
        out.append(part)
    return "".join(out)


def _esc(text: str) -> str:
    """HTML 转义。"""
    return _html.escape(text, quote=False)


def _attr(text: str) -> str:
    """属性值转义（引号也要转义）。"""
    return _html.escape(text, quote=True)


def _link_target(url: str) -> str:
    """链接目标：站内相对路径保持原样，其余加安全属性。"""
    url = url.strip()
    if url.startswith(("http://", "https://", "mailto:", "ftp://", "//")):
        return (f'<a href="{_attr(url)}" target="_blank" '
                f'rel="noopener noreferrer">{url}</a>')
    return f'<a href="{_attr(url)}">{url}</a>'


def _render_links_and_images(text: str) -> str:
    """处理图片 / 链接 / 裸链接。

    ⚠️ 传入的 text 里，裸文本部分已经做过 HTML 转义（``&`` → ``&amp;``），
    所以 URL 里的 ``&`` 已经是 ``&amp;``。这里不能再转义一次，
    否则会变成 ``&amp;amp;``。
    """

    def img(m):
        alt = m.group(1)
        src = m.group(2)
        title = m.group(3) or m.group(4) or m.group(5)
        title_attr = f' title="{_attr(title)}"' if title else ""
        return (f'<img src="{_attr(src)}" alt="{_attr(alt)}"{title_attr} '
                f'loading="lazy" decoding="async" '
                f'style="max-width:100%;height:auto;border-radius:8px;margin:12px 0;">')

    def link(m):
        label = m.group(1)
        url = m.group(2)
        title = m.group(3) or m.group(4) or m.group(5)
        title_attr = f' title="{_attr(title)}"' if title else ""
        if url.startswith(("http://", "https://", "mailto:", "ftp://", "//")):
            return (f'<a href="{_attr(url)}"{title_attr} target="_blank" '
                    f'rel="noopener noreferrer">{label}</a>')
        return f'<a href="{_attr(url)}"{title_attr}>{label}</a>'

    text = _RE_IMAGE.sub(img, text)
    text = _RE_LINK.sub(link, text)
    text = _RE_AUTOLINK.sub(lambda m: _link_target(m.group(1)), text)
    text = _RE_BARE_URL.sub(lambda m: _link_target(m.group(1)), text)
    return text


def render_inline(text: str, _depth: int = 0) -> str:
    """把一行（已去首尾空白）里的行内 Markdown 转成 HTML。

    架构：**先生成 HTML 片段存进 stash，最后只对剩下的纯文本做转义。**

    这样避免了「先转义再匹配 URL」导致的两个问题：
      - URL 里的 ``&`` 被转成 ``&amp;`` 后再放进 href → 二次转义成 ``&amp;amp;``
      - URL 里的 ``/`` 被当成路径分隔处理，导致链接被截断

    处理顺序：
      1. 行内代码（内容只转义，不参与后续解析）
      2. 原文里已有的 HTML 标签（原样透传）
      3. 裸链接 ``<https://...>``
      4. 强调（**粗体** / *斜体* / ~~删除~~ / ==下划线==）——
         强调的内容**递归**走一遍本函数，所以 ``*文字 [链接](x)*``
         能同时得到 <em> 与 <a>
      5. 图片 / 链接
      6. 剩下的纯文本转义
      7. 还原 stash
    """
    if _depth > 6:                       # 防御：异常嵌套时不无限递归
        return _esc(text)

    stash: list[str] = []

    def keep(html: str) -> str:
        """把一段已生成的 HTML 存起来，换成占位符。

        ⭐ ID 带**深度前缀**（_depth）：强调内容会递归调用 render_inline，
        内外两层各有独立的 stash，编号都从 0 开始 ——
        不加前缀的话，内层会把外层的占位符用自己的 stash 还原掉（串号）。
        """
        stash.append(html)
        return f"{_PH_STASH}{_depth}:{len(stash) - 1}{_PH_END}"

    # ---- 1) 行内代码 ----
    text = _RE_INLINE_CODE.sub(
        lambda m: keep(f"<code>{_esc(m.group(2))}</code>"), text)

    # ---- 2) 原文里已有的 HTML 标签：原样透传 ----
    text = _RE_HTML_TAG.sub(lambda m: keep(m.group(0)), text)

    # ---- 3) 裸链接 <https://...> ----
    text = _RE_AUTOLINK.sub(
        lambda m: keep(_link_target(m.group(1))), text)

    # ---- 4) 强调：内容递归处理，所以里面的链接/图片也生效 ----
    def strong(inner_text):
        return keep(f"<strong>{render_inline(inner_text, _depth + 1)}</strong>")

    def em(m):
        return keep(f"<em>{render_inline(m.group(1), _depth + 1)}</em>")

    def strike(m):
        return keep(f"<del>{render_inline(m.group(1), _depth + 1)}</del>")

    def under(m):
        return keep(f"<u>{render_inline(m.group(1), _depth + 1)}</u>")

    text = _RE_STRONG_EM.sub(
        lambda m: keep(f"<strong><em>{render_inline(m.group(1), _depth + 1)}</em></strong>"),
        text)
    text = _replace_balanced_strong(text, strong)
    text = _RE_EM.sub(em, text)
    text = _RE_EM_U.sub(em, text)
    text = _RE_STRIKE.sub(strike, text)
    text = _RE_UNDERLINE.sub(under, text)

    # ---- 5) 图片 / 链接 ----
    def img(m):
        alt = m.group(1)
        src = m.group(2)
        title = m.group(3) or m.group(4) or m.group(5)
        title_attr = f' title="{_attr(title)}"' if title else ""
        return (f'<img src="{_attr(src)}" alt="{_attr(alt)}"{title_attr} '
                f'loading="lazy" decoding="async" '
                f'style="max-width:100%;height:auto;border-radius:8px;margin:12px 0;">')

    def link(m):
        label = render_inline(m.group(1), _depth + 1)
        url = m.group(2)
        title = m.group(3) or m.group(4) or m.group(5)
        title_attr = f' title="{_attr(title)}"' if title else ""
        if url.startswith(("http://", "https://", "mailto:", "ftp://", "//")):
            return (f'<a href="{_attr(url)}"{title_attr} target="_blank" '
                    f'rel="noopener noreferrer">{label}</a>')
        return f'<a href="{_attr(url)}"{title_attr}>{label}</a>'

    text = _RE_IMAGE.sub(lambda m: keep(img(m)), text)
    text = _RE_LINK.sub(lambda m: keep(link(m)), text)
    text = _RE_BARE_URL.sub(lambda m: keep(_link_target(m.group(1))), text)

    # ---- 6) 剩下的都是纯文本，转义 ----
    text = _esc(text)

    # ---- 7) 还原 stash（只还原本层 depth 前缀的）----
    #    ⭐ 必须**循环**：本层的占位符可能嵌在上一层生成的 HTML 里
    #    （比如「**粗 `code` 粗**」—— 内层递归返回的字符串里带着外层的占位符），
    #    单次 sub 只扫一遍，替换出来的内容里的占位符不会被再处理。
    prefix = f"{_PH_STASH}{_depth}:"
    re_this = re.compile(re.escape(prefix) + r"(\d+)" + re.escape(_PH_END))
    for _ in range(8):                      # 最多循环 8 次，防御性上限
        new_text, n = re_this.subn(
            lambda m: stash[int(m.group(1))], text)
        if not n:
            break
        text = new_text
    return text


# --------------------------------------------------------------------
# 块级解析
# --------------------------------------------------------------------

_RE_FENCE = re.compile(r"^(\s*)(`{3,}|~{3,})\s*([^\s`]*)\s*$")
_RE_ATX = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
_RE_HR = re.compile(r"^\s{0,3}([-*_])(\s*\1){2,}\s*$")
_RE_UL = re.compile(r"^(\s*)[-*+]\s+(.*)$")
_RE_OL = re.compile(r"^(\s*)(\d+)[.)]\s+(.*)$")
_RE_TASK = re.compile(r"^\[([ xX])\]\s+(.*)$")
_RE_QUOTE = re.compile(r"^\s{0,3}>\s?(.*)$")
_RE_TABLE_SEP = re.compile(r"^\s*\|?\s*:?-{1,}:?\s*(\|\s*:?-{1,}:?\s*)*\|?\s*$")

# 块级原始 HTML（透传）
_RE_HTML_BLOCK = re.compile(
    r"^\s{0,3}</?(?:div|table|thead|tbody|tfoot|tr|th|td|ul|ol|li|dl|dt|dd|"
    r"blockquote|pre|figure|figcaption|section|article|aside|details|summary|"
    r"picture|source|video|audio|iframe|p)\b",
    re.I,
)

# 这些块级标签出现时，其后到空行为止的内容整体透传
# （注意：这里存的是**标签名**，不含尖括号）
_RAW_HTML_BLOCKS = frozenset({
    "pre", "table", "div", "figure", "blockquote", "ul", "ol", "details",
    "summary", "section", "article", "aside", "dl", "picture", "video",
    "audio", "iframe", "figure",
})


def _split_table_row(line: str) -> list[str]:
    """把一行表格按未转义的 ``|`` 切成单元格。"""
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|") and not line.endswith("\\|"):
        line = line[:-1]

    cells, cur, i = [], [], 0
    while i < len(line):
        ch = line[i]
        if ch == "\\" and i + 1 < len(line) and line[i + 1] == "|":
            cur.append("|")
            i += 2
            continue
        if ch == "|":
            cells.append("".join(cur).strip())
            cur = []
            i += 1
            continue
        cur.append(ch)
        i += 1
    cells.append("".join(cur).strip())
    return cells


def _convert_table(rows: list[list[str]]) -> str:
    """表格 → HTML。第一行是表头。"""
    if not rows:
        return ""
    head, body = rows[0], rows[1:]
    out = ["<table>", "<thead><tr>"]
    for c in head:
        out.append(f"<th>{render_inline(c)}</th>")
    out.append("</tr></thead>")
    if body:
        out.append("<tbody>")
        for r in body:
            out.append("<tr>")
            for c in r:
                out.append(f"<td>{render_inline(c)}</td>")
            out.append("</tr>")
        out.append("</tbody>")
    out.append("</table>")
    return "".join(out)


def _collect_blocks(lines: list[str], start: int) -> tuple[list, int, int]:
    """从一个位置开始收集同类块。

    返回 ``(items, next_index, kind)``。
    - kind ``"list"`` → items 是 ``(indent, marker, content)`` 三元组
    - kind ``"quote"`` → items 是原始行
    - kind ``"table"`` → items 是单元格二维列表
    """
    i = start
    n = len(lines)

    # ---- 表格 ----
    if i < n and lines[i].strip().startswith("|") and i + 1 < n \
            and _RE_TABLE_SEP.match(lines[i + 1]) \
            and "-" in lines[i + 1]:
        rows = [_split_table_row(lines[i])]
        i += 2
        while i < n and lines[i].strip().startswith("|"):
            rows.append(_split_table_row(lines[i]))
            i += 1
        return rows, i, "table"

    # ---- 引用 ----
    if i < n and _RE_QUOTE.match(lines[i]):
        items = []
        while i < n:
            m = _RE_QUOTE.match(lines[i])
            if m:
                items.append(m.group(1))
                i += 1
            elif lines[i].strip() and items:
                # 引用块里的续行（懒延续）
                items.append(lines[i].strip())
                i += 1
            else:
                break
        return items, i, "quote"

    # ---- 列表 ----
    m_ul = _RE_UL.match(lines[i])
    m_ol = _RE_OL.match(lines[i])
    if m_ul or m_ol:
        items = []
        base_indent = len((m_ul or m_ol).group(1))
        while i < n:
            line = lines[i]
            m = _RE_UL.match(line) or _RE_OL.match(line)
            if m:
                indent = len(m.group(1))
                if indent < base_indent:
                    break
                content = m.group(m.lastindex)
                # 有序列表的 group 布局不同，重新取
                if m.re is _RE_OL or m.re.pattern.startswith(r"^(\s*)(\d+)"):
                    content = m.group(3)
                else:
                    content = m.group(2)
                items.append((indent, line.strip()[:2], content))
                i += 1
                continue
            # 列表项的续行（缩进的非列表行）
            if (line.strip() and items
                    and (len(line) - len(line.lstrip())) > base_indent
                    and not _RE_HR.match(line)):
                items.append((len(line) - len(line.lstrip()), "", line.strip()))
                i += 1
                continue
            # 空行：看后面是否还有同级列表项
            if not line.strip():
                j = i
                while j < n and not lines[j].strip():
                    j += 1
                if j < n:
                    nm = _RE_UL.match(lines[j]) or _RE_OL.match(lines[j])
                    if nm and len(nm.group(1)) >= base_indent:
                        items.append((base_indent, "", ""))
                        i = j
                        continue
                break
            break
        return items, i, "list"

    return [], i, "none"


def _render_list(items: list) -> str:
    """列表 items → <ul>/<ol>，支持嵌套与任务列表。

    items 是 ``(indent, marker, content)`` 三元组；indent 是相对根的缩进量。
    """
    if not items:
        return ""
    ordered = bool(items[0][1][:1].isdigit())

    # 先把扁平的 items 变成树
    root: list = []
    stack: list = [(-1, root)]  # (indent, 容器)

    for indent, marker, content in items:
        if content == "":
            continue
        # 回退到「能容纳当前 indent 的最近层级」。
        # 用 <= 而不是 <：因为栈里存的是「下一层子项」的 indent，
        # 与当前项同级时必须退回到父层，否则同级项会错进上一个 li 的子列表。
        while len(stack) > 1 and indent <= stack[-1][0]:
            stack.pop()
        parent_container = stack[-1][1]

        is_task = bool(_RE_TASK.match(content))
        checked = False
        if is_task:
            m = _RE_TASK.match(content)
            checked = m.group(1).lower() == "x"
            content = m.group(2)

        li = {"content": content, "children": [], "task": is_task,
              "checked": checked}
        parent_container.append(li)

        # 下一个更深缩进的项，挂到这个 li 下
        stack.append((indent, li["children"]))

    def emit(container, tag):
        if not container:
            return ""
        out = [f"<{tag}>"]
        for li in container:
            cls = ' class="task-item"' if li["task"] else ""
            inner = render_inline(li["content"])
            if li["task"]:
                checked = " checked" if li["checked"] else ""
                inner = f'<input type="checkbox" disabled{checked}> {inner}'
            if li["children"]:
                inner += emit(li["children"], "ul")
            out.append(f"<li{cls}>{inner}</li>")
        out.append(f"</{tag}>")
        return "".join(out)

    return emit(root, "ol" if ordered else "ul")


def markdown_to_html(md_content: str) -> str:
    """Markdown → HTML。站点正文用。

    与旧版正则实现保持 HTML 结构一致，但修掉了以下问题：

    - 图片前的多余 ``!``
    - 代码块 / 行内代码里的 Markdown 标记被误解析
    - 代码块里的 ``<`` ``>`` ``&`` 未转义
    - 有序列表编号重复（``<li>1. 第一</li>``）
    - 多级列表被拆散
    - 表格单元格里的转义竖线 ``\\|``
    - 裸链接 ``<https://...>``
    """
    if not md_content:
        return ""

    lines = md_content.replace("\r\n", "\n").split("\n")
    out: list[str] = []
    i = 0
    n = len(lines)

    while i < n:
        line = lines[i]
        stripped = line.strip()

        # 空行
        if not stripped:
            i += 1
            continue

        # ---- 围栏代码块 ----
        m = _RE_FENCE.match(line)
        if m:
            fence = m.group(2)
            lang = m.group(3)
            marker = fence[0]
            i += 1
            body = []
            while i < n:
                cm = _RE_FENCE.match(lines[i])
                if cm and cm.group(2)[0] == marker and len(cm.group(2)) >= len(fence) \
                        and not cm.group(3):
                    i += 1
                    break
                body.append(lines[i])
                i += 1
            code = _esc("\n".join(body))
            cls = f' class="{_attr(lang)}"' if lang else ""
            out.append(f"<pre><code{cls}>{code}</code></pre>")
            continue

        # ---- 分隔线 ----
        if _RE_HR.match(line):
            out.append("<hr>")
            i += 1
            continue

        # ---- ATX 标题 ----
        m = _RE_ATX.match(line)
        if m:
            level = len(m.group(1))
            text = m.group(2).strip()
            out.append(f"<h{level}>{render_inline(text)}</h{level}>")
            i += 1
            continue

        # ---- 原始 HTML 块级：整体透传 ----
        if _RE_HTML_BLOCK.match(line):
            tag = re.match(r"^\s{0,3}</?([a-zA-Z0-9]+)", line).group(1).lower()
            if tag in _RAW_HTML_BLOCKS:
                block = []
                while i < n and lines[i].strip():
                    block.append(lines[i])
                    i += 1
                out.append("\n".join(block))
                continue

        # ---- 缩进代码块（4 空格 / Tab）----
        if re.match(r"^(?: {4}|\t)\S", line):
            block = []
            while i < n and (not lines[i].strip()
                             or re.match(r"^(?: {4}|\t)", lines[i])):
                if not lines[i].strip():
                    # 看看空行之后是不是还是缩进块
                    j = i
                    while j < n and not lines[j].strip():
                        j += 1
                    if j < n and re.match(r"^(?: {4}|\t)\S", lines[j]):
                        block.extend(lines[i:j])
                        i = j
                        continue
                    break
                block.append(lines[i][4:] if lines[i].startswith("    ") else lines[i][1:])
                i += 1
            if block:
                code = _esc("\n".join(block))
                out.append(f"<pre><code>{code}</code></pre>")
                continue

        # ---- 表格 / 引用 / 列表 ----
        items, nxt, kind = _collect_blocks(lines, i)
        if kind == "table":
            out.append(_convert_table(items))
            i = nxt
            continue
        if kind == "quote":
            # ⭐ 与旧渲染器保持一致：连续的引用行用 <br> 分隔，
            #    而不是合并成一个段落（合并会丢掉行结构，例：
            #    「**原始出处**：… / **发布日期**：…」会被挤成一行）。
            inner = "<br>\n".join(
                render_inline(item) for item in items)
            out.append(f"<blockquote>{inner}</blockquote>")
            i = nxt
            continue
        if kind == "list":
            out.append(_render_list(items))
            i = nxt
            continue

        # ---- 段落：连续非空行合并 ----
        para = []
        while i < n and lines[i].strip():
            if _RE_FENCE.match(lines[i]) or _RE_ATX.match(lines[i]) \
                    or _RE_HR.match(lines[i]):
                break
            if para and (_RE_UL.match(lines[i]) or _RE_OL.match(lines[i])):
                break
            # 段落中途出现块级 HTML 标签（如 <div>）→ 断开，
            # 否则标签会被包进 <p>，变成非法的嵌套结构。
            if para and _RE_HTML_BLOCK.match(lines[i]):
                break
            para.append(lines[i].strip())
            i += 1
        if para:
            out.append(f"<p>{render_inline(' '.join(para))}</p>")

    return "\n".join(out)


if __name__ == "__main__":
    import sys
    print(markdown_to_html(sys.stdin.read()))
