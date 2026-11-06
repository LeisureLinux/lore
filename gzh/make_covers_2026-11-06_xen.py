# -*- coding: utf-8 -*-
"""2026-11-06 Xen XSA-523 客机逃逸一文的公众号封面（1200×675）。"""
from PIL import Image, ImageDraw, ImageFont

W, H = 1200, 675
FONT_B = "/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc"
FONT_BOLD = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
BASE = "/home/axu/codex/writings/lore/gzh"

c = dict(dir="2026-11-06_xen-xsa-523-grant-copy-guest-escape",
         accent=(122, 162, 214), bg=(11, 13, 16),
         t1="一个 2015 年的优化，", t1sz=52,
         t2="十一年后被推翻", t2sz=58,
         sub="Xen XSA-523 解读  ｜  客机逃逸 · 性能优化反噬 · AI 参与发现",
         info="FreeLAMP.com  ·  技术解读 / 安全  ·  2026-11-06")

im = Image.new("RGB", (W, H), c["bg"])
d = ImageDraw.Draw(im)
for y in range(H):
    t = y / (H - 1)
    d.line([(0, y), (W, y)], fill=(int(c["bg"][0] + 14 * t),
                                   int(c["bg"][1] + 17 * t),
                                   int(c["bg"][2] + 24 * t)))
d.rectangle([(0, 0), (W, 7)], fill=c["accent"])
pad = 70
f1 = ImageFont.truetype(FONT_B, c["t1sz"], index=2)
f2 = ImageFont.truetype(FONT_B, c["t2sz"], index=2)
fs = ImageFont.truetype(FONT_BOLD, 25, index=2)
fi = ImageFont.truetype(FONT_BOLD, 25, index=2)
d.text((pad, 140), c["t1"], font=f1, fill=(246, 247, 250))
d.text((pad, 240), c["t2"], font=f2, fill=c["accent"])
d.text((pad, 400), c["sub"], font=fs, fill=(178, 186, 200))
bar_y = H - 90
d.rounded_rectangle([(pad, bar_y), (W - pad, bar_y + 52)], radius=8, fill=(24, 27, 34))
d.rectangle([(pad, bar_y), (W - pad, bar_y + 2)], fill=c["accent"])
d.text((pad + 16, bar_y + 16), c["info"], font=fi, fill=(216, 222, 234))
for n, b in (("t1", d.textbbox((pad, 140), c["t1"], font=f1)),
             ("t2", d.textbbox((pad, 240), c["t2"], font=f2)),
             ("sub", d.textbbox((pad, 400), c["sub"], font=fs)),
             ("info", d.textbbox((pad + 16, bar_y + 16), c["info"], font=fi))):
    print(f"  {n}={b[2]}" + ("  ⚠️ 越界" if b[2] > W - 40 else ""))
im.save(f"{BASE}/{c['dir']}/cover.png")
print("saved", im.size)
