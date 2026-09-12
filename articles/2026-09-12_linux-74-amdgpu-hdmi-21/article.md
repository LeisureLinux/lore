> 本文翻译自 Phoronix，作者 Michael Larabel，2026-09-12。
> 原标题：*Patches Ready For AMDGPU HDMI 2.1 Enabled By Default With Linux 7.4 With FreeSync, VRR & ALLM*
> 原文：<https://www.phoronix.com/news/Linux-7.4-AMDGPU-HDMI-2.1-Go>

## 事件概览

Linux 7.4 即将抵达一个纠缠 AMDGPU 用户多年的里程碑：**AMDGPU 内核显卡驱动的 HDMI 2.1 支持，这次是默认开启**。

过去数年，HDMI Forum 一直拒绝为 AMDGPU 的开源驱动实现放行 HDMI 2.1；直到今年早些时候事情出现转机——外界普遍猜测与 Valve 的介入有关——HDMI 2.1 补丁才开始陆续浮出水面。在即将到来的 Linux 7.4 周期里，这批工作的主体将落地，并且默认启用。

时间线简单复盘一下：

- **今年 5 月初**：AMDGPU 的 HDMI 2.1 FRL（Fixed Rate Link，固定速率链路）补丁首次出现，用于在 HDMI 上承载更高分辨率与刷新率；随后 AMD 确认正在推进完整的 HDMI 2.1 实现。
- **Linux 7.2**：HDMI 2.1 FRL 已合入 AMDGPU 驱动，但当时**默认关闭**。
- **此后数月**：其它 HDMI 2.1 相关补丁陆续公开。
- **Linux 7.4**：这批工作要么全部、要么占压倒多数都将合入，且默认开启。

## 这次 DRM-Next 拉取里有什么

昨日提交到 DRM-Next、面向 Linux 7.4 的最新 AMDGPU 特性拉取请求，把 HDMI 2.1 的关键能力一次性补齐：

| 能力 | 说明 |
|------|------|
| **HDMI 2.1 FreeSync** | AMD 自适应同步，终于进主线 AMDGPU 驱动 |
| **HDMI 2.1 VRR** | 可变刷新率，对玩家意义最大 |
| **HDMI 2.1 ALLM** | Auto Low Latency Mode，自动低延迟模式：部分显示器/电视可借此获得更低延迟的游戏体验 |
| **FRL 默认启用** | 这段代码最初默认关闭，直到 VRR 等工作就绪、且为避免任何可能的用户体验回退才迟迟未开 |

对玩家而言，VRR 与 FreeSync 终于进入主线内核的 AMDGPU 驱动，是实打实的利好。

## 顺带的硬件更新

这一拉取请求还带来了面向未来 AMD 显卡的更新：

- **GFX12.1 图形引擎**
- **DCN 6 显示引擎**
- **SMU 15 IP**

以及其它修复与改进。

## 时间线

- **合并窗口**：Linux 7.4 的合并窗口将在 10 月下旬开启，具体取决于 Linux 7.3 稳定版何时就绪。
- **正式发布**：若进展顺利，Linux 7.4 可能在 2026 年底或 2027 年 1 月初面世——在这个被 AI 催热的繁忙补丁世界里，节奏仍未完全确定。

无论如何，AMDGPU 的 HDMI 2.1 特性补丁如今已全部对齐 Linux 7.4，对 Linux 爱好者与玩家来说，这会是一份不错的「圣诞礼物」。

## 解读：为什么这件事值得记一笔

### 1. 一场持续多年的「规范战争」的阶段性胜利

HDMI Forum 长期拒绝为开源 Linux 驱动提供 HDMI 2.1 规范许可，理由是开源实现会暴露 HDMI 技术细节。AMD 早在 2021 年就做过开源实现，却被 HDMI Forum 阻止发布；Valve 也曾就此与 HDMI Forum 交涉未果。

转机出现在 2026 年：Valve 与 AMD 合作推进的 HDMI 2.1 FRL 补丁自 5 月起陆续进入内核邮件列表。换句话说，开源社区不是等来了规范，而是靠工程实现把功能先做了出来。

### 2. Valve 的 Steam Machine 是直接受益者

HDMI 2.1 的限制同样直接牵动 Valve 的 Steam Machine。Valve 此前确认硬件本身支持 HDMI 2.1，但 SteamOS 受限于底层 AMD 开源图形栈，无法完整暴露特性。

今年 6 月，Valve 工程师 Pierre-Loup Griffais 向 DigitalFoundry 确认，Steam Machine 的 HDMI 2.1 FRL 工作已完成，当前软件栈已启用 HDMI 2.1 VRR，不仅支持 FreeSync 显示器，也支持 HDMI Forum 的 VRR 显示器；未来更新后还将支持 4K@240Hz 的 DSC（Display Stream Compression，显示流压缩）输出。不过 Steam Machine 产品页目前仍标注 HDMI 2.0，新驱动尚未部署到 SteamOS。

### 3. NVIDIA 开源驱动（Nouveau）也在赶进度

同一波 DRM-Misc-Next 里，Nouveau 也在为 Linux 7.4 准备 HDMI 2.1 DSC：为 Blackwell GPU 支持 2.147 GHz 像素时钟（当前未压缩的 HDMI FRL 仅约 1.78GHz，DSC 接好后将触及更高上限），并首次默认启用 Nouveau 的原子模式设置（atomic mode-setting）。

此外，AMD 的 EDID 解析器修复也会进 7.4——部分显示器厂商只在 AMD VSDB（Vendor-Specific Data Block）里声明 VRR 能力，而通用 DRM EDID 解析器此前未处理某些版本的 AMD VSDB，导致 VRR 能力识别不全，这一处将在 7.4 修正。

### 4. 对桌面 Linux 与信创场景的意义

对于跑在 AMD 平台上的 Linux 桌面——包括信创场景下的云桌面、瘦客户机接大屏电视——HDMI 2.1 默认开启意味着高刷、低延迟、可变刷新率终于不再需要手动开内核参数，或等发行版单独 backport。过去这块一直是 Windows 阵营的体验优势，Linux 7.4 将明显缩小差距。
