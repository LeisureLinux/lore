# -*- coding: utf-8 -*-
from PIL import Image, ImageDraw, ImageFont

W, H = 1200, 675
FONT_B = "/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc"
FONT_BOLD = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
BASE = "/home/axu/codex/writings/lore/gzh"

CFG = [
 {"dir": "2026-10-27_nvidia-openshell-agent-runtime",
  "accent": (76, 141, 255), "bg": (10, 12, 22),
  "t1": "NVIDIA OpenShell", "t1sz": 76,
  "t2": "给 agent 造一个默认不给权限的运行时", "t2sz": 44,
  "sub": "内核级强制 + SMT 形式化验证 ｜ 策略变更前先证明它不越界",
  "info": "FreeLAMP.com  ·  OpenShell / AI agent 权限  ·  2026-10-27"},
 {"dir": "2026-10-27_openbsd-wine-port-gs-emulation",
  "accent": (245, 158, 11), "bg": (18, 14, 10),
  "t1": "OpenBSD 把 Wine 移植回来了", "t1sz": 64,
  "t2": "打开大门的是一套手写的 x86 指令解码器", "t2sz": 44,
  "sub": "%gs 模拟 · 三级回退 · 44 个 patch ｜ 十五年，两次尝试",
  "info": "FreeLAMP.com  ·  OpenBSD / Wine / gsbase  ·  2026-10-27"},
 {"dir": "2026-10-27_hackios-xnu-ios16-on-android",
  "accent": (244, 114, 182), "bg": (16, 12, 18),
  "t1": "HackiOS：iOS 跑在安卓上", "t1sz": 68,
  "t2": "而且 iOS 用户态一字节未改", "t2sz": 48,
  "sub": "XNU 开源内核 ｜ 不刷机全在 RAM ｜ QEMU 12GB 磁盘即可",
  "info": "FreeLAMP.com  ·  HackiOS / XNU / 开源研究  ·  2026-10-27"},
]

def make(c):
    im = Image.new("RGB", (W, H), c["bg"])
    d = ImageDraw.Draw(im)
    ar, ag, ab = c["accent"]
    for y in range(H):
        t = y / (H - 1)
        d.line([(0, y), (W, y)], fill=(int(c["bg"][0] + 18*t), int(c["bg"][1] + 18*t), int(c["bg"][2] + 26*t)))
    d.rectangle([(0, 0), (W, 7)], fill=c["accent"])
    pad = 70
    f1 = ImageFont.truetype(FONT_B, c["t1sz"], index=2)
    f2 = ImageFont.truetype(FONT_B, c["t2sz"], index=2)
    fs = ImageFont.truetype(FONT_BOLD, 32, index=2)
    fi = ImageFont.truetype(FONT_BOLD, 26, index=2)
    d.text((pad, 140), c["t1"], font=f1, fill=(246, 247, 250))
    d.text((pad, 250), c["t2"], font=f2, fill=c["accent"])
    d.text((pad, 400), c["sub"], font=fs, fill=(178, 186, 200))
    bar_y = H - 90
    d.rounded_rectangle([(pad, bar_y), (W - pad, bar_y + 52)], radius=8, fill=(30, 32, 44))
    d.rectangle([(pad, bar_y), (W - pad, bar_y + 2)], fill=c["accent"])
    d.text((pad + 16, bar_y + 16), c["info"], font=fi, fill=(216, 222, 234))
    print(c["dir"], "| t1", d.textbbox((pad,140), c["t1"], font=f1)[2],
          "| t2", d.textbbox((pad,250), c["t2"], font=f2)[2],
          "| sub", d.textbbox((pad,400), c["sub"], font=fs)[2])
    out = f"{BASE}/{c['dir']}/cover.png"
    im.save(out)
    print("  saved", out)

for c in CFG:
    make(c)
