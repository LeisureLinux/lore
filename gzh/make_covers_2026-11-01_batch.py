# -*- coding: utf-8 -*-
from PIL import Image, ImageDraw, ImageFont
W, H = 1200, 675
FONT_B = "/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc"
FONT_BOLD = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
BASE = "/home/axu/codex/writings/lore/gzh"
CFG = [
 {"dir": "2026-11-01_cve-2026-98432-nftables-mitigation-detection",
  "accent": (96, 165, 250), "bg": (11, 15, 22),
  "t1": "打不了补丁时", "t1sz": 62,
  "t2": "怎么挡", "t2sz": 58,
  "sub": "CVE-2026-98432 ｜ nftables 应急规则 ｜ 怎么查谁开着 MPTCP",
  "info": "FreeLAMP.com  ·  漏洞缓解 / 入侵检测 / 运维  ·  2026-11-01"},
 {"dir": "2026-11-01_email-encryption-threat-model-dane-mta-sts",
  "accent": (167, 139, 250), "bg": (16, 14, 22),
  "t1": "「邮件加密」", "t1sz": 62,
  "t2": "到底在防谁", "t2sz": 58,
  "sub": "四层保护 ｜ 四个不能同时满足的目标 ｜ 威胁模型优先",
  "info": "FreeLAMP.com  ·  邮件安全 / 端到端加密 / 隐私  ·  2026-11-01"},
]
for c in CFG:
    im = Image.new("RGB", (W, H), c["bg"]); d = ImageDraw.Draw(im)
    for y in range(H):
        t = y/(H-1)
        d.line([(0,y),(W,y)], fill=(int(c["bg"][0]+18*t), int(c["bg"][1]+19*t), int(c["bg"][2]+24*t)))
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
    print(c["dir"], "| t1", d.textbbox((pad,140), c["t1"], font=f1)[2],
          "t2", d.textbbox((pad,250), c["t2"], font=f2)[2], "sub", d.textbbox((pad,400), c["sub"], font=fs)[2])
    im.save(f"{BASE}/{c['dir']}/cover.png"); print("   saved")
