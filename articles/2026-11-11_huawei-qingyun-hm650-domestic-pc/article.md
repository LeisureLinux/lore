---
title: "麒麟 X90 进桌面：华为擎云 HM650 的「100% 国产」该怎么读"
date: 2026-11-11
slug: huawei-qingyun-hm650-domestic-pc
category: 技术/解读
author: FreeLAMP.com
original_source: "一手核对：SCMP《No Intel, no Qualcomm: Huawei unveils desktop built entirely with China-made components》（Iris Deng，2026-11-05）＋ Tom's Hardware《Huawei develops 'entirely Chinese' homegrown desktop PC system》（Anton Shilov，2026-11-09，含 TechInsights 拆解与供应链判断）＋ tbreak《Huawei Qingyun HM650 desktop claims Chinese-made parts》（含浙江科正认证、价格分歧、华为自家数据标注）＋ Huawei Central《Huawei's first HarmonyOS Desktop PC launched》（发布会规格）＋ Notebookcheck / TechSpot / TechNews 科技新报 / 天极网（yesky）交叉核对 ＋ Microsoft Learn 5.7.515 高容量发件人规则（用于对照「5000 封/天」口径）"
original_date: 2026-11-05
original_url: "https://www.scmp.com/tech/tech-trends/article/3373435/no-intel-no-qualcomm-huawei-unveils-desktop-built-entirely-china-made-components"
description: "解读华为 2026-11-05 在武汉鸿蒙办公产业峰会发布的擎云 HM650 系列台式机：首款搭载麒麟 X90、运行鸿蒙企业版的华为桌面 PC，主打政企与政府市场，宣称「100% 国产化认证」。本文按四层拆开这个说法：①产品层 —— 麒麟 X90 为 10 核 20 线程（4+4+2 泰山 Armv8 核、全核 SMT）、Maleoon 910 GPU、40W TDP、双面散热，配 16GB LPDDR5 + 256/512GB SSD；②认证层 —— 浙江科正电子信息产品检验验证的是「零件在国内制造」，不等于「每个零件都由中国设计」，SCMP 与 tbreak 都点明认证范围模糊；③供应链层 —— Tom's Hardware 明确指出芯片虽由中芯国际 SMIC N+2（7nm 级）制造、内存可能是长鑫 CXMT、闪存可能是长江存储 YMTC，但产线设备来自荷兰/美国/日本、材料来自日本、IP 来自英国、EDA 来自美国（部分国产）；④软件层 —— 鸿蒙企业版用华为自研内核与架构，不再含早期版本的 Linux 组件，带来安全更新与软硬协同的控制力，代价是 Windows 应用兼容性不明。价格与开售时间标注分歧（6899 元 vs 7199 元，12 月 1 日、仅商用渠道、未见中国境外销售），华为自家的「性能提升 15%」「21000+ 应用」「鸿蒙电脑出货破百万」均标为厂商口径、非独立实测。结论：这台机器真正的里程碑是「整机零件国产化 + 自有 OS 栈在政企桌面闭环」，不是「半导体全链条自主」；把「制造地」当成「设计来源」或「设备/EDA 来源」，就是把三层混成一层。"
published: true
---

> 原文：SCMP《No Intel, no Qualcomm: Huawei unveils desktop built entirely with China-made components》（2026-11-05）
> 深度补充：Tom's Hardware（Anton Shilov，2026-11-09）
>
> 本文依据上述报道及华为发布会规格、多家交叉核对逐条标注。

## 一、先把「100% 国产」拆成四个问题

华为 2026 年 11 月 5 日在武汉的鸿蒙办公产业峰会上发布**擎云 HM650 系列**台式机，SCMP 的标题写得很直白：**No Intel, no Qualcomm**；Tom's Hardware 四天后的跟进则加了个更长的后缀 —— *but Western supply chain lingers*（但西方供应链仍在）。

这两个标题凑一起，恰好就是本文要拆的四个问题：

| 层 | 问题 | 结论 |
|---|---|---|
| 产品 | 里面装的是什么 | 麒麟 X90 + 鸿蒙企业版，没有 Intel/Qualcomm，也没有 Windows |
| 认证 | 「100% 国产化」证明了什么 | 证明**零件在国内制造**，不证明**每个零件由中国设计** |
| 供应链 | 造这些零件的工具从哪来 | 设备/材料/IP/EDA 仍大量依赖境外 |
| 软件 | 换掉 Windows 换来了什么、丢了什么 | 换来内核与更新自主，代价是 Windows 应用兼容性不明 |

**一句话**：这台机器是「整机零件国产化 + 自有 OS 栈」的里程碑，不是「半导体全链条自主」的里程碑。

## 二、产品层：麒麟 X90 第一次进台式机

麒麟 X90 不是新芯片 —— SCMP 说它 2025 年就出现在华为消费级笔记本和平板里，**HM650 是它第一次进桌面台式机**。

