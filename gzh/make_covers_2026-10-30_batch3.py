# -*- coding: utf-8 -*-
from PIL import Image, ImageDraw, ImageFont
W, H = 1200, 675
FONT_B = "/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc"
FONT_BOLD = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
BASE = "/home/axu/codex/writings/lore/gzh"
CFG = [
 {"dir": "2026-10-30_teamviewer-cve-2026-111585-viewer-side-rce",
  "accent": (56, 189, 248), "bg": (10, 16, 22),
  "t1": "你连上去的机器", "t1sz": 58,
  "t2": "可以反过来打你", "t2sz": 54,
  "sub": "CVE-2026-111585 ｜ 一次 32 位乘法 ｜ TeamViewer 15.83 修复",
  "info": "FreeLAMP.com  ·  远程控制 / 整数溢出 / 攻防反转  ·  2026-10-30"},
 {"dir": "2026-10-30_php2shell-ai-assisted-attack-roots-25-servers",
  "accent": (250, 204, 21), "bg": (18, 17, 10),
  "t1": "Claude Code、DeepSeek、Kimi", "t1sz": 50,
  "t2": "都在攻击者的工具箱里", "t2sz": 46,
  "sub": "PHP2Shell 打到域控 ｜ 25 台设备 ｜ 22 台停放",
  "info": "FreeLAMP.com  ·  AI 辅助攻击 / 事件分析 / 横向移动  ·  2026-10-30"},
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
