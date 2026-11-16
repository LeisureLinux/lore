---
title: "FAA 全国停飞：两台 Juniper 路由器，压垮了几十年的铜线网络"
date: 2026-11-16
slug: faa-ground-stop-juniper-routers-copper-tdm-network
category: 技术/解读
author: FreeLAMP.com
original_source: "一手核对：Tom's Hardware《Two HPE Juniper network routers grounded all US flights on Friday — FAA's decades-old copper network buckled under a feature HPE says 'worked as intended,' creaking air traffic communication system became overloaded by 'very high rate' pinging》（Jowi Morales，2026-11-15；curl 直连取得全文，web_fetch 只返回摘要；正文要点：据 WSJ，新装的 HPE/Juniper 路由器向大范围网络广播，压垮老旧系统；TCAS 等机载安全系统不受影响；最先在 Indianapolis Center 出现通话问题；FAA 追到 El Dorado, Arkansas 无线电站点与 Amarillo, Texas 雷达站点；FAA 技术主管 Rebecca Guy 记者会原话『a thousand connections over every four to five seconds』；FAA 仍用几十年历史的铜线网络，正花数十亿美元升级光纤；约四小时恢复；旅客恢复需数小时到一两天；并引 2024 CrowdStrike 事件作恢复时长对照）＋ FAA 官方《Nationwide Ground Stop: Questions and Answers》（2026-11-15；11-13 约 15:30 ET 技术故障、出于谨慎发布全国地面停飞、20:15 恢复；官方定性：legacy equipment 在 FTI 网络被『1,000 connection attempts every 4 to 5 seconds』数据洪泛时失稳，扰动航空通信与雷达馈送；初步调查指向 Amarillo radar site 与 El Dorado radio site；L3Harris 为 FAA 当前网络服务商，事发时在 El Dorado 施工含部署新路由器；屏蔽两处后网络稳定；作为预防在所有新路由器上禁用 broadcasting function；17/22 个 ARTCC 受影响并扩散到多个 TRACON；约 3500 架空中飞机安全落地；约 12462 班取消，其中主要航司 9082 班；明确『No, this is due to the legacy TDM system causing instabilities』、升级改造的塔台没倒、铜线因淘汰正在被断开；远程站点例行更换白天做了几十年、今后要重评估维护窗口；作为预防在约 60 台同类路由器上禁用该功能）＋ The Conversation《How did 'wire replacements' ground planes across the entire US?》（2026-11-14；铜线→光纤、TDM→IP 的技术澄清：物理介质与传输组织方式不是一回事，铜也能跑数字、TDM 也是数字；TDM 固定时隙单通道、IP 分组多路径；故障路由器若不及时隔离会沿网络影响其他设备；正确配置与网络分段能限制故障域；根因仍待查：安装错误、配置错误、设备缺陷皆可能；并澄清与 Microsoft / AI / SMART 无关的传言）＋ NBC News《How a router problem at one FAA site led to a nationwide ground stop》（17/22 中心）＋ WSJ《The Single Router in Southern Arkansas That Ground Air Travel to a Halt》归档摘录（Rebecca Guy 原话、L3Harris 安装新 Juniper 路由器后开始高频发数据、Arkansas 与 Texas 两处数据压垮系统；Indianapolis 先出现静电与通话不清）＋ Hardware Busters 汇总（HPE 发言人『they did not fail』、routers working as designed；FAA 在约 60 台 Juniper 路由器上关掉 broadcasting feature；L3Harris 协助调查；Duffy 称无蓄意或恶意迹象；Bedford 自问是安装、配置还是设备技术问题；引 Tom's 约四小时恢复）＋ 搜索交叉：交通部长 Sean Duffy 在 ABC This Week 说禁用 69 台该型号路由器的数据广播；Reuters 报道 Duffy 把升级称为 analog→digital；WebProNews 给出 15:54 ET 停飞令、20:19 ET 解除；2023-01 NOTAM 系统故障也曾全国停飞（The Conversation 引用 GAO）"
original_date: 2026-11-15
original_url: "https://www.tomshardware.com/networking/two-hpe-juniper-network-routers-grounded-all-the-us-flights-on-friday-faas-decades-old-copper-network-buckled-under-a-feature-hpe-says-worked-as-intended-creaking-air-traffic-communication-system-became-overloaded-by-very-high-rate-pinging"
description: "解读 Tom's Hardware 那条「两台 HPE/Juniper 路由器让全美航班停飞」。文章以 FAA 官方 Q&A 为主证据，把媒体标题与官方口径分开：FAA 说的是『两处潜在位置』（El Dorado, Arkansas 无线电站点与 Amarillo, Texas 雷达站点），其中 L3Harris 正在 El Dorado 做例行更换并部署新路由器；官方定性是 legacy TDM / FTI 网络被每 4–5 秒 1000 次连接尝试的数据洪泛冲得失稳，不是现代化升级本身把塔台弄垮。时间线与数字全部按 FAA：11-13 约 15:30 ET 故障、全国地面停飞、20:15 恢复；17/22 个 ARTCC 受影响并扩散到多个 TRACON；约 3500 架空中飞机安全落地；约 12462 班取消（主要航司 9082 班）；屏蔽两处后网络稳定，并在约 60 台同类路由器上禁用 broadcasting function（交通部长 Duffy 在 ABC 说 69 台，口径差异按出处标注）。技术侧用 The Conversation 澄清铜线/光纤与 TDM/IP 是两件事：TDM 固定时隙、IP 分组多路径；新设备按设计持续发探测/广播，在旧 TDM 链路上就变成放大后的连接洪泛，故障域因为没有分段而扩散到全国。也写清厂商与官方的分歧：HPE 称设备『did not fail』、按设计工作；FAA 与 L3Harris 仍在查根因（安装、配置、设备缺陷皆可能），Duffy 称无蓄意或恶意迹象，Bedford 自问是安装、配置还是设备故障；与 Microsoft、AI、SMART、网络攻击无关。边界：本文未接触 FAA 设备、未验证路由器型号与功能名（官方只写 broadcasting function），Tom's 标题里的『worked as intended』来自 HPE 口径；60/69 台与 15:30/15:54、20:15/20:19 的时间差按各自出处标注。结论：这不是『两台路由器击落全国航班』的猎奇故事，而是一次新旧协议交界处的故障域失控 —— 设备没坏，边界没画好。"
published: true
---

