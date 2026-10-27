# -*- coding: utf-8 -*-
from PIL import Image, ImageDraw, ImageFont

W, H = 1200, 675
FONT_B = "/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc"
FONT_BOLD = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
BASE = "/home/axu/codex/writings/lore/gzh"

CFG = [
 {"dir": "2026-10-27_tyler-cowen-outrun-ai-hackers",
  "accent": (245, 158, 11), "bg": (16, 14, 12),
  "t1": "怎么跑得比 AI 黑客快", "t1sz": 68,
  "t2": "Cowen 的答案，最扎实的一条不是技术", "t2sz": 44,
  "sub": "10% 组织被尝试利用 ｜ 攻击峰值在午夜 ｜ lrand48 与 25 年的曲线种子",
  "info": "FreeLAMP.com  ·  AI 安全 / 密码学 / 应急响应  ·  2026-10-27"},
 {"dir": "2026-10-27_1password-for-agents",
  "accent": (34, 197, 94), "bg": (12, 18, 14),
  "t1": "1Password for Agents", "t1sz": 74,
  "t2": "给 agent 开通账号，而不是把密码交给它", "t2sz": 46,
  "sub": "请求 → 批准 → 自动填充 ｜ agent 全程看不到密码",
  "info": "FreeLAMP.com  ·  凭证管理 / AI agent 安全  ·  2026-10-27"},
]

def make(c):
    im = Image.new("RGB", (W, H), c["bg"])
    d = ImageDraw.Draw(im)
    ar, ag, ab = c["accent"]
    for y in range(H):
        t = y / (H - 1)
        d.line([(0, y), (W, y)], fill=(int(c["bg"][0]+16*t), int(c["bg"][1]+16*t), int(c["bg"][2]+22*t)))
    d.rectangle([(0, 0), (W, 7)], fill=c["accent"])
    pad = 70
    f1 = ImageFont.truetype(FONT_B, c["t1sz"], index=2)
    f2 = ImageFont.truetype(FONT_B, c["t2sz"], index=2)
    fs = ImageFont.truetype(FONT_BOLD, 31, index=2)
    fi = ImageFont.truetype(FONT_BOLD, 26, index=2)
    d.text((pad, 140), c["t1"], font=f1, fill=(246, 247, 250))
    d.text((pad, 245), c["t2"], font=f2, fill=c["accent"])
    d.text((pad, 400), c["sub"], font=fs, fill=(178, 186, 200))
    bar_y = H - 90
    d.rounded_rectangle([(pad, bar_y), (W-pad, bar_y+52)], radius=8, fill=(28, 32, 44))
    d.rectangle([(pad, bar_y), (W-pad, bar_y+2)], fill=c["accent"])
    d.text((pad+16, bar_y+16), c["info"], font=fi, fill=(216, 222, 234))
    print(c["dir"], "| t1", d.textbbox((pad,140), c["t1"], font=f1)[2],
          "| t2", d.textbbox((pad,250), c["t2"], font=f2)[2],
          "| sub", d.textbbox((pad,400), c["sub"], font=fs)[2])
    im.save(f"{BASE}/{c['dir']}/cover.png")
    print("  saved")

for c in CFG: make(c)
