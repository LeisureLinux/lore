---
title: "Firefox 反指纹：75% 降到 46%，以及一次拿 2500 万用户做研究的伦理设计"
date: 2026-11-12
slug: mozilla-firefox-fingerprinting-ccs2026
category: 技术/解读
author: FreeLAMP.com
original_source: "一手核对：Mozilla Security Blog《Open research, stronger privacy: Making Firefox users harder to fingerprint》（Tom Ritter、Frederik Braun、Christoph Kerschbaumer，2026-11-10）全文 ＋ CCS 2026 论文《Large-Scale Measurement and Real-World Mitigation of Web Browser Fingerprinting in the Wild》扩展版 PDF 全文（近 2500 万 Firefox 发布版用户遥测、75%→46%、OHTTP、cohort 分析、三家商业指纹库、伦理附录与局限章节）＋ Mozilla Research 论文页（作者列表、CCS '26 2026-11-15–19 海牙）＋ Mozilla 2025-11-10 博客《Firefox expands fingerprint protections》（Firefox 145、unique 用户近乎减半、Private Browsing / ETP Strict 首发）＋ fingerprinting.study 测试套件 ＋ Firefox 官方 Resist Fingerprinting 支持文档与 mod_http2 无关的浏览器指纹背景"
original_date: 2026-11-10
original_url: "https://blog.mozilla.org/security/2026/11/10/open-research-stronger-privacy-making-firefox-users-harder-to-fingerprint/"
description: "本文解读 Mozilla 2026-11-10 的反指纹研究公告，并以 CCS 2026 论文与 2025 年官方博客交叉核对。核心数字：基于近 2500 万 Firefox 发布版用户的真实遥测，反向工程 Akamai、Fingerprint Pro、Signifyd 三家商业指纹库，量化各特征的熵与用户唯一性；论文明确写出防护把「唯一可识别用户」比例从 75% 降到 46%，同时扩大共享同一指纹的 cohort。具体做法分三类：减少暴露（屏幕分辨率 API 只隐藏任务栏/dock 的尺寸位置）、标准化（处理器核心数只报 4 或 8）、以及让图像渲染、Web Audio、Android 数学运算输出更一致；语言与时区等网站必需信息保留；随机化也在用，但 Mozilla 与论文都承认其收益难以量化、不在本次测量范围内。文章重点写「开放研究」背后的伦理设计：所有特征经 OHTTP 以独立 probe 提交，中继看到 IP 看不到内容、Mozilla 看到内容看不到 IP；严格限制数据访问与留存，单条遥测记录数月前已删除、只保留并公开聚合结果；约 7% 用户选择退出遥测带来的偏差被论文讨论。也标出三处容易读错的地方：① 75%→46% 那批防护在论文里写的是 Firefox 143 落地，而 2025/2026 两篇博客都写 Firefox 145；② 并非所有防护默认全开，隐藏任务栏尺寸是默认，其余先在隐私浏览与 ETP Strict 上线，走 Total Cookie Protection 同样的渐进策略；③ 论文不分析指纹稳定性、不复制商业服务端专有匹配算法，且明确承认改 API 与网页兼容性存在根本权衡。结论：这是把「大规模实测 → 挑最高熵特征 → 分级上线」做成可复现方法学的一次实践，比单点补丁更值得关注。"
published: true
---

> 一手：Mozilla 安全博客、CCS 2026 论文扩展版、2025 年官方防护公告
> 对照：官方支持文档、公开测试套件
>
> 这篇公告最值得读的不是防护清单，是它怎么合法地拿两千万人的浏览器特征做研究。

11 月 10 日 Mozilla Security Blog 发了《Open research, stronger privacy: Making Firefox users harder to fingerprint》，三位作者 Tom Ritter、Frederik Braun、Christoph Kerschbaumer。它对应的论文《Large-Scale Measurement and Real-World Mitigation of Web Browser Fingerprinting in the Wild》被 CCS 2026 接收（11 月 15–19 日，海牙），并配了 `fingerprinting.study` 网站与浏览器测试套件。

标题叫「开放研究」，这四个字是有分量的 —— 论文把指纹跟踪称为「largely invisible to users」，正因为用户既看不见也删不掉，才需要厂商用这种规模的数据自己去量。

## 一、先看数字：75% → 46%

论文摘要里最硬的一句：

> 基于近 2,500 万 Firefox 发布版用户的真实遥测，量化各特征对唯一性的贡献；防护把唯一可识别用户比例从 75% 降到 46%，同时保持网页兼容性。论文把这一结果概括为在保持网页兼容性的前提下降低用户唯一性。

