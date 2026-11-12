---
title: "Kora：把 CPU、GPU、NPU 和局域网里的机器当成一台电脑的 Linux 桌面"
date: 2026-11-12
slug: kora-cortex-whole-chip-inference-npu
category: 技术/解读
author: FreeLAMP.com
original_source: "一手核对：KORA Systems 官方 press kit（press.kora.fun，2026-11-10 06:00 PT，含主新闻稿、KORA×Qualcomm 联合新闻稿、HUMAIN 更新与完整 FAQ）全文 ＋ Tom's Hardware《New Linux desktop OS splits AI workloads across CPU, GPU, and NPU…》（Shane Downing，2026-11-11，含 NPU 支持表与 Kirt McMaster 采访）＋ TechCrunch《After challenging Google's Android with Cyanogen…》（2026-11-10，含 Nix / Fedora Silverblue、专有与开源边界、订阅模式、50 人团队与 Codex/Claude 使用率）＋ WIRED 同期报道 ＋ Qualcomm 官方 Snapdragon X2 Elite 产品页（80/85 TOPS 口径）＋ 本站 2026-09-23《高通在夏威夷谈 Snapdragon X2 的 Linux》与 2026-10-09《骁龙笔记本的 AI PC 叙事，在 Linux 上还缺最关键的那一环》两篇旧文"
original_date: 2026-11-10
original_url: "https://www.tomshardware.com/software/linux/cyanogen-co-founder-unveils-kora-a-linux-os-that-splits-ai-models-across-the-cpu-gpu-and-npu-snapdragon-x2-elite-and-hexagon-npu-get-full-support-first"
description: "本文以 KORA 官方新闻稿与联合新闻稿为主，Tom's Hardware / TechCrunch / WIRED 作对照，指出媒体标题「Cyanogen 联合创始人发布 Kora」容易让人误读成「系统已可下载」：实际是 2026-11-10 的发布预告，HUMAIN OS 企业版 2027 年商用（首批 OEM 搭载 Snapdragon X2 Elite 的 Linux 桌面），Kora 面向开发者与创作者「2027 年稍晚」才到。技术核心是 Cortex 混合推理引擎，把本机 CPU/GPU/NPU 乃至同一局域网内其他机器调度成「一台电脑」，本地模型默认、必要时用云端前沿模型；内部的 Lemma 基于 llama.cpp / whisper.cpp / stable-diffusion.cpp / ONNX，主要支持 GGUF，可按需把模型层切分到不同处理器，运行库用 llama.cpp 的 Hexagon 后端。官方联合稿宣称近一年与高通合作，在 X2 Elite（Oryon CPU + Adreno GPU + 80 TOPS Hexagon NPU）上跑完整 Linux 桌面、26B 语言模型完全端侧运行并同时跑语音识别与嵌入模型，高通继续把 X2 Elite 支持上游进主线内核；Tom's 引 McMaster 称 Gemma 4 26B 解码约 25 tokens/s，且「今天只有 Snapdragon X2 Elite 上的 Hexagon 被支持」，AMD XDNA 2 计划上市时支持、Intel NPU 仍在洽谈。官方 FAQ 明说 Cortex 是自有技术且不开源，「开放」只发生在模型层；底座是 Linux + Nix（替代 Playtron GameOS 的 Fedora Silverblue），桌面与 Cortex 专有，工作区用 AppArmor 加细粒度权限隔离，公司预计 2027 年约 70% 模型调用在本地完成并靠订阅变现。文章也接上本站两篇旧文：9 月高通谈 X2 的 Linux 尚是早期开发者预览、Hexagon NPU 还在补，10 月写过 Linux 上缺 NPU 这一环——Kora 声称补的正是它，但整套说法目前只有厂商自述与演示、没有第三方实测。"
published: true
---

> 一手：KORA Systems 官方新闻稿、与高通的联合新闻稿、完整 FAQ（2026-11-10）
> 对照：Tom's Hardware / TechCrunch / WIRED 同期报道、高通官方产品页、本站两篇 Snapdragon X2 旧文
>
> 标题说「发布」，但要看清发布的是产品还是预告。

11 月 10 日，Cyanogen 联合创始人 Kirt McMaster 的公司 KORA Systems 公布了 Kora —— 一套「从内核到 shell」围绕 AI 重建的 Linux 桌面。Tom's Hardware 的标题把最抓眼的部分放在前面：把 AI 负载拆到 CPU、GPU、NPU，甚至同一局域网里的其他机器。

我去把官方 press kit 的两份新闻稿和完整 FAQ 读完，觉得最该先说的是三件容易被标题盖住的事：这是 2027 年才上市的预告；核心引擎不开源；「全芯片推理」今天只在一种 NPU 上成立。

## 一、先摆正时间点

官方主稿写的是「Kora 将于 2027 年登陆 PC」，与高通的联合稿更具体：

