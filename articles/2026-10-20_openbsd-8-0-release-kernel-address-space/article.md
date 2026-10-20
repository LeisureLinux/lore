---
title: "OpenBSD 8.0 发了：而这次最值得看的不是漏洞修复清单，是内核虚拟地址空间从 4G 跳到 512G"
date: 2026-10-20
slug: openbsd-8-0-release-kernel-address-space
tags: [OpenBSD, "8.0", 内核地址空间, pmap, DRM, Linux 6.18.53, Intel Arc, OpenSSH 10.6, LibreSSL 4.4.0, pledge, unveil, vmm, vmd, RISC-V, arm64 休眠, loongson 退役, YubiKey, 发布解读]
category: Linux/运维
author: FreeLAMP.com
original_source: "OpenBSD 官方 8.0 发布页（一手）"
original_author: "OpenBSD 项目（Theo de Raadt 等）"
original_date: 2026-10-20
original_url: "https://www.openbsd.org/80.html"
description: "OpenBSD 8.0 于 2026 年 10 月 20 日发布，是第 61 个版本。本文没有逐条罗列更新，而是挑出三条真正改变系统边界的改动：amd64 内核虚拟地址空间从 4G 提升到 512G（而这直接解锁了大于 4GB 显存显卡的映射）、arm64 首次支持休眠、以及 DRM 更新到 Linux 6.18.53 带来 Intel Arc A 系列支持。另附 OpenSSH 10.6 与 LibreSSL 4.4.0 的安全相关变化，和一条值得注意的退役：loongson 架构因 Clang 22 不再工作而被放弃。"
published: true
---

