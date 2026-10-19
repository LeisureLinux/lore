#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
from PIL import Image, ImageDraw, ImageFont
BASE=os.path.dirname(os.path.abspath(__file__))
FB="/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc"; FR="/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
W,H=1200,675; BG=(10,13,18); FG=(240,244,250); MUTED=(130,140,152); SAFE=56
c=dict(slug="2026-10-19_acpi-table-override-guide-initrd-cpio", accent=(250,204,21),
  l1="ACPI 覆盖到底怎么做", l2="不要重编译整张表",
  sub="dump · 改一处 · 打 cpio 进 initrd · 重启",
  bar="kernel/firmware/acpi/ · 争取等长替换 · 不要刷固件")
def fit(d,t,fp,start,mw):
    sz=start
    while sz>16:
        f=ImageFont.truetype(fp,sz,index=2)
        if d.textlength(t,font=f)<=mw: return f
        sz-=1
    return ImageFont.truetype(fp,16,index=2)
def luma(rgb):
    r,g,b=rgb; return 0.2126*r+0.7152*g+0.0722*b
out=os.path.join(BASE,c["slug"],"cover.png"); os.makedirs(os.path.dirname(out),exist_ok=True)
acc=c["accent"]; im=Image.new("RGB",(W,H),BG); d=ImageDraw.Draw(im)
for y in range(H):
    t=y/H
    d.line([(0,y),(W,y)],fill=(int(10+16*t),int(13+18*t),int(18+26*t)))
d.rectangle([0,0,W,7],fill=acc)
f1=fit(d,c["l1"],FB,62,W-2*SAFE); f2=fit(d,c["l2"],FB,62,W-2*SAFE)
b1=d.textbbox((SAFE,70),c["l1"],font=f1); b2=d.textbbox((SAFE,156),c["l2"],font=f2)
d.text((SAFE,70),c["l1"],font=f1,fill=FG); d.text((SAFE,156),c["l2"],font=f2,fill=acc)
fs=fit(d,c["sub"],FR,28,W-2*SAFE); bs=d.textbbox((SAFE+2,252),c["sub"],font=fs)
d.text((SAFE+2,252),c["sub"],font=fs,fill=MUTED)
bx,by=SAFE,H-128
fb=fit(d,c["bar"],FR,23,W-2*bx-40); bb=d.textbbox((bx+20,by+24),c["bar"],font=fb)
d.rounded_rectangle([bx,by,W-bx,by+72],12,fill=(22,28,36),outline=acc,width=2)
d.text((bx+20,by+24),c["bar"],font=fb,fill=FG)
im.save(out,quality=95)
iss=[]
for n,b in (("l1",b1),("l2",b2),("sub",bs),("bar",bb)):
    if b[0]<0 or b[2]>W or b[1]<0 or b[3]>H: iss.append(f"{n} 越界")
if b2[3]>H*0.5: iss.append("主标题越中线")
if luma(FG)-luma(BG)<120 or luma(acc)-luma(BG)<60: iss.append("对比度不足")
print(f"{'OK ' if not iss else 'WARN'} l1={f1.size} l2={f2.size} sub={fs.size} bar={fb.size}"+("" if not iss else " ⚠ "+"; ".join(iss)))
