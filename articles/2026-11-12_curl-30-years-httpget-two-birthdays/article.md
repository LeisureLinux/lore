---
title: "curl 30 年：两个生日、三十亿装机量，和一个不肯设终点的人"
date: 2026-11-12
slug: curl-30-years-httpget-two-birthdays
category: 技术/解读
author: FreeLAMP.com
original_source: "一手核对：Daniel Stenberg《30 years of Internet transfers with curl》（daniel.haxx.se，2026-11-11）全文，含 httpget 起源、1996 年互联网数据、两次改名、curl 4.0、社区/BDFL/独立性/数字/未来各节 ＋ curl 官方历史页 curl.se/docs/history.html（HttpGet 0.1 1996-11-11、Daniel 的 0.2 1996-12-17、urlget 2.0 1997-08、2001 年换 MIT/MPL 许可）＋ curl.se 首页（over twenty billion installations 与协议清单）＋ Daniel《ignore the slop》（2026-10-22，AI 生成漏洞报告立场）＋ Daniel《Do minor curl vulnerabilities in the open》《OSI approved the curl license》《A curl audit by Aisle》等近期博文标题作背景"
original_date: 2026-11-11
original_url: "https://daniel.haxx.se/blog/2026/11/11/30-years-of-internet-transfers-with-curl/"
description: "本文解读 Daniel Stenberg 的 curl 30 周年长文，并用 curl 官方历史页与首页交叉核对。核心事实：项目有两个生日 —— 1996-11-11 巴西学生 Rafael Sagula 发布 100 多行 C 的 httpget 0.1（只用 IPv4 地址、无主机名/URL、几乎无错误检查），Daniel 为 Amiga IRC 频道机器人查汇率而找到它，1996-12-17 发布带自己补丁的 0.2；1997-08 因支持 FTP 改名 urlget 2.0；1998 年加上传（FTP upload / HTTP POST）后改名 cURL，1998-03-20 的 curl 4.0 已有 3300 行代码、24 个命令行选项、3 种协议。文章把 1996 年的对照数据摆出来：瑞典家庭平均 30 kbps、全球 3600 万网民 / 25 万网站，如今 200 Mbps、60–70 亿用户 / 10 亿网站。也梳理Daniel 自述的工程与治理观：1999-09 才全面用 CVS、2010 转 git；23 年里 curl 只是业余爱好，后来变成全职；curl 不是法律实体、不隶属任何基金会或公司；他仍是 BDFL 但强调数千贡献者、每年数百新作者；libcurl 估算 300 亿装机（官网首页另写「超过 200 亿」，说明是粗估）；支持二十多种 URL scheme，是 HTTP/2、HTTP/3 早期采用者，2009 年首次参加斯德哥尔摩 IETF 会议并进入 HTTPbis。重点写他最不客气的两段：把一切免费送出去之后「再试着让人付钱」不是好买卖、开源会持续有资金问题且太多项目系于单一维护者；以及「不相信 AI 会杀死开源」，结合 10 月《ignore the slop》里「AI 辅助的漏洞报告常常准确，忽略真实漏洞只会让用户更不安全」的立场。结尾纪念 2016 年去世的 Rafael Sagula，并点出全文没有终点目标、只有持续打磨的行事方式。"
published: true
---

> 一手：Daniel Stenberg 30 周年长文全文、curl 官方历史页与首页
> 对照：Daniel 近期关于 AI 生成漏洞报告的博文
>
> 这篇纪念文最容易被漏掉的一句，藏在结尾：「我们有两个生日。」

11 月 11 日，Daniel Stenberg 发了《30 years of Internet transfers with curl》。按惯例这类文章容易写成「从 100 行代码到三十亿设备」的励志叙事，但 Daniel 自己在末尾堵了这个读法：

> 前不久不是刚过 25 周年吗？是的，我们有两个不同的生日：httpget 生于 1996 年 11 月，curl 生于 1998 年 3 月。

两个生日：1996 年 11 月 11 日诞生的是 `httpget`，1998 年 3 月诞生的是 `curl`。这次纪念的是前者，而后者还要再等四个月。把这个分清楚，整篇的时间线才立得住。

