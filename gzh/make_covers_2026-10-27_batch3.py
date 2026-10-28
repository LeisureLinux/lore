# -*- coding: utf-8 -*-
from PIL import Image, ImageDraw, ImageFont

W, H = 1200, 675
FONT_B = "/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc"
FONT_BOLD = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
BASE = "/home/axu/codex/writings/lore/gzh"

CFG = [
 {"dir": "2026-10-27_goahead-three-tls-bugs",
  "accent": (248, 113, 113), "bg": (16, 12, 14),
  "t1": "GoAhead 的三个 TLS 漏洞", "t1sz": 70,
  "t2": "都犯了同一个错：配置了，却没执行", "t2sz": 44,
  "sub": "CRL 加载但不执行 ｜ DH 模数只剩 1 字节 ｜ 链深度被绕过",
  "info": "FreeLAMP.com  ·  GoAhead / TLS / 嵌入式安全  ·  2026-10-27"},
 {"dir": "2026-10-27_wiz-php2shell-exploitation-attempts",
  "accent": (34, 197, 94), "bg": (12, 16, 13),
  "t1": "php2shell 一周实测", "t1sz": 72,
  "t2": "攻击者卡在「同一个 worker」上", "t2sz": 46,
  "sub": "暴露面降 47.9% ｜ 全球 10% 组织被尝试 ｜ 尚无成功的端到端利用",
  "info": "FreeLAMP.com  ·  php2shell / 蜜罐 / 事件响应  ·  2026-10-27"},
 {"dir": "2026-10-27_tailscale-ssh-investigation-update",
  "accent": (56, 189, 248), "bg": (12, 14, 18),
  "t1": "Tailscale SSH 权限提升", "t1sz": 70,
  "t2": "官方：不建议所有人关掉", "t2sz": 46,
  "sub": "但给了一条开关：TS_SSH_DISABLE_FORWARDING=1",
  "info": "FreeLAMP.com  ·  Tailscale / SSH / 零信任  ·  2026-10-27"},
 {"dir": "2026-10-27_ghostty-1-4-0-release",
  "accent": (168, 85, 247), "bg": (14, 12, 18),
  "t1": "Ghostty 1.4", "t1sz": 82,
  "t2": "Kitty 图形 100% 完整，内存降到 16 KiB", "t2sz": 42,
  "sub": "解析快 5.7 倍 ｜ 10 个安全公告 ｜ 粘贴保护没把回车当行尾",
  "info": "FreeLAMP.com  ·  Ghostty / 终端 / 性能  ·  2026-10-27"},
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
    fs = ImageFont.truetype(FONT_BOLD, 30, index=2)
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
