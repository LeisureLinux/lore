---
title: "Linux 内核 AI 缺陷报告：59 个真洞背后，卡住的是人"
date: 2026-11-14
slug: ai-bug-reports-linux-windows-review-bottleneck
category: 技术/解读
author: FreeLAMP.com
original_source: "一手核对：ZDNet《'We need more reviewers': Finding Linux bugs is easy now – fixing them is another story》（Steven Vaughan-Nichols，2026-11-13 8:20 pm ET；微软 FORGE Lab 59 份上游报告、2026 年至 11 月 2 日内核 CVE 团队日均 27 个、11 月 Patch Tuesday 726 个 CVE、Lorenzo Stoakes 11-10 退出 reviewerships、GKH 在 Open Source Summit Europe 的问答、Linus 7.4-rc2 LKML 公告、Daniel Stenberg 采访、作者列举 11 月安全事件）＋ Microsoft Security Blog《Lessons from 59 Linux Kernel Bug Reports》（FORGE Lab 与 Cen Zhang，2026-11-11；MDASH 漏斗 26502 原始发现 → 11769 筛选候选 → 621 有 PoC → 59 上游报告；33 个 CVE、8 个确认本地提权利用、38 个修复已合入 mainline；两轮扫描服务器配置与模型 token 占比；621 例去向 266/163/133；首份公开报告 6-27、9-01 前 55 份公开；首个补丁到 mainline 中位 41 天、最长 108 天；59 个 bug 平均 8.1 岁、最老 cls_u32 至少 21 年；CVE-2026-64563 rhashtable 一行状态复位缺陷剖析；结论「Finding bugs and fixing them are drastically out of balance」把瓶颈明确归到人力上）＋ Lorenzo Stoakes 的 LKML 原帖与回复（2026-11-10 12:03 UTC 的 [PATCH 0/4] MAINTAINERS 移除 reviewerships；19:18 UTC 回复中「AI wave has been horrible」与 slop 频率从偶尔→每周→每隔几天→约一半以上；Andrew Morton 的 Nacked-by 玩笑；四个补丁与 CREDITS 条目）＋ Linux 7.4-rc2 LKML 公告（经 ZDNet 与多家媒体转述，Linus 提到 BPF 侧修复快过新报告）＋ curl 项目 Daniel Stenberg 相关报道（The Register 2026-10-21：Linux Foundation 调查约 25% PR 是 AI slop、大项目 31%；curl 调整低中危漏洞处理）＋ Phoronix / Linux Stans / CryptoBriefing 等关于 7.4-rc1 19671 commits 与 BPF 转折的报道作交叉验证"
original_date: 2026-11-13
original_url: "https://www.zdnet.com/innovation/ai-bug-reports-linux-windows/"
description: "核查 ZDNet「AI 让找 bug 变容易、修 bug 成了瓶颈」这条论断。文章以微软 FORGE Lab 的 MDASH 复盘为主证据：两周扫描产出 26502 条原始发现，经置信度筛选到 11769、QEMU 里做出 PoC 的 621 例，最终只形成 59 份上游报告（9.5%）；33 个 CVE 中 24 个 High 以上、8 个确认本地提权利用、38 个修复合入 mainline，首个补丁到进入 mainline 中位 41 天、最长 108 天，59 个 bug 平均已在内核里 8.1 年、最老至少 21 年。写清「四个人月才把发现变成报告」与把瓶颈明确归到人力上才是核心，而非 AI 找到了多少洞。第二部分核维护者侧：Lorenzo Stoakes 11-10 提交四个补丁移除 MM core / misc / reclaim / Rust 相关 reviewership，理由是 AI 生成系列带来的吞吐量超出带宽；后续回信把 slop 频率写成从偶尔到约一半以上，Andrew Morton 回了句 Nacked-by 玩笑。也标出 GKH「maintainers burnt out for ten years」是 ZDNet 转述的 OSS Europe 问答，Linus 7.4-rc2 关于 BPF 修复快过新报告只是局部信号、他本人说其他子系统尚未到达该点；Stenberg 的「manage the flood pretty well so far」是谨慎乐观而非问题解决。文章同时纠正几处口径：日均 27 个内核 CVE 来自 ZDNet 引用的第三方统计而非 CVE 官方公告、Windows 726 个 CVE 是 11 月 Patch Tuesday 单月总量、两者单位不可直接比较；Linux 侧「任何 bug 都可能是安全 bug」有 Linus 2024 年原话作背景。结论：AI 把发现端的成本压到接近零，把分类、复现、写补丁、review、合入这条人类链路暴露成系统瓶颈；短期答案不是更多扫描，而是更高信号比的提交规范与更多 review 人手。"
published: true
---

11 月 13 日 ZDNet 那篇文章的标题很准：找 bug 已经不难了，难的是修。作者 Steven Vaughan-Nichols 把微软 FORGE Lab 的 59 份内核报告、Lorenzo Stoakes 退出 reviewership、Greg Kroah-Hartman 的抱怨和 Linus 在 7.4-rc2 里的一句乐观放到了一起。

