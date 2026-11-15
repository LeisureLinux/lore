---
title: "OSINT 案例研究：12 起网络犯罪调查与公共记录核对"
date: 2026-11-15
slug: osint-case-studies-12-cybercrime-investigations
category: 技术/译文
author: FreeLAMP.com
original_source: "原文：OSINTsearch《OSINT Case Studies: 12 Cybercrime Investigations Checked Against the Public Record》，作者 Patrick Saif，2026-09-22，9 min read，https://osintsearch.org/blog/osint-case-studies 。网页版经 curl 直连取得（web_fetch 曾失败），正文段落、12 行案例表、FAQ 与伦理规则均按 HTML 原文逐段核对；页面用 Cloudflare 对邮箱做了反爬遮蔽，内嵌 JSON 里保留了两个 Gmail 与 3k@xakep.ru 的原文。原文为系列索引页：12 篇帖子中 6 篇跟单个案件/团伙（Scattered Spider、TeamPCP、KFC Watermelon、Galochkin、Joeleoli、LockBitSupp 等），6 篇是跨案例方法指南；方法为从起诉书/申诉/宣誓书/量刑备忘录/OFAC 条目/具名报道取公开标识符，2026 年 9 月用 OSINTsearch 的 email lookup（约 175 平台）与 username search（约 760 平台）跑一遍，按时间线给结果分级并与记录核对。本稿按用户要求『尽量翻译原文』处理：保留原文结构、所有小节、12 行表格、六条教训、七条伦理规则与四问 FAQ，仅把英文转写为中文；另按要求补一张 OSINT 术语中英对照参考表（术语释义为本工作区整理，非原文内容）。英文原文引用按发布规范控制在 1 处以内。"
original_date: 2026-09-22
original_url: "https://osintsearch.org/blog/osint-case-studies"
description: "按用户要求『尽量翻译原文』处理 OSINTsearch 的案例索引长文。原文是 Patrick Saif 2026-09-22 的《OSINT Case Studies: 12 Cybercrime Investigations Checked Against the Public Record》，用已起诉、定罪或受制裁网络犯罪案件里由法院文件、美国财政部制裁条目与具名调查报道印出的邮箱/别名做输入，2026 年 9 月跑 OSINTsearch 的邮箱查找（约 175 平台）与用户名搜索（约 760 平台），把每个输入、来源文件、搜索与返回结果都摊开。译文完整保留：读前声明（无罪推定、不揭露任何人、命名由检方/财政部/记者完成）、『这些案例研究是什么』、『用大白话讲方法』六步、12 行案例与技巧对照表、六条跨案例教训（日常邮箱才说话、生造句柄是指纹而词典词是伪装、邮箱锚点胜过句柄匹配、日期区分所有者与抢注者、记录做锚搜索做示意、知道哪类文件会印出标识符）、七条伦理规则、四问 FAQ 与『自己动手』。原文给出的具体数字全部保留：volhvb 11 个精确匹配、joeleoli 33 个、deadcatx3 21 个、Express 316 个、mango 439 个、nerowolfe 113 个；Fitzpatrick 个人 Gmail 返回 11 个注册、TeamPCP 案 24 个结果；Grubbs 30 个月、Evans 24 个月、Galochkin 2023-09-07 制裁、Khoroshev 2024-05-07 制裁、SDN 清单 23 个地址来自 10 项网络相关指定；Krebs 2018/2019 印出的两个只差一个字母的 Gmail 也按原文译出。另附一张术语参考表：OSINT、OPSEC、pivot、persona/burner address、presence data、display name、creation date、squatter、exact match、alias collision、email anchor、evidence ladder、indictment/complaint/affidavit/sentencing memo、OFAC/SDN、public record、attribution、zero result、named reporting 等，中文释义为本工作区整理。边界：这是译文，不是本工作区独立调查；未运行任何 OSINT 查找、未复核案件原始卷宗；原文对未定罪者明确无罪推定，译文原样保留。"
published: true
---

> 原文：OSINTsearch《OSINT Case Studies: 12 Cybercrime Investigations Checked Against the Public Record》，Patrick Saif，2026 年 9 月 22 日，约 9 分钟阅读。
> 本文按「尽量贴原文」译写：保留原有结构、表格、数字与伦理声明；文末术语表为另行整理，非原文内容。

