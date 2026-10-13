#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成《内网域名没有一个是安全的》公众号封面图（1200x675，石墨极简风格）。

规格与配色沿用 lore/gzh/make_covers_2026-10-06.py 的约定：
  画布 1200x675（公众号 16:9），深色渐变底 + 顶部 7px 强调色条，
  主标题（第一行白、第二行强调色）+ 副标题 + 底部圆角信息条。
字体：NotoSansCJK-Bold.ttc index=2（SC Bold）/ Black.ttc index=2（SC Black）。
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

# 深青蓝强调色：呼应「DNS / 域名」主题，与同属网络安全类的
# 2026-10-06_wildcard-listen-to-lan-only（青 #38BDF8）保持系列感。
ACCENT = (56, 189, 248)
WARN = (249, 115, 22)   # 暖橙：呼应正文里 .lan 的风险标记

CFG = dict(
    slug="2026-10-14_internal-tld-name-collision",
    l1="内网域名",
    l2="没有一个是安全的",
    sub=".lan / .local / .home / .corp 的真实状态，以及 ICANN 给出的 .internal",
    bar="IANA 登记表核验 · 根区实测 NXDOMAIN · .lan 是明确风险 · 隔离比换域名更重要",
    accent=ACCENT,
)

out = os.path.join(BASE, CFG["slug"], "cover.png")
os.makedirs(os.path.dirname(out), exist_ok=True)
acc = CFG["accent"]

im = Image.new("RGB", (W, H), BG)
d = ImageDraw.Draw(im)

# 垂直渐变底
for y in range(H):
    t = y / H
    d.line([(0, y), (W, y)], fill=(int(10 + 16 * t), int(13 + 18 * t), int(18 + 26 * t)))

# 顶部强调条
d.rectangle([0, 0, W, 7], fill=acc)

# 主标题：第一行白、第二行强调色
d.text((56, 70), CFG["l1"], font=F(62), fill=FG)
d.text((56, 156), CFG["l2"], font=F(62), fill=acc)

# 副标题（.lan / .local ... 用 mono 更有「域名」质感）
d.text((58, 252), CFG["sub"], font=F(27, "bold"), fill=MUTED)

# 底部圆角信息条
bx, by = 56, H - 128
d.rounded_rectangle([bx, by, W - bx, by + 72], 12, fill=(22, 28, 36), outline=acc, width=2)
d.text((bx + 20, by + 24), CFG["bar"], font=F(22, "bold"), fill=FG)

# 右侧风险角标：视觉上呼应正文里 .lan 的风险定性
tag = ".lan = 明确风险"
tf = F(22, "bold")
tw = d.textlength(tag, font=tf)
d.rounded_rectangle([W - 56 - tw - 32, 258, W - 56, 258 + 44], 8,
                    fill=(38, 20, 12), outline=WARN, width=2)
d.text((W - 56 - tw - 16, 258 + 10), tag, font=tf, fill=WARN)

im.save(out, quality=95)
print("OK", out, im.size)
