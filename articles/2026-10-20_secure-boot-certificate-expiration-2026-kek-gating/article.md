---
title: "Secure Boot 证书到期：真正的问题不是「证书过期」，而是「更新信任的钥匙，锁在被更新的那把锁里」"
date: 2026-10-20
slug: secure-boot-certificate-expiration-2026-kek-gating
tags: [Secure Boot, UEFI, 证书到期, KEK, db, dbx, PK, Microsoft Windows Production PCA 2011, Windows UEFI CA 2023, KEK 2K CA 2023, shim, Linux, BitLocker, PCR7, CVE-2026-8863, fwupd, mokutil, 固件更新]
category: 系统/硬件
author: FreeLAMP.com
original_source: "微软官方 KB 5062710 / KB 5079373 + Red Hat / AlmaLinux / Rocky Linux 官方说明 + Microsoft Linux 博客 + CERT VU#616257 + 本机实测 efivars"
original_author: "Microsoft Support；Peter Jones / Marta Lewandowska（Red Hat）；Microsoft Linux and Open Source Blog"
original_date: 2026-10-19
original_url: "https://support.microsoft.com/en-us/servicing/os/secure-boot/certificate-expiration-and-ca-updates-7ff40d33-95dc-4c3c-8725-a9b95457578e"
description: "微软三张 2011 年的 Secure Boot 证书在 2026 年陆续到期，Windows Production PCA 2011 的日期是 10 月 19 日。但到期本身不停机，真正的问题是 KEK 门控：KEK CA 2011 在 6 月 24 日就过期了，而它是授权 db 更新的唯一凭证，所以没拿到 2023 KEK 的机器连后续证书更新都收不到。本文梳理三张证书的分工、三种（而非两种）实际状态、Linux shim 完全不同的处境，以及更新 db 会改动 PCR7 从而触发 BitLocker 恢复模式这个坑。"
published: true
---

