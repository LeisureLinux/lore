---
title: "GPL 许可证完整对照：GPL、Apache、MIT、BSD、MPL、EPL 的版本与差异"
date: 2026-11-11
slug: open-source-licenses-complete-guide
category: 技术/解读
author: FreeLAMP.com
original_source: "一手核对：SPDX License List 与弃用标识符（GPL-2.0-only / -or-later 拆分）＋ OSI 许可目录与 SPDX ID 采用说明 ＋ GNU 官方 GPLv2/v3 / LGPL / AGPL 文本与 FSF 兼容性列表 ＋ Apache 2.0 §3/§4/§5/§9、MPL 2.0 §3.3 与 Mozilla FAQ、EPL-2.0 FAQ 与 FSF 收录说明 ＋ choosealicense.com 的条件矩阵 ＋ Linux 内核 COPYING 的 v2-only 声明 ＋ Asahi Linux 2026-11-07 GPLv2+ 公告"
original_date: 2026-11-11
original_url: "https://spdx.org/licenses/"
description: "本文把主流开源许可证按「版本 → 条件 → 兼容性」完整梳理一遍，作为可查的参考稿。覆盖：GNU 家族（GPLv1/v2/v3、LGPL 2.0/2.1/3.0、AGPL 1.0/3.0、GFDL）、permissive 家族（MIT、ISC、BSD 4/3/2/1/0-Clause、Apache 1.0/1.1/2.0、Boost、Unlicense/CC0）、弱 copyleft（MPL 1.1/2.0、EPL 1.0/2.0、CDDL 1.0/1.1、EUPL、Artistic、zlib、SQLite 公有领域）、以及常被误称开源的 source-available 许可（BSL 1.1、SSPL、Elastic License 2.0、CC BY-NC、OpenSSL 旧许可、JSON、专有）。重点讲清五组最容易记错的差异：① GPLv2 与 v3 的专利授权、反 Tivoization（安装信息）、DRM、Apache-2.0 兼容、§7 附加条款、30 天治愈期；② **GPL-2.0-only 与 GPL-2.0-or-later 是两种不同许可**，SPDX 自 2019 起弃用含糊的 GPL-2.0 / GPL-2.0+，Linux 内核是 v2-only，Asahi Linux 2026-11 选的是 v2-or-later；③ MPL 2.0 的**文件级 copyleft** 与 §3.3「Larger Work」双向兼容机制，EPL-2.0 的 secondary license 选项；④ Apache-2.0 的专利授权与专利终止条款（这也是它与 GPLv2 不兼容、却与 GPLv3 单向兼容的原因）；⑤ BSD-4-Clause 的广告条款导致与 GPL 不兼容，以及 3→2→1→0-Clause 的简化序列。附兼容性矩阵、选型决策树、SPDX 写法速查，以及「许可证管不到什么」（LLM 洗代码、网络服务例外、商标、专利诉讼之外的行为）。"
published: true
---

> 参考：SPDX 许可清单、OSI 许可目录与 choosealicense.com 条件矩阵。本文依据各许可
>
> 本文依据各许可证官方文本、FSF / OSI / Mozilla / Eclipse 官方说明与 SPDX 规范整理。

## 〇、先建立一个坐标：所有开源许可证只回答三个问题

不管名字多复杂，任何一份开源许可证都在回答同一组问题：

| 问题 | 两端的答案 |
|---|---|
| **改了之后要不要公开源码？** | 要（copyleft） / 不要（permissive） |
| **公开的范围有多大？** | 整个衍生作品 / 仅修改过的文件 / 仅这个库 |
| **别人能不能闭源卖？** | 不能 / 能（只要保留声明） |

再加两个几乎家家都有的附加维度：**专利授权有没有明文**、**商标有没有限制**。

把许可证放进这个坐标，就不会被名字绕晕：

```
                      公开范围 ←——————————————————→ 不公开
强 copyleft   AGPLv3  GPLv3  GPLv2   LGPL   MPL/EPL   Apache-2.0  MIT  BSD  0BSD/Unlicense/CC0
              └──────── 整个作品 ────────┘ └─ 文件/库 ─┘ └────── permissive ──────┘
                    专利：GPLv3+ / Apache-2.0 / MPL2 / EPL2 有明文；GPLv2 / MIT / BSD 没有
```

