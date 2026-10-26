# -*- coding: utf-8 -*-
from PIL import Image, ImageDraw, ImageFont

W, H = 1200, 675
FONT_B = "/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc"
FONT_BOLD = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
OUT = "/home/axu/codex/writings/lore/gzh/2026-10-27_freedns-25-years-shared-domain-registry/cover.png"

def main():
    im = Image.new("RGB", (W, H), (12, 16, 24))
    d = ImageDraw.Draw(im)
    for y in range(H):
        t = y / (H - 1)
        d.line([(0, y), (W, y)], fill=(int(12 + 18 * t), int(20 + 20 * t), int(38 + 30 * t)))
    d.rectangle([(0, 0), (W, 7)], fill=(56, 189, 248))
    pad = 70
    t1_font = ImageFont.truetype(FONT_B, 80, index=2)
    t2_font = ImageFont.truetype(FONT_B, 54, index=2)
    sub_font = ImageFont.truetype(FONT_BOLD, 34, index=2)
    info_font = ImageFont.truetype(FONT_BOLD, 26, index=2)

    t1 = "FreeDNS 二十五年"
    t2 = "716 万人，靠 5606 个付费账户撑着"
    d.text((pad, 140), t1, font=t1_font, fill=(245, 247, 250))
    d.text((pad, 245), t2, font=t2_font, fill=(56, 189, 248))
    sub = "不投广告的 DNS ｜ 共享域名池 ｜ 每月 70 亿次查询"
    d.text((pad, 400), sub, font=sub_font, fill=(176, 186, 200))

    bar_y = H - 90
    d.rounded_rectangle([(pad, bar_y), (W - pad, bar_y + 52)], radius=8, fill=(26, 32, 48))
    d.rectangle([(pad, bar_y), (W - pad, bar_y + 2)], fill=(56, 189, 248))
    d.text((pad + 16, bar_y + 16), "FreeLAMP.com  ·  FreeDNS / DDNS / 基础设施  ·  2026-10-27",
           font=info_font, fill=(218, 224, 234))

    for txt, font, y0 in [(t1, t1_font, 140), (t2, t2_font, 245)]:
        print(txt, d.textbbox((pad, y0), txt, font=font))
    im.save(OUT)
    print("saved", OUT)

if __name__ == "__main__":
    main()
