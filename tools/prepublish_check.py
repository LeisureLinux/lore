#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""发布前检查：一条命令跑完所有硬性门槛。

检查项：
1. **标题规范**（tools/check_title.py）—— 必须以具体产品名开头做主语
2. **排版合规**（gzh-design-skill/scripts/validate_gzh_html.py）—— 平台红线 + 裸符号 + 列数 + 英文引用
3. **front matter 完整性**—— title / date / slug / category / description / published

用法：
    python3 tools/prepublish_check.py <slug>
    python3 tools/prepublish_check.py --all          # 全量体检（历史文章，会大量报错）
    python3 tools/prepublish_check.py --all --newest 10

退出码: 1 = 有 ERROR（发布前必须修）; 0 = 全部通过。
"""
import argparse
import os
import re
import subprocess
import sys

LORE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(LORE, "tools"))

import check_title  # noqa: E402

ARTICLES = os.path.join(LORE, "articles")
GZH = os.path.join(LORE, "gzh")
VALIDATOR = "/home/axu/.agents/skills/gzh-design-skill/scripts/validate_gzh_html.py"

REQUIRED_META = ["title", "date", "slug", "category", "description", "published"]


def check_front_matter(slug):
    """检查 article.md 的 front matter 与 metadata.yaml。"""
    errs, warns = [], []
    art = os.path.join(ARTICLES, slug, "article.md")
    meta = os.path.join(ARTICLES, slug, "metadata.yaml")

    if not os.path.exists(art):
        return [f"article.md 不存在: {art}"], warns
    if not os.path.exists(meta):
        errs.append(f"metadata.yaml 不存在: {meta}")

    content = open(art, encoding="utf-8").read()
    m = re.match(r"^\s*---[ \t]*\n(.*?)\n---[ \t]*$", content, re.S | re.M)
    if not m:
        errs.append("article.md 缺少 YAML front matter")
    else:
        fm = m.group(1)
        keys = set(re.findall(r"^([A-Za-z_][A-Za-z0-9_]*):", fm, re.M))
        missing = [k for k in REQUIRED_META if k not in keys]
        if missing:
            errs.append(f"front matter 缺字段: {missing}")
        if "⭐" in fm or "**" in re.sub(r"description:.*", "", fm, flags=re.S):
            warns.append("front matter 里出现了 ⭐ 或 **")

    # 正文（去掉 front matter）不应有裸 ⭐
    body = content[m.end():] if m else content
    if "⭐" in body:
        warns.append("正文里出现了 ⭐（段首五角星会被排版成旁注卡片）")
    if re.search(r"^>\s*\*\*?⭐", body, re.M):
        errs.append("正文有以 ⭐ 开头的引用块")

    return errs, warns


def check_html(slug):
    """跑 gzh-design-skill 的校验脚本。"""
    d = os.path.join(GZH, slug)
    html = os.path.join(d, "排版_石墨极简风(graphite-minimal).html")
    if not os.path.exists(html):
        return [f"排版 HTML 不存在: {html}"], []
    r = subprocess.run([sys.executable, VALIDATOR, html],
                       capture_output=True, text=True)
    out = r.stdout
    errs = []
    # 校验脚本用「❌ ERROR ×N」标记错误
    m = re.search(r"❌ ERROR ×(\d+)", out)
    if m and int(m.group(1)) > 0:
        errs.append(f"排版校验有 {m.group(1)} 项 ERROR —— 详见校验脚本输出")
    if "span leaf 包裹: 0" in out:
        errs.append("排版 HTML 里没有 span leaf 包裹")
    return errs, []


def run_one(slug, verbose=True):
    errs, warns = [], []
    art = os.path.join(ARTICLES, slug, "article.md")
    if not os.path.exists(art):
        print(f"❌ {slug}: 文章不存在")
        return 1

    title = check_title.article_title(art)
    if not title:
        errs.append("读不到 title")
    else:
        e, w = check_title.check_title(title)
        errs += [f"标题：{x}" for x in e]
        warns += [f"标题：{x}" for x in w]

    e, w = check_front_matter(slug)
    errs += e
    warns += w

    e, w = check_html(slug)
    errs += e
    warns += w

    if errs or warns:
        print(f"\n{'❌' if errs else '⚠️ '} {slug}")
        print(f"   标题：{title}")
        for x in errs:
            print(f"   ERROR: {x}")
        for x in warns:
            print(f"   WARN:  {x}")
    elif verbose:
        print(f"✅ {slug}")
    return 1 if errs else 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("slug", nargs="*")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--newest", type=int, default=0)
    args = ap.parse_args()

    slugs = list(args.slug)
    if args.all or not slugs:
        slugs = sorted(d for d in os.listdir(ARTICLES)
                       if os.path.isdir(os.path.join(ARTICLES, d)))
        if args.newest:
            slugs = slugs[-args.newest:]

    n_bad = 0
    for s in slugs:
        n_bad += 1 if run_one(s) else 0

    print(f"\n{'=' * 52}")
    print(f"检查 {len(slugs)} 篇：不合规 {n_bad} 篇")
    if n_bad:
        print("❌ 发布前必须修掉 ERROR")
    else:
        print("✅ 全部通过")
    sys.exit(1 if n_bad else 0)


if __name__ == "__main__":
    main()
