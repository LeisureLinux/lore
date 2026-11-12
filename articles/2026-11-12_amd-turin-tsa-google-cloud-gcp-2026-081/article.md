---
title: "AMD Turin 三个 TSA 侧信道：为何必须停机再启动"
date: 2026-11-12
slug: amd-turin-tsa-google-cloud-gcp-2026-081
category: 技术/解读
author: FreeLAMP.com
original_source: "一手核对：The Hacker News《Google Cloud Warns Three AMD Turin CPU Flaws Could Leak Data Across Processes in VMs》（Swati Khandelwal，2026-11-12；C4D/N4D/H4D/Z4D/G4、Medium、stop-and-start、Debian 状态、Xen 更正说法）＋ Google Cloud Security Bulletin GCP-2026-081（2026-11-10 发布，Medium；三 CVE 描述、受影响机型、Google 已缓解 VM 间与 VM-宿主机间、11-10 起更新 VM 报告的 CPU 信息、VM/bare metal/嵌套虚拟化/GKE/Cloud Run 各项动作、Rebooting the guest OS isn't enough、GKE 镜像尚未列出、Cloud Run 无需动作）＋ AMD-SB-7073《AMD Transient Scheduler Attacks for Zen 5 Processors》（2025-07-08 的 AMD-SN-7029 后续；Zen 5「impacted differently」、CVE-2024-36350/36357 各 5.6 CVSS 3.1 AV:L/AC:H/PR:L/UI:N/S:C/C:H/I:N/A:N；EPYC 8005/9005 需 TurinPI_1.0.0.B 2026-07-10 + OS 更新，9005 另有 SEV FW 1.3A.05 与 TCB [SNP]=0x6）＋ AMD-SB-3055《Transient Execution Vulnerability》（2026-11-10 初始版；CVE-2026-0004 5.7 CVSS 4.0，L1D 缓存推断，EPYC 8005/9005 微码 C1:0x0B002175-Dense / B0:0x0B101066 + Linux/Windows/VMware OS 更新）＋ AMD-SB-7029 原始 TSA 公告（2025-07-08；TSA-SQ / TSA-L1 / CVE-2024-36348 / 36349 评分与 Milan/Genoa 固件表）＋ AMD《Technical Guidance for Mitigating Transient Scheduler Attacks》Rev 2.0（2025-07-16；TSA-L1 微标签误命中、TSA-SQ 存储队列假完成、仅 Family 19h 已知受影响、VERW 内存形式由 CPL0 在特权切换与 idle 前执行、WBINVD/FLUSH_CMD 无效、TSA_SQ_NO/TSA_L1_NO/VERW_CLEAR 三个 CPUID 位、SEV-SNP 需 attestation、缓解可能影响性能）＋ Xen XSA-525《x86: Transient Scheduler Attacks (update)》（2026-11-10 18:00 UTC，XSA-471 后续；明写 AMD 此前说 Zen5 不受 TSA-SQ/L1 影响的说法已更正、新变体 TSA-Fill 由 AMD-SB-3031 与 CVE-2026-0004 追踪、仅 Zen5 已知受影响、所有 Xen 版本受影响、无缓解手段、微码自 2026-09-23 进入 linux-firmware、VM 需重启而非迁移、提供 4.17–4.21 补丁）＋ Linux 内核提交 cf27412f19c9cc5909b9107cd1b3f4ab7608e362（Borislav Petkov，2025-11-05，x86/bugs: Mitigate TSA on AMD Zen5；6 文件 +15/-4，新增 X86_FEATURE_TSA_FILL_NO、把 0x1a 家族加入 TSA 黑名单、KVM 合成 CPUID 位；Zen5 靠 VERW_CLEAR 位判断而不查微码修订表）＋ Debian Security Tracker CVE-2026-0004（linux：bookworm 6.1.176-1 / bookworm security 6.1.190-1 / trixie 6.12.107-1 / trixie security 6.12.116-1 / forky 7.2.15-1 均 vulnerable，仅 sid 7.3.4-1 fixed；xen 各分支仍 vulnerable、unstable 未修）＋ Google Cloud CPU platforms 文档（Turin = 第五代 EPYC 9B45，对应 N4D/C4D/G4/H4D/Z4D）"
original_date: 2026-11-12
original_url: "https://thehackernews.com/2026/11/google-cloud-warns-three-amd-turin-cpu.html"
description: "本文解读 Google Cloud GCP-2026-081 与 AMD Turin（第五代 EPYC / Zen 5）的三个 Transient Scheduler Attacks。核心不是「三个新洞」：CVE-2024-36350（TSA-SQ）与 CVE-2024-36357（TSA-L1）是 2025-07-08 就已披露的旧洞，AMD-SB-7073 这次修正了 Zen 5 的受影响口径——AMD 此前认为 Zen 5 不受影响，Xen XSA-525 直接写明该说法已被更正；第三个 CVE-2026-0004 是新的 TSA-Fill，Xen/Debian/内核提交都用这个名称，但 Xen 引 AMD-SB-3031，Google 与 THN 引 AMD-SB-3055，公告编号口径并不统一。评分也要拆开：AMD 给两个旧 CVE 各 5.6（CVSS 3.1，本地/高复杂度/低权限），新 CVE 给 5.7（CVSS 4.0），Google 把整件事评为 Medium，三家均未报告在野利用、三个 CVE 都未进 CISA KEV。技术根因按 AMD 白皮书：TSA-L1 来自 L1D 微标签误命中造成的 false completion，TSA-SQ 来自存储队列里未就绪的旧 store 被错误转发；缓解靠新微码 + OS/虚拟机监控器配合，由 CPL0 在内核态→用户态、hypervisor→VM 切换以及进入 idle 前执行内存形式 VERW，WBINVD / FLUSH_CMD 无效，且可能影响性能。文章重点解释 Google 那句「重启客户机 OS 不够、必须 stop 再 start」：补丁要依据新 CPUID 位（TSA_SQ_NO / TSA_L1_NO / 新增 TSA_FILL_NO / VERW_CLEAR）决定是否开启缓解，Google 从 11-10 起更新 VM 看到的 CPU 信息，只有完整 stop/start 才会重新枚举；Xen 也说 VM 需重启而非仅迁移。并逐项列出 GCP-2026-081 的动作：主机侧 VM 间与 VM-宿主机间 Google 已缓解，客户需自己处理 VM 内部进程间风险；bare metal / 嵌套虚拟化、GKE（新节点镜像尚待公告更新）、Cloud Run（无需动作）。最后给出 Debian 与 Xen 的修包现状、自建 Turin 服务器需 PI 固件 + OS 双更新、以及本文未实测的边界。"
published: true
---

