---
title: "Microsoft 365 丢掉几个 9：SLA 的合同算术与架构师的账本"
date: 2026-11-14
slug: microsoft-365-sla-three-nines-ops-architect
category: 技术/解读
author: FreeLAMP.com
original_source: "一手核对：Reddit r/sysadmin 帖《Microsoft just passed the mark for losing \"three 9s\" so far on their availability for the entire year》（帖 ID 1xuw2tg，2026-11-13 前后，104 points / 12 children；正文用年度 downtime 表算 99.999%=5.25 分、99.99%=52.5 分、99.9%=8.76 小时，称从本 subreddit 报告故障的约 12:45 ET 到次日 9:30 ET 已跨过第三个 9、来到 99.8% 且还在下降；评论区含「除非再来 87.6 小时否则不会再掉一个 9」「1% 折扣」「Bet you they try weasel out of credits by claiming it was a disruption not downtime」「M365 宕机没有 BC/DR 预案」「15–20 小时后交接去睡觉」等技术与组织讨论；Reddit 直连 403，正文与评论经本机登录态 Chrome/bsk 取得）＋ Microsoft《Service Level Agreement for Microsoft Online Services》October 1, 2026 英文版 docx 原文（从 microsoft.com/licensing 下载并解开：General Terms 的 Applicable Period 定义、Incident、User Minutes、Claims 条款、45 天处理、非 Azure 服务索赔截止为事故月次月月底、Service Credits 为 sole and exclusive remedy、仅适用于未达标服务的费用、Limitations 排除项、以及「Microsoft outage communications ... are not a confirmation of missed Service Levels or Service Credits eligibility」；Exchange Online 章：Downtime 定义为「users are unable to send or receive email with Outlook Web Access」，Uptime Percentage = (User Minutes − Downtime) / User Minutes × 100，Downtime 按 user-minutes 计算，三档 credit <99.9%→25%、<99%→50%、<95%→100%，无 Scheduled Downtime，另列 OWA 例外场景）＋ Microsoft Licensing Documents SLA 下载页（当前版 2026-10-01，覆盖 Azure / Dynamics 365 / Office 365 / Intune）＋ The Register《Microsoft's massive M365 outage stretches past 18 hours as its fixes keep failing》（Simon Sharwood，2026-11-13；故障约 11-12 18:00 UTC 起、影响 Exchange Online 及依赖它的十余项服务、微软称服务器自动健康检查失败、后续 12:00/13:00 UTC 更新与恢复进展、措辞从「no indication of malicious activity」到「not aware of any malicious activity」）＋ TechCrunch《Microsoft's latest email outage turned into a full-blown global cloud crisis》（Zack Whittaker，2026-11-13；Kentik 的 Doug Madory 称约 18 小时流量才回来、微软称与 cyber / AI agents 无关、Charles Lamanna 表态复盘）＋ 事故编号 EX1550543 / MO1550821 与 12-31 索赔截止的媒体核对（Cybernews、CTOL、Pasquale Pillitteri 等二手报道，本文仅用于交叉验证，合同口径以 docx 为准）"
original_date: 2026-11-13
original_url: "https://www.reddit.com/r/sysadmin/comments/1xuw2tg/microsoft_just_passed_the_mark_for_losing_three/"
description: "从运维与架构师视角拆 r/sysadmin 那句「微软今年丢掉三个 9」。帖子按年度 downtime 表算：一次从约 12:45 ET 到次日 9:30 ET 的故障就跨过 8.76 小时，把年度可用率压到 99.8%。核对微软 2026-10-01 版 Online Services SLA 后发现，真正该算的不是年度而是月度：Exchange Online 的 Uptime Percentage =（User Minutes − Downtime）/ User Minutes × 100，Downtime 按「受影响用户数 × 时长」的 user-minutes 计，且只定义为无法通过 Outlook Web Access 收发邮件；11 月 43200 分钟对应 43.2 分钟阈值，三档 credit 为 <99.9% 抵扣 25%、<99% 50%、<95% 100%，只作用于该服务的月费、绝不现金赔付，合同明写 Service Credits 是 sole and exclusive remedy，且「微软的故障通报不等于确认未达标或具备索赔资格」。文章给出几组运维可自己套的算术：全员 8 小时约 98.89% → 50%，100 人里 10 人断 3 小时只有 99.96% → 无 credit，说明「故障持续多久」与「多少用户受影响」同等重要。也列出索赔动作（12-31 前主动提交、附时间与时长/受影响用户数/资源名/位置、45 天处理、个人与家庭版不适用、套件里只按受影响服务计费）。架构部分把 SLA 与业务连续性分开：SLA 是订阅费的折扣规则，不是营业中断险；单一身份/邮件平面、管理面与数据面同故障域、故障期间状态页与工单也可能依赖同一套服务，才是需要预先设计的部分。给出可执行的清单：独立监视与证据留存、带外通信与权威 DNS/身份旁路、邮件连续性（次级 MX / 归档 / 队列）、降级模式与演练、把 credit 索赔写进事故复盘流程。结论：几个 9 是供应商账单上的数字，架构师该守的是恢复时间与业务损失，两者别混为一本账。"
published: true
---

