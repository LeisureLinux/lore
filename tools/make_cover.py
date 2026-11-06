# -*- coding: utf-8 -*-
"""公众号封面生成器（1200×675）——统一工具，支持背景主题色轮换。

用法：
    python3 tools/make_cover.py <slug> --t1 "主标题第一行" --t2 "主标题第二行" \
        --sub "副标题" --info "底部信息条"

背景主题色按 slug 的哈希**稳定轮换**（同一 slug 每次生成同色，便于重跑），
色板刻意做成深色但**带明显色相**，避免所有封面都是近黑。

新增文章直接调用本工具即可，不必再写一次性脚本。
历史封面可用 --theme <name> 显式指定。
"""
import argparse
import hashlib
import os

from PIL import Image, ImageDraw, ImageFont

W, H = 1200, 675
FONT_B = "/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc"
FONT_BOLD = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
BASE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "gzh")

# ---- 背景主题色板 ---------------------------------------------------------
# (bg_top, bg_bottom, accent, sub_color, card_bg)
# 深色但有明确色相，避免整站封面都是黑。
THEMES = {
    "indigo":   ((16, 17, 38), (28, 24, 62), (129, 140, 248), (170, 178, 225), (30, 30, 54)),
    "crimson":  ((34, 14, 20), (58, 20, 30), (248, 113, 133), (214, 160, 172), (48, 22, 30)),
    "teal":     ((10, 30, 32), (14, 52, 54), (45, 212, 191), (154, 206, 201), (16, 44, 46)),
    "amber":    ((36, 24, 10), (62, 40, 14), (251, 191, 36), (216, 190, 140), (50, 34, 14)),
    "violet":   ((26, 14, 40), (44, 22, 66), (196, 181, 253), (188, 172, 216), (36, 22, 52)),
    "forest":   ((10, 26, 16), (16, 46, 26), (74, 222, 128), (156, 202, 170), (14, 40, 22)),
    "azure":    ((10, 22, 38), (16, 40, 66), (56, 189, 248), (160, 190, 215), (14, 36, 58)),
    "rose":     ((36, 14, 26), (60, 22, 42), (244, 114, 182), (216, 164, 190), (48, 20, 32)),
    "lime":     ((22, 30, 10), (38, 52, 16), (163, 230, 53), (186, 204, 154), (30, 42, 14)),
    "slate":    ((18, 20, 26), (30, 34, 44), (148, 163, 184), (176, 186, 204), (28, 32, 42)),
    "copper":   ((32, 20, 12), (56, 34, 18), (251, 146, 60), (212, 176, 142), (46, 28, 16)),
    "ocean":    ((8, 26, 34), (12, 48, 58), (34, 211, 238), (152, 196, 208), (12, 42, 52)),
}

THEME_NAMES = list(THEMES.keys())


def pick_theme(slug):
    """按 slug 稳定选色（同一 slug 永远同色，重跑可复现）。"""
    h = hashlib.sha256(slug.encode("utf-8")).hexdigest()
    return THEME_NAMES[int(h[:8], 16) % len(THEME_NAMES)]


def build(slug, t1, t2, sub, info, theme=None, t1sz=52, t2sz=54):
    name = theme or pick_theme(slug)
    bg0, bg1, accent, sub_c, card = THEMES[name]

    im = Image.new("RGB", (W, H), bg0)
    d = ImageDraw.Draw(im)
    for y in range(H):
        t = y / (H - 1)
        d.line([(0, y), (W, y)],
               fill=(int(bg0[0] + (bg1[0] - bg0[0]) * t),
                     int(bg0[1] + (bg1[1] - bg0[1]) * t),
                     int(bg0[2] + (bg1[2] - bg0[2]) * t)))

    # 顶部强调条
    d.rectangle([(0, 0), (W, 7)], fill=accent)
    # 右下角大面积色块，给封面一点层次（避免整块纯色）
    d.ellipse([W - 300, H - 300, W + 140, H + 140], fill=card)

    pad = 70
    f1 = ImageFont.truetype(FONT_B, t1sz, index=2)
    f2 = ImageFont.truetype(FONT_B, t2sz, index=2)
    fs = ImageFont.truetype(FONT_BOLD, 25, index=2)
    fi = ImageFont.truetype(FONT_BOLD, 25, index=2)

    d.text((pad, 140), t1, font=f1, fill=(246, 247, 250))
    d.text((pad, 240), t2, font=f2, fill=accent)
    d.text((pad, 400), sub, font=fs, fill=sub_c)

    bar_y = H - 90
    d.rounded_rectangle([(pad, bar_y), (W - pad, bar_y + 52)], radius=8, fill=card)
    d.rectangle([(pad, bar_y), (W - pad, bar_y + 2)], fill=accent)
    d.text((pad + 16, bar_y + 16), info, font=fi, fill=(222, 228, 238))

    out_dir = os.path.join(BASE, slug)
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, "cover.png")
    im.save(out)

    print(f"theme={name}  {out}")
    for label, b in (("t1", d.textbbox((pad, 140), t1, font=f1)),
                     ("t2", d.textbbox((pad, 240), t2, font=f2)),
                     ("sub", d.textbbox((pad, 400), sub, font=fs)),
                     ("info", d.textbbox((pad + 16, bar_y + 16), info, font=fi))):
        flag = "  ⚠️ 越界" if b[2] > W - 40 else ""
        print(f"  {label}={b[2]}{flag}")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("slug")
    ap.add_argument("--t1", required=True)
    ap.add_argument("--t2", required=True)
    ap.add_argument("--sub", required=True)
    ap.add_argument("--info", required=True)
    ap.add_argument("--theme", choices=THEME_NAMES, help="显式指定主题色")
    ap.add_argument("--t1sz", type=int, default=52)
    ap.add_argument("--t2sz", type=int, default=54)
    a = ap.parse_args()
    build(a.slug, a.t1, a.t2, a.sub, a.info, theme=a.theme,
          t1sz=a.t1sz, t2sz=a.t2sz)


if __name__ == "__main__":
    main()
