---
title: "Rembrandt：10 天做出一个 Lightroom 替代品，而它的 README 自己交代了原型来自 darktable"
date: 2026-10-09
slug: rembrandt-photo-editor-github
tags: [Rembrandt, 照片编辑, Lightroom, darktable, RAW, GPL, AI生成代码, vibe coding, WebGPU, Tauri, LibRaw, 开源许可, 原创]
category: 开源/工具
author: FreeLAMP.com
original_source: "GitHub: thesnarkitecht/rembrandt（README / NOTICE / SECURITY）/ Hacker News 讨论"
original_author: "thesnarkitecht；HN 讨论参与者"
original_date: 2026-10-09
original_url: "https://github.com/thesnarkitecht/rembrandt"
description: "Rembrandt 是一个 GPL-3.0 的跨平台照片编辑器，自称 Lightroom 替代品，无需账号、无订阅、无追踪，AI 全部在本地跑，还能自托管。它 2026 年 9 月 29 日建仓，10 天内出了 10 个 release，75 次提交全部来自一个人。本文梳理它的技术栈（JavaScript + WebGL2/WebGPU 着色器 + Rust/Tauri 外壳 + WASM 版 LibRaw）、值得肯定的工程取舍（XMP 副文件、构建存证、AI 不上传），以及在 HN 上被追问出的那个最关键问题：它 README 的 Credits 里承认最早的原型移植了 darktable 的算法。"
published: true
---

