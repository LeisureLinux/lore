# -*- coding: utf-8 -*-
from PIL import Image, ImageDraw, ImageFont

W, H = 1200, 675
FONT_B = "/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc"
FONT_BOLD = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
OUT = "/home/axu/codex/writings/lore/gzh/2026-10-26_linux-desktop-first-decade-ten-turning-points/cover.png"

def main():
    im = Image.new("RGB", (W, H), (12, 16, 24))
    d = ImageDraw.Draw(im)
    for y in range(H):
        t = y / (H - 1)
        d.line([(0, y), (W, y)], fill=(int(14 + 22 * t), int(18 + 20 * t), int(32 + 34 * t)))
    d.rectangle([(0, 0), (W, 7)], fill=(168, 85, 247))
    pad = 70
    t1_font = ImageFont.truetype(FONT_B, 80, index=2)
    t2_font = ImageFont.truetype(FONT_B, 56, index=2)
    sub_font = ImageFont.truetype(FONT_BOLD, 36, index=2)
    info_font = ImageFont.truetype(FONT_BOLD, 26, index=2)

    t1 = "Linux 桌面的前三十年"
    t2 = "十次转折，与一个反复出现的教训"
    d.text((pad, 140), t1, font=t1_font, fill=(245, 247, 250))
    d.text((pad, 245), t2, font=t2_font, fill=(168, 85, 247))
    sub = "Debian → Qt 分家 → Knoppix → Ubuntu → KDE 4 → Cinnamon"
    d.text((pad, 400), sub, font=sub_font, fill=(176, 186, 200))

    bar_y = H - 90
    d.rounded_rectangle([(pad, bar_y), (W - pad, bar_y + 52)], radius=8, fill=(30, 34, 50))
    d.rectangle([(pad, bar_y), (W - pad, bar_y + 2)], fill=(168, 85, 247))
    d.text((pad + 16, bar_y + 16), "FreeLAMP.com  ·  Linux 桌面史  ·  2026-10-26",
           font=info_font, fill=(218, 224, 234))

    for txt, font, y0 in [(t1, t1_font, 140), (t2, t2_font, 245)]:
        print(txt, d.textbbox((pad, y0), txt, font=font))
    im.save(OUT)
    print("saved", OUT)

if __name__ == "__main__":
    main()
