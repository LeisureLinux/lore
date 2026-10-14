#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""2026-10-13 两篇公众号封面（1200x675，石墨极简风格）。

规格沿用 lore/gzh/make_covers_2026-10-06.py 的约定：
  画布 1200x675（公众号 16:9），深色渐变底 + 顶部 7px 强调色条，
  主标题（第一行白、第二行强调色）+ 副标题 + 底部圆角信息条。
  微信列表按 2.35:1 居中裁切，所以主标题不贴边（左右各留 56px，上下留白充足）。
字体：NotoSansCJK-Bold.ttc / Black.ttc，index=2 为 SC。
自检：用 PIL 量文字 bbox 是否越界 + 文字区/背景亮度对比（不用 tesseract OCR）。
"""
import os
from PIL import Image, ImageDraw, ImageFont

BASE = os.path.dirname(os.path.abspath(__file__))
FB = "/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc"
FR = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"


def F(sz, kind="black"):
    return ImageFont.truetype(FR if kind == "bold" else FB, sz, index=2)


W, H = 1200, 675
BG = (10, 13, 18)
FG = (240, 244, 250)
MUTED = (130, 140, 152)
SAFE = 56  # 左右安全边距

CFG = [
    # npm 供应链 / SlugFest：用深红强调，呼应「供应链风险」的警示语义
    dict(slug="2026-10-13_npm-trusted-publishing-slugfest", accent=(248, 113, 113),
         l1="1500 个 npm 包",
         l2="发布权可以被继承",
         sub="根因不是 npm 大意，是它用「名字」而不是「ID」验证发布者",
         bar="仓库改名/转移/删除后旧名可被占用 · 48 小时过期修复 · 代理每月装 70~350 个包"),
    # Asterinas / framekernel：用 Rust 橙，呼应「Rust 内核」且与系统类文章区分
    dict(slug="2026-10-13_asterinas-0-19-framekernel", accent=(230, 130, 74),
         l1="Asterinas 0.19",
         l2="不减少地址空间，只减少 unsafe",
         sub="framekernel：宏内核的速度，微内核的安全性",
         bar="unsafe 收敛在 OSTD 约 2000 行 · xfstests 用例翻倍 · 自举通过"),
]


def fit(d, text, font_path, start, max_w, kind="bold"):
    """字号自适应：从 start 往下找第一个不超 max_w 的字号。"""
    sz = start
    while sz > 16:
        f = ImageFont.truetype(font_path, sz, index=2)
        if d.textlength(text, font=f) <= max_w:
            return f
        sz -= 1
    return ImageFont.truetype(font_path, 16, index=2)


def luma(rgb):
    r, g, b = rgb
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


for c in CFG:
    out = os.path.join(BASE, c["slug"], "cover.png")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    acc = c["accent"]

    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)

    # 垂直渐变底
    for y in range(H):
        t = y / H
        d.line([(0, y), (W, y)], fill=(int(10 + 16 * t), int(13 + 18 * t), int(18 + 26 * t)))

    # 顶部强调条
    d.rectangle([0, 0, W, 7], fill=acc)

    # 主标题：第一行白、第二行强调色
    f_l1 = fit(d, c["l1"], FB, 62, W - 2 * SAFE)
    f_l2 = fit(d, c["l2"], FB, 62, W - 2 * SAFE)
    b1 = d.textbbox((SAFE, 70), c["l1"], font=f_l1)
    b2 = d.textbbox((SAFE, 156), c["l2"], font=f_l2)
    d.text((SAFE, 70), c["l1"], font=f_l1, fill=FG)
    d.text((SAFE, 156), c["l2"], font=f_l2, fill=acc)

    # 副标题
    f_sub = fit(d, c["sub"], FR, 28, W - 2 * SAFE, "bold")
    bsub = d.textbbox((SAFE + 2, 252), c["sub"], font=f_sub)
    d.text((SAFE + 2, 252), c["sub"], font=f_sub, fill=MUTED)

    # 底部圆角信息条
    bx, by = SAFE, H - 128
    f_bar = fit(d, c["bar"], FR, 23, W - 2 * bx - 40, "bold")
    bbar = d.textbbox((bx + 20, by + 24), c["bar"], font=f_bar)
    d.rounded_rectangle([bx, by, W - bx, by + 72], 12, fill=(22, 28, 36), outline=acc, width=2)
    d.text((bx + 20, by + 24), c["bar"], font=f_bar, fill=FG)

    im.save(out, quality=95)

    # ---- 自检 ----
    issues = []
    for name, b in (("l1", b1), ("l2", b2), ("sub", bsub), ("bar", bbar)):
        if b[0] < 0 or b[2] > W or b[1] < 0 or b[3] > H:
            issues.append(f"{name} 越界 {b}")
    # 主标题不贴边（微信 2.35:1 裁切会切掉上下，主标题须在上半区）
    if b2[3] > H * 0.5:
        issues.append(f"主标题第二行底部 {b2[3]} 越过中线（裁切风险）")
    for name, b in (("l1", b1), ("l2", b2), ("sub", bsub)):
        if b[2] > W - 20:
            issues.append(f"{name} 右边界 {b[2]} 过于贴近画布")
    # 文字与背景亮度对比
    contrast_ok = luma(FG) - luma((10, 13, 18)) > 120 and luma(acc) - luma((10, 13, 18)) > 60
    if not contrast_ok:
        issues.append("对比度不足")
    print(f"{'OK ' if not issues else 'WARN'} {out} {im.size} "
          f"l1={f_l1.size}px l2={f_l2.size}px sub={f_sub.size}px bar={f_bar.size}px "
          f"对比={luma(FG)-luma((10,13,18)):.0f}/{luma(acc)-luma((10,13,18)):.0f}"
          + ("" if not issues else "  ⚠ " + "; ".join(issues)))