- HUMAIN OS（与沙特 PIF 支持的 HUMAIN 共同开发的企业版）2027 年商用，是「全球首批搭载 Linux 桌面 + Snapdragon X2 Elite 的 OEM PC」；
- Kora（面向开发者与创作者）2027 年稍晚跟进，扩展到 Snapdragon PC；
- 两家合作「近一年」，高通工程师参与了桌面 bring-up 与推理调优，并继续把 X2 Elite 支持上游进 mainline Linux 内核。

所以这不是「现在可以装的系统」，是一次产品发布预告 + 生态合作公告。TechCrunch 补充了商业面：预计免费使用、靠订阅打包模型与 agent 服务变现；公司约 50 名工程师，用 Codex 与 Claude 等 AI 编码工具，McMaster 称开发至少提速五倍。

顺带理清血统：公司前身是 Playtron（2022 年成立的 Linux 游戏 OS 公司，产品 GameOS），2025 年 7 月更名 Kora 转向 AI；Kora 不是从零写的，复用了 GameOS 近三年的工作，但底座从 Fedora Silverblue 换成了 Linux + Nix。团队主要从 Linux 游戏社区招募，McMaster 明确说没有一名 Kora 工程师来自 Cyanogen —— 标题里的「Cyanogen 联合创始人」是创始人履历，不是团队传承。

## 二、Cortex 到底做什么

官方给 Cortex 的定位是「操作系统的神经系统」：一个为本地模型优化的混合推理引擎，把机器里每一颗芯片（CPU、GPU、NPU）以及网络上每一台机器变成「一台计算机」。本地模型默认跑在用户自己的硅上，需要时再接入云端前沿模型；Cortex 本身不是模型，它管的是调度——哪个任务去哪块算力。

被媒体较少展开的是内部层次。Tom's 采访里 McMaster 说：

- 主要支持 GGUF（llama.cpp 的模型格式）；
- Lemma 是 Cortex 里的推理引擎，「能按需把模型层切到不同处理器上」，构建在 llama.cpp、whisper.cpp、stable-diffusion.cpp 与 ONNX 之上；
- 在 X2 Elite 上，NPU 路径用的是 llama.cpp 的 Hexagon 后端（高通自家框架是 QAIRT/QNN）。

上层还有三件配套：神经工作区（把应用、agent、项目信息按工作/客户隔开）、神经文件系统（按语义而不只是文件名/目录索引）、以及 KORA SDK（把项目、记忆、上下文、语义搜索、邮件等原语开放给第三方）。官方 FAQ 写了一句很关键的安全细节：工作区内部通过 AppArmor 加上每个应用/agent 的细粒度权限（硬件、文件、AI 工具、连接服务）来强制隔离；记忆系统对联系人、邮件、日历、云文件的分析在本机用本地模型完成，产生的记忆与上下文留在本机，只有用户授权时才把相关上下文发给云服务。

「开放」这个词在新闻稿里出现频率很高，但要精确定义。官方 FAQ 自己写得很直白：Cortex 是 Kora 自有技术，不是开源；开放的是模型层——任何实验室的模型、本地或云端、由用户选择，第三方可基于同样的权限体系接入。TechCrunch 也确认：Linux 与 Nix 是开源，但 Cortex 引擎与桌面界面保持专有，公司未承诺把自己的软件开源。所以「开源 AI 桌面」是误读，准确说法是开源底座 + 专有智能层 + 开放模型接入。

## 三、Snapdragon X2 Elite：厂商自述的三个数字

联合稿与技术 FAQ 给出的口径：

| 项 | 官方说法 |
|---|---|
| 平台 | Oryon CPU + Adreno GPU + 80 TOPS Hexagon NPU 单芯片 |
| 桌面 | 在 X2 Elite 上跑起完整 Linux 桌面（Kora 自研桌面环境） |
| 模型 | 26B 参数语言模型完全端侧运行，同时跑 ASR 与 embedding 模型 |
| 性能 | Tom's 引 McMaster：Gemma 4 26B 解码约 25 tokens/s |
| 本地占比 | 预计 2027 年约 70% 的模型调用在本地完成，其余取决于硬件与负载 |
| Windows 兼容 | Kora 自研兼容/翻译技术，在 Snapdragon 上的 Linux 里运行选定的 x86-64 Windows 应用 |

几个必须标注的边界：

- 80 TOPS 是算力指标，26B 是参数量，两者不能直接换算；公告没披露模型名称、量化方式、内存容量与功耗（Tom's 补充了 Gemma 4 26B 与 25 tok/s，但仍是厂商口径）。高通官网对 X2 Elite 系列标的是「最高 85 TOPS」，联合稿写 80 TOPS，属于具体 SKU 差异，不是矛盾。
- 「今天支持的 NPU 只有一种」。McMaster 对 Tom's 的原话是「only Hexagon on Snapdragon X2 Elite is supported today」。Tom's 那张表列出：AMD XDNA 2（Ryzen AI）计划上市时支持、走 ONNX、大概率先跑嵌入与语音识别而非语言模型；Intel NPU 支持在规划中、「洽谈进行中」，业界对应 OpenVINO。也就是说，跨 CPU/GPU/NPU 的宏大叙事，目前只在一家硬件上被验证。
- 没有第三方实测。所有性能数字来自 Kora 与高通的联合稿、以及记者转述的创始人采访；本站未拿到机器复现。