11 月 13 日前后，r/sysadmin 出现一个标题很会算账的帖子：「微软今年丢掉三个 9」。作者拿年度停机时间表当尺子：99.999% 一年只能停 5.25 分钟，99.99% 是 52.5 分钟，99.9% 是 8.76 小时；按本版报告故障的约 12:45 ET 到次日 9:30 ET，这一趟就跨过了 8.76 小时，于是「现在 99.8%，还在往下掉，还没算今年其他停机」。

帖子底下 100 多分、十几条主回复，情绪很足，但技术含量也高：有人接「除非再来 87.6 小时，不然不会再掉一个 9」，有人问「就算全年 99%，你拿那 1% 折扣干什么」，有人预言微软会把 outage 说成 disruption 来躲 credit，还有做过 BC/DR 的人写「我们把 ERP 的台风演练做了无数次，从没演练过邮件没了 —— 因为它最早被搬上云，大家默认它不会挂」。

这篇值得从运维和架构师两个视角写。因为把微软 2026-10-01 版 SLA 原文翻出来之后，会发现帖子的算术没错，但量的不是合同上那把尺。

## 一、帖子的尺子：年度，全局，简单除法

原帖的算法干净利落：一年 8760 小时，99.9% 对应 8.76 小时，一次近 21 小时的事故直接把年度可用率打到 99.8% 附近。这个表在容量规划、对外宣传、年度复盘里都常用，评论区那句「87.6 小时才会再掉一个 9」也是同一套线性换算。

它回答的问题是：作为观察者的我们，今年整体看到了多少不可用时间。这没问题。

但它不是微软合同里的度量。

## 二、合同的尺子：月度、按用户分钟、按服务

我把微软官方《Service Level Agreement for Microsoft Online Services》2026 年 10 月 1 日版的 docx 下下来解开了。Exchange Online 那一段写得很具体：

- Downtime 定义为用户无法通过 Outlook Web Access 收发邮件的时段，且该服务没有 Scheduled Downtime；
- Uptime Percentage = `(User Minutes − Downtime) / User Minutes × 100`；
- Downtime 以 user-minutes 计：每次事故的分钟数 × 受影响用户数；
- Applicable Period 对 M365 这类服务是「事故所在自然月」，不是全年；
- 三档 credit：低于 99.9% 抵扣 25%、低于 99% 50%、低于 95% 100%；
- Service Credit 只作用于未达标的那个服务的月费，不是整个套件；合同原话「Service Credits are your sole and exclusive remedy」把救济限定在抵扣，且客户不得自行抵扣账单。

11 月有 30 天 = 43,200 分钟。0.1% 就是 43.2 分钟 —— 网上流传的「44 分钟」只在「全公司每一个用户全月都断」的前提下成立。把 user-minutes 代进去，会得到几组对运维更实用的结果：

| 场景（100 用户 / 11 月） | 丢失 user-minutes | 月度可用率 | credit |
|---|---|---|---|
| 全员断 1 小时 | 6,000 | 99.86% | 25% |
| 全员断 8 小时 | 48,000 | 98.89% | 50% |
| 10 人断 3 小时 | 1,800 | 99.96% | 无 |

