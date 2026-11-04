# -*- coding: utf-8 -*-
from PIL import Image, ImageDraw, ImageFont
W, H = 1200, 675
FONT_B = "/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc"
FONT_BOLD = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
BASE = "/home/axu/codex/writings/lore/gzh"
CFG = [
 dict(dir="2026-11-04_rtx-spark-linux-npcf-power-management-gap", accent=(126, 196, 200), bg=(10, 14, 16),
      t1="插上电源，GPU 掉到", t1sz=52, t2="780 MHz", t2sz=60,
      sub="RTX Spark 笔记本上的 Linux 解读  ｜  NPC · 加密功耗表 · 缺失的密钥",
      info="FreeLAMP.com  ·  技术解读 / 硬件与驱动  ·  2026-11-04"),
 dict(dir="2026-11-04_php2shell-ai-wakeup-call-formal-verification", accent=(216, 156, 120), bg=(16, 13, 11),
      t1="「40 年技术债", t1sz=54, t2="要还了」", t2sz=58,
      sub="PHP2Shell 与 AI 安全  ｜  攻防不对称 · 形式化验证 · 算力分配",
      info="FreeLAMP.com  ·  技术解读 / AI 安全  ·  2026-11-04"),
 dict(dir="2026-11-04_rtx-50-gpu-price-spike-memory-shortage", accent=(232, 140, 96), bg=(16, 12, 11),
      t1="一张显卡涨 370%", t1sz=54, t2="涨的其实是 DRAM", t2sz=52,
      sub="RTX 50 涨价解读  ｜  $9,400 · 内存短缺 · 溢价流向谁",
      info="FreeLAMP.com  ·  技术解读 / 硬件与市场  ·  2026-11-04"),
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
