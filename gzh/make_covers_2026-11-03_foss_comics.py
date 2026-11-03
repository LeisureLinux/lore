# -*- coding: utf-8 -*-
"""F/OSS Comics 五部曲 + 系列导读 的公众号封面（1200×675）。"""
from PIL import Image, ImageDraw, ImageFont

W, H = 1200, 675
FONT_B = "/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc"
FONT_BOLD = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
BASE = "/home/axu/codex/writings/lore/gzh"

CFG = [
    dict(dir="2026-11-03_foss-comics-unix-bsd-series-guide",
         accent=(232, 168, 84), bg=(18, 15, 11),
         t1="一条磁带如何长成", t1sz=58,
         t2="一个操作系统", t2sz=58,
         sub="F/OSS Comics Unix 与 BSD 五部曲  ｜  完整中文翻译",
         info="FreeLAMP.com  ·  技术史 / 开源运动  ·  2026-11-03"),
    dict(dir="2026-11-03_foss-comics-09-unix-philosophy",
         accent=(126, 186, 214), bg=(11, 14, 18),
         t1="Unix 哲学不是", t1sz=56,
         t2="先有纲领、后有实践", t2sz=52,
         sub="F/OSS Comics 第 9 篇  ｜  完整中文翻译",
         info="FreeLAMP.com  ·  技术史 / Unix  ·  2026-11-03"),
    dict(dir="2026-11-03_foss-comics-10-dennis-ritchie",
         accent=(214, 140, 130), bg=(18, 13, 13),
         t1="我不过是", t1sz=58,
         t2="签发工资条而已", t2sz=56,
         sub="Dennis Ritchie 生平  ｜  F/OSS Comics 第 10 篇 完整中文翻译",
         info="FreeLAMP.com  ·  技术史 / 人物传记  ·  2026-11-03"),
    dict(dir="2026-11-03_foss-comics-11-bsd-part1",
         accent=(150, 196, 140), bg=(11, 16, 12),
         t1="你把代码给了他们，", t1sz=52,
         t2="他们又改好送回来", t2sz=52,
         sub="Unix 源码进入 UC Berkeley  ｜  F/OSS Comics 第 11 篇 完整中文翻译",
         info="FreeLAMP.com  ·  技术史 / BSD  ·  2026-11-03"),
    dict(dir="2026-11-03_foss-comics-12-vi-editor",
         accent=(196, 168, 110), bg=(17, 15, 11),
         t1="「我写它是为了", t1sz=54,
         t2="电传打字机」", t2sz=56,
         sub="vi 的诞生  ｜  F/OSS Comics 第 12 篇 完整中文翻译",
         info="FreeLAMP.com  ·  技术史 / 编辑器  ·  2026-11-03"),
    dict(dir="2026-11-03_foss-comics-13-bsd-beginnings",
         accent=(170, 150, 214), bg=(14, 12, 18),
         t1="调优内核、修 bug，", t1sz=52,
         t2="然后继续复制", t2sz=56,
         sub="BSD 的开端  ｜  F/OSS Comics 第 13 篇 完整中文翻译",
         info="FreeLAMP.com  ·  技术史 / BSD  ·  2026-11-03"),
]


def build(c):
    im = Image.new("RGB", (W, H), c["bg"])
    d = ImageDraw.Draw(im)
    for y in range(H):
        t = y / (H - 1)
        d.line([(0, y), (W, y)], fill=(int(c["bg"][0] + 16 * t),
                                       int(c["bg"][1] + 20 * t),
                                       int(c["bg"][2] + 16 * t)))
    d.rectangle([(0, 0), (W, 7)], fill=c["accent"])
    pad = 70
    f1 = ImageFont.truetype(FONT_B, c["t1sz"], index=2)
    f2 = ImageFont.truetype(FONT_B, c["t2sz"], index=2)
    fs = ImageFont.truetype(FONT_BOLD, 26, index=2)
    fi = ImageFont.truetype(FONT_BOLD, 26, index=2)
    d.text((pad, 140), c["t1"], font=f1, fill=(246, 247, 250))
    d.text((pad, 245), c["t2"], font=f2, fill=c["accent"])
    d.text((pad, 400), c["sub"], font=fs, fill=(178, 186, 200))
    bar_y = H - 90
    d.rounded_rectangle([(pad, bar_y), (W - pad, bar_y + 52)], radius=8, fill=(28, 32, 44))
    d.rectangle([(pad, bar_y), (W - pad, bar_y + 2)], fill=c["accent"])
    d.text((pad + 16, bar_y + 16), c["info"], font=fi, fill=(216, 222, 234))
    b1 = d.textbbox((pad, 140), c["t1"], font=f1)
    b2 = d.textbbox((pad, 245), c["t2"], font=f2)
    bs = d.textbbox((pad, 400), c["sub"], font=fs)
    bi = d.textbbox((pad + 16, bar_y + 16), c["info"], font=fi)
    warn = []
    if b1[2] > W - 40:
        warn.append(f"t1 越界 {b1[2]}")
    if b2[2] > W - 40:
        warn.append(f"t2 越界 {b2[2]}")
    if bs[2] > W - 40:
        warn.append(f"sub 越界 {bs[2]}")
    if bi[2] > W - 40:
        warn.append(f"info 越界 {bi[2]}")
    im.save(f"{BASE}/{c['dir']}/cover.png")
    print(f"✅ {c['dir']}: t1={b1[2]} t2={b2[2]} sub={bs[2]} info={bi[2]}"
          + (f"  ⚠️ {'; '.join(warn)}" if warn else "  (无越界)"))


for c in CFG:
    build(c)
