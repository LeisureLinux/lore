---
title: "一个 CAB 文件、七个「合法」文件、和一条通往政府定制 Windows 的链：NetamLoader 拆解"
date: 2026-11-01
slug: netamloader-apt-windows-china-government-edition
tags: [NetamLoader, Kaspersky, APT, 网络间谍, 供应链攻击, Windows安全, AppDomainManager注入, XAML, 二进制反序列化, TypeConfuseDelegate, AMSI绕过, EDR绕过, dllhost, PatchMyPC, CAB, 中国政府版Windows, Windows10ChinaGovernmentEdition, 技术主权, 事件响应, IOC]
category: 安全/事件分析
author: FreeLAMP.com
original_source: "⭐ 一手核对：Kaspersky Securelist《Unknown APT uses NetamLoader to attack a Win10 OS customized for governments in Asia》（GReAT，2026-10-29）+ The Hacker News 报道（Ravie Lakshmanan，2026-11-01）+ 微软官方 Windows 10 China Government Edition 发布公告（2017-05-23）+ Google Cloud 关于 AppDomainManager 注入的技术说明"
original_date: 2026-11-01
original_url: "https://thehackernews.com/2026/11/netamloader-malware-targets-government.html"
description: "Kaspersky 披露了一个此前未记录的 .NET 程序集加载框架 NetamLoader：它不靠漏洞利用，而是把一个 CAB 文件放进 Windows 更新缓存目录，里面装着七个「看起来完全合法」的文件 —— 其中六个是第三方补丁工具 Patch My PC 的真实组件，连用来做注入的 .NET 程序集都是微软签名的。真正恶意的是两个 .config 与一个 .resx：AppDomainManager 注入让 .NET 在主函数运行前就加载攻击者指定的程序集，BinaryFormatter 反序列化触发 TypeConfuseDelegate，再逐层 XAML 解密推进。本文逐层拆解了这条链（含 AMSI 绕过、dllhost.exe 进程脱钩、C2 轮询节奏与反沙箱抖动）、完整的 IOC 清单、以及它真正值得注意的地方：Kaspersky 明确**未做归因**，且受害者只有一台 —— 目标不是「渗透」，而是「验证一条针对政府定制操作系统的攻击路径是否可行」。"
published: true
---