我把其中能核的一手源都翻了：微软安全博客的完整复盘、Stoakes 的 LKML 原帖与回信、以及 7.4-rc2 相关报道。结论比「AI 淹没开源」这种说法更具体，也更有用。

## 一、59 个真洞是怎么来的

微软 FORGE Lab 与 Cen Zhang 于 11 月 11 日发了复盘《Lessons from 59 Linux Kernel Bug Reports》。他们用代号 MDASH 的系统在 2026 年 5 月底到 6 月中扫描了内核的网络、文件系统、安全模块等子系统，漏斗如下：

| 阶段 | 数量 |
|---|---|
| 两周扫描的原始发现 | 26,502 |
| 置信度筛选 + 快速筛查 agent 后 | 11,769 |
| QEMU 里生成了 PoC 证据 | 621 |
| 最终形成上游报告 | 59（约 9.5%） |

ZDNet 只写了「59 份报告、其中有个 21 年前的洞」，容易让人以为 AI 一按就出货。实际是一名全职研究员加一名实习生做了三个月，扫描本身只占两周，其余全在把噪声变成可复现、可提交、可打补丁的东西。

621 个有 PoC 的案子里，266 个（42.8%）与别的案子同根因、163 个（26.2%）经评估安全影响有限而不报、133 个（21.4%）已被别人报过或上游已修。首份公开报告 6 月 27 日才发出，比扫描开始晚五周多；到 9 月 1 日公开了 55 份，另 4 份先私下报告、10 月中转到公开列表。

这些不是幻觉报告。33 个已分配 CVE，其中 24 个 CVSS 3.1 ≥ 7.0；8 个在受控环境里确认了本地提权利用；38 个修复已合入 mainline，一半一次过，其余经历 1–4 轮修改；从首个公开补丁到进 mainline 中位 41 天、最长 108 天。59 个 bug 平均在内核里躺了 8.1 年，最老的 `cls_u32` 位移越界至少 21 年。

微软自己给的结论，正好是 ZDNet 标题的出处：

> 「Finding bugs and fixing them are drastically out of balance.」

报告 59 个用了超过四个人月；五个月后仍有部分报告在与维护者往返。原文写得很清楚：agent 可以帮忙起草初始补丁，但人工验证、子系统理解、与维护者迭代依然不可省，把瓶颈明确归到人力上。

## 二、维护者这一侧发生了什么

11 月 10 日，ARM 工程师、内核 MM 子系统维护者 Lorenzo Stoakes 发了一组四个补丁，从 `MAINTAINERS` 里删掉自己的 MM core、MM misc/reclaim、MM Rust 相关 reviewership，并给自己加一条 CREDITS（THP 共同维护）。cover letter 的原话是：

> 他写道：AI 生成的补丁系列带来的吞吐量，已经让他没有带宽再对维护领域之外普遍提供 review

他随后在回信里把趋势写得更具体：最早偶尔看到 slop，后来每周至少一次，再后来每隔几天，现在差不多是我看到的一半甚至更多；并补了一句「AI 这一波很糟糕，而且还在明显变糟」。Andrew Morton 回了句带情绪的玩笑：能不能给他一个 `Nacked-by`

这里要标一处 ZDNet 的简化：文章写他「放弃审代码」，但补丁与后续回信都表明，他保留自己维护领域的 review，只是不再对全领域兜底；他甚至自嘲「这个前提多半是假的，我大概还是会去审各种东西」。这是收窄收件箱，不是退出内核。

ZDNet 还引了 GKH 在 Open Source Summit Europe 问答里的话：「没有足够的人审 LLM 生成的补丁……维护者已经 burnout 十年了」，以及 Linus 在 7.4-rc2 公告里说 BPF 侧「修复来得比新报告快，或许是转机的苗头」。这两处都属转述/局部信号：Linus 同一段就写了「大多数其他领域还没到那一步」「别屏息，最多交叉手指」；GKH 在采访里对「AI 修复何时追上报告」的回答是「更近了，但还没到」，连估计都不肯给。curl 的 Daniel Stenberg 说的是「目前为止我们把这波洪水管理得还行，会随某周谁又发来一批发现而起伏」—— 谨慎乐观，不是问题解决。

## 三、几个不能混着读的数字

ZDNet 为了说明「不只是 Linux」，摆了两组数：2026 年至 11 月 2 日内核 CVE 团队日均 27 个 CVE，以及 11 月 Patch Tuesday 726 个 CVE。这里有三个口径问题：

