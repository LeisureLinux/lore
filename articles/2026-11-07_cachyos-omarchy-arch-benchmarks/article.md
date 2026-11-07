---
title: "CachyOS 与 Omarchy 4.5 跑分：图形谁吃亏、编译谁占便宜"
date: 2026-11-07
slug: cachyos-omarchy-arch-benchmarks
category: 技术/解读
author: FreeLAMP.com
original_source: "一手核对：Phoronix《Arch Linux vs. CachyOS vs. Omarchy 4.5 Performance Benchmarks》（Michael Larabel，2026-11-06）全 7 页的逐页结论与测试环境说明 ＋ Omarchy 4.5 与 CachyOS 内核版本的事实核对"
original_date: 2026-11-06
original_url: "https://www.phoronix.com/review/cachyos-omarchy-benchmarks"
description: "本文解读 Phoronix 于 2026 年 11 月 6 日发布的《Arch Linux vs. CachyOS vs. Omarchy 4.5 Performance Benchmarks》全 7 页结果，并把它从跑分流水账整理成「谁在什么地方吃亏、为什么」。测试环境是同一台 Framework Desktop 机器（AMD Ryzen AI Max+ 395「Strix Halo」、64GB 内存、集显 Radeon 8060S、2TB WD_BLACK SN7100 NVMe），三个系统分别是 Arch Linux（通用 archinstall + KDE Plasma）、CachyOS（默认安装并更新）、Omarchy 4.5（原生安装）。**关键前提**：CachyOS 跑的是 Linux 7.3，而 Omarchy 和 Arch 上游当时都还在 7.2；三个系统都是 GCC 16.2；**而 Omarchy 默认用 performance 性能配置，Arch 和 CachyOS 在这台笔记本上默认是 balanced** —— 这个差异是解读很多结果的关键。**逐项结果**：图形测试里 CachyOS 与 Arch 用 Mesa 26.2 表现相当，**Omarchy 明显落后**，原因是它用 Hyprland 而另外两者用 KDE Plasma Wayland，Xonotic 这类第一人称射击也最慢；压缩与编解码里 **Omarchy 因 performance 配置而在多数 Zstd 测试和 OpenAPV 编码上小幅领先**，SVT-AV1 是 CachyOS 拿下，**x265 编码 CachyOS 最快**；**编译与科学计算是 CachyOS 的强项** —— 7-Zip、各类开源项目构建时间、GNU Octave 都最快，PyTorch 也是它但优势很薄；数据库方面 Omarchy 在 ClickHouse 上小幅领先、PostgreSQL 结果混杂、**Blender 5.2 CPU 渲染三者无明显差异**；脚本侧 CachyOS 的 Python 拿下多场胜利，**其 PHP 包的优化程度明显比另两者激进**；浏览器里 CachyOS 与 Omarchy 咬得很紧，**Llama.cpp 三者无显著差异**。**120 多项测试的几何平均结果是 CachyOS 第一，但只是略微领先**。本文的落点：CachyOS 的领先几乎全部来自「预编译优化过的包」（Zen 4+ 优化包、激进优化的 PHP、更好的编译器配置），Omarchy 的落后几乎全部集中在图形栈（Wayland 合成器差异），而在这台机器上默认性能配置的差异被放大了。"
published: true
---

> 原文：Phoronix《Arch Linux vs. CachyOS vs. Omarchy 4.5 Performance Benchmarks》（Michael Larabel，2026-11-06）
> 原文链接：<https://www.phoronix.com/review/cachyos-omarchy-benchmarks>
>
> 本文依据 Phoronix 全 7 页的逐页结论与测试环境说明。

## 一、这不是三方横评，是两种不同的赌注

先把结论摆前面：**120 多项测试的几何平均，CachyOS 第一，但只是略微领先。** 而这个「略微领先」的分项构成，比排名本身有意思得多。

因为这三者其实在做三种不同的选择：

| | CachyOS | Omarchy 4.5 | Arch Linux 上游 |
|---|---|---|---|
| 定位 | 性能优先的发行版 | 面向 Arch 理念的「Opinionated」桌面 | 基准参考系 |
| 内核 | **Linux 7.3** | Linux 7.2 | Linux 7.2 |
| 桌面 | KDE Plasma Wayland | Hyprland | KDE Plasma Wayland |
| 编译器 | GCC 16.2 | GCC 16.2 | GCC 16.2 |
| 默认性能配置 | **balanced**（这台机器上） | **performance** | **balanced**（这台机器上） |
| 预编译优化包 | **有大量（Zen 4+ 优化包等）** | 默认 | 无 |