> 来源：[github.com/thesnarkitecht/rembrandt](https://github.com/thesnarkitecht/rembrandt)（README、NOTICE.md、SECURITY.md）、[Hacker News 讨论（2026-10-08）](https://news.ycombinator.com/item?id=50012199)
> 本文为**解读**。仓库指标（stars、提交数、release 时间）是笔者于 2026-10-09 通过 GitHub API 实测的。

## 一句话结论

Rembrandt 是一个 **GPL-3.0 的跨平台照片编辑器**，定位是 Lightroom 的免费替代品：**不用账号、没有订阅、没有追踪、AI 全在本地跑、可以自托管**。技术上它是 **JavaScript + WebGL2/WebGPU 着色器做编辑引擎，Rust/Tauri 做桌面外壳，LibRaw 编译成 WASM 解 RAW**。它的野心和完成度确实惊人，**但最值得读的其实是两个细节**：一，它 README 的 Credits 里承认**最早的原型移植了 darktable 的算法**；二，作者把「用自然语言下指令」这个功能明确写成「**一个词汇表，不是语言模型**」。

## 一、先看客观指标：这是一个 10 天大的项目

这些数字是笔者实测的，它们决定了你该怎么看待这个项目：

| 指标 | 数值（2026-10-09 实测） |
|---|---|
| 仓库创建 | **2026-09-29** |
| 提交数 | **75** 次 |
| 贡献者 | **1 人**（thesnarkitecht） |
| Stars / Forks | **78 / 3** |
| Release | **v0.3.10 于 2026-10-09 发布，10 天内 10 个版本**，每个 19 个产物 |
| 主语言 | C++（主要是内置的 LibRaw）、JavaScript、CSS、Rust |
| 许可证 | **GPL-3.0-or-later** |

**这组数字本身就是本文的核心信息**：一个**创建 10 天、单个作者、75 次提交**的仓库，却已经拿出跨平台安装包、自托管服务器、Lightroom 目录导入、AI 蒙版与降噪、超分辨率、HDR/全景拼接这一整套功能清单。

**对照一下参考系**：darktable 有 **1.3 万 stars、1.4 千 forks**，而它的项目页明确写着「**darktable 不是免费的 Adobe Lightroom 替代品**」。两者不是一个量级的项目，也不该被放在同一句话里比较。

## 二、技术栈：它的工程选择其实很聪明

抛开来源问题，这套架构选择是站得住的：

| 层 | 技术 | 说明 |
|---|---|---|
| 编辑引擎 / 本地 AI | **JavaScript + WebGL2 / WebGPU 着色器** | 编辑和 AI 推理都走 GPU 着色器路径 |
| 桌面外壳 | **Rust + [Tauri](https://tauri.app)** | 小体积，不是 Electron |
| RAW 解码 | **[LibRaw](https://www.libraw.org)（C++）编译为 WebAssembly** | 复用成熟解码器，不改上游代码 |
| 镜头校正数据 | **[Lensfun](https://lensfun.github.io)**（1,500+ 镜头配置文件） | 直接转换数据库，只取数据、代码自写 |
| 超分辨率 | [Real-ESRGAN](https://github.com/xinntao/Real-ESRGAN) 紧凑通用模型（BSD-3） | 模型文件+许可声明齐备 |
| AI 降噪 | [KAIR / FFDNet](https://github.com/cszn/KAIR) | 输出新的 DNG，保留原文件 |
| 主体/景深/物体蒙版 | [MediaPipe](https://ai.google.dev/edge/mediapipe) Tasks Vision（Apache-2.0） | 本地模型，不上传 |

**几个我认为值得单独肯定的细节**：

- **「Ask in words」不是 LLM**。README 的原话是「它在你设备上运行：**一个词汇表，不是语言模型**」。也就是说，你说「暖一点、亮一点」「阴影 +25」，它走的是规则式的词表解析，而不是调用大模型。**在一个到处把 LLM 当作卖点的时期，明确说自己没用 LLM，这是一种诚实，也顺便绕开了幻觉和成本问题**；
- **编辑无损且不锁死**。原图从不移动或改写，编辑存为标准 **XMP 副文件**放在照片旁边，Lightroom、darktable 都能读。作者在 HN 上的回应也很到位：「**如果这个项目哪天停了，你的东西也不会被锁住。**」
- **构建有存证**。每个 release 由 GitHub Actions 从公开源码构建，附 `SHA256SUMS`，0.3.8 起带**签名构建存证**（`gh attestation verify`）。自更新只装本仓库 release 的产物、只走 HTTPS、SHA-256 不匹配就拒绝，且**从不申请管理员权限**；
- **GPL 里加了应用商店的额外许可**（GPL-3.0 第 7 条），允许通过 App Store 或 Google Play 分发，前提是源码持续可用。这是个务实的处理，避免了 GPL 与商店条款的经典冲突。

**一个中立观察**：仓库里有 `src/vendor/nsfw/`（TensorFlow.js + NSFWJS 模型）。README 功能列表里没提，可能是为图片库导入做准备。这个不算问题，但值得知道。

## 三、最关键的问题：那个「原型移植了 darktable 算法」

这是 HN 上被追问出来的，也是这个项目最值得讨论的地方。

有用户直接问：**「它相对 darktable 有什么优势？darktable 的一个批评是它强调场景参照工作流……这个项目也是 C++ 写的、也用场景参照工作流？这巧合得有点巧。有多少重要的设计决定（或实现）是从 darktable 抄来的？」**

作者的回应很坦诚，我完整引用：

> 这是个公道的问题。**场景参照的设计是仿照 darktable 的，这个功劳归 darktable。** 我最早的原型移植了一些 darktable 的算法，**我在发布前把它替换成了独立实现**。两个项目都是 GPL-3.0，README 现在直接署名了 darktable。**我做 Rembrandt 是因为 darktable 的学习曲线让我用不下去，不是因为它更差；它的控制力强得多。** 这里的目标是可接近性：更少、更宽的控制项，用于蒙版和降噪的本地 AI，以及 Lightroom 目录导入。

**如何评价这个回应？**

**从合规角度它是正面的**：两个项目都是 GPL-3.0，本来就不需要「独立实现」这个说法；作者主动替换、主动署名、主动说明，比很多项目规范。

**但从项目成熟度角度，它暴露了真实状态**：**一个「独立实现」是在发布前几天才替换进去的，而 75 次提交全部来自一个人，10 天内出了 10 个版本。** 这不等于代码有问题，但意味着**它还没有经历过时间检验**——没有第二个人的代码审查，没有长期的 bug 积累与修复，没有用户踩出来的边界情况。

**HN 上最尖锐的批评**来自一位自称职业摄影师的人：

> 我数了数，**过去一年至少出现了十个这类照片编辑应用**，很多是最近几个月冒出来的，全部是 LLM 辅助或者完全 AI 生成的。**它们确实能用，但……不像 Lightroom 或 darktable（一个花了数年才做到成熟的开源 RAW 编辑器），它们全都边缘粗糙。** 也许未来它们会更好，但**现在它们是爱好者的应用**。

**还有一条批评值得引用**，它指出了沟通方式的问题：

> 你的评论里唯一令人惊讶的是，**今天最新一个 vibe coded 应用居然被顶了上来**。说真的，你得问 Claude 才知道这工作流是不是受 darktable 启发。**这个帖子里读了 Claude 写的 README 的人，可能比「你」更了解「你的」软件是怎么工作的。**

**以及关于可持续性的一条**：

> 这恰好是我**不想把照片管理工作流托付**给的那种项目。**软件现在比以前更便宜，但用心的维护和长寿命对我来说值钱得多。**

**而作者对这个批评的回应，恰恰是整套设计里最聪明的地方**：

> 说得公道。**你的原图永远不会被修改，编辑是标准的 XMP 副文件，Lightroom 和 darktable 都能读，所以如果这个项目哪天停了，也不会锁住任何东西。**

**换句话说：他把「项目可能早死」这个风险，用「不锁定数据」这个设计给对冲掉了。** 这是一个很成熟的回答方式：不辩解自己会活下去，而是让用户不必赌它活下去。

## 四、我认为真正值得讨论的那个问题

HN 上有一条评论问到了点子上，而且它超越了 Rembrandt 本身：

> **这是一个完整的 clean room 实现吗？** 我真的很想看看 AI clean room 逆向工程项目在**法律挑战**面前会是什么结果。按说 clean room 实现是合法的。**但有了 AI 它们变得太容易了**，看起来这一点会需要改变。**或者世界会崩溃。很难说哪个更可能。**

**这是这个项目最有价值的讨论点**，而且它和我们之前写过的一件事直接相连：**有一个类似的案例里，某项目的 CLAUDE.md 里明确写了一整套「clean room」规则**：绝不读取、反汇编或复制目标软件包里的任何内容（只允许看名字和列表）、行为只能来自公开文档、规范和黑盒观察、**绝不复制 GPL/AGPL 代码**。

**AI 时代让「独立实现」这件事的性质发生了两处变化**：

**第一，实现成本塌了。** 过去 clean room 需要一组人、一套严格的隔离流程（一组人读原代码写规格，另一组人只看规格写代码），这个成本本身就是一种过滤器，让 clean room 只被少数认真的团队采用。现在一个人加上 AI 就能在几天内产出一份「独立实现」。**过滤器消失了，但法律标准没变**，于是「独立实现」这个声称的可信度就变得难以评估。

**第二，可审计性下降了。** 判断一个实现是否真的独立，过去可以看提交历史、看换手记录、看文档。而 AI 生成的代码没有这种痕迹。**审查者能看到的只有最终代码和作者的自述。**

**注意这里的重点是：Rembrandt 的许可证合规看起来是干净的。** 它 GPL-3.0，上游也是 GPL-3.0，NOTICE.md 把 LibreRaw（LGPL-2.1）、MediaPipe（Apache-2.0）、Real-ESRGAN（BSD-3）、Lensfun 数据库（CC BY-SA 3.0）、RAWmakase（MIT）等各自的许可和归属都列了出来，还注明了引擎实现的是哪些**已发表方法**（sRGB、BT.2020、CIE CAT16、OkLab、暗通道先验、引导滤波、Fritsch–Carlson 单调三次插值）。

**这份 NOTICE 的细致程度，说实话超过了很多人类维护的老项目。** 所以真正的问题不是「它抄了没有」，而是：**当「独立实现」可以在一周内由 AI 批量产出时，我们靠什么来判断一份开放源代码的诚意。**

## 五、我的判断

**第一，把它当成一个可以现在就托付照片库的工具，是不理性的。** 10 天、单人、75 次提交、10 个 release，这是**一个野心很大的个人项目**，不是可以依赖的基础设施。**但它也不需要你现在就托付**——作者自己把不锁定数据做成了设计，这是它最值得信任的一点。

**第二，它最聪明的两个决定都跟「诚实」有关**：一是明确说「Ask in words」是**词表而不是语言模型**；二是主动在 Credits 里写明场景参照设计仿自 darktable。**在一个 AI 项目普遍夸大能力的时期，这种自曝短处的写法反而赢得了讨论空间**，HN 上那些尖锐的批评最后大多也承认「你的原图不会被锁住」这一点做得对。

**第三，它最大的未知数不是技术，是时间。** HN 上那位摄影师说的「它们全都边缘粗糙」很可能是对的，而**边缘粗糙这件事恰恰是时间才能磨平的**：4K 分数缩放的截图模糊、打印机协议栈的坑、某个镜头配置文件的偏差。这些都不在功能清单上，只在日常使用里。**而我们前几天刚写过那篇 Linux 桌面的评论，讲的正是同一件事**：功能列表可以几天做出来，粗糙边缘要几年。

**第四，也是最该记住的一点**：**这个项目真正的新闻价值不在 Rembrandt 本身，而在于它是「AI clean room 实现」这条新路的又一个样本。** 当一个人可以在 10 天里造出一份跨平台 Lightroom 替代品时，值得重新思考的**不是他做得对不对**，而是**我们用什么标准去评价、去审计、去信任这类软件**。

**最后留一个实用建议**：如果你好奇，最合理的用法是**只读不写**——装它、导入几张大尺寸 RAW、试试本地 AI 蒙版和超分辨率，但**不要把唯一一份照片库第一次接进去**。等它活过一年、有了第二个贡献者、积累起一批别人踩过的坑，再考虑正经使用。**而在这之前，你损失的最多只是半小时试用时间，不是你的照片。**

## 关键事实速查

| 项目 | 内容 |
|---|---|
| 定位 | 跨平台照片编辑器，Lightroom 替代品；无需账号、无订阅、无追踪、可自托管 |
| 许可 | **GPL-3.0-or-later**，并按第 7 条加入「允许应用商店分发」的额外许可 |
| 实测指标 | 建仓 **2026-09-29**；**75 次提交、1 名贡献者、78 stars**；**10 天内 10 个 release**（v0.3.10 于 10-09） |
| 技术栈 | JavaScript + **WebGL2/WebGPU 着色器**；**Rust/Tauri** 外壳；**LibRaw（C++）编译为 WASM** 解 RAW |
| ⚠️ 关键交代 | README Credits 承认**最早的原型移植了 darktable 的算法**，发布前替换为独立实现；作者在 HN 上确认场景参照设计仿自 darktable |
| 「Ask in words」 | 明确为「**一个词汇表，不是语言模型**」，在本地运行 |
| 本地 AI | MediaPipe（主体/景深/物体蒙版）、Real-ESRGAN（超分辨率）、KAIR/FFDNet（降噪） |
| 数据不锁定 | 原图从不移动或改写；编辑存为 **标准 XMP 副文件**，Lightroom/darktable 可读 |
| 供应链措施 | GitHub Actions 构建 + `SHA256SUMS` + **签名构建存证**（0.3.8 起）；更新器校验 SHA-256、不申请管理员权限 |
| ⚠️ 未签名 | 安装包**尚未代码签名**，macOS/Windows 首次运行会警告（Windows 的 SignPath 免费签名在申请中） |
| ⚠️ 参考系对比 | darktable：**1.3 万 stars / 1.4 千 forks**，多年积累；且其项目页明确写「不是 Lightroom 的免费替代品」 |
| HN 主要批评 | 边缘粗糙、单人维护的可持续性、UI「AI 感」、以及「需要问 Claude 才知道工作流受谁启发」 |
| 延伸议程 | AI clean room 逆向工程的法律挑战：实现成本塌了，但法律标准未变，可审计性下降 |

## 延伸阅读

- [thesnarkitecht/rembrandt](https://github.com/thesnarkitecht/rembrandt)
- [Hacker News 讨论（42 条评论）](https://news.ycombinator.com/item?id=50012199)
- [darktable](https://www.darktable.org/)
- [本站：Adobe 全家桶的免费替代：Photoshop→GIMP、Lightroom→darktable、Illustrator→Inkscape、Premiere→Kdenlive](/articles/2026-09-24_adobe-free-alternatives-switch/)
- [本站：「Linux 桌面永远成功不了」这句话，2026 年该改口了](/articles/2026-10-09_linux-desktop-not-expecting-experts/)