11 月 15 日 Tom's Hardware 的标题很长，也很会抓眼球：「两台 HPE Juniper 路由器让全美航班周五停飞 —— FAA 几十年历史的铜线网络，被一个 HPE 称『按设计工作』的功能压垮」。

把 FAA 官方问答、Tom's 正文、WSJ 原始报道与 The Conversation 的技术解释摆在一起看，结论比标题克制，也更有价值：设备大概率没坏，坏的是新旧协议交界处没有画好的故障域边界。

## 一、先把口径拆开：两处位置，不是「两台 confirmed 故障设备」

Tom's 标题写「two routers」，WSJ 的独家标题甚至写「阿肯色州南部的那一台路由器」。FAA 官方 Q&A 的措辞要谨慎得多：

> 初步调查指出两处潜在位置是数据洪泛来源：得州 Amarillo 的雷达站点，与阿肯色州 El Dorado 的无线电通信站点；L3Harris（FAA 当前网络服务商）当时正在 El Dorado 施工，其中包括部署一台新路由器。

也就是说：官方确认的是两个站点的异常流量、其中一处有新装设备；并没有说「两台路由器都确认故障」。Indianapolis Center 最先出现飞行员与管制员通话不清、无线电杂音，随后排查才追到这两处。屏蔽两处后网络稳定。

顺带一个容易混的背景：这轮工作的性质是把老化的铜线电信链路换成光纤、把 TDM 逐步迁到 IP，FAA 明确答「不是升级改造导致了这次事故」「拿到改造的塔台没有倒」，问题出在 legacy TDM 系统在异常数据下失稳。

## 二、1000 次连接 / 4–5 秒，为什么能压垮一张国家网

FAA 官方与记者会给的是同一个数字：

