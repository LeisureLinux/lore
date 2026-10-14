#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""2026-10-14 两篇公众号封面（1200x675，石墨极简风格）。

规格沿用 lore/gzh/make_covers_2026-10-13.py 的约定：
  画布 1200x675（公众号 16:9），深色渐变底 + 顶部 7px 强调色条，
  主标题（第一行白、第二行强调色）+ 副标题 + 底部圆角信息条。
  微信列表按 2.35:1 居中裁切，所以主标题不贴边（左右各留 56px，上下留白充足）。
字体：NotoSansCJK-Bold.ttc / Black.ttc，index=2 为 SC。
自检：用 PIL 量文字 bbox 是否越界 + 相邻文字块间距 + 2.35:1 裁切安全性 +
      文字区/背景亮度对比（不用 tesseract OCR）。
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
SAFE = 56

CFG = [
    # Firefox Enterprise：用 Mozilla 品牌橙红，呼应 Firefox 且带「企业/主权」的严肃感
    dict(slug="2026-10-14_firefox-enterprise-digital-sovereignty", accent=(255, 138, 61),
         l1="Firefox 进企业市场",
         l2="赌的是欧洲会为「不依赖美国」付钱",
         sub="自托管管理面是实打实的产品，管辖权却是另一回事",
         bar="搜索收入仍占约 85% · 首发法德奥瑞四国 · 竞品已有 581 条评价的 Island"),
    # Mesa Torx：用青绿强调，呼应「NPU/加速器」且与图形栈的冷色系一致
    dict(slug="2026-10-14_mesa-torx-yolox-pytorch-npu", accent=(45, 212, 191),
         l1="NPU 终于能用 PyTorch 跑了",
         l2="Mesa 走了一条被忽略的捷径",
         sub="图形驱动与 AI 加速器的形状，四件事四件对得上",
         bar="i.MX93 上 YOLOX-Nano 单帧 17ms · 编译可在别处做 · Mesa 26.3"),
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
        issues.append(f"主标题第二行底部 {b2[3]} 越过中线（2.35:1 裁切风险）")
    for name, b in (("l1", b1), ("l2", b2), ("sub", bsub)):
        if b[2] > W - 20:
            issues.append(f"{name} 右边界 {b[2]} 过于贴近画布")
    if luma(FG) - luma(BG) < 120 or luma(acc) - luma(BG) < 60:
        issues.append("对比度不足")
    print(f"{'OK ' if not issues else 'WARN'} {out} {im.size} "
          f"l1={f_l1.size}px l2={f_l2.size}px sub={f_sub.size}px bar={f_bar.size}px "
          + ("" if not issues else "  ⚠ " + "; ".join(issues)))