结论一：故障时长只是分子的一半，另一半是「多少用户被算作受影响」。 合同里「受影响用户」的举证责任在客户：索赔材料要含事故描述、起止时间与时长、受影响资源名、用户数与位置、错误截图等。帖子评论区那句「他们会说是 disruption 不是 downtime」，在合同层面有更精确的对应：微软还专门写了「outage communications 只是让客户采取预防措施，并不构成对未达标或索赔资格的确认」，以及「性能降级但服务未真正不可用」不计入。状态页写 `Service degradation` 和合同里算不算 Downtime，是两件事。

结论二：月度窗口会重置。 年度 8.76 小时是观察指标；合同是每月 43.2 分钟起算，一年重置 12 次。一次 21 小时的事故在 11 月肯定越线，但它不会像帖子说的那样「记账到全年」。

## 三、索赔是一套运维流程，不是自动到账

合同把动作写得很死，值得直接抄进 runbook：

- 不会自动给：客户必须向支持提交 claim，附全部验证材料；微软通常在收到后 45 天内处理；
- 非 Azure 服务的截止：事故月次月月底前送达 —— 11 月 12 日的事故对应 2026-12-31；Azure 是事故后 60 天（不同口径）；
- 只赔受影响服务：套件里只有邮件挂了，就只按邮件那一块的费用折算，不是整张 M365 发票打五折；
- 不是现金：抵扣后续账单，且不超过该服务当月费用；个人/家庭版不适用，部分批量许可改为补服务时长；
- 排除项：客户侧网络、第三方软件、未付许可、预览版、计划维护、以及「仅降级但未真正不可用」等；合同也写明不覆盖营收损失、运营成本与间接损失。

于是那条「微软欠你钱」的帖子，准确版本应该是：按合同，你可能有权申请一张折扣券，得自己写材料、按期提交、按受影响服务计算，而且它跟业务损失无关。评论区那个反问「1% 折扣你打算干嘛」虽然刻薄，但确实点到了 SLA 的本质。

顺带一个口径提醒：事故编号 EX1550543 / MO1550821、12-31 截止、25%/50% 这些在多家媒体上都有转述，本文以微软 docx 原文为准；媒体给的具体时长与「是否算 downtime」只是推断，最终以微软对索赔的认定为准。

## 四、这次事故暴露的是故障域，不是百分比

按 The Register 与 TechCrunch 的报道：故障约 11 月 12 日 18:00 UTC 起，最初是「服务器自动健康检查失败而不可用」，随后扩散到 Exchange Online 以及依赖邮件/身份的十余项服务 —— Teams、Copilot、Defender、Intune、Planner、Purview、Fabric、部分 Windows 365 Cloud PC 与管理工具；微软一度说修复动作「未带来预期缓解」，到 13 日 12:00/13:00 UTC 才报告持续恢复；Kentik 的 Doug Madory 观察到约 18 小时后流量才回来。微软称与网络攻击、AI/agents 无关，Charles Lamanna 表示在复盘。

对架构师来说，比「掉了几个 9」更该记的是三件事：

1. 单点不在虚拟机，在控制平面与身份。 一个后端健康检查/容量变更，能让邮件、会议、AI 助手、终端管理、安全门户同时不可用。买多少个 9 都改变不了「它们共享同一个故障域」这个事实。
2. 管理面也一起进去了。 状态页、Service Health、Intune 管理台、工单系统若都建在同一租户同一身份体系上，故障时你连「看清楚发生了什么、通知谁、从哪儿改配置」都要绕路。带外通信、独立状态页订阅、离线联系人清单不是形式主义。
3. 邮件是业务流，不是工具。 评论区那位前 BC/DR 负责人说得最实在：ERP 的台风演练做了一轮又一轮，唯独没演练过邮件消失，因为它最早迁上云、被默认成「不会挂的基础设施」。而邮件往往连着订单确认、密码重置、审批链与告警通道。

## 五、架构师该记在另一本账上

