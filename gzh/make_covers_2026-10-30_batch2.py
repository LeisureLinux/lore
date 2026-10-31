# -*- coding: utf-8 -*-
from PIL import Image, ImageDraw, ImageFont
W, H = 1200, 675
FONT_B = "/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc"
FONT_BOLD = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
BASE = "/home/axu/codex/writings/lore/gzh"
CFG = [
 {"dir": "2026-10-30_cve-2026-98432-mptcp-kernel-uaf-claude-remote-root",
  "accent": (96, 165, 250), "bg": (12, 14, 20),
  "t1": "两行代码，11 年", "t1sz": 66,
  "t2": "Claude 用它换来了 root", "t2sz": 50,
  "sub": "CVE-2026-98432 ｜ MPTCP UAF ｜ Go 默认开 MPTCP",
  "info": "FreeLAMP.com  ·  Linux 内核 / UAF / RCU / 供应链  ·  2026-10-30"},
 {"dir": "2026-10-30_fragnesia-cve-2026-46300-php2shell-panos-root",
  "accent": (248, 113, 113), "bg": (18, 12, 14),
  "t1": "19000 台防火墙", "t1sz": 62,
  "t2": "24 台被 root，25 台被利用", "t2sz": 44,
  "sub": "PHP2Shell + Fragnesia ｜ 通往 Active Directory 的完整链",
  "info": "FreeLAMP.com  ·  事件分析 / 横向移动 / KEV  ·  2026-10-30"},
 {"dir": "2026-10-30_beeper-ebpf-in-kernel-http-parsing",
  "accent": (74, 222, 128), "bg": (10, 16, 14),
  "t1": "把 HTTP 解析搬进内核", "t1sz": 58,
  "t2": "eBPF 做出 4.5 倍吞吐", "t2sz": 50,
  "sub": "Beeper ｜ ETH Zürich + NYU + NVIDIA ｜ LPC 2026",
  "info": "FreeLAMP.com  ·  eBPF / 内核态 / 性能优化  ·  2026-10-30"},
]
for c in CFG:
    im = Image.new("RGB", (W, H), c["bg"]); d = ImageDraw.Draw(im)
    for y in range(H):
        t = y/(H-1)
        d.line([(0,y),(W,y)], fill=(int(c["bg"][0]+18*t), int(c["bg"][1]+20*t), int(c["bg"][2]+24*t)))
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