**第一条要记住的**：**「开源」不等于「随便用」**，也不等于「不能卖钱」。OSI 的定义里，商业使用是被允许的；copyleft 约束的是「分发修改版时是否必须同许可开源」，不是「能不能收费」。

## 一、GNU 家族：版本最多，也最容易记错

### 1.1 GPL 的三个版本

| 版本 | 年份 | 关键变化 |
|---|---|---|
| **GPLv1** | 1989 | 初版，针对「只发二进制不给源码」；现已基本无项目使用（SPDX `GPL-1.0-only` / `-or-later`） |
| **GPLv2** | 1991 | 加入「自由或死亡」条款（若某国法律不允许自由分发则不能分发）；**Linux 内核、Git、MySQL（旧）** 用这一版 |
| **GPLv3** | 2007 | 针对 1991→2007 年间出现的规避手段打补丁，见下表 |

### 1.2 GPLv2 → GPLv3 的六处实质差异

| | **GPLv2** | **GPLv3** |
|---|---|---|
| 专利 | 无明文条款（隐含授权争议大） | **§11 明示专利授权**：贡献者授予实施其贡献所需专利；并禁止用专利协议制造歧视性交易 |
| **Tivoization** | 无规定 → 给源码但用硬件签名校验让你**跑不了自己编译的版本**，v2 下合规 | **§6 要求提供「安装信息」**（含签名密钥等），让用户能真正安装并运行修改版 |
| DRM / 反规避法 | 无规定 | 明确不许借 DMCA 类反规避条款限制 GPL 授予的权利 |
| 与 Apache-2.0 | **不兼容**（Apache 的专利终止条款被视作「额外限制」） | **单向兼容**（Apache-2.0 代码可并入 GPLv3 项目） |
| 附加条款 | 严格禁止 | §7 允许有限额外条款（署名、商标免责、责任限制等） |
| 违规治愈 | 终止即永久 | 首次违规有 **30 天治愈期**（§8） |
| 用语 | "distribute" | 改为 "convey"，定义更精确、更国际化 |

**v3 最主要的两大动因就是专利与 Tivoization**。TiVo 当年按 v2 规矩给了源码，但机顶盒只认厂商签名的内核 —— FSF 认为这违背了自由软件本意。**Linus 明确反对这一条**，认为硬件厂商有权控制自己的设备，因此 **Linux 内核至今是 GPL-2.0-only**，并在 `COPYING` 里专门说明「对内核而言唯一有效的版本就是这一个」。

### 1.3 「-only」与「-or-later」：这是两种许可，不是一个写法的两种记号

这是最常被忽略、也最影响实务的一点。许可文本通常有一句：

> 你可以按本许可第 N 版，或（由你选择）**任何更新版本** 的条款使用。

**有这句 = `-or-later`；没有 = `-only`。** 两者法律效果不同：

| 写法 | 含义 | 例子 |
|---|---|---|
| `GPL-2.0-only` | 只能用 v2，不能升 v3 | **Linux 内核**、Git |
| `GPL-2.0-or-later` | 接收者可选 v2 / v3 / 以后任何版本 | 大量 GNU 工具、**Asahi Linux 2026-11 的选择** |
| `GPL-3.0-or-later` | 起步就是 v3 | GCC 部分组件、许多新 GNU 项目 |

**这解释了 Asahi 那次改许可为什么写「version 2 or later」**：既与 GPLv2 内核生态对齐，又**保留了将来升到 v3 的权利** —— 而 v3 才有 Apache-2.0 兼容性。若写死 v2-only，将来想并入 Apache-2.0 代码会卡住。

**SPDX 在 2019 年前后把含糊的标识符全部弃用了**：`GPL-2.0`、`GPL-3.0`、`LGPL-2.1`、`AGPL-3.0`（不带后缀）以及 `GPL-2.0+` 这类写法都被标为 deprecated，替换为 `GPL-2.0-only` / `GPL-2.0-or-later` 等。**现在写 SPDX 必须带后缀**，否则工具会警告。

### 1.4 LGPL：让专有软件能「链接」自由库

| 版本 | 年份 | 说明 |
|---|---|---|
| **LGPL-2.0** | 1991 | 初版叫「Library GPL」 |
| **LGPL-2.1** | 1999 | 改名为「Lesser GPL」，澄清「衍生作品」边界；glibc 等大量 C 库用它 |
| **LGPL-3.0** | 2007 | 与 GPLv3 同步，加入专利/安装信息条款，实质是「GPLv3 + 链接例外」 |