「唯一」的定义是 cohort size = 1 —— 在数据集里，这个人的指纹组合只出现一次。论文特意说这还不够，原话是「cohort structure」不能由唯一用户比例代替：两个数据集唯一用户比例相同，共享指纹的群组结构可能差很远（剩下的人全挤在一个大组里，和全都是两人一组，隐私含义完全不同），所以同时报告了 cohort 结构。

方法上，他们反向工程了三家商业指纹服务：Akamai、Fingerprint Pro、Signifyd，逐个列出各自采集的测量项（Accept-Language、Audio Fingerprint、FPJS Canvas Image、Available Resolution、Timezone Offset、CPU Count、User Agent、CSS System Colors/Fonts 等），再把这些测量组合成「该服务能看到的信息」的规范指纹，模拟其识别能力。论文也注明：服务端匹配算法是专有的，没有复制，评估的是「信息可得性」而非厂商内部行为。

这解释了博客那句「保护少数几个浏览器特征就能显著削弱流行指纹技术」—— 不是拍脑袋选的，是量出来的熵排序。

## 二、具体改了什么

Mozilla 把手段分成三类，博客与论文措辞略有不同，合起来看：

| 类型 | 例子 | 目的 |
|---|---|---|
| 减少暴露 | 屏幕分辨率 API 隐藏系统任务栏 / dock 的尺寸与位置 | 桌面布局细节不再进指纹 |
| 标准化 | 处理器核心数只报 4 或 8，不报精确值；字体白名单补齐 9 个特定 locale 字体 | 把连续值收敛成少数桶 |
| 一致性修复 | 图像渲染、Web Audio、Android 上的数学运算输出更统一 | 消除同一浏览器在不同硬件/平台上的细微差异 |

保留的是网站真正需要的信息：语言、时区。Mozilla 的目标写得很直白 —— 让更多用户的浏览器在指纹脚本眼里「长得一样」，同时不把日常网站弄坏（论文里专门讨论了 breakage：改 Web API 减指纹，根本权衡就是用户体验与网页兼容性，所以他们拒绝把选择丢给用户弹窗，也拒绝照搬 Tor Browser 那种高破坏性的严格模式）。

还有一类手段博客单独提了：随机化（canvas readback 之类注入上下文相关的确定性噪声）。但两边都很诚实地标注：随机化的收益难以量化，不在本次报告的测量范围内。所以 75%→46% 这个数字，主要归功于减少暴露与标准化，不能算到随机化头上。

## 三、「开放研究」四个字背后的伦理设计

这部分最容易被转述漏掉，也是我觉得最值得写的地方。要研究「怎么让人不被指纹识别」，前提是先大规模收集真实的浏览器特征 —— 这本身就是一件敏感的事。论文的附录 A 与博客给出的 safeguards：

- OHTTP（Oblivious HTTP）：每项用户特征作为独立 probe 通过中继提交。中继看到用户 IP、看不到请求内容；Mozilla 收到内容、看不到 IP。两者被协议拆开。
- 访问与留存：严格限制数据访问；单条遥测记录数月前已删除，只保留并公开聚合结果用于开放科学。
- 选择偏差：Firefox 遥测可退出，论文估计约 7% 用户关闭；作者讨论过这个偏差，认为数据集既非自选择、也无强地域倾斜，影响有限。
- 不弹窗：论文明确反对把决定丢给用户 —— 指纹议题复杂、用户难以做知情一致的选择，且提示疲劳会让弹窗变成噪声。

也就是说，Mozilla 用「IP 与内容分离 + 最小留存 + 只发布聚合」把一次潜在的隐私风险，转成了可公开复核的方法学。对比某些「为了反追踪而先大范围采集」的争议，这套设计是有参考价值的。

## 四、三处容易读错的地方

① 版本口径不一致。 论文原文写「这批防护随 Firefox 143 落地」，而 2025-11-10 的官方博客与 2026-11-10 这篇都写 Firefox 145。合理解读是 143 起分批落地、145 完成某一阶段；但两处一手材料确实不同，写稿时按各自出处标注，不替 Mozilla 统一成一个版本号。

② 不是全部默认全开。 博客明说：像隐藏任务栏/dock 这类所有浏览模式默认开启；其余防护先在隐私浏览窗口与 ETP Strict 模式上线，走的是当年 Total Cookie Protection 用过多年的渐进策略，正朝默认启用推进。想在所有窗口都拿到，需要到增强型跟踪保护设置里选 Strict；若遇到网站功能异常，官方给了回退步骤。把这读成「Firefox 145 之后人人自动满配」是错的。

