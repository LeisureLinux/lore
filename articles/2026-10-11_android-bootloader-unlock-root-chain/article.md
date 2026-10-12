---
title: "解锁 Bootloader 不等于 Root：Android 刷机链的每一层到底在解什么锁"
date: 2026-10-11
slug: android-bootloader-unlock-root-chain
tags: [Android, Bootloader, Root, Magisk, KernelSU, APatch, AVB, dm-verity, Play Integrity, Widevine, TEE, LineageOS, TWRP, 系统安全, 原创]
category: 系统与软件
author: FreeLAMP.com
original_source: "AOSP 官方文档 / Magisk 与 KernelSU 官方文档 / Play Integrity API 文档"
original_author: "FreeLAMP.com（基于 AOSP 与各方案官方文档核实）"
original_date: 2026-10-11
original_url: "https://source.android.com/docs/security/features/verifiedboot/avb"
description: "解锁 Bootloader 和获取 Root 经常被混为一谈，但它们解决的是两个完全不同层级的问题：前者在引导层解除签名校验，后者在内核与用户空间换取 UID 0。本文从 AOSP 的 Android Verified Boot 语义出发，说清 LOCKED 与 UNLOCKED 到底意味着什么、为什么解锁必须擦数据、Android 13 之后为什么多出一个 init_boot 分区；再对比 Magisk、KernelSU、APatch 三种提权方案的真实机制差异（含一处常见误传的纠正），最后交代 Play Integrity 的分级判定和 Widevine 降级这些无法绕过的代价。"
published: true
---

