# -*- coding: utf-8 -*-
"""2026-11-03 FreeRDP 3.33 与 Linux Mint 两篇的公众号封面（1200×675）。"""
from PIL import Image, ImageDraw, ImageFont

W, H = 1200, 675
FONT_B = "/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc"
FONT_BOLD = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
BASE = "/home/axu/codex/writings/lore/gzh"

CFG = [
    dict(dir="2026-11-03_freerdp-3-33-wasm-ai-prs",
         accent=(120, 190, 200), bg=(10, 14, 17),
         t1="RDP 跑进了浏览器，", t1sz=52,
         t2="维护者被 PR 淹没", t2sz=56,
         sub="FreeRDP 3.33 解读  ｜  WebAssembly  ·  AI PR 泛滥",
         info="FreeLAMP.com  ·  技术解读 / 开源治理  ·  2026-11-03"),
    dict(dir="2026-11-03_linux-mint-30-years-distrohopping",
         accent=(160, 200, 130), bg=(12, 16, 11),
         t1="30 年漂移之后", t1sz=56,
         t2="终于到家", t2sz=58,
         sub="Linux Mint  ·  Flatpak  ·  Wayland  ·  zram",
         info="FreeLAMP.com  ·  技术解读 / Linux 桌面  ·  2026-11-03"),
]


def build(c):
    im = Image.new("RGB", (W, H), c["bg"])
    d = ImageDraw.Draw(im)
    for y in range(H):
        t = y / (H - 1)
        d.line([(0, y), (W, y)], fill=(int(c["bg"][0] + 16 * t),
                                       int(c["bg"][1] + 20 * t),
                                       int(c["bg"][2] + 16 * t)))
    d.rectangle([(0, 0), (W, 7)], fill=c["accent"])
    pad = 70
    f1 = ImageFont.truetype(FONT_B, c["t1sz"], index=2)
    f2 = ImageFont.truetype(FONT_B, c["t2sz"], index=2)
    fs = ImageFont.truetype(FONT_BOLD, 26, index=2)
    fi = ImageFont.truetype(FONT_BOLD, 26, index=2)
    d.text((pad, 140), c["t1"], font=f1, fill=(246, 247, 250))
    d.text((pad, 245), c["t2"], font=f2, fill=c["accent"])
    d.text((pad, 400), c["sub"], font=fs, fill=(178, 186, 200))
    bar_y = H - 90
    d.rounded_rectangle([(pad, bar_y), (W - pad, bar_y + 52)], radius=8, fill=(28, 32, 44))
    d.rectangle([(pad, bar_y), (W - pad, bar_y + 2)], fill=c["accent"])
    d.text((pad + 16, bar_y + 16), c["info"], font=fi, fill=(216, 222, 234))
    b1 = d.textbbox((pad, 140), c["t1"], font=f1)
    b2 = d.textbbox((pad, 245), c["t2"], font=f2)
    bs = d.textbbox((pad, 400), c["sub"], font=fs)
    bi = d.textbbox((pad + 16, bar_y + 16), c["info"], font=fi)
    warn = []
    for n, b in (("t1", b1), ("t2", b2), ("sub", bs), ("info", bi)):
        if b[2] > W - 40:
            warn.append(f"{n} 越界 {b[2]}")
    im.save(f"{BASE}/{c['dir']}/cover.png")
    print(f"✅ {c['dir']}: t1={b1[2]} t2={b2[2]} sub={bs[2]} info={bi[2]}"
          + (f"  ⚠️ {'; '.join(warn)}" if warn else "  (无越界)"))


for c in CFG:
    build(c)