这些 OSINT 案例研究，是从调查人员结束的地方开始的。案例里的每一个邮箱地址和别名，都先由法院文件、美国财政部制裁条目，或具名的调查报道印出来，涉及已被起诉、定罪或受网络犯罪相关制裁的人。2026 年 9 月，我们把这些标识符跑过 OSINTsearch 的邮箱查找与用户名搜索，然后写下返回的结果。这一页是整套系列的索引：每篇帖子讲什么、教什么方法，以及跨案例都成立的教训。

先读这段。 本系列点到的每个人，都已被公开起诉、定罪或制裁，每一句陈述都对照该记录来写。被起诉但未被定罪者推定无罪。本系列不揭露任何人。命名工作由检察官、财政部和记者完成；搜索只是展示他们公布的标识符今天还能返回什么。

## 这些 OSINT 案例研究是什么

每篇帖子拿已经公开的标识符，问两个问题：这个地址或别名，今天在仍在运营的平台上能走多远？这教会我们什么调查方法？其中六篇跟一个案件或一个团伙，从 Scattered Spider 到 TeamPCP；另六篇是借多个案例讲一种技巧的指南。合起来，它们就是「把每个输入都摆出来」的 OSINT 调查示例。

搜索结果是叠加在记录之上的「存在性」与档案数据。显示名或所在地是账号持有人自己填的，任何一项都不能替代记录。

## 用大白话讲方法

- 从一份印出标识符的文件开始：起诉书、刑事申诉、宣誓书、量刑备忘录、OFAC 条目，或具名新闻报道。那些在网上流传、却不见于任何一手来源的知名被告地址，不搜。
- 一个字母一个字母地抄。Krebs 在 2018 年印出的是 `nexuszeta1337@gmail.com`，2019 年对同一注册印出的是 `nexuczeta1337@gmail.com`。差一个字母，结果就变了。
- 把每个邮箱跑一遍邮箱查找。它检查约 175 个平台，报告找到的注册，以及平台公开的档案信息 —— 例如一个 GitHub 句柄、显示名与创建日期。
- 把每个别名跑一遍用户名搜索。它检查约 760 个平台。邮箱那一路返回的任何句柄，同样再跑一遍。
- 把每个日期放到案件时间线上：创建于别名存在之前、使用期间，还是姓名公开之后。
- 对照记录给每个结果分级，把与记录矛盾的结果和吻合的结果并排记下。

## 案例研究与指南

| 帖子 | 来自公共记录的案件 | 它教的方法 |
|---|---|---|
| 黑客是怎么被抓的 | RaidForums、REvil、AlphaBay、Scattered Spider 等案件的法院记录 | 九种反复出现的 OPSEC 失误，以及已公布的个人邮箱今天还能返回什么 |
| Scattered Spider 句柄地图 | 16 名被起诉者，来自美国起诉书与申诉、以及英国伦敦交通局起诉材料（Krebs） | 把一个团伙已公布的别名整体画图，把噪声、起诉后抢注者与符合记录的档案分开 |
| KFC Watermelon 与 LuminosityLink | Colton Grubbs，2018 年被判 30 个月 | 邮箱 → GitHub 显示名 → 带日期的句柄轨迹 |
| Galochkin 与 volhvb | Maksim Galochkin，2023 年 9 月 7 日受制裁，三份起诉书点名 | 一个生造句柄在四个邮箱间复用；以及为什么最老的账号常常最有用 |
| Joeleoli：用户名对邮箱 | Joel Martin Evans，2026 年 8 月 27 日被判 24 个月 | 当句柄里带着姓名，而邮箱什么也返回不了时 |
| 用邮箱找 GitHub 账号 | 七个公共记录地址，含 Grubbs、Benthall、Khoroshev 相关 | 提交归属，以及把显示名当作佐证来读 |
| 用 OSINT 做威胁行为者归属 | OFAC 的别名与地址，加上 TeamPCP、LockBit 的报道 | 分级证据梯：从别名撞车一路到有邮箱锚定的账号 |
| 一次性邮箱能追吗？ | Fitzpatrick、Coelho、Buchanan、Rudometov 案的宣誓书与申诉 | 人格化地址如何通过它们碰过的东西被追踪 |
| 记录里的 LockBitSupp | Dmitry Khoroshev，起诉书已解封，2024 年 5 月 7 日受制裁 | 以已公布邮箱为锚，给一个著名别名上的账号定年 |
| OFAC SDN 清单里的邮箱地址 | SDN 清单上 10 项网络相关指定中的 23 个地址 | 找到并检索制裁条目里的邮箱字段 |
| 怎么查一个账号的创建时间 | LockBitSupp 别名、TrickBot 制裁条目、Krebs 关联到 Daniel Kaye 的 spdr01 别名 | 把创建日期当证据读：案前、案中还是案后 |
| TeamPCP 逮捕 | Ruben Ian Thomson，2026 年 8 月在珀斯被捕，在加州被起诉 | 顺着记者的归属链走，再检验其中公布的地址与别名 |

