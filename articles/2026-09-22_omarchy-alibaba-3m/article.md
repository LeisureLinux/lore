# 阿里云砸 300 万美元给 Omarchy：把 Arch 系桌面做成「理想 agentic OS」，默认调通 Qwen

> 原文：[Alibaba Contributing $3M USD To Omarchy To Work On Making "Ideal" Agentic OS](https://www.phoronix.com/news/Omarchy-Alibaba-3M)（Phoronix，Michael Larabel，2026-09-22）。本文由 LeisureLinux 翻译整理并加注解读；文内事实来自原文。

Omarchy 项目今天宣布：**阿里云（Alibaba Cloud）将向 Omarchy 基金会合计捐赠 300 万美元**，用于推进这个 Linux 发行版的开发，并把它打造成「理想的 agentic 操作系统」。

## 译文：钱怎么花

阿里云是**匹配 DigitalOcean 的承诺**——DigitalOcean 此前承诺未来三年每年给 Omacom 基金会 100 万美元；阿里云现以同等节奏（三年、每年 100 万）加入，合计就是 300 万。

作为合作的一部分，阿里云会帮着建立 **Omarchy China**，做本地 CDN、托管、线下聚会等中国本地化举措。

阿里云的官方表述，是要和 Omarchy 一起造一个「理想」的 agentic OS：

> 「我们要协作，把 Omarchy 做成那台电脑上理想的 agentic 操作系统——一个漂亮、有趣的 Linux 桌面，人和智能体可以在上面一起工作，且**所有者始终掌握控制权**。
> ……
> 这意味着开箱即用地为 Qwen 模型做调优，并努力与中国用户依赖的服务做完整集成。模型、操作系统、服务，应当从你开机那一刻起就协同工作。让你的电脑准备好和智能体协作，不该本身成为一个项目。」

更多细节见 Omarchy 今天的[公告](https://omarchy.org/news/2026/09/alibaba-cloud-joins-as-founding-corporate-patron/)。

## 解读：这是「agentic OS」叙事里最实在的一笔钱

**1. Omarchy 是什么：Arch 系、靠 dotfiles 复现、瞄准「开发者桌面」。**

Omarchy 是基于 Arch Linux 的桌面发行版，由 Omakub/Omarchy 作者（Jesse Vincent 系）推动，定位是「开箱即用的漂亮开发者 Linux 桌面」，核心卖点是用一套 dotfiles/脚本把 Hyprland/终端/编辑器/AI 工具链一次性铺好、可复现。它和我们的读者群高度重合——你在 Debian+niri 上折腾的那些桌面壳工程，Omarchy 想直接做成产品化的一键方案。

**2. 阿里云的真正意图：把 Qwen + 中文服务「焊」进桌面。**

「开箱即用地调优 Qwen 模型、与中文服务完整集成、开机即协同」——这不是泛泛赞助，而是把**国产大模型 + 国产云服务**做成桌面的默认层。对阿里云，这是把模型能力从「云端 API」下沉到「本地操作系统」的关键一步：用户一开机，agent 就在手边，且默认指向 Qwen 与阿里系服务。和华为「灵衢」、各类国产 OS 叙事是同一方向——**AI 能力下沉到 OS 层**。

**3. 「agentic OS」是真趋势，但「所有者掌握控制权」是必须盯的红线。**

文章原话强调「owner remains in charge」——人和 agent 协作、但人说了算。这恰恰是 agentic OS 最该被审视的点：当 OS 默认内置能联网、能调用服务、能替你执行动作的 agent，权限模型、可审计性、撤销机制就不再是「高级话题」，而是出厂默认。Omarchy 若真把 agent 做成桌面的操作系统级原语，它的权限/审计设计会比它的壁纸更重要——否则「理想 agentic OS」会滑向「默认给你装了个你控制不住的副驾」。

**4. 钱的意义：独立发行版拿到了多年期的生存弹药。**

DigitalOcean + 阿里云各三年百万级，是独立 Linux 桌面项目少见的「企业级长期赞助」。这能买到持续的维护人力与本地化（Omarchy China 的 CDN/托管/社区）。对比 Void Linux 因 AI 政策争议 maintainer 批量 orphan 100+ 包那类社区失血事件，Omarchy 这步走的是「基金会化 + 企业赞助」的稳路——对桌面 Linux 生态是健康信号。

一句话收尾：阿里云给 Omarchy 的 300 万，买的不是广告位，而是把 Qwen 与中文服务焊进一个开箱即用的 Linux 桌面的门票——「agentic OS」从概念视频，开始变成有多年期资金铺底的实体。