**核心机制**：允许专有程序**动态链接** LGPL 库而不被传染；但你若修改了库本身，修改部分必须按 LGPL 开源，且要让用户能替换这个库（反「私有化锁定」）。**WINE 2002 年从 MIT 改的就是 LGPL** —— 对兼容层是刚需，否则没人能在上面跑闭源 Windows 程序。

**注意**：Asahi 报告特意说「**strong** copyleft licences only」，明确排除了 LGPL 这一档。这个用词是有分量的。

### 1.5 AGPL：补上「网络服务」那个洞

GPL 的触发点是**分发（convey）**。SaaS 时代，我改了 GPL 代码、只在自己服务器上跑、从不给用户二进制 —— 就永远不会触发「提供源码」。**AGPLv3 §13 专门补了这一条**：**若修改版通过网络被用户交互使用，必须向这些用户提供该修改版的完整源码**。

| 版本 | SPDX | 说明 |
|---|---|---|
| AGPL-1.0 | `AGPL-1.0-only` / `-or-later` | 2002，Affero 公司自用，几乎无项目 |
| **AGPL-3.0** | `AGPL-3.0-only` / `-or-later` | 2007，与 GPLv3 同步 + §13 网络条款；MongoDB（旧）、Grafana（部分）、Nextcloud 等 |

**AGPL 是最强的 copyleft**，也正因为如此，很多企业在合规清单里默认禁用。

### 1.6 GFDL 与其它 GNU 许可

- **GFDL 1.1 / 1.2 / 1.3**：GNU 自由文档许可，给手册/文档用；带「不变章节」「封面文本」等概念，与 GPL **互不兼容**（所以文档别直接塞进代码库当代码许可）。Debian 曾因 GFDL 的 invariant sections 判定其不满足 DFSG。
- **GNU Autoconf 例外 / GCC Runtime Library Exception / Classpath Exception / font exception**：这些是**许可例外**而非独立许可。比如 **GPL + Classpath Exception** 让 GCC 编译出来的程序不被 GPL 传染 —— Java 生态里很关键。

## 二、Permissive 家族：条件少，但差异也不小

### 2.1 MIT 与 ISC

| | MIT | ISC |
|---|---|---|
| 长度 | ~170 词 | 更短，去掉了「sublicense」等冗余措辞 |
| SPDX | `MIT` | `ISC` |
| 条件 | **保留版权声明 + 许可文本** | 同左 |
| 专利 | **无明文** | 无明文 |
| 商标 | 无规定 | 无规定 |

**MIT 的实质条件只有一条：保留版权与许可声明。** 这正是 Asahi 报告里那句「MIT 明确允许这样做，也没有针对恶意行为者的例外条款」的来历 —— 你拿走代码、闭源、卖钱都行，**只要别把声明删了**（所以「剥掉署名」本身已违反 MIT，只是取证难）。

**ISC 与 MIT 法律效果几乎等价**，OpenBSD 偏好它。另有 `MIT-0`（无归属版）、`X11`、`Expat` 等变体；`MIT` 在 SPDX 里指 Expat 版。

### 2.2 BSD 家族：一条广告条款毁了兼容性

| 版本 | SPDX | 条件 | 关键 |
|---|---|---|---|
| **BSD-4-Clause**（原始） | `BSD-4-Clause` | 保留声明 + **所有广告材料必须注明「本项目含加州大学代码」** | **与 GPL 不兼容**（广告条款属「额外限制」），FSF 建议别用 |
| **BSD-3-Clause** | `BSD-3-Clause` | 保留声明 + **不得用原作者名字为衍生品背书** | 1999 年删掉广告条款后与 GPL 兼容；FreeBSD 用 |
| **BSD-2-Clause** | `BSD-2-Clause` | 保留声明 + 免责 | 又称 Simplified/FreeBSD；NetBSD、OpenBSD 部分 |
| **BSD-1-Clause** | `BSD-1-Clause` | 只保留版权声明 | 少见 |
| **0BSD** | `0BSD` | **无条件** | 又称 Zero-Clause BSD / Free Public License；接近公有领域 |

