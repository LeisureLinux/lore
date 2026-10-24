# -*- coding: utf-8 -*-
from PIL import Image, ImageDraw, ImageFont
import os

W, H = 1200, 675
FONT_B = "/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc"
FONT_BOLD = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
OUT = "/home/axu/codex/writings/lore/gzh/2026-10-24_macos-no-longer-unix-open-group/cover.png"

def main():
    im = Image.new("RGB", (W, H), (12, 16, 24))
    d = ImageDraw.Draw(im)
    # gradient background
    for y in range(H):
        t = y / (H - 1)
        r = int(15 + 20 * t)
        g = int(20 + 16 * t)
        b = int(35 + 30 * t)
        d.line([(0, y), (W, y)], fill=(r, g, b))
    # accent top strip
    d.rectangle([(0, 0), (W, 7)], fill=(239, 68, 68))
    # guidelines
    pad = 70
    # title font
    title_font = ImageFont.truetype(FONT_B, 84, index=2)
    title2_font = ImageFont.truetype(FONT_B, 60, index=2)
    sub_font = ImageFont.truetype(FONT_BOLD, 40, index=2)
    info_font = ImageFont.truetype(FONT_BOLD, 26, index=2)
    t1 = "macOS 不再是 Unix"
    t2 = "Open Group 注册表上 Apple 的条目空了"
    # draw t1 white
    y = 150
    d.text((pad, y), t1, font=title_font, fill=(245, 247, 250))
    # t2 accent lower
    y2 = 250
    d.text((pad, y2), t2, font=title2_font, fill=(239, 68, 68))
    # subtitle
    sub = "macOS 26 Tahoe 证书仍可打开 · UNIX 03 · 2026-10 注册表上 Apple 消失"
    d.text((pad, 400), sub, font=sub_font, fill=(180, 188, 200))
    # bottom bar
    bar_y = H - 90
    d.rounded_rectangle([(pad, bar_y), (W - pad, bar_y + 52)], radius=8, fill=(239, 68, 68, 200) if False else (30, 36, 50))
    d.rectangle([(pad, bar_y), (W - pad, bar_y + 2)], fill=(239, 68, 68))
    info = "FreeLAMP.com  ·  macOS / UNIX / Open Group  ·  2026-10-24"
    d.text((pad + 16, bar_y + 16), info, font=info_font, fill=(220, 226, 236))

    # self-check bbox
    import PIL.ImageDraw as ID
    for (txt, font, y0) in [(t1, title_font, 150), (t2, title_font, 250)]:
        bbox = d.textbbox((pad, y0), txt, font=font)
        print(txt, bbox)
    im.save(OUT)
    print("saved", OUT)

if __name__ == "__main__":
    main()
