---
title: "ACPI 覆盖到底怎么做：从作者的仓库里拆出完整流程，以及哪些部分能迁移到你自己的笔记本"
date: 2026-10-19
slug: acpi-table-override-guide-initrd-cpio
tags: [ACPI, DSDT, SSDT, 覆盖, initrd, cpio, acpidump, acpiview, iasl, ACPICA, EFI stub, 内核补丁, memblock, EFI内存描述符, AML, Method, Name, Buffer, 电源管理, 笔记本, Arch Linux ARM]
category: Linux/运维
author: FreeLAMP.com
original_source: "pfeifferj/archlinuxarm-proart-p16 仓库源码与构建脚本（逐文件阅读）+ ACPI 规范与内核 ACPI 表覆盖机制"
original_author: "Josephine Pfeiffer（仓库作者）；Linux 内核 ACPI 子系统"
original_date: 2026-10-19
original_url: "https://github.com/pfeifferj/archlinuxarm-proart-p16"
description: "很多人想改笔记本的 ACPI，但不知道覆盖到底是怎么生效的。本文从 RTX Spark 那篇实测背后的仓库里，把 ACPI 覆盖的完整链条拆出来：怎么 dump 自己的表（UEFI Shell + acpiview，或从 /sys/firmware/acpi/tables 直接读）、怎么把它打成 initrd 里的 cpio 让内核在启动时加载、怎么只改几个 Method 而不是重编译整张表（为什么重编译会破坏无关的 AML）、以及 ARM64 上一个真实的allocator 陷阱（跨 EFI 描述符边界会被后期映射拒绝）。最后说明哪些部分可迁移，哪些不可。"
published: true
---

