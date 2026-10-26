# -*- coding: utf-8 -*-
from PIL import Image, ImageDraw, ImageFont

W, H = 1200, 675
FONT_B = "/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc"
FONT_BOLD = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
OUT = "/home/axu/codex/writings/lore/gzh/2026-10-27_emaki-arch-niri-desktop-intro/cover.png"

def main():
    im = Image.new("RGB", (W, H), (14, 12, 22))
    d = ImageDraw.Draw(im)
    # warm dusk gradient (Emaki = valley at sunset)
    for y in range(H):
        t = y / (H - 1)
        r = int(30 + 60 * t)
        g = int(18 + 26 * t)
        b = int(52 + 40 * t)
        d.line([(0, y), (W, y)], fill=(r, g, b))
    d.rectangle([(0, 0), (W, 7)], fill=(244, 162, 97))
    pad = 70
    t1_font = ImageFont.truetype(FONT_B, 92, index=2)
    t2_font = ImageFont.truetype(FONT_B, 56, index=2)
    sub_font = ImageFont.truetype(FONT_BOLD, 34, index=2)
    info_font = ImageFont.truetype(FONT_BOLD, 26, index=2)

    t1 = "Emaki"
    t2 = "一个不需要你配置的 Linux 桌面"
    d.text((pad, 130), t1, font=t1_font, fill=(250, 246, 240))
    d.text((pad, 250), t2, font=t2_font, fill=(244, 162, 97))
    sub = "Arch + niri 滚动平铺 ｜ 13 天 9 个版本 ｜ 一个人做的"
    d.text((pad, 400), sub, font=sub_font, fill=(206, 194, 200))

    bar_y = H - 90
    d.rounded_rectangle([(pad, bar_y), (W - pad, bar_y + 52)], radius=8, fill=(34, 28, 44))
    d.rectangle([(pad, bar_y), (W - pad, bar_y + 2)], fill=(244, 162, 97))
    d.text((pad + 16, bar_y + 16), "FreeLAMP.com  ·  Emaki / niri / Wayland  ·  2026-10-27",
           font=info_font, fill=(226, 214, 216))

    for txt, font, y0 in [(t1, t1_font, 130), (t2, t2_font, 250)]:
        print(txt, d.textbbox((pad, y0), txt, font=font))
    im.save(OUT)
    print("saved", OUT)

if __name__ == "__main__":
    main()