> 一手：谷歌云公告、AMD 三份安全公告与技术白皮书、Xen 公告、内核提交、Debian 追踪页
> 媒体：黑客新闻站（2026-11-12）
>
> 这条公告里最反直觉的一句是「重启客户机操作系统不够，必须 stop 再 start」。要理解它，得先看 VM 看到的 CPUID 被改了：这次补丁的开关不在内核代码里，而在虚拟 CPU 的特征位上。

11 月 12 日 The Hacker News 报道，Google Cloud 提醒使用 AMD Turin 处理器的客户：三个 TSA 侧信道可能让同一 VM 内的进程互相推断数据。Turin 是第五代 AMD EPYC（Zen 5），在 Google Cloud 里对应 C4D、N4D、H4D、Z4D、G4 机型及 C4D / Z4D 裸金属实例。

我把 Google 的安全公告、AMD 三份 bulletin 与技术白皮书、Xen 的 XSA-525、内核提交和 Debian tracker 都翻了一遍。这条新闻真正的层次比「三个漏洞」要多。

## 一、三个洞里，两个是旧洞换口径

Google 的 GCP-2026-081 于 2026-11-10 发布，整体评级 Medium，列出三个 CVE：

| CVE | 名称 | 来源 | AMD 评分 |
|---|---|---|---|
| CVE-2024-36350 | TSA-SQ（store queue） | 2025-07-08 已披露 | 5.6，CVSS 3.1 `AV:L/AC:H/PR:L/UI:N/S:C/C:H/I:N/A:N` |
| CVE-2024-36357 | TSA-L1（L1D cache） | 2025-07-08 已披露 | 5.6，同上 |
| CVE-2026-0004 | TSA-Fill | 新 | 5.7，CVSS 4.0 `AV:L/AC:H/AT:N/PR:L/UI:N/VC:H/VI:N/VA:N/...` |

