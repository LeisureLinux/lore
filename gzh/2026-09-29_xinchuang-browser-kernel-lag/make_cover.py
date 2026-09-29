#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成《信创浏览器内核版本碎片化》公众号封面图。
规格：1200×675（16:9），公众号封面推荐尺寸。
产物：lore/gzh/2026-09-29_xinchuang-browser-kernel-lag/cover.png
"""
import os
from PIL import Image, ImageDraw, ImageFont

OUT = "/home/axu/codex/writings/lore/gzh/2026-09-29_xinchuang-browser-kernel-lag/cover.png"

W, H = 1200, 675
FB = "/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc"
FR = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
FM = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"   # Mono SC 在同 ttc 的 index 7

def F(sz, kind="black"):
    if kind == "mono":
        return ImageFont.truetype(FM, sz, index=7)   # Noto Sans Mono CJK SC
    if kind == "bold":
        return ImageFont.truetype(FR, sz, index=2)   # Noto Sans CJK SC Bold
    return ImageFont.truetype(FB, sz, index=2)       # Noto Sans CJK SC Black

BG     = (10, 13, 18)
FG     = (240, 244, 250)
MUTED  = (130, 140, 152)
GREEN  = (48, 212, 117)
RED    = (255, 84, 84)
ORANGE = (233, 120, 32)
BLUE   = (88, 166, 255)
YELLOW = (255, 209, 74)

im = Image.new("RGB", (W, H), BG)
d = ImageDraw.Draw(im)

# 竖向渐变背景
for y in range(H):
    t = y / H
    d.line([(0, y), (W, y)], fill=(int(10 + 16 * t), int(13 + 18 * t), int(18 + 26 * t)))

# 顶部橙条
d.rectangle([0, 0, W, 7], fill=ORANGE)

# 主标题
d.text((56, 54), "信创浏览器", font=F(74), fill=FG)
d.text((56, 146), "内核落后 1–3 年", font=F(74), fill=RED)

# 副标题
d.text((58, 250), "Chrome 两周一个大版本，信创还停在 120", font=F(30, "bold"), fill=MUTED)

# 核心：版本号对撞
# 左：社区（绿）
lx, ly = 60, 330
d.rounded_rectangle([lx, ly, lx + 330, ly + 170], 18, fill=(18, 34, 24), outline=GREEN, width=3)
d.text((lx + 26, ly + 18), "社区 Chromium", font=F(26, "bold"), fill=GREEN)
d.text((lx + 26, ly + 58), "152", font=F(92, "mono"), fill=GREEN)
d.text((lx + 240, ly + 112), "最新", font=F(26, "bold"), fill=MUTED)

# 右：信创（红）
rx, ry = 810, 330
d.rounded_rectangle([rx, ry, rx + 330, ry + 170], 18, fill=(36, 20, 20), outline=RED, width=3)
d.text((rx + 26, ry + 18), "信创浏览器", font=F(26, "bold"), fill=RED)
d.text((rx + 26, ry + 56), "120", font=F(92, "mono"), fill=RED)
d.text((rx + 232, ry + 112), "常见值", font=F(26, "bold"), fill=MUTED)

# 中间箭头 + 差距
d.text((530, 386), "VS", font=F(56), fill=YELLOW)

# 底部：碎片清单
bx, by = 60, 540
d.text((bx, by), "93", font=F(40, "mono"), fill=ORANGE)
d.text((bx + 76, by + 8), "deepin", font=F(26, "bold"), fill=MUTED)
d.text((bx + 230, by), "108", font=F(40, "mono"), fill=ORANGE)
d.text((bx + 330, by + 8), "UOS 浏览器", font=F(26, "bold"), fill=MUTED)
d.text((bx + 540, by), "120", font=F(40, "mono"), fill=ORANGE)
d.text((bx + 640, by + 8), "360 信创版", font=F(26, "bold"), fill=MUTED)
d.text((bx + 850, by), "132", font=F(40, "mono"), fill=ORANGE)
d.text((bx + 950, by + 8), "奇安信", font=F(26, "bold"), fill=MUTED)

# 底条
d.rectangle([0, H - 52, W, H], fill=(16, 20, 26))
d.text((56, H - 43), "LeisureLinux · 聊内核和发行版", font=F(25, "bold"), fill=(150, 160, 170))
d.text((W - 300, H - 43), "Ungoogled-Chromium 过渡方案", font=F(24, "bold"), fill=GREEN)

im.save(OUT, quality=95)
print("OK", OUT, im.size)
