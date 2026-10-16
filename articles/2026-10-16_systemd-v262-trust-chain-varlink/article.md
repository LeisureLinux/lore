---
title: "systemd v262 那 35 条改动，真正的主线是把「启动信任」变成一条可以逐段签名的链"
date: 2026-10-16
slug: systemd-v262-trust-chain-varlink
tags: [systemd, 可信启动, TPM, PCR, NvPCR, UKI, systemd-boot, dm-verity, LUKS, Varlink, D-Bus, 机密计算, TDX, coredump, 译文]
category: Linux/运维
author: FreeLAMP.com
original_source: "Lennart Poettering 博客（Mastodon Stories for systemd v262）/ systemd v262 NEWS"
original_author: "Lennart Poettering；systemd 项目"
original_date: 2026-10-15
original_url: "https://0pointer.net/blog/mastodon-stories-for-systemd-v262.html"
description: "systemd v262 于 2026 年 9 月 22 日发布，Lennart Poettering 随后在 Mastodon 上发了 35 条帖子介绍重点变化，并整理成一篇索引。本文不逐条复述，而是从这 35 条里抽出两条主线：一条是启动信任链的精细化（NvPCR 换掉锚定秘密、PCR policyrefs 让不同启动阶段用不同的签名策略、加密加 verity 的 DDI、只读 ESP、持久化 TPM EK），另一条是 Varlink 对 D-Bus 的持续替代（sysupdate、cryptenroll、journal、report 都新增了 Varlink 接口，而 sysupdated 的 D-Bus API 将在 v263 移除）。文章也说明为什么 v262 里最重要的那条 AI 金丝雀此前已单独写过，此处不重复。"
published: true
---

