---
title: "TrueNAS 一次更新了三件事：Proxmox 插件、27 RC.1，以及一个让备份服务器消失的认证"
date: 2026-10-21
slug: truenas-2026-proxmox-plugin-27rc1-veeam-ready
tags: [TrueNAS, Proxmox, Proxmox VE, Veeam, Veeam Ready Appliance, All-In-One Virtualized, TrueNAS 27, RC.1, OpenZFS, "2.4", Linux "6.18", Fusion Pools, TrueSearch, WebShare, Object Interface, S3, NVMe-oF, NVMe/TCP, iSCSI, NFS, vSphere, 虚拟化, 备份, 存储]
category: 存储/虚拟化
author: FreeLAMP.com
original_source: "TrueNAS 官方三篇博客（Proxmox 插件 / 27 RC.1 功能集 / Veeam Ready All-In-One）+ 官方论坛 RC.1 发布帖"
original_author: "iXsystems / TrueNAS 团队"
original_date: 2026-09-11
original_url: "https://www.truenas.com/blog/truenas-27-rc1-feature-set/"
description: "2026 年 9 到 10 月，TrueNAS 连着发了三件事：一个直接把 zvol 变成 Proxmox 存储的插件、把 TrueNAS 26 改名为 27 的 RC.1、以及一个让「备份服务器」这个盒子可以消失的 Veeam 认证。这篇逐条解读，并指出官方博客没写、但论坛里已经有人踩到的那个坑：RC.1 的 NVMe/TCP target 有一个 MDTS 回归，会让 Proxmox 卷被切到只读。"
published: true
---