## 四、这件事为什么值得 Linux 读者看一眼

本站 9 月写过《高通在夏威夷谈 Snapdragon X2 的 Linux》：那时是早期开发者预览、定制内核 + Debian 13 用户态、Adreno 走 Freedreno/Turnip 开源驱动，而 Hexagon NPU 支持「还在补」；10 月那篇标题干脆叫《骁龙笔记本的 AI PC 叙事，在 Linux 上还缺最关键的那一环》。

Kora 声称补上的正是这一环，而且路径很说明问题：不走社区驱动路线，用高通自己的 QAIRT/QNN 栈，通过 llama.cpp 的 Hexagon 后端把 NPU 拉进调度。与此同时高通继续把 X2 Elite 支持上游进 mainline —— 这两件事并行不悖：主线内核解决「能跑」，厂商私有栈解决「NPU 能不能被用于推理」。对普通发行版用户，前者才是可复用的公共资产；后者目前锁在 Kora/HUMAIN OS 里。

另一条值得警惕的线是「局域网内其他机器」。官方把「网络上每一台机器变成一台计算机」写进 Cortex 定义，意味着推理调度可能跨越单机边界；官方 FAQ 强调工作区隔离与权限，但分布式推理的认证、加密、发现机制在新闻稿里没有展开。这属于「能力很吸引人、细节尚未公开」的部分，不宜当成已解决。

最后是定位。TechCrunch 引 Statcounter：Windows 2026 年 10 月约占桌面 OS 77%；McMaster 不打算抢这十亿用户，明说「微软可以留着它那十亿用户」，盯的是当下约 4500–5000 万重度 AI 用户（他预计 2033 年超 2 亿）。这套说法与订阅变现、企业版先行、OEM 合作一起看，Kora 更像从高价细分市场切入的专有发行版，而不是要挑战整个 Linux 发行版生态。

## 五、事实边界

- 本文技术事实以 Kora 官方 press kit（2026-11-10 主稿、KORA×Qualcomm 联合稿、HUMAIN 更新、FAQ）为准；Tom's Hardware 的 NPU 表与 McMaster 采访、TechCrunch 的开源/商业细节、WIRED 的定位描述均标注来源。
- 26B 端侧、25 tokens/s、70% 本地调用、80 TOPS、Windows 应用兼容等均为厂商自述或计划值，无第三方基准、无公开量化/内存/功耗数据；「70%」是 2027 年预测，不是实测。
- NPU 支持状态为发布时点口径：仅 Snapdragon X2 Elite 的 Hexagon「今天支持」，AMD/Intel 为计划或洽谈中；后续可能变化。
- 官方明确 Cortex 与桌面专有、模型层开放；本文未把 Kora 描述为开源发行版。Linux 与 Nix 的开源属性不等于整个产品开源。
- 本文未安装或运行 Kora（2027 年才上市），未验证任何演示；与本站两篇 Snapdragon X2 旧文的对照属编辑判断。

## 六、结论

Kora 真正提出的问题是：当一台 PC 里同时有 CPU、GPU、NPU，桌面上又同时跑着本地模型、云端模型和一堆 agent，谁来当那个调度者？ 它的答案是把这件事塞进操作系统内核层，而不是留给每个 App 自己解决 —— 这个方向本身比「又一个 Linux 发行版」有意思得多。

但目前能确定的是：底座 Linux + Nix 开源，Cortex 专有；模型层开放，引擎不开放；跨芯片调度今天只在 X2 Elite 的 Hexagon 上成立；两个 OS 都要等 2027。一份写得很漂亮的 press kit，和一套能被第三方验证的系统，中间还隔着整整一年。

## Sources

- KORA 官方 press kit（含主新闻稿、联合新闻稿与 FAQ，2026-11-10）：<https://press.kora.fun/>
- KORA × Qualcomm 联合新闻稿纯文本：<https://press.kora.fun/kit/releases/KORA-Qualcomm-Release.txt>
- Tom's Hardware（Shane Downing，2026-11-11）：<https://www.tomshardware.com/software/linux/cyanogen-co-founder-unveils-kora-a-linux-os-that-splits-ai-models-across-the-cpu-gpu-and-npu-snapdragon-x2-elite-and-hexagon-npu-get-full-support-first>
- TechCrunch（2026-11-10）：<https://techcrunch.com/2026/11/10/after-challenging-googles-android-with-cyanogen-its-co-founder-takes-aim-at-windows-for-ai-era/> ｜ WIRED：<https://www.wired.com/story/kora-new-linux-based-desktop-operating-system-is-built-for-ai-nerds>
- Qualcomm Snapdragon X2 Elite 产品页：<https://www.qualcomm.com/laptops/products/snapdragon-x2-elite>
- 本站旧文：<https://freelamp.com/articles/2026-09-23_qualcomm-snapdragon-x2-linux/> ｜ <https://freelamp.com/articles/2026-10-09_snapdragon-linux-npu-ai-pc/>