> 来源：[OpenBSD 8.0 官方发布页](https://www.openbsd.org/80.html)（**2026-10-20 发布**，第 **61** 个 OpenBSD 版本）
> 一手材料：本文所有条目均逐项摘自官方发布页原文。版本号、signify 公钥、"What's New" 全文均来自该页。**该页面是 OpenBSD 项目自己维护的发布说明，不是第三方转述。**
> 本文为**解读**。第一节关于「为什么 4G 是个天花板」的分析、第四节的判断是笔者补充的部分。

## 一句话结论

**发布页里最容易被跳过的是一行关于内存的数字，而我认为它是这次版本里唯一称得上「结构改变」的条目**：

> **「把 amd64 内核虚拟地址空间的大小从 4G 提升到 512G。」**

**（Raised the size of amd64 kernel virtual address space from 4G to 512G.）**

**这句话只有一行，而它的含义需要结合同页另一条才完整**：

> **「amd64 上增加的核虚拟地址空间允许映射超过 4GB 的显存。」**

**（Increased kernel virtual address space on amd64 allows mapping more than 4GB of VRAM.）**

**也就是说：这两条是同一件事的两面。而它解决的是一个具体的天花板问题**：**一台装了 8GB 或 16GB 显存显卡的 amd64 机器，在 8.0 之前跑 OpenBSD，显存最多只能用 4GB，因为内核没有足够的虚拟地址空间去映射更多。**

**而这恰好解释了同页另一条为什么重要**：

> **「在 `inteldrm(4)` 中加入对 Intel Arc A 系列（DG2/Alchemist）显卡的支持。」**

**Arc A 系列的显存是 6GB 到 16GB。而在 4G 内核地址空间下，这些卡跑不起来。所以这两条改动是配套的：先把地址空间扩到 512G，才谈得上支持大显存的卡。**

**我认为这个顺序揭示了 OpenBSD 这类系统改动的典型形态**：**一个看似枯燥的 pmap 常量调整，是某个具体硬件能不能用的前提条件。而发布页把这两条分开写、都没解释关联，所以读者很容易把前者当成无关紧要的内部整理。**

## 一、为什么 4G 是个天花板

**先把这一节讲清楚，因为它是理解整个版本的关键。**

**内核虚拟地址空间（kernel virtual address space，简称 KVA）是内核自己的「寻址预算」。** **内核在映射物理内存、映射设备寄存器（MMIO）、映射显存时，都要从这块地址空间里分配。**

**而 amd64 上这块空间原来是 4G。** **这意味着**：

- **一块 16GB 的显卡，它的显存只能被映射进来 4GB 以内的部分**；
- **而 4G 还要和内核的其他映射（直接映射、vmalloc、设备 MMIO）共享**，所以实际可用的还不到 4G。

**而「显存映射」这件事为什么必须经过内核地址空间？** **因为 GPU 驱动（`inteldrm(4)` 这类）需要在**内核上下文**里访问显存**：**比如做命令提交、读硬件状态、处理 GPU 页错误。这些操作不能用用户空间的指针，必须用内核虚拟地址。**

**所以「4G 上限」的真实含义是**：**任何显存超过约 3GB（减去其他映射后）的显卡，在 OpenBSD amd64 上都只能用到其中一小部分。** **而这在 2026 年基本等于「现代独显都不能用」。**

**提升到 512G 之后，这个约束消失了。** **而 `pmap(9)` 里的直接映射（direct map）现在被放在一个随机位置，这一条同页也写了**：

> **「`pmap(9)` 直接映射现在被放置在随机位置。」**

**我认为这一条值得单独说，因为它的意图很清楚**：**直接映射是内核访问物理内存的最直接路径，而它的地址固定就意味着「内核某块内存的虚拟地址可预测」。随机化它，是给内核漏洞利用增加难度。** **所以这两条改动合起来的效果是**：**地址空间大了 128 倍，而其中最关键的一段位置不再固定。**

**而 512G 这个数字本身也有讲究**：**它不是一个「刚好够用」的数字，是一个「留出足够增长空间」的数字**。**从 4G 到 512G 是 128 倍，这个幅度说明他们不是按当前需求算的，是按「下一代显卡可能要 24GB 或 32GB 显存」算的。**

## 二、arm64 第一次有了休眠

**同页里还有一条只有五个词的改动，而它的份量不小**：

> **「加入了休眠支持。」（Added hibernate support.）**（arm64 平台条目下）

**hibernate（休眠到磁盘）在 x86 上是很成熟的功能，而在 arm64 上长期缺失。** **原因是它需要把整块物理内存写进 swap，然后从一个几乎全新的固件状态恢复**，而这涉及**ACPI 状态保存、设备重新初始化、以及最麻烦的「恢复过程中的内存完整性」。**

**而发布页在下面几行给了这项工作真正的难度，我完整摘出来**：

> **「在 hibernate 解包磁盘镜像时，校验拷贝到 piglet 的块的大小。」**
> **「在读取块时，针对整数溢出校验磁盘镜像大小。」**
> **「在 unhibernate 读取 chunktable 时，防止镜像越界读取。」**
> **「在 unhibernate 之后清理 framebuffer。」**
> **「让 nvme(4) 休眠支持分配专用队列失败变成非致命。」**

**这几条全是「恢复路径上的防御性检查」。** **我认为这是 hibernate 这类功能最容易被低估的地方**：**写内存到磁盘很简单，难的是「读回来的时候，如果镜像被改过或损坏了怎么办」。**

**因为 hibernate 的镜像是一个**保存在磁盘上的、包含全部内存内容的文件**。而如果攻击者能改这个文件，那么在恢复时，内核就会把那块内存当成真的内存来用。** **「针对整数溢出校验磁盘镜像大小」和「防止镜像越界读取」这两条，就是在堵这个口子。**

**而「在 unhibernate 之后清理 framebuffer」这一条，我认为最实用**：**因为 framebuffer 在休眠前存着屏幕内容，而恢复后如果不清，你可能会在解锁界面上看到休眠前屏幕的残留。** **这是一个纯粹的隐私细节，而它出现在一份内核改动清单里，说明有人真的在意。**

## 三、DRM 追到 Linux 6.18.53，以及 Intel Arc

**图形栈的更新是**：

> **「把 `drm(4)` 更新到 Linux 6.18.53。」**

**这个数字值得注意，因为它意味着 OpenBSD 的图形栈落后 Linux 主线大约「一个开发周期」**：**Linux 6.18 是一个 2026 年的版本，而 OpenBSD 8.0 在同年 10 月就追到了 6.18.53（含 stable 修正）。** **对 OpenBSD 来说，这是一个相当紧的跟随节奏**，因为**它的 DRM 是把 Linux 的整套驱动框架移植过来，而这个移植不是「复制文件」那么简单**，需要适配 OpenBSD 的 bus_dma、中断模型、以及 pledge/unveil。

**而 Intel Arc A 系列（DG2/Alchemist）的支持，我在第一节已经讲了它和地址空间扩容的关联。**

**另有一条 Intel 相关的修正，我认为值得单独指出，因为它是一个真实的硬件怪癖**：

> **「绕过在部分 Alder Lake 系统上看到的 `inteldrm(4)` GuC 超时错误。」**

**（Workaround `inteldrm(4)` GuC timeout errors seen on some Alder Lake systems.）**

**GuC 是 Intel GPU 的微控制器固件，负责调度。而「timeout」意味着驱动等它回应超时了。** **而这在 Alder Lake 上是一个已知的、只出现在「部分系统」上的问题**，所以**处理方式是 workaround（绕过）而不是修复**。**我认为这个措辞的诚实度值得注意**：**它没有写「修复了 GuC 超时」，而是写「绕过在部分系统上看到的超时」。这两个表述的区别是：前者暗示找到了根因，后者承认只是让它不再卡住。**

## 四、安全侧的改动里，有三条我认为信号最强

**这一节我不逐条罗列（发布页那一节有几十条），只挑出三条能反映 OpenBSD 安全思路的。**

### 第一条：`unveil(2)` 现在管到了 man 工具链

> **「`unveil(2)` 现在限制 `man(1)`、`makewhatis(8)` 和 `man.cgi(8)` 的读写访问。」**

**`unveil` 是 OpenBSD 的「文件系统可见性」机制：一个进程可以声明「我只需要看到这几个路径」，之后它就无法访问其他任何路径，即使它被攻破。**

**而这条改动的意义在于它的目标**：**`man.cgi(8)` 是 OpenBSD 官网那个在线 man 页面的 CGI**。**也就是说：一个对公网开放的、把用户输入（man 页名）变成文件路径的程序，现在被限制在只能访问 man 相关的几个目录。**

**我认为这是 unveil 这个机制最典型的用法**：**它不是「检查输入是否合法」，而是「即使检查失败，这个进程也拿不到别的东西」。而这两层的差别在于：前者依赖「检查逻辑没有漏洞」，后者不依赖。**

### 第二条：`syspatch` 被加固了，而原因很值得玩味

> **「加固了 `syspatch(8)` 以对抗恶意脚本。」**

**（Hardened `syspatch(8)` against malicious scripts.）**

**`syspatch` 是 OpenBSD 的二进制补丁工具**，**它下载官方签名的补丁包并应用。** **而「对抗恶意脚本」这句话的意思是**：**它要应用的那些补丁脚本本身如果不怀好意（或者被篡改），不能让它们为所欲为。**

**而同页还有两条相关的**：

> **「`fw_update(8)` 现在检查本地 `SHA256.sig` 的签名。」**
> **「在 `fw_update(8)` 中，让 `tar(1)` 跳过预期位置之外的文件。」**

**「跳过预期位置之外的文件」这一条我特别想指出**，**因为它对应的是经典的压缩包路径穿越攻击**：**一个 tar 包里如果有 `../../etc/passwd` 这样的路径，解压时就会写到目录外面去。** **而 `fw_update` 是以 root 跑的**，所以这条尤其重要。

**我认为这三条放一起说明一件事**：**OpenBSD 对自己的「更新通道」也在做纵深防御。** **它没有假设「签名验证通过就万事大吉」，而是额外假设「即使包是签过名的，它解压出来的东西也不该越界」。**

### 第三条：OpenSSH 10.6 里那条「移除预认证攻击面」

**OpenSSH 10.6 的安全相关条目我看了一遍，其中这一条最值得说**：

> **「把一些关键的公钥解析和验证路径从预认证攻击面中移除。」**

**「预认证攻击面」（pre-auth attack surface）是我认为这次发布里最重要的一个概念。** **它的含义是**：**在认证完成之前，服务端要处理的那些代码，是任何能连上 22 端口的人都能触发的。所以这部分代码里每一个 bug 都是「未认证远程」级别的。**

**而「移除」这个动词意味着他们做的是**减少**而不是加固**：**把这些解析路径挪到认证之后去做。** **我认为这个方向比任何具体的漏洞修复都更有价值，因为它是**结构性的**：**少一段预认证代码，就少一整类预认证漏洞。**

**而同版本里另外两条也印证了这个方向**：

> **「禁止 在 `scp(1)` 的 `-O` 文件名里出现 NUL 字节。」**
> **「避免在通过命令行做 `ssh(1)` 下载时写入服务器控制的路径。」**

**第二条尤其值得注意**，因为**它是「scp/ssh 下载」这个场景里的一个经典不对称**：**你从服务器下载文件，而文件名是服务器给的。如果服务器给了一个绝对路径或 `../` 路径，而你直接用它写文件，那么服务器就决定了你本地写到哪里。** **「避免写入服务器控制的路径」正是修这个。**

### 另有三条「兼容性破坏」值得提前知道

**OpenSSH 10.6 专门列了一节「Potentially incompatible changes」，其中两条会影响实际使用**：

> **「对 `ssh-mldsa44-ed25519` 使用 IANA 分配的 codepoint，而不是 `@openssh.com`。」**
> **「让 `sshd_config(5)` 的 `DisableForwarding=yes` 覆盖 `PermitTunnel=yes`。」**

**第二条是一个行为改变**：**以前你如果两个都设了，可能是 `PermitTunnel` 赢；现在 `DisableForwarding` 赢。** **这对「我明明关了转发，为什么还能建隧道」这类困惑是一个修复，但也可能让某些依赖旧行为的配置突然不通。**

**而第一条涉及一个更前瞻的东西**：

> **「加入实验性的 `ssh(1)` 对复合后量子 `mldsa44-ed25519` 签名方案的支持。」**

**「实验性」（experimental）这个词很重要**：**它意味着这个方案还不能用于生产，但它已经能被试了。而选择 ML-DSA（Dilithium）作为后量子签名算法，与 NIST 在 2024 年标准化的方向一致。**

## 五、一条容易被忽略的退役：loongson 架构没了

**在「其他架构」一节里有一条**：

> **「退役了对 loongson 架构的支持（无法配合 Clang 22 工作）。」**

**（Retired support for loongson architecture (not working with Clang 22).）**

**我认为这条值得单独拿出来，因为它是这次发布里唯一一个「功能被删除」的条目，而理由很具体：不是因为没人用，是因为工具链跟不上了。**

**loongson 在这里指的是**龙芯早期的 MIPS 架构（`mips64el`），而不是后来的 LoongArch**。** **而这个退役的理由「not working with Clang 22」说明了一件事**：**OpenBSD 在推进编译器版本，而 loongson 的代码在新的 Clang 下编译不过了。**

**而它选择的是「退役」而不是「修」**，**这反映了一个现实**：**小众架构的维护成本，在编译器快速迭代的时代会被放大。** **因为每一次工具链升级，所有小众架构都要跟着改，而改的人往往只有一两个。**

**顺带说一句：同页里 luna88k（m88k 架构）反而**在改进**，有五条改动，包括「从 m88k 88100 数据通路中移除了非特权内核内存读写漏洞」。** **所以「小众架构」和「被退役的架构」不是同一个概念**：**m88k 有人维护，MIPS/loongson 没有。**

**而这个对比我认为挺有意思**：**一个 1980 年代的架构活了下来，而一个 2000 年代被寄予厚望的架构退役了。原因不是技术先进程度，是「有没有人在维护」。**

## 六、我的判断

**第一，这次发布最值得学的是「发布说明的写法」，而不是任何单个功能。** **OpenBSD 的发布页有一个很罕见的特点：它列出「没做成什么」和「绕过了什么」。** **比如「绕过在部分 Alder Lake 系统上看到的 GuC 超时」这一条，它诚实地承认这是 workaround 而不是 fix。而「loongson 因 Clang 22 不工作而退役」这一条，它直接把原因写出来，没有用「架构调整」这类模糊说法。** **我认为这种写法对用户的价值很高**，因为**它让读者能判断「这个改动对我意味着什么」**，**而不是让读者去猜「修复了若干问题」到底修了什么。**

**第二，那个 4G → 512G 的改动，是一个「前提性改动」的典型样本，而这类改动最容易被忽略。** **因为它的效果不是「多了一个功能」，而是「某个功能现在可以有了」。** **而发布页把「地址空间扩容」和「支持 Arc A 系列」写成两条独立的条目，中间隔着几行其他内容，所以读者很容易只看到后者，而不知道前者是它的前提。** **我认为这提示了一个阅读技术发布说明的方法**：**当看到「支持某个新硬件」时，去找同版本里「有没有什么基础设施被改了」，因为那往往才是真正的成本所在。**

**第三，`unveil` 扩到 `man.cgi` 这件事，是一个很好的「安全机制怎么落地」的样本。** **`man.cgi` 是一个对公网开放的 CGI，输入是 URL 里的 man 页名，输出是一个 HTML 页面。这类程序的传统做法是「仔细过滤输入」，而 unveil 的做法是「不管输入是什么，这个进程只能读这几个目录」。** **我认为后者的可靠性高一档，因为它不依赖「过滤逻辑完美无缺」。而这个思路在 OpenBSD 里已经用了很多年**：**从 `pledge` 到 `unveil`，一直是「限制能做什么」而不是「检查输入对不对」。**

**第四，关于「要不要升级」，我认为这次的理由比往常更充分一些，而理由不在安全侧。** **安全侧当然有大量 CVE 修复（libexpat、perl、libXfont、Xserver、nsd 各自都有），但那些在 errata 里也能拿到。** **这次只有 8.0 才有的东西是**：**amd64 上能映射超过 4GB 显存、arm64 上能休眠、RISC-V 上有了向量扩展和高级中断架构支持、以及 `vmm` 支持到 64 个 VCPU。** **而这几条里，对普通用户感知最强的是第一条和第二条。**

**而我对 arm64 休眠那条特别想说一句**：**它出现在一台 2026 年的 arm64 笔记本上才算真正有意义**（发布页提到 Samsung Galaxy Book4 Edge、HONOR MagicBook Art 14 Snapdragon 这两台设备的 ufshci 能在休眠后存活）。**也就是说：OpenBSD 的 arm64 支持已经细到「某台具体型号的笔记本能休眠了」。这个粒度说明它不是「能跑」，是「能用」。**

> **最后一个需要说明的事**：**你给我的两条链接指向同一个页面**。`t.co/Zjy2TdgZbd` 这个短链的响应体里就是一个 JS/Meta 跳转，目标是 `https://www.openbsd.org/80.html`：
>
> ```html
> <noscript><META http-equiv="refresh" content="0;URL=https://www.openbsd.org/80.html"></noscript>
> <script>window.opener = null; location.replace("https:\/\/www.openbsd.org\/80.html")</script>
> ```
>
> **所以我按一条材料处理。这个细节没什么信息量，但顺手说明一下，免得你以为我漏读了一条。**

## 关键事实速查

| 项目 | 内容 |
|---|---|
| **版本** | **OpenBSD 8.0**，**2026-10-20 发布**，**第 61 个 OpenBSD 版本** |
| **发布歌曲 / 封面** | **《The Simps on AI》**；**Artwork by yvaneht nioj and clanker** |
| **signify 公钥** | **base**：`RWSMSt0erHTctUxq2JDAgQRo64ztikp8JvQeiSPte3NZ0Geou0TkTEiE`；**fw**：`RWRjzXzC89s1iQC9P3xgcdeN6OUoJz9t7ggTY0xBb1W8PfeOzAdwod66`；**pkg**：`RWRspL7ERnSFIscdEvBwVySymWNopJ+CEZHbaB3IMJIt0bUXGBuIfUqC`；**syspatch**：`RWQAeCccO9yAASmUJSCJEW9C5WOP/GAsa5dhMtPPmb5pehzPO7EAmqhK` |
| ⭐ **最大的结构改动** | **「把 amd64 内核虚拟地址空间的大小从 4G 提升到 512G。」**（**128 倍**） |
| ⭐ **它解锁了什么** | **「amd64 上增加的核虚拟地址空间允许映射超过 4GB 的显存。」** |
| ⭐ **配套的硬件支持** | **`inteldrm(4)` 加入 Intel Arc A 系列（DG2/Alchemist）支持**；**Arc A 的显存 6–16GB，在 4G 上限下跑不起来** |
| **内核地址空间安全化** | **「`pmap(9)` 直接映射现在被放置在随机位置。」** |
| **amd64 其他** | **用 AES CPU 指令加速 swap 加密** |
| ⭐ **arm64 首次休眠** | **「加入了休眠支持。」**；**用 AES 指令加速 swap 加密**；**实现了 bounce buffers** |
| **arm64 休眠的防御性检查** | **校验拷贝到 piglet 的块大小**；**针对整数溢出校验镜像大小**；**防止 unhibernate 读取 chunktable 时越界**；**unhibernate 后清理 framebuffer**；**nvme 专用队列分配失败改为非致命** |
| **arm64 休眠的真机验证** | **`ufshci(4)` 能在 Samsung Galaxy Book4 Edge 和 HONOR MagicBook Art 14 Snapdragon 上熬过休眠** |
| **DRM** | **更新到 Linux 6.18.53** |
| **Intel 相关修正** | **绕过在部分 Alder Lake 系统上看到的 `inteldrm(4)` GuC 超时错误**（workaround，非 fix） |
| **RISC-V** | **通过 `elf_aux_info(3)` 的 AT_HWCAP/AT_HWCAP2 把可用的 CPU 扩展暴露给用户态**；**内核支持 'V' 向量扩展**；**支持 RISC-V Advanced Interrupt Architecture（`imsic(4)`、`aplic(4)`）**；**支持 Sstc 定时器扩展**；**bounce buffers** |
| **sparc64** | **改用 LLVM 工具链** |
| ⚠️ **架构退役** | **「退役了对 loongson 架构的支持（无法配合 Clang 22 工作）。」**（指早期 MIPS 龙芯，非 LoongArch） |
| **对照：luna88k 反而在改进** | **5 条改动，含「从 m88k 88100 数据通路中移除了非特权内核内存读写漏洞」** |
| ⭐ **pledge/unveil 扩展** | **`unveil(2)` 现在限制 `man(1)`、`makewhatis(8)`、`man.cgi(8)` 的读写访问** |
| **pledge 相关** | **修复 `vfs(9)` 里一处 pledge**；**为 `lldpd(8)` 加入 'mcast' pledge**；**收紧 `pledge_sockopt()` 对不同 socket 类型的 level/optname 检查** |
| ⭐ **更新通道加固** | **「加固了 `syspatch(8)` 以对抗恶意脚本」**；**`fw_update(8)` 现在检查本地 `SHA256.sig` 的签名**；**`fw_update(8)` 里的 `tar(1)` 跳过预期位置之外的文件**（防路径穿越，且它以 root 运行） |
| **OpenSSH** | **10.6** |
| ⭐ **OpenSSH 最重要的一条** | **「把一些关键的公钥解析和验证路径从预认证攻击面中移除。」** |
| **OpenSSH 安全修复** | **禁用 `ssh(1)` 的 LZ77 字典编码器以规避潜在侧信道泄漏**；**修复 `ChannelTimeout` 与 `RekeyLimit` 未被应用**；**让 `authorized_keys` 的 `restrict` 关键字正确作用于隧道转发** |
| **OpenSSH 兼容性破坏** | **`ssh-mldsa44-ed25519` 改用 IANA 分配的 codepoint（不再是 `@openssh.com`）**；**`DisableForwarding=yes` 现在覆盖 `PermitTunnel=yes`** |
| **OpenSSH 新增** | **实验性的复合后量子 `mldsa44-ed25519` 签名方案支持**；**`ssh-add -P` 跳过 PIN 输入**；**`ssh-keygen hexdump`**；**`ssh -Z user@host` 列出将尝试的公钥** |
| **OpenSSH 其他修复** | **`ssh(1)` 压缩载荷不得膨胀超过最大载荷长度**；**从 supercop ed25519 切到 libsodium**；**修复 `sshd(8)` 两处一字节越界读**；**避免 `ssh(1)` 客户端 realloc 后的 use-after-free** |
| **LibreSSL** | **4.4.0** |
| **LibreSSL 重要修复** | **修复 `openssl(1)`、`nc(1)`、`ocspcheck(8)` 在提供这些机制的宿主上静默跳过 `pledge(2)` 和 `unveil(2)`**；**ML-KEM 代码里把 `failure_key` 清零**；**修复 MSVC ARM64 优化器在常数时间大数代码里生成错误代码**；**`ecdh_compute_key()` 加入无穷远点检查**；**修复 `crl_cb()` 里 EXFLAG_CRITICAL 的错误处理** |
| **内核态 VMM** | **`vmm` 支持每 guest 最多 64 个 VCPU**；**guest VM 增加 x2apic 模式**；**`vmd(8)` 支持 checksum offload**；**MSI/MSI-X virtio 中断**；**修复 32/64 位 ELF 加载器在畸形 ELF 下的越界读** |
| **libexpat** | **更新到 2.8.4**（CVE-2026-66046、CVE-2026-76641、CVE-2026-76957） |
| **perl 修复** | **CVE-2026-57433**（Storable 有符号整数溢出）、**CVE-2026-57432**（pack/unpack 整数溢出）、**CVE-2026-13221**（正则匹配错误）、**Socket 2.041**（CVE-2026-12087 堆越界读） |
| **X 相关** | **LibXfont 修复 CVE-2026-56001/56002/56003**；**Xserver 修复 CVE-2026-55999/56000** |
| **nsd** | **修复 CVE-2026-12244/12245/12246/12490** |
| **sudo** | **1.9.17p2** |
| **材料说明** | **两条链接指向同一页面**：`t.co/Zjy2TdgZbd` 的响应体就是跳到 `openbsd.org/80.html` 的 JS/Meta 跳转 |

## 延伸阅读

- [Linux 7.3 发布：一万八千个提交、三千名开发者，而两篇报道各说一半](https://freelamp.com/articles/2026-10-19_linux-7-3-release-record-commits-ai-churn/)
- [TEE 的漏洞清单已经长得能写进一篇博客：而作者最狠的一句是「打断一台等于打断全部」](https://freelamp.com/articles/2026-10-19_tee-attestation-forgery-threat-model/)
- [为了让这台 128GB 的 RTX Spark 笔记本跑 Linux，她自己写了 ACPI 覆盖和触控板补丁](https://freelamp.com/articles/2026-10-19_rtx-spark-laptop-arch-linux-arm-nvidia/)
- [Libreboot 26.10 加入了 EDK2 支持，而它的反 AI 政策写进了一个机器可读的文件](https://freelamp.com/articles/2026-10-16_libreboot-2610-uefi-edk2-anti-ai-policy/)
- [OpenBSD 8.0 官方发布页（一手）](https://www.openbsd.org/80.html)