## 一、从汇率机器人到 curl 4.0

curl 官方历史页把 Daniel 博文里凭记忆写的部分补全了：

| 时间 | 事件 |
|---|---|
| 1996-11-11 | 巴西学生 Rafael Sagula 发布 HttpGet 0.1：100 多行 C，只用裸 IPv4 地址，没有主机名/URL，几乎没有错误检查 |
| 1996-12-17 | Daniel 的 0.2：他当时在给 EFnet 上某个 Amiga 频道写 IRC bot，想让机器人提供汇率换算，需要自动抓取数据；找到 HttpGet 后修 bug、加域名解析，用邮件发 diff 给 Rafael |
| 1997-08 | 加了 FTP 下载，`httpget` 名字不再准确 → urlget 2.0 |
| 1997-11 / 1998 初 | FTP upload、HTTP POST 陆续加入 |
| 1998-03-20 | 再加上传后第二次改名 cURL（含 URL、能念、好敲），curl 4.0：3300 行代码、24 个命令行选项、3 种协议 |
| 1999-09 | 项目才全面采用 CVS；2010 年转 git |
| 2001-01 | curl 7.5.2 改用 MIT（或 MPL） 许可，结束此前与 GPL 项目的兼容争议 |

Daniel 在博文里对当年那段有个很诚实的反省：看到 100 行 C 就把 HTTP 的「语言」看懂了，「后来我才明白那是一种简洁的幻觉」。这句比任何「协议很简单」的入门教程都准确 —— 三十年后 curl 支持二十多种 URL scheme，HTTP 引擎是投入最多的部分，也是 HTTP/2、HTTP/3 的早期实现之一。

他还顺手给了 1996 年的坐标：瑞典家庭平均网速 30 kbps（V.90 把调制解调器提到 56 kbps 之前），全球 3600 万网民、25 万网站；今天瑞典平均 200 Mbps，全球 60–70 亿用户、约 10 亿网站。SSL 当年存在但少用，只覆盖极少数站点。

## 二、三十年攒出来的治理方式

这篇长文真正有分量的部分，是 Daniel 反复讲「怎么维持」而不是「做了什么」：

- 没有终点目标。 原文写得干脆：「I don't have an end goal with curl and I never did」—— 只想把网络传输做到尽可能快、安全、用对协议；「不赶着去哪儿，就是不停往前走，永不停止地打磨、拧紧每一颗螺栓」。
- 不依附任何组织。 curl 不是法律实体、不是正式组织，没有 umbrella、不属于任何公司，就是「一群松散连接在互联网上的人 + 几个邮件列表 + 一个网站 + 一些 git 仓库」。他称这大概是软件项目能做到的最自由独立状态。
- BDFL 但不独角戏。 他承认自己仍是 Benevolent Dictator For Life，紧接着强调「curl 从来不是单人马戏」： literally 数千人贡献过代码，每年有数百名新作者；船大到某个尺寸就不可能只靠船长。
- 开源给的，和开源要的。 他坚持宽松许可，因为「把共同、开放的积木块建好」是行业能按想要的速度出货的前提；但也不粉饰：「把一切都免费送出去，然后再试着让人为此付钱，不是个好推销」。他直说开源会继续有资金问题，太多项目「随一个维护者的存亡而起落」。
- IETF 那条线。 2000 年代末他加入 HTTPbis 邮件列表，2009 年第一次参加 IETF 会议（斯德哥尔摩），见到了 Roy、Larry、Mark、Julian 这些 HTTP RFC 作者。从「读 100 行 C 学协议」到「参与写协议」，是这条三十年线最漂亮的闭环。

关于规模，有个值得自己核一下的细节：博文写 libcurl 估算 300 亿装机（thirty billion），并明说这是粗估 —— 大多数使用者从不告知，只能靠 credit 屏幕、开源许可窗口或手册里提到它来推断，一个流行 App 今天用明天不用就能让数字浮动几十亿。而 curl.se 首页写的是「超过 200 亿装机」。同一项目两个官方页面口径不同，恰好证明 Daniel 自己那句「rough estimate」不是谦辞。本文标题取博文口径，但把它标成估算。

