#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""2026-10-19 第二批 9 篇封面。"""
import os
from PIL import Image, ImageDraw, ImageFont
BASE=os.path.dirname(os.path.abspath(__file__))
FB="/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc"; FR="/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
W,H=1200,675; BG=(10,13,18); FG=(240,244,250); MUTED=(130,140,152); SAFE=56

CFG=[
 dict(slug="2026-10-19_zero-standing-privilege-machine-identities", accent=(96,165,250),
      l1="轮换只是买时间", l2="关键在没人能关掉它",
      sub="吊销改有效性，轮换只改值", bar="Drift 洗了 700 家组织 · Okta 靠 IP 白名单+DPoP 挡住"),
 dict(slug="2026-10-19_pwnescape-cve-2026-99999-linux-networking-vm-escape", accent=(244,114,182),
      l1="17 年的内核 bug", l2="AI 用 3 天找到",
      sub="而修复只堵了 5 个消费点", bar="32 字节 = 60 − 28 · 44 行补丁作者说这不是完整修复"),
 dict(slug="2026-10-19_flatpak-sandbox-security-debate-flatkill-rebuttal", accent=(250,204,21),
      l1="沙箱是安全的", l2="而应用不是",
      sub="这句 2023 年的判断，2026 年收到了两个新证据", bar="CVE-2026-34078 完整逃逸 · ArchWiki 至今警告未有效沙箱化"),
 dict(slug="2026-10-19_tee-attestation-forgery-threat-model", accent=(167,139,250),
      l1="打断一台", l2="等于打断全部",
      sub="你的验签器接受任何一台合格 CPU 的证书", bar="提取成本 <1000 美元 · Intel 官方定性「不在范围内」"),
 dict(slug="2026-10-19_nist-ecdsa-curve-seeds-lrand48-timestamp", accent=(52,211,153),
      l1="二十五年的后门疑云", l2="答案是一个时间戳",
      sub="lrand48 + Unix time，不是任何哈希", bar="0x330E 倒推 · 十个时间戳落在 1997-05 至 1998-04"),
 dict(slug="2026-10-19_gentoo-chromium-last-rites-maintainer-burnout", accent=(251,146,60),
      l1="Gentoo 给 Chromium", l2="做了临终祷告",
      sub="602 个 CVE 是测量结果，不是失职的证据", bar="每周 6 小时 · 需 3 人 · 实有 1 人 · 单次编译 15 小时"),
 dict(slug="2026-10-19_innodb-vs-iceberg-olap-migration-internals", accent=(56,189,248),
      l1="8,000 字换 9 个月", l2="只为只读两列",
      sub="从 InnoDB 到 Iceberg，换掉的是引擎替你做的决定", bar="三层剪枝 · 乐观/悲观提交对照 · 100GB 的教训"),
 dict(slug="2026-10-19_tplink-eap770-dma-cache-bug-kernel-exploit", accent=(239,68,68),
      l1="校验和是对的", l2="数据是错的",
      sub="64 字节缓存行，两年，五个错误假设", bar="fast_recycled 跳过 invalidate · 8% 速度换正确性"),
 dict(slug="2026-10-19_rtx-spark-laptop-arch-linux-arm-nvidia", accent=(34,211,238),
      l1="128GB 统一内存", l2="装上了 Arch Linux",
      sub="代价是自己写 ACPI 覆盖和驱动补丁", bar="116.0 GiB 同一池 · Blackwell 只能跑开源内核模块"),
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
    print(f"{'OK ' if not iss else 'WARN'} {c['slug'][:50]:52s} l1={f1.size} l2={f2.size}"+("" if not iss else " ⚠ "+"; ".join(iss)))
