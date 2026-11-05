# -*- coding: utf-8 -*-
from PIL import Image, ImageDraw, ImageFont
W, H = 1200, 675
FONT_B = "/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc"
FONT_BOLD = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
BASE = "/home/axu/codex/writings/lore/gzh"
c = dict(dir="2026-11-05_openssh-password-auth-bypass-musl-crypt",
         accent=(140, 200, 180), bg=(10, 15, 13),
         t1="不需要密码", t1sz=58,
         t2="一次就登录成功", t2sz=54,
         sub="OpenSSH 认证绕过解读  ｜  musl crypt · 硬约定 · Alpine",
         info="FreeLAMP.com  ·  技术解读 / 开源安全  ·  2026-11-05")
im = Image.new("RGB", (W, H), c["bg"]); d = ImageDraw.Draw(im)
for y in range(H):
    t = y/(H-1)
    d.line([(0,y),(W,y)], fill=(int(c["bg"][0]+16*t), int(c["bg"][1]+20*t), int(c["bg"][2]+16*t)))
d.rectangle([(0,0),(W,7)], fill=c["accent"])
pad = 70
f1 = ImageFont.truetype(FONT_B, c["t1sz"], index=2); f2 = ImageFont.truetype(FONT_B, c["t2sz"], index=2)
fs = ImageFont.truetype(FONT_BOLD, 26, index=2); fi = ImageFont.truetype(FONT_BOLD, 26, index=2)
d.text((pad,140), c["t1"], font=f1, fill=(246,247,250))
d.text((pad,245), c["t2"], font=f2, fill=c["accent"])
d.text((pad,400), c["sub"], font=fs, fill=(178,186,200))
bar_y = H-90
d.rounded_rectangle([(pad,bar_y),(W-pad,bar_y+52)], radius=8, fill=(28,32,44))
d.rectangle([(pad,bar_y),(W-pad,bar_y+2)], fill=c["accent"])
d.text((pad+16, bar_y+16), c["info"], font=fi, fill=(216,222,234))
for n,b in (("t1",d.textbbox((pad,140),c["t1"],font=f1)),("t2",d.textbbox((pad,245),c["t2"],font=f2)),
            ("sub",d.textbbox((pad,400),c["sub"],font=fs)),("info",d.textbbox((pad+16,bar_y+16),c["info"],font=fi))):
    print(f"  {n}={b[2]}"+("  ⚠️" if b[2]>W-40 else ""))
im.save(f"{BASE}/{c['dir']}/cover.png"); print("saved")