## 三、AI 那句判断，要结合他一个月前的话读

周年文里最容易被断章取义的是「不相信 AI 会杀死开源」这句。孤立看像一句乐观表态，但 Daniel 十天前刚写过《ignore the slop》，立场具体得多：

有人劝他「直接忽略 AI 生成的漏洞报告」，他回答这做不到也没用：AI 辅助产出的报告经常是准确的，有时真指出漏洞；因为报告来自 AI 就忽略真实漏洞，「不会让用户更安全，只会让他们更脆弱」。他不把这些叫 slop，因为报告通常正确，只是太啰嗦。

把两篇放一起，他的意思就清楚了：AI 会改变开源项目的输入负载（更多报告、更多噪声要分诊），但不会取消「共同开放的基础组件」这个需求。这跟他谈资金问题、谈单一维护者是同一种不粉饰 —— 承认压力，不唱衰，也不喊口号。近期博文列表里还有《Do minor curl vulnerabilities in the open》《OSI approved the curl license》《A curl audit by Aisle》，方向一致：把流程、许可、审计都摊开做。

## 四、个人与纪念

Daniel 写前 23 年 curl 只是业余爱好，同期换过很多工作、结婚、买房、两个孩子长成大人，「不知怎么把爱好变成了全职工作」。他说动力来自设计架构、设计 API、想明白怎么给数十亿设备提供网络传输能力这些事本身；几周后满 56 岁，希望还能再干几十年。

文章最后一段留给 Rafael Sagula：那位 1996 年贴出 100 行代码的巴西学生2016 年去世了，Daniel 写「感谢他替我们踢出了这一脚」。这也是为什么标题里的「30 年」不该只算到 Daniel 头上 —— 没有那 100 行、没有当年用邮件互发 diff 的习惯，后面的故事不会开始。

## 五、事实边界

- 本文事实以 Daniel 2026-11-11 博文为主，时间线细节（0.2 发布日期、urlget 2.0、MIT/MPL 许可切换、IRC 汇率机器人）以 curl 官方历史页 `curl.se/docs/history.html` 交叉核对；两处日期口径以官方历史页为准。
- 「两个生日」为 Daniel 原文明确区分：httpget 1996-11、curl 1998-03；媒体常写的「curl 25 周年」对应后者。
- 300 亿装机为博文估算、首页另写超过 200 亿，本文未把任一数字当作精确统计。
- 协议数量、HTTP/2 与 HTTP/3 早期采用、IETF 参与、BDFL 与独立性等均为作者自述；本文未独立验证协议实现细节或贡献者统计。
- 《ignore the slop》引述据 2026-10-22 原文，仅用于解释周年文中的 AI 判断，不代表对 AI 生成报告质量的普遍结论。

## 六、结论

三十年这篇里，最不像庆功话的一句其实是坦白「开头大多做错了，只是不断学习、调整、重试、迭代、一版一版发下去」。没有终点、没有宏大路线图，靠几十年持续交付稳定的高质量把世界拿下。

把它和那些「开源不可持续」的讨论放一起看，Daniel 给的答案很朴素：项目能活三十年，靠的不是某个天才设计，是宽松许可、透明流程、数千贡献者、以及一个二十三年里每天每周都愿意拧紧螺栓的人。至于 AI —— 它改变的是报告队列的长度，不是这个结论。

## Sources

- Daniel Stenberg《30 years of Internet transfers with curl》（2026-11-11）：<https://daniel.haxx.se/blog/2026/11/11/30-years-of-internet-transfers-with-curl/>
- curl 官方历史页：<https://curl.se/docs/history.html> ｜ curl 首页：<https://curl.se/>
- Daniel Stenberg《ignore the slop》（2026-10-22）：<https://daniel.haxx.se/blog/2026/10/22/ignore-the-slop/>
- Daniel 近期相关：《Do minor curl vulnerabilities in the open》<https://daniel.haxx.se/blog/2026/10/20/do-minor-curl-vulnerabilities-in-the-open/> ｜《OSI approved the curl license》<https://daniel.haxx.se/blog/2026/10/15/osi-approved-the-curl-license/>
