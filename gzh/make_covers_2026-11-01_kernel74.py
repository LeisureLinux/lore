# -*- coding: utf-8 -*-
from PIL import Image, ImageDraw, ImageFont
W, H = 1200, 675
FONT_B = "/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc"
FONT_BOLD = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
BASE = "/home/axu/codex/writings/lore/gzh"
c = {"dir": "2026-11-01_linux-7-4-merge-window-ai-review-sashiko",
  "accent": (163, 190, 140), "bg": (16, 18, 16),
  "t1": "19,671 个提交", "t1sz": 60,
  "t2": "内核史上最大合并窗口", "t2sz": 46,
  "sub": "AI 从「写补丁」转向「审补丁」 ｜ Sashiko ｜ OverlayFS 真漏洞",
  "info": "FreeLAMP.com  ·  Linux 内核 / AI 代码评审 / 治理  ·  2026-11-01"}
im = Image.new("RGB", (W, H), c["bg"]); d = ImageDraw.Draw(im)
for y in range(H):
    t = y/(H-1)
    d.line([(0,y),(W,y)], fill=(int(c["bg"][0]+18*t), int(c["bg"][1]+22*t), int(c["bg"][2]+18*t)))
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
