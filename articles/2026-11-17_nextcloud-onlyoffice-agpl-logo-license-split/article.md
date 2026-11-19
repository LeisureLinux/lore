---
title: "Nextcloud 与 ONLYOFFICE 分手：多数自托管者没读过的那条许可证"
date: 2026-11-17
slug: nextcloud-onlyoffice-agpl-logo-license-split
category: 技术/解读
author: FreeLAMP.com
original_source: "原文：Nextcloud 与 ONLYOFFICE 的许可证争议，由读者提供正文解读角度——AGPL 的规则（修改自托管 app 并让团队通过网络使用，须向这些用户提供修改后源码；只运行未修改的 AGPL app 供他人网络使用不触发源码提供要求，只有修改后供他人使用或分发副本才会）；DocuSeal 附加条款要求交互界面保留原始 DocuSeal 署名（较礼貌的额外规则）；争议在 ONLYOFFICE 两句话：分发须保留原始 logo、同时不授予商标权，二者合读冲突，因为商标就是 logo，fork 难以同时遵守。＋ 在线一手：ONLYOFFICE 2026-03-30 博客《ONLYOFFICE flags license violations in Euro-Office project》（指控 Nextcloud/IONOS 的 Euro-Office 违反 AGPL 与知识产权，要求保留品牌/署名、完整履行分发义务）与 2026-03-31 博客《Partnership with Nextcloud suspended》（暂停与 Nextcloud 的伙伴合作，但继续支持开发 Nextcloud 版 connector，不影响现有客户）；Nextcloud 2026-04-17 博客《Euro-Office: License compliance and what open source means》（每条附加条款逐条审查：7(a) 免责声明有效且保留；7(b) 要求保留产品 logo + 7(e) 拒绝授予商标权自相矛盾，FSF 认为 logo 不属「合理法律声明或作者署名」，组合构成第 10 条禁止的 further restriction，接收方可依第 7 条移除；Euro-Office 以 commit e452ace 删除该条款；EDIT 8-18：ONLYOFFICE 后来提出新方案并改动 GitHub 许可证，Nextcloud 表示会更新代码头文件匹配新许可证）；Nextcloud 商标指南（未修改版可用其商标，修改版 AGPL 需提供源码的那些改动则不可用）；Nextcloud FAQ（AGPL 是版权许可，不影响商标）。＋ GNU AGPLv3 全文：第 7 条 a–f 附加条款范围、「further restriction 可移除」、第 10 条「不得施加进一步限制」、第 13 条远程网络交互（修改版须向网络用户提供修改版源码）；DocuSeal 仓库 LICENSE 抓取显示为标准 AGPL 全文，附加署名条款未在该次抓取段出现。＋ 第三方：heise / The Register / Computerworld 报道与 IT 法律博客（itenrecht.nl）分析，FSF 博客明确「保留原始 Product logo」不属 AGPL 兼容附加条款、构成 further restriction。"
original_date: 2026-11-17
original_url: "https://nextcloud.com/blog/euro-office-license-compliance-and-what-open-source-means"
description: "解读 Nextcloud 与 ONLYOFFICE 因许可证条款暂停八年合作。先讲准 AGPL 规则：修改自托管 app 并让团队通过网络使用，须向这些用户提供修改后源码；只运行未修改的 AGPL app 供他人网络使用不触发，只有修改后供他人使用或分发副本才会（第 13 条）。对比 DocuSeal 附加条款——要求交互界面保留原始 DocuSeal 署名，是较礼貌、可履行的额外规则。争议焦点是 ONLYOFFICE 在 AGPL 第 7 条加的两句话：分发须保留原始产品 logo（7b）+ 不授予任何商标权（7e）；二者合读冲突，因为 logo 就是商标，fork 可能难以同时遵守。Nextcloud 的 Euro-Office fork 删除该条款（commit e452ace），理由是 logo 不属 7b 的「合理法律声明或作者署名」，组合构成第 10 条禁止的 further restriction，而第 7 条允许移除 further restriction；FSF 与 AGPL 作者 Bradley Kuhn 支持这一判断。ONLYOFFICE 2026-03-30/31 先指控许可违规并宣布暂停合作（但继续维护 Nextcloud connector），Nextcloud 4-17 发文逐条回应；8-18 编辑注明 ONLYOFFICE 提出新方案并改了 GitHub 许可证，Nextcloud 表示会更新头文件匹配新许可——争议有后续，不是停在分手声明。给出读者可操作建议：自托管和 fork 前细读许可证附加条款，分清版权许可与商标权，保留署名可用 About 对话框满足，修改版网络服务留好源码提供路径，遇到 further restriction 可依第 7 条移除并留法律意见。边界：非法律意见、未逐字核验 DocuSeal 附加条款文本、双方主张分开写、未代表任何一方立场。"
published: true
---