**这条序列值得记**：`4 → 3 → 2 → 1 → 0` 就是不断删条件的历史。而 **4-Clause 的广告条款**在 1990 年代造成过著名的「BSD 广告堆」问题（一个产品里要罗列几十条大学署名），也直接导致它与 GPLv2 不兼容 —— 这是 OSI/FSF 都点名过的坑。

### 2.3 Apache 家族：1.0 → 1.1 → 2.0

| 版本 | SPDX | 状态 | 关键 |
|---|---|---|---|
| Apache-1.0 | `Apache-1.1` 前 | 已被取代 | 带广告条款，类似 BSD-4 |
| **Apache-1.1** | `Apache-1.1` | OSI 标为 **Superseded** | 仍有广告条款问题 |
| **Apache-2.0** | `Apache-2.0` | 现行 | 见下 |

**Apache-2.0 相对 MIT 多了三样东西**：

1. **§3 明示专利授权**：每个贡献者授予你实施其贡献所需的专利许可；
2. **专利终止条款**：你若起诉任何人「本作品侵犯专利」，你的专利授权即终止 —— 这是它当年**与 GPLv2 不兼容**的原因（被视作额外限制），却让它与 **GPLv3 单向兼容**；
3. **§4 要求标注修改**（NOTICE 文件、State changes），**§6 商标不授权**（不能拿 Apache 项目名做宣传）。

**所以 Apache-2.0 是「有专利条款的 permissive」**：仍然允许闭源分发修改版，但比 MIT 更规范、更适合公司间协作。几乎所有 ASF 项目、Android、Kubernetes、Rust、LLVM（部分）都在用它。

### 2.4 极简与公有领域

| 许可 | SPDX | 说明 |
|---|---|---|
| Boost-1.0 | `BSL-1.0` | 只对**源码分发**要求保留声明；二进制分发无条件 —— 比 MIT 还松 |
| Unlicense | `Unlicense` | 无条件献入公有领域 |
| CC0-1.0 | `CC0-1.0` | 公有领域奉献（含兜底许可） |
| WTFPL | `WTFPL` | 玩笑式无条件许可，部分合规工具不接受 |
| 0BSD | `0BSD` | 无条件 BSD |

**注意**：`Unlicense`、`CC0` 在部分大陆法系国家「放弃著作权」本身效力存疑，CC0 因此带了兜底授权条款。**WTFPL / JSON License（"The Software shall be used for Good, not Evil"）** 因措辞含糊，通常被企业合规工具判为不可用；后者还因「Good/Evil」无定义被 OSI 拒过。

## 三、弱 / 文件级 copyleft：Mozilla、Eclipse、CDDL

### 3.1 MPL 2.0：按**文件**画 copyleft 边界

| 版本 | SPDX | 说明 |
|---|---|---|
| MPL-1.1 | `MPL-1.1` | 1998（Netscape 时代），**与 GPL 不兼容**，FSF 曾建议别用 |
| **MPL-2.0** | `MPL-2.0` | 2012，受 GPLv3 起草过程启发重写，**GPL 兼容**；Firefox、Thunderbird、Rust（早期）、Terraform（旧） |

Mozilla 官方 FAQ 把三者边界讲得最清楚：

> **MPL**：copyleft 作用于**任何含 MPL 代码的文件**；
> **LGPL**：作用于**基于该库的任何库**；
> **GPL**：作用于**基于该代码的整个软件**。

**§3.3「Larger Work」机制**：你可以把 MPL 文件与 GPL / LGPL / 专有文件组合成一个更大的作品，**新增文件可用其它许可（含专有）**，但 MPL 覆盖的那些文件仍须保持 MPL 并开源。Mozilla 还发布过专门的《MPL-in-GPL Developer Guidelines》说明组合时的标注方式。**MPL 也含明示专利授权与商标限制**（choosealicense 表里 MPL 的 Limitations 明确列了 ✕ Trademark use）。

### 3.2 EPL：Eclipse 的「次级许可」设计

| 版本 | SPDX | 说明 |
|---|---|---|
| **EPL-1.0** | `EPL-1.0` | 2004，弱 copyleft；**与 GPL 不兼容**；Eclipse IDE、Jetty（旧） |
| **EPL-2.0** | `EPL-2.0` | 2017，FSF 收录；**允许初始贡献者声明 GPL-2.0-or-later 作为「secondary license」** |