**第三行和第五行是解读所有结果的关键。** 在解读具体项目之前，得先把这两条放进来。

### 测试环境

同一台 **Framework Desktop** 机器：

- AMD Ryzen AI Max+ 395「Strix Halo」
- 64GB 内存
- 集显 **Radeon 8060S Graphics**
- 2TB WD_BLACK SN7100 NVMe SSD

安装方式：Arch 用通用 archinstall 装 KDE Plasma；CachyOS 按默认安装并更新；Omarchy 4.5 也是原生安装。

**最后一条差异值得单独强调**：CachyOS 明确「包含大量开箱即用的优化，来自 Zen 4+ 优化包和其它调优」—— 这是它很多项目领先的直接原因。

而 **performance 与 balanced 的默认差异**，在 Phoronix 自己的推测里也出现了（见第三节）。

## 二、图形：Omarchy 唯一明显吃亏的地方

这是全篇里**差距最清晰、也最容易被误读**的一项。

**结论：CachyOS 与 Arch Linux 表现相当（都用 Mesa 26.2，跑 Radeon 8060S）；Omarchy 明显落后。**

Phoronix 的原话：

> 对于吃性能的 GravityMark OpenGL 与 Vulkan 图形测试，CachyOS 和 Arch Linux 表现相当（Mesa 26.2，Strix Halo 的 Radeon 8060S）。**Omarchy 是那个异常值**，在它的 Hyprland 环境下比另外两者慢。

> The Xonotic first person shooter was also the slowest on Omarchy 4.5. This was similar in other graphics tests too, presumably due to some overhead or lack of optimizations compared to KDE Plasma Wayland on Arch Linux and CachyOS.

（Xonotic 这个第一人称射击游戏在 Omarchy 4.5 上也是最慢的。**在其它图形测试里情况也类似**，推测是相比 Arch Linux 和 CachyOS 上的 KDE Plasma Wayland，存在一些额外开销或优化缺失。**这是全文我唯一想原样保留的英文** —— 因为它把「推测」两个字写在了明处，而不是替读者把话说满。）

**这里的归因很值得注意**：Phoronix 把原因指向**桌面环境**（Hyprland vs KDE Plasma Wayland），而不是驱动、内核或 Mesa 版本。

而这三者用的是**同一块硬件、同一个 Radeon 8060S、同一代 Mesa（26.2）**。所以变量只有两个：**合成器** 和 **内核版本**（7.3 vs 7.2）。

**这意味着对 Omarchy 用户来说，真正的结论不是「Omarchy 慢」，而是「在图形密集型负载下，Hyprland + Wayland 这条路线的开销比 KDE Plasma 明显」** —— 而这个差距是**架构选择**带来的，不是 bug。

值得注意的是：Phoronix 用的措辞是「推测是」（presumably）—— **它没有做拆解来确认这究竟是合成器本身的开销，还是 KDE Plasma 那边有额外优化。** 这个区分对读者是有意义的：如果是前者，那 Omarchy 追平的路径是「等 Hyprland 优化」；如果是后者，那 CachyOS/Arch 的图形优势里有一部分来自 KDE 的额外优化，而不只是「Hyprland 慢」。

## 三、压缩与编解码：Omarchy 靠默认配置扳回一城

**结论：Omarchy 在多数 Zstd 测试和 OpenAPV 编码上小幅领先；SVT-AV1 被 CachyOS 拿下；x265 编码 CachyOS 最快。**

Phoronix 的原话：

> 由各操作系统自带的 Zstd 在大多数 Zstandard 压缩测试中为 Omarchy 带来小幅领先，**原因可能是它默认使用 performance 配置，而另外两者是 balanced**。

> 同样，**Omarchy 4.5 在开箱即用的 OpenAPV 视频编码上最快**。

> CachyOS 拿下了 SVT-AV1 编码这一项，而 Omarchy 在默认配置下也拿下了一些额外项目。

> **CachyOS 在 x265 视频编码性能上最快。**

**这一页最能说明「基准测试的结果有多依赖配置」。**

Zstd 那一项的领先，Phoronix 自己给出的解释是**默认性能配置的差异** —— 而不是「Omarchy 打包了更好的 zstd」。

**换句话说：如果 Arch 和 CachyOS 也默认用 performance，CachyOS 在这一项的领先大概率会缩小甚至反转。**

而这引出一个方法论上的要点：**这篇测试测的是「默认安装后的体验」，而不是「某个软件包的上限」。** 两者都不是错的，但读者要清楚自己看的是哪一个。

而 x265 那一项就完全是另一回事了 —— 那是 **CachyOS 的包本身更优**（Phoronix 在第 6 页明确说 CachyOS 的 PHP 包「优化程度明显更激进」，x265 大概同理）。