③ 论文的边界。 不分析指纹稳定性（随机化会降低稳定性，但作者说这接近随机化范畴、不在本次分析内）；不复制专有服务端算法；不覆盖超出威胁模型的场景；并承认 breakage 报告只占实际问题的一小部分。再加上 Mozilla 特意说明随机化收益「难以量化」—— 46% 不是「反指纹完成度」，是在这套测量框架下的结果。

顺带一个时间坐标：2025-11-10 那篇博客已经宣布「第二阶段防护完成、unique 用户近乎减半」，2026-11-10 这篇属于把支撑那批决策的研究、数据与论文公开，并非新功能首发。中间还夹着 2026 年 5 月那批 mod_http2 / 证书相关旧文，别把两个十一月的公告当成同一件事。

## 五、和其它防护的层次

博客末尾把配套能力列了一圈，值得按层次理解：

- Total Cookie Protection：始终开启，按站点分割有状态标识，解决「cookie 跨站跟随」；
- Fingerprinting Protections（本文主角）：解决无状态的跨站识别；
- Firefox Relay：邮箱掩码，防数据经纪商用邮箱串联订阅；
- 内置免费 VPN：隐藏 IP。

前两层是浏览器内建、默认或分级自动的；后两层是账号/网络侧的可选能力。另外 Firefox 还有一个更严格的 `privacy.resistFingerprinting`（RFP，about:config 高级项）：会把 canvas 读出变随机噪声、时区报 UTC、locale 报 en-US、数学结果微扰、限制字体，官方支持文档明确写「对多数用户不推荐，可能造成网站异常」，且扩展可能悄悄开启它。这跟本文的「分级上线、保兼容」是两条不同路线，别混为一谈。

## 六、结论

把这篇压缩成一句：Mozilla 先用近 2,500 万用户的真实数据找出「哪几个特征最让人独一无二」，再只改那几个，把唯一用户从 75% 压到 46%，并把方法、数据与伦理设计全部公开。

单点补丁（字体白名单、canvas 加噪）业界早就有，真正新的是用大规模实测给防护排优先级、并用 cohort 而非单一比例来验收。76 页论文里那些「数据集规模影响唯一性估计」「按 OS 分群会改变结论」的方法学讨论，比结论本身更该被同行复用。

当然也别过度读：46% 仍意味着近一半用户在这套框架下可被唯一识别；随机化没被量化；部分防护还只在 Strict / 隐私浏览里；论文自己列了一串局限。这是「把追踪精度实质打下去」，不是「指纹问题解决了」。

## 七、事实边界

- 75%→46%、近 2,500 万用户、OHTTP 独立 probe、约 7% 退出率、三家商业指纹库、cohort 定义均取自 CCS 2026 论文扩展版；博客只给结论未给完整方法学。
- 「Firefox 143 落地」出自论文，「Firefox 145」出自 2025 与 2026 两篇官方博客，本文按出处分别标注，未替官方调和。
- 本文未运行 `fingerprinting.study` 测试套件、未实测本机 Firefox 的指纹变化；防护开关状态以 2026-11-10 官方博客为准，具体版本行为可能随发布变化。
- 论文不分析稳定性、不复制专有匹配算法、承认兼容性权衡，这些限制均按原文转述。

## Sources

- Mozilla Security Blog《Open research, stronger privacy: Making Firefox users harder to fingerprint》（2026-11-10）：<https://blog.mozilla.org/security/2026/11/10/open-research-stronger-privacy-making-firefox-users-harder-to-fingerprint/>
- CCS 2026 论文扩展版 PDF：<https://research.mozilla.org/files/2026/11/large-Scale_measurement_and_real-world_mitigation_of_web_browser_fingerprinting_in_the_wild_extended_version.pdf>
- Mozilla Research 论文页：<https://research.mozilla.org/> ｜ 测试套件：<https://fingerprinting.study/>
- Mozilla《Firefox expands fingerprint protections》（2025-11-10）：<https://blog.mozilla.org/en/firefox/fingerprinting-protections/>
- Firefox 官方 Resist Fingerprinting 支持文档：<https://support.mozilla.org/en-US/kb/resist-fingerprinting> ｜ 产品页：<https://www.firefox.com/en-US/features/block-fingerprinting>