FSF 对 EPL-2.0 的评语很精确：**「就 GPL 兼容性而言，2.0 与 1.0 基本等价，唯一变化是明确提供了把 GPLv2+ 指定为某段代码 secondary license 的选项」** —— 也就是说，**默认仍不兼容，除非项目主动声明**。此外 EPL-2.0 把「商业分发者须为贡献者免责」等条款现代化，并允许选择更宽松的次级许可（如 `EPL-2.0 OR GPL-2.0-or-later`）。

### 3.3 CDDL 与 Sun/Oracle 系

| 许可 | SPDX | 说明 |
|---|---|---|
| **CDDL-1.0** | `CDDL-1.0` | 2004，Sun 为 OpenSolaris 设计，**文件级 copyleft**、含专利条款、**与 GPLv2 不兼容**（这也是 ZFS 无法直接进 Linux 内核的著名原因） |
| **CDDL-1.1** | `CDDL-1.1` | 2010，Oracle 小幅更新（治理/管辖），兼容性未变 |

**ZFS on Linux 的困境**是这类「许可不兼容」最出名的现实案例：CDDL 与 GPLv2 双方都是 copyleft，但条款冲突（专利终止 / 附加限制 / 分发义务不同），导致代码无法合法合并进内核，只能以独立模块分发。**Oracle 也从未把 CDDL 换成 GPL。**

### 3.4 其它值得记的

| 许可 | SPDX | 类型 | 备注 |
|---|---|---|---|
| **EUPL-1.2** | `EUPL-1.2` | 弱 copyleft | 欧盟官方，与 GPLv3/AGPLv3/MPL/EPL 等有**官方兼容性附录**，多语言等效文本 |
| **Artistic-2.0** | `Artistic-2.0` | 弱 | Perl 双许可（Artistic 或 GPL）的一方；1.0 已被标 Superseded |
| **zlib** | `Zlib` | permissive | 要求标注修改、不得冒充原版；zlib/libpng 生态 |
| **PostgreSQL** | `PostgreSQL` | permissive | 类似 MIT + 不得用校名背书 |
| **Python-2.0** | `Python-2.0` | permissive | CNRI 时代遗留，现 Python 主要用 PSF 许可 |
| **SQLite** | 公有领域奉献 | 无条件 | 用 blessing 代替许可文本 |
| **CC BY / BY-SA / BY-NC** | `CC-BY-4.0` 等 | **非软件许可** | CC 官方明确建议不要用于软件；`BY-NC` 因禁商业使用**不符合 OSI 开源定义** |

## 四、Source-available ≠ 开源：这一栏最容易被误用

下面这些**不在 OSI 批准清单里**，或虽公开源码但不满足开源定义（不得限制商业使用、不得限制领域、不得歧视用途）：

| 许可 | 限制 | 为什么不算开源 |
|---|---|---|
| **BSL 1.1**（Business Source License，MariaDB / CockroachDB / Sentry 用过） | 禁止作为「竞争性服务」提供；N 年后自动转 Apache-2.0 / GPL | 有用途限制 + 延迟开源 |
| **SSPL**（MongoDB 2018 起） | 若把软件作为服务提供，必须开源**整套服务栈** | 对「其它软件」施加义务，超出开源定义 |
| **Elastic License 2.0** | 禁止提供第三方托管、禁止绕过许可密钥 | 用途限制 |
| **CC BY-NC / BY-ND** | 禁商业 / 禁演绎 | 直接违反 OSD 第 1、2 条 |
| **OpenSSL 旧许可**（≤1.1.1 前的双许可） | 广告条款 + GPL 例外 | 与 GPL 冲突；OpenSSL 3.0 已改 **Apache-2.0** |
| **APSL 2.0** | 要求改动回传、可单方终止 | OSI 标为 Non-Reusable |
| **JSON License** | 「用于善不用于恶」 | 用途歧视 + 措辞含糊 |

**判断口诀**：只要出现「不得用于 X」「不得提供 Y 服务」「N 年后才开源」「必须把整套栈也开源」，基本就不是 OSI 意义上的开源。

## 五、兼容性矩阵（实务最该查的表）

**「兼容」是单向的**：A 的代码能并入 B 的作品 ⇒ A 兼容 B，反之未必。

