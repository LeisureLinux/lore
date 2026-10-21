#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""2026-10-21 php2shell 封面（1200x675）。"""
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
    dict(slug="2026-10-21_php2shell-cve-2026-109618-109619-root-cause-distro-patching",
         accent=(255, 92, 92),
         l1="补丁还没发布", l2="攻击就已经开始了",
         sub="一个躺了二十年的 PHP 缺陷，Hello World 也能被一击拿下",
         bar="longjmp 根因 · 390 个文件的补丁 · Debian/Ubuntu/RHEL 打补丁指南",
         tag="CVSS 9.2 · 已在被利用"),
]

for c in CFG:
    out = os.path.join(BASE, c["slug"], "cover.png")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    acc = c["accent"]
    im = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(im)
    for y in range(H):
        t = y / H
        d.line([(0, y), (W, y)], fill=(int(10+20*t), int(13+10*t), int(18+14*t)))
    d.rectangle([0, 0, W, 7], fill=acc)

    # 左上角警示标签
    tag = c["tag"]
    ft = F(22, "bold")
    tb = d.textbbox((0, 0), tag, font=ft)
    tw, th = tb[2]-tb[0], tb[3]-tb[1]
    d.rounded_rectangle([56, 52, 56+tw+34, 52+th+22], 6, fill=(58, 18, 18), outline=acc, width=1)
    d.text((56+17, 52+9), tag, font=ft, fill=acc)

    d.text((56, 118), c["l1"], font=F(64), fill=FG)
    d.text((56, 206), c["l2"], font=F(64), fill=acc)
    d.text((58, 306), c["sub"], font=F(28, "bold"), fill=MUTED)

    bx, by = 56, H-128
    d.rounded_rectangle([bx, by, W-bx, by+72], 12, fill=(22, 28, 36), outline=(58, 18, 18), width=2)
    d.text((bx+20, by+24), c["bar"], font=F(23, "bold"), fill=FG)

    im.save(out, quality=95)

    # ── 自检 ──
    problems = []
    # 文字越界
    for txt, fnt, pos, nm in [
        (c["l1"], F(64), (56, 118), "L1"),
        (c["l2"], F(64), (56, 206), "L2"),
        (c["sub"], F(28, "bold"), (58, 306), "SUB"),
        (c["bar"], F(23, "bold"), (bx+20, by+24), "BAR"),
    ]:
        bb = d.textbbox(pos, txt, font=fnt)
        if bb[0] < 0 or bb[2] > W or bb[3] > H:
            problems.append(f"{nm} 越界 {bb}")
        right_limit = W-56 if nm != "BAR" else W-bx-16
        if bb[2] > right_limit:
            problems.append(f"{nm} 右侧超限 bb[2]={bb[2]} > {right_limit}")
    # 相邻块间距 ≥8px
    bb1 = d.textbbox((56, 118), c["l1"], font=F(64))
    bb2 = d.textbbox((56, 206), c["l2"], font=F(64))
    bb3 = d.textbbox((58, 306), c["sub"], font=F(28, "bold"))
    if bb2[1] - bb1[3] < 8: problems.append(f"L1/L2 间距 {bb2[1]-bb1[3]} < 8")
    if bb3[1] - bb2[3] < 8: problems.append(f"L2/SUB 间距 {bb3[1]-bb2[3]} < 8")
    if by - bb3[3] < 8: problems.append(f"SUB/BAR 间距 {by-bb3[3]} < 8")
    # 2.35:1 裁切安全（微信列表居中裁切 → 上下各裁 (675 - 1200/2.35)/2 ≈ 82px）
    crop = int((H - W/2.35)/2)
    if bb1[1] < crop or bb3[3] > H-crop:
        problems.append(f"2.35:1 裁切不安全 crop={crop}")

    print("OK", out, im.size)
    print("   自检:", "全部通过" if not problems else problems)