## 四、编译与科学计算：CachyOS 的真正主场

**结论：7-Zip、各类开源项目构建时间、GNU Octave 都是 CachyOS 最快；PyTorch 也是 CachyOS，但优势很薄。**

Phoronix 的原话：

> 用各系统自带的 7-Zip，**CachyOS 交付了最快的压缩性能**。

> **在各类开源代码库的构建时间上，CachyOS 最快。**

> CachyOS 和 Omarchy 在 Numpy 上都比上游 Arch Linux 略快。

> **PyTorch 在 CachyOS 上最快，尽管优势非常微小。**

**「各类开源代码库的构建时间」这一项，是最贴近开发者的指标** —— 因为对每个用 CachyOS 的人来说，构建时间就是每天要付的成本。

而这一项领先的原因，几乎可以直接从前面的信息推出来：**CachyOS 打包了为 Zen 4+ 优化的二进制包**，编译型软件装上去就是更快的机器码。

**Numpy 那一条也印证了这一点**：CachyOS 和 Omarchy 都比上游 Arch 快 —— **因为「自己构建过」比「直接用发行版二进制」要快**，而这两个系统都提供（或者倾向提供）更针对本机优化的构建。

## 五、数据库与渲染：这一页几乎打平

**结论：Omarchy 在 ClickHouse 上小幅领先；PostgreSQL 结果混杂；GNU Octave 是 CachyOS 最好；Blender 5.2 CPU 渲染三者无明显差异。**

Phoronix 的原话：

> **Omarchy 在 ClickHouse 数据库服务器上有小幅领先。**

> 看 PostgreSQL 性能时，**结果是混杂的**。

> 各系统自带的 GNU Octave 在 **CachyOS 上表现最好**。

> **在这三个基于 Arch Linux 的操作系统上，Blender 5.2 的 CPU 渲染性能没有任何实际差异。**

**「PostgreSQL 结果混杂」和「Blender 无明显差异」这两条，是全篇最有价值的「负面信息」。**

它们说明的是：**在这类负载上，发行版之间根本没有可感知的差别** —— 而这类项目恰恰是很多人在选发行版时最关心的（数据库服务器、3D 渲染）。

**换句话说，「换个发行版能快多少」这个问题，在很多场景下的答案是「差不多」。**

而 ClickHouse 那一条是 Omarchy 唯一的数据库胜出 —— 有意思的是，ClickHouse 是**服务端**（不是客户端库），而 ClickHouse 在 Arch 系发行版里往往是用官方仓库的预编译包而非自行构建。**这提示 Omarchy 在「服务端软件」这一类的选择上更贴近上游原版** —— 而对服务端软件来说，「用上游原版」通常就是「性能最好」，因为上游自己最清楚怎么编译自己。

## 六、脚本：PHP 是 CachyOS 最明显的优势项

**结论：CachyOS 的 Python 拿下多场胜利；其 PHP 包的优化程度明显比 Omarchy 和 Arch 激进。**

Phoronix 的原话：

> **CachyOS 在 Python 性能上相对 Omarchy 和 Arch Linux 拿下一批胜利。**

> **CachyOS 的 PHP 包也比 Omarchy 或 Arch Linux 优化得更激进。**

**「更激进」这个词是 Phoronix 自己的判断**，而不是「更快」。

那么「优化得更激进」是什么意思？在解释器型语言上，它通常指的是**更激进的编译选项、更深的 profile-guided optimization、或者更激进的 opcode 优化**。

**而这带来一个值得想清楚的问题**：CachyOS 的 PHP 更快，但也可能意味着它的 PHP 在某些边缘场景下兼容性更差（因为它偏离上游构建配置更多）。

**跑分领先和「默认行为最接近上游」这两件事，在解释器型语言上往往是此消彼长的。** 这不是缺点，只是**你在为谁优化**的选择。

## 七、浏览器与本地推理：Firefox 咬得很紧，Llama.cpp 三家打平

**结论：CachyOS 与 Omarchy 在 Firefox 基准测试里争第一；Llama.cpp 三者无显著差异。**

Phoronix 的原话：

**在这台 AMD Strix Halo 桌面上，CachyOS 和 Omarchy 在 Firefox 网页浏览器基准测试里争第一。**

> **各操作系统提供的 Llama.cpp 包之间没有任何显著差异。**

**Llama.cpp 三家打平这一条特别值得注意。**

Llama.cpp 是本地跑大模型最热门的运行时，而且它**极度依赖具体的 CPU 指令集优化**（AVX-512、AVX2 等）以及编译参数。