按 Tom's Hardware 与发布会规格汇总：

| 项 | 规格 |
|---|---|
| CPU | 10 核 20 线程，**4+4+2** 配置的华为自研泰山（Taishan）Armv8 核，全核支持 SMT |
| GPU | Maleoon 910（Arm Mali 系） |
| NPU | 独立神经网络单元 |
| 主频 / 功耗 | 2.3 GHz；**40W TDP**（常规桌面处理器多为 65–125W），配双面散热 |
| 内存 | 16GB LPDDR5，Tom's 推测来自长鑫 **CXMT** |
| 存储 | 256GB / 512GB SSD，Tom's 推测来自长江存储 **YMTC** |
| 制造 | 华为未官方披露；**TechInsights 拆解**确认为中芯国际 **SMIC N+2（7nm 级）** |
| 型号 | HM650（企业）/ HM650G（政府），有 8 核与 10 核配置 |

Tom's 的评价很克制：这证明华为能用**国内可获得的半导体制造能力**做出 PC 级处理器，**但工艺节点仍落后于 Intel、TSMC、Samsung 的领先制程**。

另外几个发布会细节：键盘有独立的**小艺 AI 键**（一键查资料/写文档/整理文件/会议转写摘要/与华为设备协同），部分 AI 功能需联网且要另付订阅；企业级集中管理、个人空间/企业空间双模式；第二代安全框架带 AI 换脸与变声检测。

## 三、认证层：「100% 国产化认证」到底认证了什么

这是最容易被标题带偏的一层。

华为平板与 PC 产品线总裁**朱懂东**在发布会上宣布该系列获得「**100% 国产化认证**」，由**浙江科正电子信息产品检验**验证。tbreak 与 Notebookcheck 都把这句话读窄了：**认证覆盖的是零件在哪里制造，不是每一个零件由谁设计**。tbreak 更直接说，认证的确切范围「并不清楚」。

而 Tom's Hardware 把华为的主张写得更完整：处理器、内存、存储、**电源**、**无线连接**全部在国内制造。所以「100%」说的是**整机 BOM 的制造地**，不是「全部自研」。

**这个区分不是抠字眼。** 一台机器可以做到「所有零件中国造」，同时里面某些芯片的 IP 授权、设计工具、或架构来自境外 —— 两者并行不悖。把「制造地」当成「设计来源」，就是把两层混成一层。

## 四、供应链层：制造地是中国的，产线不是

Tom's Hardware 那段最值得原样记住的判断：

> CPU、内存、存储芯片虽然在国内流片，但用的仍是**境外制造设备**（荷兰、美国、日本）、**材料**（日本）、**IP**（英国）、以及 **EDA 软件**（美国，部分国产）。

也就是说：

- **芯片**：SMIC N+2 制造 ✅，但光刻/沉积等设备、EDA、Arm 指令集授权 ❌
- **整机**：CPU / 内存 / SSD / 电源 / 无线模块国内制造 ✅
- **半导体产业链**：设备、材料、IP、EDA 仍有境外依赖 ❌

> **Probably yes. Yet, with major caveats, including a semiconductor supply chain that relies on tools and software designed and produced elsewhere.**

（**这是全文唯一原样保留的英文**：Tom's Hardware 给 HM650「是否完全国产」下的结论 —— 大概可以，但附带一条重大条件：半导体供应链仍依赖别处设计与生产的工具和软件。）

Tom's 自己给的结论是：「**能不能说 HM650 系列完全依赖中国开发和制造的零件？大概可以。但有重大附带条件**」—— 附带条件就是上面那条供应链。这个「大概可以 + 但是」，比任何一句「完全自主」或「都是噱头」都准确。

顺带一提，本号 10 月写过华为 Peerium/灵衢那篇，结论也是同一套方法：**新闻稿说「突破」，论文说「延续」**。看这类发布，先把「谁说的、证明到哪一层」问清楚，比争口号有用。

## 五、软件层：换掉 Windows 换来什么、丢掉什么

HM650 跑的是 **HarmonyOS 企业版**（发布会口径为 HarmonyOS PC 7.0 / V1.0 Enterprise Edition）。Tom's 特别点出：**与早期含 Linux 组件的鸿蒙版本不同，企业版用华为自己的内核与软件架构**。

这带来的收益是实的：操作系统由一家中国公司开发维护，安全更新、软硬协同、整机集成都在自己手里；对政企与政府客户，这本身就是采购理由。

代价也写得明白：**与既有 Windows 应用的兼容性，对依赖跨国公司 Windows 软件的企业客户可能仍是限制**。tbreak 补了一句更准：华为称「21000+ 应用适配鸿蒙」，但那是**整个生态的数字，不是 HM650 上验证过的应用数**；HM650 能否跑原生 Windows 应用，**不清楚**。

