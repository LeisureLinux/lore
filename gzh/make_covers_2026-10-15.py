#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""2026-10-15 七篇公众号封面（1200x675，石墨极简风格）。

规格沿用 lore/gzh/make_covers_2026-10-13.py 的约定：
  画布 1200x675（公众号 16:9），深色渐变底 + 顶部 7px 强调色条，
  主标题（第一行白、第二行强调色）+ 副标题 + 底部圆角信息条。
  微信列表按 2.35:1 居中裁切，所以主标题不贴边（左右各留 56px，上下留白充足）。
字体：NotoSansCJK-Bold.ttc / Black.ttc，index=2 为 SC。
自检：PIL 量文字 bbox 越界 + 相邻文字块间距 + 2.35:1 裁切安全 + 亮度对比。
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
    # AI 贡献政策：用蓝色强调（治理/规则语义），与安全类的红橙区分
    dict(slug="2026-10-15_open-source-ai-contribution-policies-compared", accent=(96, 165, 250),
         l1="四个开源项目",
         l2="四种 AI 贡献政策",
         sub="分歧不在「允不允许」，而在「声明到底有什么用」",
         bar="GCC 15 行门槛 · 内核取消 Assisted-by · Debian 不禁止 · Flathub 必须声明"),
    # KDE：用 KDE 蓝青强调
    dict(slug="2026-10-15_kde-plasma-6-8-x11-retirement", accent=(41, 182, 246),
         l1="KDE 在 30 岁生日当天",
         l2="退役了 X11",
         sub="不是告别，而是一次刻意的对齐；X11 应用仍能跑",
         bar="X11 服务了 42 年 · 提前 11 个月宣布 · 内置 dwell clicker 无障碍"),
    # GNU Boot：用 GNU 红强调
    dict(slug="2026-10-15_gnu-boot-fsf-fiscal-sponsorship", accent=(220, 76, 70),
         l1="GNU Boot 加入 FSF",
         l2="但它替代的不是现代电脑",
         sub="财政赞助解决「谁替你收钱」，不解决「我的笔记本能不能用」",
         bar="仍是 0.1 RC6 · 已测试机型集中在 2006~2009 年 · 可复现构建"),
    # Cloud Hypervisor：用紫强调（虚拟化）
    dict(slug="2026-10-15_cloud-hypervisor-54-live-migration", accent=(167, 139, 250),
         l1="Cloud Hypervisor 54",
         l2="承诺前两个版本可迁移",
         sub="把一句口头保证，变成了一条可依赖的工程约束",
         bar="n-2 兼容窗口 · 协议版本成为内部细节 · 回迁不受支持"),
    # RVA23：用 RISC-V 绿强调
    dict(slug="2026-10-15_riscv-rva23-hwprobe-detection", accent=(74, 222, 128),
         l1="我这台机器符不符合 RVA23",
         l2="终于能一句话问清了",
         sub="实质是把基线的定义权，从多个下游收回到内核",
         bar="39 个强制扩展 → 一个位 · GCC 只查了 24 个 · 仍在 v8 返工"),
    # 红帽：用红帽红强调
    dict(slug="2026-10-15_red-hat-lightwell-backport-netops-as-code", accent=(238, 88, 88),
         l1="95% 的漏洞早有修复",
         l2="但平均等 5 个月才装上",
         sub="瓶颈不在找漏洞，而在「变更本身的成本」",
         bar="回移补丁到固定版本 · AI 管排序、人管批准 · 自动化管执行"),
    # Nothing：用 Nothing 黑白配橙
    dict(slug="2026-10-15_nothing-os-5-android-17-rollout", accent=(255, 92, 92),
         l1="Nothing OS 5 开始推送",
         l2="但大版本和补丁是两条线",
         sub="拿不到 Android 17，不等于停止收安全补丁",
         bar="10 款机型排到 2027 年 1 月 · CMF Phone 1 八月仍在收补丁"),
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
