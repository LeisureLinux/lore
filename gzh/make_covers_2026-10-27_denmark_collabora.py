# -*- coding: utf-8 -*-
from PIL import Image, ImageDraw, ImageFont

W, H = 1200, 675
FONT_B = "/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc"
FONT_BOLD = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
OUT = "/home/axu/codex/writings/lore/gzh/2026-10-27_denmark-collabora-office-pilot-failed/cover.png"

def main():
    im = Image.new("RGB", (W, H), (14, 16, 22))
    d = ImageDraw.Draw(im)
    for y in range(H):
        t = y / (H - 1)
        d.line([(0, y), (W, y)], fill=(int(16 + 18 * t), int(18 + 16 * t), int(30 + 24 * t)))
    d.rectangle([(0, 0), (W, 7)], fill=(220, 38, 38))
    pad = 70
    t1_font = ImageFont.truetype(FONT_B, 72, index=2)
    t2_font = ImageFont.truetype(FONT_B, 52, index=2)
    sub_font = ImageFont.truetype(FONT_BOLD, 32, index=2)
    info_font = ImageFont.truetype(FONT_BOLD, 26, index=2)

    t1 = "丹麦的 Collabora 试点静默收场"
    t2 = "38 个人，6 个月，0 个评估"
    d.text((pad, 140), t1, font=t1_font, fill=(245, 247, 250))
    d.text((pad, 245), t2, font=t2_font, fill=(220, 38, 38))
    sub = "Georgia 字体缺失 ｜ 文件打开全空白 ｜ Ctrl+P 打印整个窗口"
    d.text((pad, 400), sub, font=sub_font, fill=(176, 186, 200))

    bar_y = H - 90
    d.rounded_rectangle([(pad, bar_y), (W - pad, bar_y + 52)], radius=8, fill=(30, 30, 42))
    d.rectangle([(pad, bar_y), (W - pad, bar_y + 2)], fill=(220, 38, 38))
    d.text((pad + 16, bar_y + 16), "FreeLAMP.com  ·  Collabora / ODF / 数字主权  ·  2026-10-27",
           font=info_font, fill=(218, 224, 234))

    for txt, font, y0 in [(t1, t1_font, 140), (t2, t2_font, 245)]:
        print(txt, d.textbbox((pad, y0), txt, font=font))
    im.save(OUT)
    print("saved", OUT)

if __name__ == "__main__":
    main()
