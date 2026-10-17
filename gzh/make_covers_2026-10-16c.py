#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""2026-10-16（第三批）两篇封面。"""
import os
from PIL import Image, ImageDraw, ImageFont
BASE = os.path.dirname(os.path.abspath(__file__))
FB = "/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc"
FR = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
W, H = 1200, 675
BG=(10,13,18); FG=(240,244,250); MUTED=(130,140,152); SAFE=56

CFG = [
    dict(slug="2026-10-16_starling-office-ai-generated-suite", accent=(96, 165, 250),
         l1="Starling 用 Claude 写出了",
         l2="一个办公套件",
         sub="而它和同一周那批 AI 政策，正好指向相反的方向",
         bar="Swift + Wayland 合成器 + X11 服务器 · Apache-2.0 · 单人匿名维护"),
    dict(slug="2026-10-16_xorg-17-cves-client-libraries", accent=(248, 113, 113),
         l1="不到两周，X.Org 又发了 17 个 CVE",
         l2="而这次全在客户端库里",
         sub="威胁模型反过来了：以前防恶意客户端，现在防恶意服务器",
         bar="libX11 / libXi / libXrender 等 · 唯一 8.3 的是越界写 · 多在扩展里"),
]

def fit(d,t,fp,start,mw):
    sz=start
    while sz>16:
        f=ImageFont.truetype(fp,sz,index=2)
        if d.textlength(t,font=f)<=mw: return f
        sz-=1
    return ImageFont.truetype(fp,16,index=2)
def luma(rgb):
    r,g,b=rgb; return 0.2126*r+0.7152*g+0.0722*b

for c in CFG:
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
    print(f"{'OK ' if not iss else 'WARN'} {c['slug'][:52]:54s} l1={f1.size} l2={f2.size} sub={fs.size} bar={fb.size}"+("" if not iss else " ⚠ "+"; ".join(iss)))
