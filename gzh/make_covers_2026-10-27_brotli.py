# -*- coding: utf-8 -*-
from PIL import Image, ImageDraw, ImageFont

W, H = 1200, 675
FONT_B = "/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc"
FONT_BOLD = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
OUT = "/home/axu/codex/writings/lore/gzh/2026-10-27_php-windows-brotli-cve-2026-111497/cover.png"

def main():
    im = Image.new("RGB", (W, H), (13, 15, 23))
    d = ImageDraw.Draw(im)
    for y in range(H):
        t = y / (H - 1)
        d.line([(0, y), (W, y)], fill=(int(15 + 18*t), int(17 + 18*t), int(26 + 28*t)))
    d.rectangle([(0, 0), (W, 7)], fill=(56, 189, 248))
    pad = 70
    f1 = ImageFont.truetype(FONT_B, 64, index=2)
    f2 = ImageFont.truetype(FONT_B, 48, index=2)
    fs = ImageFont.truetype(FONT_BOLD, 31, index=2)
    fi = ImageFont.truetype(FONT_BOLD, 26, index=2)
    t1 = "PHP 第五天再发 Windows 包"
    t2 = "而这次修的东西不在 PHP 源码里"
    d.text((pad, 140), t1, font=f1, fill=(246, 247, 250))
    d.text((pad, 245), t2, font=f2, fill=(56, 189, 248))
    sub = "版本号没变 ｜ 修复代码在源码里躺了 8 个月 ｜ Accept-Encoding 删 br 无效"
    d.text((pad, 400), sub, font=fs, fill=(178, 186, 200))
    bar_y = H - 90
    d.rounded_rectangle([(pad, bar_y), (W - pad, bar_y + 52)], radius=8, fill=(28, 32, 46))
    d.rectangle([(pad, bar_y), (W - pad, bar_y + 2)], fill=(56, 189, 248))
    d.text((pad + 16, bar_y + 16), "FreeLAMP.com  ·  PHP / Brotli / 供应链  ·  2026-10-27",
           font=fi, fill=(216, 222, 234))
    print("t1", d.textbbox((pad,140), t1, font=f1)[2], "| t2", d.textbbox((pad,250), t2, font=f2)[2],
          "| sub", d.textbbox((pad,400), sub, font=fs)[2])
    im.save(OUT)
    print("saved", OUT)

if __name__ == "__main__":
    main()