3 月 30 日，ONLYOFFICE 发博客指控 Nextcloud 与 IONOS 牵头的 Euro-Office 项目违反其许可条款；次日宣布暂停与 Nextcloud 的伙伴合作。表面看是一次商业分手，真正导火索却是一份多数自托管者从来没读过的东西——源文件头部那段许可证附加条款。

先把最容易被说错的 AGPL 规则讲准，再看这场争议的真正焦点。

## 一、AGPL 的网络条款到底要求什么

AGPL 是 GPL 的「网络版」。它比普通 GPL 多出来的关键一条是第 13 条：修改了程序，并且你的版本支持通过网络与用户交互，那么必须向这些远程用户提供你修改版的对应源码，通过网络服务器免费提供即可。

这里有两个常被混淆的边界：

- 只运行未修改的 AGPL app 供他人通过网络使用，不会因为「网络使用」这一点就触发提供源码的义务；
- 一旦修改后供他人使用，或者分发副本，相应的源码提供与保留声明义务才会启动。

换句话说，日常在公司内部自托管一个原样未改的 AGPL 应用，和「改了代码再让别人通过网络用」，在法律义务上不是一回事。这也是为什么这类争议一般落在「改了之后怎么发」这个环节，和「跑不跑」关系不大。

## 二、附带条款的世界：DocuSeal 是个温和例子

很多 AGPL 项目会在许可证第 7 条允许的范围内附加额外条件。第 7 条列举了允许的事项，包括保留合理的法律声明或作者署名（7b）、拒绝授予商标权（7e）等；超出范围的「非许可性附加条款」被视为第 10 条意义上的「进一步限制（further restriction）」，而第 7 条明确允许接收方移除这种条款。

读者提到的 DocuSeal 是个温和例子：它要求交互界面保留原始 DocuSeal 署名。这类要求落在「作者署名 / 法律声明」的常规范围里，属于较礼貌、也容易履行的附加规则——在「关于」对话框里保留署名即可，不妨碍你改代码、也不妨碍你分发。

问题出在，如果附加条款越过了第 7 条划定的范围，就会和第 10 条「不得施加进一步限制」相撞。

## 三、ONLYOFFICE 的两句话为什么冲突

争议集中在 ONLYOFFICE 每个源文件头部的两句话：

- 依据第 7(b) 条，分发程序时必须保留原始产品 logo；
- 依据第 7(e) 条，不授予你使用其商标的任何权利。

单看每一句，似乎都能在第 7 条里找到对应项。Nextcloud 把这两句并列后写道：「you MUST include the product logo / you do NOT get permission to use the logo in any way」——合起来就是一个死结：logo 本身就是商标。你被要求保留一个商标，却又没有被授予使用它的任何权利——fork 的人很难同时遵守这两句话。

Nextcloud 的论证是：

1. 第 7(b) 条允许保留的是「合理的法律声明或作者署名」。产品 logo 既不是法律声明，也不是作者署名，把它塞进 7(b) 超出了范围；
2. 自由软件基金会（FSF）明确表示，logo 一般不属于「法律声明」或「作者署名」；「保留原始 Product logo」不属于 AGPL 兼容的附加条款，构成第 10 条禁止的进一步限制；
3. 既然是进一步限制，第 7 条允许接收方移除它。Euro-Office 正是用 commit `e452ace` 删掉了这段条款，同时保留了真正有实质内容的部分（7(a) 的免责声明、GUI 素材的 CC BY-SA 声明）。

