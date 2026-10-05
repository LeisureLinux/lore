#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成《国庆回老家，万物皆隧道》公众号封面图（1200x675，石墨极简风格）。"""
import os
from PIL import Image, ImageDraw, ImageFont

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "cover.png")
FB = "/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc"
FR = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"


def F(sz, kind="black"):
    if kind == "bold":
        return ImageFont.truetype(FR, sz, index=2)
    return ImageFont.truetype(FB, sz, index=2)


BG = (10, 13, 18)
FG = (240, 244, 250)
MUTED = (130, 140, 152)
ACCENT = (56, 189, 248)      # 隧道蓝
ACCENT2 = (139, 92, 246)     # 收敛紫
W, H = 1200, 675

im = Image.new("RGB", (W, H), BG)
d = ImageDraw.Draw(im)

# 渐变底
for y in range(H):
    t = y / H
    d.line([(0, y), (W, y)],
           fill=(int(10 + 16 * t), int(13 + 18 * t), int(18 + 26 * t)))

# 顶部主题色条（蓝->紫渐变，呼应"一条隧道/收敛"）
for x in range(W):
    t = x / W
    d.line([(x, 0), (x, 7)],
           fill=(int(56 + (139 - 56) * t), int(189 + (92 - 189) * t), int(248 + (246 - 248) * t)))

# 主标题
d.text((56, 70), "国庆回老家", font=F(66), fill=FG)
d.text((56, 162), "万物皆隧道", font=F(66), fill=ACCENT)

# 副标题
d.text((58, 262), "把家里所有服务收敛到只剩一个 SSH 端口", font=F(28, "bold"), fill=MUTED)

# 中部：左侧"改造前"，右侧"改造后"
box_y = 330
d.rounded_rectangle([56, box_y, 560, box_y + 130], 12,
                    fill=(26, 20, 22), outline=(120, 60, 60), width=2)
d.text((76, box_y + 16), "改造前", font=F(22, "bold"), fill=(220, 120, 120))
d.text((76, box_y + 52), "N 个端口暴露 · 可达性绑网络位置", font=F(20, "bold"), fill=MUTED)
d.text((76, box_y + 88), "在家能用，出门就废", font=F(20, "bold"), fill=MUTED)

d.rounded_rectangle([640, box_y, 1144, box_y + 130], 12,
                    fill=(18, 28, 26), outline=(60, 160, 120), width=2)
d.text((660, box_y + 16), "改造后", font=F(22, "bold"), fill=(90, 210, 150))
d.text((660, box_y + 52), "全部只听 127.0.0.1 · 隧道按需拉取", font=F(20, "bold"), fill=MUTED)
d.text((660, box_y + 88), "在家在外，同一份配置", font=F(20, "bold"), fill=MUTED)

# 箭头
d.text((598, box_y + 48), "→", font=F(44), fill=ACCENT)

# 底部信息条
bx, by = 56, H - 118
d.rounded_rectangle([bx, by, W - bx, by + 66], 12,
                    fill=(22, 28, 36), outline=ACCENT2, width=2)
d.text((bx + 20, by + 18),
       "DNS 53 · 代理 8888 · RDP 3389 · RustDesk 21118 · 模型网关 7863 · 只留 22",
       font=F(21, "bold"), fill=FG)

im.save(OUT, quality=95)
print(f"OK {OUT} {im.size}")
