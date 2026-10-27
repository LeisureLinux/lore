# -*- coding: utf-8 -*-
from PIL import Image, ImageDraw, ImageFont

W, H = 1200, 675
FONT_B = "/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc"
FONT_BOLD = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
OUT = "/home/axu/codex/writings/lore/gzh/2026-10-27_github-stars-token-savers-eval/cover.png"

def main():
    im = Image.new("RGB", (W, H), (13, 13, 17))
    d = ImageDraw.Draw(im)
    for y in range(H):
        t = y / (H - 1)
        d.line([(0, y), (W, y)], fill=(int(14 + 16*t), int(14 + 16*t), int(20 + 24*t)))
    d.rectangle([(0, 0), (W, 7)], fill=(250, 204, 21))
    pad = 70
    f1 = ImageFont.truetype(FONT_B, 66, index=2)
    f2 = ImageFont.truetype(FONT_B, 48, index=2)
    fs = ImageFont.truetype(FONT_BOLD, 32, index=2)
    fi = ImageFont.truetype(FONT_BOLD, 26, index=2)
    t1 = "8.4 万星，宣称省 60–90%"
    t2 = "三个团队测出：省 token ≠ 省钱"
    d.text((pad, 140), t1, font=f1, fill=(246, 247, 250))
    d.text((pad, 245), t2, font=f2, fill=(250, 204, 21))
    sub = "r = 0.15 ｜ rtk 实测 +7.6%，唯一为真的 ponytail 只省 10.3%"
    d.text((pad, 400), sub, font=fs, fill=(178, 186, 200))
    bar_y = H - 90
    d.rounded_rectangle([(pad, bar_y), (W - pad, bar_y + 52)], radius=8, fill=(30, 30, 40))
    d.rectangle([(pad, bar_y), (W - pad, bar_y + 2)], fill=(250, 204, 21))
    d.text((pad + 16, bar_y + 16), "FreeLAMP.com  ·  AI agent 工具评测 / Token 成本  ·  2026-10-27",
           font=fi, fill=(216, 222, 234))
    print("t1", d.textbbox((pad,140), t1, font=f1)[2], "| t2", d.textbbox((pad,250), t2, font=f2)[2],
          "| sub", d.textbbox((pad,400), sub, font=fs)[2])
    im.save(OUT)
    print("saved", OUT)

if __name__ == "__main__":
    main()
