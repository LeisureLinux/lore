# -*- coding: utf-8 -*-
from PIL import Image, ImageDraw, ImageFont
W, H = 1200, 675
FONT_B = "/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc"
FONT_BOLD = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
BASE = "/home/axu/codex/writings/lore/gzh"
CFG = [
 {"dir": "2026-10-27_uefi-edk2-pxe-icmp-cve-2026-97631",
  "accent": (248, 113, 113), "bg": (16, 12, 14),
  "t1": "一个 16 岁的缓冲区溢出", "t1sz": 70,
  "t2": "全球大多数服务器的固件都能被远程打穿", "t2sz": 40,
  "sub": "CVE-2026-97631 ｜ EDK II PXE ICMP ｜ CVSS 9.5 ｜ ring 0",
  "info": "FreeLAMP.com  ·  UEFI / 固件安全 / 预执行环境  ·  2026-10-27"},
 {"dir": "2026-10-27_android-private-dns-ddr-doh",
  "accent": (250, 204, 21), "bg": (16, 14, 10),
  "t1": "安卓其实早就有系统级 DoH", "t1sz": 66,
  "t2": "只是被藏在一个 feature flag 后面", "t2sz": 48,
  "sub": "RFC 9462 DDR ｜ Private DNS ｜ 两条 flag ｜ 免 root 不耗电",
  "info": "FreeLAMP.com  ·  Android / DNS 加密 / DDR  ·  2026-10-27"},
]
for c in CFG:
    im = Image.new("RGB", (W, H), c["bg"]); d = ImageDraw.Draw(im)
    for y in range(H):
        t = y/(H-1)
        d.line([(0,y),(W,y)], fill=(int(c["bg"][0]+16*t), int(c["bg"][1]+16*t), int(c["bg"][2]+22*t)))
    d.rectangle([(0,0),(W,7)], fill=c["accent"])
    pad = 70
    f1 = ImageFont.truetype(FONT_B, c["t1sz"], index=2)
    f2 = ImageFont.truetype(FONT_B, c["t2sz"], index=2)
    fs = ImageFont.truetype(FONT_BOLD, 30, index=2)
    fi = ImageFont.truetype(FONT_BOLD, 26, index=2)
    d.text((pad,140), c["t1"], font=f1, fill=(246,247,250))
    d.text((pad,245), c["t2"], font=f2, fill=c["accent"])
    d.text((pad,400), c["sub"], font=fs, fill=(178,186,200))
    bar_y = H-90
    d.rounded_rectangle([(pad,bar_y),(W-pad,bar_y+52)], radius=8, fill=(28,32,44))
    d.rectangle([(pad,bar_y),(W-pad,bar_y+2)], fill=c["accent"])
    d.text((pad+16, bar_y+16), c["info"], font=fi, fill=(216,222,234))
    print(c["dir"], "| t1", d.textbbox((pad,140), c["t1"], font=f1)[2],
          "| t2", d.textbbox((pad,250), c["t2"], font=f2)[2],
          "| sub", d.textbbox((pad,400), c["sub"], font=fs)[2])
    im.save(f"{BASE}/{c['dir']}/cover.png"); print("  saved")
