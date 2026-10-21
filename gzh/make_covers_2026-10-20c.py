#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
from PIL import Image, ImageDraw, ImageFont
BASE=os.path.dirname(os.path.abspath(__file__))
FB="/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc"; FR="/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
W,H=1200,675; BG=(10,13,18); FG=(240,244,250); MUTED=(130,140,152); SAFE=56

CFG=[
 dict(slug="2026-10-21_pingcap-tidb-cloud-breach-fulcrumsec", accent=(239,68,68),
  l1="10.6 TB 被窃", l2="而凭证就写在自家仓库里",
  sub="88 次连续导出，没有一次检测事件",
  bar="官方确认 SQL 编辑器文本被导出 · 攻击方称 11.5 万组 API Key"),
 dict(slug="2026-10-20_nginx-three-critical-flaws-config-dependent", accent=(34,197,94),
  l1="三个 9.2 分漏洞", l2="而决定风险的是配置",
  sub="查版本号是错的起点，该查配置组合",
  bar="三者向量都是 AC:H · 97205 其实是 UAF 不是堆溢出"),
 dict(slug="2026-10-20_php-critical-security-release-oct-21-2026", accent=(139,92,246),
  l1="两个 CVSS 9.2", l2="在 14:00 UTC 发布",
  sub="而真正的难点是「你根本不知道自己跑什么版本」",
  bar="只有 8.2–8.5 会被修 · 补丁发布后你依然脆弱"),
 dict(slug="2026-10-20_pwnescape-kvm-escape-broader-attack-surface", accent=(244,114,182),
  l1="逃出来的地方", l2="不是 hypervisor",
  sub="而是主机内核的最低层",
  bar="只更新 guest 不能修复 · 必须更新 host"),
 dict(slug="2026-10-20_omarchy-4-5-rc1-aarch64-snapdragon-n1x", accent=(56,189,248),
  l1="三类 ARM 同时跑起来", l2="而这不是「多了个架构」",
  sub="Snapdragon 拉 Windows 固件 / N1X 开源驱动 / Apple 合并 fork",
  bar="启动 6 秒→1 秒 · 每显示器工作区 · 50 种语言"),
 dict(slug="2026-10-20_rtx-pro-5500-china-orders-export-compliant", accent=(251,191,36),
  l1="600 万张订单", l2="交付上限 5%",
  sub="而产能被下一代旗舰抽走了",
  bar="350 亿美元是意向 · 实际 30–60 万张"),
 dict(slug="2026-10-20_encrypted-dns-providers-adguard-controld", accent=(45,212,191),
  l1="加密 DNS 藏住了域名", l2="没藏住 IP 和 SNI",
  sub="而 ECH 的前提恰恰是 DNS 必须加密",
  bar="「不绑定 IP」是有条件的 · 别删 2011 CA 那类反直觉"),
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
