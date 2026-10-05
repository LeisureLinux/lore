#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""封面 1200x675，石墨极简。"""
import os
from PIL import Image, ImageDraw, ImageFont
BASE=os.path.dirname(os.path.abspath(__file__)); OUT=os.path.join(BASE,"cover.png")
FB="/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc"; FR="/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
def F(sz,k="black"): return ImageFont.truetype(FB if k=="black" else FR,sz,index=2)
BG=(10,13,18); FG=(240,244,250); MUTED=(138,148,162); DIM=(86,94,108)
ORANGE=(245,158,11); BLUE=(56,189,248); GREEN=(74,210,150); RED=(232,96,96)
W,H=1200,675
im=Image.new("RGB",(W,H),BG); d=ImageDraw.Draw(im)
for y in range(H):
    t=y/H; d.line([(0,y),(W,y)],fill=(int(10+16*t),int(13+18*t),int(18+26*t)))
for x in range(W):
    t=x/W
    d.line([(x,0),(x,7)],fill=(int(ORANGE[0]+(BLUE[0]-ORANGE[0])*t),int(ORANGE[1]+(BLUE[1]-ORANGE[1])*t),int(ORANGE[2]+(BLUE[2]-ORANGE[2])*t)))
d.text((52,54),"万物皆隧道 · 续",font=F(38),fill=ORANGE)
d.text((52,108),"每个访问端一张",font=F(56),fill=FG)
d.text((52,178),"3 分钟证书",font=F(56),fill=BLUE)
d.text((54,264),"公网 IPv4 是 CGNAT，端口映射根本不可能",font=F(24,"bold"),fill=MUTED)
by=330
d.rounded_rectangle([52,by,552,by+120],12,fill=(26,20,22),outline=(120,60,60),width=2)
d.text((72,by+14),"发现",font=F(20,"bold"),fill=RED)
d.text((72,by+48),"光猫 WAN 在 100.64/10",font=F(21,"bold"),fill=MUTED)
d.text((72,by+82),"DDNS / 端口映射全部无效",font=F(21,"bold"),fill=MUTED)
d.rounded_rectangle([608,by,1108,by+120],12,fill=(18,28,26),outline=(60,160,120),width=2)
d.text((628,by+14),"改用",font=F(20,"bold"),fill=GREEN)
d.text((628,by+48),"CF 隧道 + 短时证书",font=F(21,"bold"),fill=MUTED)
d.text((628,by+82),"零入站端口 · 自动轮换",font=F(21,"bold"),fill=MUTED)
d.text((566,by+42),"→",font=F(34),fill=BLUE)
bx,byy=52,H-104
d.rounded_rectangle([bx,byy,W-bx,byy+56],12,fill=(22,28,36),outline=ORANGE,width=2)
d.text((bx+18,byy+15),"CF 隧道 · IPv6 直通 · LAN，三条路并存",font=F(19,"bold"),fill=FG)
d.text((52,H-36),"LeisureLinux 聊网络与安全",font=F(16,"bold"),fill=DIM)
im.save(OUT,quality=95); print("OK",OUT,im.size)
