#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
from PIL import Image, ImageDraw, ImageFont
BASE=os.path.dirname(os.path.abspath(__file__))
FB="/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc"; FR="/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
W,H=1200,675; BG=(10,13,18); FG=(240,244,250); MUTED=(130,140,152); SAFE=56

CFG=[
 dict(slug="2026-10-21_unix-history-origins-system-v-bsd-split", accent=(251,146,60),
  l1="Unix 分裂的答案", l2="在一份 1956 年的同意令里",
  sub="AT&T 不能卖 Unix，只能送源码，150 美元一盘磁带",
  bar="1982 拆分 → System V → 十八年版权诉讼"),
 dict(slug="2026-10-21_commercial-unix-2026-aix-hpux-solaris-status", accent=(239,68,68),
  l1="商业 Unix 只剩一个在开发", l2="HP-UX 刚刚断线",
  sub="它死于一枚停产的 CPU，不是死于技术",
  bar="AIX 支持到 2028 · Solaris 自 2018 无大版本 · Xenix 1996 就停了"),
 dict(slug="2026-10-21_bsd-family-2026-freebsd-openbsd-netbsd-ghostbsd", accent=(34,211,238),
  l1="浪潮 K-UX 拿到了 UNIX 认证", l2="而它是 RHEL 衍生版",
  sub="认证是三年期商标许可，血统是永久的",
  bar="FreeBSD 15.1 · OpenBSD 8.0 · NetBSD 11.0 · GhostBSD 26.1"),
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
    print(f"{'OK ' if not iss else 'WARN'} {c['slug'][:48]:50s} l1={f1.size} l2={f2.size}"+("" if not iss else " ⚠ "+"; ".join(iss)))