Khoroshev、Thomson、Coelho 与 Rudometov 是被起诉而非定罪，推定无罪；本系列中其他未被定罪者同样如此。

## 六条跨案例成立的教训

下面每个例子都来自表中的某篇帖子。

### 1. 会说话的，是日常那个邮箱

人格化地址很少能识别到谁。Fitzpatrick 案的宣誓书描述了一个用于注册 RaidForums 的 Riseup 地址；邮箱查找没找到任何注册，与这一角色相符；而 Google 记录关联到他的个人 Gmail 返回了 11 个注册。TeamPCP 案里，记录关联到 BreachForums「Express」账号的那个地址查不到注册，与记录所述的「只用于论坛」相符；Krebs 关联到 Thomson 名下某个 Microsoft 账号的 Gmail 则返回 24 个结果。人格化地址反而是通过它们碰过的东西被追踪，一次性邮箱那篇帖子展示了这一点。

### 2. 生造句柄是指纹，词典词是伪装

`volhvb` 返回 11 个精确匹配、没有近似项。`joeleoli` 返回 33 个结果，全是精确匹配。`deadcatx3` 返回 21 个精确匹配，其中包括 Krebs 报道过的 HackerOne 档案。常见字符串表现完全不同：Krebs 关联到该团伙的 BreachForums 名字 `Express` 返回 316 个精确匹配，TrickBot 的别名 `mango` 返回 439 个。撞上一个常用词只是起点，从来不是答案。

### 3. 邮箱锚点胜过句柄匹配

`nerowolfe` 是一位虚构侦探的名字，返回 113 个精确匹配。其中只有一个 —— 经 `3k@xakep.ru` 抵达的 GitHub 账号 —— 有公共记录作锚，并带着 Krebs 关联到 Khoroshev 的 NeroWolfe 人格。Grubbs 也是同一模式：已公布的 Gmail 解析到一个显示「Colton Grubbs」的 GitHub 账号；Maksim Rudenskiy 的 OFAC 条目里那个地址，解析到显示「Max Rudensky」的 GitHub 账号。

### 4. 日期区分所有者与抢注者

创建日期是唯一一个持有人自己填不了的档案字段。在 `lockbitsupp` 这个别名上，一个无关玩家持有的 Steam 账号可追到 2004 年，比 LockBit 存在早了好几年（Steam 允许改个人主页 URL，所以句柄本身可能更新）。一个 Codeforces 账号出现在起诉书解封五天后，TikTok 与 Twitch 账号在 2025 年 12 月跟上，全都是可能的抢注者或冒充者。Joeleoli 案里，显示「Joel Evans」的 GitLab 档案可追到 2017 年 9 月，早于他承认的共谋期；同一句柄上的 MyAnimeList 账号创建于被捕约 21 个月后，同样按抢注处理。在 `volhvb` 这个句柄上，所有带日期的账号都没有创建于制裁指定之后。

### 5. 记录做锚，搜索做示意

`deadcatx3` 上的 HackerOne 档案显示「ruben thomson」，与 Krebs 报道的一字不差。`volhvb` 上的 Medium 档案显示的是制裁条目里姓名的西里尔字母拼法。两者之所以有意义，只因为公共记录事先已把句柄与姓名连上。好的来源会自己说明这一点。谈到自己对 LockBit 的还原，Krebs 写道：「Does the above timeline prove that NeroWolfe/Khoroshev is LockBitSupp? No.」在一个记录里根本没出现的句柄上，显示名匹配只是线索，不是结论。

### 6. 要知道哪类文件会印出标识符

Khoroshev 的起诉书一个邮箱地址都没印，IntelBroker 的申诉只写「西邮箱账号 1 号」，而 Khoroshev 的 OFAC 条目印了两个地址。Scattered Spider 案里，英国与欧洲当局公布了姓名、年龄、城镇与刑期，却没有别名、邮箱或句柄；可供检索的字符串来自美国文件与记者。我们的 SDN 邮箱指南讲了怎么在清单上找到它们。

## 本系列遵守的伦理规则

