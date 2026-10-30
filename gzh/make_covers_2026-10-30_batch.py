# -*- coding: utf-8 -*-
from PIL import Image, ImageDraw, ImageFont
W, H = 1200, 675
FONT_B = "/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc"
FONT_BOLD = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
BASE = "/home/axu/codex/writings/lore/gzh"
CFG = [
 {"dir": "2026-10-30_binance-6-36-billion-hack-eip-7702-presigned-authorization",
  "accent": (245, 158, 11), "bg": (14, 16, 22),
  "t1": "63.6 亿美元，20 分钟", "t1sz": 62,
  "t2": "史上最大规模加密盗窃", "t2sz": 50,
  "sub": "EIP-7702 批量预签 ｜ 私钥没泄露，被偷走的是签名能力",
  "info": "FreeLAMP.com  ·  供应链安全 / 链上取证 / TRM  ·  2026-10-30"},
 {"dir": "2026-10-30_cursor-claude-code-extension-ssh-backdoor",
  "accent": (239, 68, 68), "bg": (16, 14, 16),
  "t1": "66 行 loader，5000 个开发者", "t1sz": 56,
  "t2": "Cursor 市场的 Claude Code 扩展被投毒", "t2sz": 40,
  "sub": "SSH 后门 ｜ 反向隧道 ｜ 卸载 ≠ 清除",
  "info": "FreeLAMP.com  ·  供应链安全 / 开发者工具 / IOC  ·  2026-10-30"},
]
for c in CFG:
    im = Image.new("RGB", (W, H), c["bg"]); d = ImageDraw.Draw(im)
    for y in range(H):
        t = y/(H-1)
        d.line([(0,y),(W,y)], fill=(int(c["bg"][0]+18*t), int(c["bg"][1]+18*t), int(c["bg"][2]+24*t)))
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
    print(c["dir"])
    print("   t1", d.textbbox((pad,140), c["t1"], font=f1)[2], "t2", d.textbbox((pad,250), c["t2"], font=f2)[2],
          "sub", d.textbbox((pad,400), c["sub"], font=fs)[2])
    im.save(f"{BASE}/{c['dir']}/cover.png"); print("   saved")