**在这种「优化空间极大」的软件上三者打平，说明这台机器上的差异已经被别的东西吃掉了** —— 而最可能的解释就是**那个 performance 与 balanced 的默认配置差异**。

**这是一个很好的对照**：CachyOS 的「预编译优化包」优势（第七节那个激进 PHP）在 Llama.cpp 上完全没体现出来。为什么？因为 Llama.cpp 是**从源码编译**的（或者发行版自己编译），而不是发行版预编译给你一个二进制。

**所以「发行版的预编译优化」这条路，只对「发行版愿意替你编译」的软件有效。** 对那些社区自己编译、或用户自己编译的东西，CachyOS 的优势就不存在了。

## 八、把所有结果摆成一张表

| 类别 | 第一 | 第二 | 第三 | 备注 |
|---|---|---|---|---|
| 图形（GravityMark/Vulkan、OpenGL、Xonotic） | CachyOS = Arch | — | **Omarchy 明显落后** | 归因指向 Hyprland vs Plasma Wayland |
| Zstd 压缩 | **Omarchy** | — | CachyOS / Arch | 归因指向默认 performance vs balanced |
| OpenAPV 编码 | **Omarchy** | — | — | 开箱最快 |
| SVT-AV1 编码 | **CachyOS** | — | — | |
| x265 编码 | **CachyOS** | — | — | |
| 7-Zip | **CachyOS** | — | — | 各系统自带版本 |
| 源码构建时间 | **CachyOS** | — | — | 各类开源项目 |
| Numpy | CachyOS = Omarchy | — | Arch | 两者均略快于上游 |
| PyTorch | **CachyOS** | — | — | 优势很薄 |
| ClickHouse | **Omarchy** | — | — | 小幅领先 |
| PostgreSQL | 混杂 | — | — | 结果分散 |
| GNU Octave | **CachyOS** | — | — | |
| Blender 5.2 CPU 渲染 | 三者无差异 | — | — | |
| Python | **CachyOS** | — | — | 拿下多场胜利 |
| PHP | **CachyOS** | — | — | 优化更激进 |
| Firefox | CachyOS ≈ Omarchy 争第一 | — | — | |
| Llama.cpp | 三者无差异 | — | — | |
| **120+ 项几何平均** | **CachyOS** | Omarchy 4.5 | Arch Linux | 略微领先 |

## 九、这篇测试该被怎么读

### 它测的是「默认安装」，不是「上限」

这是最需要先说清的一点。CachyOS 的领先几乎全部来自**它预编译给你什么**，而不是「Arch 上游做不到」。

**你如果自己编译，拿到的就是上游水平** —— 而第七节那个 Llama.cpp 三家打平，正是这个论断的现成证据。

### 它测的是一台机器的一个配置组合

**这台机器的默认性能配置是 balanced**（Arch 和 CachyOS）**而 Omarchy 是 performance**。

这意味着：

- **对 CachyOS 不公平的地方**：它被限制在了 balanced，而它的包本来就是为 performance 准备的；
- **对 Omarchy 有利的地方**：它拿到了 performance 配置。

**如果 Arch 和 CachyOS 也默认 performance，压缩和编解码那一页的结果很可能会变。**

而 Phoronix 自己的推测（Omarchy 在 Zstd 上领先「原因可能是它默认用 performance」）已经承认了这一点，只是没有做对照实验。

### 它没有回答「值不值得」

**这是所有跑分文章的通病，也是这篇最该被指出的地方。**

CachyOS 领先的方式（预编译优化包、激进的 PHP 构建）**有代价**：

- 那些优化包是你**用不到那个 CPU 型号时的浪费**（Zen 4+ 优化包在非 Zen 4+ 机器上可能反而是负担）；
- 激进的构建配置可能偏离上游，**在边缘场景下兼容性更差**；
- 而「构建时间快」这个优势，**在你自己构建时就消失了**。

**而 Omarchy 的图形落后，代价是「你选了 Hyprland」。** 如果你不在乎那 5–10% 的图形开销，换来的是一套完整的 Opinionated 桌面体验 —— 这笔账 Phoronix 没算，因为它只测性能。

### 唯一可以确定的事

**在这台机器上、这三个默认安装之间，性能差异的量级是「个位数百分比」，而不是「翻倍」。**

120 多项测试，几何平均，**CachyOS 只是略微领先。**

**这个结论本身就是最有价值的一条** —— 因为它意味着：**选发行版时，性能通常不该是决定性因素。**

真正值得拿去做决策的，是那些**明确打平的项目**：PostgreSQL、Blender CPU 渲染、Llama.cpp —— **在这些地方，换发行版一分钱收益都没有。**
