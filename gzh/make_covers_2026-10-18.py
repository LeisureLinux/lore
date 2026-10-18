#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""2026-10-18 公众号封面（1200x675，石墨极简风格）。"""
import os
from PIL import Image, ImageDraw, ImageFont

BASE = os.path.dirname(os.path.abspath(__file__))
FB = "/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc"
FR = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"

W, H = 1200, 675
BG = (10, 13, 18)
FG = (240, 244, 250)
MUTED = (130, 140, 152)
SAFE = 56

CFG = [
    # LRC / A2 / TTML 三种歌词格式
    dict(slug="2026-10-18_lrc-ttml-karaoke-formats", accent=(251, 146, 60),
         l1="歌词格式的三次分裂",
         l2="349 首歌，我转了三遍",
         sub="LRC 起于 1998 年的 Winamp 插件，A2 加了词级标记，TTML 来自字幕标准",
         bar="车载锁死平台：CarPlay 与 Android Auto 互不相通 · 免费+离线+逐词只剩两个选择"),
]

def fit(d, text, font_path, start, max_w):
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
    for y in range(H):
        t = y / H
        d.line([(0, y), (W, y)], fill=(int(10 + 16 * t), int(13 + 18 * t), int(18 + 26 * t)))
    d.rectangle([0, 0, W, 7], fill=acc)

    f_l1 = fit(d, c["l1"], FB, 62, W - 2 * SAFE)
    f_l2 = fit(d, c["l2"], FB, 62, W - 2 * SAFE)
    b1 = d.textbbox((SAFE, 70), c["l1"], font=f_l1)
    b2 = d.textbbox((SAFE, 156), c["l2"], font=f_l2)
    d.text((SAFE, 70), c["l1"], font=f_l1, fill=FG)
    d.text((SAFE, 156), c["l2"], font=f_l2, fill=acc)

    f_sub = fit(d, c["sub"], FR, 28, W - 2 * SAFE)
    bsub = d.textbbox((SAFE + 2, 252), c["sub"], font=f_sub)
    d.text((SAFE + 2, 252), c["sub"], font=f_sub, fill=MUTED)

    bx, by = SAFE, H - 128
    f_bar = fit(d, c["bar"], FR, 23, W - 2 * bx - 40)
    bbar = d.textbbox((bx + 20, by + 24), c["bar"], font=f_bar)
    d.rounded_rectangle([bx, by, W - bx, by + 72], 12, fill=(22, 28, 36), outline=acc, width=2)
    d.text((bx + 20, by + 24), c["bar"], font=f_bar, fill=FG)

    im.save(out, quality=95)

    issues = []
    for name, b in (("l1", b1), ("l2", b2), ("sub", bsub), ("bar", bbar)):
        if b[0] < 0 or b[2] > W or b[1] < 0 or b[3] > H:
            issues.append(f"{name} 越界 {b}")
    if b2[3] > H * 0.5:
        issues.append(f"主标题第二行底部 {b2[3]} 越过中线")
    for name, b in (("l1", b1), ("l2", b2), ("sub", bsub)):
        if b[2] > W - 20:
            issues.append(f"{name} 右边界 {b[2]} 过于贴近画布")
    if luma(FG) - luma(BG) < 120 or luma(acc) - luma(BG) < 60:
        issues.append("对比度不足")
    print(f"{'OK ' if not issues else 'WARN'} {c['slug'][:52]:54s} "
          f"l1={f_l1.size}px l2={f_l2.size}px sub={f_sub.size}px bar={f_bar.size}px"
          + ("" if not issues else "  ⚠ " + "; ".join(issues)))
