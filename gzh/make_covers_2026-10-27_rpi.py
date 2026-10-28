# -*- coding: utf-8 -*-
from PIL import Image, ImageDraw, ImageFont
W, H = 1200, 675
FONT_B = "/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc"
FONT_BOLD = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
OUT = "/home/axu/codex/writings/lore/gzh/2026-10-27_raspberry-pi-zero-3-w-pi-4-model-a/cover.png"
im = Image.new("RGB", (W, H), (14, 16, 20))
d = ImageDraw.Draw(im)
for y in range(H):
    t = y/(H-1)
    d.line([(0,y),(W,y)], fill=(int(16+18*t), int(18+18*t), int(24+22*t)))
d.rectangle([(0,0),(W,7)], fill=(228, 33, 36))
pad = 70
f1 = ImageFont.truetype(FONT_B, 62, index=2)
f2 = ImageFont.truetype(FONT_B, 46, index=2)
fs = ImageFont.truetype(FONT_BOLD, 30, index=2)
fi = ImageFont.truetype(FONT_BOLD, 26, index=2)
t1 = "树莓派悄悄放了两块新板子的设备树"
t2 = "Zero 3 W 换上 Pi 4 的芯片，Pi 4 Model A 回来了"
sub = "BCM2711 ｜ 天线切换 ｜ SPI flash 引导器 ｜ 电源键"
d.text((pad,140), t1, font=f1, fill=(246,247,250))
d.text((pad,245), t2, font=f2, fill=(228,33,36))
d.text((pad,400), sub, font=fs, fill=(178,186,200))
bar_y = H-90
d.rounded_rectangle([(pad,bar_y),(W-pad,bar_y+52)], radius=8, fill=(28,32,44))
d.rectangle([(pad,bar_y),(W-pad,bar_y+2)], fill=(228,33,36))
d.text((pad+16, bar_y+16), "FreeLAMP.com  ·  Raspberry Pi / 设备树 / 开源硬件  ·  2026-10-27", font=fi, fill=(216,222,234))
print("t1", d.textbbox((pad,140), t1, font=f1)[2], "| t2", d.textbbox((pad,250), t2, font=f2)[2], "| sub", d.textbbox((pad,400), sub, font=fs)[2])
im.save(OUT); print("saved", OUT)