> ⭐ **本文核对的一手材料**：
> - **[Kaspersky Securelist：Unknown APT uses NetamLoader to attack a Win10 OS customized for governments in Asia](https://securelist.com/netamloader/121676/)**（**GReAT，2026-10-29**，含完整感染链图、配置项表、基础设施表与完整 IOC 清单）
> - **[The Hacker News：NetamLoader Malware Targets Government Windows 10 Systems in Asia via .NET Injection](https://thehackernews.com/2026/11/netamloader-malware-targets-government.html)**（Ravie Lakshmanan，2026-11-01）
> - **[微软官方：Announcing Windows 10 China Government Edition](https://blogs.windows.com/windowsexperience/2017/05/23/announcing-windows-10-china-government-edition-new-surface-pro/)**（2017-05-23，CETC/CMIT 合资公司开发的背景）
> - **[Google Cloud Threat Intelligence：Windows Session Hijacking via CCMEXEC（AppDomainManager 注入的技术说明）](https://cloud.google.com/blog/topics/threat-intelligence/windows-session-hijacking-via-ccmexec)**
> ⚠️ **本文为**解读**。所有技术细节均来自一手材料；**不提供可运行的 payload 或利用代码**。

## 一句话结论

**⭐ 而这条链最反直觉、也最值得记的地方，是它从头到尾「一个漏洞都没用」。**

**它靠的是：**

```
一个 CAB 文件 → 放进 Windows 更新缓存目录
  → 里面 7 个文件，6 个是第三方补丁工具 Patch My PC 的真组件
  → 唯一「不合法」的是两个 .config 和一个 .resx
  → 而它们做的事，是让 .NET 在程序主函数运行前就加载攻击者的程序集
```

**⭐ 而 Kaspersky 的结论更值得注意 —— 受害者只有一台，未做归因：**

> **「Based on KSN telemetry data, we identified **a single victim in Asia**.」**
>
> **「After analyzing the TTPs, code similarities, and infrastructure, **we were unable to link the attack to any known APT group**.」**

**⭐ 我认为这才是这件事真正的性质 —— 它更像一次「可行性验证」，而不是一次大规模入侵。**

## 一、事件轮廓

### 1.1 关键事实

| | |
|---|---|
| **恶意框架名** | ⭐ **NetamLoader**（此前未记录的 .NET 程序集加载框架，基于 XAML 标记构建） |
| **发现方** | ⭐ **Kaspersky（GReAT 团队）** |
| **发现时间** | ⭐ **2026 年上半年** —— KSN 为一个使用 AppDomainManager 注入的 .config 文件发出检测告警 |
| **公开** | **2026-10-29** |
| **受害者** | ⭐ **亚洲，仅一台**（KSN 遥测） |
| **目标** | ⭐ **「仅供政府实体使用」的定制 Windows 版本** —— 推断受害者为亚洲政府机构 |
| **归因** | ⭐ **无。未与任何已知 APT 组织关联** |
| **Kaspersky 检测名** | `HEUR:Trojan.MSIL.NetamLoader.gen`、`Trojan.MSIL.Zapchast.*`、`Trojan.Script.Agent.*` |

### 1.2 ⭐ 而「发现」这个过程本身就很有意思

**⭐ 因为 Kaspersky 第一次分析时，结论是「没发现恶意代码」：**

> **「Initial analysis of the CAB contents found **no malicious code**: most executables were legitimate components of the third-party patch management tool **Patch My PC**, and **even the .NET assemblies used for the injection were Microsoft-signed**.」**
>
> **「A **later re-examination** of the original .config file and the full loading process revealed the infection chain and framework described in this report.」**

**⭐ 我认为这一句是全文最有价值的技术情报之一 —— 它说明了这类攻击的一个根本特征：**

> **⭐⭐ **「文件本身是干净的」这件事，恰恰是这类攻击的**设计目标**，而不是它的缺陷。**

**—— 一个只看文件哈希和签名的扫描器，会得出「这是合法软件」的结论。**

**⭐ 而真正的恶意性藏在「**谁在什么时候加载了谁**」这个关系里 —— 也就是加载顺序。**

### 1.3 而交付方式，Kaspersky 也没说清楚

> **「We did not observe how the CAB file was delivered to the victim; we only saw the process `PatchMyPC-ScriptRunner.exe` running with the following arguments:」**
>
> `C:\Windows\SoftwareDistribution\Download\Install\PatchMyPC-ScriptRunner.exe -updatepackage -applicationid=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`

**⭐ 而这个命令行本身就很值得注意 —— 它完全像一次正常的补丁更新操作。**

**⭐ 而且 CAB 的落盘路径是：**

```
C:\Windows\SoftwareDistribution\Download\e4537a1762fcafd2fd96bfc825bad34f9db9a24\
```

**—— `SoftwareDistribution\Download` 就是 Windows 更新缓存目录。** **一个 CAB 放在这里，看起来就像一次「离线更新包」。**

## 二、⭐⭐ 第一阶段：三个「干净」文件的组合

**⭐ 而第一阶段的精妙之处在于：七个文件里，六个是真货。**

**⭐ Kaspersky 列出的 CAB 内容：**

| 文件 | 是什么 |
|---|---|
| `fabric.config` | ⚠️ **攻击者的** |
| `Microsoft.HostIntegration.Connectors.dll` | ⭐ **微软签名的真实程序集**（被用作注入载体）** |
| `PatchMyPC-Enum.dll` | ⭐ **Patch My PC 的真实组件** |
| `PatchMyPC-Models.dll` | ⭐ 同上 |
| `PatchMyPC-ScriptRunner.exe` | ⭐ 同上（**启动器**）** |
| `PatchMyPC-ScriptRunner.exe.config` | ⚠️ **攻击者的**（含 AppDomainManager 注入）** |
| `Resources.resx` | ⚠️ **攻击者的**（含反序列化载荷）** |

**⭐ 所以「恶意文件」只有 3 个，而另外 4 个 —— 包括那个启动器 exe —— 全是真的第三方软件。**

### 2.1 ⭐ 第一步：AppDomainManager 注入

**⭐ 这是整条链的入口，而它的原理值得讲清楚 —— 因为它利用的不是漏洞，而是 .NET 的**正常加载机制**。**

**Kaspersky 的描述：**

> **「With this mechanism, when `PatchMyPC-ScriptRunner.exe` runs, the accompanying configuration file `PatchMyPC-ScriptRunner.exe.config` **in the same directory is loaded before the executable's main function runs**.」**

**⭐ 而那个 .config 的内容（Kaspersky 原样给出）：**

```xml
<configuration>
  <runtime>
    <appDomainManagerType value="Microsoft.ApplicationServer.Caching.DataCacheFactoryConfiguration">
    </appDomainManagerType>
    <appDomainManagerAssembly value="Microsoft.HostIntegration.Connectors, Version=1.0.0.0, Culture=neutral, PublicKeyToken=31bf3856ad364e35">
    </appDomainManagerAssembly>
    <NGenAssemblyUsageLog enabled="0" />
  </runtime>
  <startup> <supportedRuntime version="v4.0" sku=".NETFramework,Version=v4.6" />
```

**⭐ 我来解释这三行各自在做什么：**

| 行 | 作用 |
|---|---|
| **`appDomainManagerType`** | ⭐ **指定 AppDomainManager 的实现类** —— 这里是 `DataCacheFactoryConfiguration`（AppFabric Cache 客户端的配置类）** |
| **`appDomainManagerAssembly`** | ⭐ **指定加载哪个程序集来实现它** —— `Microsoft.HostIntegration.Connectors`，**微软签名的正版程序集** |
| ⭐ **`NGenAssemblyUsageLog enabled="0"`** | ⭐ **关掉 NGEN 用法日志** —— **这是第一个「痕迹抑制」动作**，而且藏在最不起眼的位置 |

**⭐ 而这里的关键洞察是 ——**

**Google Cloud 的技术说明解释了 `DataCacheFactoryConfiguration` 这个类为什么特殊：**

**⭐ 它有一个「构造函数里会执行任意代码」的行为** —— 因为 `DataCacheFactoryConfiguration` 在被实例化时，其基类的构造函数会调用一个可被重写的虚方法。

**⭐ 而 `.config` 机制本身会**根据 `appDomainManagerAssembly` 加载指定的程序集** —— 于是攻击者不需要提供任何恶意 DLL，只要指定一个**「加载时构造函数会干活」的合法微软程序集**就够了。**

**⭐ 而 Microsoft.HostIntegration.Connectors.dll 正好有这样的类。**

### 2.2 ⭐⭐ 第二步：BinaryFormatter 反序列化 + TypeConfuseDelegate

**⭐ 这一步是真正的「武器」，而且用的是 .NET 里一个臭名昭著的反序列化原语。**

**Kaspersky 的描述：**

> **「Parsing this .resx file with `ResXResourceSet` causes the embedded Base64-encoded binary payload to invoke `BinaryFormatter.Deserialize()`, triggering a **deserialization vulnerability** that enables a **TypeConfuseDelegate attack**. The TypeConfuseDelegate then invokes `XamlReader.Parse()`, which loads a XAML payload (named XAML-1) embedded within the binary object.」**

**⭐ 我把这三步拆开 —— 它的巧妙在于「用一种类型混淆去骗过另一种类型的检查」：**

```
Resources.resx 里的 Base64 数据
    ↓ BinaryFormatter.Deserialize()
反序列化触发（这是 .NET 里最经典的一类 RCE 原语）
    ↓ TypeConfuseDelegate
把「委托」伪装成「另一个类型」→ 骗过 BinaryFormatter 的类型白名单
    ↓ 调用 XamlReader.Parse()
加载 XAML-1
```

**⭐ 而「加载 XAML」这一步是整个攻击链的关键设计选择 —— 因为 XAML 天然支持：**
- **内嵌 Base64 资源**
- **多层层叠**
- **最终能触发任意 .NET 代码**

**—— 也就是说：⭐ 攻击者用 XAML 作为一个「可编程的载荷封装格式」，把整个攻击链做成了多段式。**

### 2.3 ⭐ 第三步：用命令行哈希当 AES 密钥

**⭐ 而这一处是我认为整个报告里最漂亮的技术细节。**

**Kaspersky 的原文：**

> **「1. Retrieve the full command line of the current host process `PatchMyPC-ScriptRunner.exe`, converting all arguments to lowercase.**
> **2. Generate the AES key by hashing the command-line string with SHA-256.**
> **3. Decode the Base64 string embedded in XAML-1 into a binary array. Use the first 16 bytes of that array as the IV, then decrypt the remaining encrypted data with AES.」**

**⭐ 我解释一下这个设计的含义：**

**—— 密钥 = SHA-256(当前进程命令行的小写形式)。**

**⭐ 而载荷的解密密钥，就藏在「这个进程是怎么被启动的」里。**

**⭐ 我认为这个设计有三个好处：**

| | |
|---|---|
| **① 环境绑定** | ⭐ **在别的机器上、或者用不同的命令行启动，解密就会失败** —— 这是一种「**靶向特定部署**」的隐式约束** |
| **② 免密钥传递** | ⭐ **不需要把密钥存进任何文件 —— 密钥由运行时环境推导出来** |
| **③ 反分析** | ⭐ **分析师要复现解密，必须先知道原始命令行** |

**⭐ 而配合第五步的「解密失败就 `Environment.Exit(0)`」，效果是：**

> **「If any exception occurs during decryption, trigger `Environment.Exit(0)`, silently terminating the host process to prevent error messages that might reveal the attack.」**

**—— 失败就静默退出，不留错误信息。**

## 三、⭐⭐⭐ 第二阶段：AMSI 绕过与进程脱钩

**⭐ 而第二阶段是整个攻击链的技术高潮。**

### 3.1 ⭐⭐ XAML-2-1：用 AMSI 自己的内存改 AMSI

**⭐ 而 AMSI 绕过的手法非常「Windows」—— 我先说清原理：**

**AMSI（Antimalware Scan Interface）** 是 .NET 调用杀毒引擎的接口。**正常流程是：脚本/程序集要被加载 → AMSI 扫描 → 通过才执行。**

**⭐ 而攻击者的做法是（Kaspersky 原文）：**

> **「The sole purpose is to **hijack a key AMSI API** to bypass anti-malware scanning.」**
>
> **「Next, **patch the method by overwriting its first bytes in memory** with the binary payload (`41 C7 00 01 00 00 00 33 C0 C3`).」**
>
> **「Obtain the native pointer of the AMSI COM object with `Marshal.GetIUnknownForObject()`. From this pointer, read the address of its **virtual method table** and add `0x18` to reach another pointer that holds the address of the `CAmsiAntimalware::Scan` method.」**

**⭐ 我把这段拆成三步：**

```
① 拿到 AMSI COM 对象的原生指针（IUnknown）
        ↓
② 读它的虚方法表（vtable），+0x18 偏移拿到 Scan 方法的地址
        ↓
③ 把 Scan 方法的前 9 字节改掉（41 C7 00 01 00 00 00 33 C0 C3）
```

**⭐ 而那 9 个字节是 x86-64 机器码，我解释一下它的含义：**

| 字节 | 含义 |
|---|---|
| `41 C7 00 01 00 00 00` | **`mov dword ptr [r8], 1`（在 r8+0 处写入 1）** |
| `33 C0` | **`xor eax, eax`（返回值置 0）** |
| `C3` | **`ret`（返回）** |

**⭐ 而 0 在 AMSI 里是 `AMSI_RESULT_BLOCKED`（已阻止）—— 嗯，这里值得想一下。**

**⭐ 但真正巧妙的是 Kaspersky 提到的这个细节：**

> **「One patch targets the `Console.Clear()` API, **which resides in the memory space of an existing legitimate module**, while the other modifies **only the virtual tables of the AMSI module**, allowing the malware to **pass code integrity checks**.」**

**⭐ 我解释这句 —— 它是这个手法能通过完整性检查的原因：**

**—— 「补丁目标放在一个合法模块的内存空间里」+「只改 AMSI 模块的虚表（不改代码）」→  这样 Windows 的代码完整性检查（CI）看的是「代码段有没有变」，而**虚表在数据段**。**

**⭐ 换句话说：⭐ 这不是「改代码」，而是「改指针」—— 改动落在数据区，完整性检查看不见。**

### 3.2 ⭐⭐ 而 XAML-2-1 还有一个更隐蔽的技巧

**⭐ Kaspersky 的配图说明写着：**

> **「Sensitive strings in XAML-2-1 are **cut into tiny pieces**」**

**⭐ 我理解这个手法的目的：**

**—— 把敏感字符串（比如那个 AMSI 方法名、C2 地址、注册表路径）切成碎片再拼起来，是为了躲过「在内存里搜明文」的检测。**

**⭐ 这是一个很典型的对抗思路：⭐ EDR 常用的检测手段之一就是在进程内存里扫特定字符串，而把字符串切碎再运行时拼接，就让这种扫描失效。**

### 3.3 ⭐⭐⭐ 而 XAML-2-2 → XAML-3：换进程，才是真正的目的

**⭐ 而这一段是整条链里最重要的一次转折 —— 因为它不是为了「执行更多代码」，而是为了「**离开原来的进程**」。**

**⭐ 先看 XAML-2-2 的构成：**

| 组件 | 是什么 |
|---|---|
| **.NET 1 Loader** | ⭐ **一个 .NET 模块，负责解密、组装、加载 XAML-3** |
| **JSON-1** | ⭐ **C2 配置 + 下一阶段载荷** |

**⭐ 而 JSON-1 又分两块：**

| | |
|---|---|
| **JSON-1-c** | ⭐ **C2 上报配置**（上报地址、AES 密钥、用于验证 C2 证书的指纹）** |
| **JSON-1-p** | ⭐ **载荷配置**：`oib`（Base64 的 .NET 2 Plugin）、`oub`（调用 `Exit(0)` 的 XAML）、`ibk`（AES 密钥）、`ibi`（压缩加密的 XAML 模板集合）** |

**⭐ 而 .NET 1 Loader 干的事，Kaspersky 列得很清楚：**

> **「XAML-2-2 loads .NET 1 Loader, which then serves as a **decrypting, assembling, and loading** for XAML-3, **reports the status to the C2 server**, and **deletes malicious files extracted from the CAB archive**, along with **CLR usage logs and Windows system Prefetch cache files** to cover up the tracks.」**

**⭐ 而关键的一句在这里：**

> **「Once the exploit succeeds, **XAML-3 is loaded into the remote host process `dllhost.exe`**. **This is a covert method for initiating a new process that loads the malicious payload XAML-3. This technique effectively separates the infection chain from its initial process, allowing it to bypass behavioral monitoring by security solutions such as EDR.**」**

**⭐ 我想强调「**separates the infection chain from its initial process**」这句话 —— 这是整个攻击链的收尾目的。**

**⭐ 因为 `dllhost.exe` 是 Windows 的 COM 宿主进程** —— 一个**极其常见、系统自带、看起来完全无害**的进程。**

**—— 于是：**

```
初始进程：PatchMyPC-ScriptRunner.exe（第三方补丁工具）← 扫描器一看，合法
                ↓
     进程脱钩
                ↓
最终进程：dllhost.exe（Windows 系统 COM 宿主）← 扫描器一看，也合法
```

**⭐ 而在中间那几层（XAML-1、XAML-2、XAML-2-2、.NET 1 Loader）里，真正的恶意逻辑已经执行完了 —— 它们只是「运输工具」。**

**⭐ 我认为这一招的聪明之处在于：**

**—— 它不是「藏起来」，而是「**穿过去**」。** **EDR 的行为检测会看到「一个补丁工具启动 → 然后系统 COM 宿主出现了」，而这条因果链的中间部分被 XAML 层层解耦了。**

### 3.4 ⭐⭐⭐ 而 XAML-3 本身还有一次「模板化」

**⭐ 而 XAML-3 的构造方式，我觉得是这个框架设计得最漂亮的地方：**

**⭐ 它不是写死的文件，而是由「模板 + 配置」现场组装的：**

> **「XAML-3 is **generated from template XAML-3**. The template is decoded and decrypted using the value of the `ibi` item in JSON-1-p. In addition to template XAML-3, the final decryption includes two other XAML templates (template `__P1__` and template `__P2__`).」**
>
> **「The content of template `__P1__` is **identical to XAML-2-1 and bypasses AMSI in the new process**.」**
>
> **「Some of the item values in template `__P2__` come from the C2 configuration data in JSON-1-p. Within template `__P2__`, the placeholder `__P__` is replaced with a compressed, encoded payload – the .NET 2 Plugin.」**

**⭐ 我把这个「模板化」的意义说清楚：**

```
XAML-2-1 的内容  ──┐
                    ├──→ 模板 __P1__（= AMSI 绕过，再在新进程里做一遍）
配置 JSON-1-p ────┘

模板 __P2__  +  占位符 __P__（= .NET 2 Plugin）
                ↓
            XAML-P2  →  加载 .NET 2 Plugin
```

**⭐ 也就是说：⭐ 「AMSI 绕过」和「加载最终插件」这两件事，被做成了**可复用的模板**，在两个不同进程里各用一次。**

**⭐ 而这直接带来了一个能力：⭐ 同一个 C2 可以在每个受害者的机器上，用**不同的** XAML 模板 + 不同的配置项，生成结构一致但内容不同的最终载荷。**

**—— 也就是说，⭐ 这不只是「一次入侵的载荷」，而是「**一个能按目标裁剪载荷的框架**」。**

## 四、⭐⭐ .NET 2 Plugin：最终行为与那些反取证细节

**⭐ 而最终插件的行为，Kaspersky 逐条列了出来 —— 而我认为其中最有意思的是那些「**看起来像 bug 的行为**」。**

### 4.1 收集系统信息

> **「Gather system information from the registry:」**
> `HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\NET Framework Setup\NDP\v4\full` → `Version`
> `HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows NT\CurrentVersion` → `BuildLab`
>
> **「Combine the queried values into a single string, for example: `"4.7.03190\n17763.rs5_release.180914-1434"`. **If any query fails, replace its result with a hyphen**."」**

**⭐ 我注意到那个示例字符串：`17763.rs5_release.180914-1434`** —— **`17763` 是 Windows 10 1803 的 build 号** —— **这正是「政府定制版 Windows 10」那个年代的版本。**

**⭐ 而「查询失败就用连字符代替」这个细节很有意思 —— 它让指纹格式保持稳定，不因环境差异而变化。**

### 4.2 ⭐⭐ 反取证：删自己的日志

**⭐ 而反取证的部分，Kaspersky 描述得非常细致 —— 我认为这是全文最值得学的部分。**

**⭐ 而它有一个我认为很聪明的设计：**

> **「Reset a registry-based exception-state logging system by **deleting the nine GUID keys** under the path `LocalMachine\SOFTWARE\Classes\appid\[specific_GUID]` one at a time, along with all of their child subkeys. **The algorithm that generates the GUID path is unique — it derives the GUID from the C2 URL — so each C2 server has its own distinct set of bound GUIDs.**」**

**⭐ 我解释一下这个「异常状态日志系统」是什么 —— 很多人不知道这个 Windows 机制：**

**⭐ 当 .NET 应用抛异常时，CLR 会在注册表里创建一个以 GUID 为名的键，记录「这个应用崩过、崩在哪个版本」。**

**⭐ 这是 .NET 崩溃分析的官方机制。而这个恶意软件：**
1. **用它自己的 GUID 生成算法在注册表里建键**（用于后续反取证）
2. **每次用完就把这些键删掉**

**⭐ 而「GUID 由 C2 URL 派生」这一点尤其值得注意 —— 因为它意味着：**

**⭐⭐ **同一套代码，在不同 C2 上产生的 GUID 路径完全不同。** **这让「按 GUID 特征做检测」变得困难 —— 检测规则无法用一个固定路径，只能按算法特征或行为检测。**

### 4.3 ⭐⭐ 而 AMSI 绕过的「第二次」

**⭐ 而插件还做了一件我一开始没注意到的事 —— 就在第 5 步：**

> **「**Anti-analysis:** Check whether the current host process is `dllhost.exe` by examining `Environment.CommandLine`.」**

**⭐ 结合前面「模板 `__P1__` 与 XAML-2-1 完全相同、会在新进程里再做一次 AMSI 绕过」，可以看出这个设计：**

**—— 因为 malware 换到了 `dllhost.exe`，而 `dllhost.exe` 不在原来的进程上下文里，所以**必须重新绕一次 AMSI**。**

**⭐ 这是「模板复用」带来的必然要求 —— 而攻击者用模板机制，把这个要求变成了自动的。**

### 4.4 ⭐⭐⭐ 而沙箱规避的三个时间参数

**⭐ 而这三个时间参数，我觉得是这个框架里最「工程化」的部分：**

| 配置项 | 值 | 作用 |
|---|---|---|
| **`is`** | **1200–2400 秒（20–40 分钟）** | ⭐ **首次连接 C2 前的抖动延迟** —— 「**used for sandbox evasion**」 |
| **`bi`** | **79200–100800 秒（22–28 小时）** | ⭐ **C2 无响应时的轮询间隔** |
| **`wi`** | **100801 秒（约 28 小时）** | ⭐ **「实际初始等待」—— 恶意软件在首次执行后等约 28 小时就退出** |

**⭐ 而「首次执行后等 28 小时就退出」这一条，是我觉得最反直觉的一个设计：**

**⭐ 换句话说：⭐ 沙箱通常只跑几分钟到几十分钟。** **而这个恶意软件在沙箱里会「什么都不做」—— 它要么在等（20-40 分钟的首次延迟），要么根本不会触发（因为它等到 28 小时后才主动退出，而那之前它连 C2 都不连）。**

**⭐ Kaspersky 对 `wi` 的描述原文：**

> **「Actual initial wait: 100801 seconds (~28 hours). The malware waits approximately 28 hours after initial execution and then exits the process.」**

**⭐ 而它的 C2 轮询节奏是：**

> **「If a valid response is received from C2, the loop pauses for **5-6 minutes** before the next request; otherwise, it pauses for **22-28 hours**, checking every 10 minutes to determine whether the allotted time has elapsed.」**

**⭐ 我把这套节奏整理一下 —— 它是一个很清晰的「正常 vs 异常」分频设计：**

```
                     ┌─ 收到有效响应 → 5-6 分钟后轮询（正常节奏）
每 10 分钟检查一次 ────┤
                     └─ 无响应       → 22-28 小时（降频，藏起来）
```

**⭐ 而「22-28 小时」这个数字还有第二层含义 —— ⭐ 它和「28 小时后退出」基本一致。**

**—— 所以这台机器在感染后的前 28 小时里，几乎不产生任何网络流量。**

### 4.5 ⭐⭐⭐ 而网络加密：AES-128-CBC + HMAC

**⭐ 而最后一层是 C2 通信的加密：**

> **「All traffic between the malware and the C2 server is encrypted and authenticated using **AES-128-CBC with HMAC**. The encryption and authentication keys are derived from a master key – specified in the configuration as `"ec"="9fT04e03tAiZAPogcDWt0w=="` – by **applying HMAC with distinct seed values**.」**

**⭐ 我注意到了一个细节 —— ⭐ 这个 master key `9fT04e03tAiZAPogcDWt0w==` 就明文写在配置里，而配置是被加密传输的。**

**⭐ 而 Kaspersky 也提到了一个我没在 THN 摘要里看到的点 —— JSON-1-c 里有一项：**

> **「`tp` — Unknown item, **suspected to be a trusted SSL certificate**. `Thumbprint` was used to verify this alleged C2 certificate.」**

**⭐ 也就是说：⭐ C2 通信除了 AES 加密，还额外做了一层「证书指纹固定（pinning）」—— 只信任那个特定指纹的证书，即使 C2 域名被劫持或换到别的 IP 也无法冒充。**

## 五、⭐⭐⭐ 基础设施与 IOC

### 5.1 C2 基础设施

**⭐ Kaspersky 的基础设施表：**

| 域名 | IP | 首次发现 | 注册商 / ASN |
|---|---|---|---|
| **`openaigpt4v[.]com`** | **104.18.14[.]219** | **2023-09-27** | **Cloudflare, Inc. / AS15169** |

**⭐ 而它的定性原文：**

> **「The attack relies on **commercial hosting infrastructure**. The C2 IP is part of **Cloudflare's CDN**, and the domain name is registered with **Cloudflare**.」**

**⭐ 我认为这里有一个值得防守方注意的点 —— ⭐ 域名名 `openaigpt4v` 本身就是一个精心挑选的「诱饵名」：**

**—— 它看起来像一个 AI 服务/SDK 的域名（`openai` + `gpt4v`），而且用的是 `openai` 的一部分。**

**⭐ 而这个域名注册于 **2023-09-27** —— 比恶意软件被发现的 2026 年上半年早了**将近三年**。**

**⭐ 所以这是一个「长期准备」的域名（domain aging）。**

### 5.2 完整 IOC 清单（Kaspersky 官方）

**⭐ 为了方便核查，我把 Kaspersky 公布的全部 IOC 列出来 —— 这类清单是防守方最需要的。**

**⭐ 文件哈希（MD5）：**

| 组件 | MD5 |
|---|---|
| CAB 归档 | `F2458ED133F8D0CA19E22C10F577E98E` |
| `Resources.resx` | `E1DC6F1ED193594F2284BE22AE08DFA4` |
| **.NET 1 Loader** | `AB81564BCB8CA7E710C66832DE747556` |
| **.NET 2 Plugin** | `CFB8B281BDF5D9390E64B10C312FB2C1` |
| `fabric.config` | `67E3617F8709D34F806F8E02BADBA8A5` |
| `PatchMyPC-ScriptRunner.exe.config` | `514AC0D73B8A1B73488EF5E2E55A75C3` |
| XAML-1 | `514117D536E347560D049CFE0C609632` |
| XAML-2 | `9000820D8153C24CD60D53001D3A97B6` |
| XAML-2-1 | `B3C4A635179680EDAFB5D006CF0CFFC6` |
| XAML-2-2 | `4F28622C5E60C01319BF48CF742FE1A5` |
| XAML-3 | `C86D53392A87DD3F3E62D62C9B92A9BD` |

**⭐ 文件路径：**
```
C:\Windows\SoftwareDistribution\Download\Install\PatchMyPC-ScriptRunner.exe.config
C:\Windows\SoftwareDistribution\Download\Install\fabric.config
C:\Windows\SoftwareDistribution\Download\Install\Resources.resx
```

**⭐ 网络：**
```
openaigpt4v[.]com
104.18.14[.]219
```

**⭐ 而 Kaspersky 公布的检测名：**
```
HEUR:Trojan.MSIL.NetamLoader.gen
Trojan.MSIL.Zapchast.*
Trojan.Script.Agent.*
```

## 六、⭐⭐⭐ 「Windows 10 中国政府版」：这条背景值得补完

**⭐ 而 THN 提到了目标系统是「Windows 10 China Government Edition」，并推测受害者很可能在中国。**

**⭐ 微软 2017 年的官方公告把这个版本的来龙去脉讲得很清楚 —— 而这段背景对理解整件事很关键。**

**⭐ 关键事实：**

> **「In Shanghai, China we announced that with strong support of **CETC and Microsoft**, **CMIT**, our joint venture has now developed Windows 10 China Government Edition for **China government customers** … **Lenovo will be one of the first OEM partners to preinstall** Windows 10 China Government Edition.」**
>
> **「CMIT has developed a version of Windows 10 specifically for the **Chinese government and state-owned entities**.」**
>
> **「Three government customers are the first to pilot Windows 10 China Government Edition – at the national level with **China Customs**, at the regional level with the **City of Shanghai (EITC)**, and the state-owned enterprise with **Westone Information Technology**.」**
>
> **「The China Government Edition is based on Windows 10 Enterprise Edition … will use these manageability features to **remove features that are not needed by Chinese government employees like OneDrive, to manage all telemetry and updates, and to enable the government to use its own encryption algorithms** within its computer systems.」**

**⭐ 我把这几点提炼成一张表 —— 因为它们正好解释了「为什么这个目标是高价值」：**

| 特性 | 含义 |
|---|---|
| **基于 Windows 10 Enterprise Edition** | ⭐ **与普通 Win10 企业版同源 —— 但企业版没有的「政府定制特性」** |
| **移除 OneDrive** | ⭐ **数据不出境的设计** |
| **管理全部遥测与更新** | ⭐ **更新通道由政府控制** —— **而这正是「供应链攻击」的入口** |
| **政府自用加密算法** | ⭐ **⭐ 这条最关键 —— 意味着「用标准 Windows 镜像做检测」的假设全部失效** |
| **试点客户** | 中国海关（国家级）、上海市（EITC）、**Westone Information Technology（国有）** |
| **OEM 预装** | **联想是首批预装 OEM 合作伙伴** |

**⭐ 而 THN 引用的 Bloomberg 报道，补上了「另一面」：**

> **「Earlier this August, Bloomberg reported that China's Ministry of State Security had ordered some government agencies to **stop using the 'Government Edition' in favor of Chinese-made Linux distributions** as part of an effort to reduce its dependence on foreign technology.」**
>
> **「'Beijing's instruction stemmed from **data security concerns**,' Bloomberg said, citing 'people familiar with the matter.'」**

**⭐ 我把这条放进去，是因为它让整件事的形状变得完整了：**

**⭐⭐ **2026 年 8 月，中国国安部要求部分政府机构停用「政府版 Windows」改用国产 Linux —— 而 2026 年 10 月，Kaspersky 披露的正是针对「政府版 Windows」的、极其精密的定向攻击链。**

**—— 这两条信息放在一起，是一个**正在进行中的迁移过程**的攻防两面：一边在减少对 Windows 的依赖，另一边有人在验证「如果继续用 Windows，那它到底有多脆弱」。**

## 七、⭐⭐ 我的评价

### 7.1 ⭐⭐⭐ 而这个案例真正教给防守方的，是「关系」比「文件」重要

**⭐ 我认为这个案例最值得记的一条，不是任何一个技术细节，而是这个认知：**

> **⭐⭐ **「文件本身是干净的」—— 是这类攻击的设计目标，而不是它的缺陷。**

**⭐ 我把它翻译成一句防守方能直接用的判据：**

| 只看这些 | 结论 |
|---|---|
| **文件哈希** | ⭐ **「这是 Patch My PC 的合法组件」** |
| **数字签名** | ⭐ **「微软签名的，合法」** |
| **文件路径** | ⭐ **「Windows 更新缓存目录，正常」** |
| **进程名** | ⭐ **「第三方补丁工具，正常」** |
| ⭐ **最终进程** | ⭐ **「dllhost.exe，系统组件，正常」** |

**⭐ 五个「正常」叠在一起 —— 而这条链就在它们中间穿过。**

**⭐ 而这也解释了 Kaspersky 为什么第一次分析会说「没发现恶意代码」：⭐ 因为恶意性根本不在文件里，而在「**谁在什么时候加载了谁**」这个关系里。**

**⭐ 而这对防守的启示非常具体：**

**⭐ **不要只对文件做检测，要对「加载关系」做检测。** 而具体到可操作的层面：**

| 可观测点 | 该看什么 |
|---|---|
| **进程创建** | ⭐ **「一个补丁工具启动 → 几十秒后 `dllhost.exe` 出现」的因果关系** |
| **AppDomain 加载** | ⭐ **`.config` 里的 `appDomainManagerAssembly` 指向了哪个程序集** |
| **内存写入** | ⭐ **AMSI 虚表被改写、`Console.Clear` 所在模块被改** |
| **注册表** | ⭐ **`HKLM\SOFTWARE\Classes\appid\` 下突增 GUID 子键** |
| **持久化清理** | ⭐ **`.config` / `.resx` 文件在运行后消失、Prefetch 被清** |

### 7.2 ⭐⭐ 而「进程脱钩」这一招，可以复制到任何 EDR 绕过里

**⭐ 我想单独强调 XAML-3 换到 `dllhost.exe` 这一步，因为它是一个**可迁移的思路**，而不是某个特定技术的细节：**

**⭐ 它的结构是：**

```
【合法外壳】→ 【多层解耦的中间层】→ 【合法外壳】
```

**⭐ 而「中间层」的作用不是「隐藏」，而是「**切断因果链**」：**

**—— 行为检测看到的是「A 之后出现了 B」，而中间的解耦让 A 和 B 之间不存在可观测的直接关系。**

**⭐ 我认为这个思路可以用在很多场景：**
- **把初始入侵和最终载荷分开**
- **让「异常进程」看起来像「正常进程」**
- **让 EDR 的进程树分析失效**

**⭐ 而这也是为什么它用 `dllhost.exe` 而不是随便一个进程 —— ⭐ 因为 `dllhost.exe` 本身就是「被用来启动新进程加载载荷」的正当用途的 COM 宿主。**

### 7.3 ⭐⭐⭐ 而这个案例最让我想说的是「受害者只有一台」这件事

**⭐ 而我认为这件事被报道得有点轻描淡写了 —— 它其实是这个案例最关键的信息。**

**⭐ 我们来对比一下两个数字：**

| | 数字 |
|---|---|
| **攻击链的复杂度** | ⭐ **两阶段、十余个组件、AppDomainManager 注入 + 反序列化漏洞 + TypeConfuseDelegate + AMSI 绕过 + 进程脱钩 + 模板化载荷 + 多层加密** |
| **实际受害者** | ⭐ **一台** |

**⭐ 我认为这个悬殊的比例只有一种解释：**

> **⭐⭐ **这不是一次「广撒网捡漏」的批量入侵，而是一次**针对特定环境的定向可行性验证**。**

**⭐ 而几条旁证都指向这个方向：**

**① 「自定义 Windows 版本」这个目标本身 ——**

**⭐ 攻击者没有去选「一个popular的 Windows 版本」，而是明确针对「**政府专用的定制版**」。**

**⭐ 而这一点太重要了：⭐ 因为政府定制版是**全封闭的**（更新通道自管、遥测自管、自用加密算法），所以它**极难被通用漏洞扫描和遥测覆盖**。**

**—— 换句话说：⭐ 如果你要做「一次演练」，测试「我能不能攻进一个别人够不着的地方」，这就是最合理的选择。**

**② 域名注册于 2023-09-27 —— 提前近三年：**

**⭐ 这不是「临时起意」，而是**长期准备**。**

**③ 载荷是完全模板化 + 配置驱动的：**

**⭐ 前面分析过 —— 同一个框架，靠 JSON-1-p 的配置项裁剪出不同的最终载荷。**

**—— 而这正是「**要打很多个不同环境**」所需要的能力。**

**④ 「Windows 10 China Government Edition」这个具体目标：**

**⭐ 结合 2026 年 8 月国安部要求停用政府版 Windows 转向国产 Linux 的背景 ——**

**⭐⭐ 我认为最合理的解读是：**

> **⭐⭐ **有人在评估「政府版 Windows 的防守面到底有多厚」。**
> **⭐ **而结论如果是「很薄」，那么「改用国产 Linux」这个决策就多了一条技术依据 —— 甚至可能成为决策的**主要**依据。**

**⭐ 而这才是这件事真正值得长期关注的地方 —— ⭐ 比任何一个技术细节都值得。**

### 7.4 ⭐⭐ 而「未归因」这件事本身，也值得说两句

**⭐ Kaspersky 的措辞很谨慎：**

> **「After analyzing the TTPs, code similarities, and infrastructure, **we were unable to link the attack to any known APT group**.」**
>
> **「at present, **no attribution to any known APT group has been established**.」**

**⭐ 我认为这个克制是对的，而且我认为这个「未归因」比随便归因某个 APT 更有价值 —— 因为：**

| | |
|---|---|
| **如果归因了** | ⭐ **读者会当成「某国干的」，然后降低警惕** |
| **没归因** | ⭐ **读者保持「不知道是谁」的警觉** |

**⭐ 而结合我在第六节说的那个背景 —— ⭐ 在「技术主权」成为全球趋势的当下，「某个国家在测试别国政府定制操作系统的防守面」这个可能性本身，**不需要指名谁也同样成立**。**

**⭐ 而 Kaspersky 自己的结论段落（我觉得这是全文最好的收尾）：**

> **「Technological sovereignty has become a global trend. … a growing number of countries are building their own core software platforms, including operating systems, databases, middleware, and cloud services, **with operating systems often the top priority**.」**
>
> **「The advantage is that each country controls the development, operation, and upgrading of its own operating systems, granting it **full autonomy over the entire process**. On the other hand, it also means that **each country must protect this entire vast ecosystem on its own**. Bringing the operation and maintenance of such a system to maturity is a lengthy process. Until then, **both the system and its emerging supply chain could be exposed to attacks through multiple vectors**, increasing potential vulnerabilities.」**

**⭐ 我把这段的逻辑提炼成一句：**

> **⭐⭐ **「技术主权」把一个防守难题从「全球分工解决」变成了「各自单独扛」—— 而攻击面并没有变小。**

## Sources

- ⭐ 一手：[Kaspersky Securelist — Unknown APT uses NetamLoader to attack a Win10 OS customized for governments in Asia](https://securelist.com/netamloader/121676/)（GReAT，2026-10-29，含完整感染链、配置项表、基础设施表与完整 IOC 清单）
- ⭐ 一手：[The Hacker News — NetamLoader Malware Targets Government Windows 10 Systems in Asia via .NET Injection](https://thehackernews.com/2026/11/netamloader-malware-targets-government.html)（Ravie Lakshmanan，2026-11-01）
- ⭐ 一手：[微软官方 — Announcing Windows 10 China Government Edition and the new Surface Pro](https://blogs.windows.com/windowsexperience/2017/05/23/announcing-windows-10-china-government-edition-new-surface-pro/)（2017-05-23；CETC/CMIT 合资公司、试点客户、移除 OneDrive、自管遥测与更新、政府自用加密算法）
- ⭐ 一手：[Google Cloud Threat Intelligence — Windows Session Hijacking via CCMEXEC（AppDomainManager 注入技术说明）](https://cloud.google.com/blog/topics/threat-intelligence/windows-session-hijacking-via-ccmexec)
- 一手：Bloomberg 报道（2026 年 8 月，中国国安部要求部分政府机构停用 Government Edition 转向国产 Linux；经 THN 引用）
- 一手：Kaspersky OpenTIP 哈希查询链接（见上文 IOC 表）

---

（说明：所有引号内内容、配置项数值、哈希与 IOC 均来自上述一手材料；**第七节的「受害者只有一台 ⇒ 可行性验证」的解读、「进程脱钩是可迁移思路」的抽象、以及「技术主权把防守难题从全球分工变成各自单独扛」的判断为笔者观点**。）
