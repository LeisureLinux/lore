#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""2026-10-06 三篇公众号封面（1200x675）。"""
import os
from PIL import Image, ImageDraw, ImageFont

BASE = os.path.dirname(os.path.abspath(__file__))
FB = "/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc"
FR = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
def F(sz, kind="black"):
    return ImageFont.truetype(FR if kind == "bold" else FB, sz, index=2)
W, H = 1200, 675
BG = (10, 13, 18); FG = (240, 244, 250); MUTED = (130, 140, 152)

CFG = [
    dict(slug="2026-10-06_zram-streams-rework", accent=(88, 166, 255),
         l1="zram 重构读写流", l2="读不再被写挡住",
         sub="内存省下几十到几百 KB，但真正的看点是优先级反转",
         bar="per-CPU 读流 + 写流 · 重压缩单例上下文 · 已在 LKML 送审"),
    dict(slug="2026-10-06_ansible-zero-trust-network", accent=(233, 84, 32),
         l1="零信任网络 5 步", l2="Ansible 怎么落地",
         sub="以及这篇厂商文稿没回答的三个问题",
         bar="策略即代码 · OPA 门控自动化自身 · EDA 三阶段 · 对照 NIST"),
    dict(slug="2026-10-06_confidential-computing-use-cases", accent=(170, 130, 240),
         l1="机密计算四种模式", l2="但证明 ≠ 承诺",
         sub="证明环境可信，不等于证明它不会乱来",
         bar="Intel TDX · 远程证明 · 受保护外包 / 多方分析 / 安全 SaaS"),
]

for c in CFG:
    out = os.path.join(BASE, c["slug"], "cover.png")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    acc = c["accent"]
    im = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(im)
    for y in range(H):
        t = y / H
        d.line([(0, y), (W, y)], fill=(int(10+16*t), int(13+18*t), int(18+26*t)))
    d.rectangle([0, 0, W, 7], fill=acc)
    d.text((56, 70), c["l1"], font=F(62), fill=FG)
    d.text((56, 156), c["l2"], font=F(62), fill=acc)
    d.text((58, 252), c["sub"], font=F(28, "bold"), fill=MUTED)
    bx, by = 56, H-128
    d.rounded_rectangle([bx, by, W-bx, by+72], 12, fill=(22, 28, 36), outline=acc, width=2)
    d.text((bx+20, by+24), c["bar"], font=F(23, "bold"), fill=FG)
    im.save(out, quality=95)
    print("OK", out, im.size)
