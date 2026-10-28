# -*- coding: utf-8 -*-
from PIL import Image, ImageDraw, ImageFont
W, H = 1200, 675
FONT_B = "/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc"
FONT_BOLD = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
OUT = "/home/axu/codex/writings/lore/gzh/2026-10-27_ghostbsd-26-2-freebsd-15-1/cover.png"
im = Image.new("RGB", (W, H), (12, 14, 18))
d = ImageDraw.Draw(im)
for y in range(H):
    t = y/(H-1)
    d.line([(0,y),(W,y)], fill=(int(14+14*t), int(16+16*t), int(22+22*t)))
d.rectangle([(0,0),(W,7)], fill=(71, 132, 255))
pad = 70
f1 = ImageFont.truetype(FONT_B, 74, index=2)
f2 = ImageFont.truetype(FONT_B, 44, index=2)
fs = ImageFont.truetype(FONT_BOLD, 30, index=2)
fi = ImageFont.truetype(FONT_BOLD, 26, index=2)
t1 = "GhostBSD 26.2"
t2 = "安装器和首次启动，被拆开了"
sub = "FreeBSD 15.1 ｜ ZFS boot environment ｜ 安装器内 GELI 整机加密"
d.text((pad,140), t1, font=f1, fill=(246,247,250))
d.text((pad,245), t2, font=f2, fill=(71,132,255))
d.text((pad,400), sub, font=fs, fill=(178,186,200))
bar_y = H-90
d.rounded_rectangle([(pad,bar_y),(W-pad,bar_y+52)], radius=8, fill=(28,32,44))
d.rectangle([(pad,bar_y),(W-pad,bar_y+2)], fill=(71,132,255))
d.text((pad+16, bar_y+16), "FreeLAMP.com  ·  GhostBSD / FreeBSD / ZFS  ·  2026-10-27", font=fi, fill=(216,222,234))
print("t1", d.textbbox((pad,140), t1, font=f1)[2], "| t2", d.textbbox((pad,250), t2, font=f2)[2], "| sub", d.textbbox((pad,400), sub, font=fs)[2])
im.save(OUT); print("saved", OUT)