| 从 ↓ 并入 → | GPLv2-only | GPLv2+ | GPLv3+ | LGPL-2.1+ | AGPLv3 | MPL-2.0 | Apache-2.0 | MIT | 专有 |
|---|---|---|---|---|---|---|---|---|---|
| MIT | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| BSD-3/2/1/0 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **BSD-4-Clause** | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ |
| **Apache-2.0** | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **MPL-2.0** | ⚠️ §3.3 | ⚠️ §3.3 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅（仅文件级） |
| **EPL-1.0 / 2.0 默认** | ❌ | ❌ | ❌ | ❌ | ❌ | ⚠️ | ✅ | ✅ | ✅（文件级） |
| **EPL-2.0 声明 secondary** | — | ✅ | ✅ | — | — | — | — | — | — |
| **CDDL-1.0/1.1** | ❌ | ❌ | ❌ | ❌ | ❌ | ⚠️ | ✅ | ✅ | ✅（文件级） |
| LGPL-2.1+ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| GPLv2-only | ✅ | ⚠️¹ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| GPLv2+ | ✅² | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| GPLv3+ | ❌ | ❌ | ✅ | ✅ | ✅³ | ❌ | ❌ | ❌ | ❌ |
| AGPLv3 | ❌ | ❌ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |

¹ `GPL-2.0-only` 代码不能单方面升到 v3；与 `GPL-2.0-or-later` 混合时整体按 **v2-only** 执行。² 并入 v2-only 作品时按 v2 条款。³ GPLv3 与 AGPLv3 有专门的 §13 组合条款，组合作品整体受 AGPL 网络条款约束。

**三条最常见的踩坑**：

1. **把 Apache-2.0 代码放进 GPLv2-only 项目** —— 不兼容。LLVM/安卓生态与内核生态之间的老问题。
2. **把 CDDL 的 ZFS 合进内核** —— 不兼容，只能外挂模块。
3. **以为 EPL-2.0 天然兼容 GPL** —— 默认不兼容，要看项目有没有声明 secondary license。

## 六、SPDX 写法速查（现在必须带后缀）

```
GPL-2.0-only          GPL-2.0-or-later
GPL-3.0-only          GPL-3.0-or-later
LGPL-2.1-only         LGPL-2.1-or-later
AGPL-3.0-only         AGPL-3.0-or-later
GFDL-1.3-only         GFDL-1.3-or-later
Apache-2.0   MIT   BSD-3-Clause   MPL-2.0   EPL-2.0   CDDL-1.0
```

**已弃用（不要再用）**：`GPL-2.0`、`GPL-2.0+`、`GPL-3.0`、`LGPL-2.1`、`AGPL-3.0` 等不带后缀的写法。

组合表达式：

```
MIT OR Apache-2.0                          # 双许可，接收者二选一
GPL-2.0-or-later WITH Classpath-exception-2.0
Apache-2.0 AND MIT                         # 同一作品含两处不同许可代码
```

Linux 内核自 4.x 起在每个源文件头用 `// SPDX-License-Identifier: GPL-2.0` 标注（内核自己的 `LICENSES/` 里保留了它并配有说明；SPDX 通用清单里已弃用该裸标识符，内核用的是自己的 `LICENSES/` 目录约定）。

## 七、选型决策树：拿到一段代码先问这五个问题

```
① 我要把它并进现有项目，那个项目是什么许可？
   ├─ GPLv2-only  → 只能进 MIT/BSD-3/2/1/0、GPLv2-only、GPLv2+（按 v2）
   │                ✗ Apache-2.0、✗ MPL-2.0（除非 §3.3）、✗ CDDL、✗ EPL 默认
   ├─ GPLv3+     → 上面全部 + Apache-2.0 + MPL-2.0 + AGPLv3（§13 组合）
   └─ 专有/闭源  → 只能进 permissive（MIT/BSD/Apache/Boost/0BSD）
                    ✗ 任何 copyleft（LGPL 只能动态链接）

② 我要不要允许别人闭源卖我修改后的版本？
   ├─ 允许 → permissive
   └─ 不允许 → copyleft

③ 不允许的话，边界画在哪？
   ├─ 整个衍生作品 → GPL / AGPL
   ├─ 这个库（允许动态链接）→ LGPL
   └─ 只有我改过的那些文件 → MPL / EPL / CDDL

④ 用户会不会只通过网络使用、拿不到二进制？
   ├─ 会 → 需要 AGPL（GPL/MPL/EPL 都管不到 SaaS）
   └─ 不会 → 不必

⑤ 我的代码会不会被塞进硬件、而硬件签名校验挡住用户自己编译的版本？
   ├─ 会且我在意 → GPLv3 的「安装信息」条款有用
   └─ 不在意 → v2 / v2+ 都行
```

