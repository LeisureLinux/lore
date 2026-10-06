#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
from PIL import Image, ImageDraw, ImageFont
BASE=os.path.dirname(os.path.abspath(__file__)); OUT=os.path.join(BASE,"cover.png")
FB="/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc"; FR="/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
def F(sz,k="black"): return ImageFont.truetype(FB if k=="black" else FR,sz,index=2)
BG=(10,13,18); FG=(240,244,250); MUTED=(138,148,162); DIM=(86,94,108)
RED=(232,96,96); GREEN=(74,210,150); ORANGE=(245,158,11); BLUE=(56,189,248)
W,H=1200,675
im=Image.new("RGB",(W,H),BG); d=ImageDraw.Draw(im)
for y in range(H):
    t=y/H; d.line([(0,y),(W,y)],fill=(int(10+16*t),int(13+18*t),int(18+26*t)))
for x in range(W):
    t=x/W
    d.line([(x,0),(x,7)],fill=(int(RED[0]+(GREEN[0]-RED[0])*t),int(RED[1]+(GREEN[1]-RED[1])*t),int(RED[2]+(GREEN[2]-RED[2])*t)))
d.text((52,52),"一个布尔值",font=F(46),fill=RED)
d.text((52,116),"把内网服务变成了公网服务",font=F(40),fill=FG)
d.text((54,196),"0.0.0.0 和 * 不是「内网」，是「所有接口」",font=F(23,"bold"),fill=MUTED)
by=262
d.rounded_rectangle([52,by,540,by+150],12,fill=(26,20,20),outline=(120,60,60),width=2)
d.text((72,by+16),"listenLAN: true",font=F(24,"bold"),fill=RED)
d.text((72,by+58),"绑 *:8888",font=F(26),fill=FG)
d.text((72,by+104),"→ 公网 IPv6 可达",font=F(22,"bold"),fill=RED)
d.rounded_rectangle([608,by,1148,by+150],12,fill=(18,28,24),outline=(60,160,120),width=2)
d.text((628,by+16),"socat 桥",font=F(24,"bold"),fill=GREEN)
d.text((628,by+58),"bind=LAN_IP",font=F(26),fill=FG)
d.text((628,by+104),"→ 内网可用 / 公网不可见",font=F(22,"bold"),fill=GREEN)
d.text((570,by+60),"→",font=F(34),fill=BLUE)
bx,byy=52,H-100
d.rounded_rectangle([bx,byy,W-bx,byy+54],12,fill=(22,28,36),outline=ORANGE,width=2)
d.text((bx+18,byy+14),"服务退回 127.0.0.1，再用 socat 在指定内网地址补一个口",font=F(19,"bold"),fill=FG)
d.text((52,H-34),"LeisureLinux 聊网络与安全",font=F(16,"bold"),fill=DIM)
im.save(OUT,quality=95); print("OK",OUT,im.size)
