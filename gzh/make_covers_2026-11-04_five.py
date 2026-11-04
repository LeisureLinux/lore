# -*- coding: utf-8 -*-
from PIL import Image, ImageDraw, ImageFont
W, H = 1200, 675
FONT_B = "/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc"
FONT_BOLD = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
BASE = "/home/axu/codex/writings/lore/gzh"
CFG = [
 dict(dir="2026-11-04_kitty-0-50-0-docked-windows", accent=(126, 196, 200), bg=(10, 14, 16),
      t1="终端的 13 条安全公告", t1sz=52, t2="半年 12 个版本", t2sz=56,
      sub="kitty 0.50.0 解读  ｜  停靠窗口 · WASM · SIMD · 扩展协议",
      info="FreeLAMP.com  ·  技术解读 / 终端安全  ·  2026-11-04"),
 dict(dir="2026-11-04_postman-desktop-auto-installs-agent-plugins", accent=(226, 132, 116), bg=(17, 12, 12),
      t1="「打开 Postman 之后", t1sz=52, t2="你的 Codex 变了」", t2sz=52,
      sub="一次产品同意边界的越界  ｜  自批钩子 · MCP · 9 种 agent",
      info="FreeLAMP.com  ·  技术解读 / 软件治理  ·  2026-11-04"),
 dict(dir="2026-11-04_gitbook-ai-agent-attack-token-rotation", accent=(140, 178, 224), bg=(11, 14, 19),
      t1="「用 AI agent 发动的", t1sz=50, t2="定向攻击」", t2sz=58,
      sub="GitBook 事件解读  ｜  全量凭据轮换 · 取证排查 · 事故通报",
      info="FreeLAMP.com  ·  技术解读 / 事件响应  ·  2026-11-04"),
 dict(dir="2026-11-04_erici-riscv-industrial-computer-reference-stack", accent=(154, 200, 140), bg=(10, 15, 11),
      t1="硅片到了", t1sz=58, t2="工业计算机还没到", t2sz=54,
      sub="ERICI 解读  ｜  RVA23 · 分区 hypervisor · QNX 风格双内核",
      info="FreeLAMP.com  ·  技术解读 / RISC-V  ·  2026-11-04"),
 dict(dir="2026-11-04_cve-2026-119977-wordpress-upgrade-window-toctou", accent=(232, 168, 100), bg=(16, 13, 10),
      t1="升级窗口里的", t1sz=54, t2="那 16 个字符", t2sz=56,
      sub="CVE-2026-119977 解读  ｜  TOCTOU · KEV · 可预测目录名",
      info="FreeLAMP.com  ·  技术解读 / Web 安全  ·  2026-11-04"),
]
def build(c):
    im = Image.new("RGB", (W, H), c["bg"]); d = ImageDraw.Draw(im)
    for y in range(H):
        t = y/(H-1)
        d.line([(0,y),(W,y)], fill=(int(c["bg"][0]+16*t), int(c["bg"][1]+20*t), int(c["bg"][2]+16*t)))
    d.rectangle([(0,0),(W,7)], fill=c["accent"])
    pad = 70
    f1 = ImageFont.truetype(FONT_B, c["t1sz"], index=2); f2 = ImageFont.truetype(FONT_B, c["t2sz"], index=2)
    fs = ImageFont.truetype(FONT_BOLD, 26, index=2); fi = ImageFont.truetype(FONT_BOLD, 26, index=2)
    d.text((pad,140), c["t1"], font=f1, fill=(246,247,250))
    d.text((pad,245), c["t2"], font=f2, fill=c["accent"])
    d.text((pad,400), c["sub"], font=fs, fill=(178,186,200))
    bar_y = H-90
    d.rounded_rectangle([(pad,bar_y),(W-pad,bar_y+52)], radius=8, fill=(28,32,44))
    d.rectangle([(pad,bar_y),(W-pad,bar_y+2)], fill=c["accent"])
    d.text((pad+16, bar_y+16), c["info"], font=fi, fill=(216,222,234))
    warn=[]
    for n,b in (("t1",d.textbbox((pad,140),c["t1"],font=f1)),("t2",d.textbbox((pad,245),c["t2"],font=f2)),
                ("sub",d.textbbox((pad,400),c["sub"],font=fs)),("info",d.textbbox((pad+16,bar_y+16),c["info"],font=fi))):
        if b[2] > W-40: warn.append(f"{n}={b[2]}")
    im.save(f"{BASE}/{c['dir']}/cover.png")
    print(f"✅ {c['dir']}" + (f"  ⚠️ {','.join(warn)}" if warn else "  (无越界)"))
for c in CFG: build(c)