前两个在 AMD-SB-7029（2025-07-08）里就公开过，当时针对 Milan / Genoa 等 Family 19h 平台给了 PI 固件与 OS 更新组合。这次的 AMD-SB-7073 是它的 Zen 5 后续版，措辞很克制：Zen 5「受影响的方式与先前已刻画的 AMD 处理器不同」，因此需要额外的 PI 固件包与对应缓解。

把话说得更直白的是 Xen XSA-525：

> AMD 此前表示 Zen 5 CPU 不受 TSA-SQ 和 TSA-L1 影响。这个说法已被更正。

这与 AMD 2025-07 技术白皮书能对上：白皮书当时写「截至本文发布，只有 Family 19h 产品已知受 TSA 影响」，并明确说 AMD Family 1Ah（Zen 5）也不受影响、只是不设置 `TSA_L1_NO` / `TSA_SQ_NO` 位。一年多后，这个判断被推翻。所以这次公告的分量，很大一部分来自一次厂商口径更正，而不是漏洞数量。

第三个 TSA-Fill（CVE-2026-0004）是新变体。这里有个容易踩坑的细节：Xen 的 XSA-525 把它记为 AMD-SB-3031，Debian tracker 的描述也写「TSA variant: TSA-Fill」；而 Google 公告与 THN 引用的是 AMD-SB-3055（2026-11-10 初始版，标题只写「瞬态执行漏洞」，没出现 TSA-Fill 字样）。编号不统一，本文按各自出处标注，不替厂商合并。

## 二、TSA 到底在泄漏什么

按 AMD 那份 Rev 2.0 技术白皮书，TSA 是一类瞬态执行侧信道：处理器在特定微架构条件下让指令「假完成」（false completion），短暂使用了无效数据，攻击者通过时序差异反推其他上下文的数据。

- TSA-L1：L1 数据缓存用基于线性地址的微标签辅助查找；微标签可能命中一个「L1 里其实没有该数据」的条目，于是假完成带出的无效数据来自该微标签对应的 L1 条目。可能影响内核→用户、hypervisor→guest、guest→guest、用户→用户等边界；不跨 SMT 线程，因为微标签不在 SMT 线程间共享。
- TSA-SQ：存储队列里的 store 通过 STLF 转发给匹配的 load；若地址匹配但旧 store 的数据还没就绪，load 可能假完成，带出曾占用该队列条目的旧 store 数据。AMD 判断主要影响内核→用户方向，因队列容量与切换路径上的 store 数量有限，跨 VM 或跨应用的泄漏不太可能；同样不跨 SMT 线程（但一个线程 idle 时其旧 store 可能被兄弟线程看到）。
- TSA-Fill：AMD-SB-3055 只描述为「可从 L1D 缓存推断数据，导致跨特权边界的敏感信息泄漏」，Xen/Debian 称其为 TSA-Fill；白皮书是 2025 年版，未涵盖这个新变体，本文不替它补技术细节。

缓解机制值得单独记：AMD 要求新微码 + 操作系统/虚拟机监控器更新配合，由 CPL0 软件在「受信任→不受信任」切换（内核退出到用户态、hypervisor 进入 VM）以及进入 idle 前执行内存形式的 `VERW` 指令来清除相关微架构结构；`WBINVD` 或 `FLUSH_CMD` MSR 不算有效缓解。AMD 也明说缓解可能影响性能，管理员应按自己工作负载评估风险。

白皮书还定义了 `TSA_L1_NO`、`TSA_SQ_NO`（CPUID `Fn8000_0021 ECX[2]/[1]`）与 `VERW_CLEAR`（`EAX[5]`）三个位，供软件判断是否需要开启缓解 —— 这正是下一节那句「重启不够」的钥匙。

