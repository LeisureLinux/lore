#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""2026-10-22 公众号封面（1200x675）。"""
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
MUTED = (150, 160, 172)

CFG = [
    dict(
        slug="2026-10-22_mail-autoconfig-thunderbird-k9-zero-touch-setup",
        accent=(96, 180, 235),
        l1="只输邮箱和密码",
        l2="服务器自己找上来",
        sub="给自建邮件域做一套 autoconfig：SRV + XML + 证书",
        bar="通配符会遮住域名 · 证书要含 SAN · fail2ban 会封自己人",
        tag="邮件自动配置",
    ),
]

for c in CFG:
    out = os.path.join(BASE, c["slug"], "cover.png")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    acc = c["accent"]
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    # 深色渐变底
    for y in range(H):
        t = y / H
        d.line([(0, y), (W, y)],
               fill=(int(10 + 20 * t), int(13 + 12 * t), int(18 + 18 * t)))
    # 顶部强调色条
    d.rectangle([0, 0, W, 7], fill=acc)

    # 左上角标签
    tag = c["tag"]
    ft = F(22, "bold")
    tb = d.textbbox((0, 0), tag, font=ft)
    tw, th = tb[2] - tb[0], tb[3] - tb[1]
    d.rounded_rectangle([56, 52, 56 + tw + 34, 52 + th + 22], 6,
                        fill=(int(acc[0] * 0.22), int(acc[1] * 0.22), int(acc[2] * 0.22)),
                        outline=acc, width=1)
    d.text((56 + 17, 52 + 9), tag, font=ft, fill=acc)

    # 主标题两行
    d.text((56, 118), c["l1"], font=F(60), fill=FG)
    d.text((56, 202), c["l2"], font=F(60), fill=acc)
    # 副标题
    d.text((58, 300), c["sub"], font=F(27, "bold"), fill=MUTED)

    # 底部信息条
    bx, by = 56, H - 128
    d.rounded_rectangle([bx, by, W - bx, by + 72], 12,
                        fill=(22, 28, 36), outline=acc, width=2)
    d.text((bx + 20, by + 24), c["bar"], font=F(23, "bold"), fill=FG)

    im.save(out, "PNG")
    # 自检：量文字 bbox 是否越界
    for label, txt, font, x, y in [
        ("l1", c["l1"], F(60), 56, 118),
        ("l2", c["l2"], F(60), 56, 202),
        ("sub", c["sub"], F(27, "bold"), 58, 300),
        ("bar", c["bar"], F(23, "bold"), bx + 20, by + 24),
    ]:
        bb = d.textbbox((x, y), txt, font=font)
        ok = bb[2] <= W - 20 and bb[3] <= H - 8
        print(f"  {label}: bbox={tuple(int(v) for v in bb)} {'OK' if ok else 'OVERFLOW!'}")
    print("written:", out)
