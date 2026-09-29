#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成《ChromeOS 2034 退场》公众号封面图。1200x675。"""
import os
from PIL import Image, ImageDraw, ImageFont

OUT = "/home/axu/codex/writings/lore/gzh/2026-09-29_chromeos-phase-out-2034-googlebook/cover.png"
W, H = 1200, 675
FB = "/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc"
FR = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
def F(sz, kind="black"):
    if kind == "mono": return ImageFont.truetype(FR, sz, index=7)
    if kind == "bold": return ImageFont.truetype(FR, sz, index=2)
    return ImageFont.truetype(FB, sz, index=2)

BG=(10,13,18); FG=(240,244,250); MUTED=(130,140,152)
BLUE=(66,133,244); GREEN=(52,168,83); YELLOW=(251,188,5); RED=(234,67,53)

im=Image.new("RGB",(W,H),BG); d=ImageDraw.Draw(im)
for y in range(H):
    t=y/H; d.line([(0,y),(W,y)],fill=(int(10+16*t),int(13+18*t),int(18+26*t)))
# 顶部四色 Google 条
seg=W//4
for i,c in enumerate([BLUE,RED,YELLOW,GREEN]):
    d.rectangle([i*seg,0,(i+1)*seg,7],fill=c)

# 主标题
d.text((56,52),"ChromeOS",font=F(76),fill=FG)
d.text((56,144),"2034 年退场",font=F(76),fill=RED)
d.text((58,248),"较新 Chromebook 可迁移到 Googlebook OS",font=F(29,"bold"),fill=MUTED)

# 中部：时间轴
ty=350
d.line([90,ty,W-90,ty],fill=(60,68,78),width=4)
pts=[(140,"2026-10-04","Googlebook\n上市",GREEN),(470,"2027 H2","管理体验\n铺开",YELLOW),(900,"2034 中","ChromeOS\n停止支持",RED)]
for x,date,label,col in pts:
    d.ellipse([x-11,ty-11,x+11,ty+11],fill=col)
    d.text((x-56,ty-76),date,font=F(26,"bold"),fill=col)
    for i,ln in enumerate(label.split("\n")):
        d.text((x-58,ty+26+i*32),ln,font=F(26,"bold"),fill=FG)

# 底部：10 年承诺的重新定义
bx,by=60,560
d.rounded_rectangle([bx,by,W-bx,by+72],12,fill=(22,28,36),outline=BLUE,width=2)
d.text((bx+20,by+10),"「10 年支持」：",font=F(27,"bold"),fill=BLUE)
d.text((bx+206,by+8),"字面不变，实质变为 ChromeOS + Googlebook OS 接力",font=F(27,"bold"),fill=FG)

im.save(OUT,quality=95); print("OK",OUT,im.size)