> 事实来源：[AOSP：Android Verified Boot 2.0](https://source.android.com/docs/security/features/verifiedboot/avb)、[AOSP：通用 boot 分区（GKI 与 init_boot）](https://source.android.com/docs/core/architecture/partitions/generic-boot)、[KernelSU 官方文档](https://kernelsu.org/)、[APatch 官方 FAQ](https://apatch.dev/faq.html)、[APatch 安装文档](https://github.com/bmax121/APatch/blob/main/docs/en/installation.md)、[Play Integrity API 文档](https://developer.android.com/google/play/integrity)
> 本文为**解读**。文中纠正了一处流传较广的说法（见第四节），并在第五节补充了 Play Integrity 的判定分层与 Widevine 的具体后果。

## 一句话结论

**解锁 Bootloader（Unlock BL）和获取 Root 经常被放在一起讨论，但它们解决的是两个完全不同层级的问题。** 用 AOSP 自己的话来说，**解锁解掉的是「验证失败是否致命」这件事**，也就是让引导链在遇到非官方镜像时不再直接拒绝；**而 Root 要的是在内核与用户空间里拿到一个能切换 UID 到 `0` 的特权通道**。**解锁 BL 是 Root 的前置条件，但绝不是 Root 本身**，两者之间隔着一整套注入、修补与隐蔽的工程。

## 一、Bootloader 解锁：它到底允许了什么

### Bootloader 在链条上的位置

设备通电后最先执行的**不是 Linux 内核**，而是固化在 Boot ROM / Flash 中的引导程序。它的职责是两个：**初始化硬件**（CPU 核心、内存控制器、存储总线、外设），以及**验证即将加载的镜像**（`boot.img`、`recovery.img`、`vbmeta` 等）是否带有可信签名。

**这里需要先把验证的层次说清楚**，因为「关闭 Secure Boot」这个说法过于笼统。现代 Android 用的是 **Android Verified Boot 2.0（AVB）**，它和「Secure Boot」不是同一个概念：

| 概念 | 作用对象 | 说明 |
|---|---|---|
| **Bootloader 内的签名校验** | 引导链本身 | 从 Boot ROM 的不可变密钥开始，逐级验证下一级引导程序与内核 |
| **AVB（Verified Boot 2.0）** | 各分区镜像 | 用 `vbmeta` 分区存放描述符：`boot` 用哈希描述符，`system` 用 hashtree 描述符，并附内核命令行描述符来启用 dm-verity |
| **dm-verity** | 只读分区的块设备 | 内核在挂载时按哈希树逐块校验，**篡改会立刻暴露而不是悄悄生效** |

**所以「解锁」触碰的是 AVB 的状态机**，而不是某一项具体校验。

### LOCKED 与 UNLOCKED 的精确语义

AOSP 对这两个状态的定义非常简洁，我认为比任何科普说法都准确：

> **在 AVB 的语境里，LOCKED 状态意味着验证错误是致命的，而在 UNLOCKED 状态下它们不是致命的。**

**这句话值得反复咀嚼**，因为它澄清了一个常见的误解：**解锁并不是「关掉了验证」**，而是**把验证结果的后果从「拒绝启动」降级为「记录并继续」**。所以：

- **解锁后设备仍然知道自己在被篡改**（verified boot state 依然会报告为 unlocked / orange）；
- **但它不再因此停止引导**；
- **这个状态会被上报给上层**，这正是后面第五节那些后果的来源。

**与状态转换绑定的两条硬性约束**（AOSP 原文要求）：

- **状态转换必须确认用户的物理在场**（`fastboot flashing unlock` 通常需要在设备屏幕上再确认一次，不能在没人看着的情况下被远程刷开）；
- **从 UNLOCKED 转回 LOCKED 时，如果设备要求全盘加密，就需要做一次数据擦除**（区别只是强度较轻）。

### 为什么解锁一定要擦数据

**这是我建议所有刷机前都要理解的一点**：解锁会擦除用户数据，**不是厂商的惩罚设计，而是安全上的必要动作**。

原因是：**在 LOCKED 状态下，加密密钥的保护与「已验证的引导状态」绑定在一起**。如果允许「先解锁、刷入自制镜像、再读走数据」，那么任何拿到你设备实物的人都可以绕过锁屏。**所以解锁这个动作本身必须让既有密钥失效**，否则它就变成了一条物理访问的数据提取通道。这也解释了为什么解锁之后你需要重新设置设备、且原有的加密数据无法恢复。

### 关于关闭验证的两种合法姿势

**一种是这里说的解锁**（设备承认自己处于 UNLOCKED，后果自负）。**另一种在某些设备上存在**：刷入**自定义 AVB 密钥**。AOSP 文档提到，Pixel 2 系列支持一个名为 `avb_custom_key` 的虚拟分区：

```bash
avbtool extract_public_key --key key.pem --output pkmd.bin
fastboot flash avb_custom_key pkmd.bin
```

**这样做的意义是**：你用自己的密钥签名自制镜像，**于是可以重新 LOCK 回去**，而引导链依然完整。**代价是**：一旦锁上你自己的密钥，官方 OTA 不再能安装（签名不匹配），而且**密钥丢失等于设备变砖**。**所以它是一条「适合长期自维护设备」的路，不是普通刷机者的路。**

> **核心结论**：解锁 BL 消除的是**引导层对镜像签名的强制性拦截**。**内核与用户空间的 Linux 权限模型、SELinux 策略、以及应用沙箱完全没有变化**。因此**解锁 BL 绝不会让系统自动获得 Root**。

## 二、Root：为什么它是一个「另加的东西」

### Android 的权限模型没有「root 应用」这个位置

Android 建立在 Linux 内核之上，其隔离模型由三层构成：**Linux UID/GID**、**应用沙箱**、以及 **SEAndroid（SELinux for Android）**。在未 Root 的系统里：

- **普通应用运行在独立沙箱中**，UID 落在 `app_X` 范围内，互相之间无法读数据；
- **即使是系统级守护进程，UID 也受限于 `system`、`radio`、`shell` 等**，**并不能任意改写 `/system`、`/vendor`**；
- **而这些分区本身就是只读的**：它们由 **dm-verity** 在挂载时按哈希树校验，**改一个字节就会立刻暴露**。

**所以「root」在这个体系里不是「打开一个开关」，而是要在用户空间里放一个能够把调用者 UID 变成 `0` 的特权通道。**

### 传统做法为什么失效了

**早年最简单的方式是把 `su` 二进制塞进 `/system/xbin`**，再配合一个授权管理器。这条路在现代 Android 上已经走不通，原因有两层：

| 机制 | 影响 |
|---|---|
| **System-as-Root（SAR）** | `/system` 直接作为根文件系统使用，不再有可写的传统路径可以顺手塞文件 |
| **动态分区（dynamic partitions）** | `/system`、`/vendor`、`/product` 等来自同一个 super 分区，**物理布局由构建时决定，运行时不可随意改写** |
| **dm-verity** | 即使你改写了，**挂载校验会失败** |

**这也解释了为什么现代方案都叫「Systemless（无系统）」**：它们的目标是**在不物理修改只读分区的前提下，让系统看起来像是被改过**。做法是**在启动早期把额外的内容叠加（overlay / bind mount）上去**，**而这一切必须在引导早期、在写保护生效之前完成**。

**而要修改引导流程，你就要动引导镜像。这正是必须解锁 BL 的原因**：

> 如果不解锁 BL，**你修改后的镜像会被引导程序直接拒绝加载**。所以链条是：**解锁 BL（允许加载非官方镜像）→ 修补引导镜像（注入提权逻辑）→ 启动早期劫持初始化流程 → 建立特权通道**。

### 一个容易被忽略的现代变化：为什么是 `init_boot.img`

**这一点在 2026 年尤其重要，因为教程里常见的老说法会让人找错文件。** AOSP 的通用 boot 分区文档写得很清楚：

- **从 Android 12 起**，通用引导镜像（GKI，Generic Kernel Image）**包含通用 ramdisk 和 GKI 内核**；
- **对于出厂即 Android 13 的设备，通用 ramdisk 被从 boot 镜像里移出，放进了单独的 `init_boot` 分区**，**boot 镜像因此只剩下 GKI 内核**。

**所以**：

- **Android 13 之前（或从 12 升级上来的设备）**：修补对象通常是 **`boot.img`**；
- **出厂 Android 13 及之后的新设备**：由于 ramdisk 搬走了，**修补对象是 `init_boot.img`**，而这恰好是 Magisk 那套「劫持 init」逻辑所需要的那部分。

**选错分区是刷机失败最常见的原因之一**，而它的根源就是这个分区拆分。

## 三、完整链路图

从一台纯净原厂设备，到完成第三方系统刷入并建立提权栈，**这里有两个分岔，而且它们互不依赖**：

```
[ 原厂设备（BL 锁定，AVB 验证为 LOCKED）]
         │
         ▼  通过 Fastboot 协议 / 官方解锁工具（需物理确认，会清空数据）
[ Unlock BL（引导层不再因验证失败而中止）]
         │
         ├───> [ 刷入第三方 Recovery（如 TWRP / Lineage Recovery）]
         │              │
         │              ▼
         │       [ 刷入第三方 ROM（如 LineageOS）] ──> 此时依然是非 Root
         │
         └───> [ 建立提权栈（修补引导镜像）]
                        │
                        ├───> Magisk（修补 boot.img 或 init_boot.img，劫持 init）
                        └───> KernelSU / APatch（在内核层拦截系统调用）
```

**这张图里最该记住的一点是那个分岔**：**刷第三方 ROM 和获取 Root 是两条独立的路**。刷了 LineageOS、GrapheneOS 这类第三方系统，**默认依然是非 Root 状态**（这是它们的有意设计）。**很多人以为「刷了机就是 root 了」，这是把两件事混成了一件。**

## 四、三种主流提权方案的机制差异

**先纠正一个流传较广的说法**：**Magisk 的核心机制是 magic mount（基于 tmpfs 的 bind mount），OverlayFS 是它在较新内核上的另一种可用手段，而 KernelSU 反而把挂载逻辑从核心里拿出去交给了「元模块」。**

这个区分不是抠字眼，因为**它直接决定了两者在「被检测」这件事上的不同表现**：**Magisk 的挂载是内置在核心里的（bind mount）**，**KernelSU 官方推荐的做法是用 `meta-overlayfs` 这类元模块来做 systemless 修改**，**文档自己的说法是这种分工「提供更多灵活性并减少检测面」**。

| 工具 | 技术实现 | 前置条件 | 特点与适用场景 |
|---|---|---|---|
| **Magisk** | **修补 `boot.img` / `init_boot.img` 的 ramdisk，用 `magiskinit` 替换 `/init`**，在引导早期以 PID 1 身份取得控制；**文件系统替换以 magic mount（tmpfs bind mount）为核心**，在支持的内核上也可用 **OverlayFS** | 解锁 BL；**无需内核源码** | **兼容性最强**。覆盖 Android 6.0 到 16+，模块生态最大。**注意：Magisk 24 起内置的 MagiskHide 已被移除，改由 Zygisk + DenyList（配合 Play Integrity Fix 一类模块）承担隐蔽工作** |
| **KernelSU** | **在内核态工作**，直接在内核空间授予 root；**提供内核接口**（可在内核态对任意进程下硬件断点、访问物理内存、拦截任意系统调用） | 解锁 BL；**需要内核源码，或使用 GKI 内核**（GKI 模式可编译进内核，也支持以模块加载的 LKM 与后加载模式） | **内核态提权**，用户空间难以通过检查 `/system` 文件或进程来识别。**挂载逻辑交由元模块（如 `meta-overlayfs`）** |
| **APatch** | **基于 KernelPatch，直接对内核镜像做二进制修补**；**SELinux 不修改上下文，而是通过 hook 绕过**；用 **SuperKey** 做超调用凭据 | 解锁 BL；**只需 stock `boot.img`，不需要内核源码**；**ARM64**；**内核 3.18–6.12**；**需要 `CONFIG_KALLSYMS=y`**；**与 Knox 保护的 Samsung 设备不兼容** | 介于两者之间：**既有 Magisk 式的「直接修补 boot 镜像」的便利，又有内核级 hook 的能力**；**可以选择不改 SELinux**，从而**在应用自己的线程上下文里直接提权（不需要 libsu 与 IPC）** |

**几个补充说明，能避免一些常见踩坑**：

- **关于 KernelSU 的「需要源码」**：官方 FAQ 的表述是**KernelSU 需要设备内核源码，而源码并不总是 OEM 提供**。这正是 **APatch 存在的理由**（它只需要 stock boot 镜像）。如果你的设备属于「OEM 不给源码」那一类，**KernelSU 的可行路径就是 GKI 内核**；
- **关于 APatch 的检测特性**：因为它**不修改 SELinux 上下文而是绕过它**，所以可以在**应用进程内部**直接拿到 root 线程，**省掉了「起一个新进程再 IPC」这一步**。这在工程上更简洁，**同时也是一个更隐蔽的形态**；
- **关于「谁更难被检测」**：三方文档各自都在强调自己的隐蔽性，**但这属于持续对抗的领域**（见下节）。

## 五、无法绕过的代价：这不是技术问题，是账本问题

**解锁 BL 和获取 Root 给了你对设备的绝对控制，但代价不是「可能有点风险」，而是几条会立即生效的具体后果。**

### 1. 硬件信任链的状态变了

**关键在于：解锁这个事实本身是被记录、并被上报的。**

- **基于 ARM TrustZone 的 TEE 安全状态会反映出来**；
- **Keymaster / Keymint（密钥与证明服务）会报告设备处于 Unlocked**；
- **于是所有以「设备完整性证明」为基础的校验都会失效**。

### 2. Play Integrity API 的分级判定（这部分值得说清）

**先纠正一个时间点**：**SafetyNet Attestation 已经被 Play Integrity API 取代**，现在讨论「过不过检测」应该以 Play Integrity 为准。它的判定是分级的：

| 判定 | 含义 | 解锁 BL 后能否通过 |
|---|---|---|
| **`MEETS_BASIC_INTEGRITY`** | 最弱的一级，只表示「检查发生在一台物理 Android 设备上」；**引导状态可以是 locked 也可以是 unlocked，可以是 verified 也可以是 unverified** | **可以**（即使已解锁、已 Root） |
| **`MEETS_DEVICE_INTEGRITY`** | 表示设备是**正品且经过认证的 Android 设备**。**Android 13 及以后，这一判定要求设备引导器处于 locked、且加载的是厂商认证镜像** | **通常不能**（Android 13+ 上尤其严格） |
| **`MEETS_STRONG_INTEGRITY`** | 最强的一级，还要求安全补丁级别在近一年内 | **在解锁 BL 的设备上被普遍认为无法通过** |

**这里有一个很值得记的细节**：Google 在 Android 13 之后**强化了 `MEETS_DEVICE_INTEGRITY`，要求它必须有硬件支撑的、正面的 verified boot 结论**。**这意味着「软件层面的伪装」不再是决定性的**。**也就是说，隐蔽手段（DenyList、Play Integrity Fix 之类）能解决的是「App 看不见 Root」，而解决不了「设备状态本身就是 Unlocked」这个硬件结论。** 这两件事经常被混为一谈，但**它们的攻防难度完全不同**。

### 3. Widevine 与流媒体清晰度

**在很多设备上，一旦解锁 BL，Widevine 安全级别会从 L1 掉到 L3**（部分设备在重新锁定后可恢复）。**原因是 L1 要求存在一条从安全引导器延伸出来的信任链，并且密钥的写入本身要求引导器处于锁定状态。** 实际后果是**高清晰度流媒体可能被降级**。

**注意这条的适用范围是「因设备而异」**：有些设备解锁后保持不变，有些会降级，有些重新锁定后能恢复。**所以它是一个需要按机型确认的事，不能一概而论。**

### 4. 攻击面扩大：你给自己开了一个内核级后门

**这是最容易被忽略的一条，而且它是纯粹的工程风险，与合规无关**：

- **提权接口本身就是一个高价值目标**。如果它的访问控制不够严格，**恶意应用只要绕过授权确认，就直接拿到内核级的全盘控制权**；
- **而「授权确认」这一层往往依赖一个运行在用户空间的管理器应用**，它自己也可能有漏洞；
- **反过来看第三种方案的设计取向**：APatch 的 SuperKey 机制、KernelSU 的内核态校验，**本质都是在试图把「授权判断」放到更早、更内层的位置**，减少被用户空间绕过的机会。

### 5. 数据安全：解锁状态下丢失设备的后果不同

**在解锁状态下，设备丢失后的风险模型发生了实质变化**：**攻击者可以刷入自定义镜像，绕过原有的锁屏与系统验证，直接通过物理接口尝试提取数据。** 而现代 Android 的**文件级加密**在这里是关键防线，**但「未加密分区」与「运行时内存挂载」这两条路径依然需要留意**。

**所以一条实用建议**：**如果你解锁了 BL，请确保全盘/文件级加密处于开启状态，并且不要给设备设置过长的解锁宽限期。** 解锁本身已经把「物理访问」的门槛降低了，**加密是剩下那层真正起作用的东西**。

## 六、总结：一条链，两种边界

| | 解锁 BL | Root |
|---|---|---|
| **所在层级** | **硬件与引导层** | **内核与用户空间** |
| **解决什么问题** | **能不能加载非官方的系统/内核镜像** | **进程能否获得 UID 0 的超级权限** |
| **本质动作** | 把 AVB 状态从 LOCKED 转为 UNLOCKED，**验证失败不再致命** | 注入特权通道（`su` / 内核 hook）**并建立授权机制** |
| **是否改变权限模型** | **完全不改变** | 直接改变 |
| **是否影响设备完整性证明** | **是（这是根源）** | 是（在已解锁的基础上进一步） |
| **能否单独存在** | **可以**（解锁后不 Root，只刷 ROM） | **不能**（必须先解锁） |

**对于开发者与安全研究人员来说，把这条链的每一层边界分清，是理解 Android 系统定制、内核调试与逆向工作的前提。** 而我认为其中最值得带走的一条判断是：

> **解锁 BL 之后，你并没有获得任何新权限，你只是把「系统拒绝你」变成了「系统允许你改，但要记账」。** 剩下的所有工作（提权、隐蔽、以及承受完整性判定的后果），都是从这一笔账开始的。

## 附：工具链相关网站

### 提权方案（Root）

| 工具 | 官方地址 |
|---|---|
| **Magisk**（源码与发布） | [github.com/topjohnwu/Magisk](https://github.com/topjohnwu/Magisk) |
| **Magisk 官方文档** | [topjohnwu.github.io/Magisk](https://topjohnwu.github.io/Magisk/) |
| **KernelSU**（官网，含安装与模块文档） | [kernelsu.org](https://kernelsu.org/) |
| **KernelSU**（源码） | [github.com/tiann/KernelSU](https://github.com/tiann/KernelSU) |
| **APatch**（官网 FAQ） | [apatch.dev](https://apatch.dev/faq.html) |
| **APatch**（源码与安装文档） | [github.com/bmax121/APatch](https://github.com/bmax121/APatch) |
| **KernelPatch**（APatch 的底层） | [github.com/bmax121/KernelPatch](https://github.com/bmax121/KernelPatch) |

> 提醒：网络上存在大量仿冒的「KernelSU / APatch 官网」下载站，**请只从上述官方地址或官方 GitHub Release 获取**，第三方站点打包的 Root 工具是植入后门的常见载体。

### 刷机与系统

| 工具 | 官方地址 |
|---|---|
| **LineageOS**（下载） | [download.lineageos.org](https://download.lineageos.org/) |
| **LineageOS**（Wiki，含设备安装指南） | [wiki.lineageos.org](https://wiki.lineageos.org/) |
| **LineageOS 浏览器刷机工具** | [flash.lineageos.org](https://flash.lineageos.org/) |
| **TWRP**（第三方 Recovery） | [twrp.me](https://twrp.me/) |
| **Android SDK Platform Tools**（`adb` / `fastboot`） | [developer.android.com/tools/releases/platform-tools](https://developer.android.com/tools/releases/platform-tools) |

### 规范与背景文档（读一手材料）

| 主题 | 地址 |
|---|---|
| **Android Verified Boot 2.0（AVB）** | [source.android.com/docs/security/features/verifiedboot/avb](https://source.android.com/docs/security/features/verifiedboot/avb) |
| **通用 boot 分区（GKI 与 `init_boot` 拆分）** | [source.android.com/docs/core/architecture/partitions/generic-boot](https://source.android.com/docs/core/architecture/partitions/generic-boot) |
| **Verified Boot 总览（含 dm-verity）** | [source.android.com/docs/security/features/verifiedboot](https://source.android.com/docs/security/features/verifiedboot) |
| **Play Integrity API**（含各判定含义） | [developer.android.com/google/play/integrity](https://developer.android.com/google/play/integrity) |
| **Play Integrity：Android 13+ 的判定改进说明** | [developer.android.com/google/play/integrity/improvements](https://developer.android.com/google/play/integrity/improvements) |

### 社区

| 站点 | 地址 |
|---|---|
| **XDA Forums**（机型专版与排障讨论） | [xdaforums.com](https://xdaforums.com/) |

## 关键事实速查

| 项目 | 内容 |
|---|---|
| **AVB 的 LOCKED / UNLOCKED** | AOSP 定义：**LOCKED 意味着验证错误是致命的，UNLOCKED 意味着不致命**（不是「关掉了验证」） |
| 状态转换的约束 | **必须确认用户物理在场**；**UNLOCKED 转回 LOCKED 时若要求全盘加密则需擦除数据** |
| **为什么解锁会擦数据** | 加密密钥的保护与已验证引导状态绑定；**不擦会让解锁变成物理访问的数据提取通道** |
| 自定义 AVB 密钥 | 部分设备（如 Pixel 2）支持 `avb_custom_key`，**可用自己的密钥签名并重新锁回**；代价是官方 OTA 失效、密钥丢失即变砖 |
| **SAR / 动态分区 / dm-verity** | 三者共同导致**传统「往 `/system/xbin` 塞 `su`」失效**，所以现代方案都是 **Systemless** |
| **`init_boot` 的来源** | **Android 12 起 GKI 镜像含通用 ramdisk；出厂 Android 13 的设备把 ramdisk 移到独立的 `init_boot` 分区**，boot 镜像只剩内核 |
| 因此修补对象 | **Android 13 之前通常是 `boot.img`；出厂 Android 13+ 是 `init_boot.img`** |
| **Magisk 的真实机制** | **`magiskinit` 替换 `/init`，在引导早期以 PID 1 取得控制**；**文件替换核心是 magic mount（tmpfs bind mount）**，较新内核也可用 OverlayFS；**Magisk 24 起移除 MagiskHide，改由 Zygisk + DenyList** |
| **KernelSU 的机制与前提** | **内核态授予 root**，可拦截任意系统调用；**需要内核源码或 GKI 内核**；**挂载逻辑交给元模块（如 `meta-overlayfs`）** |
| **APatch 的机制与前提** | **基于 KernelPatch 直接二进制修补内核镜像**；**只需 stock `boot.img`，无需内核源码**；**ARM64、内核 3.18–6.12、需 `CONFIG_KALLSYMS=y`**；**不兼容 Knox 保护的 Samsung**；**不改 SELinux 上下文而用 hook 绕过**，可在应用线程内直接提权 |
| **Play Integrity 三级** | **`MEETS_BASIC_INTEGRITY` 解锁后仍可通过**；**`MEETS_DEVICE_INTEGRITY` 在 Android 13+ 要求 locked + 认证镜像**；**`MEETS_STRONG_INTEGRITY` 在解锁设备上普遍无法通过** |
| ⚠️ 关键区分 | **隐蔽手段能解决「App 看不见 Root」，但解决不了「设备状态本身是 unlocked」这个硬件结论** |
| Widevine | 很多设备解锁后 **L1 降为 L3**（部分重新锁定可恢复）；**因机型而异** |
| 最容易被忽略的风险 | **提权通道本身就是一个内核级后门**，其授权确认层若被绕过，恶意应用可直达全盘控制 |

## 延伸阅读

- [本站：LineageOS 24 一次把 174 个设备搬上 Android 17：而它同时宣布了一条硬底线](/articles/2026-10-11_lineageos-24-changelog-32/)
- [本站：在 Linux 上原生跑安卓应用：Waydroid 实操与边界（不是模拟器，是容器化 LineageOS）](/articles/2026-09-28_android-native-on-linux-waydroid/)
- [本站：Windows Update 换证书：Win7 早就没补丁了，Win10 却还有个到 2027 年 10 月的活口](/articles/2026-10-09_windows-update-certificate-rotation-2027/)
- [AOSP：Android Verified Boot 2.0](https://source.android.com/docs/security/features/verifiedboot/avb)
