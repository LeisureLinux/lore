# -*- coding: utf-8 -*-
from PIL import Image, ImageDraw, ImageFont

W, H = 1200, 675
FONT_B = "/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc"
FONT_BOLD = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
OUT = "/home/axu/codex/writings/lore/gzh/2026-10-27_stalwart-1-0-mail-server/cover.png"

def main():
    im = Image.new("RGB", (W, H), (14, 16, 24))
    d = ImageDraw.Draw(im)
    for y in range(H):
        t = y / (H - 1)
        d.line([(0, y), (W, y)], fill=(int(16 + 20*t), int(18 + 20*t), int(30 + 30*t)))
    d.rectangle([(0, 0), (W, 7)], fill=(239, 68, 68))
    pad = 70
    f1 = ImageFont.truetype(FONT_B, 80, index=2)
    f2 = ImageFont.truetype(FONT_B, 50, index=2)
    fs = ImageFont.truetype(FONT_BOLD, 32, index=2)
    fi = ImageFont.truetype(FONT_BOLD, 26, index=2)
    t1 = "Stalwart 1.0"
    t2 = "比 Postfix + Dovecot 更快"
    d.text((pad, 140), t1, font=f1, fill=(246, 247, 250))
    d.text((pad, 245), t2, font=f2, fill=(239, 68, 68))
    d.text((pad, 400), "SIMD/SWAR · 25 万封邮件全文搜索 4ms · 38 项赢 35 项", font=fs, fill=(178, 186, 200))
    bar_y = H - 90
    d.rounded_rectangle([(pad, bar_y), (W - pad, bar_y + 52)], radius=8, fill=(30, 32, 44))
    d.rectangle([(pad, bar_y), (W - pad, bar_y + 2)], fill=(239, 68, 68))
    d.text((pad + 16, bar_y + 16), "FreeLAMP.com  ·  Stalwart / 邮件服务器 / JMAP  ·  2026-10-27",
           font=fi, fill=(216, 222, 234))
    print("t1", d.textbbox((pad,140), t1, font=f1)[2], "| t2", d.textbbox((pad,250), t2, font=f2)[2],
          "| sub", d.textbbox((pad,400), "SIMD/SWAR · 25 万封邮件全文搜索 4ms · 38 项赢 35 项", font=fs)[2])
    im.save(OUT)
    print("saved", OUT)

if __name__ == "__main__":
    main()