> 来源：[Lennart Poettering：Mastodon Stories for systemd v262](https://0pointer.net/blog/mastodon-stories-for-systemd-v262.html)（2026-10-15）
> 一手材料：[systemd v262 NEWS](https://raw.githubusercontent.com/systemd/systemd/v262/NEWS)、[systemd v262 release](https://github.com/systemd/systemd/releases/tag/v262)（**发布于 2026-09-22**）
> 说明：**用户给的链接是那 35 条 Mastodon 帖子的索引页，不是变更清单本身。** **所以本文的事实部分取自 v262 的官方 NEWS 文件，索引页只用来确认哪些改动是作者本人认为的重点。**
> ⚠️ **本站此前已单独写过 v262 里的一条**：[systemd 262 正式发布：内嵌兜底 unit、LUO 热更新会话，还带一只「AI 提交金丝雀」](/articles/2026-09-22_systemd-262-released/)（**2026-09-22**）。**那篇讲的是 AI/LLM 金丝雀那条**，**本文不重复**，**而是覆盖其余的技术主线。**
> 本文为**解读**。第一节对「两条主线」的归纳、第四节的判断是笔者补充的部分。

## 一句话结论

**systemd v262 于 2026 年 9 月 22 日发布**，**Lennart Poettering 事后在 Mastodon 上发了 35 条帖子介绍重点变化**，**并整理成一篇索引**（**就是用户给的链接**）。

**因为我此前已经单独写过这一版里最显眼的那条（AI/LLM 提交金丝雀），所以这篇我换一个做法**：**不从这 35 条里逐条挑亮点，而是找出贯穿其中、且能解释「为什么这些改动会一起出现」的主线。**

**我的判断是两条**：

| 主线 | 内容 | 在 35 条里的占比 |
|---|---|---|
| **① 启动信任链精细化** | **让「信任」从「一个整体」变成「可以逐段签名、逐段验证的链」** | **约占三分之一** |
| **② Varlink 持续替代 D-Bus** | **新接口一律先上 Varlink，实验性的 D-Bus API 到期就撤** | **横跨多条，且有一条明确的移除公告** |

**而这两条共同的底色，是这一版对未来变更的两次预告（都在 v263 生效）**：

> **① systemd-logind 对 UAPI.1 引导加载器规范的集成，此前支持一个特殊目录 `/run/boot-loader-entries/`……但看起来（据我们所知）它实际上没有被任何项目使用（这与 UAPI.1 本身形成鲜明对比，后者的采用远超 systemd），而且它的实现并不完整。在未来的 v263 版本中，我们打算移除对 `/run/boot-loader-entries/` 及相关接口的支持，以简化我们的代码库。对 UAPI.1 的支持当然会保留。**
>
> **② 实验性的「systemd-sysupdated」D-Bus API 将在下一个版本（v263）中被移除。计划是客户端改为通过 Varlink IPC 直接与 systemd-sysupdate（也就是 systemd-sysupdated 的后端）通话。「updatectl」工具将沿着这个方向重做。**

**我认为第 ① 条值得单独留意，因为它是这 35 条里少见的「承认某个东西没人用」的表述**。**而它的措辞很克制**：**不是说「这个设计错了」，而是说「据我们所知它没被使用」。** **这种表述方式在技术项目里并不常见，而它实际上提供了一个很有用的信号**：**UAPI.1 本身被广泛采用，而 systemd 为兼容旧系统加的那个旁路目录没人用**。 **也就是说，这一条移除不是因为设计不好，而是因为「过渡期的兼容层」在过渡完成后变成了纯负担。**

## 一、主线一：把启动信任链切成可逐段签名的段

**这一版的改动里，有相当密集的一组都指向同一件事**：**让「哪些代码在哪一阶段被验证过」变成可以分别声明、分别签名的东西。**

**我把它们按「解决什么问题」重新组织。**

### NvPCR 不再依赖锚定秘密

**这是这组里我认为技术上最关键的一条**：

> **NvPCR 的锚定方式得到了改进。它们现在创建的写入策略只允许从 initrd 环境执行初始 extend，并且不再依赖一个密封到 TPM 的秘密（也就是「锚定秘密」）。为了让 NvPCR 工作，所有 NvPCR 定义（`/usr/lib/nvpcr/*.nvpcr`）现在必须被打包在 UKI 里。UKI 还必须嵌入一个签名的 PCR 策略，它绑定到 initrd 引导阶段、并带有「initrd」策略引用。这可以通过向 ukify 提供 `--sign-initrd-pcrs` 选项来创建。没有在 initrd 中定义或初始化的 NvPCR，如果在运行时尝试惰性初始化，将会失败。**

**我需要把这个改动解释清楚，因为它涉及一个容易被忽略的信任问题。**

**先说 NvPCR 是什么**：**TPM 的 PCR（平台配置寄存器）是用来「记录启动过程中每一段代码的度量值」的**。**而 NvPCR（non-volatile PCR）是在普通 PCR 之外额外提供的一个机制**，**它的价值在于能被「扩展」多次而不像普通 PCR 那样在重启时被清空。**

**而在此之前，NvPCR 的可用性依赖一个「锚定秘密」**（**一个密封到 TPM 的秘密**）。**报告说这个设计现在被换掉了**，**换成的是**：**写入策略只允许从 initrd 阶段做初始 extend，加上 NvPCR 定义必须打包进 UKI。**

**我认为这个改动解决的是一个具体而根本的问题**：**如果 NvPCR 的可用性依赖一个「被别人也知道的秘密」，那么它记录的内容的可信度就有上限。** **而改成「只有 initrd 能初始化它」之后，NvPCR 的内容就获得了一个**来自启动路径本身**的保证。**

**而代价是明确的**：**NvPCR 定义必须进 UKI**（**也就是那个统一内核镜像**），**并且要嵌一个带 `initrd` 策略引用的签名 PCR 策略。** **这提高了打包要求**，**但也正是它让保证变得可验证**：**因为「必须打包进 UKI」意味着它进入了被签名的范围。**

### PCR policyrefs：不同启动阶段用不同签名

**紧跟着的一条改动，恰好补上了上一节提到的那个「策略引用」**：

> **systemd-measure 新增了 `--policyref=`，而 systemd-cryptenroll 与 systemd-repart 里对应的 `--tpm2-public-key-policyref=` 选项，用来选择 TPM 对象在解锁时所要求的那个引用。这使得例如「仅限 initrd 的签名策略」成为可能，而 ukify 可以通过 `--sign-initrd-pcrs` 生成它，无需为后续启动阶段复用同一个签名。**

**这一条我认为是整组改动里最能说明「精细化」这个方向的**。**把它和旧的方式对比一下会很清楚**：

| | **旧方式** | **policyrefs** |
|---|---|---|
| **签名覆盖范围** | **一个签名覆盖整个启动流程** | **不同阶段可以用不同的签名** |
| **initrd 与后续阶段** | **复用同一个签名** | **可以分别签，且可以不共用** |
| **泄露一个签名的影响** | **影响所有阶段** | **只影响它覆盖的那个阶段** |
| **典型用法** | — | **「仅限 initrd 的签名策略」** |

**也就是说**：**它让「信任的粒度」和「信任的对象」对齐了**。**在此之前，一个签名必须同时证明「这个 initrd 可信」和「这个后续启动阶段可信」**，**而这两件事的验证时机和风险面其实不同。**

### 加密 + verity 的 DDI：把「机密性」和「真实性」分包在两套机制上

**这一条我读到时觉得设计非常讲究**：

> **一个分区可以同时组合 `Encrypt=` 与 `Verity=data`。在这个模式下，repart 先写入 LUKS2 密文，然后在这个密文之上构建 dm-verity 元数据，所以 verity 构成外层真实性封装，而 LUKS2 是内层加密层。（换句话说，这提供了被认证的机密性。）**

**「verity 是外层、LUKS2 是内层」这个顺序，是整句话里最关键的信息**。**而这个顺序不能被反过来，原因是两条**：

| 关注的属性 | 由谁提供 | 为什么必须在这层 |
|---|---|---|
| **真实性（authenticity）** | **dm-verity** | **它必须验证「你读到的东西是原样的」。如果它在内层，那么外层的解密操作已经先处理了可能被篡改的密文** |
| **机密性（confidentiality）** | **LUKS2** | **它必须是最内层，因为只有它需要看到明文** |

**而官方给这个组合的定性是「被认证的机密性」（authenticated confidentiality）**，**我认为这个用词是准确的**：**它不是「加密 + 校验」这种简单叠加，而是两个属性各自由最适合的机制承担，且顺序由信任依赖决定。**

### 只读 ESP、持久化 TPM EK、CoCo 的系统凭据

**这组里还有三条值得列出来，因为它们各自补了一个空档**：

| 改动 | 解决什么 |
|---|---|
| **systemd-boot / systemd-stub 支持只读 ESP** | **ESP（EFI 系统分区）在很多平台上需要被固件读写，但它的内容在正常运行时不需要变**。**支持只读可以让「启动路径的输入不可被运行时改写」这件事更明确** |
| **持久化 TPM EK** | **EK（Endorsement Key）是 TPM 的身份密钥**。**这条改动会在可能的情况下从 EK 证书验证生成的 EK，然后再持久化它**；**优先使用受支持的高区间 EK 模板，从而让背书层级保持受保护，同时使用持久化的 EK** |
| **systemd-vmspawn 里的 CoCo VM 系统凭据** | **把「给机密计算虚拟机注入系统凭据」这条路打通**（**与同版本里的 Intel TDX CoCo 支持配套**） |

**而「持久化 EK」那一条的措辞值得留意**：**它强调「在持久化之前先用证书验证」。** **这说明改动关注的不是「能不能持久化」，而是「持久化的那个东西是不是真的」。** **在一套以 TPM 为信任根的机制里，这个顺序是不能省的。**

## 二、主线二：Varlink 在稳步替换 D-Bus

**第二条主线不像第一条那么显眼**（**因为它分散在十几个不同的组件里**），**但它的方向非常明确**：**新的接口先上 Varlink，而实验性的 D-Bus API 到点就撤。**

### 这一版新增或强化的 Varlink 接口

| 组件 | 改动 |
|---|---|
| **systemd-sysupdate** | **新增完成钩子**；**且 v263 将移除 sysupdated 的 D-Bus API，客户端改为直接通过 Varlink 与 sysupdate 通话** |
| **systemd-cryptenroll** | **实现了 Varlink API，允许通过 IPC 以编程方式登记额外的密钥** |
| **systemd-sysinstall** | **新增 Varlink IPC** |
| **systemd-report** | **成为 Varlink 服务并提供新指标**；**generate 与 upload 命令现在可以对其产生的报告做密码学签名**，**签名来自链接到 `/run/systemd/report.sign/` 的后端 Varlink 签名器**，**新的 `--sign=` 选项用来选择** |
| **journal** | **支持通过 Varlink 跟踪日志** |
| **.socket 单元** | **新增 Varlink socket 标记与 `varlinkctl list-sockets`** |

**我认为 systemd-report 那条最能说明 Varlink 的定位**。**注意它的签名机制：签名不是内置的，而是从一个「链接到 `/run/systemd/report.sign/` 的后端 Varlink 签名器」获取的。**

**也就是说**：**签名能力本身被做成了一个可插拔的后端，而 Varlink 是这个插拔的接口。** **这比「让 report 自己会签名」要灵活得多**：**因为在企业环境里，「谁来签名」往往需要一个集中式的密钥管理服务，而不是让每个组件自己管私钥。**

### 为什么是 Varlink 而不是继续用 D-Bus

**报告在这一版里没有给长篇论证，但从两条改动的组合能推出方向**：**sysupdated 的 D-Bus API 被移除、客户端改为直接用 Varlink 与后端通话。** **而这个决定的前提是**：**那个 D-Bus 服务本身只是后端的一个包装。**

**我认为这里有一个可以推广的判断**：**当一个 D-Bus 服务只是「把某个进程的能力暴露出去」时，它引入的是一个额外的中介；而 Varlink 的模型是「客户端直接和进程说话」。** **中介的价值在于「把能力聚合到一个总线上」**，**但如果这个能力只由一个进程提供、且没有聚合的需求，中介就只剩下成本。**

**而在同一版里还有一条改动，从另一个角度支持了这个方向**：

> **实验性的 `--introspect-cli` 现在提供机器可读的命令元数据（JSON），它由声明式的动词／选项描述生成。需要做命令／选项发现的脚本可以消费这个接口，而不是去解析人类可读的 `--help` 输出。该特性是实验性的，JSON schema 在未来的稳定化公告之前很可能会继续变化。**

**「让脚本不用解析 `--help`」这件事，和 Varlink 的取向是一致的**：**两者都在把「人可读的输出」和「机器可读的接口」分开。** **而这个分开是必要的，因为人类可读的输出会为了可读性而变更，而机器接口一旦被依赖就很难改。**

**而官方特意标注「schema 很可能会变」是正确做法**：**它意味着这个接口目前是给人试用的，不是给人依赖的。**

## 三、其余改动：按「谁会用得上」分类

**我把剩下的 35 条按使用者分类，这样比按组件分类更有参考价值。**

### 对做服务器与切片管理的人

| 改动 | 内容 |
|---|---|
| **ActivatingConcurrencyMax=** | **Slice 单元新增该配置，用来限制一个切片层级里同时处于 activating 状态的单元数量**；**后续的激活会被排队，并在槽位释放时自动启动** |
| **原子地入队多个任务** | **manager 新增 D-Bus 方法 `EnqueueUnitJobMany()` 用来排队** |
| **原子增删标签** | **`AddAndRemoveTags()` 可以原子地设置一些标签并取消另一些**；**`hostnamectl tags` 接受 `+TAG` 与 `-TAG` 参数，无需替换整个列表**（**即此前已写过的 LUO 相关话题之外的补充**） |
| **机器标签可以写成 key=value** | **同一个 key 不能被赋予多个不同的值** |

**「原子地入队」和「原子增删标签」这两条放在一起看，会发现一个共同的需求**：**调用方想要表达的是「最终状态」，而不是「一串操作」。** **而逐个操作的问题在于中途失败会留下一个中间状态**，**而这个中间状态在自动化脚本里往往没有被正确处理。**

### 对做安全启动与磁盘加密的人

| 改动 | 内容 |
|---|---|
| **首次启动时的恢复密钥登记** | **新增 `systemd-cryptenroll-firstboot.service` 单元提供这个向导**；**systemd-cryptenroll 新增 `--recovery-key-file` 之类的机制来以原子且相对安全的方式把恢复密钥写入文件** |
| **LUKS 支持 rogue TPM 防护** | **针对 LUKS 登记提供防护** |
| **home 的 fscrypt v2 支持** | **systemd-homed 支持 fscrypt v2**；**v1 的 home 仍可解锁、重加密与停用，但没有原地的 v1 到 v2 策略升级** |
| **密码轮换的顺序** | **LUKS-backed home 的密码轮换现在会先添加所有替换 keyslot，再移除旧的**；**如果添加新槽失败，旧槽保持不变，避免在登记失败时被锁在外面** |
| **TPM PCR bank 选择** | **现在会考虑 SHA384 与 SHA512 PCR bank** |

**「先加后删」这个顺序值得单独指出**，**因为它是所有密钥轮换操作都应该遵循的规则**。**而它的价值恰恰在失败路径上**：**轮换失败时，系统仍然可用**。 **而反过来做（先删后加）的后果是**：**一旦添加失败，你就失去了两把钥匙，而其中一把是你刚删掉的。**

**这个模式和我在别处写过的一件事是同一个道理**（**DevOps 里改配置时的「先加新的、验证、再删旧的」**）：**关键不在于正常路径有多快，而在于失败路径有没有退路。**

### 对做容器、扩展与不可变系统的人

| 改动 | 内容 |
|---|---|
| **overlayfs 上可执行** | **允许在 dm-verity 保护的文件系统上执行，同时仍然拒绝可写上层里的文件**；**这需要内核 v7.2 或更新**；**在更老的内核上，从 overlayfs 挂载执行仍然被完全拒绝** |
| **confext / sysext 应用时重启或重载单元** | **应用扩展时可以重启或重载单元** |
| **静态、单二进制服务管理器构建** | **支持静态的、单二进制的构建** |
| **加密加 verity 的 DDI** | **见上一节** |
| **`/etc/clonetab`** | **新增 dm-clone 引导集成**：**`/etc/clonetab` 条目由 `systemd-clonesetup-generator` 翻译成 `systemd-clonesetup@.service` 单元，由 `clonesetup.target` 拉入，而 `systemd-clonesetup` 创建和移除 device-mapper clone 设备**；**条目可以设置 `region-size=` 来控制预填充的粒度** |
| **sysupdate 的 installdb** | **systemd-sysupdate 新增 installdb** |

**「静态单二进制构建」这一条值得留意**，**因为它的使用场景很窄但很关键**：**在最小容器镜像、initramfs、以及某些嵌入式环境里，动态链接器和共享库本身就是负担。** **而一个「静态、单二进制」的服务管理器意味着一个文件就能跑起来。**

**而 `/etc/clonetab` 这条的设计（用 generator 从表文件生成单元）是 systemd 的典型做法**：**表文件给人写，单元给系统执行，中间的翻译由 generator 完成。** **而这个模式的价值在于**：**它让「配置」和「运行时对象」解耦**：**用户可以只维护一份简单的表，而不是一堆 .service 文件。**

### 对桌面与本地化的人

| 改动 | 内容 |
|---|---|
| **FONT_SCALE=** | **vconsole 配置新增 `FONT_SCALE=`**，**配套 `vconsole.font_scale=` 内核命令行与 credential 支持**；**值可以写成因子或百分比**；**目前只支持 100% 与 200%，其他值会被夹到最近的支持值** |
| **基于词表的主机名模式** | **主机名设置逻辑新增一种通配符**：**原有的 `?` 会解析为一个由机器 ID 哈希派生的十六进制字符**，**新增的 `$` 会从词表文件里挑选一个词**（**同样通过哈希**）；**这可以用来自动分配易记的主机名** |

**这两条的共同点是「把选择权交给配置，但把随机性交给哈希」**。**主机名那条尤其巧妙**：**它让多台机器自动获得不同的、但易记的名字，而不需要一个集中的分配服务。** **而「通过哈希派生」意味着这个过程是确定性的**：**同一台机器每次得到同一个名字，而不同机器得到不同名字。**

**FONT_SCALE 那条的「其他值会被夹到最近的支持值」是一个正确的默认行为**：**它避免了「不支持就不要启动」这种硬失败，同时又不假装支持了没实现的缩放级别。**

### 对做崩溃分析与机密计算的人

| 改动 | 内容 |
|---|---|
| **内核 coredump socket 协议** | **systemd-coredump 现在支持 Linux 6.17 起可用的内核 coredump socket 协议**；**在支持的平台上，`systemd-coredumpd.service` 监听 `/run/systemd/coredumpd/kernel`，`systemd-coredump-register.service` 通过 `kernel.core_pattern` 注册该 socket**；**更老的内核继续使用每个 coredump 一个 `systemd-coredump@.service` 的路径**；**对 coredump.conf 的修改需要重载 `systemd-coredumpd.service`** |
| **机密的 CoCo 支持** | **systemd-vmspawn 支持 Intel TDX CoCo**；**并为 CoCo VM 提供系统凭据** |
| **会话作为抑制剂** | **`pam_systemd` 的 `inhibit=` 支持把会话当作抑制剂** |
| **NvPCR 与 PCR policyrefs** | **见第一节** |
| **socket inode 上的扩展属性** | **由 `.socket` 单元管理的 AF_UNIX socket 现在可以标记扩展属性**；**socket 单元新增 `XAttrEntryPoint=`、`XAttrListen=`、`XAttrAccept=` 辅助项，用来标记入口点等** |

**内核 coredump socket 那一条的技术含量在于它换掉了什么**。**旧的路径是「每个 coredump 都拉起一个服务实例」**，**而新的路径是「一个常驻服务监听一个 socket」。** **对崩溃这种可能短时间内大量发生的事件来说，前者会带来实例创建的开销与并发压力**，**而后者把这件事变成了「往一个 socket 写数据」。**

**而「coredump.conf 修改需要重载 coredumpd.service」这句提示是必要的**，**因为常驻服务的配置通常不会自动重载**：**这个提示避免了「改了配置但没生效」这类排查。**

### 其余零散改动

| 改动 | 内容 |
|---|---|
| **DNS-SD 的行为修正** | **通过 systemd-resolved 的 D-Bus 方法注册的 DNS-SD 服务，现在会在注册它们的客户端从总线断开时自动注销**，**这与等效的 Avahi API 的行为一致**；**报告说明由于一个 bug，客户端跟踪从来没有工作过，这类服务过去会一直保持注册直到 systemd-resolved 退出**；**现在客户端必须在服务要保持注册期间保持总线连接打开**，**一次性的注册（例如通过 `busctl` 或 `gdbus`）会在工具退出后立即被撤销**；**要独立于客户端生命周期注册 DNS-SD 服务，请使用 `*.dnssd` 文件** |
| **移除的构建选项** | **Meson 选项 `-Dlibiptc=`（v259 弃用）、`-Dlibidn=`、`-Drc-local=`、`-Dsysvinit-path=`、`-Dsysvrcnd-path=`（自 v260 起弃用且无效）已被移除** |
| **Type=notify-reload 更严格** | **这类服务现在在发送 `READY=1` 时被要求捕获或阻塞 `ReloadSignal=`**；**如果既不捕获也不阻塞，服务会以协议错误启动失败**；**此前允许启动，尽管后续的重载可能触发信号的默认动作并终止服务** |
| **tmpfiles 更严格** | **对于不使用参数字段的 `tmpfiles.d/` 行类型，systemd-tmpfiles 现在会拒绝非空的参数字段** |
| **systemd-report 签名** | **见第二节** |
| **systemd.firstboot=headless** | **首次启动向导的无头模式** |
| **systemd.credentials_boot_policy=** | **引导凭据策略** |
| **systemctl kexec --kernel-cmdline-reuse** | **复用内核命令行** |
| **RestartRandomizedDelaySec=** | **重启随机化延迟** |
| **kexec 计数与关机时间戳** | **PID 1 新增 D-Bus 属性 `KExecCount`，表示自上次真正启动以来系统经历过的 kexec 重启次数**；**它还暴露上一个 kexec 周期的关机时间戳**（**仅在 LUO 可用时**）；**`systemd-analyze time` 用它们来报告 kexec／实时更新的耗时** |

**「Type=notify-reload 更严格」这一条是这一版里少数会**破坏既有服务**的改动**，**所以值得单独说**：**它把一个「以前能用但埋着雷」的情况变成了「直接启动失败」。** **而报告解释了那颗雷是什么**：**后续的重载可能触发信号默认动作并终止服务。** **也就是说，旧行为下这个服务可能在某次重载时无声地死掉，而新行为让问题在启动时就暴露。** **对于一个 init 系统来说，「早失败且说清楚」几乎总是优于「晚失败且难定位」。**

**而 `KExecCount` 和「暴露上一个 kexec 周期的关机时间戳」这两条，配合 `systemd-analyze time` 的改动，解决的是一个具体的可观测性问题**：**在用 kexec 做快速重启（或 LUO 做内核实时更新）时，「这次启动实际上包含了什么」在时间维度上变得不直观。** **而这两个量让它重新变得可测量。**

## 四、我的判断

**第一，这一版的真正主题是「把信任的粒度调到和信任的对象一样细」。**

**我之所以把这个判断放在最前面，是因为如果只看那 35 条的标题，会觉得 v262 是「又一个功能密集的版本」**（**35 条里有 15 个不同的组件，看起来像是平均用力**）。**但把它们按「关注点」重排之后，会发现三分之一都在做同一件事**：

- **NvPCR 换掉锚定秘密** → **让「这段度量是在 initrd 里初始化的」这件事本身获得保证**；
- **PCR policyrefs** → **让「initrd 的策略」和「后续阶段的策略」可以分别签名**；
- **加密 + verity 的 DDI** → **让「机密性」和「真实性」各自由最适合的机制承担，且顺序符合信任依赖**；
- **只读 ESP** → **让启动路径的输入在运行时不可被改写**；
- **持久化 TPM EK 之前先验证** → **让被持久化的那个东西是「已验证的」**。

**这五条的共同点是**：**它们都在把「一个大而模糊的信任声明」拆成「多个小而精确、可以分别验证的声明」。** **而这正是可信启动这个领域长期以来的核心难点**：**因为「我的系统是可信的」这句话在没有粒度的情况下是不可验证的。**

**第二，那个「verity 在外、LUKS2 在内」的顺序，是这一版里最适合拿来当教学例子的地方。**

**它演示了一个通用原则**：**当两个安全属性需要叠加时，它们的顺序不是任意的，而是由「谁依赖谁」决定的。**

**具体地说**：**真实性验证必须在解密之后做的那个假设不成立**（**因为如果先解密，你就已经把可能被篡改的数据喂给了密码学实现**），**而机密性必须是最后一道**（**因为只有它需要看到明文**）。**所以顺序被唯一确定了。**

**而我认为这个原则值得记住，因为它在别的地方也出现**：**比如 TLS 的「先握手验证身份，再加密传输数据」**、**以及我在别处提到的签名与加密在供应链安全里的应用顺序。** **在这些场景里，顺序错了不会立刻报错**（**系统照样运行**），**但会静默地削弱某个保证。**

**而官方给这个组合起名叫「被认证的机密性」，而不是「加密 + 完整性校验」，我认为这个命名本身就是一种精确**：**它说的是「这两个属性都成立」，而不是「我用了两个机制」。**

**第三，Varlink 对 D-Bus 的替换是渐进的，而它给出的理由值得那些设计内部接口的人参考。**

**注意它的做法不是「宣布 D-Bus 过时」**，**而是**：**新接口一律先上 Varlink**（**sysinstall、cryptenroll、journal、report 都是新增的**），**而对已有的实验性 D-Bus API 给一个明确的移除版本号**（**sysupdated 在 v263 移除**）。 **而且移除的理由是清楚的**：**那个 D-Bus 服务只是后端（sysupdate）的一个包装**，**客户端可以直接通过 Varlink 与后端通话。**

**我认为这个判断可以推广到很多内部服务的设计上**：**当一个服务只是「把另一个进程的能力转发到一条总线上」时，它存在的价值取决于「有多少个不同的消费者需要从这条总线上找到它」。** **如果只有一个或很少的消费者，那么这层转发带来的是额外的失败点和版本耦合，而不是解耦。**

**而这一版里 `--introspect-cli` 那条改动从另一个角度印证了同一个方向**：**它把「人可读的 `--help`」和「机器可读的 JSON」分开。** **这两件事被混在一起是很多工具的长期问题**：**而分开之后，人类可读的输出可以为了可读性自由变更，而机器接口则获得了一个可以被明确版本化的形态。**

**而官方给这个新接口标注「schema 很可能会变」是正确的做法**：**它明确划出了「可以试用」和「可以依赖」的界线**，**而这条界线在很多项目里是缺失的。**

**第四，这一版里有几条改动会破坏既有行为，而这些改动的处理方式值得单独看。**

**最明显的一条是 Type=notify-reload 的收紧**：

> **这类服务现在在发送 `READY=1` 时被要求捕获或阻塞 `ReloadSignal=`。如果它们既不捕获也不阻塞，服务会以协议错误启动失败。此前允许启动，尽管后续的重载可能触发信号的默认动作并终止服务。**

**我认为这条改动的处理方式是教科书式的**：**它把一个「可能在生产里某次重载时静默死亡」的问题，变成了「启动时就明确失败」。** **而在 init 系统这个位置，「早失败且说清楚」的价值远高于兼容性。**

**另一条是 DNS-SD 的行为修正，而它的说明方式我认为更值得学**：

> **由于一个 bug，客户端跟踪从来没有工作过，这类服务过去会一直保持注册直到 systemd-resolved 退出（但也没有在守护进程重启后存活）。**

**「这个 bug 让功能从来没有真正生效过」这句话，实际上是在说**：**这个接口的文档行为与实际行为一直不一致，而没人发现。** **而现在的修正让行为与文档一致**，**代价是依赖旧（错误）行为的客户端会受影响**（**一次性的注册会在工具退出后被撤销**）。

**而报告给出的替代方案很具体**：**要独立于客户端生命周期注册，使用 `*.dnssd` 文件。** **这比「请注意行为变化」要有用得多，因为它直接指出了该走哪条路。**

**第五，那两条「未来移除」的预告，比任何新增功能都更能说明这个项目的工作方式。**

**回顾一下那两条**：**移除 `/run/boot-loader-entries/`**（**理由是「据我们所知它没有被任何项目使用」**），**移除 sysupdated 的 D-Bus API**（**理由是客户端可以直接用 Varlink 与后端通话**）。

**而两条预告有一个共同的结构**：**先说清「为什么可以移除」**（**一条是没人用，一条是有等价且更直接的替代**），**再给出明确的版本号**。

**我认为这个模式值得所有维护长期接口的项目参考**，**因为它同时满足了两件通常冲突的目标**：**一方面它给了使用者足够的水位信息**（**v263，也就是下一个版本**），**另一方面它没有为了兼容而无限期背负无用的代码**。

**而第一条的表述「据我们所知它没有被任何项目使用」，实际上也暴露了一件事**：**维护者对「自己的接口被用在哪里」的可见度是有限的。** **而他们选择的处理方式是**：**把「我们观察到的情况」说出来**（**而不是断言「没人用」**），**然后给一个版本号的缓冲**。 **这给了使用者一个反驳的机会**：**如果有人正在用，可以在 v263 发布前说明。**

**最后，我想指出这一版里我最欣赏的一处工程判断，它不在任何一条功能列表里，而在一条「更严格」的改动里**：

> **对于不使用参数字段的 `tmpfiles.d/` 行类型，systemd-tmpfiles 现在会拒绝非空的参数字段。**

**这条改动的价值在于「拒绝无意义输入」**。**一个不该有参数的行类型，如果被写上了参数，那么它在旧行为下会被静默忽略**：**而用户会以为那个参数生效了。**

**而在一套管理启动和文件系统状态的工具里，静默忽略是比报错危险得多的行为**。 **因为报错会在部署时被发现，而静默忽略会在某次「为什么没生效」的排查里被发现**，**而那时距离写出那行配置可能已经过去了几个月。**

## 关键事实速查

| 项目 | 内容 |
|---|---|
| **版本** | **systemd v262** |
| **发布时间** | **2026 年 9 月 22 日** |
| **用户给的链接** | **Lennart Poettering 的《Mastodon Stories for systemd v262》**（**2026-10-15**），**是 35 条 Mastodon 帖子的索引，不是变更清单本身** |
| **下一版预告** | **v263 的同类帖子将在几周内开始，标签 `#systemd263`** |
| **⚠️ 本站已写过的** | **[systemd 262 正式发布：内嵌兜底 unit、LUO 热更新会话，还带一只「AI 提交金丝雀」](/articles/2026-09-22_systemd-262-released/)**（**涉及 AI/LLM 金丝雀**，**本文不重复**） |
| **⭐ 主线一：信任链精细化** | **NvPCR 换掉锚定秘密、PCR policyrefs、加密 + verity 的 DDI、只读 ESP、持久化 TPM EK 前先验证** |
| **NvPCR 的改动** | **写入策略只允许从 initrd 环境执行初始 extend**；**不再依赖密封到 TPM 的「锚定秘密」**；**所有 NvPCR 定义（`/usr/lib/nvpcr/*.nvpcr`）必须打包进 UKI**；**UKI 还须嵌入绑定到 initrd 引导阶段、带「initrd」策略引用的签名 PCR 策略**（**ukify 的 `--sign-initrd-pcrs`**）；**未在 initrd 中定义或初始化的 NvPCR，在运行时惰性初始化会失败** |
| **PCR policyrefs** | **systemd-measure 新增 `--policyref=`**；**systemd-cryptenroll 与 systemd-repart 新增 `--tpm2-public-key-policyref=`**；**使得「仅限 initrd 的签名策略」成为可能，无需为后续启动阶段复用同一签名** |
| **加密 + verity 的 DDI** | **一个分区可组合 `Encrypt=` 与 `Verity=data`**；**repart 先写 LUKS2 密文，再在密文上构建 dm-verity 元数据**；**所以 verity 是外层真实性封装，LUKS2 是内层加密层**（**即「被认证的机密性」**） |
| **只读 ESP** | **systemd-boot / systemd-stub 支持只读 ESP** |
| **持久化 TPM EK** | **可能时从 EK 证书验证生成的 EK，然后再持久化**；**优先使用受支持的高区间 EK 模板，让背书层级保持受保护** |
| **TPM PCR bank 选择** | **现在会考虑 SHA384 与 SHA512 PCR bank** |
| **⭐ 主线二：Varlink 替代 D-Bus** | **v263 将移除 sysupdated 的 D-Bus API**，**客户端改为通过 Varlink 直接与 systemd-sysupdate 通话**；**updatectl 将按此重做** |
| **本版新增的 Varlink 接口** | **systemd-cryptenroll（可通过 IPC 编程登记额外密钥）**、**systemd-sysinstall**、**journal（通过 Varlink 跟踪日志）**、**systemd-report（成为 Varlink 服务）**、**.socket 单元的 Varlink socket 标记 + `varlinkctl list-sockets`** |
| **systemd-report 的签名** | **generate 与 upload 可对报告做密码学签名**；**签名来自链接到 `/run/systemd/report.sign/` 的后端 Varlink 签名器**；**新增 `--sign=` 选择** |
| **`--introspect-cli`** | **以 JSON 提供机器可读的命令元数据**，**由声明式的动词／选项描述生成**；**脚本可消费它而不必解析 `--help`**；⚠️ **实验性，JSON schema 很可能继续变化** |
| **ActivatingConcurrencyMax=** | **Slice 单元新增**，**限制一个切片层级里同时处于 activating 状态的单元数**；**后续激活排队，槽位释放时自动启动** |
| **原子操作** | **manager 新增 `EnqueueUnitJobMany()` 原子入队多个任务**；**`AddAndRemoveTags()` 原子设置与取消标签**；**`hostnamectl tags` 接受 `+TAG`／`-TAG`** |
| **机器标签** | **可写成 key=value**；**同一 key 不能被赋予多个不同值** |
| **恢复密钥登记** | **新增 `systemd-cryptenroll-firstboot.service` 提供首次启动向导**；**可以原子且相对安全的方式把恢复密钥写入文件** |
| **rogue TPM 防护** | **针对 LUKS 登记提供防护** |
| **fscrypt v2** | **systemd-homed 支持 fscrypt v2**；**v1 home 仍可解锁／重加密／停用，但没有原地 v1→v2 策略升级** |
| **home 密码轮换** | **先添加所有替换 keyslot，再移除旧的**；**新槽失败则旧槽保留，避免登记失败时被锁在外面** |
| **overlayfs 上可执行** | **允许在 dm-verity 保护的文件系统上执行，仍拒绝可写上层里的文件**；**需内核 v7.2+**；**更老内核上从 overlayfs 挂载执行仍被完全拒绝** |
| **静态单二进制构建** | **支持静态、单二进制的服务管理器构建** |
| **`/etc/clonetab`** | **新增 dm-clone 引导集成**：**条目由 `systemd-clonesetup-generator` 翻译成 `systemd-clonesetup@.service`，由 `clonesetup.target` 拉入**；**条目可设 `region-size=` 控制预填充粒度** |
| **sysupdate 其他** | **新增完成钩子**；**新增 installdb**；**硬件建议的功能／组件** |
| **confext / sysext** | **应用扩展时可重启或重载单元**；**`systemd-sysext status --json=` 与 `systemd-confext status --json=` 的 `extensions` 字段现在总是数组** |
| **FONT_SCALE=** | **vconsole 配置新增**，**配套 `vconsole.font_scale=` 内核命令行与 credential**；**值可写成因子或百分比**；**目前只支持 100% 与 200%，其他值夹到最近支持值** |
| **主机名词表通配符** | **原有 `?` 解析为由机器 ID 哈希派生的十六进制字符**；**新增 `$` 从词表文件挑选一个词**（**同样通过哈希**）；**可用于自动分配易记主机名** |
| **内核 coredump socket 协议** | **支持 Linux 6.17 起的该协议**；**`systemd-coredumpd.service` 监听 `/run/systemd/coredumpd/kernel`，`systemd-coredump-register.service` 通过 `kernel.core_pattern` 注册**；**更老内核继续走每个 coredump 一个 `systemd-coredump@.service`**；⚠️ **改 coredump.conf 需重载 `systemd-coredumpd.service`** |
| **机密计算** | **systemd-vmspawn 支持 Intel TDX CoCo**；**为 CoCo VM 提供系统凭据** |
| **会话作为抑制剂** | **`pam_systemd` 的 `inhibit=`** |
| **socket 扩展属性** | **`.socket` 单元管理的 AF_UNIX socket 可标记扩展属性**；**新增 `XAttrEntryPoint=`、`XAttrListen=`、`XAttrAccept=`** |
| **kexec 可观测性** | **PID 1 新增 D-Bus 属性 `KExecCount`（自上次真正启动以来的 kexec 重启次数）**；**并暴露上一个 kexec 周期的关机时间戳**（**仅 LUO 可用时**）；**`systemd-analyze time` 用它们报告 kexec／实时更新耗时** |
| **DNS-SD 行为修正** | **通过 systemd-resolved D-Bus 方法注册的 DNS-SD 服务，现在会在注册客户端断开总线时自动注销**（**与 Avahi API 一致**）；**此前因 bug，客户端跟踪从未工作**；**一次性注册（busctl／gdbus）会在工具退出后立即撤销**；**要独立于客户端生命周期，请用 `*.dnssd` 文件** |
| **⚠️ Type=notify-reload 收紧** | **这类服务在发送 `READY=1` 时须捕获或阻塞 `ReloadSignal=`**；**否则以协议错误启动失败**；**此前允许启动，尽管后续重载可能触发信号默认动作并终止服务** |
| **tmpfiles 更严格** | **对不使用参数字段的 `tmpfiles.d/` 行类型，拒绝非空参数字段** |
| **移除的构建选项** | **`-Dlibiptc=`（v259 弃用）、`-Dlibidn=`、`-Drc-local=`、`-Dsysvinit-path=`、`-Dsysvrcnd-path=`（自 v260 起弃用且无效）** |
| **v263 移除预告 ①** | **`/run/boot-loader-entries/` 及相关接口**（**理由：据我们所知没有任何项目使用，且实现不完整**）；**UAPI.1 支持保留** |
| **v263 移除预告 ②** | **实验性的 `systemd-sysupdated` D-Bus API**（**客户端改为通过 Varlink 直接与 systemd-sysupdate 通话**） |
| **其他零散** | **`systemd.firstboot=headless`**；**`systemd.credentials_boot_policy=`**；**`systemctl kexec --kernel-cmdline-reuse`**；**`RestartRandomizedDelaySec=`** |

## 延伸阅读

- [Lennart Poettering：Mastodon Stories for systemd v262](https://0pointer.net/blog/mastodon-stories-for-systemd-v262.html)
- [systemd v262 NEWS](https://raw.githubusercontent.com/systemd/systemd/v262/NEWS)、[v262 release](https://github.com/systemd/systemd/releases/tag/v262)
- [本站：systemd 262 正式发布：内嵌兜底 unit、LUO 热更新会话，还带一只「AI 提交金丝雀」](/articles/2026-09-22_systemd-262-released/)
- [本站：systemd 262-rc1 里那条被低估的改动：把「同步故障」撕开](/articles/2026-08-26_systemd-262-rc1/)
- [本站：Cloud Hypervisor 54 承诺「前两个版本可迁移」](/articles/2026-10-15_cloud-hypervisor-54-live-migration/)
- [本站：同一周里，四个开源项目对 AI 贡献给出了四种答案](/articles/2026-10-15_open-source-ai-contribution-policies-compared/)
