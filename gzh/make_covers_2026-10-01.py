#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""批量生成 2026-10-01 七篇公众号封面图（1200x675，石墨极简风格）。"""
import os
from PIL import Image, ImageDraw, ImageFont

BASE = os.path.dirname(os.path.abspath(__file__))
FB = "/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc"
FR = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"

def F(sz, kind="black"):
    if kind == "bold":
        return ImageFont.truetype(FR, sz, index=2)
    return ImageFont.truetype(FB, sz, index=2)

BG = (10, 13, 18)
FG = (240, 244, 250)
MUTED = (130, 140, 152)
LINE = (60, 68, 78)
W, H = 1200, 675

# 每篇：目录、主题色、主标题行、副标题、底部标签行
CFG = [
    dict(slug="2026-10-01_plex-remote-streaming-paywall", accent=(232, 90, 79),
         title=["Plex 关掉了最后一个", "免费漏洞"],
         sub="远程串流自己的电影，现在必须付费",
         bar="本地播放仍免费 · Plex Pass / Remote Watch Pass · Tailscale 绕过 · Jellyfin"),
    dict(slug="2026-10-01_firebase-ios-crash-incident", accent=(234, 67, 53),
         title=["一个畸形配置包", "放倒成千上万 iOS 应用"],
         sub="Firebase 事故复盘：启动即崩，开发者只能等",
         bar="nil 字典键 · 2 小时 11 分修复 · 缓存再崩 4 小时 · 状态页全程沉默"),
    dict(slug="2026-10-01_bloomberg-terminal-history", accent=(251, 188, 5),
         title=["它曾是金融权力的象征", "彭博终端简史"],
         sub="从送信信鸽到交易员桌上的专用键盘",
         bar="1841 商人交易所 · 1867 电报纸带机 · 1981 Market Master · 史密森尼藏品"),
    dict(slug="2026-10-01_esp32-wifi-commissioning-testing", accent=(52, 168, 83),
         title=["ESP32 的五种配网方式", "以及怎么全部自动测试"],
         sub="BLE / Soft AP / Captive Portal / SmartConfig / WPS",
         bar="硬件在环 · CI 回归 · NVS 凭据持久化 · 重启不该重新配网"),
    dict(slug="2026-10-01_gitea-28-0-0-released", accent=(52, 168, 83),
         title=["Gitea 28.0.0 发布", "出网访问默认收紧"],
         sub="版本号去掉 1. 前缀，一批安全默认值变严",
         bar="内部代理 · EGRESS_MODE · Actions 400 天过期 · 自注册默认关闭 · ROOT_URL"),
    dict(slug="2026-10-01_qt-6-12-lts-released", accent=(65, 205, 82),
         title=["Qt 6.12 LTS 发布", "QML 热重载进内核"],
         sub="改代码不重启，不用再从第五个界面点回来",
         bar="StyleKit 进 Qt Labs · Canvas Painter 转正 · HarmonyOS 支持级别存疑"),
    dict(slug="2026-10-01_tplink-wifi-8-router-us-ban", accent=(66, 133, 244),
         title=["首款 Wi-Fi 8 路由全球预售", "美国却不在名单上"],
         sub="TP-Link Archer 8 Ultra：技术不是门槛，批准才是",
         bar="博通芯片 · 吞吐 +33% · 802.11bn 尚未定稿 · FCC 有条件批准"),
    dict(slug="2026-10-01_goodix-501d-linux-fingerprint-postmortem", accent=(139, 92, 246),
         title=["协议全通，算法卡死", "Goodix 指纹适配复盘"],
         sub="从 PSK 提取到私有引擎逆向，一次完整的失败",
         bar="501d/GM168SEC · TLS-PSK · DPAPI 密封 · usbmon 抓包 · Wine 缺 WBDI · 13mm² 面积上限"),
]

for c in CFG:
    out = os.path.join(BASE, c["slug"], "cover.png")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    acc = c["accent"]
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    # 渐变底
    for y in range(H):
        t = y / H
        d.line([(0, y), (W, y)],
               fill=(int(10 + 16 * t), int(13 + 18 * t), int(18 + 26 * t)))
    # 顶部主题色条
    d.rectangle([0, 0, W, 7], fill=acc)

    y = 70
    for i, line in enumerate(c["title"]):
        d.text((56, y), line, font=F(64 if i == 0 else 64),
               fill=FG if i == 0 else acc)
        y += 92
    d.text((58, y + 10), c["sub"], font=F(28, "bold"), fill=MUTED)

    # 底部信息条
    bx, by = 56, H - 132
    d.rounded_rectangle([bx, by, W - bx, by + 74], 12,
                        fill=(22, 28, 36), outline=acc, width=2)
    d.text((bx + 20, by + 24), c["bar"], font=F(24, "bold"), fill=FG)

    im.save(out, quality=95)
    print(f"OK {out} {im.size}")