- FTI 网络被以每 4 到 5 秒 1000 次连接尝试的速率灌入数据；
- FAA 技术主管 Rebecca Guy 的说法被多家媒体逐字引用：「We saw two places that were actually pinging our network at a very high rate, a thousand connections over every four to five seconds.」
- 结果是地空通信与部分雷达馈送失稳；17 个 / 共 22 个航路交通管制中心（ARTCC）受影响，并扩散到若干终端雷达进近管制（TRACON）。

按现代 IP 网络的尺度，每秒几百次连接根本不算什么 —— Tom's 也拿大型 DDoS 的流量做过对照。真正的反差在 The Conversation 讲清楚的那层：铜线/光纤是物理介质，TDM/IP 是信息组织方式，两者不是一回事。铜线照样能跑数字信号，TDM 本身也是数字制式；这场迁移里变化最大的是：

| | TDM | IP |
|---|---|---|
| 传送方式 | 单通道、固定时隙，像按点放行单车道桥 | 分组、可走多路径，弹性与容量都高 |
| 故障行为 | 链路窄、设备按既定节奏工作 | 一台设备若持续发探测/广播，包会沿网络自由扩散 |
| 对隔离的要求 | 相对局部 | 必须靠分段、限速、配置把故障域圈住 |

于是一个在 IP 世界里「正常」的 broadcasting / keepalive 类功能，落到几十年历史、正在被淘汰的 TDM 铜线链路上，就成了放大后的连接洪泛。FAA 的处置也正是按这个逻辑：切断两处 → 网络稳定 → 在所有新路由器上禁用该 broadcasting function，并作为预防在约 60 台同类路由器上关掉同一功能。

这里有个必须按出处标注的口径差：FAA Q&A 写「approximately 60 similar routers」，交通部长 Sean Duffy 周日在 ABC《This Week》说的是 69 台该型号路由器。两者可能统计范围不同，本文不替官方统一。

## 三、时间线与影响面（以 FAA 官方为准）

| 时间（ET，2026-11-13） | 事件 |
|---|---|
| 约 15:30 | FAA 出现技术故障；官方称出于谨慎发布全国地面停飞 |
| 约 15:54 | 媒体记录的停飞令下达（WebProNews 口径，与官方「约 15:30」略有差异） |
| 期间 | 17/22 个 ARTCC 失稳；约 3,500 架空中飞机全部安全落地 |
| 20:15 | FAA：系统稳定、空中交通恢复（媒体记 20:19 解除） |
| 周末 | 约 12,462 班取消，其中主要航司 9,082 班；FAA 特别声明「并非全部由停飞直接造成」 |

FAA 反复强调两点：部分无线电频率与雷达馈送始终可用，管制员能维持通信与跟踪；TCAS 这类主要依靠机载应答机相互通信的安全系统不受影响。Tom's 也写明，问题的核心是无法同时协调数千架在空中飞行的飞机，所以只能先不让新飞机起飞；并非飞机本身失去安全保障。

恢复不止四小时：Tom's 说旅客从几小时到一两天才续上行程，并拿 2024 年 CrowdStrike 事件作对照 —— 网络恢复得快，航班与乘客的「排空」要慢得多。

## 四、厂商说「没坏」，官方说「还在查」

这是整起事件最值得玩味的一层，也是 Tom's 标题里 `'worked as intended'` 的出处：

- HPE（已收购 Juniper Networks）：发言人表示设备按设计工作、「没有发生故障」；
- FAA / L3Harris：仍在联合调查根因。FAA 只说屏蔽两处、关掉功能后稳定；L3Harris 协助调查；
- 交通部长 Duffy：没有蓄意或恶意行为的迹象；
- FAA 局长 Bryan Bedford 在记者会上自己把三种可能摆出来：安装错误？配置错误？还是「放进系统的设备技术本身有问题把错误传播出去」？—— 没人给出答案；
- The Conversation 补了一句冷静的：安装、配置、设备缺陷都还是候选，也顺手否掉了「与 Microsoft / AI / SMART 交通管理系统有关」的传言。

