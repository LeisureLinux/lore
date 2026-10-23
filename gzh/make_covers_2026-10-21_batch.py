#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""2026-10-21 三篇公众号封面（1200x675）。"""
import os
from PIL import Image, ImageDraw, ImageFont

BASE = os.path.dirname(os.path.abspath(__file__))
FB = "/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc"
FR = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
def F(sz, kind="black"):
    return ImageFont.truetype(FR if kind == "bold" else FB, sz, index=2)

W, H = 1200, 675
BG = (10, 13, 18); FG = (240, 244, 250); MUTED = (150, 160, 172)

CFG = [
    dict(slug="2026-10-21_truenas-2026-proxmox-plugin-27rc1-veeam-ready", accent=(80, 190, 220),
         l1="备份服务器", l2="这个盒子可以消失了",
         sub="TrueNAS 一次更新三件事，而它们指向同一个方向",
         bar="Proxmox 插件 · 27 RC.1 · Veeam All-In-One 认证",
         tag="存储平台在吞掉周边"),
]

for c in CFG:
    out = os.path.join(BASE, c["slug"], "cover.png")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    acc = c["accent"]
    im = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(im)
    for y in range(H):
        t = y / H
        d.line([(0, y), (W, y)], fill=(int(10+20*t), int(13+10*t), int(18+16*t)))
    d.rectangle([0, 0, W, 7], fill=acc)

    # 左上角标签
    tag = c["tag"]
    ft = F(22, "bold")
    tb = d.textbbox((0, 0), tag, font=ft)
    tw, th = tb[2]-tb[0], tb[3]-tb[1]
    d.rounded_rectangle([56, 52, 56+tw+34, 52+th+22], 6,
                        fill=(int(acc[0]*0.22), int(acc[1]*0.22), int(acc[2]*0.22)),
                        outline=acc, width=1)
    d.text((56+17, 52+9), tag, font=ft, fill=acc)

    d.text((56, 118), c["l1"], font=F(60), fill=FG)
    d.text((56, 202), c["l2"], font=F(60), fill=acc)
    d.text((58, 300), c["sub"], font=F(27, "bold"), fill=MUTED)

    bx, by = 56, H-128
    d.rounded_rectangle([bx, by, W-bx, by+72], 12, fill=(22, 28, 36), outline=acc, width=2)
    d.text((bx+20, by+24), c["bar"], font=F(23, "bold"), fill=FG)

    im.save(out, quality=95)

    # ── 自检 ──
    problems = []
    for txt, fnt, pos, nm in [
        (c["l1"], F(60), (56, 118), "L1"),
        (c["l2"], F(60), (56, 202), "L2"),
        (c["sub"], F(27, "bold"), (58, 300), "SUB"),
        (c["bar"], F(23, "bold"), (bx+20, by+24), "BAR"),
    ]:
        bb = d.textbbox(pos, txt, font=fnt)
        if bb[0] < 0 or bb[2] > W or bb[3] > H:
            problems.append(f"{nm} 越界 {bb}")
        limit = W-56 if nm != "BAR" else W-bx-16
        if bb[2] > limit:
            problems.append(f"{nm} 右超 {bb[2]}>{limit}")
    bb1 = d.textbbox((56, 118), c["l1"], font=F(60))
    bb2 = d.textbbox((56, 202), c["l2"], font=F(60))
    bb3 = d.textbbox((58, 300), c["sub"], font=F(27, "bold"))
    if bb2[1]-bb1[3] < 8: problems.append(f"L1/L2 间距 {bb2[1]-bb1[3]}<8")
    if bb3[1]-bb2[3] < 8: problems.append(f"L2/SUB 间距 {bb3[1]-bb2[3]}<8")
    if by-bb3[3] < 8: problems.append(f"SUB/BAR 间距 {by-bb3[3]}<8")
    crop = int((H - W/2.35)/2)
    if bb1[1] < crop or bb3[3] > H-crop:
        problems.append(f"2.35:1 裁切不安全 crop={crop}")
    # 亮度对比
    def lum(x1,y1,x2,y2):
        px=[im.getpixel((x,y)) for y in range(y1,y2,3) for x in range(x1,x2,3)]
        ls=[0.299*r+0.587*g+0.114*b for r,g,b in px]
        return max(ls)-min(ls)
    for nm,(x1,y1,x2,y2) in {'L1':(56,118,900,190),'L2':(56,202,900,280),
                              'SUB':(58,300,1140,344),'BAR':(70,547,1140,619)}.items():
        if lum(x1,y1,x2,y2) < 100:
            problems.append(f"{nm} 对比不足")

    print(f'{im.size}  {os.path.basename(out)}')
    print('   自检:', '全部通过 ✅' if not problems else problems)