SLA 定价的是订阅费，业务连续性要定价的是停摆损失，两者不能互相替代。合同自己就把这条划清了：credit 是唯一救济，且不覆盖营收与运营成本。可操作的清单大致是：

- 独立观测与证据：从供应商体系之外做拨测，记录起止时间、受影响用户/租户、失败的具体操作（OWA 收发信），保存状态页历史与截图 —— 这既是故障判断依据，也是索赔材料；
- 带外通信与旁路：应急联系人、会议桥、工单与公告渠道不依赖同一身份/邮件平面；权威 DNS、IdP、管理员账号的紧急访问路径预先演练；
- 邮件连续性：次级 MX 或邮件网关排队、历史邮件归档可检索、关键通知多通道（短信/IM）；想清楚恢复后积压邮件如何对账；
- 降级模式：哪些业务可以在「无邮件、无 Copilot、无 Teams」下继续，哪些必须先停；把答案写成开关而不是事故当晚讨论；
- 演练要包含 SaaS：把「M365 全断 8 小时」放进年度 DR 场景，验证的是本公司能不能继续运转，而不是能不能修微软；
- 把索赔写进复盘模板：事故编号、证据包、责任人、12-31 这类截止日自动进待办，别让几十到几百美元的 credit 因为没人提交而过期 —— 它的价值不在钱，在让 SLA 变成有反馈的治理信号。

## 六、边界

- 本文的合同条款来自微软 2026-10-01 版 SLA 英文 docx 原文；事故时间线、受影响服务与「约 18 小时」来自 The Register / TechCrunch 等媒体转述，微软最终根因与官方认定的 downtime 尚未公布。
- Reddit 直连 403，帖子正文与评论经本机登录态 Chrome 取得；帖子分数、时间与部分评论为抓取时点状态。
- 三组 user-minutes 示例是按合同公式自行换算的示意，不代表任何真实租户的认定结果；「受影响用户数」的口径由微软在索赔时判断。
- 12-31 截止、EX1550543 / MO1550821 等编号在多家二手报道中出现，本文以合同通用条款（次月月底）为准，具体事件分类以微软为准。
- 本文未提交任何索赔、未复现故障，也未做微软与其他云厂商 SLA 的横向测评。

## 七、结论

「丢掉三个 9」是一句漂亮的观察，但它是年度、全局、观察者视角的账。合同上真正在跑的是月度、按服务、按用户分钟的账：11 月 43.2 分钟起算，25%/50%/100% 三档，只抵该服务月费，还得自己在 12 月 31 日前把材料交上去。

对运维，落点是证据与流程；对架构师，落点是故障域与恢复能力。几个 9 写在供应商账单上，RTO 与停摆损失写在自己的账本上 —— 把这两本账分开，才是这次事故最该留下的东西。

## Sources

- Reddit r/sysadmin 原帖（帖 ID 1xuw2tg）：<https://www.reddit.com/r/sysadmin/comments/1xuw2tg/microsoft_just_passed_the_mark_for_losing_three/>
- Microsoft《Service Level Agreement for Microsoft Online Services》October 1, 2026（官方下载页与 docx）：<https://www.microsoft.com/licensing/docs/view/Service-Level-Agreements-SLA-for-Online-Services>
- The Register《Microsoft's massive M365 outage stretches past 18 hours as its fixes keep failing》：<https://www.theregister.com/saas/2026/11/13/microsofts-massive-m365-outage-stretches-past-18-hours-as-its-fixes-keep-failing/5309609>
- TechCrunch《Microsoft's latest email outage turned into a full-blown global cloud crisis》：<https://techcrunch.com/2026/11/13/microsoft-latest-email-outage-turned-into-a-full-blown-global-cloud-crisis/>
- 索赔口径交叉验证：Cybernews <https://cybernews.com/news/microsoft-outage-customer-compensation/> ｜ CTOL <https://www.ctol.digital/news/microsoft-365-outage-100-percent-service-credit-cap/> ｜ 索赔指南 <https://pasqualepillitteri.it/en/news/32826/microsoft-365-outage-sla-credit-how-to-claim>
- Microsoft 状态页：<https://status.cloud.microsoft/>