**再加一条现实建议**：**新项目优先写 `X-or-later`**（`GPL-3.0-or-later` 最省事）。写死 `-only` 会把项目锁在某个版本上；Asahi 这次选 `GPL-2.0-or-later` 就是留了升级通道。唯一例外是你要与 Linux 内核代码直接混合 —— 那就只能是 `GPL-2.0-only`（内核没有 or-later 选项）。

## 八、许可证管不到什么（这几条最容易被误解）

**① 管不到「读进去再改写」。** 这是 2026 年最现实的一条。MIT 明确允许拿走代码、闭源、卖钱，只要保留声明；GPL 约束的是**分发**这个动作，**管不到有人把公开代码读进去、用 LLM 改写、换个来源声明**。Asahi 官方报告里那句「MIT 明确允许这样做，也没有针对恶意行为者的例外条款」说的正是这个。GPL 改变的是**商业化的法律成本**（MIT 下可闭源卖，GPL 下分发修改版必须同许可开源、源码公开就更容易被发现抄袭），不是技术防线。

**② 管不到商标。** Apache-2.0 §6、MPL-2.0 都明确不授予商标权；GPL 也不管。项目名、logo 要走单独的商标政策 —— 这也是 Debian 把 Mozilla 的 Firefox 改名 Iceweasel 的旧事由来。

**③ 管不到专利诉讼之外的事。** GPLv3 §11 / Apache-2.0 §3 给的是**明示专利授权**，但它们不提供专利侵权担保，也不覆盖第三方专利。

**④ 不保证「没有漏洞」、不提供担保。** 几乎所有许可都带免责（Limitation of Liability / Warranty）。

**⑤ 不自动解决贡献者版权归属。** GPL 的 relicense 需要版权持有人（或全部贡献者授权 / CLA）。这正是 Asahi 那次改动被 OpenBSD 的 Bryan Steele 质疑「看似未经所有既往贡献者同意」的原因 —— **改许可证本身不是许可证能解决的问题**。

**⑥ 不覆盖「网络服务」这个动作**（AGPL 除外）。这是 1991 年 GPLv2 起草时想不到的场景，也是 AGPL 存在的全部理由。

## 九、一份速查：常见项目的实际许可

| 项目 | 许可 | 值得注意 |
|---|---|---|
| Linux 内核 | **GPL-2.0-only**（含 syscall 例外） | 明确拒绝 v3 |
| Git | GPL-2.0-only | |
| GCC / glibc | GPL-3.0-or-later / **LGPL-2.1-or-later** | glibc 用 LGPL 让专有程序能链接 |
| WINE | **LGPL-2.1-or-later**（2002 从 MIT 改） | 兼容层必须允许闭源 Windows 程序 |
| Firefox | **MPL-2.0** | 文件级 copyleft，允许专有扩展 |
| Chromium | **BSD-3-Clause** 为主 + 第三方多许可 | Chrome 品牌构建才含专有 codec |
| Apache 系 / Kubernetes / Rust / LLVM | **Apache-2.0** | 专利授权 + 商标限制 |
| Node.js / jQuery / React（旧） | MIT | |
| FreeBSD / NetBSD | BSD-3-Clause / BSD-2-Clause | 4-Clause 已弃用 |
| ZFS / illumos | **CDDL-1.0** | 与 GPLv2 不兼容，进不了内核 |
| Eclipse IDE | **EPL-2.0** | 默认不兼容 GPL，可声明 secondary |
| MongoDB（4.0 后）/ Elasticsearch（7.11 后） | **SSPL / Elastic License 2.0** | **不是 OSI 开源** |
| Terraform（1.6 后）/ Redis（7.4 后） | **BSL 1.1 / RSAL+SSPL** | source-available，非开源 |
| OpenSSL 3.0 | **Apache-2.0** | 旧版双许可已被取代 |
| SQLite | 公有领域奉献 | 无许可文本，用 blessing |
| Asahi Linux（2026-11 起） | **GPL-2.0-or-later** | 从 MIT 转，明确「只用强 copyleft」 |
| Omarchy | **MIT** | DHH 强调「最宽松的许可」 |