> 来源：本文所有技术细节都回到一手材料核对：[TrueNAS Proxmox Plugin 发布博客](https://www.truenas.com/blog/truenas-proxmox-plugin)（2026-09-11）、[TrueNAS 27 RC.1 功能集博客](https://www.truenas.com/blog/truenas-27-rc1-feature-set/)（2026-10-05）、[Veeam Ready All-In-One 认证博客](https://www.truenas.com/blog/truenas-veeam-vsa-all-in-one-ready/)（2026-09-22）、[TrueNAS 27 改名说明](https://www.truenas.com/blog/truenas-27-is-here/)、[官方论坛 RC.1 发布帖](https://forums.truenas.com/t/truenas-27-0-0-rc-1-is-now-available/68265)（含 20 条社区反馈）。
> 本文为**技术解读**。第五节（三件事之间的关联）、第七节（我的判断）是笔者补充的部分。

## 一句话结论

**这三件事看起来是三个独立的产品更新，实际上指向同一个方向：iXsystems 在把 TrueNAS 从一个「你挂载上去的存储设备」变成一个「你的基础设施里的一层」。**

**三条线索分别是：**

1. **Proxmox 插件**：**把「存储管理」从 TrueNAS 的网页界面搬进了 Proxmox 的创建虚拟机流程**。**磁盘不再是你手工切出来的 LUN，而是 Proxmox 要一块、TrueNAS 就自动建一块。**
2. **TrueNAS 27 RC.1**：**把搜索、S3 接口做进平台本身**。**S3 那条尤其关键，因为「每个 bucket 就是一个 ZFS dataset」。**
3. **Veeam Ready All-In-One (Virtualized) 认证**：**让 Veeam 备份服务器本身变成一个跑在 TrueNAS 上的虚拟机，而它的备份仓库是同一台机器上的 zvol。** **「那个需要单独采购、加固、打补丁的备份服务器」消失了。**

**而这三件事拼起来是一个完整的故事**：**存储平台开始吞掉它周边的东西（虚拟化管理、对象存储、备份服务器）。**

**⚠️ 而我也要提前说一个官方博客没写的东西**：**RC.1 的 NVMe/TCP target 有一个 MDTS 回归，会让 Proxmox 卷在 I/O 错误后被切成只读。** **社区已经有人在论坛上报了，并给出了 udev 规则的 workaround。** 详见第六节。

## 术语速查

| 缩写 / 术语 | 含义 |
|---|---|
| **TrueNAS** | iXsystems 的存储操作系统，基于 **OpenZFS** |
| **Proxmox VE** | 开源的虚拟化平台（KVM + LXC），**VMware 迁移的主要落脚点之一** |
| **zvol** | **ZFS 的块设备卷**（`ZFS` 原生的块存储），可以被当成裸盘用 |
| **iSCSI** | 把块设备通过网络暴露出去的协议，**LUN 就是「逻辑单元号」，一块可挂载的虚拟盘** |
| **NVMe-oF / NVMe/TCP** | NVMe over Fabrics，**把 NVMe 协议跑在网络上**（TCP 版本不需要特殊网卡） |
| **NFS** | 网络文件系统，**文件级**共享 |
| **SMB** | Windows 文件共享协议 |
| **QCOW2** | QEMU 的写时复制磁盘格式 |
| **COW** | Copy-on-Write，写时复制。**NFS 上的快照就是靠它实现的，而这也是它慢的原因** |
| **HA** | High Availability，双控制器高可用 |
| **VSA** | **Veeam Software Appliance**，Veeam 的加固 Linux 一体机镜像 |
| **Veeam B&R** | Veeam Backup & Replication |
| **Immutable / Object Lock** | 不可变存储 / 对象锁，**防勒索软件删备份的关键机制** |
| **TrueNAS Connect** | iXsystems 的云连接服务，**TrueSearch / WebShare 依赖它** |
| **MDTS** | Maximum Data Transfer Size，**NVMe 的「单次传输最大尺寸」参数** |
| **special vdev** | **ZFS 的特殊设备组**，用来放元数据和小文件，加速随机访问 |
| **SLOG / ZIL** | ZFS 的日志设备（ZIL 是意图日志，SLOG 是它的独立设备） |
| **RAIDZ** | ZFS 的软件 RAID，**类似 RAID-Z1/Z2/Z3** |
| **LXC** | Linux 容器 |

## 一、Proxmox 插件：把「切 LUN」变成「点一下」

**先看官方博客的开头一句，它把整个卖点压成了六个字**：

> **「You click the button. TrueNAS builds the disks.」**
>
> **「你点那个按钮。TrueNAS 建磁盘。」**

### 它要解决什么

**官方对现状的描述很准确**：

> **「Proxmox VE has become one of the default landing spots for teams leaving VMware, and TrueNAS is already a common storage layer underneath those clusters. Most of those deployments run today on NFS or hand-cut iSCSI LUNs, and both are legitimate, well-worn ways to connect the two platforms.」**
>
> **「Proxmox VE 已经成为离开 VMware 的团队默认的落脚点之一，而 TrueNAS 已经是那些集群下面常见的存储层。**大多数这类部署今天跑在 NFS 或者手工切的 iSCSI LUN 上**，两者都是合理、久经使用的连接方式。」**

**而两条路的代价，官方引的是 Proxmox 自己的文档，这一点我认为很聪明**：

> **「Proxmox's own storage docs are upfront about the challenge: on NFS, snapshots run through QEMU Copy-on-Write files, and can block the VM while they're happening, and on large disks can take 'several minutes, or in extreme cases, even hours.'」**
>
> **「Proxmox 自己的存储文档对这个问题很坦率：在 NFS 上，快照要通过 QEMU 的写时复制文件实现，在执行时会阻塞这台虚拟机，而在大磁盘上可能花上『几分钟，极端情况甚至几小时』。」**

> **「Hand-cut iSCSI LUNs avoid that specific cost, but bring their own: no native snapshot support at all before Proxmox VE 9, and every storage change becomes a change request instead of a click, a new zvol, a new iSCSI extent, a new LUN mapping, and a wait for approval and execution.」**
>
> **「手工切的 iSCSI LUN 避开了那个特定的代价，但带来自己的问题：**在 Proxmox VE 9 之前完全没有原生快照支持**，而每一次存储变更都变成一个变更请求而不是一次点击：新建一个 zvol、新建一个 iSCSI extent、新建一个 LUN 映射，然后等待审批和执行。」**

**⭐ 而官方把这件事总结成了一句我认为非常精准的话**：

> **「Proxmox's own documentation frames this as the standard menu for any array without a plugin: NFS or hand-cut LUNs, pick your penalty.」**
>
> **「Proxmox 自己的文档把这个描述成任何没有插件的存储阵列的标准选项：NFS 或者手工切 LUN，挑一个惩罚。」**

**「pick your penalty」，挑一个惩罚。** **这句话比我读过的任何存储选型文章都准确**：**在没有插件的情况下，你面对的不是「哪个更好」，而是「你更愿意承担哪种代价」。**

### 插件实际做什么

**官方的定义**：

> **「The new TrueNAS Proxmox Plugin is a native Proxmox VE storage backend that lets Proxmox provision, snapshot, resize, migrate, and delete TrueNAS-backed VM disks directly, over iSCSI or NVMe/TCP, without manual LUN management.」**
>
> **「新的 TrueNAS Proxmox 插件是一个原生的 Proxmox VE 存储后端，让 Proxmox 可以直接通过 iSCSI 或 NVMe/TCP 创建、快照、调整大小、迁移和删除 TrueNAS 支撑的虚拟机磁盘，无需手工 LUN 管理。」**

> **「On TrueNAS 25.10+, it registers automatically and turns every VM disk request into an automated zvol, published as an iSCSI LUN or NVMe/TCP namespace.」**
>
> **「在 TrueNAS 25.10+ 上，它会自动注册，并把每一次虚拟机磁盘请求变成自动化的 zvol，以 iSCSI LUN 或 NVMe/TCP namespace 的形式发布出去。」**

**⚠️「turns every VM disk request into an automated zvol」**，**这句话是全部的意义所在。** **在这个插件之前，「请求一块磁盘」和「磁盘真的出现」之间，隔着一个人。** **而现在没有那个人了。**

**而日常使用层面的变化，官方写得很具体**：

> **「Day-to-day, that means thinner, sparse volumes on demand, and native OpenZFS snapshots, including live snapshots that capture RAM state.」**
>
> **「日常而言，这意味着按需的、更精简的稀疏卷，以及原生 OpenZFS 快照，**包括捕获 RAM 状态的实时快照**。」**

**⚠️「live snapshots that capture RAM state」**，**这一条值得单独说。** **捕获 RAM 状态的快照意味着「整机状态」被保存下来，而不仅是磁盘。** **对做升级前备份、做测试环境的人来说，这是「能回到那个精确时刻」和「能回到那个磁盘状态」的区别。**

### 版本要求与安装

**这是我认为最该被记下来的实操部分**：

| 项目 | 要求 |
|---|---|
| **Proxmox VE** | **8.x 或更新**（**9.x 被推荐**） |
| **TrueNAS** | **25.10 或更新** |
| ⚠️ **NVMe/TCP 传输** | **需要 Proxmox VE 9.x，并且每个节点上装 `nvme-cli` 客户端 initiator** |
| **安装方式** | **签名 APT 源**（**PVE 8 用 bookworm，PVE 9 用 trixie，自动检测版本**）、**集群感知的交互式安装器（带健康检查和回滚）**、**或无网络的独立 `.deb`** |

**⚠️ 而官方特别点出了一个安全层面的改善，我认为这条对运维最实用**：

> **「API key authentication replaces the SSH-as-root habits some ZFS-over-iSCSI workflows required.」**
>
> **「API key 认证取代了某些 ZFS-over-iSCSI 工作流所要求的『以 root 身份用 SSH』的习惯。」**

**⭐「以 root 身份用 SSH」**，**这是 Proxmox 传统 ZFS-over-iSCSI 方案的已知代价**，**而这个插件用 API key 把它换掉了。** **这不是一个性能改善，是一个攻面缩小。**

### 它的边界：官方明确说了它不是什么

**这一节我认为比功能列表更重要，因为误解边界会导致架构决策错误**：

> **「Treat it as separated compute and storage on TrueNAS, not as a hyperconverged Ceph substitute.」**
>
> **「把它当作 TrueNAS 上分离的计算与存储，而不是一个超融合的 Ceph 替代品。」**

**而它管什么、不管什么，官方 FAQ 写得很清楚**：

- **替换**：**虚拟机磁盘**的手工 iSCSI LUN 管理，或基于 NFS 的 QCOW 方案
- ⚠️ **不替换**：**ISO 和备份**。**「插件只处理块存储，所以基于文件的内容按设计留在 TrueNAS 原生的 NFS 或 SMB 共享上。」**
- **克隆、移动、备份、导入**：**仍然在主机侧运行，按你原来在 Proxmox 上的方式规划这些操作**

### 一个我认为很聪明的设计：多租户隔离规则

> **「Multi-tenancy rules (one dataset and one target or subsystem per cluster) let labs and service providers run several Proxmox clusters against one TrueNAS without extent-name collisions.」**
>
> **「多租户规则（每个集群一个 dataset 和一个 target 或 subsystem）让实验室和服务提供商可以在同一台 TrueNAS 上跑多个 Proxmox 集群，而不会有 extent 名字冲突。」**

**⭐「不会有 extent 名字冲突」**，**这个细节暴露了手工管 LUN 时代的一个真实痛点。** **两个集群各自建了一个叫 `vm-100-disk-0` 的 extent，然后它们撞了。** **而「一个集群一个 dataset + 一个 target」这个规则，是用命名空间把问题根治掉，而不是加前缀。**

### 状态：Early Adopter，Enterprise 在验证中

**官方措辞很谨慎**：

> **「This release is for Early Adopters: actively developed, and the version we're introducing to TrueNAS Community Edition users first. TrueNAS Enterprise support is in active validation and orderable.」**
>
> **「这个版本是给早期采用者的：正在积极开发中，是我们先向 TrueNAS Community Edition 用户引入的版本。TrueNAS Enterprise 支持正在积极验证中，且已可订购。」**

## 二、TrueNAS 27 RC.1：改名，以及四个功能

### 先说改名：26 变成 27

**用户材料里说的「我们听到了，名字改了」是准确的，但官方给出的理由更具体**：

> **「Going forward, each major release is named for the year most of you will deploy it: TrueNAS 27 now, TrueNAS 28 next. Within TrueNAS 27, the dot releases are purely sequential and not tied to any month. The RELEASE version will be 27.0.」**
>
> **「往后，每个大版本以你们大多数人会部署它的那一年命名：现在是 TrueNAS 27，然后是 TrueNAS 28。在 TrueNAS 27 内部，点版本号是纯粹顺序的，不绑定月份。RELEASE 版本会是 27.0。」**

**而官方对「为什么是现在改」的解释，我认为很务实**：

> **「RC.1 is the point where many more of our customers and community members start running this release train. Changing the name now means TrueNAS 27.0 ships with its final name from day one, so documentation, upgrade paths, and support conversations never have to translate between two names.」**
>
> **「RC.1 是更多客户和社区成员开始跑这条发布线的时点。**现在改名意味着 TrueNAS 27.0 从第一天起就用最终名字发布**，这样文档、升级路径和支持对话都不需要在两个名字之间翻译。」**

**⚠️ 而有一个容易搞混的细节，官方论坛帖明确说了**：

> **「The earlier 26-BETA.1, 26-BETA.2, and 26-BETA.3 releases keep their original names, and their documentation remains available in the 26 documentation.」**
>
> **「更早的 26-BETA.1、26-BETA.2、26-BETA.3 保留原来的名字，它们的文档仍然在 26 文档里。」**

**所以：`26-BETA.*` 是历史名字（不改），`27-RC.1` 起用新名字。** **而你会搜到「TrueNAS 26」的文档，那不是错，那是历史版本。**

### 底座：OpenZFS 2.4 + Linux 6.18

**这一块是「升级就能拿到」的部分，而它有几个具体数字**：

> **「OpenZFS 2.4 provides a number of tangible improvements. Dedup writes are up to 25% faster, encryption is faster on CPUs with AVX2 extensions (all currently shipping TrueNAS Enterprise appliances are AVX2-capable), and smarter write allocation reduces fragmentation and keeps pools responsive as they fill up.」**
>
> **「OpenZFS 2.4 提供了若干实实在在的改进。**去重写入快了最多 25%**，在支持 AVX2 的 CPU 上加密更快（所有当前出货的 TrueNAS Enterprise 设备都支持 AVX2），而更聪明的写分配减少了碎片，并让池在装满时仍保持响应。」**

**而两个「管理员会直接用到」的功能**：

- **默认的用户、组和项目配额**
- **可以限制在特定时间窗口内运行的 scrub（数据校验扫描）**

**内核侧**：

> **「the Linux kernel moves to 6.18, with updated drivers for Broadcom tri-mode HBAs, Gen5 PCIe switching, and new NVIDIA GPUs. Linux containers (LXC), introduced as experimental in 25.04 and matured in 25.10, are now fully supported.」**
>
> **「内核移到 6.18，带来 Broadcom 三模 HBA、Gen5 PCIe 交换和新的 NVIDIA GPU 的驱动更新。**Linux 容器（LXC）从 25.04 的实验特性、25.10 的成熟，现在获得完全支持。**」**

**⚠️ 但请注意：论坛上有人报了 LXC 相关的实际问题**（第六节会讲）。

### 功能一：TrueSearch + WebShare（依赖 TrueNAS Connect）

**这一组的定位是「找文件和看文件不需要挂载」**：

> **「TrueSearch: Finding a file on a large NAS usually means walking the directory tree, or asking whoever saved it. TrueSearch is a server-side index of file names, metadata, and content, so results come back in seconds instead of minutes.」**
>
> **「TrueSearch：在一个大 NAS 上找文件通常意味着遍历目录树，或者去问存它的人。TrueSearch 是一个文件名、元数据和内容的**服务端索引**，所以结果以秒而不是分钟返回。」**

**而 macOS 那条集成，我认为是这一组里最实用的**：

> **「With Spotlight Search enabled on an SMB share hosted on TrueNAS, Finder searches it the way it natively searches your local macOS device. TrueNAS does the indexing ahead of time, so nobody's Mac is crawling the share over the network.」**
>
> **「在 TrueNAS 托管的 SMB 共享上启用 Spotlight Search 后，Finder 会像原生搜索你本地 macOS 设备那样搜索它。**TrueNAS 提前完成索引，所以没有人的 Mac 需要在网络上爬这个共享。**」**

**⭐「没有人的 Mac 需要在网络上爬这个共享」**，**这句话点出了传统 NAS 搜索的真实成本：它不是「慢」，是「把负担放在每台客户端上」。** **20 台 Mac 同时搜一个共享，就是 20 次网络遍历。**

**而 WebShare 的定位**：

> **「WebShare brings the same data to a browser, tablet, or phone, with your ACLs and permissions intact. Preview media, browse snapshots, and share or collect files, much like Dropbox, without handing your company's data to a public cloud.」**
>
> **「WebShare 把同样的数据带到浏览器、平板或手机上，你的 ACL 和权限保持完整。预览媒体、浏览快照、分享或收集文件，很像 Dropbox，而不把你的公司数据交给公有云。」**

**⚠️ 而有一个必须标注的依赖**：**「WebShare 和 TrueSearch 需要 TrueNAS Connect。」** **这一点在评估时不能忽略，因为它意味着这两个功能不是纯本地能力。**

### 功能二：Fusion Pools 2.0 与 Live Dataset Tiering

**这一节我认为是全文技术含量最高的部分，而它有一个非常具体的经济背景**：

> **「With flash prices up more than 300% and a roughly 20X cost gap between flash and HDD raw capacity, TrueNAS has continued to refine and reinvigorate the hybrid storage design it was built around.」**
>
> **「**闪存价格涨了超过 300%，而闪存和 HDD 的裸容量成本差距大约是 20 倍**，所以 TrueNAS 继续改进并重振它一直围绕构建的混合存储设计。」**

**⭐「闪存涨了 300%」+「20 倍成本差」**，**这两个数字是理解 Fusion Pools 为什么现在被重点推的全部原因。** **混合存储不是新技术，它是被价格逼回来的。**

**三个具体改动**：

**① RAIDZ special vdev（原先是 mirror only）**

> **「Special vdevs have been available for several years in TrueNAS, but have been limited to mirror topologies only for redundancy. TrueNAS 27 RC.1 introduces support for RAIDZ special vdevs, allowing for greater flexibility and letting you make the most of available SSD capacity.」**
>
> **「special vdev 在 TrueNAS 里已经可用好几年了，但为了冗余它们一直被限制在仅镜像拓扑。**TrueNAS 27 RC.1 引入了对 RAIDZ special vdev 的支持**，带来更大灵活性，并让你充分利用已有的 SSD 容量。」**

**⚠️ 这一条的实际意义是容量效率**：**mirror 意味着 50% 的容量开销，而 RAIDZ1 是「n-1」个盘的可用容量。** **对小容量 SSD 组成的 special vdev 来说，这个差别很实在。**

**② special vdev 兼作 SLOG**

> **「Alongside the new layout options for the special vdev, the special vdev can now act as part of the ZFS log device chain for handling synchronous writes. If a dedicated log device is present, it takes priority. But in case of a device failure, or where a mixed workload makes sense initially, the special vdev absorbs these writes.」**
>
> **「除了新的布局选项，special vdev 现在可以作为 ZFS 日志设备链的一部分来处理同步写入。**如果有专门的日志设备，它优先。**但在设备故障时，或者在混合负载最初合理的情况下，special vdev 会吸收这些写入。」**

**⚠️ 注意这里的措辞：「如果有专门的日志设备，它优先。」** **所以这不是「用 special vdev 替代 SLOG」，而是「在 SLOG 缺位或故障时，special vdev 顶上」。** **这是一个降级路径，不是替代方案。**

**③ Live Dataset Tiering（仅 Enterprise）**

> **「the new 'Live Dataset Tiering' feature in TrueNAS Enterprise 27 RC.1, which allows for transparent migration of data blocks between the performance and capacity tiers of your pool without disrupting clients.」**
>
> **「TrueNAS Enterprise 27 RC.1 的新『Live Dataset Tiering』特性，允许在池的性能层和容量层之间**透明迁移数据块，而不中断客户端**。」**

**⚠️「不中断客户端」**，**这是它和「手动搬数据」的本质区别。** **传统的分层是给新写入分层，而老数据你要么重建、要么忍着。** **而「透明迁移」意味着你可以事后调整那个已经建错的池。**

### 功能三：Stateful SMB Failover（仅 Enterprise HA）

**这一条解决的是一个很具体的痛点，而官方的描述很到位**：

> **「For SMB users, this failover used to mean a dropped session. Connected clients had to reconnect and sometimes re-authenticate, and large copy jobs in progress could fail and have to start again, interrupting workflows and frustrating end-users.」**
>
> **「对 SMB 用户来说，这种故障切换以前意味着会话掉线。已连接的客户端必须重连，有时还要重新认证，**而正在进行的大复制任务可能失败并必须重新开始**，中断工作流并让终端用户沮丧。」**

**而新行为**：

> **「TrueNAS 27 adds stateful SMB failover, keeping SMB session states consistent across a controller failover, so clients pick up their existing sessions without re-authenticating. Large transfers keep going from where they were before.」**
>
> **「TrueNAS 27 增加了有状态 SMB 故障切换，在控制器故障切换期间保持 SMB 会话状态一致，所以客户端接续它们已有的会话而无需重新认证。**大传输从它们原处继续。**」**

**⭐ 而官方点了三个「这件事真正重要」的场景**：

> **「This matters most where files are big and time is short: editors working on shared media, digital surveillance systems, and scanners or instruments writing multi-GB files straight to the NAS.」**
>
> **「这在文件大而时间紧的地方最重要：处理共享媒体的编辑、**数字监控系统**，以及直接把多 GB 文件写入 NAS 的扫描仪或仪器。」**

**⚠️「数字监控系统」这个例子值得注意**。**因为摄像头流在故障切换时断掉，意味着那段录像就是永久缺失的。** **它不是「重试一下就好」，而是「那几秒/几分钟没有了」。**

### 功能四：TrueNAS Object Interface（原生 S3）

**这一条我认为是三篇博客里最被低估的功能，因为它的设计选择非常关键**：

> **「As a late addition to TrueNAS 27, object storage is also available as a native TrueNAS service. This provides concurrent, universal access to stored data whether you are using SMB, NFS, WebShare, and now via the S3 protocol. The design is simple: **each object storage bucket is a ZFS dataset**.」**
>
> **「作为 TrueNAS 27 的后期补充，对象存储也可以作为原生 TrueNAS 服务使用。这提供了对已存数据的**并发、通用访问**，无论你用的是 SMB、NFS、WebShare，还是现在的 S3 协议。**设计很简单：每个对象存储 bucket 就是一个 ZFS dataset。**」**

**⭐「每个 bucket 就是一个 ZFS dataset」。** **这个设计决定的连带效果是**：

> **「Your object data gets the same snapshots, quotas, replication, and data integrity as everything else on your TrueNAS system, and you manage it from the same WebUI.」**
>
> **「你的对象数据获得和 TrueNAS 上其他所有东西一样的快照、配额、复制和数据完整性，并且你从同一个 WebUI 管理它。」**

**而它已经覆盖的 API 范围**：

> **「RC.1 already covers the core S3 API that applications depend on, including multipart uploads, object tagging, bucket and object ACLs, versioning and immutability. That makes it a practical, immutable target for S3-compatible backup software.」**
>
> **「RC.1 已经覆盖了应用所依赖的核心 S3 API，包括分片上传、对象标签、bucket 和对象 ACL、**版本控制和不可变性**。这让它成为一个实用的、不可变的、给 S3 兼容备份软件用的目标。」**

**⚠️ 而两个必须知道的限制**：

1. **「版本控制和对象锁特性需要 TrueNAS Connect Plus 许可或 TrueNAS Enterprise 系统。」**
2. **「无容量限制，包括在完全离线模式下用于气隙环境。」** ← 这条是好消息

**⭐ 而这一条和第三节的 Veeam 认证，以及「备份」这件事连起来看才有意思**：**S3 + 不可变 + 每个 bucket 是 dataset = 一个自带 ZFS 保护的、勒索软件改不了的备份目标。** **而 MinIO 在前一段时间的变化，让「有没有一个自托管的、不收费的 S3 实现」变成了一个真实的问题。** **TrueNAS 这一步正好落在这个空位上。**

## 三、Veeam 认证：让备份服务器这个盒子消失

**这是用户材料里只提了一句、而我认为是三件事里最被低估的一件。**

### 那个认证到底是什么

> **「TrueNAS is the first storage platform certified under the newest Veeam Ready Appliance category: All-In-One (virtualized). It's built for servers that run the Veeam Software Appliance (VSA) directly, instead of just sitting behind it as a repository target.」**
>
> **「TrueNAS 是第一个通过最新 Veeam Ready Appliance 类别认证的存储平台：**All-In-One (virtualized)**。它是为那些**直接运行 Veeam Software Appliance (VSA)** 的服务器而建的，而不只是作为它的仓库目标坐在后面。」**

**而「第一个」这个说法是可以核实的，而且官方给了核实方法**：

> **「As of September 18, 2026, Veeam's qualifications page lists exactly two systems under that category, and both are TrueNAS: the TrueNAS F-Series and the TrueNAS V-Series. Both High Availability (HA) and Single Controller versions are available, with the TrueNAS H-Series in progress for certification for smaller deployments.」**
>
> **「截至 2026 年 9 月 18 日，Veeam 的资质页面上该类别下恰好列了两个系统，而两个都是 TrueNAS：TrueNAS F-Series 和 TrueNAS V-Series。HA 和单控制器版本都可用，而 TrueNAS H-Series 正在为更小的部署做认证。」**

**「Veeam 的资质页面上该类别下恰好列了两个系统，而两个都是 TrueNAS」**，**这是一个我可以让读者自己去核实的陈述，而官方的态度也很明确**：**「采购团队可以直接在 Veeam 的网站上核验那个列表。」**

### 为什么这件事重要：采购流程

> **「Enterprise procurement teams check Veeam Ready listings before a vendor gets anywhere near an RFP. **Until now, storage and the Veeam server were certified separately, if the server was certified at all.**」**
>
> **「企业采购团队会让厂商在接近 RFP 之前先过 Veeam Ready 列表这一关。**直到现在，存储和 Veeam 服务器是分开认证的，如果服务器有认证的话。**」**

**⭐「直到现在，存储和 Veeam 服务器是分开认证的」。** **这一句点出了认证的实质变化：从「两个各自合格的零件」变成「一个被验证过的组合」。** **而这两个的差别在采购上是决定性的**。**分开认证的产品组合起来，集成风险在你身上；而被认证的组合，集成风险在厂商身上。**

### VSA 是什么，以及它消除了什么

> **「The Veeam Software Appliance (VSA) is a hardened Linux image that packages Veeam Backup & Replication, a backup proxy, and a hardened repository role into one deployable guest, so you get a working Veeam server without hand-building one on Windows or Linux first, significantly reducing the risks of accidental misconfiguration while also enabling best practices like automatic software updates and secure defaults out of the box.」**
>
> **「Veeam Software Appliance (VSA) 是一个加固的 Linux 镜像，把 Veeam Backup & Replication、一个备份代理和一个加固的仓库角色打包进一个可部署的 guest，所以你得到一个能工作的 Veeam 服务器，而不必先在 Windows 或 Linux 上手工搭一个，这显著降低了意外错配的风险，同时开箱即用地启用了自动软件更新和安全默认值等最佳实践。」**

**而它跑在哪里**：

> **「On TrueNAS hardware, the VSA software runs as a VM under **TrueNAS Data Hypervisor**, the platform's built-in virtualization layer. Its boot disk and its backup repository are both **zvols**, protected by the same self-healing storage and automated checksums as every other bit saved to TrueNAS.」**
>
> **「在 TrueNAS 硬件上，VSA 软件作为一台虚拟机跑在 **TrueNAS Data Hypervisor** 之下，即该平台内置的虚拟化层。**它的启动盘和备份仓库都是 zvol**，受到和存到 TrueNAS 上其他每一位数据相同的自愈存储和自动校验和保护。」**

**⭐ 而官方给了一张对照表，我认为这张表是整个认证的价值所在**：

| 传统 Veeam 栈 | TrueNAS 上的 VSA |
|---|---|
| **备份服务器**：单独一台 Windows 或 Linux 主机，要规划、采购、加固、打补丁 | **加固的 Veeam Software Appliance 虚拟机** |
| **仓库**：通常是单独的 NAS、SAN 或磁盘扩展柜 | **同一台 TrueNAS 系统上的备份存储 zvol** |
| **认证**：存储和备份服务器分开认证，如果都有认证的话 | **Veeam Ready Appliance, All-In-One (virtualized)** |

### 一个官方说得比较诚实的地方：它还给了「不该用这个」的条件

> **「If you're already running a large proxy farm, or your hypervisor design needs transport options the appliance doesn't support yet, talk to your account team about sizing the consolidated path against that topology before you commit.」**
>
> **「如果你已经在跑一个大型的代理集群，或者你的虚拟机设计需要这个 appliance 尚不支持的传输选项，在承诺之前先和你的客户团队讨论把这条整合路径与那个拓扑对照起来做容量规划。」**

**⚠️ 而这段后面还有一句，我认为是整篇博客里最该被引用的话**：

> **「A virtual appliance on TrueNAS also helps provide additional resiliency, with a separate physical Veeam server, it means a separate system that requires a spares kit, redundant power, and a contingency plan in case of disk corruption.」**
>
> **「TrueNAS 上的虚拟 appliance 也有助于提供额外的韧性：一台独立的物理 Veeam 服务器，意味着一个独立的系统，需要备件包、冗余电源，以及一个在磁盘损坏情况下的应急预案。」**

**⭐「备件包、冗余电源、应急预案」**，**这是三件真实的、要花钱的事。** **而把备份服务器变成一台虚拟机，消掉的就是这三件。**

**⚠️ 但我必须补一个反面**：**「备份服务器和它的仓库在同一台机器上」这件事，同时也意味着「单点故障」**。 **官方对此的回应是**：

> **「TrueNAS appliances with High-Availability (HA) strengthen this even further, with 99.999% uptime on the appliance and the ability to automatically restart the Veeam VSA virtual machine in controller failover scenarios.」**
>
> **「带 HA 的 TrueNAS 设备进一步强化这一点，设备有 99.999% 的可用性，并有能力在控制器故障切换场景中自动重启 Veeam VSA 虚拟机。」**

**⭐ 所以准确的读法是**：**All-In-One 的「1」是靠 HA 支撑的。** **在单控制器的 V-Series 或 F-Series 上，你省掉了一个盒子，同时把那个盒子提供的故障隔离也省掉了。** **而官方给的出路是「上 HA」。** **这不算隐瞒，但如果你只读前三段，你会以为这是无条件的好事。**

### 一个我认为最被低估的价值点

> **「A VSA on TrueNAS also gets a resiliency edge a physical Veeam server doesn't: ZFS's self-healing checksums protect the appliance's own data the same way they protect your backups, preventing data corruption from impacting the underlying operating system.」**
>
> **「TrueNAS 上的 VSA 还获得了一个物理 Veeam 服务器没有的韧性优势：**ZFS 的自愈校验和保护这个 appliance 自身的数据，就像它保护你的备份一样**，防止数据损坏影响底层操作系统。」**

**⭐「保护 appliance 自身的数据，就像它保护你的备份一样」**，**这句话揭示了一个很多人没意识到的不对称。** **传统部署里，备份数据有校验和保护，而备份服务器自己的操作系统盘没有。** **所以一个「备份服务器」其实是「被保护的数据 + 一个裸奔的操作系统」。** **而把它变成 zvol 之后，那两层都被 ZFS 保护了。**

**⚠️ 但这里有一个我必须指出的逻辑边界**：**如果整个池出问题，两者一起坏。** **自愈校验和能防「静默位翻转」，不能防「池丢了」。** **所以这个优势是真的，但它的范围是「单盘/单块损坏」，不是「灾难恢复」。** **而备份系统的核心价值恰恰是后者。** **所以这条优势应该被读成「提高日常可靠性」，而不是「替代异地备份」。**

### 认证标签的完整清单

> **「TrueNAS's F-Series and V-Series both cleared it, and both now carry the All-in-one, Backup Target – Disk DAS, and Immutability tags.」**
>
> **「TrueNAS 的 F-Series 和 V-Series 都通过了，两者现在都带有 **All-in-one、Backup Target – Disk DAS、Immutability** 三个标签。」**

**⭐「Immutability」这个标签值得单独指出。** **它是防勒索软件的核心机制**：**如果备份目标能被打成不可变，勒索软件即使拿到管理员权限也删不掉那些备份。**

## 四、版本与硬件支持矩阵

**把三篇博客里的版本要求汇总成一张表，我认为这是最实用的部分**：

| 组件 | 要求 |
|---|---|
| **Proxmox 插件** | **Proxmox VE 8.x+**（**9.x 推荐**）+ **TrueNAS 25.10+** |
| **NVMe/TCP 传输** | **Proxmox VE 9.x** + **每个节点装 `nvme-cli`** |
| **NVMe-oF 在 TrueNAS 侧** | **NVMe-oF target 已是 TrueNAS 原生能力**（**插件只是自动化了 zvol → namespace 这一步**） |
| **S3 Object Interface 基础功能** | **所有 TrueNAS 版本**，**无容量限制**，**支持完全离线/气隙** |
| ⚠️ **S3 版本控制与 Object Lock** | **需要 TrueNAS Connect Plus 许可或 TrueNAS Enterprise** |
| **TrueSearch / WebShare** | **需要 TrueNAS Connect** |
| **Live Dataset Tiering** | **仅 TrueNAS Enterprise** |
| **Stateful SMB Failover** | **仅 TrueNAS Enterprise HA** |
| **Veeam Ready All-In-One** | **F-Series、V-Series**（**HA 与单控制器均可用**）；**H-Series 认证进行中** |
| **Veeam 认证的完整标签** | **All-in-one**、**Backup Target – Disk DAS**、**Immutability** |
| **27.0 正式版** | **2026 年 12 月初** |

**⚠️ 这张表里有一个我必须强调的读法**：**「Community Edition 能用的」和「Enterprise 才能用的」界限**。 **社区版拿到的是：Proxmox 插件（Early Adopter）、S3 基础功能、TrueSearch/WebShare（需 Connect）。** **而 Live Dataset Tiering、Stateful SMB Failover、S3 的版本控制与 Object Lock，都是 Enterprise 侧的能力。** **这个分界在官方博客里是分散写的，但决策时它是第一位的。**

## 五、三件事连起来看：存储平台在吞掉周边

**这一节是我的分析，而我认为它比任何单条新闻都重要。**

**把三件事并排放，会看到一个共同的模式**：

| 事件 | 它吞掉了什么 |
|---|---|
| **Proxmox 插件** | **吞掉了「存储管理界面」**：你不再需要打开 TrueNAS 的 UI 去切 LUN |
| **S3 Object Interface** | **吞掉了「对象存储那一层第三方软件」**：不再需要跑一个容器化的 MinIO 之类 |
| **Veeam All-In-One** | **吞掉了「备份服务器这台物理机」**：它变成同一台机器上的一个虚拟机 |

**⭐ 三次「吞掉」的共同点：每一次都是把「一个需要单独管理的东西」变成「平台内部的一个对象」。**

**而每一次的技术手段也相同**：**用 ZFS 的 zvol / dataset 作为统一底座。** **虚拟机磁盘是 zvol，备份仓库是 zvol，S3 bucket 是 dataset。** **一旦所有东西都是 ZFS 对象，那么「用同一套快照、复制、校验和保护它们」就自动成立了。**

**⚠️ 而这个策略有一个我必须指出的代价，而它在官方博客里没有被正面讨论：**

> **你越是把所有东西都放在同一台机器上，那台机器就越是一个单点。**

**官方对 Veeam 那条的答案是「上 HA」。** **但 HA 解决的是「控制器坏了」，不是「机房没了」、「勒索软件拿到了 root」、「有人 `zpool destroy` 了」。** **所以这个整合策略的正确用法，是「把同一台机器上的东西做好，同时把异地的第二份做好」**，**而不是「因为它是 All-In-One，所以我不需要别的了」。**

**而 Proxmox 那条官方自己就把边界写清楚了**：**「把它当作分离的计算与存储，而不是一个超融合的 Ceph 替代品。」** **这句话我认为应该被推广到三件事上**：**TrueNAS 在变成一个更完整的平台，但它不是「一个什么都能干的盒子」的替代品。** **它是「一台把存储周边整合好的机器」，而「周边」的定义里不包括「异地」和「另一套独立故障域」。**

## 六、⚠️ 官方博客没写，但社区已经踩到的坑

**这一节是我认为本文最有价值的部分，因为它来自一手论坛而不是新闻稿。**

**官方论坛的 RC.1 发布帖下面有 20 条反馈，其中有一条是直接的回归报告。**

### NVMe-oF 的 MDTS 回归（会让 Proxmox 卷变成只读）

**报告者 Azza 的原话**：

> **「I found a bug/regression with NVMe-oF (with assistance from Claude). Since the 27.0.0-RC.1 update I had some read/write issues in Proxmox volumes through the TrueNAS plugin over NVMe-oF. In one case this caused Proxmox to switch the volume to read only mode.」**
>
> **「我发现了一个 NVMe-oF 的 bug/回归（在 Claude 的协助下）。自从升级到 27.0.0-RC.1 之后，我通过 TrueNAS 插件走 NVMe-oF 的 Proxmox 卷出现了读写问题。**其中一次导致 Proxmox 把那个卷切换到了只读模式。**」**

**而技术根因他定位得非常清楚**：

> **「TrueNAS logs show `nvmet_tcp: queue N: failed to map data`. Proxmox logs show `I/O Error (sct 0x0 / sc 0xf)`. The cause appears to be that **TrueNAS's NVMe/TCP target tells Proxmox it accepts I/O of any size (MDTS=0), and then rejects large transfers.** Proxmox was sending requests up to 32MB (max_sectors_kb=32768).」**
>
> **「TrueNAS 日志显示 `nvmet_tcp: queue N: failed to map data`。Proxmox 日志显示 `I/O Error (sct 0x0 / sc 0xf)`。原因看起来是 **TrueNAS 的 NVMe/TCP target 告诉 Proxmox 它接受任意大小的 I/O（MDTS=0），然后又拒绝大传输。** Proxmox 发出的请求最大到 32MB（`max_sectors_kb=32768`）。」**

**⭐ 这个 bug 的形状非常典型**：**target 在上报能力时说了「我什么大小都能收」（MDTS=0 表示无限制），而实际处理时大请求会失败。** **initiator（Proxmox）完全合理地按最大能力发请求，然后被拒。**

**而他给的 workaround 是限制 initiator 侧的最大传输尺寸**：

> **「I have worked around this by creating a udev rule on Proxmox limiting `max_sectors_kb=1024` for every namespace whose subsystem NQN is `nqn.2026-09.org.freenas.ctl:*`」**
>
> **「我的绕法是在 Proxmox 上创建一条 udev 规则，对所有 subsystem NQN 为 `nqn.2026-09.org.freenas.ctl:*` 的 namespace 限制 `max_sectors_kb=1024`。」**

**⚠️ 而官方的回应是要求提工单**：

> **「Thanks… can you report the bug and provide the NAS-ticket number.」**
>
> **「谢谢……你能报一下这个 bug 并提供 NAS 工单号吗。」**

**⚠️ 所以到本文写作时，这个 bug 的状态是「已报告、有 workaround、待修复」。** **而这恰好是两个功能交汇的地方**：**Proxmox 插件正在 Early Adopter 阶段推广 NVMe/TCP 作为「最低延迟」的选项，而 RC.1 的 NVMe/TCP target 正好有这个回归。** **所以如果你打算同时上这两个，先测 NVMe/TCP，或者先用 iSCSI。**

### 其他值得注意的社区反馈

**论坛里还有几条我认为对评估有实际价值的**：

| 反馈 | 内容 |
|---|---|
| **Ubuntu 容器不响应关机命令** | **「TrueNAS 等到超时，然后直接杀掉容器里的进程。这严重破坏了 UPS 即将断电时的关机流程。」** 用户说**「过去是能工作的，我猜是在 26BETA 时坏的」** |
| **LXC 容器仍不能在容器里跑 Docker** | **「LXC 容器重启会拿到新 MAC 地址，默认就意味着新 IP。」**，注意：**官方说 LXC「现在获得完全支持」，而社区说容器里跑 Docker 仍有问题。** 这两个陈述不矛盾，但合起来读才准确 |
| **启动后有 10 秒网络延迟** | **「控制台显示就绪提示之后，网络（ping/ssh/web）有 10 秒延迟。」** 用户自己追加：**「这个延迟在 Beta 里也有，所以这就是 TN 27 的方式。」** |
| **升级后 reboot 失败（AMD EPYC 平台）** | **「第二台（EPYC）服务器在执行升级脚本后无法执行重启动作并失败。」** 手动重启 + 清理失败升级后恢复正常 |
| **许可证告警（官方已说明）** | **非 iX 硬件上通过 TrueNAS Connect 拿到的 Community 许可，升级后会看到「System serial does not match license」和「running on unsupported hardware」告警。** **官方明确说「这些告警是外观性的，可以安全地忽略」** |
| **一个功能失效的反馈** | **社区成员说在 Community Edition + TrueNAS Connect 上「无法在 SMB 共享上启用 Spotlight 搜索」**，试过断开重连、删账号都不行。**官方把讨论转到了单独的帖子** |

**⚠️ 其中「Ubuntu 容器不响应关机」那条，我认为对生产环境的风险等级最高**：**因为它破坏了 UPS 触发关机的路径。** **而 UPS 关闭流程是「最后一道保护」，它坏了就意味着一次断电可能变成一次非正常关机。** **而报告者自己也说不确定是什么时候坏的（「我猜是 26BETA」）。** **这类「不确定从哪个版本开始」的回归，恰恰是最难排查的。**

## 七、我的判断

**第一，这三件事里，Proxmox 插件的价值最容易被准确衡量，而 Veeam 认证的价值最容易被低估。** **因为插件解决的是一个「你每天都在花时间」的问题**（切 LUN、等待审批），**而认证解决的是一个「你每三年才花一次时间」的问题**（采购、认证、RFP）。 **但后者的杠杆更大**：**它决定了一整套架构能不能通过一次采购评审。** **而「TrueNAS 是 Veeam 那个新类别下唯一两个条目」这件事，在 RFP 阶段的说服力是功能列表给不了的。**

**第二，我认为「pick your penalty（挑一个惩罚）」这个表述值得被整个存储行业学。** **因为它在没有插件的情况下，诚实地承认了「NFS 快照会阻塞虚拟机」和「手工 LUN 每次变更都要走变更流程」这两件事都是代价，而不是把它们包装成「各有优势」。** **一个厂商愿意引用竞争对手文档里对自己不利的描述，然后用「我们消除了这个二选一」来卖东西，这比列 20 个功能点有效得多。**

**第三，我担心的是「三件事同时发布」造成的注意力分散。** **因为这三件事的成熟度差异很大**：**S3 Object Interface 是 Early Access、Proxmox 插件是 Early Adopter、Veeam 认证是「已经通过、可以采购」、而 27.0 正式版要等到 12 月。** **把这四件事打包成「TrueNAS 的三个更新」，会让读者模糊掉「哪个现在能用、哪个要等、哪个只在 Enterprise 有」这个最关键的分界。** **这也是我为什么在第四节专门做了一张版本矩阵，因为官方博客里这些信息是分散在三个页面里的。**

**第四，那个 NVMe-oF 的 MDTS 回归，我认为它揭示了一个关于「功能组合」的普遍风险。** **Proxmox 插件推荐 NVMe/TCP 作为「最低延迟」的选项，而 RC.1 的 NVMe/TCP target 有这个回归，**两者都是新的，而它们的交汇点没有在任何一个功能发布说明里被测试到。** **这不是任何一方的错，而是「多个新功能同时上线」的必然结果。** **所以我的建议是**：**如果你要上 Proxmox 插件，先用 iSCSI（它更老、更成熟），等 NVMe/TCP 这个 bug 修完再切。** **而如果你已经在用 NVMe/TCP，那条 udev 规则（`max_sectors_kb=1024`）值得先加上。

**第五，关于「All-In-One 到底安不安全」这个问题，我认为官方给的答案是对的，但读者容易读成更强的结论。** **官方说 HA 版有 99.999% 可用性，并且能在控制器故障切换时自动重启 VSA 虚拟机。** **这两条都是真的。** **但它们回答的是「硬件坏了怎么办」，不是「这一整套被勒索软件打了怎么办」。** **而备份系统的核心价值恰恰是后者。** **所以我认为正确的架构判断是**：**All-In-One 让你省掉一个盒子，而那个盒子的作用是「故障隔离」和「独立故障域」。** **你应该用省下来的钱去买「异地的那一份」，而不是认为「All-In-One 所以不需要异地了」。** **ZFS 的自愈校验和确实给了 appliance 自身一层额外保护（这是真的优势，而且很独特），但它的范围是「静默位翻转」，不是「池丢了」。**

**第六，也是最后一条：那个「闪存涨了 300%、闪存和 HDD 成本差 20 倍」的数字，我认为是这三篇博客里最有信息量的一句，而它被埋在 Fusion Pools 那一节的中段。** **因为它解释了为什么 2026 年整个存储行业都在重新谈混合存储，也解释了为什么 TrueNAS 要做「special vdev 兼作 SLOG」这种看起来很小、实际很实用的改动。** **在一个全闪存被当成默认答案的时代，「混合」重新变成一个需要认真设计的选项，而这个转向的原因是价格，不是技术。** **这一条对采购决策的影响，比任何一个功能点都大。**

## 关键事实速查

### 三件事的基本信息

| 项目 | 内容 |
|---|---|
| **Proxmox 插件** | **发布 2026-09-11**；**Early Adopter**，先向 Community Edition 开放；**Enterprise 支持「正在积极验证，且已可订购」** |
| **TrueNAS 27 RC.1** | **发布 2026-10-05**；**27.0 正式版 2026 年 12 月初**；**底座 OpenZFS 2.4 + Linux kernel 6.18** |
| **Veeam 认证** | **博客 2026-09-22**；**Veeam 资质页面截至 2026-09-18 该类别下恰好两个系统，都是 TrueNAS** |
| **改名** | **TrueNAS 26 → TrueNAS 27**（**以部署年份命名，27 是因为大多数人在 2027 年部署**）；**26-BETA.1/2/3 保留原名** |

### Proxmox 插件

| 项目 | 内容 |
|---|---|
| ⭐ **核心** | **「You click the button. TrueNAS builds the disks.」**；**每次磁盘请求 → 自动 zvol → iSCSI LUN 或 NVMe/TCP namespace** |
| **它消除的二选一** | **「NFS 或者手工切 LUN，挑一个惩罚」**：**NFS 快照走 QCOW，会阻塞虚拟机，大磁盘「几分钟，极端情况几小时」**；**手工 LUN 在 PVE 9 之前无原生快照，每次变更都是变更请求** |
| **快照** | **原生 OpenZFS 快照**，**包括捕获 RAM 状态的实时快照** |
| **传输** | **iSCSI**（现在可用）；**NVMe/TCP**（**需 PVE 9.x + `nvme-cli`**） |
| **版本要求** | **Proxmox VE 8.x+（9.x 推荐）** + **TrueNAS 25.10+** |
| **安装** | **签名 APT**（**PVE 8 → bookworm，PVE 9 → trixie，自动检测**）、**集群感知交互式安装器（健康检查 + 回滚）**、**独立 `.deb`（气隙节点）** |
| ⭐ **安全改善** | **「API key 认证取代了某些 ZFS-over-iSCSI 工作流所要求的『以 root 身份用 SSH』的习惯」** |
| ⚠️ **边界** | **「把它当作 TrueNAS 上分离的计算与存储，而不是超融合的 Ceph 替代品」** |
| ⚠️ **不替换什么** | **ISO 和备份**：**「插件只处理块存储，文件类内容按设计留在原生 NFS 或 SMB 共享上」** |
| **多租户** | **「每个集群一个 dataset 和一个 target 或 subsystem」**，**避免 extent 名字冲突** |

### TrueNAS 27 RC.1

| 项目 | 内容 |
|---|---|
| ⭐ **底座** | **OpenZFS 2.4 + Linux kernel 6.18**；**LXC 从「实验」到「完全支持」** |
| **OpenZFS 2.4 数值** | **去重写入快最多 25%**；**AVX2 CPU 上加密更快**（**所有当前出货的 Enterprise 设备都支持 AVX2**）；**更聪明的写分配减少碎片** |
| **新增管理员功能** | **默认的用户/组/项目配额**；**可限制时间窗口的 scrub** |
| **TrueSearch** | **服务端索引文件名、元数据和内容**；**macOS Spotlight 集成**（**「TrueNAS 提前索引，所以没有人的 Mac 需要在网络上爬这个共享」**） |
| **WebShare** | **浏览器/平板/手机访问，ACL 和权限保持完整**；**「很像 Dropbox，而不把数据交给公有云」** |
| ⚠️ **TrueSearch/WebShare 依赖** | **需要 TrueNAS Connect** |
| **Fusion Pools 2.0** | **RAIDZ special vdev**（**原先仅 mirror**）；**special vdev 兼作 SLOG**（**有专门日志设备时它优先**） |
| ⚠️ **经济背景** | **「闪存价格涨了超过 300%，闪存和 HDD 裸容量成本差约 20 倍」** |
| **Live Dataset Tiering** | **仅 Enterprise**；**「在性能层和容量层之间透明迁移数据块，而不中断客户端」** |
| **Stateful SMB Failover** | **仅 Enterprise HA**；**「大传输从它们原处继续」**；**官方点名的场景：共享媒体编辑、数字监控系统、扫描仪写多 GB 文件** |
| ⭐ **Object Interface** | **「每个对象存储 bucket 就是一个 ZFS dataset」** → 同一套快照/配额/复制/完整性；**覆盖分片上传、对象标签、bucket/对象 ACL、版本控制、不可变性** |
| ⚠️ **S3 限制** | **基础功能全版本可用、无容量限制、支持完全离线气隙**；**版本控制和 Object Lock 需 TrueNAS Connect Plus 许可或 Enterprise** |

### Veeam 认证

| 项目 | 内容 |
|---|---|
| ⭐ **认证名称** | **Veeam Ready Appliance — All-In-One (Virtualized)** |
| ⭐ **唯一性** | **截至 2026-09-18，该类别下恰好两个系统，都是 TrueNAS：F-Series、V-Series**；**HA 与单控制器均可**；**H-Series 认证进行中** |
| **三个标签** | **All-in-one**、**Backup Target – Disk DAS**、**Immutability** |
| **VSA 是什么** | **加固 Linux 镜像**，把 **Veeam B&R + 备份代理 + 加固仓库角色**打包成一个可部署 guest |
| **跑在哪** | **TrueNAS Data Hypervisor（平台内置虚拟化层）**；**启动盘和备份仓库都是 zvol** |
| ⭐ **相比传统部署** | **备份服务器**：从「单独主机，要规划/采购/加固/打补丁」→ **加固 VSA 虚拟机**；**仓库**：从「单独 NAS/SAN/磁盘柜」→ **同一系统的 zvol**；**认证**：从「分开认证」→ **组合认证** |
| ⭐ **省掉的真实成本** | **「一台独立的物理 Veeam 服务器意味着一个独立的系统，需要备件包、冗余电源，以及一个在磁盘损坏情况下的应急预案」** |
| ⭐ **独特优势** | **「ZFS 的自愈校验和保护这个 appliance 自身的数据，就像它保护你的备份一样，防止数据损坏影响底层操作系统」** |
| **HA 的价值** | **99.999% 可用性**；**控制器故障切换时能自动重启 VSA 虚拟机** |
| ⚠️ **官方给的不适用条件** | **「已经在跑大型代理集群」**；**「虚拟机设计需要这个 appliance 尚不支持的传输选项」** |

### ⚠️ 社区已报的问题（RC.1）

| 问题 | 细节 |
|---|---|
| ⭐ **NVMe-oF MDTS 回归** | **「TrueNAS 的 NVMe/TCP target 告诉 Proxmox 它接受任意大小的 I/O（MDTS=0），然后又拒绝大传输」**；**Proxmox 日志 `I/O Error (sct 0x0 / sc 0xf)`**；**TrueNAS 日志 `nvmet_tcp: queue N: failed to map data`**；**后果：Proxmox 把卷切成只读**；**workaround：Proxmox 上 udev 规则限制 `max_sectors_kb=1024`**（**对 NQN 为 `nqn.2026-09.org.freenas.ctl:*` 的 namespace**） |
| ⚠️ **Ubuntu 容器不响应关机** | **「TrueNAS 等到超时然后杀掉容器里的进程。这严重破坏了 UPS 即将断电时的关机流程」**；**用户称「过去能工作，猜是 26BETA 时坏的」** |
| **LXC 里跑 Docker 仍有问题** | 社区称仍需 workaround；**「LXC 容器重启会拿到新 MAC 地址，默认就是新 IP」**（**与官方「LXC 完全支持」并不矛盾，但合起来读才准确**） |
| **启动后 10 秒网络延迟** | **控制台显示就绪后 ping/ssh/web 延迟 10 秒**；**「这个延迟在 Beta 里也有，所以这就是 TN 27 的方式」** |
| **AMD EPYC 平台升级后 reboot 失败** | 手动重启 + 清理失败升级后恢复正常 |
| **许可证告警（官方已说明）** | 非 iX 硬件 + Community 许可：**「System serial does not match license」**、**「running on unsupported hardware」**；**官方：「这些告警是外观性的，可以安全地忽略」** |
| **Spotlight 搜索失效** | 有社区成员称在 Community + Connect 上无法启用 SMB 共享的 Spotlight，官方转到单独帖子处理 |

## 延伸阅读

- [从 VMware 迁到 Proxmox：不是换个虚拟化平台，是换掉一整套你不再拥有的抽象](https://freelamp.com/articles/2026-10-15_red-hat-lightwell-backport-netops-as-code/)
- [机器凭据轮换只是买时间：ZSP 的关键不在「换密码」，在「有没有人负责关掉它」](https://freelamp.com/articles/2026-10-19_zero-standing-privilege-machine-identities/)
- [一个 LLM 网关的发布管道被攻破：攻击者用官方签名发出了一个专门偷你密钥的包](https://freelamp.com/articles/2026-10-21_litellm-1-107-0-supply-chain-compromise/)
- [TrueNAS 官方：Proxmox 插件发布博客](https://www.truenas.com/blog/truenas-proxmox-plugin)
- [TrueNAS 官方：27 RC.1 功能集](https://www.truenas.com/blog/truenas-27-rc1-feature-set/)
- [TrueNAS 官方：Veeam Ready All-In-One 认证](https://www.truenas.com/blog/truenas-veeam-vsa-all-in-one-ready/)
- [官方论坛：TrueNAS 27.0.0-RC.1 发布帖（含 20 条社区反馈）](https://forums.truenas.com/t/truenas-27-0-0-rc-1-is-now-available/68265)