- 只用公共记录。 对象是被公开起诉、定罪或制裁的人。检索的每个标识符都先由法院、财政部或具名报道印出，每条陈述都链回该来源。
- 无罪推定。 被起诉意味着「被指控」。人格归属写成确立它的那一方，例如「Krebs 关联到他的 NeroWolfe 人格」。
- 不涉及未成年人与受害者。 两者都不被识别、不被描述。
- 不写未公布的句柄。 当查找冒出一个记录从未印过的句柄或显示名时，帖子只笼统描述，例如「某个显示名与受制裁姓名相符的档案」。共用同一句柄的无关人员，绝不点名。
- 零结果不是证明。 一次查找没找到注册，只说明这次查找找到了什么，不说明账号不存在。只有当记录本身这么描述时，才把一个邮箱称作人格化或一次性地址。
- 对后出现的账号加限定。 凡在逮捕、解封或指定之后创建的，一律当作可能的抢注者或冒充者。
- 有些已公布的细节不写。 电话号码、密码、护照与税务号码、亲属信息，即便来源印了也略去。

## 常见问题

什么是 OSINT 案例研究？
把开源调查做成一份「输入摆出来」的实作示例：标识符、印出它的文件、跑过的搜索、以及返回了什么。这里每个输入都是公共记录里的邮箱或别名，因此任何人都能查来源、重跑搜索。

这些案例里的标识符从哪来？
起诉书、刑事申诉、宣誓书、量刑备忘录、OFAC 制裁条目，以及 KrebsOnSecurity、BleepingComputer 这类具名报道。这些工作背后的记者与机构 —— 包括 Intel 471 与 OpenSanctions —— 值得拿走大部分功劳。

用户名或显示名匹配，能证明账号归谁吗？
不能。匹配只说明某个字符串被注册了，而显示名是自己填的。归属指南给每类证据分级，用户名核验清单给了做比对用的工作表。

我能自己重做这些调查吗？
能。从一手来源取一个标识符，先跑邮箱查找，再搜它返回的任何句柄，按创建日期排序，把与记录矛盾的结果和吻合的结果并排记下。

## 自己动手做一份案例研究

这套方法对任何线索都成立，也可以用在自己的数字足迹上。在 OSINTsearch 上对一个邮箱地址或用户名跑一次免费搜索，结果会显示平台与可得的档案细节（显示名、加入日期等），付费方案可导出 CSV、JSON 或 PDF。

## OSINT 术语参考表

> 下表为本工作区整理，用于读这篇译文与同系列文章；不是原文自带的表格。