## 十、结论：三条能带走的规则

**① 先看「-only / -or-later」，再看版本号。** 这两者法律效果不同；SPDX 已弃用裸标识符，写的时候必须带后缀。

**② 兼容性是单向的。** permissive → copyleft 通常可以，反之不行；Apache-2.0 → GPLv2 不行、→ GPLv3 可以；CDDL / EPL 默认与 GPL 不兼容。

**③ 别把许可当护城河。** 它约束的是「分发修改版时要不要同许可开源」，不是「别人能不能复制你」。当复刻成本趋近于零（本号同期那篇《SaaS 软件 IP 大减值》讨论的正是这个），许可既挡不住 LLM 洗代码，也保不住估值；**能被重新定价的，是那些快不起来的东西 —— 分发、客户、信任、以及判断力**。

---

## Sources

- SPDX License List 与弃用标识符: <https://spdx.org/licenses/>
- OSI 许可目录（含 SPDX ID 与 Superseded / Non-Reusable 标注）: <https://opensource.org/licenses> ｜ <https://opensource.org/blog/osi-adopts-spdx-ids-for-license-urls>
- GNU 官方许可文本与 FSF 兼容性说明: <https://www.gnu.org/licenses/> ｜ <https://www.gnu.org/licenses/license-list.html>
- Linux 内核 `COPYING` / `LICENSES/` 的 GPL-2.0-only 声明: <https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/plain/COPYING>
- Apache-2.0 全文: <https://www.apache.org/licenses/LICENSE-2.0>
- Mozilla MPL-2.0 FAQ 与《MPL-in-GPL Developer Guidelines》: <https://www.mozilla.org/en-US/MPL/2.0/FAQ/> ｜ <https://www.mozilla.org/en-US/MPL/2.0/combining-mpl-and-gpl/>
- Eclipse EPL-2.0 FAQ 与 FSF 收录说明: <https://www.eclipse.org/legal/epl-2.0/faq/> ｜ <https://www.fsf.org/blogs/licensing/eclipse-public-license-version-2-0-added-to-license-list-1>
- Chromium 官方 Audio/Video 支持页: <https://www.chromium.org/audio-video/>
- choosealicense.com 条件矩阵: <https://choosealicense.com/licenses/>
- Asahi Linux《Progress Report: Linux 7.3》（2026-11-07，MIT→GPLv2+ 与 WINE 2002 类比）: <https://asahilinux.org/2026/11/progress-report-7-3/>
- 本号《Asahi Linux 改 GPL》与《SaaS 软件 IP 大减值》: <https://freelamp.com/articles/2026-11-10_asahi-linux-gpl-license-omarchy-dhh/> ｜ <https://freelamp.com/articles/2026-11-11_great-software-ip-writedown/>

### 事实边界说明

- 各许可条款（GPLv3 §6/§7/§8/§11/§13、AGPL §13、Apache-2.0 §3/§4/§6、MPL §3.3、EPL secondary license）：依据官方许可文本与 FSF / Mozilla / Eclipse 官方说明，本文未逐字抄录条款。
- SPDX 弃用裸标识符、`-only` / `-or-later` 拆分：依据 SPDX License List 与 2019 年前后的工具链变更；Linux 内核使用自己的 `LICENSES/` 目录约定，本文已单独注明。
- 兼容性矩阵是**实务简表**，不是法律意见；具体组合需按实际代码结构、链接方式、分发形态与司法辖区判断，建议由法务复核。
- 「source-available 不算开源」一节：依据 OSI 开源定义（OSD）与 OSI 许可目录；BSL / SSPL / Elastic License 2.0 均不在 OSI 批准清单。
- 常见项目许可表为公开信息汇总，个别项目存在**双许可 / 版本迁移 / 部分组件不同许可**（如 Chromium 第三方代码、Terraform 与 Redis 的改许可时间点），本文按主体许可标注，使用前请以项目仓库 `LICENSE` 文件为准。
- 第十节第③条与《SaaS 软件 IP 大减值》的串联是本文的解读，非任何许可证文本观点。