> 来源：[pfeifferj/archlinuxarm-proart-p16](https://github.com/pfeifferj/archlinuxarm-proart-p16)（**MIT 许可**，386 个文件）
> 一手材料：本文所有流程、命令、补丁内容均**逐文件阅读仓库源码**得出，包括 `acpi_builder.py`（16 KB）、`stage-acpi-dump.py`、`acpi-dump.nsh`、`power-source.sed`、`power-splice.json`、`power-method-changes.json`、内核补丁 `0001-arm64-bound-acpi-override-allocation.patch` 及其 README、`component.yaml`。
> 配套阅读：[为了让这台 128GB 的 RTX Spark 笔记本跑 Linux，她自己写了 ACPI 覆盖和触控板补丁](https://freelamp.com/articles/2026-10-19_rtx-spark-laptop-arch-linux-arm-nvidia/)
> 本文为**技术解读**。第二节关于「为什么不能重编译整张表」的分析、第五节的迁移建议是笔者补充的部分。

## 一句话结论

**先把最容易误解的一点说清：ACPI 覆盖不是「改固件」，是「让内核在启动时用一张你自己的表替换掉固件那张」。** 作者仓库里那句注释说得很直白：

> **「在 RAM 中提前应用 ACPI 归档；不要刷固件。」**（Apply early ACPI archive in RAM; do not flash firmware.）

**而这条路径在内核里有一个专门的开关，叫 `CONFIG_ACPI_TABLE_UPGRADE`。它的机制是**：**内核在早期启动时，去 initrd（initramfs）里找 `/kernel/firmware/acpi/` 目录，如果那里有 `DSDT.aml`、`SSDT.aml` 等文件，就优先使用它们，而不是固件里的对应表。**

**所以整件事的技术链条只有四步**：

1. **dump** 出你自己机器上的表；
2. **改** 你想改的地方（这一步是全部难度的所在）；
3. **打包** 成 cpio，放进 initrd；
4. **重启**，内核会用你的表。

**而这里面真正会让人卡住的从来不是第 1、3、4 步，是第 2 步。而这篇文章的重点就在第 2 步，以及一个作者踩到但很少人知道的内核 allocator 陷阱。**

## 零、背景：那些 dump 出来的文件是什么，AML 又是怎么变成文件的

**在进入流程之前，先把「你到底在和什么东西打交道」说清楚。因为 ACPI 这一套东西的名词密度很高，而很多人第一次面对 `/sys/firmware/acpi/tables/` 里那堆 `DSDT`、`SSDT15`、`FACP`、`APIC` 时会直接迷路。**

### 固件给你的不是一个文件，是一堆「表」

**ACPI 的全部内容就是一组二进制表。它们由主板固件（UEFI/BIOS）在出厂时编译好，放在闪存里，操作系统启动时读出来。而它们不是「配置文件」，是**可以被解释执行的字节码**。**

**Linux 启动时，这些表会被投影到两个地方，都是只读的：**

- **`/sys/firmware/acpi/tables/`**：**一张表一个文件，文件名就是它的签名**（比如 `DSDT`、`SSDT1`）；
- **`/sys/firmware/acpi/tables/dynamic/`**：**运行时才加载的表**（比如某些驱动用 `LoadTable` 操作码动态加载的 SSDT）。

**所以「dump」这件事，字面意思就是「把内核已经读进来的这些表，原样复制出来」。** **而 `acpidump` 这个工具做的事更绕一层：它把表按 ACPI 的 `RSDP → RSDT/XSDT → 各张表` 的指针链全部走一遍，然后打成一个 `.dat` 文本文件（十六进制 + 元信息）。**

### 四类名字先分清：DSDT、SSDT、FACP、APIC

**表很多，但对「改笔记本 ACPI」这件事，只有四类需要先记住**：

| 名字 | 它是什么 | 你在里面会看到什么 |
|---|---|---|
| **DSDT** | **「差异化系统描述表」**，每台机器**只有一张** | **几乎是全部的设备树和逻辑**：`\_SB.PCI0`、`\_SB.EC0`（嵌入式控制器）、`\_SB.BAT0`（电池）、电源方法、`_OSI` 判断 |
| **SSDT** | **「附加系统描述表」**，可以有**很多张** | **厂商把功能拆到多张表里**，比如 ASUS 把电源/EC 相关方法放进一张 OEM Table ID 为 `ASUSSSDT` 的表 |
| **FACP**（文件里常叫 FADT） | **固定 ACPI 描述表**，记录**硬件寄存器的地址** | **`DSDT` 的物理地址、电源管理寄存器、复位寄存器、`ARM_BOOT_FLAGS`** |
| **APIC/MADT** | **多 APIC 描述表**，描述**中断控制器拓扑** | **每个 CPU 核、IOAPIC、中断源覆盖** |

**而「为什么改表通常改 DSDT 和 SSDT」也就清楚了**：**FACP 和 MADT 是「硬件事实」，改它们等于欺骗内核对硬件的认知，风险极高；而 DSDT/SSDT 是「逻辑」，改它们是在改「系统怎么理解和使用这些硬件」。**

**作者改的正是 SSDT 和 DSDT**：SSDT 里那 6 个 EC 方法、DSDT 里那一处 `_OSI` 判断。

### 每张表都有同一个 36 字节的头

**这是理解「为什么 AML 文件能被校验和拼接」的关键。所有 ACPI 表都以同一个 36 字节结构开头，我从内核 `include/acpi/actbl.h` 里取出原文**：

```c
struct acpi_table_header {
    char signature[4];        /* ASCII table signature，如 "DSDT" */
    u32  length;              /* 整张表的字节数，含这个头 */
    u8   revision;            /* ACPI 规范次版本号 */
    u8   checksum;            /* 使整张表字节和为 0 */
    char oem_id[6];           /* ASCII OEM 标识，如 "NVDA\0\0" */
    char oem_table_id[8];     /* ASCII OEM 表标识，如 "ANGUS   " */
    u32  oem_revision;        /* OEM 修订号 */
    char asl_compiler_id[4];  /* ASL 编译器厂商 ID，如 "INTL" */
    u32  asl_compiler_revision;
};
```

**这五个字段在后面每一节都会回来找你**：

- **`signature`**：**决定内核认不认这张表**（不是文件名！）；
- **`length`**：**必须与文件实际大小一致**，否则内核拒绝；
- **`checksum`**：**所有字节加起来模 256 必须为 0**，所以任何改动都必须重算；
- **`oem_id` + `oem_table_id` + `oem_revision`**：**这三个决定你的表是「替换」平台表还是「追加」**。

**而「重算校验和」在代码里就是一行**（作者的做法）：

```python
modified[9] = 0
modified[9] = -sum(modified) % 256
```

**先把自己的校验和字节置零，再把全部字节求和取负模 256，写回去。** **这就是为什么你手改一个字节也必须重算校验和，否则内核会在 `Bad table checksum` 这一步扔掉你的表。**

### AML 是什么：它是字节码，不是文本

**这是整篇文章最需要建立的概念。DSDT 和 SSDT 里的内容叫 AML（ACPI Machine Language），它是**二进制字节码**，由 ACPI 虚拟机（内核里的 ACPICA）解释执行。**

**而你在网上搜到的 `.dsl` 文件是 ASL（ACPI Source Language），是它的源码形式。** **两者的关系和 C 语言非常像**：

```text
ASL 源码 (.dsl)      ← 人写、可读
      ↓  iasl 编译
AML 字节码 (.aml)    ← 机器读、不可读
      ↓  ACPICA 解释执行
```

**而反方向也有一条路，也就是「反编译」**：

```text
AML 字节码 (.aml)    ← 固件里的原始形态
      ↓  iasl -d  反汇编
ASL 源码 (.dsl)      ← 可读、可改
```

**所以 ACPI 表的修改流程，本质上是**：**从固件里拿到 `.aml` → 反汇编成 `.dsl` → 改 `.dsl` → 重新编译成 `.aml` → 替换回去。**

**而这里有一个致命的事实，它是本文第三节全部复杂度的根源**：**「反汇编再编译」不是一个无损往返。** **`.aml → .dsl → .aml` 这一圈走下来，即使你一个字符都没改，出来的字节也可能和原始文件不同。**

### 为什么反汇编再编译会「不一样」

**这有四个具体原因，而它们每一个都会在第三节变成实际麻烦**：

**① 编码不唯一。** **AML 的「包长度」字段是**变长编码**（1 到 4 字节），同一段内容可以用不同宽度编码。iasl 编译时会选一个宽度，而这个宽度不一定和你原来那张表用的一致。**

**② 反汇编可能丢失结构信息。** **有些字节序列在 AML 里是合法的，但反汇编成 ASL 时没有对应的语法能精确表达，于是 iasl 会输出一个「语义等价但写法不同」的 ASL，重新编译就成了不同的字节。**

**③ 编译器版本不同，输出不同。** **这就是为什么作者在代码里强制校验 `iasl` 必须是 20260408 这个具体版本，甚至区分「64 位构建」：**

```python
require(re.search(r"version 20260408\b", run_iasl(located, ["-v"], work)) is not None,
        f"{iasl} is not ACPICA iasl 20260408; build it from {IASL_SOURCE}")
```

**④ 注释和格式全丢了。** **`.aml` 里没有注释，所以反汇编出来的 ASL 一定和厂商写的那份不一样。**

**所以作者的结论是「编译整张表会重写无关的 AML」，而他的对策不是「想办法让它无损」，而是绕过它**：**只从编译产物里抠出那 6 个方法的字节，然后拼接回原始 `.aml`。** **这样原始表里 99% 的字节根本没经过编译器。**

**我认为理解这一层之后，第三节那些看起来过度的哈希校验就会变得合理**：**它们不是在防御「恶意的输入」，而是在防御「一个必然会发生、且无法通过肉眼发现的漂移」。**

### dump 出来的文件长什么样

**最后把「你手上会拿到什么」具体化。用两条路线拿到的东西形态不同**：

**路线 B（从 `/sys/firmware/acpi/tables/` 复制）拿到的就是**原始 `.aml` 字节**，文件名是签名：**

```text
/tmp/acpi-orig/
├── DSDT          ← 原始 AML 字节
├── SSDT1
├── SSDT2
├── FACP
└── APIC
```

**而作者的 `acpi_builder.py` 检查的正是这些文件头里的 `signature` 和 `length`，而不是文件名。它甚至允许你把这些文件改名成 `foo.bin`、`bar.bin`，因为判断完全靠内容：**

```python
with path.open("rb") as stream:
    head = stream.read(24)
if head[:4] not in found or head[:4] == b"SSDT" and head[10:24] != ASUS_SSDT:
    continue
```

**注意这一行里的 `head[10:24] != ASUS_SSDT`：它在读**第 10 到 24 字节**，也就是 `oem_id[6] + oem_table_id[8]`，用来挑出「OEM ID 是 `_ASUS_`、表 ID 是 `ASUSSSDT`」的那一张。** **这就是为什么背景里要先记住那个 36 字节头的布局：第 10 字节开始正好是 OEM 标识。**

**路线 A（UEFI `acpiview -d`）下场的文件名是 `DSDT0000.bin`、`SSDT0000.bin`、`SSDT0001.bin` 这种，带序号。** **而作者代码里有一个专门的错误提示，说明这两种形态的差别会造成什么误会**：

> **「`{path.name}` 里不正好装着一张表；删掉旧的 dump 再 dump 一次」**

**这条提示针对的正是 `acpiview` 不截断文件的坑：如果文件里残留了上一次更长的表，那么「文件大小」就会大于表头里的 `length`，而内核会以 `File length does not match table length` 拒绝它。**

### 一句话把背景收掉

**如果你只需要记住三件事**：

1. **ACPI 表 = 36 字节头 + AML 字节码主体；头里的 `signature` 决定内核认不认，`length` 和 `checksum` 决定内核收不收。**
2. **AML 是字节码，`.dsl` 是它的源码形式；`iasl -d` 反汇编，`iasl` 编译。**
3. **「反汇编再编译」不是无损往返，所以专业做法是「只替换改过的字节」，而不是「重编译整张表」。**

**后面所有流程都是在处理这三个事实的后果。**

## 一、先回答两个版本与架构问题

**这两个问题在查证之后都和我原本的印象不同，所以我把一手依据列出来。**

### `ACPI_TABLE_UPGRADE` 的版本历史：v4.7 就有了，但当时只限 x86

**关键在于它不是「v4.8 新加的功能」，而是一条分两步的历史**：

- **v4.7 时 `ACPI_TABLE_UPGRADE` 已经存在**，而它的依赖写的是：

  ```
  depends on BLK_DEV_INITRD && X86
  ```

  **注意最后那个 `X86`**：**那个版本的这个开关是 x86 专属的，arm64 根本选不到它。**

- **v4.8 时依赖被改成了架构抽象**：

  ```
  depends on BLK_DEV_INITRD && ARCH_HAS_ACPI_TABLE_UPGRADE
  ```

  **也就是把硬编码的 `X86` 换成了一个架构可以自行 `select` 的符号。**

**而这个改动是 2016 年那批提交做的，共三条**（commit 日期 2016-06-22，进入 v4.8）：

| commit | 内容 |
|---|---|
| `5d8813271f8a` | **ACPI / tables: Convert initrd table override to table upgrade mechanism**（2016-04-18） |
| `91dda51a1157` | **ACPI / tables: introduce ARCH_HAS_ACPI_TABLE_UPGRADE**（2016-06-22） |
| `38b04a74c587` | **ACPI: ARM64: support for ACPI_TABLE_UPGRADE**（2016-06-22） |

**而 v4.8 里两个架构都自己 `select` 了这个符号，我实测确认了原文**：

```
# arch/x86/Kconfig
	select ARCH_HAS_ACPI_TABLE_UPGRADE if ACPI

# arch/arm64/Kconfig
	select ARCH_HAS_ACPI_TABLE_UPGRADE if ACPI
```

**所以在今天的内核上，x86 和 arm64 都能用这个功能。而「arm64 支持 ACPI 表覆盖」这件事的起点是 v4.8（2016 年 10 月发布）。**

**还有一个更新的事实值得补**：**现代内核里还有一个 `ACPI_TABLE_OVERRIDE_VIA_BUILTIN_INITRD`**，用来支持「内核和 initrd 编在同一个镜像里」的场景。而 Kconfig 的 help 说得很清楚：

> **「本选项提供从内建的未压缩 initrd 覆盖任意 ACPI 表的功能。」**

**而它有两个附加约束**：`depends on ACPI_TABLE_UPGRADE`、`depends on INITRAMFS_SOURCE!="" && INITRAMFS_COMPRESSION_NONE`。**也就是说，只有你用的是内建且未压缩的 initramfs 时才需要它。**

### 那两个 `.aml` 文件不是 arm 专用的，x86 用同一套

**这个问题的答案很干净：完全不是 arm 专用。x86 用同样的目录、同样的机制、同样的文件名惯例。**

**一手依据是内核文档 `Documentation/admin-guide/acpi/initrd_table_override.rst`，它的例子就是 x86 的机器**（例子里用的是 `DefinitionBlock ("DSDT.aml", "DSDT", 2, "INTEL ", "TEMPLATE", ...)`），而它给的打包命令是：

```bash
mkdir -p kernel/firmware/acpi
cp dsdt.aml kernel/firmware/acpi
find kernel | cpio -H newc --create > /boot/instrumented_initrd
cat /boot/initrd >>/boot/instrumented_initrd
```

**而路径 `kernel/firmware/acpi/` 在源码里是写死在 `acpi_table_upgrade()` 里的常量**：

```c
char cpio_path[32] = "kernel/firmware/acpi/";
```

**这个常量与架构无关，因为 `acpi_table_upgrade()` 本身就在 `drivers/acpi/tables.c`，是所有用 ACPI 的架构共用的。**

### 一个我原来写错的地方：内核不按文件名匹配

**这一点必须纠正，因为它会影响你怎么命名文件。我读了 `acpi_table_upgrade()` 的完整实现，它是这样挑文件的**：

```c
for (sig = 0; sig < ARRAY_SIZE(table_sigs); sig++)
    if (!memcmp(table->signature, table_sigs[sig], 4))
        break;
```

**它读文件头 4 字节的 `signature`，然后在一个白名单数组里查。所以真正决定「这张表能不能被接受」的是**文件内容里的签名**，不是文件名。**

**而白名单 `table_sigs[]` 包含 46 个签名，都是 ACPI 规范里的表名，其中和笔记本改表最相关的几个是**：

**`ACPI_SIG_DSDT`、`ACPI_SIG_SSDT`、`ACPI_SIG_FADT`（就是 FACP）、`ACPI_SIG_MADT`、`ACPI_SIG_ECDT`、`ACPI_SIG_SRAT`、`ACPI_SIG_SLIT`、`ACPI_SIG_DMAR`、`ACPI_SIG_HPET`、`ACPI_SIG_MCFG`、`ACPI_SIG_IORT`（ARM 的中断映射表）、`ACPI_SIG_PPTT`、`ACPI_SIG_NHLT`。**

**而它还有四条硬性校验，每条都会 `pr_err` 然后跳过这个文件**：

| 校验 | 失败信息 |
|---|---|
| 文件至少有一个 ACPI 表头那么大 | `Table smaller than ACPI header` |
| **签名在 `table_sigs[]` 白名单里** | `Unknown signature` |
| **文件大小必须等于表头里声明的 `length`** | `File length does not match table length` |
| **校验和必须正确** | `Bad table checksum` |

**⚠️ 而这里有一个我原本没提到的陷阱，值得单独说**：**「文件大小必须等于表头里声明的 length」这条检查意味着，你不能把一个「比表头声明的长度更长」的文件塞进去**（比如从 `acpiview` dump 出来的文件如果带了填充字节）。**如果你 dump 出来的 `.bin` 比 `length` 字段大，这条检查会直接拒绝它，而错误信息只说「长度不匹配」，不会告诉你是填充的问题。** **解法是：用 `acpixtract` 从 `acpidump` 的输出里提取，或者手动按 `length` 字段截断。**

**另外，有两条明确的「不能覆盖」**（内核文档写得很直白）：

> **「iasl 认识的 ACPI 表都应该可以覆盖，除了：`ACPI_SIG_RSDP`（签名有 6 字节）、`ACPI_SIG_FACS`（没有普通的 ACPI 表头结构）。」**

**而最后两个限制也值得记**：**① 一次最多 64 张表**（`NR_ACPI_INITRD_TABLES`）；**② 内核如果处于 lockdown 状态，会直接忽略覆盖**，日志是 `kernel is locked down, ignoring table override`（`security_locked_down(LOCKDOWN_ACPI_TABLES)`）。**如果你在开了 Secure Boot 的机器上试这个功能而完全不生效，第二条是最可能的原因。**

### 覆盖是怎么生效的：「替换」还是「追加」

**这是另一个容易误解的地方。内核文档的原话**：

> **「注意：如果放在这里的表与平台表**匹配**（相同表签名、相同 OEMID、相同 OEM Table ID）且 OEM Revision **更新**，那么平台表会被这张表**升级**。如果放在这里的表与平台表**不匹配**（表签名不同，或 OEMID 不同，或 OEM Table ID 不同），这张表会被**追加**。」**

**所以有两种行为**：

- **替换（upgrade）**：**签名 + OEMID + OEM Table ID 三者都相同，且你的 `OEM Revision` 更大**。**这就是为什么内核文档明确要求「提高 OEM Revision」**，作者代码里也是这么做的（把 `OEM revision` 从 4 改成 5、从 1 改成 2）。
- **追加（append）**：三者有任一不同，那么这张表会被**加进去**而不是替换。**这可以用来插入一张原本不存在的表（比如插一个自定义 SSDT），但如果你本意是替换，那么「追加」会导致两张表同时存在。**

**我认为这个区分很重要，因为它是「为什么我改了表但没生效」最常见的原因**：**如果你忘了提高 OEM Revision，内核会认为平台的那张更新，于是你的表被忽略，而且不会有显眼的报错。**

## 二、第一步：dump 你自己的表，有两条路

**作者给了两条路，而我认为这个设计很值得学，因为它照顾了两种完全不同的处境。**

### 路线 A：UEFI Shell + acpiview（不需要 Linux 能启动）

**脚本本身写得很短，而它的注释解释了为什么这么做**：

```text
# Dump this P16's firmware DSDT and SSDTs to \H7607A-ACPI on the stick that
# holds this Shell, as input for provenance/hardware/power-archive-builder.py.
```

**而核心只有三条命令**：

```text
acpiview -s DSDT -d
acpiview -s SSDT -d
```

**而脚本里有一句提示很关键，因为它是很多人踩过的坑**：

> **「acpiview 会写入一个已存在的 dump 文件而不截断它。」**（acpiview writes into an existing dump file without truncating it.）

**这就是为什么脚本在 dump 前先删掉旧的 `*.bin`**：「**在 dump 之前先删掉旧的 dump，因为 acpiview 不会截断已存在的文件。**」

**而脚本的健壮性做得比一般教程细，因为它每步都检查 `%lasterror%`**：

```text
if x%homefilesystem% == x then
  echo STOP: this Shell has no own-filesystem mapping.
  exit /b 1
endif
%homefilesystem%
```

**而它最后还检查「到底 dump 出来没有」**：

```text
if not exist DSDT0000.bin then
  echo STOP: no DSDT was dumped. This Shell needs the acpiview command.
  exit /b 1
endif
if not exist SSDT0000.bin then
  echo STOP: no SSDT was dumped.
  exit /b 1
endif
```

**我认为这个「no DSDT was dumped」的检查值得单独表扬，因为它是「脚本化 dump」和「教程式的敲命令」的区别**：**`acpiview` 不是所有 UEFI Shell 版本都带，而如果它缺失，脚本会静默失败，用户会拿到一个空目录而不知道为什么。** **加一句检查，就把一个需要经验才能诊断的失败变成了一个明确的错误信息。**

**而要用这条路，还需要准备 UEFI Shell 本身。作者的 `stage-acpi-dump.py` 做了这件事，而它的做法有一处值得学**：

> **「把固定版本的 EDK2 Shell 复制到 `EFI/BOOT/BOOTAA64.EFI`，把 dump 脚本复制到 `EFI/BOOT/startup.nsh`。不分区、不格式化，也不碰 U 盘上的其他文件。」**

**「不分区、不格式化，也不碰 U 盘上的其他文件」（Nothing is partitioned or formatted and no other file on the stick is touched）。** **而它对已有文件的态度是「拒绝覆盖」**：

```python
if path.exists() or path.is_symlink():
    require(path.is_file() and path.read_bytes() == data,
            f"Refusing to replace {path}; use a stick without {name}")
```

**「拒绝替换……用一个没有这个文件的 U 盘」。** **我认为这个设计是对的：它把一个「可能破坏用户数据」的操作变成了一个「明确要求你换一个 U 盘」的提示。** **而它同时还校验了 Shell 的 SHA-256 是否匹配 `locks/hardware.json` 里 pin 的值**，所以你不会拿到一个被替换过的 Shell。

### 路线 B：从 `/sys/firmware/acpi/tables` 直接读（需要 Linux 能启动）

**作者在 `acpi_builder.py` 的文档字符串里给了这条路的完整命令**：

```bash
mkdir DIR
for table in /sys/firmware/acpi/tables/DSDT /sys/firmware/acpi/tables/SSDT*; do
    sudo cat "$table" | tee "DIR/${table##*/}" > /dev/null
done
```

**而它有一个前提条件，作者写得很明确**：

> **「Linux 启动时没有加载 h7607a-acpi.cpio，比如在这台 P16 上跑另一个发行版的 live 系统。」**

**这个前提很重要，因为它是「鸡生蛋」问题**：**如果你已经加载了覆盖表，那么 `/sys/firmware/acpi/tables/` 里是**覆盖后**的表，你 dump 出来的就不是固件的原表了。**

**而作者在代码里对这个坑做了一个主动检查，我认为这是整个仓库里最值得学的设计**：

```python
def firmware(name, data, expected, override, description):
    digest = sha(data)
    require(digest != override,
            f"{name} is the {description} from h7607a-acpi.cpio, not the firmware's; dump it with "
            "the UEFI Shell kit or from a Linux booted without that archive")
    require(digest == expected,
            f"{name} is not the {description} of firmware {FIRMWARE} (SHA-256 {digest}); "
            f"these overrides are only for BIOS {FIRMWARE}")
```

**这段代码做了两个检查，而第二个检查的意义超出这个项目**：

1. **「你 dump 出来的东西不等于我们的覆盖表」**：排除「你 dump 到了自己的覆盖」这个错误；
2. **「你 dump 出来的东西必须等于我们 pin 的那个固件版本」**：**这就是「ACPI 覆盖与固件版本强绑定」这件事的代码化。**

**第二条检查为什么必要，作者的错误信息说得很清楚**：

> **「这些覆盖只适用于 BIOS H7607BA.300」**（these overrides are only for BIOS H7607BA.300）

**我认为这是本文最该被记住的一条工程原则：ACPI 覆盖不是一个「通用的修复」，它是一个「针对某个固件版本的二进制补丁」。** **因为 AML 是字节码，而覆盖是通过「按字节偏移替换」实现的（下一节会讲），所以固件版本一变，偏移全错，而错位的结果不是「报错」，是「一个语义完全不同的表」。** **而这个检查把这种无声的错误变成了一个明确的拒绝。**

## 三、第二步：改哪里，以及为什么不能重编译整张表

**这是全部难度的所在，而作者的方案有两个非常具体的技术决定。**

### 决定一：只改 6 个 Method 的名字，不重编译整张表

**先看目标是什么。`component.yaml` 里的两条说明**：

> **「在不使用全局 OSI 覆盖的情况下启用 NVDA8400 SSPM。」**（Enable NVDA8400 SSPM without a global OSI override.）
> **「仅修复 RRA9/RRA8/WRA9/WRA8/RWEC/GBST 的缓冲区生命周期。」**（Repair buffer lifetime in RRA9/RRA8/WRA9/WRA8/RWEC/GBST only.）

**而具体的改动内容，`power-source.sed` 写得很清楚，因为它是「字面替换脚本」**：

```text
# \_SB.EC0.RRA9
3590,3604s/Local0/RSPB/g
3590s/RSPB = Buffer/Name (RSPB, Buffer/
3590s/{}/{})/
```

**也就是说：在 ASL 源码的第 3590 到 3604 行，把 `Local0` 全部改成 `RSPB`；然后把第 3590 行的 `RSPB = Buffer` 改成 `Name (RSPB, Buffer`，把 `{}` 改成 `{})`。**

**翻成 AML 的语义，这是一个非常具体的问题**：**原来的代码把缓冲区存在一个**局部变量** `Local0` 里，而 AML 的局部变量在方法返回时就被销毁。改动之后，同一个缓冲区变成了一个**命名对象** `Name (RSPB, ...)`，它的生命周期跨越方法调用。**

**我认为这个改法的精妙之处在于它是一个「最小侵入」的修复**：**它没有改变任何逻辑，只改变了那个缓冲区的存储位置。而这恰好是「缓冲区生命周期」这个 bug 的正确修法。**

**而 `power-method-changes.json` 给出了每个方法的精确位置，包括**：

```json
{
  "method": "RRA9",
  "path": "\\_SB.EC0.RRA9",
  "local_replaced": "Local0",
  "new_name": "RSPB",
  "source_line": 3586,
  "original_source_sha256": "810af402...",
  "modified_source_sha256": "a9ee2c64..."
}
```

**注意每一条都带 `original_source_sha256` 和 `modified_source_sha256`**，也就是说**每一个方法的原文是什么、改完应该是什么，都被 pin 住了。**

### 决定二：编译后只「拼接」那 6 个方法，而不是替换整张 SSDT

**这是整个仓库里最有技术含量的设计，而 `acpi_builder.py` 的文档字符串解释得最清楚**：

> **「SSPM 只改它的 `_STA` 谓词，而六个编译后的 ASUS 方法被**拼接**进原始 SSDT，因为编译整张表会重写无关的 AML。」**
>
> **（SSPM changes only its _STA predicate, and six compiled ASUS methods are spliced into the original SSDT, since compiling the whole table would rewrite unrelated AML.）**

**「编译整张表会重写无关的 AML」（compiling the whole table would rewrite unrelated AML）。这句话解释了很多人的困惑，值得展开。**

**为什么重编译会「重写无关的 AML」？因为 ASL 反编译再编译不是一个无损往返。** **具体原因有几个**：**① iasl 在反汇编时会规范化某些编码（比如 package length 用最宽的编码）；② 不同的 iasl 版本对同一段 ASL 可能生成不同的字节；③ 反汇编时可能丢失一些元信息，而重新编译时会用默认值填补。** **结果就是：即使你的 ASL 只改了一个名字，重新编译出来的整张表也和原表到处都不一样。** **而这张表是要被加载进内核的，任何「无关」的差异都可能带来不可预测的后果。**

**所以作者的做法是**：**先把改过的 ASL 编译一遍，然后从编译产物里**只提取那 6 个方法的字节**，再把这 6 段字节**拼接**回原始的 SSDT 二进制里。**

**而这段代码的实现比我预想的严谨得多，我完整读了一遍，它做了四件事**：

**第一，从编译产物里按名字找方法，并要求「恰好一个匹配」**：

```python
def compiled_method(compiled, name, digest):
    matches = []
    for offset in range(36, len(compiled) - 6):
        if compiled[offset] != 0x14:      # MethodOp
            continue
        length, width = pkg_length(compiled, offset + 1)
        name_start = offset + 1 + width
        if compiled[name_start:name_start + 4] == name.encode("ascii"):
            end = offset + 1 + length
            require(end <= len(compiled), f"Truncated {name} method")
            matches.append(compiled[offset:end])
    require(len(matches) == 1, f"Expected exactly one compiled {name} method")
    return exact(matches[0], digest, f"Compiled {name} method")
```

**第二，替换时校验原文的哈希、新长度，以及**外层容器的长度**也要跟着改**：

```python
delta = sum(len(data) - (b - a) for a, b, data in patches if start <= a < b <= end)
require(delta == row["scope_added_bytes"], "Wrong enclosing AML length adjustment")
patches.append((offset, offset + width, encode_length(old_length + delta, width)))
```

**「Wrong enclosing AML length adjustment」。** **这是 AML 的一个结构特性：每个 Scope 和 Device 都有自己的 package length 字段，而里面替换了多长的字节，外面那个长度就必须跟着改。** **而更麻烦的是，AML 的长度字段是**变长编码**（1 到 4 字节，首字节的高两位指示后面还有几个字节），所以「加了几十个字节」可能会让长度字段本身的宽度变掉。** **作者的 `encode_length()` 专门处理了这个问题，而且它有一句检查：**

```python
require(0 <= length < (1 << (6 if width == 1 else 4 + 8 * (width - 1))),
        "New AML package length changes its encoded width")
```

**「新的 AML package 长度改变了它的编码宽度」。** **如果一个替换让外层 Scope 的长度从「1 字节能表示」变成「需要 2 字节」，那么整个结构就要重新编码，而这个检查会直接拒绝，而不是产出一个畸形的表。**

**第三，替换是**从后往前**做的，防止偏移失效**：

```python
for start, end, data in sorted(patches, reverse=True):
    require(36 <= start < end <= last_start, "Overlapping AML replacements")
    modified[start:end] = data
    last_start = start
```

**「Overlapping AML replacements」这个检查防的是「两段替换区间重叠」，而 `last_start` 这个游标保证「上一次替换的起点必须比这一次的终点更靠后」。**

**第四，改完之后重算长度字段和校验和**：

```python
struct.pack_into("<I", modified, 4, len(modified))   # 表长度
struct.pack_into("<I", modified, 24, 2)              # OEM revision = 2
modified[9] = 0
modified[9] = -sum(modified) % 256                   # 校验和
table(modified, b"SSDT", b"_ASUS_ASUSSSDT", 2)
```

**`modified[9] = -sum(modified) % 256` 这一行是 ACPI 表校验和的标准算法：把第 9 字节（校验和字段）置零，求和，取和的负值模 256。** **而它接着用 `table()` 函数验证了一遍结果**，也就是**自己产出的表必须通过自己的一致性检查**。

**我认为这套做法的价值不在于「它会拼接字节」，而在于它把「字节级操作」做成了可验证的**：**每一个原始方法有哈希、每一个新方法有哈希、每一处长度调整有预期值、最终产物有哈希，而所有这些哈希都写在 `power-splice.json` 和 `power-method-changes.json` 里。** **结果是：如果固件版本不对，或者 iasl 版本不对，或者拼接逻辑有 bug，任何一处不匹配都会让构建停下来，而不是产出一个能启动但行为诡异的表。**

### 决定三：SSPM 那个改动是「改谓词」，不是「全局 OSI 覆盖」

**`acpi_builder.py` 里这一段看得最清楚**：

```python
def patch_dsdt(original):
    exact(original, DSDT_INPUT, "Firmware DSDT")
    table(original, b"DSDT", b"NVDA\0\0ANGUS   ", 4)
    start = 0x10269
    predicate = b"_OSI\x0dWindows 2022\0"
    require(original[start:start + len(predicate)] == predicate, "SSPM predicate changed")
    modified = bytearray(original)
    modified[start:start + len(predicate)] = b"\0" + b"\xa3" * (len(predicate) - 1)
    struct.pack_into("<I", modified, 24, 5)
    ...
```

**这里的 `0xa3` 是 AML 的 `Noop` 操作码。所以这个改动的含义是**：**把 `_OSI("Windows 2022")` 这个判断「打掉」：第一个字节置零，剩下的字节全部替换成 `Noop`。** **而 `_OSI` 是 ACPI 里那个著名的「报告我是哪个操作系统」的机制，厂商经常用它来「只在 Windows 上启用某个功能」。**

**而 `component.yaml` 那句说明点出了关键**：

> **「在不使用全局 OSI 覆盖的情况下启用 NVDA8400 SSPM。」**

**「不使用全局 OSI 覆盖」（without a global OSI override）。**

**这里有一个非常实用的技术区分，我认为值得单独讲**：**传统的做法是给内核传 `acpi_osi="Windows 2022"` 这个启动参数，让**整个系统**都假装自己是 Windows 2022。而这个做法的副作用是：所有依赖 `_OSI` 判断的地方都会走 Windows 分支，包括那些你并不想改的地方。** **而作者的做法是**只把这一处 `_OSI` 调用替换成 `Noop`**，于是**只有这一个判断失效（也就是那一处的条件恒为假或被跳过），其他所有 `_OSI` 调用保持原样。**

**我认为这是本文最值得推荐给普通用户的一条技巧**：**如果你的笔记本某个功能「只在 Windows 下启用」，先用 `acpi_osi` 试，如果它带来了别的副作用，那么「精确地把那一处 `_OSI` 调用打掉」是一个更可控的方案。** **当然，它的代价是你必须做完整的 dump + 改表 + 打包流程，而不是加一个启动参数。**

## 四、第三步：打成 cpio，放进 initrd

**这一步在代码里很短，但它的细节决定了「能不能启动」**：

```python
def archive(dsdt, ssdt):
    result = b"".join(member(name, b"", stat.S_IFDIR | 0o755, inode)
                      for inode, name in enumerate(("kernel", "kernel/firmware", "kernel/firmware/acpi"), 1))
    result += member("kernel/firmware/acpi/DSDT.aml", dsdt, stat.S_IFREG | 0o644, 4)
    result += member("kernel/firmware/acpi/SSDT.aml", ssdt, stat.S_IFREG | 0o644, 5)
    result += member("TRAILER!!!", b"", 0, 6)
    result += bytes(-len(result) % 512)
```

**关键点有两个，都是内核 ACPI 子系统的硬性要求**：

**第一，路径必须是 `kernel/firmware/acpi/`。** **这是内核在 `acpi_table_upgrade()` 里写死的前缀，不是可以随便改的。**

**第二，惯例是 `DSDT.aml` / `SSDT.aml`。** **但这里有一个重要更正：内核**不**按文件名匹配，它按文件里的表签名匹配。**`acpi_table_upgrade()` 会读每个文件头 4 字节的 `signature`，到 `table_sigs[]` 数组里查。所以文件名其实只是给你自己看的，真正起作用的是文件内容。**（详见下一节。）**

**而作者是**手写 cpio 格式**的，没有调用 `cpio` 命令**：

```python
def member(name, data, mode, inode):
    name = name.encode("ascii") + b"\0"
    fields = (inode, mode, 0, 0, 2 if stat.S_ISDIR(mode) else 1,
              0, len(data), 0, 0, 0, 0, len(name), 0)
    entry = b"070701" + b"".join(f"{value:08x}".encode() for value in fields) + name
    entry += bytes(-len(entry) % 4)
    entry += data
    return entry + bytes(-len(entry) % 4)
```

**`070701` 是「new ASCII」格式的 cpio 魔数，而 `member()` 实现了它的头部结构（13 个十六进制字段）+ 名字 + 4 字节对齐 + 数据 + 4 字节对齐。**

**为什么要手写而不是调 `cpio`？我认为有两个原因，而第二个更重要**：

1. **避免依赖**：构建过程不需要 `cpio` 命令，也不受它的版本和默认参数影响；
2. **可复现**：手写的话，产出的字节完全由代码决定，而作者给这个归档 pin 了 SHA-256（`311dc5b4...`）。**用 `cpio` 命令的话，inode 号、时间戳这些字段可能会让每次产出都不同。**

**而 `TRAILER!!!` 那个条目是 cpio 格式要求的结束标记，最后那行 `bytes(-len(result) % 512)` 是把整个归档补齐到 512 字节边界。** **这些都是格式细节，但漏掉任何一个，内核就找不到那张表。**

**而放进 initrd 之后，还有一件事需要说清**：**这个 cpio 必须被**包含在 initrd 里**，而不是放在 `/boot` 旁边。** 作者的做法是把它作为 `h7607a-acpi.cpio` 并通过 `assets/hardware/acpi/` 路径提供，而在安装器里它会被合并进 initramfs。

## 五、一个很少人知道的陷阱：跨 EFI 描述符边界会被拒绝

**这一节我认为是整篇文章最有价值的部分，因为它是作者实际踩到的坑，而且**这个坑与 ACPI 覆盖的逻辑完全无关**：它是内核 allocator 的问题。**

**现象描述得很具体**（来自补丁的 README）：

> **「H7607BA 的启动录像 `IMG_1427.MOV` 显示，一个位于 `0x2050a00000`、长度 `0x12144` 的替换 DSDT 跨过了 EFI 描述符边界 `0x2050a0d000`。内核先接受了早期的表映射，然后用『requested region covers multiple EFI memory regions』拒绝了它的永久映射。ACPICA 报告 `AE_NO_ACPI_TABLES`；结果 USB、NVMe 和 GPU 枚举都无法进行。」**

**这段描述里的因果链非常清楚，值得拆成四步**：

1. **内核把 initrd 里的覆盖表复制到一块内存**（用 `memblock_phys_alloc_range`）；
2. **这块内存**跨过了两个 EFI 内存描述符的边界**（因为 memblock 会**合并**相邻的可用描述符，所以它以为这是一整块连续内存）；
3. **早期的表解析阶段接受它**（因为那时还没有建立永久映射，只是临时映射）；
4. **但后期的 `acpi_os_ioremap()` 拒绝它**（因为它不允许一个映射跨多个 EFI 内存区域），报 `AE_NO_ACPI_TABLES`。

**而后果是全面的**：「**USB、NVMe 和 GPU 枚举都无法进行。**」**也就是说：系统看起来在启动，但所有 PCIe 设备都找不到。**

**而作者给的补丁解决了这个问题，它的思路是「不要让分配跨描述符」**：

> **「它增加了一个架构分配钩子。ARM64 在**单个**可用的、write-back、非 runtime 的 EFI conventional-memory 描述符内部保留完整的原生页。现有的 memblock 保留、NOMAP 处理和 ACPI 映射保护保持不变。**没有合适的描述符就意味着明确的分配失败；不存在跨描述符的回退。**」**

**「没有合适的描述符就意味着明确的分配失败；不存在跨描述符的回退」（No fitting descriptor means an explicit allocation failure; there is no fallback across descriptors）。**

**而补丁的代码逻辑是**：

```c
for_each_efi_memory_desc(md) {
    if (md->type != EFI_CONVENTIONAL_MEMORY ||
        !(md->attribute & EFI_MEMORY_WB) ||
        (md->attribute & EFI_MEMORY_RUNTIME))
        continue;
    start = ALIGN(md->phys_addr, PAGE_SIZE);
    end = md->phys_addr + (md->num_pages << EFI_PAGE_SHIFT);
    end = ALIGN_DOWN(min(end, max_addr), PAGE_SIZE);
    if (end <= start || size > end - start)
        continue;
    addr = memblock_phys_alloc_range(size, PAGE_SIZE, start, end);
    if (addr) { ...; return addr; }
}
pr_err("No single usable EFI region can hold the ACPI table overrides\n");
return 0;
```

**也就是说：它遍历所有 EFI 描述符，只考虑「conventional memory + write-back + 非 runtime」的那些，然后在**单个描述符的范围之内**分配。如果一个描述符装不下，就试下一个；如果全都装不下，就明确失败。**

**而补丁还解决了另一个细节问题**：

> **「在每个候选被约束之前，先解析 accessible-memory 哨兵值。」**

```c
if (max_addr == MEMBLOCK_ALLOC_ACCESSIBLE)
    max_addr = memblock_get_current_limit();
```

**这是因为 `ACPI_TABLE_UPGRADE_MAX_PHYS` 可能等于 `MEMBLOCK_ALLOC_ACCESSIBLE` 这个特殊的哨兵值，而它不是一个真实的物理地址。如果不先把它解析成实际限制，那么 `min(end, max_addr)` 就会算出一个荒谬的结果。**

**我认为这个补丁的形态值得单独评价，因为它展示了一个好的上游补丁应该长什么样**：

- **用 `__weak` 默认实现保留原行为**，所以不影响其他架构：

```c
phys_addr_t __init __weak
arch_alloc_acpi_tables(phys_addr_t size, phys_addr_t max_addr)
{
    return memblock_phys_alloc_range(size, PAGE_SIZE, 0, max_addr);
}
```

- **有明确的失败日志**：`pr_err("No single usable EFI region can hold the ACPI table overrides")`；
- **成功时也打印细节**：`pr_info("Table override allocation %pa (%llu bytes) within EFI region %pa-%pa")`；
- **并且它是**针对特定上游 commit** 打的（`Base: NVIDIA/NV-Kernels 2234cd7f8f8a...`），而不是硬套在任意内核上。

**而我在读这段代码时意识到一件事，值得对普通用户说明**：**这个坑不是 RTX Spark 独有的。** **任何在 ARM64 上使用 ACPI 表覆盖（`CONFIG_ACPI_TABLE_UPGRADE` + initrd 里的 `kernel/firmware/acpi/`）的系统，都可能遇到同样的分配跨边界问题。** **而它特别隐蔽，因为**它取决于你的机器有多少可用内存，以及 EFI 描述符恰好在哪个地址被切开**。** 换句话说：**同一台机器，内存容量不同、或者固件版本不同，都可能表现成「能启动」和「不能启动」两种结果，而原因与你的覆盖表内容毫无关系。**

## 六、这套做法哪些能迁移到你自己的笔记本

**这一节是我认为你（问这个问题的读者）最需要的部分，所以我把「可迁移」和「不可迁移」分开列。**

### 可以直接迁移的

**① dump 的方法。** 两条路都通用：**UEFI Shell + `acpiview`（适用于 Linux 还起不来的情况），或者从 `/sys/firmware/acpi/tables/` 直接读（适用于 Linux 能启动）。** 而那个「先删旧 dump，因为 acpiview 不截断」的坑，在所有机器上都成立。

**② initrd 覆盖的机制。** `kernel/firmware/acpi/DSDT.aml` 这个路径和文件名是内核约定的，与硬件无关。**你只要确认内核开了 `CONFIG_ACPI_TABLE_UPGRADE`**（大多数发行版默认开，可以 `grep ACPI_TABLE_UPGRADE /boot/config-$(uname -r)` 确认）。

**③ 「只改_method 不重编译整表」的思路。** 这是最重要的可迁移经验。**具体做法是**：用 `iasl -d` 反汇编、改 ASL、`iasl` 编译、然后**只把你改过的那几个方法（或那几段字节）拼接回原表**，而不是用编译产物替换整张表。**如果你嫌手写拼接太麻烦，一个更简单的替代是：只替换你确认过的、长度变化可控的那几段，其余保持原样。**

**④ 「`_OSI` 精确打掉」而不是全局 `acpi_osi` 的技巧。** 如果你的需求是「让某个 Windows-only 的功能启用」，先试 `acpi_osi=`，如果它有副作用，再考虑精确打掉那一处 `_OSI` 调用（把它替换成 `Noop`）。

**⑤ 版本绑定与哈希校验的做法。** **一定要记下你的固件版本，并给原始 dump 和最终产物都留哈希。** 因为 ACLI 覆盖是**二进制补丁**，固件一升级就必须重做。

### 不能直接迁移的

**① 具体的改动内容。** `RRA9`、`RRA8`、`WRA9`、`WRA8`、`RWEC`、`GBST` 这六个方法，是 ASUS 在这台机器上的 EC（嵌入式控制器）电池/电源方法。**它们的名字和内部逻辑是 ASUS 的实现细节**，你的笔记本（任何品牌）几乎不可能有同名同结构的方法。

**② 具体的字节偏移。** 所有 `0x10269`、`3590,3604` 这类偏移都是**这个固件版本**的产物。换一台机器、换一个固件版本，全部失效。

**③ ARM64 的 allocator 补丁。** 如果你用的是 x86_64，这个坑通常不存在（因为 `ACPI_TABLE_UPGRADE_MAX_PHYS` 和 EFI 描述符布局不同）。**而如果你确实在 ARM64 上遇到 `AE_NO_ACPI_TABLES`，那么这个补丁的思路（在单个 EFI 描述符内分配）是可以参考的。**

### 我建议的最小可行路径

**如果你只是想「改一处 ACPI 行为」，而你的 Linux 已经能启动**，那么最短路径是：

1. **`cp -r /sys/firmware/acpi/tables /tmp/acpi-orig`**，并记下 `dmesg | grep -i acpi` 里的固件版本；
2. **`iasl -d DSDT`** 反汇编，找到你要改的那一处；
3. **只改那一处**，`iasl` 编译；
4. **如果长度没变**（这是最省事的情况），直接把你编译出的那个方法段替换回原表，或者干脆整表替换（长度不变时风险小得多）；
5. **打成 `kernel/firmware/acpi/DSDT.aml` 的 cpio**，加进 initrd；
6. **重启，用 `dmesg | grep -i "Table Upgrade"` 确认内核确实用了你的表**。

**「如果长度没变」这个条件是关键，也是我建议你优先追求的目标**：**因为长度一变，你就要处理外层 Scope/Device 的 package length，而那个变长编码很容易出错。** **而如果你能把改动做成「等长替换」（比如把一个名字换成同样长度的另一个名字，或者把一个调用换成同样长度的 `Noop`），整个流程会简单一个量级。**

> **最后一个提醒，关于风险**：**ACPI 表是内核在设备枚举之前加载的，所以一张错的表可以让系统连看都看不到设备，甚至完全无法启动。** **所以务必保留一条「不加载覆盖」的启动路径**（比如在 bootloader 里留一个不带那个 cpio 的条目），并且**先在能启动的前提下验证，再把它固化进默认 initrd。** **作者仓库里那句「不要刷固件」也是同一个道理：** **RAM 里的表重启即失效，而刷进固件的表是不可逆的。**

## 七、Secure Boot 会挡住这件事吗：会，但机制和你想的不一样

**这是一个非常容易问错的问题。我一开始也以为「开了 Secure Boot 就没法改 initrd」，而查完之后发现：Secure Boot 本身不拦这个动作，它拦的是另一层，而那一层恰好把 ACPI 表覆盖列为禁止项。**

### 先纠正一个可能的误解：Secure Boot 不校验你的 initrd 内容

**很多人以为开启 Secure Boot 之后，initrd 是被签名校验的。这在主流方案里不成立。**

**原因在于签名的对象。以 shim + GRUB 这套链路为例**：

- **shim 是被微软签名的，由固件验证**；
- **GRUB/kernel 由 shim 用 MOK（Machine Owner Key）验证**；
- **而 initrd 没有对应的签名校验环节**（**除非你启用了 IMA appraisal，那是另一套机制**）。

**所以在「把 cpio 塞进 initrd」这个动作上，Secure Boot 不会拦你。你完全可以改 initrd，也可以启动。**

### 真正会拦你的是 kernel lockdown，而它由 Secure Boot 自动触发

**这是关键的一环。`kernel_lockdown(7)` man page 里有一句非常明确的表述**：

> **「在一台支持 EFI 的 x86 或 arm64 机器上，如果系统以 EFI Secure Boot 模式启动，lockdown 会被自动启用。」**
>
> **（On an EFI-enabled x86 or arm64 machine, lockdown will be automatically enabled if the system boots in EFI Secure Boot mode.）**

**而这个自动触发的机制在早期是一个编译选项 `CONFIG_LOCK_DOWN_IN_EFI_SECURE_BOOT`**，LWN 当年介绍这批补丁时写得很直白：

> **「启用 `CONFIG_LOCK_DOWN_IN_EFI_SECURE_BOOT` 会导致 EFI secure boot 触发内核 lockdown。」**

**而现在这个行为已经整合进 lockdown LSM 本身，默认随 Secure Boot 生效。** **所以链路是**：

```text
Secure Boot 开启
      ↓  （自动）
kernel lockdown 进入 integrity 级别
      ↓
LOCKDOWN_ACPI_TABLES 被禁止
      ↓
acpi_table_upgrade() 直接返回，完全不读你的 cpio
```

### 而 lockdown 里那一条，名字就叫「modifying ACPI tables」

**我在内核源码 `security/security.c` 里找到了 `lockdown_reasons[]` 这张表，它有 31 项，而其中一项的原文是**：

```c
[LOCKDOWN_ACPI_TABLES] = "modifying ACPI tables",
```

**也就是说：lockdown 拦的不是「改 initrd」这个文件操作，而是「修改 ACPI 表」这个行为本身。**

**而它属于哪个级别，也是可以从枚举顺序读出来的。`include/linux/security.h` 里 `enum lockdown_reason` 的顺序是**：

```text
LOCKDOWN_NONE
LOCKDOWN_MODULE_SIGNATURE
...
LOCKDOWN_MSR
LOCKDOWN_ACPI_TABLES        ← 在这里
LOCKDOWN_DEVICE_TREE
...
LOCKDOWN_INTEGRITY_MAX      ← integrity 级别的边界
LOCKDOWN_KCORE
...
LOCKDOWN_CONFIDENTIALITY_MAX
```

**`LOCKDOWN_ACPI_TABLES` 在 `LOCKDOWN_INTEGRITY_MAX` **之前**，所以它属于 **integrity** 级别。而这意味着**：

- **`lockdown=integrity`（也就是 Secure Boot 自动触发的那个级别）就足以禁掉它**；
- **不需要 confidentiality 级别**。

**man page 列出的 integrity 级禁止项里，有三条和 ACPI 直接相关**：

> **「ACPI 表的覆盖。」（The overriding of ACPI tables.）**
> **「ACPI 错误注入的使用。」**
> **「ACPI RDSP 地址的指定。」**
> **「ACPI 自定义方法的使用。」**

**注意第一条的措辞：不是「限制」，是列在「被禁用或受限制」那一组的 `overriding of ACPI tables` 下面，和 `/dev/mem`、BPF、kprobes 并列。这个级别非常明确。**

### 那实际会发生什么：一个静默的跳过

**我特意强调「静默」，因为这是实际踩坑时最容易困惑的地方。**

**回到内核那段代码（`acpi_table_upgrade()` 的实现）**：

```c
if (table_nr == 0)
    return;

if (security_locked_down(LOCKDOWN_ACPI_TABLES)) {
    pr_notice("kernel is locked down, ignoring table override\n");
    return;
}
```

**注意这个检查的位置：它在「已经找到表」之后才做。** **而它只输出一条 `pr_notice` 级别的日志，然后 `return`。**

**所以如果你开了 Secure Boot 又塞了 cpio，实际表现是**：

- **系统正常启动**（不会报错，不会拒绝启动）；
- **你的表完全没有被应用**；
- **`dmesg` 里只有一行 `kernel is locked down, ignoring table override`**，而它在大量启动日志里非常不显眼。

**我认为这是一个很典型的「安全机制的可用性代价」：它做对了（拒绝未授权的表修改），但它的反馈方式让「我改了但没生效」这个诊断变得困难。** **而如果你不知道要找这一行，你会怀疑是自己改的表有问题，而实际上根本没走到那一步。**

### 一个可执行的确认流程

**在你动手做任何覆盖之前，先花十秒确认三件事**：

**① 现在是不是在 lockdown 里？**

```bash
cat /sys/kernel/security/lockdown
```

**输出形如 `[none] integrity confidentiality`，方括号括住的那个就是当前级别。我的机器上就是 `[none]`（没开 Secure Boot）。** **如果是 `[integrity]` 或 `[confidentiality]`，那么 ACPI 表覆盖已经被禁。**

**② 内核是不是有表覆盖能力？**

```bash
grep -E 'ACPI_TABLE_UPGRADE|LOCKDOWN' /boot/config-$(uname -r)
```

**我本机（一份真实的 fedora 系内核配置）的输出是**：

```text
CONFIG_ACPI_TABLE_UPGRADE=y
CONFIG_ARCH_HAS_ACPI_TABLE_UPGRADE=y
CONFIG_SECURITY_LOCKDOWN_LSM=y
# CONFIG_SECURITY_LOCKDOWN_LSM_EARLY is not set
CONFIG_LOCK_DOWN_KERNEL_FORCE_NONE=y
# CONFIG_LOCK_DOWN_KERNEL_FORCE_INTEGRITY is not set
```

**也就是说：能力有（`=y`），而默认级别是 none（`FORCE_NONE=y`）。** **而 `SECURITY_LOCKDOWN_LSM_EARLY` 未开启这一项值得注意**：**它决定 lockdown 是否在早期就生效。如果它没开，那么「早期启动阶段」的一些检查可能会晚一点才起作用。**

**③ Secure Boot 到底开没开？**

```bash
mokutil --sb-state
```

**或者直接读 EFI 变量（不需要装工具）**：

```bash
od -An -t u1 -N1 /sys/firmware/efi/efivars/SecureBoot-8be4df61-93ca-11d2-aa0d-00e098032b8c
```

**最后那个字节是 `1` 就是开着，`0` 就是关着。**

### 如果你必须保留 Secure Boot，还有没有别的路

**有三条，而它们的代价和风险依次上升。**

**方案一：`CONFIG_EFI_CUSTOM_SSDT_OVERLAYS`（最温和，但只能加 SSDT）**

**这是我在读源码时发现的一条很多人不知道的路径。内核里有一个开关**：

```
config EFI_CUSTOM_SSDT_OVERLAYS
	bool "Load custom ACPI SSDT overlay from an EFI variable"
```

**它的用法是给内核传启动参数 `efivar_ssdt=<变量名>`，内核会从 EFI 变量里读一张 SSDT 并加载。** **而关键在于：它**也会**检查 lockdown。**

```c
static int __init efivar_ssdt_setup(char *str)
{
    int ret = security_locked_down(LOCKDOWN_ACPI_TABLES);
    if (ret)
        return ret;
    ...
}
__setup("efivar_ssdt=", efivar_ssdt_setup);
```

**所以这条路在 Secure Boot 下同样被挡住。** **而它即使能用，也只是「追加一张 SSDT」，不能替换 DSDT。**

**方案二：在 lockdown 生效前加载（理论上可行，实践上不推荐）**

**`SECURITY_LOCKDOWN_LSM_EARLY` 这个选项的存在本身就说明了一个时间窗问题**：**如果 lockdown 的初始化不是 early 的，那么在某些早期代码路径上它可能还没生效。** **但我不建议把方案建立在「抢在安全检查之前」上，因为**：**第一，这个窗口在不同内核版本上行为可能变化；第二，这实质上是在绕过一项安全机制，而你本来是为了安全才开 Secure Boot 的。**

**方案三：关掉 Secure Boot（最直接，也是作者的选择）**

**回到作者的场景：她是在一台要跑 Linux 的笔记本上做这件事。而她的做法是**：

> **「用 Secure Boot 关闭的状态从 U 盘启动这台 P16。」**（Boot the P16 from the stick with Secure Boot disabled）

**我认为这个选择在这个场景下是合理的，理由有三个**：

- **这是她自己的机器**，威胁模型里没有「有人物理接触并篡改 initrd」这一项；
- **她做的改动是「修复一个厂商固件的 bug」**，而不是「绕过安全边界」；
- **她的替代方案代价更高**（买一台新 AP、或者接受数据损坏，见另一篇）。

**但这个选择不通用。** **如果你在管理一批机器，或者你的威胁模型里确实包含「物理接触」，那么**：**在 Secure Boot 和 ACPI 覆盖之间，你必须选一个。这是内核设计上的一个明确的、有意的取舍，而不是一个可以绕过的实现细节。**

### 一句话把这一节收掉

**Secure Boot 不拦你改 initrd，而是通过 lockdown 拦住「修改 ACPI 表」这个行为本身；做法是静默跳过，只留一行 `pr_notice`。**

**所以正确的顺序是：先 `cat /sys/kernel/security/lockdown` 看级别，再决定要不要动手。** **如果那里是 `[integrity]`，那么你在 initrd 上花的所有功夫都不会生效，而原因和你的表毫无关系。**

## 关键事实速查

| 项目 | 内容 |
|---|---|
| **仓库** | **`pfeifferj/archlinuxarm-proart-p16`**，MIT，386 个文件，**2026-10-19 创建** |
| ⭐ **覆盖的本质** | **不是改固件，是让内核在启动时用 initrd 里的表替换固件表**；**「在 RAM 中提前应用 ACPI 归档；不要刷固件。」** |
| **内核开关** | **`CONFIG_ACPI_TABLE_UPGRADE`**；内核去 initrd 里找 **`/kernel/firmware/acpi/`** |
| ⭐ **引入版本** | **v4.7 已有，但依赖写的是 `depends on BLK_DEV_INITRD && X86`（x86 专属）**；**v4.8 改成 `ARCH_HAS_ACPI_TABLE_UPGRADE`** |
| ⭐ **arm64 支持起点** | **v4.8（2016-10）**，commit **`38b04a74c587`「ACPI: ARM64: support for ACPI_TABLE_UPGRADE」**；抽象符号由 **`91dda51a1157`** 引入；机制改造由 **`5d8813271f8a`** 完成 |
| **v4.8 两架构都 select** | **`arch/x86/Kconfig` 和 `arch/arm64/Kconfig` 都写 `select ARCH_HAS_ACPI_TABLE_UPGRADE if ACPI`** |
| ⭐ **是否 arm 专用** | **不是。x86 与 arm64 共用同一套机制**：`acpi_table_upgrade()` 在 **`drivers/acpi/tables.c`**，路径常量 **`char cpio_path[32] = "kernel/firmware/acpi/"`** 与架构无关 |
| **内建 initrd 场景** | **`ACPI_TABLE_OVERRIDE_VIA_BUILTIN_INITRD`**；**`depends on INITRAMFS_SOURCE!="" && INITRAMFS_COMPRESSION_NONE`** |
| ⚠️ **我原来写错的一点** | **内核不按文件名匹配，而是读文件头 4 字节 `signature` 去 `table_sigs[]` 白名单里查** |
| **白名单规模** | **46 个签名**，含 **DSDT、SSDT、FADT、MADT、ECDT、SRAT、SLIT、DMAR、HPET、MCFG、IORT、PPTT、NHLT** 等 |
| ⭐ **四条硬性校验** | ① **文件至少有一个 ACPI 表头大**（`Table smaller than ACPI header`）；② **签名在白名单**（`Unknown signature`）；③ **文件大小必须等于表头声明的 `length`**（`File length does not match table length`）；④ **校验和正确**（`Bad table checksum`） |
| ⚠️ **第 3 条的陷阱** | **文件比 `length` 字段长会被直接拒绝**（比如带填充字节的 dump），错误信息只说「长度不匹配」；解法是用 `acpixtract` 提取或按 `length` 截断 |
| **明确不能覆盖的** | **`ACPI_SIG_RSDP`**（签名 6 字节）、**`ACPI_SIG_FACS`**（无普通 ACPI 表头） |
| **其他限制** | **一次最多 64 张表**（`NR_ACPI_INITRD_TABLES`）；**内核 lockdown 时直接忽略**，日志 `kernel is locked down, ignoring table override`（`LOCKDOWN_ACPI_TABLES`） |
| ⭐ **替换 vs 追加** | **表签名 + OEMID + OEM Table ID 三者相同且 `OEM Revision` 更大 → 替换（upgrade）**；**任一不同 → 追加（append）**。**忘了提高 OEM Revision 会导致你的表被忽略** |
| ⭐ **dump 路线 A** | **UEFI Shell + `acpiview -s DSDT -d` / `acpiview -s SSDT -d`**（Linux 起不来时用） |
| ⚠️ **acpiview 的坑** | **「acpiview 会写入一个已存在的 dump 文件而不截断它」** → 脚本先 `rm -q *.bin` |
| **dump 脚本的健壮性** | 检查 `%homefilesystem%` 映射、每步检查 `%lasterror%`、**最后检查 `DSDT0000.bin` 和 `SSDT0000.bin` 是否真的存在** |
| ⭐ **dump 路线 B** | 从 **`/sys/firmware/acpi/tables/DSDT /sys/firmware/acpi/tables/SSDT*`** 直接 `cat`；**前提是这次启动没加载覆盖 cpio** |
| **U 盘准备** | Shell 复制到 **`EFI/BOOT/BOOTAA64.EFI`**，脚本到 **`EFI/BOOT/startup.nsh`**；**「不分区、不格式化，也不碰 U 盘上的其他文件」**；校验 Shell 的 SHA-256 |
| ⭐ **固件绑定检查** | 代码里拒绝两种输入：**「你 dump 出来的是我们的覆盖表而不是固件原表」**、**「固件版本不是 H7607BA.300」** |
| ⭐ **改了什么（SSDT）** | **只改 6 个方法：`RRA9`、`RRA8`、`WRA9`、`WRA8`、`RWEC`、`GBST`**；**把 `Local0`/`Local5` 改成命名对象 `RSPB`**（局部变量 → 跨方法生命周期的命名缓冲区） |
| **具体 sed 改动** | `3590,3604s/Local0/RSPB/g`；`3590s/RSPB = Buffer/Name (RSPB, Buffer/`；`3590s/{}/{})/` |
| ⭐ **为什么不重编译整表** | **「编译整张表会重写无关的 AML」** → 做法是**只把 6 个编译后的方法拼接回原始 SSDT** |
| **拼接的严谨性** | ① 每个方法要求「恰好一个匹配」并校验哈希；② **外层 Scope/Device 的 package length 要同步改**；③ **变长编码的宽度变化会被拒绝**；④ 从后往前替换并检查重叠；⑤ 重算表长度和校验和，最后再用 `table()` 自检 |
| **SSPM 改法** | 把 **`_OSI("Windows 2022")`** 谓词替换为 **`\0` + `Noop`(0xa3)**；**「不使用全局 OSI 覆盖」** |
| ⭐ **为什么不用 `acpi_osi=`** | 全局 OSI 覆盖会让**所有**依赖 `_OSI` 的地方都走 Windows 分支；精确打掉只影响那一处 |
| **cpio 路径** | **`kernel/firmware/acpi/DSDT.aml`** 和 **`kernel/firmware/acpi/SSDT.aml`**（内核写死的前缀和文件名） |
| **手写 cpio** | 魔数 **`070701`**（new ASCII），13 个十六进制字段 + 名字 + 4 字节对齐 + 数据；以 **`TRAILER!!!`** 结束，整体补齐 **512 字节** |
| **为什么要手写** | 不依赖 `cpio` 命令，且**产出可复现**（作者给归档 pin 了 SHA-256 `311dc5b4...`） |
| ⭐ **那个 allocator 陷阱** | 替换 DSDT 在 **`0x2050a00000`、长度 `0x12144`**，**跨过 EFI 描述符边界 `0x2050a0d000`** → 早期映射接受，**后期 `acpi_os_ioremap()` 拒绝**，报 **`AE_NO_ACPI_TABLES`** |
| **后果** | **「USB、NVMe 和 GPU 枚举都无法进行」** |
| **根因** | **memblock 会合并相邻可用 EFI 描述符**，所以分配可能跨边界 |
| ⭐ **补丁思路** | 增加 **`arch_alloc_acpi_tables()`** 架构钩子（`__weak` 默认保留原行为）；ARM64 只在**单个 conventional + write-back + 非 runtime 的 EFI 描述符内**分配；**「没有合适的描述符就意味着明确的分配失败；不存在跨描述符的回退」** |
| **补丁细节** | 先解析 **`MEMBLOCK_ALLOC_ACCESSIBLE` 哨兵值**（`memblock_get_current_limit()`）；成功时 `pr_info` 打印地址/大小/区域，失败时 `pr_err` |
| **补丁基线** | **`NVIDIA/NV-Kernels 2234cd7f8f8a9fdbceef37f82c531016aab8cf73`** |
| ⚠️ **这个坑是否通用** | **任何在 ARM64 上用 `CONFIG_ACPI_TABLE_UPGRADE` 的系统都可能遇到**；是否触发取决于内存容量和 EFI 描述符的切分位置，**与覆盖表内容无关** |
| **可迁移 ①** | dump 的两条路线 + acpiview 不截断的坑 |
| **可迁移 ②** | `kernel/firmware/acpi/` 这个内核约定路径（先确认 `CONFIG_ACPI_TABLE_UPGRADE`） |
| **可迁移 ③** | **只改方法不重编译整表**的思路 |
| **可迁移 ④** | **精确打掉一处 `_OSI`** 而不是全局 `acpi_osi=` |
| **可迁移 ⑤** | 固件版本绑定 + 原始 dump 和产物的哈希 |
| ❌ **不可迁移 ①** | `RRA9`/`RRA8`/`WRA9`/`WRA8`/`RWEC`/`GBST` 是 **ASUS 这台机器的 EC 实现细节** |
| ❌ **不可迁移 ②** | 所有字节偏移（如 `0x10269`、`3590,3604`）只对**这个固件版本**有效 |
| ❌ **不可迁移 ③** | ARM64 allocator 补丁；x86_64 通常不会有这个坑 |
| ⭐ **最小可行路径** | dump → `iasl -d` 反汇编 → 只改一处 → **争取「等长替换」**（避免处理 package length 变长编码）→ 打 cpio → 重启后用 `dmesg \| grep "Table Upgrade"` 确认 |
| ⭐ **Secure Boot 是否拦截** | **不拦「改 initrd」，但会自动触发 lockdown；`LOCKDOWN_ACPI_TABLES` 属于 **integrity** 级** |
| ⭐ **决定性原文** | **`[LOCKDOWN_ACPI_TABLES] = "modifying ACPI tables"`**（`security/security.c` 的 `lockdown_reasons[]`，共 31 项） |
| **自动触发依据** | **man page：`On an EFI-enabled x86 or arm64 machine, lockdown will be automatically enabled if the system boots in EFI Secure Boot mode.`**；旧开关 **`CONFIG_LOCK_DOWN_IN_EFI_SECURE_BOOT`** |
| ⚠️ **实际表现** | **系统正常启动、表完全没应用、`dmesg` 只有一行 `kernel is locked down, ignoring table override`**（`pr_notice` 级，很不起眼） |
| **检查位置** | **在「已经找到表」之后才检查 lockdown**，然后 `return` |
| ⭐ **十秒确认** | **`cat /sys/kernel/security/lockdown`**（方括号是当前级别）；**`grep -E 'ACPI_TABLE_UPGRADE\|LOCKDOWN' /boot/config-$(uname -r)`**；**`mokutil --sb-state`** |
| **本机实测（对照）** | **`CONFIG_ACPI_TABLE_UPGRADE=y`、`FORCE_NONE=y`、`SECURITY_LOCKDOWN_LSM_EARLY` 未开**；**`/sys/kernel/security/lockdown` 显示 `[none]`** |
| **man page 里 integrity 级的 ACPI 三条** | **「ACPI 表的覆盖」「ACPI 错误注入的使用」「ACPI RDSP 地址的指定」「ACPI 自定义方法的使用」** |
| ⚠️ **替代方案一** | **`CONFIG_EFI_CUSTOM_SSDT_OVERLAYS` + `efivar_ssdt=`**：**同样检查 lockdown，所以也被挡住**；且**只能追加 SSDT，不能替换 DSDT** |
| **替代方案二** | **抢在 lockdown 生效前加载**：理论可行（`SECURITY_LOCKDOWN_LSM_EARLY` 的存在说明有时间窗），**但不推荐**，行为随版本变化且本质是绕过安全机制 |
| **替代方案三** | **关掉 Secure Boot**（作者的选择）；**在 Secure Boot 与 ACPI 覆盖之间必须选一个，这是有意的设计取舍** |
| ⚠️ **风险提示** | ACPI 表在设备枚举**之前**加载，错的表可以让系统看不到任何设备甚至无法启动；**务必保留一条不带该 cpio 的启动条目**；**RAM 里的表重启即失效，而刷固件不可逆** |

## 延伸阅读

- [为了让这台 128GB 的 RTX Spark 笔记本跑 Linux，她自己写了 ACPI 覆盖和触控板补丁](https://freelamp.com/articles/2026-10-19_rtx-spark-laptop-arch-linux-arm-nvidia/)
- [想下载一个 ISO，最后写了个内核漏洞利用程序：而他只需要往两个 sysfs 文件里写两个零](https://freelamp.com/articles/2026-10-19_tplink-eap770-dma-cache-bug-kernel-exploit/)
- [Linux 7.3 发布：一万八千个提交、三千名开发者，而两篇报道各说一半](https://freelamp.com/articles/2026-10-19_linux-7-3-release-record-commits-ai-churn/)
- [Libreboot 26.10 加入了 EDK2 支持，而它的反 AI 政策写进了一个机器可读的文件](https://freelamp.com/articles/2026-10-16_libreboot-2610-uefi-edk2-anti-ai-policy/)
- [作者仓库（一手，含全部脚本与哈希）](https://github.com/pfeifferj/archlinuxarm-proart-p16)
- [内核 ACPI 表覆盖补丁原文](https://github.com/pfeifferj/archlinuxarm-proart-p16/blob/main/01-platform/kernel/patches/provenance/hardware/backports/acpi/0001-arm64-bound-acpi-override-allocation.patch)