> 来源：微软官方两份文档 [KB 5062710（证书到期与 CA 更新）](https://support.microsoft.com/en-us/servicing/os/secure-boot/2025/06/windows-secure-boot-certificate-expiration-and-ca-updates)、[KB 5079373（证书到期后会发生什么）](https://support.microsoft.com/en-us/servicing/os/secure-boot/2026/02/when-secure-boot-certificates-expire-on-windows-devices)
> 一手材料：本文的日期、证书名、结论全部来自上述微软文档原文；Linux 侧来自 [Red Hat 官方博客](https://www.redhat.com/en/blog/expiration-secure-boot-signing-certificates-2026)、[Microsoft Linux and Open Source Blog](https://techcommunity.microsoft.com/blog/linuxandopensourceblog/what-it-teams-need-to-know-about-linux-secure-boot-certificates-expiring-in-2026/4530725)、[AlmaLinux](https://almalinux.org/blog/2026-07-14-secure-boot-2023-certificates)、[Rocky Linux](https://rockylinux.org/news/2026-06-02-secure-boot-ca-kek-transition)、[CERT VU#616257](https://www.kb.cert.org/vuls/id/616257)；本机 efivars 实测见第四节。
> 本文为**解读**。第二节关于 KEK 门控的分析、第四节的三种状态分类、第五节的 Linux 侧梳理、第六节的判断是笔者补充的部分。

## 一句话结论

**这条新闻的通行标题是「证书今天到期，快去检查你的电脑」。而我认为这个标题把问题问错了地方。**

**因为微软自己的文档写得很清楚：到期这件事本身不会让任何机器停摆。**

> **「没有收到较新 2023 证书的设备将继续正常启动和运行，标准 Windows 更新也会继续安装。」**

**「不会停」不是安慰，是事实。但紧接着有一句更值得注意的话**：

> **「然而，设备将不再能够获得针对早期启动过程的新安全保护。」**

**而我认为这次事件真正的架构问题，藏在一个很少有人提到的依赖关系里。有一份分析把它写得很直接**：

> **「密钥交换密钥是授权两个 Secure Boot 数据库变更的凭证，所以它对整个部署起着门控作用。一台没有接收 `Microsoft Corporation KEK 2K CA 2023` 的设备，没有有效的权限去接受那个携带 `Microsoft Windows UEFI CA 2023` 的允许列表更新。」**

**「一台没有接收 2023 KEK 的设备，没有有效的权限去接受携带 2023 证书的那个更新。」**

**这就是这次事件的全部要害，而它是一个循环依赖**：

**要更新信任库（db），需要一把授权钥匙（KEK）；而那把授权钥匙，本身在 6 月 24 日就已经过期了。**

**所以「10 月 19 日」这个日期，对已经装好 2023 证书的机器毫无影响，而对没装好的机器，它标志着**那扇门已经关上了**：不是今天关的，是四个月前关的。**

## 一、先把三张证书分清楚，因为它们的日期和职责完全不同

**「Secure Boot 证书到期」这个说法掩盖了一个事实：不是一张证书，是三张；不是一个日期，是三个；而且它们管的东西完全不同。**

**我从微软 KB 5062710 的表格里把原文抄下来，因为这张表本身就是全部信息**：

| 到期证书 | 到期日 | 新证书 | 存放在 | 它的职责 |
|---|---|---|---|---|
| **Microsoft Corporation KEK CA 2011** | **2026 年 6 月 24 日** | **Microsoft Corporation KEK 2K CA 2023** | **KEK** | **签署对 db 和 dbx 的更新** |
| **Microsoft Windows Production PCA 2011** | **2026 年 10 月 19 日** | **Windows UEFI CA 2023** | **db** | **用于签署 Windows 引导加载器** |
| **Microsoft UEFI CA 2011** | **2026 年 6 月 27 日** | **Microsoft UEFI CA 2023** | **db** | **签署第三方引导加载器和 EFI 应用** |
| **Microsoft UEFI CA 2011** | **2026 年 6 月 27 日** | **Microsoft Option ROM UEFI CA 2023** | **db** | **签署第三方 option ROM** |

**这张表里有三个细节值得单独说。**

**第一，那个被更新最多的日期其实不是 10 月 19 日。**

**三张证书里有两张在 6 月底就过期了，其中包括 KEK。** **而大量媒体报道集中在 10 月 19 日，因为那是「Windows 自己」的那张。** **但从依赖关系看，6 月 24 日才是真正的分水岭**：**KEK 一过期，那扇允许你接收后续更新的门就关了一半。**

**第二，`Microsoft UEFI CA 2011` 被拆成了两个证书，而这是一个改进。** 微软自己的解释是：

> **「在续订 `Microsoft Corporation UEFI CA 2011` 证书期间，两个证书把引导加载器签署与 option ROM 签署分开了。这允许对系统信任做更精细的控制。例如，需要信任 option ROM 的系统可以添加 `Microsoft Option ROM UEFI CA 2023`，而不添加对第三方引导加载器的信任。」**

**也就是说：以前「信任微软签的第三方东西」是一个整体开关，现在拆成了「引导加载器」和「option ROM」两个独立开关。** **这个改动本身是对的**，因为它让「我只需要我的网卡固件被签名」这件事不再附带「我也信任所有第三方 bootloader」。**但它同时意味着：如果你的硬件有带签名 option ROM 的设备（某些网卡、存储控制器、显卡），你需要**额外**把那一个也装上，否则那个硬件的固件可能验证不过。**

**第三，所有三张证书都是「同一套」，即历史上每一台 Windows 设备都带同样一组。** 微软原文：

> **「自 Windows 引入 Secure Boot 支持以来，所有基于 Windows 的设备都在 KEK 和 DB 中携带了同一组微软证书。」**

**这解释了为什么这次轮换的规模这么大：它不是「某些型号的问题」，是「全部设备同时到期」。**

## 二、真正的机制：KEK 门控，以及一个看起来像死锁的循环

**这一节是我想重点讲的，因为它是这次事件里最少被解释、也最能决定「你能不能修好」的部分。**

**先把 Secure Boot 的四个数据库说清楚。它们都在 UEFI 的 NVRAM 里**：

| 数据库 | 全名 | 作用 |
|---|---|---|
| **PK** | Platform Key | **平台密钥，最顶层。有它就处于 User Mode（Secure Boot 可开）；清空它就进入 Setup Mode（可自由改其他库）** |
| **KEK** | Key Exchange Key | **授权「谁可以修改 db 和 dbx」** |
| **db** | Signature Database | **允许列表：谁签的代码可以执行** |
| **dbx** | Forbidden Signature Database | **吊销列表：谁签的代码禁止执行** |

**而关键在 KEK 的定义里：它不是「一把用来签代码的钥匙」，它是「一把用来改规则的钥匙」。**

**于是那个循环出现了：**

```
要往 db 里加 2023 证书
        ↓  需要
KEK 里有授权的签名
        ↓  而 KEK CA 2011 已于 2026-06-24 过期
能不能用它签新的 db 更新？
        ↓
微软的答案是：不能再用它签（但已签过的仍有效）
        ↓
所以要装 2023 KEK
        ↓  而装 KEK 需要……
```

**注意最后一行，它不是一个真正的死锁。** **因为装 KEK 有另外两条不依赖签名时效的路**：

1. **固件更新（BIOS/UEFI）** 可以把新的 KEK 和 db 一起写进去；
2. **Windows Update 推送的 kext/更新包**在某些路径上使用**已签好的**更新包，而那些包是在证书仍然有效时签的（**签名时刻有效即可，之后证书过期不影响已有签名**）。

**所以准确的说法不是「死锁」，是「你必须走那两条路之一，而如果两条都走不了，你就卡住了」。**

**而「两条都走不了」不是假设。它对应的是真实的一类设备**：**过了支持期、厂商不再发 BIOS 更新、系统又不在 Windows 更新的服务范围内。** **微软自己给这条路留了一个保底说法，措辞很克制**：

> **「对于任何设备，无论是个人还是组织管理的，请联系你的 OEM 询问所需的固件更新信息，同时留意这类更新可能只对仍在支持期内的设备提供。」**

**「这类更新可能只对仍在支持期内的设备提供」。这句话是这次事件里最诚实的一句，也是它最容易被忽略的一句**，因为**它等于说：有相当一部分老旧设备，官方路径到此为止。**

**而 Red Hat 在讲 Linux 侧时把这个后果说得更直接**：

> **「遗留系统（例如老旧物理服务器、老旧笔记本或台式机、没有厂商固件更新的系统、从不会拿到 BIOS/UEFI 更新的专用设备），如果无法接收对其 Secure Boot db 的更新，那么在到期之后需要更新引导加载器或 shim 时，可能会遇到问题。」**

## 三、「到期」和「吊销」是两件事，而这个区分决定了你要不要动手

**这一节是我认为原文最应该强调、却几乎没提的一点。**

**因为中文语境里「证书过期」很容易被读成「证书失效、相关软件全部不能用」。而在 Secure Boot 里，这两件事的法律含义完全不同。**

**微软在讲 Linux 的那篇文章里说得很清楚**：

> **「过期不是吊销，它不会导致立即的启动失败。」**

> **「UEFI Secure Boot 是拿签名去对照信任数据库和吊销状态来验证的，**不是**对照证书的有效期。」**

**「不是对照证书的有效期」（not against the certificate's validity period）。** **这句是理解整件事的钥匙。**

**两者的差别是**：

- **到期（expiration）**：**意味着微软不能再**新签**东西了。已经签好的东西，签名依然有效。**
- **吊销（revocation）**：**意味着告诉所有系统「不要再信任这个东西签的任何东西」。**

**所以**：

- **一台老机器上那个已经装好的 Windows Boot Manager，签名是 2016 年签的，到期不会让它失效**；
- **同理，一个 2011 年签的 Linux shim，也不会在 6 月 27 日突然启动不了**。

**微软的结论是**：**「目前也没有吊销 `Microsoft UEFI CA 2011` 的计划。」** **Red Hat 的说法一致**：**「因此，硬件厂商没有计划在不久的将来移除或吊销 2011 证书。」**

**而这条区分带来一个**反直觉但非常重要**的操作结论**，微软原文写得很明确：

> **「出于同样的原因，不要从系统的 Secure Boot db 里移除 2011 CA。移除它会剥掉那条信任路径。这次过渡不要求移除，而现有引导组件可能仍然依赖 2011 CA。」**

**「不要移除 2011 CA」。** **我认为这句话值得单独拎出来，因为它反着很多人的直觉**：**既然它过期了，那就删掉它、只留新的。而这样做的后果是：你直接切断了所有仍由 2011 签名的组件的信任路径，包括你自己那台机器上正在用的 bootloader。**

**所以正确的状态是**：**两套都留着。2011 留着让老东西继续能跑，2023 留着让新东西能跑。**

**微软给的那张兼容性矩阵很简洁，我直接引用**：

| 固件信任库 | 仅 2011 签名的 shim | 仅 2023 签名的 shim | 双签名 shim |
|---|---|---|---|
| **只有 2011 CA** | **能启动**（依赖 2011 信任继续存在） | **不能启动** | **应该能启动** |
| **只有 2023 CA** | **不能启动** | **能启动** | **应该能启动** |
| **两个 CA 都有** | **能启动** | **能启动** | **能启动** |

**这张表解释了为什么 Linux 发行版现在都在发「双签名」的 shim**：**它是唯一在三种固件状态下都能启动的选项。**

## 四、实际状态不止两种：我在自己机器上看到的第三种

**这一节是我把自己机器的 efivars 读出来的结果，因为它恰好是一个容易被忽略的状态。**

**媒体通常把设备分成两类：已经拿到 2023 证书的，和没拿到的。而我实测发现问题比这复杂。**

**我的机器是一台 H3CBook Ultra 14T（物理机，EFI 启动），`/sys/firmware/efi/efivars/` 里只有 5 个变量**：

```
AdvancedSetupPage-a04a27f4-...
dbDefault-8be4df61-...
dbxDefault-8be4df61-...
KEKDefault-8be4df61-...
PKDefault-8be4df61-...
```

**注意两件事**：

**第一，没有 `PK`、`KEK`、`db`、`dbx`，也没有 `SecureBoot` 和 `SetupMode`。只有四个 `*Default` 变量。**

**`*Default` 是 UEFI 规范里的「出厂默认库」，它是固件自带的一份镜像，不是当前生效的库。** **一台机器如果只有 `*Default` 而没有真实的 `PK`/`KEK`/`db`，通常意味着 Secure Boot 没有被真正启用或配置**（PK 为空时平台处于 Setup Mode）。

**第二，而更值得注意的是那些 `*Default` 变量里的内容。我把 `dbDefault`（4087 字节）里的证书主体名抽出来看**：

```
Microsoft Windows Production PCA 2011
Microsoft Corporation UEFI CA 2011
Microsoft Corporation Third Party Marketplace Root
Microsoft Root Certificate Authority 2010
```

**也就是说：这台机器固件里的「出厂默认信任库」，只有 2011 年的证书，一条 2023 的都没有。**

**我认为这个观察的价值在于它指出了第三种状态**：**不是「已有 2023」，不是「有 2011 但在等更新」，而是「固件里连当前生效的信任库都没有配，默认库还是 2011 版」**。 **而这种状态下，Windows 那边的「检查 Device security」很可能显示「没有启用」或者干脆没有这一项**，**于是用户会以为「我不受影响」。而实际上，如果哪天要启用 Secure Boot，它会起用一个只有 2011 证书的旧默认库。**

**所以「检查 Secure Boot 状态」这件事，实际上要回答三个层次的问题**：

1. **Secure Boot 现在开着吗？**
2. **如果开着，db 里有 2023 证书吗？**
3. **如果没开，固件的默认库里有没有 2023 证书？（这决定了你将来能不能开）**

**而第三层几乎没人查。**

### 三个层次的检查命令

**Windows 侧**（原文提到的路径）：**Windows 安全中心 → 设备安全性 → 安全启动**。**如果显示黄色警告或「older boot trust configuration」，就说明在第二层上没通过。** 另外**事件查看器 → Windows 日志 → 系统，来源筛选 `TPM-WMI`**，有两条关键事件：

- **Event ID 1808**：**「此设备已更新 Secure Boot CA/密钥」**，说明成功；
- **Event ID 1801**：**「此设备上有可用的更新版 Secure Boot 证书，但尚未应用到固件」**，或者 **「需要更新 Secure Boot CA/密钥」**。

**Linux 侧**（可以更精确）：

```bash
# 第一层：Secure Boot 到底开没开
mokutil --sb-state

# 第二层：db 和 KEK 里有没有 2023
mokutil --db  | grep 'UEFI CA 2023'
mokutil --kek | grep 'KEK 2K CA 2023'

# 或不用 mokutil，直接看 efivars 里有哪些变量
ls /sys/firmware/efi/efivars/ | grep -E '^(db|KEK|dbx|PK)-'
```

**AlmaLinux 给出的判据很清晰**：**「如果两条命令都打印出匹配的证书，你的系统就绪了，到此为止。」** **而如果什么都没打印，可以用 fwupd 试着装**：

```bash
sudo dnf install -y fwupd
sudo fwupdmgr refresh
sudo fwupdmgr update
sudo reboot
```

**注意 `fwupdmgr update` 能装的前提是厂商把这个更新发布成了 fwupd 固件包，而这又回到了「设备是否在支持期内」那个约束。**

## 五、Linux 用户：这是另一个故事，而且比 Windows 那边更微妙

**原文完全是从 Windows 角度写的，但这次的证书轮换对 Linux 影响的方式不一样，而这一点值得单独说清。**

**为什么微软的证书会出现在 Linux 的启动链里？Red Hat 的解释最清楚**：

> **「微软充当签名机构，为每一个合格的、受信任的公司或实体签署 shim，一旦它通过了公开的安全审查。这允许在任意给定设备上安装任意操作系统，以及双系统启动。它也确保了 Linux 生态里一个共同的安全标准。」**

**也就是说：shim 这个由微软签名的中间层，是「Linux 能在开了 Secure Boot 的品牌机上启动」这件事的全部基础。** **而它签在 `Microsoft UEFI CA 2011` 下。而那张证书，6 月 27 日过期了。**

**但这里有一个很多人会误判的地方**：**到期不等于你的 Linux 明天起不来。** 原因上面说过，签名有效性不看证书有效期。**Red Hat 的原话**：

> **「非常重要的一点：只要公开证书没有被系统移除或吊销，由这把密钥签署的 shim 就会继续启动。同样，只要公开证书已注册进被安装系统的固件里，使用这个 shim 的新安装也继续可行。」**

**真正的风险窗口在另一个地方，而微软那篇 Linux 文章把它说得非常准确**：

> **「一旦某家操作系统厂商发布了一个**只由** `Microsoft UEFI CA 2023` 签署的 shim，那么任何固件还没有信任 2023 CA 的系统都将启动失败。」**

**「只由 2023 签署」（signed only by the 2023 CA）。** **这就是为什么现在的过渡形态是双签名**：**Red Hat 从 2025 年 10 月起，微软开始用两把密钥同时签署 shim**：

> **「从 2025 年 10 月开始，微软开始用两把不同的密钥签署 shim：`Microsoft Windows UEFI Driver Publisher`（2011）和 `Microsoft UEFI CA 2023` signer（2023）。在 6 月之后，他们只能用 2023 那把签了。」**

**而各家的处境不同，这个对比很有意思**：

- **AlmaLinux**：**x86_64 的 shim 双签名；而 aarch64 的 shim **只用 2023 签**。** **AlmaLinux 对此的说明很实用**：**「如果你的 ARM64 系统今天能在 Secure Boot 启用状态下启动，那它已经信任 2023 证书了。」**（因为如果它不信任，它早就启动不了了。）
- **RHEL**：**从 RHEL 9.8 和 10.2 起提供双签名 shim**，**所有受支持的 RHEL 9 和 10 z-stream 也已收到**。**而 RHEL 7.9（第一个支持 Secure Boot 的版本）不会收到双签名 shim。**
- **Rocky Linux**：也是双签名，**并且加了一句技术提醒**：**「同一个 shim 二进制携带来自两把 CA 的签名，而它能否成功启动取决于你的固件是否能够解析和验证一个 PE EFI 二进制里的多个签名，这是支持该特性的硬件上的预期行为。」**

**「取决于你的固件是否能够解析多个签名」。** **这句话是一个隐藏的兼容性风险**：**双签名依赖固件正确实现「一个 PE 文件多个签名」的解析。而这类「依赖固件正确实现某个规范细节」的地方，恰恰是老设备最容易出问题的地方。**

### 而 Linux 侧还有一个 Windows 侧没有的麻烦：dbx 真的动了

**这是我认为最该被单独指出的一条，因为它和「到期不是吊销」形成了对照。**

**Arch Wiki 的 Secure Boot 条目里现在有一条维护提示**：

> **「MS UEFI CA 2011 已在 2026 年 6 月过期。在过期之后，微软**追溯性地**把 11 个有漏洞的 Linux shim 放进了 dbx。」**

**「追溯性地把 11 个有漏洞的 Linux shim 放进了 dbx」。**

**而这件事的源头是一个真实的安全问题。CERT 的 VU#616257 写得很清楚**：

> **「微软签署的开源 shim 项目的 UEFI 引导加载器，主要是 0.9 及更早版本，被认定容易受到 Secure Boot 绕过的影响。为缓解这个风险，受影响的引导加载器将被加入 `Microsoft UEFI Forbidden Signature Database (DBX)`。」**
>
> **「攻击者可以利用这些有漏洞的 shim 引导加载器，使用一种类似 BYOVD 的技术，在早期启动阶段、操作系统初始化之前执行任意代码，从而绕过 Secure Boot 保护。」**

**编号是 CVE-2026-8863。**

**所以 Linux 侧的实际局面是**：**「到期」本身没事，但「吊销」是真实发生了的，而且是针对旧版本 shim 的。** **这意味着**：

- **如果你用的是老发行版、老 shim（0.9 及更早）**，**那么在你更新 dbx 之后，那个 shim 会被拒绝**；
- **而如果你为了保住旧 shim 而不更新 dbx**，**你就保留了一个已知可被绕过的提权路径。**

**这是一个明确的取舍，而不是一个「不用担心」的问题。** **而这里的解法只有一个方向：更新到双签名的新 shim，同时更新 dbx。**

## 六、一个几乎没人提但会咬人的副作用：更新 db 会改动 PCR7，可能触发 BitLocker 恢复模式

**这一节是我在 Red Hat 的文档里注意到的一条，而原文完全没提。**

**Red Hat 的文章在讲 TPM 相关的操作时写了这么一句**：

> **「先对一个没有变化的 PCR 值（例如 PCR0）重新封装，重启，然后才对着新的 PCR7 值重新封装。」**

**这句话的背景是：BitLocker 依赖 TPM 的 PCR 度量，而 PCR7 恰恰是记录「Secure Boot 状态与密钥数据库」的那一个。** **也就是说**：**你更新 db 这个动作，会改变 PCR7；而 PCR7 一变，TPM 的封装就与当前状态不匹配了。**

**后果**：**下次启动时 BitLocker 会认为「启动环境被改动了」，从而要求输入恢复密钥。**

**我认为这是这次事件里「操作建议最容易被漏掉」的一条，而原文的建议只提到了「备份 BitLocker recovery key」。** **备份是对的，但它的定位错了**：**原文把它写成「万一出问题」的保险，而实际上「改 db 导致 PCR7 变化」是一个**预期内**的后果，不是意外。**

**所以对任何开了 BitLocker 的机器，正确的顺序是**：

1. **先确认你能拿到 BitLocker 恢复密钥**（微软账户、AD、或打印出来的那张纸），**并且真的能读出来**；
2. **然后再去做 BIOS 更新或证书更新**；
3. **如果启动后进了恢复界面，这是可预期的，输密钥进去就行**。

**而对于 Linux 侧用 TPM 做全盘加密（systemd-cryptenroll 绑 PCR7）的机器，逻辑完全一样**：**你改了 db，PCR7 就变了，LUKS 的 TPM 解锁就会失效，需要重新入册。**

## 七、我的判断

**第一，这次事件真正的教训不是「证书会过期」，而是「信任链的更新机制本身可能被自己锁住」。** KEK 的职责是授权 db 和 dbx 的变更，而 KEK 自己也在过期清单里。**这不是设计疏忽，是任何「用信任去引导信任」的系统都会遇到的递归问题**：**你必须选择一个「不需要被更新就能更新其他东西」的根，而现实中不存在这样的根，所以任何 PKI 都必须处理「根自己也会老」这件事。** **而 KEK 这个位置的尴尬在于：它既不是根（上面还有 PK 和硬件的信任根），又承担了根的职责（授权整个数据库变更）。所以它过期的时候，代价是「中间层断了」，而修复它需要动用更上层的手段（固件更新）。**

**第二，「到期不等于吊销」这个区分，是判断「我该不该动手」的唯一依据。** **如果只记一件事，就记这句**：**Secure Boot 验证签名时看的是「信任库 + 吊销状态」，不看证书有效期。** **所以**：**一个已经装好的、由 2011 签名的 bootloader 不会因为到期而失效；而一旦它进了 dbx，那才是真的不能用了。** **这也直接推出了那条反直觉的操作建议：不要删掉 2011 CA，因为删掉等于自己动手吊销了它。**

**第三，Linux 侧的局面比 Windows 侧更需要主动关注，而原因和大多数人想的相反。** 大多数人担心的是「shim 到期会不会起不来」，**而实际上这个问题的答案是「不会」。真正会发生的是「旧 shim 被追溯性地放进 dbx」**，因为那些版本（0.9 及更早）有 CVE-2026-8863 这个可绕过的洞。**所以这次对 Linux 用户的实际要求，不是「等证书更新」，是「确认自己的 shim 是双签名的新版本，并且 dbx 已经更新」。** **前者保证能启动，后者保证安全。而这两件事方向一致，不存在取舍**，**除非你被卡在一个无法更新 shim 的老发行版上，那时候取舍才真的存在。**

**第四，我对「去检查一下你的电脑」这类建议有一点保留。** **因为**真正需要动手的是三类人**，而他们的判断标准完全不同**：

- **普通 Windows 用户**：**大概率不用做任何事**，因为微软通过月度累积更新自动推送。**唯一要确认的是「设备安全性」里没有黄字。**
- **开了 BitLocker 的机器**：**必须做一件事，但不是更新证书，是确认你能拿到恢复密钥。** 因为**改 db 会改 PCR7，这是预期行为。**
- **老设备（过保、无 BIOS 更新、非 Windows 11）**：**这一类才是真正受影响的，而他们恰恰是最没有官方路径的**，因为微软那句话已经说了：**「这类更新可能只对仍在支持期内的设备提供。」**

**而第三类人正是这次事件真正的受众，也是最不容易从「检查你的电脑」这句话里得到有效指引的群体。**

> **最后一件值得记的事，是关于「过期」这个概念本身**：**证书过期在 PKI 里从来不是一个「突然失效」的事件，它是一条缓慢生效的时间边界，而边界的另一侧不是「不能用了」，是「不能再签新的了」。** **所以每次看到「某证书即将到期」这类新闻，第一个该问的问题不是「什么东西会坏」，而是「还有谁需要用它签新东西，而他们准备好了吗」。** **这次事件的答案很具体**：**微软已经准备好了（2023 证书从 2025 年 10 月就开始双签），发行版大多准备好了（双签名 shim），而固件和过保设备没有。** **而固件这一层的更新周期不是按月算的，是按「厂商还记不记得这个型号」算的。**

## 关键事实速查

| 项目 | 内容 |
|---|---|
| **三张到期证书（微软 KB 5062710）** | **`Microsoft Corporation KEK CA 2011`：2026-06-24**；**`Microsoft Windows Production PCA 2011`：2026-10-19**；**`Microsoft UEFI CA 2011`：2026-06-27** |
| **对应新证书** | **KEK → `Microsoft Corporation KEK 2K CA 2023`**；**Windows Production → `Windows UEFI CA 2023`**；**UEFI CA → `Microsoft UEFI CA 2023` + `Microsoft Option ROM UEFI CA 2023`（拆成两张）** |
| **各自职责** | **KEK：签署对 db 和 dbx 的更新**；**Windows Production：签署 Windows Boot Manager**；**UEFI CA：签署第三方 bootloader（含 Linux shim）与 EFI 应用** |
| **历史背景** | **「自 Windows 引入 Secure Boot 支持以来，所有基于 Windows 的设备都在 KEK 和 DB 中携带了同一组微软证书。」** |
| ⭐ **到期会怎样（官方）** | **「没有收到较新 2023 证书的设备将继续正常启动和运行，标准 Windows 更新也会继续安装。」** |
| ⭐ **但会失去什么** | **「不再能够获得针对早期启动过程的新安全保护」**：**Windows Boot Manager 更新、Secure Boot 数据库与吊销列表更新、启动链新漏洞修复** |
| **官方明确的「不工作了」** | **① 新的 Secure Boot 与 Boot Manager 保护无法应用；② 早期启动环境的漏洞修复（如 BitLocker 绕过缓解、Secure Boot 吊销）不可用；③ 依赖微软 Secure Boot 信任的某些第三方组件若需新证书条目会更新失败** |
| ⭐ **KEK 门控（核心机制）** | **「密钥交换密钥是授权两个 Secure Boot 数据库变更的凭证……一台没有接收 `Microsoft Corporation KEK 2K CA 2023` 的设备，没有有效的权限去接受那个携带 `Microsoft Windows UEFI CA 2023` 的允许列表更新。」** |
| ⭐ **到期 ≠ 吊销** | **「过期不是吊销，它不会导致立即的启动失败。」**；**「UEFI Secure Boot 是拿签名去对照信任数据库和吊销状态来验证的，**不是**对照证书的有效期。」** |
| ⭐ **反直觉的操作建议** | **「不要从系统的 Secure Boot db 里移除 2011 CA。移除它会剥掉那条信任路径。」** |
| **吊销计划** | **「目前也没有吊销 `Microsoft UEFI CA 2011` 的计划。」**（微软）；**「硬件厂商没有计划在不久的将来移除或吊销 2011 证书。」**（Red Hat） |
| **兼容性矩阵** | **固件只有 2011：2011-only 能启、2023-only 不能启、双签名能启**；**只有 2023：反之**；**两者都有：全部能启** |
| ⭐ **真正的风险窗口** | **「一旦某家操作系统厂商发布了一个只由 `Microsoft UEFI CA 2023` 签署的 shim，那么任何固件还没有信任 2023 CA 的系统都将启动失败。」** |
| **shim 双签起点** | **「从 2025 年 10 月开始，微软开始用两把不同的密钥签署 shim」**（2011 与 2023），**6 月之后只能用 2023 那把** |
| **AlmaLinux** | **x86_64 双签名**；**aarch64 只用 2023 签**；**「如果你的 ARM64 系统今天能在 Secure Boot 启用状态下启动，那它已经信任 2023 证书了。」** |
| **RHEL** | **从 RHEL 9.8 / 10.2 起双签名 shim**，**所有受支持的 9 和 10 z-stream 已收到**；**RHEL 7.9 不会收到双签名 shim** |
| **Rocky Linux 的提醒** | **双签名能否启动「取决于你的固件是否能够解析和验证一个 PE EFI 二进制里的多个签名」** |
| ⭐ **Linux 侧真正的麻烦** | **Arch Wiki：`MS UEFI CA 2011` 过期后，微软「追溯性地把 11 个有漏洞的 Linux shim 放进了 dbx」** |
| **那个漏洞** | **CVE-2026-8863**，**shim 0.9 及更早**，**类似 BYOVD 的手法可在早期启动阶段执行任意代码、绕过 Secure Boot**（CERT VU#616257） |
| ⭐ **BitLocker 副作用** | **改 db 会改变 PCR7**，而 PCR7 记录 Secure Boot 状态与密钥库 → **BitLocker 可能进恢复模式**；Red Hat 的建议是**先对不变的 PCR（如 PCR0）重新封装，重启，再对新 PCR7 重新封装** |
| **Windows 侧查看** | **Windows 安全中心 → 设备安全性 → 安全启动**；黄字或 **`older boot trust configuration`** 说明未就绪 |
| **Windows 事件日志** | **来源 `TPM-WMI`**：**Event ID 1808 = 已更新成功**；**Event ID 1801 = 固件有证书但未应用 / 固件不含新证书** |
| **Linux 侧查看** | `mokutil --sb-state`；`mokutil --db \| grep 'UEFI CA 2023'`；`mokutil --kek \| grep 'KEK 2K CA 2023'`；`ls /sys/firmware/efi/efivars/ \| grep -E '^(db\|KEK\|dbx\|PK)-'` |
| **用 fwupd 补装** | `sudo dnf install -y fwupd` → `fwupdmgr refresh` → `fwupdmgr update` → 重启 → 复查 |
| ⭐ **我本机实测（第三种状态）** | **H3CBook Ultra 14T（物理机、EFI 启动）**；**`/sys/firmware/efi/efivars/` 只有 5 个变量，全是 `*Default`，没有 `PK`/`KEK`/`db`/`dbx`/`SecureBoot`**；**每个 `*Default` 属性均为 `0x06`（BOOTSERVICE + RUNTIME，无 NON_VOLATILE）** |
| ⭐ **而 `dbDefault` 里只有 2011** | 抽出证书主体名：**`Microsoft Windows Production PCA 2011`、`Microsoft Corporation UEFI CA 2011`、`Microsoft Corporation Third Party Marketplace Root`、`Microsoft Root Certificate Authority 2010`**，**无任何 2023 证书** |
| **该查的三个层次** | **① Secure Boot 现在开着吗；② 开着的话 db 有 2023 吗；③ 没开的话固件默认库有 2023 吗（决定将来能不能开）** |
| **官方对禁用 Secure Boot 的态度** | **「Secure Boot 不应当被禁用来绕过证书到期。」**（会移除针对启动级恶意软件的防护，并带来新的安全与合规风险） |
| ⚠️ **OEM 更新的限制** | **「这类更新可能只对仍在支持期内的设备提供。」** |
| ⚠️ **受影响最重的一类** | **Red Hat：老旧物理服务器、老旧笔记本台式机、无厂商固件更新的系统、从不更新 BIOS/UEFI 的专用设备** |

## 延伸阅读

- [ACPI 覆盖到底怎么做：从作者的仓库里拆出完整流程](https://freelamp.com/articles/2026-10-19_acpi-table-override-guide-initrd-cpio/)
- [为了让这台 128GB 的 RTX Spark 笔记本跑 Linux，她自己写了 ACPI 覆盖和触控板补丁](https://freelamp.com/articles/2026-10-19_rtx-spark-laptop-arch-linux-arm-nvidia/)
- [Windows Update 要换证书了：一次提前两年的公告，和它没说的部分](https://freelamp.com/articles/2026-10-09_windows-update-certificate-rotation-2027/)
- [Libreboot 26.10 加入了 EDK2 支持，而它的反 AI 政策写进了一个机器可读的文件](https://freelamp.com/articles/2026-10-16_libreboot-2610-uefi-edk2-anti-ai-policy/)
- [微软官方：证书到期与 CA 更新（KB 5062710）](https://support.microsoft.com/en-us/servicing/os/secure-boot/2025/06/windows-secure-boot-certificate-expiration-and-ca-updates)
- [微软官方：证书到期后会发生什么（KB 5079373）](https://support.microsoft.com/en-us/servicing/os/secure-boot/2026/02/when-secure-boot-certificates-expire-on-windows-devices)