## 三、为什么必须 stop/start

GCP-2026-081 把责任边界划得很清楚：

- Google 已缓解：VM 与 VM 之间、VM 与宿主机之间的攻击路径；
- 客户要自己处理：VM 内部的风险，例如同一核心上进程之间、进程与内核之间。

针对后者，公告给的动作是：

> 谷歌公告的处置说明：等操作系统厂商修复、装补丁，待平台自 11 月 10 日起更新了 VM 报告的 CPU 信息后，停机再启动该 VM；「Rebooting the guest OS isn't enough.」

道理在内核提交里。`cf27412f19c9`（Borislav Petkov，2025-11-05，`x86/bugs: Mitigate TSA on AMD Zen5`）做了 6 个文件、+15/−4 的改动：把 Zen 5（Family `0x1a`）加入 TSA 受影响名单，新增 `X86_FEATURE_TSA_FILL_NO`，让 `cpu_set_bug_bits()` 同时检查 `TSA_SQ_NO` / `TSA_L1_NO` / `TSA_FILL_NO`，并让 KVM 能把这三个位合成给 guest。提交说明还写：Zen 5 不再需要微码修订表，因为合适的微码会置起 `VERW_CLEAR` 位，检测大幅简化。

也就是说，打过补丁的内核靠 VM 看到的 CPUID 位决定要不要启用 `VERW` 缓解。Google 在宿主机侧改的是「呈现给 VM 的 CPU 信息」；纯 `reboot` 只是把同一个 guest 内核重跑一遍，虚拟 CPU 的特征位枚举不变。只有完整 stop → start 才会重新走一遍枚举。Xen 的 XSA-525 用的是同一逻辑：「修复的一部分是不再把 Zen5 报告为对 TSA-SQ/L1 安全……VM 需要重启（而非仅仅迁移）才能拿到这个状态变化。」

顺带一个公告没解决的运维问题：GCP-2026-081 没说明客户如何判断 CPU 信息更新是否已经到达某个 VM。THN 也点出了这一点。在 OS 厂商尚未发修复之前，公告同样没给临时动作。

## 四、各服务该做什么

按 GCP-2026-081 原文逐项：

- VM：等 OS 厂商修复 → 安装 → 待 Google 的 CPU 信息更新到达 → stop / start。
- Bare metal（C4D / Z4D）：自管 OS 或 hypervisor 的，等厂商修复可用后自行应用。
- VM 内再跑 hypervisor（嵌套虚拟化）：同样等 CPU 信息更新，之后 stop / start。
- GKE：Turin 裸金属实例的新节点镜像「将会提供」，升级节点即可带上 CPU 信息更新；公告写明新镜像可用时会更新本公告，写稿时尚未列出具体版本。
- Cloud Run：无需动作。

对自建 Turin 服务器，AMD 的口径是 PI 固件 + OS 更新两者都要：EPYC 8005 / 9005 对应 `TurinPI_1.0.0.B`（2026-07-10 目标日期），9005 另有 SEV FW `1.3A.05` 与 SNP attestation 的 TCB 值 `[SNP]=0x6`；CVE-2026-0004 另列微码 `C1:0x0B002175-Dense` / `B0:0x0B101066`，OS 侧点名 Linux / Windows / VMware。Xen 侧则说所有 Xen 版本受影响、无缓解手段，只能打 XSA-525 的补丁（4.17 至 4.21 各分支都有）并更新 dom0 微码；Zen 5 全部 TSA 变体的微码自 2026-09-23 起已进入 `linux-firmware`。

## 五、修包现状与暴露度

Debian Security Tracker 对 CVE-2026-0004 的状态（2026-11-12 查询）：

- `linux`：bookworm `6.1.176-1`、bookworm security `6.1.190-1`、trixie `6.12.107-1`、trixie security `6.12.116-1`、forky `7.2.15-1` 均标 vulnerable；仅 sid `7.3.4-1` 已修。
- `xen`：bookworm / trixie / forky / sid 各分支仍 vulnerable，unstable 也标未修。

