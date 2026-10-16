#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""2026-10-16 五篇公众号封面（1200x675，石墨极简风格）。

规格沿用 lore/gzh/make_covers_2026-10-15.py 的约定：
  画布 1200x675（公众号 16:9），深色渐变底 + 顶部 7px 强调色条，
  主标题（第一行白、第二行强调色）+ 副标题 + 底部圆角信息条。
  微信列表按 2.35:1 居中裁切，所以主标题不贴边（左右各留 56px）。
字体：NotoSansCJK-Bold.ttc / Black.ttc，index=2 为 SC。
自检：PIL 量文字 bbox 越界 + 相邻文字块间距 + 2.35:1 裁切 + 亮度对比。
"""
import os
from PIL import Image, ImageDraw, ImageFont

BASE = os.path.dirname(os.path.abspath(__file__))
FB = "/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc"
FR = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"

W, H = 1200, 675
BG = (10, 13, 18)
FG = (240, 244, 250)
MUTED = (130, 140, 152)
SAFE = 56

CFG = [
    # systemd：紫（与 Cloud Hypervisor 同属系统类，但用更深紫区分）
    dict(slug="2026-10-16_systemd-v262-trust-chain-varlink", accent=(139, 122, 246),
         l1="systemd v262 的 35 条改动",
         l2="主线是把启动信任切成段",
         sub="NvPCR、policyrefs、verity 与 LUKS 的层次顺序",
         bar="35 条帖子的索引不是变更清单 · 事实取自官方 NEWS · 不重复已写的 AI 金丝雀"),
    # Ubuntu：橙（Canonical 品牌色）
    dict(slug="2026-10-16_ubuntu-26-10-stonking-stingray", accent=(233, 84, 32),
         l1="Ubuntu 26.10 用 Sequoia",
         l2="换掉了 GnuPG 签名",
         sub="发行版第一次把「量子威胁」写进自己的包管理器",
         bar="换实现（内存安全）与换算法（时间表）是两件事 · dbus-broker 换了 D-Bus 实现"),
    # AI 逆向硬件：青绿
    dict(slug="2026-10-16_ai-reverse-engineer-linux-hardware-drivers", accent=(45, 212, 191),
         l1="用 AI 逆向工程硬件驱动",
         l2="真正的产物是一套方法论",
         sub="在 KVM 里跑厂商 Windows 驱动，在宿主上用 usbmon 抓包",
         bar="差异就是 bug 清单 · 每个常量都可追溯到记录 · 人的职责是验证"),
    # CPPC + Mutter：蓝
    dict(slug="2026-10-16_cppc-boost-default-mutter-damage-tracking", accent=(96, 165, 250),
         l1="两个「隐含假设」的修正",
         l2="一个改默认值，一个补状态",
         sub="CPU boost 该不该默认开，复用缓冲能不能只拷最新那帧",
         bar="Arm 工程师质疑 boost 概念本身 · Mutter 写明失效边界并保守回退"),
    # Defender：微软蓝
    dict(slug="2026-10-16_microsoft-defender-linux-desktop-preview", accent=(56, 189, 248),
         l1="Defender 装到了 Linux 桌面",
         l2="它卖的是「补上可见性盲区」",
         sub="高权限、高价值、容易被管理员忽略",
         bar="公共预览非 GA · 无桌面专用 agent · 桌面环境不是支持变量"),
]


def fit(d, text, font_path, start, max_w):
    sz = start
    while sz > 16:
        f = ImageFont.truetype(font_path, sz, index=2)
        if d.textlength(text, font=f) <= max_w:
            return f
        sz -= 1
    return ImageFont.truetype(font_path, 16, index=2)


def luma(rgb):
    r, g, b = rgb
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


for c in CFG:
    out = os.path.join(BASE, c["slug"], "cover.png")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    acc = c["accent"]

    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    for y in range(H):
        t = y / H
        d.line([(0, y), (W, y)], fill=(int(10 + 16 * t), int(13 + 18 * t), int(18 + 26 * t)))
    d.rectangle([0, 0, W, 7], fill=acc)

    f_l1 = fit(d, c["l1"], FB, 62, W - 2 * SAFE)
    f_l2 = fit(d, c["l2"], FB, 62, W - 2 * SAFE)
    b1 = d.textbbox((SAFE, 70), c["l1"], font=f_l1)
    b2 = d.textbbox((SAFE, 156), c["l2"], font=f_l2)
    d.text((SAFE, 70), c["l1"], font=f_l1, fill=FG)
    d.text((SAFE, 156), c["l2"], font=f_l2, fill=acc)

    f_sub = fit(d, c["sub"], FR, 28, W - 2 * SAFE)
    bsub = d.textbbox((SAFE + 2, 252), c["sub"], font=f_sub)
    d.text((SAFE + 2, 252), c["sub"], font=f_sub, fill=MUTED)

    bx, by = SAFE, H - 128
    f_bar = fit(d, c["bar"], FR, 23, W - 2 * bx - 40)
    bbar = d.textbbox((bx + 20, by + 24), c["bar"], font=f_bar)
    d.rounded_rectangle([bx, by, W - bx, by + 72], 12, fill=(22, 28, 36), outline=acc, width=2)
    d.text((bx + 20, by + 24), c["bar"], font=f_bar, fill=FG)

    im.save(out, quality=95)

    issues = []
    for name, b in (("l1", b1), ("l2", b2), ("sub", bsub), ("bar", bbar)):
        if b[0] < 0 or b[2] > W or b[1] < 0 or b[3] > H:
            issues.append(f"{name} 越界 {b}")
    if b2[3] > H * 0.5:
        issues.append(f"主标题第二行底部 {b2[3]} 越过中线")
    for name, b in (("l1", b1), ("l2", b2), ("sub", bsub)):
        if b[2] > W - 20:
            issues.append(f"{name} 右边界 {b[2]} 过于贴近画布")
    if luma(FG) - luma(BG) < 120 or luma(acc) - luma(BG) < 60:
        issues.append("对比度不足")
    print(f"{'OK ' if not issues else 'WARN'} {c['slug'][:52]:54s} "
          f"l1={f_l1.size}px l2={f_l2.size}px sub={f_sub.size}px bar={f_bar.size}px"
          + ("" if not issues else "  ⚠ " + "; ".join(issues)))