换句话说，「设备按设计工作」与「系统被压垮」可以同时成立：一个功能在它的协议语境里完全合规，放进另一个带宽、时序与故障隔离假设都不同的老网络里，就成了放大器。这属于集成测试该回答的问题，不能简单当成厂商甩锅。

FAA 自己也在 Q&A 里承认了流程层面的教训：远程站点的例行更换几十年来都在白天做、从没出过事，但「基于周五发生的情况，我们会重新评估维护窗口」。The Conversation 给的工程答案更直接：网络分段（segmentation）+ 配置限速，让一台路由器的错误传不了那么远。

## 五、边界

- 本文以 FAA 官方 Q&A 为时间线、数字与根因定性的主证据；Tom's Hardware / WSJ / NBC / The Conversation / Hardware Busters 用于补充厂商口径、现场细节与技术解释。
- 未接触 FAA 设备、未验证路由器具体型号与功能名：FAA 只写 `broadcasting function`，媒体写 pinging / 高频连接，本文不替它命名成某个具体协议特性。
- 60 台（FAA）与 69 台（Duffy）、15:30/15:54、20:15/20:19 的差异按各自出处标注，不强行统一。
- Tom's 标题的「two routers」与 WSJ 标题的「single router」是媒体简化；FAA 原文为「两处潜在位置」。
- 「约 12,462 班取消」为 FAA 官方数字，且官方声明并非全部由停飞直接造成；本文不把它换算成受影响旅客数。
- 根因（安装 / 配置 / 设备）尚未公布；本文不判定责任，也不把 HPE 的「按设计工作」当作最终结论。
- 未使用 Tom's 评论区观点；与 Microsoft、AI、网络攻击无关的澄清按 The Conversation 与 Duffy 口径标注。

## 六、结论

把标题翻译成工程语言，这件事是：一台按设计不断发探测/广播的新路由器，接进一张按固定时隙、窄链路、缺少分段的老 TDM 铜线网；流量没有被圈在局部，于是 17 个管制中心同时失稳，FAA 只能让全国航班先别起飞。

它不是「两台小路由器击落了全美航空」的猎奇故事，也不是「铜线该背锅」那么简单。设备没有坏，功能按设计跑，现代化工程本身也没被官方认定为原因 —— 真正缺的是新旧协议交界处的故障域边界：限速、隔离、分段、维护窗口与上线前的集成验证。FAA 关掉 60（或 69）台设备上的同一个功能，本质上是先用手把边界补上，再回头查为什么当初没画。

## Sources

- Tom's Hardware（Jowi Morales，2026-11-15）：<https://www.tomshardware.com/networking/two-hpe-juniper-network-routers-grounded-all-the-us-flights-on-friday-faas-decades-old-copper-network-buckled-under-a-feature-hpe-says-worked-as-intended-creaking-air-traffic-communication-system-became-overloaded-by-very-high-rate-pinging>
- FAA《Nationwide Ground Stop: Questions and Answers》（2026-11-15）：<https://www.faa.gov/newsroom/nationwide-ground-stop-questions-and-answers> ｜ NAS Status：<https://nasstatus.faa.gov/>
- WSJ 独家归档：<https://archive.ph/sVlpZ> ｜ NBC News：<https://www.nbcnews.com/news/us-news/router-problem-one-faa-site-led-nationwide-ground-stop-rcna609325>
- The Conversation《How did 'wire replacements' ground planes across the entire US?》（2026-11-14）：<https://theconversation.com/how-did-wire-replacements-ground-planes-across-the-entire-us-296658>
- Hardware Busters 汇总（HPE / L3Harris / Bedford 口径）：<https://hwbusters.com/news/faa-ground-stop-traced-to-two-new-juniper-routers-flooding-a-decades-old-network/>
- Reuters（Duffy 关于升级的报道，经 The Conversation 引用）：<https://www.reuters.com/business/aerospace-defense/us-aviation-shutdown-blamed-l3-harris-installed-router-2026-11-14/> ｜ WebProNews 时间线：<https://www.webpronews.com/faa-nationwide-ground-stop-air-traffic-control-communications-outage/>