AGPL 的作者 Bradley M. Kuhn 也公开支持 Nextcloud 的法律判断。Nextcloud 表示会在「关于」对话框里显著署名 Ascensio System SIA 和所有贡献者——这正是 7(b) 本来允许的做法。

## 四、双方各说了什么

把主张分开摆，不替任何一方下最终结论：

- ONLYOFFICE（3 月 30 日）：Euro-Office 使用了源自 ONLYOFFICE 的技术，违反许可与国际知识产权法；要求保留品牌与「对原始技术的恰当署名」、完整履行开源分发义务；认为附加条款是「单一不可分割、可执行」的法律框架，不能挑选适用。
- ONLYOFFICE（3 月 31 日）：暂停与 Nextcloud 的伙伴合作，理由是「信任与共同原则不再被遵守」；但强调不受影响的现有合作继续，并明确会继续支持与开发 Nextcloud 版 connector。
- Nextcloud（4 月 17 日）：逐条审查附加条款后认为，7(a) 有效并保留；logo 条款自相矛盾、构成 further restriction，依第 7 条移除；Euro-Office 因此完全合规，四项用户自由（运行、研究、修改、再分发）完整保留。
- 进展：Nextcloud 那篇博客在 8 月 18 日更新——ONLYOFFICE 后来提出了一份新方案，并改了 GitHub 上的许可证；Nextcloud 表示会更新项目代码与许可证头文件以匹配新许可证。也就是说，这不是停在 3 月分手声明的旧闻，后面还有和解式的技术调整。

## 五、对自托管者和 fork 者意味着什么

1. fork 前先读源文件头部的许可证声明，尤其是 AGPL 第 7 条附加了什么。多数人只看仓库首页写着 AGPLv3，却没读每个文件头那几行附加条款。
2. 分清版权许可与商标权。AGPL 是版权许可，本身不授予也不影响商标；「保留 logo」这种要求落在商标领域，不能用版权许可的条款想当然地覆盖。
3. 保留署名有正当做法。想标注技术来源，用「关于」对话框里的作者署名即可，这落在 7(b) 的合理范围内；要求保留商标 logo 则另当别论。
4. 修改后通过网络提供服务，要留好源码提供路径（AGPL 第 13 条）。注意触发条件是「修改 + 网络交互」，不是「只要有人通过网络访问」。
5. 遇到疑似进一步限制，可依第 7 条移除，并在提交信息里写清理由——Euro-Office 的 commit 就是范例。真有法律风险时，找律师出具意见，别只靠社区共识。

## 六、边界

- 本文是技术解读，不是法律意见；双方对条款效力仍有不同主张，最终解释权在法院或权威机构。
- 文中把 ONLYOFFICE 的指控、Nextcloud 的回应、FSF 与 Kuhn 的表态分开陈述，不代表笔者站队。
- DocuSeal 的附加署名条款按读者提供的上下文转述；本次抓取到的仓库 LICENSE 显示为标准 AGPL 全文，附加条款文本未在该次抓取中出现，故未逐字核验。
- 本次未修改、未分发任何相关代码，未对 Euro-Office 或 ONLYOFFICE 的代码合规性做独立技术审计。
- 时间线以 2026-11-17 能核到的公开材料为准；8 月 18 日的编辑说明争议已出现后续调整。

## Sources

- ONLYOFFICE 博客：<https://www.onlyoffice.com/blog/2026/03/onlyoffice-flags-license-violations-in-euro-office-project-by-nextcloud-and-ionos> ｜ <https://www.onlyoffice.com/blog/2026/03/partnership-with-nextcloud-suspended>
- Nextcloud 博客（含 8-18 更新）：<https://nextcloud.com/blog/euro-office-license-compliance-and-what-open-source-means>
- GNU AGPLv3 全文：<https://www.gnu.org/licenses/agpl-3.0.txt> ｜ FSF 对本案的表态：<https://www.fsf.org/blogs/licensing/agpl-is-not-a-tool-for-taking-freedom-away>
- heise / The Register / Computerworld 报道与 itenrecht.nl 法律分析（第三方，用于交叉印证）