这跟 THN 说的「只在 unstable 修了」一致，但要注意 Debian 的 `unstable` 即 sid，而 `forky`（testing）仍脆弱。

暴露度按出处标清：Google 与 AMD 都未在公告里报告在野利用，三个 CVE 均未进入 CISA KEV；AMD 的三个评分都是本地、高攻击复杂度、低权限；Google 整件事评 Medium。这些是厂商口径，不等于「风险为零」—— 云上多租户场景里，同一 VM 内能跑任意代码的攻击者依然是现实威胁模型。

## 六、边界

- 本文未实测：没在 Turin 或 GCP 机型上复现 TSA，没验证 `VERW` 缓解开关与性能影响；技术描述来自 AMD 白皮书、内核提交与各公告。
- 公告编号差异：Xen 引 AMD-SB-3031，Google / THN 引 AMD-SB-3055；两者都对应 CVE-2026-0004，本文不判断哪个为准。
- 白皮书版本差：AMD 技术指导是 2025-07 Rev 2.0，只覆盖 TSA-SQ / TSA-L1 与 Family 19h，未含 TSA-Fill 与 Zen 5 更正；新变体的微架构细节以 AMD 后续 bulletin 为准，本文未做推测。
- Google 未给的可观测性：如何确认某 VM 已收到 CPU 信息更新、GKE 新节点镜像的具体版本号，公告都还没写。
- 机型清单来自 GCP-2026-081 与 Google Cloud CPU platforms 文档（Turin = EPYC 9B45，对应 N4D / C4D / G4 / H4D / Z4D）；非 Turin 的老平台（Rome / Milan / Genoa）在 2025 年那轮公告里也收到过同样的 stop/start 指引，本文不重复展开。

## 七、结论

这条新闻读下来，最该记住的三件事：

1. 它是口径更正：Zen 5 从「不受 TSA-SQ/L1 影响」变成「受影响方式不同」，外加一个新变体 TSA-Fill；两个旧 CVE 编号沿用，第三个是 CVE-2026-0004。
2. 评分没那么吓人，但云上边界要分层：AMD 给 5.6 / 5.6 / 5.7，Google 评 Medium，无在野利用报告；Google 已挡住 VM 间与 VM-宿主机间路径，剩下 VM 内部进程间由客户自己补。
3. 「重启不够」有硬道理：缓解靠 CPUID 位驱动，Google 改的是虚拟 CPU 的特征枚举，必须 stop/start 才会重新读；Xen 也要求重启而非仅迁移。

对运维来说，动作顺序很明确：先确认机型是不是 C4D / N4D / H4D / Z4D / G4，再等自己 OS 厂商的内核修复，装完之后做一次真正的 stop/start，而不是 `reboot`。GKE 用户还得等公告补上新节点镜像版本。

## Sources

- The Hacker News（Swati Khandelwal，2026-11-12）：<https://thehackernews.com/2026/11/google-cloud-warns-three-amd-turin-cpu.html>
- Google Cloud GCP-2026-081：<https://docs.cloud.google.com/support/bulletins> ｜ CPU platforms：<https://docs.cloud.google.com/compute/docs/cpu-platforms>
- AMD-SB-7073：<https://www.amd.com/en/resources/product-security/bulletin/amd-sb-7073.html> ｜ AMD-SB-3055：<https://www.amd.com/en/resources/product-security/bulletin/amd-sb-3055.html> ｜ AMD-SB-7029：<https://www.amd.com/en/resources/product-security/bulletin/amd-sb-7029.html>
- AMD 技术白皮书《Mitigating Transient Scheduler Attacks》Rev 2.0：<https://www.amd.com/content/dam/amd/en/documents/resources/bulletin/technical-guidance-for-mitigating-transient-scheduler-attacks.pdf>
- Xen XSA-525：<https://xenbits.xen.org/xsa/advisory-525.html> ｜ Linux 内核提交 `cf27412f19c9`：<https://github.com/torvalds/linux/commit/cf27412f19c9cc5909b9107cd1b3f4ab7608e362>
- Debian Security Tracker CVE-2026-0004：<https://security-tracker.debian.org/tracker/CVE-2026-0004>