| 英文术语 | 中文 | 在这篇文章里的意思 |
|---|---|---|
| OSINT / Open-Source Intelligence | 开源情报 | 从公开可得来源做情报搜集与分析；本文强调「公开」不等于「可随意下结论」 |
| Public record | 公共记录 | 法院文件、财政部条目、具名报道等可核对的一手来源；全文的「锚」 |
| Primary source | 一手来源 | 直接印出标识符的文件；网上流传但无一手来源的地址不搜 |
| Indictment | 起诉书 | 检方提出的正式指控；被起诉不等于定罪 |
| Complaint / Affidavit | 刑事申诉 / 宣誓书 | 案件早期文件，常印出别名、邮箱、注册信息 |
| Sentencing memo | 量刑备忘录 | 定罪量刑阶段文件，可作身份与时间的佐证 |
| Presumption of innocence | 无罪推定 | 原文反复声明：charged means alleged |
| OFAC | 美国财政部海外资产控制办公室 | 发布制裁指定的机构 |
| SDN List | 特别指定国民清单 | 制裁条目清单；文中「10 项网络相关指定里的 23 个邮箱」 |
| Designation | 制裁指定 | 把某人/实体列入清单的动作；「指定之后创建的账号」要加限定 |
| Sanctioned / charged / convicted | 受制裁 / 被起诉 / 已定罪 | 三种不同法律状态，译文严格区分 |
| Named reporting | 具名报道 | 有明确作者与出处的调查报道，如 KrebsOnSecurity |
| Identifier | 标识符 | 邮箱、别名、句柄等可检索的字符串 |
| Alias / handle / username | 别名 / 句柄 / 用户名 | 本文基本可互换，指账号上的公开名字 |
| Coined handle | 生造句柄 | 如 `volhvb`；低碰撞、像指纹 |
| Dictionary word / common string | 词典词 / 常见字符串 | 如 `Express`、`mango`；高碰撞，只作起点 |
| Alias collision | 别名撞车 | 不同人用了同一字符串；匹配本身不是归属 |
| Exact match / near miss | 精确匹配 / 近似项 | 搜索结果的两类命中；文中用数量说明噪声 |
| Pivot / username pivot | 转向检索 / 用户名转向 | 从一个标识符跳到另一个标识符继续查 |
| Email lookup / reverse email lookup | 邮箱查找 / 反向邮箱查找 | 用邮箱查平台注册与公开档案（约 175 平台） |
| Username search | 用户名搜索 | 用句柄查平台占用情况（约 760 平台） |
| Presence data | 存在性数据 | 「该字符串在某平台被注册」这类信号，不等于身份 |
| Display name | 显示名 | 账号持有人自填；只能作佐证，不能替代记录 |
| Profile / creation date / join date | 档案 / 创建日期 / 加入日期 | 创建日期是持有人填不了、可用于定年的字段 |
| Persona address / burner email | 人格化地址 / 一次性邮箱 | 为特定角色或论坛注册用的地址；常查不到注册 |
| Everyday mailbox | 日常邮箱 | 个人常用邮箱；原文发现它反而返回最多结果 |
| Email anchor | 邮箱锚点 | 由公共记录印出、能把账号锚定到记录的邮箱 |
| Evidence ladder / evidence grade | 证据梯 / 证据分级 | 从「字符串撞车」到「邮箱锚定 + 记录复现」逐级加权 |
| Threat actor attribution | 威胁行为者归属 | 把别名/账号归到具体人或团伙；文中强调不能靠一次匹配 |
| OPSEC | 行动安全 | 嫌疑人隐藏身份的操作习惯；九种 recurring mistakes |
| Squatter / impersonator | 抢注者 / 冒充者 | 姓名公开后新注册的同名账号；一律加 hedge |
| Hedge | 限定表述 | 对不确定结果写「可能」「一致的」而非断言 |
| Zero result | 零结果 | 查找没返回注册；只说明这次查找的范围，不是「不存在」 |
| Corroboration / contradiction | 佐证 / 矛盾 | 与记录吻合或冲突的结果，要并排记录 |
| Case timeline | 案件时间线 | 把别名使用期、逮捕、解封、指定与账号创建日排到一起 |
| Commit attribution | 提交归属 | 由邮箱与 GitHub 提交/显示名推断代码作者 |
| Unmask / doxxing | 揭露 / 人肉 | 原文明确「本系列不揭露任何人」 |
| No minors / no victims | 不涉及未成年人 / 受害者 | 伦理规则之一 |
| CSV / JSON / PDF export | 结构化导出 | 付费方案把结果导出，便于留痕与复核 |

## 译注与边界

- 这是一篇译文，主体结构与全部数字均依原文；术语表是本工作区补的，不是原文内容。
- 原文页面对邮箱做了 Cloudflare 反爬遮蔽，两个 Krebs 印出的 Gmail 与 `3k@xakep.ru` 依据页面内嵌数据还原；译文照抄，未做任何搜索或验证。
- 本工作区未运行任何 OSINT 查找、未复核案件卷宗、未独立验证原文中的匹配数量与日期；这些是 OSINTsearch 2026 年 9 月自述的搜索结果。
- 原文对未定罪者的无罪推定、不点名无关同名人、略去电话/密码/证件号等规则，译文原样保留；相应人名与案件名只作为公共记录中的转述出现。
- 原文作者 Patrick Saif 是 OSINTsearch 的构建者，文中「约 175/760 平台」「免费搜索 / 付费导出」属产品自述，不构成本工作区对工具的推荐或测评。
- 英文原文引用仅保留 Krebs 那一句；其余引语均转为中文转述。

## Sources

- 原文：Patrick Saif《OSINT Case Studies: 12 Cybercrime Investigations Checked Against the Public Record》，OSINTsearch，2026-09-22：<https://osintsearch.org/blog/osint-case-studies>
- 系列索引与分类页：<https://osintsearch.org/blog> ｜ <https://osintsearch.org/blog/tag/osint%20case%20studies>
- 原文提到的具名来源（仅列出处，本文未逐篇复核）：KrebsOnSecurity <https://krebsonsecurity.com/> ｜ BleepingComputer <https://www.bleepingcomputer.com/> ｜ OpenSanctions <https://www.opensanctions.org/> ｜ OFAC SDN 清单 <https://ofac.treasury.gov/specially-designated-nationals-and-blocked-persons-list-sdn-human-readable-lists>