- 日均 27 是文章引用的第三方统计（`free-linux.com` 转述内核 CVE CNA 数据），不是 CVE 官方公告里的数字；
- 726 是 11 月单月的微软补丁日总量，与「日均」不是同一量纲，文中「绝大多数来自 AI 程序员」也未给出来源拆分；
- 内核侧还有个背景：Linus 2024 年就说过「任何 bug 都可能是安全 bug，只要有人足够聪明想出滥用方式」。Linux 从手机到超算都跑，同一处缺陷在一台设备上是高危、在另一台上可能根本不出现 —— 所以内核 CVE 数量天然容易膨胀，不能简单等同于「漏洞变多了」。

把这三层拆开，ZDNet 的定性判断（AI 把发现端产量拉高）依然成立，但具体数字不宜当成同口径的行业指标。

## 四、真正被卡住的是哪一段

把两边的材料叠起来看，瓶颈其实很清晰：

1. 发现端：模型 + 静态扫描 + PoC agent 已经能低成本量产候选，MDASH 两周给出 2.6 万条。
2. 甄别端：去重、判根因、判安全影响、判断是不是已经被报过，全靠懂子系统的人。621 → 59 这一步，42.8% 是同根因合并，21.4% 是撞车。
3. 修复端：上游惯例是「报漏洞要带能用的补丁」，agent 起草初稿可以，验证与迭代不行；38/59 合入、中位 41 天。
4. review 端：维护者带宽是固定值。Stoakes 的退出、GKH 的「缺 reviewer」、curl 此前因 AI 报告洪流调整漏洞处理流程，说的都是同一件事。

AI 把第一段的边际成本压到接近零，后面三段却仍是人力密集型。 这就是「失衡」的完整含义。微软在结论里给的对策落在「聚焦真正高危的问题」，而不是再多扫几轮—— 因为猎人与维护者都会被真实发现的体量拖垮。

顺带一个反直觉的注脚：那 59 个洞平均 8.1 岁。AI 并没有制造新漏洞，它只是用更低成本翻出了长期没人有空去翻的旧账；账单最后还是落到同一批人手上。

## 五、边界

- 本文的 FORGE Lab 漏斗、时间与 CVE 数字来自微软 2026-11-11 官方博客；Stoakes 引语来自 11-10 LKML 原帖与回信；Linus 7.4-rc2 的说法经 ZDNet 与多家媒体转述，我未逐字核对 LKML 原信。
- GKH 在 OSS Europe 的问答、Stenberg 的采访，均为 ZDNet 转述，未找到逐字稿；Linux Foundation 调查（约 25% PR 为 AI slop、大项目 31%）来自 The Register 2026-10-21 报道，属另一份材料。
- 「AI 程序员贡献了绝大多数 11 月 Windows CVE」是 ZDNet 的归因，微软公告未给该拆分，本文不采纳为结论。
- 文末 ZDNet 列举的 11 月安全事件（TCP 9.8 分洞、Alpine OpenSSH、GitLab 险情、PHP2Shell）为作者列举，本文未逐项核实，仅作为背景提及。
- 本文未运行 MDASH、未复现任何 CVE，也未统计内核 CVE 总量。

## 六、结论

这条新闻真正值得记住的是一条长期被忽略的生产关系被暴露了，而非「AI 又找出 59 个内核洞」：开源安全的产能上限，从来不由「能发现多少问题」决定，而由「有多少人能读、能判、能写补丁、能 review」决定。

MDASH 的漏斗已经把答案算得很清楚 —— 2.6 万条发现最终变成 59 份报告，中间每一步都是人。BPF 那个「修复快过报告」的苗头值得高兴，但 Linus 自己都说了别屏息。短期更现实的解法，是让提交方承担更多复现与自检责任、把信号比提上去，以及正视 GKH 那句朴素到有点无奈的话：我们需要更多 reviewer。

## Sources

- ZDNet《'We need more reviewers': Finding Linux bugs is easy now – fixing them is another story》：<https://www.zdnet.com/innovation/ai-bug-reports-linux-windows/>
- Microsoft Security Blog《Lessons from 59 Linux Kernel Bug Reports》（2026-11-11）：<https://www.microsoft.com/en-us/security/blog/2026/11/11/lessons-from-59-linux-kernel-bug-reports/>
- Lorenzo Stoakes，LKML `[PATCH 0/4] MAINTAINERS: remove my reviewerships`：<https://lore.kernel.org/lkml/avMRk95T26rsq4JK@gremlin/T/> ｜ 回信：<https://lore.kernel.org/lkml/avNsYKFvA5u46us3@gremlin/>
- Linux 7.4-rc2 相关报道：<https://linuxstans.com/linux-7-4-rc2-ai-bug-fixes-bpf/> ｜ <https://cryptobriefing.com/linus-torvalds-ai-patch-flood-peaked/>
- The Register《AI cuts coding time, but it's also filling open source's inbox with crap》（2026-10-21）：<https://www.theregister.com/2026/10/21/linux_foundation_ai_slop/>
- FORGE Lab 三个月回顾：<https://forge-blog.github.io/posts/linux-kernel-3-month-lookback/>
