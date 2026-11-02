# -*- coding: utf-8 -*-
from PIL import Image, ImageDraw, ImageFont
W, H = 1200, 675
FONT_B = "/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc"
FONT_BOLD = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
BASE = "/home/axu/codex/writings/lore/gzh"
c = {"dir": "2026-11-01_ipfs-is-a-bad-idea-shipyard-winds-down",
  "accent": (94, 234, 212), "bg": (10, 18, 20),
  "t1": "「IPFS 是个坏主意」", "t1sz": 54,
  "t2": "和它背后那场退场", "t2sz": 50,
  "sub": "Shipyard 9-30 终止运营 ｜ Kubo / Helia / Boxo 失去维护者",
  "info": "FreeLAMP.com  ·  去中心化存储 / 开源治理 / 架构  ·  2026-11-01"}
im = Image.new("RGB", (W, H), c["bg"]); d = ImageDraw.Draw(im)
for y in range(H):
    t = y/(H-1)
    d.line([(0,y),(W,y)], fill=(int(c["bg"][0]+16*t), int(c["bg"][1]+24*t), int(c["bg"][2]+24*t)))
d.rectangle([(0,0),(W,7)], fill=c["accent"])
pad = 70
f1 = ImageFont.truetype(FONT_B, c["t1sz"], index=2)
f2 = ImageFont.truetype(FONT_B, c["t2sz"], index=2)
fs = ImageFont.truetype(FONT_BOLD, 27, index=2)
fi = ImageFont.truetype(FONT_BOLD, 26, index=2)
d.text((pad,140), c["t1"], font=f1, fill=(246,247,250))
d.text((pad,245), c["t2"], font=f2, fill=c["accent"])
d.text((pad,400), c["sub"], font=fs, fill=(178,186,200))
bar_y = H-90
d.rounded_rectangle([(pad,bar_y),(W-pad,bar_y+52)], radius=8, fill=(28,32,44))
d.rectangle([(pad,bar_y),(W-pad,bar_y+2)], fill=c["accent"])
d.text((pad+16, bar_y+16), c["info"], font=fi, fill=(216,222,234))
print("t1", d.textbbox((pad,140), c["t1"], font=f1)[2], "t2", d.textbbox((pad,250), c["t2"], font=f2)[2],
      "sub", d.textbbox((pad,400), c["sub"], font=fs)[2])
im.save(f"{BASE}/{c['dir']}/cover.png"); print("saved")