**「能不能跑 Windows 软件」和「有多少应用适配」是两个问题**，厂商给的是后者，采购方要问的是前者。

## 六、数字要标口径：哪些是厂商说的，哪些是媒体说的

这一节专门防止把宣传口径写成事实：

| 说法 | 出处 | 标注 |
|---|---|---|
| 软硬协同性能提升 **15%** | 华为自家实验室 | **厂商口径，非独立实测** |
| **21000+ 应用**适配鸿蒙 | 华为 | 全生态数字，非 HM650 验证数 |
| 鸿蒙电脑出货**破 100 万台** | 华为（2025 至今） | 厂商口径 |
| 「100% 国产化认证」 | 华为，浙江科正验证 | 认证范围＝制造地，非设计来源 |
| 价格 **6899 元 / 7199 元** | 媒体分歧 | tbreak 明确说**报道不一致**，Notebookcheck 记 7199 元（约 1080 美元） |
| **12 月 1 日**开售 | 多家媒体 | 仅**商用渠道**，不走零售；未见中国境外销售 |
| 目标客户 | SCMP / 发布会 | 政企、政府、金融、能源 |

**价格与开售时间有分歧，本文不挑一个当定论**，按「报道不一致」如实写。

## 七、结论：把三层分开，才知道这台机器值在哪

> **「国产」至少有三层：零件在哪造、谁设计的、用什么设备和工具造的。HM650 把第一层做到了可认证，第二层部分做到，第三层仍挂在境外供应链上。**

这不妨碍它是个真里程碑：**这是华为第一次把自研 PC 级 SoC、国产内存与存储、自有内核的操作系统，装进一台面向政企规模化交付的台式机**。在受制裁的环境里，「整机 BOM 制造地 + OS 栈」闭环本身就是可交付的能力。

但把它读成「半导体全链条自主」就过了。Tom's 标题里那个 *but Western supply chain lingers*，和标题前半句同样重要。

最后留一个更实用的读法：**下次看到「100% 国产」，先问认证的是制造地、设计来源，还是产线工具。** 三个答案对应三件完全不同的事 —— 这也正是本号写 Peerium、写 secwrap、写「配置了 ≠ 生效了」时反复用的那把尺子。

## 八、事实边界

- **本文未拿到华为官方产品页与认证证书原件**；规格、认证机构名称、发布会细节来自 SCMP、Huawei Central、tbreak、Notebookcheck、TechNews 科技新报、天极网等公开报道的交叉核对。
- **Kirin X90 的制程**：华为未官方披露，SMIC N+2（7nm 级）来自 **TechInsights 拆解**，本文按 Tom's Hardware 转述，非华为确认。
- **CXMT / YMTC**：Tom's 用 "probably" 推测内存与闪存供应商，本文保留推测语气，未当作确认事实。
- **价格、开售日期、渠道**存在报道分歧，本文并列列出，不作单一结论。
- **15% / 21000+ / 100 万台**均为华为自家口径，未找到独立测试或第三方审计。
- **Windows 应用兼容性**：多家媒体均标「不清楚」，本文不作推测。
- **境外供应链**（设备/材料/IP/EDA 来源）为 Tom's Hardware 的分析判断，非华为披露；本文按报道转述。
- 本文只做公开资料核对与口径辨析，不构成采购建议或对厂商主张的独立验证。

---

## Sources

- SCMP, Iris Deng, *No Intel, no Qualcomm: Huawei unveils desktop built entirely with China-made components*（2026-11-05）: <https://www.scmp.com/tech/tech-trends/article/3373435/no-intel-no-qualcomm-huawei-unveils-desktop-built-entirely-china-made-components>
- Tom's Hardware, Anton Shilov, *Huawei develops 'entirely Chinese' homegrown desktop PC system…but Western supply chain lingers*（2026-11-09）: <https://www.tomshardware.com/tech-industry/huawei-develops-entirely-chinese-homegrown-desktop-pc-system-features-10-core-20-thread-kirin-x90-consumer-cpu-and-huais-own-harmonyos-operating-system-but-western-supply-chain-lingers>
- tbreak, Abbas Jaffar Ali, *Huawei Qingyun HM650 desktop claims Chinese-made parts*（2026-11-09）: <https://tbreak.com/huawei-qingyun-hm650-chinese-parts/>
- Huawei Central, *Huawei's first HarmonyOS Desktop PC launched with Kirin X90…*（2026-11-05）: <https://www.huaweicentral.com/huaweis-first-harmonyos-desktop-pc-launched/>
- Notebookcheck / TechSpot / TechNews 科技新报 / 天极网 yesky 交叉核对
- 本号《华为 Peerium：新闻稿说「突破」冯·诺依曼，论文说「延续」冯·诺依曼》: <https://freelamp.com/articles/2026-10-08_huawei-peerium-lingqu-hc2026/>
