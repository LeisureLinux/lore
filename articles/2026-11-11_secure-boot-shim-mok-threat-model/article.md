---
title: "Secure Boot 不是「锁死系统」：一篇借用 shim 的文章，把威胁模型读错了"
date: 2026-11-11
slug: secure-boot-shim-mok-threat-model
category: 技术/解读
author: FreeLAMP.com
original_source: "一手核对：Leo Smith《Not so secure boot》（leosmith.wtf，2026-11-08）全文与全部命令 ＋ Microsoft Learn《Windows Secure Boot Key Creation and Management Guidance》（Microsoft Corporation UEFI CA 2011 用途与 db 配置）＋ Ubuntu 官方 Secure Boot 文档（shim/MokManager/MOK 注册流程、明确说明会削弱保护）＋ SUSE《SUSE and Secure Boot: The Details》（MOK 设计初衷、需物理在场、GPLv3 与反 tivoization）＋ Intel《Secure the Network Infrastructure – Secure Boot Methodologies》与《UEFI Secure Boot in Linux》（shim 由微软 CA 签名、MOKList 为 Boot Service 变量、OS 运行时不可访问）＋ UEFI Forum 白皮书（Secure Boot 针对 pre-boot 恶意代码、更改信任需物理在场）＋ CERT VU#309662（2022 年真正的 shim Secure Boot 绕过漏洞，CVE-2022-34301/34302/34303）＋ 本机实测 sbverify --list /usr/lib/shim/shimx64.efi 与 pesign -S"
original_date: 2026-11-08
original_url: "https://leosmith.wtf/blog/not-so-secure-boot.html"
description: "本文核对 Leo Smith 的《Not so secure boot》。作者用一张 Ubuntu/Debian/Fedora 的微软签名 shim，配合自签 MOK 与 MokManager 注册，在开着 Secure Boot 的企业笔记本上从 U 盘引导了自己的系统，结论是「not so secure boot」。但这套机制在微软、Ubuntu、SUSE、Intel 的官方文档里都是明确设计：Secure Boot 的目标是校验启动链完整性、防 EFI 级恶意代码，不是把机器锁到某个操作系统；Microsoft Corporation UEFI CA 2011 本就用于签第三方引导加载器；MOK 就是让机器所有者注册自己的密钥，SUSE 文档写明注册过程要重启并物理在场，Intel 文档写明 MOKList 是 Boot Service 变量、OS 运行时不可访问；Ubuntu 官方文档也直说 MOK 会削弱 Secure Boot 保护。文章逐层拆解三个概念混淆：完整性不等于锁定系统、物理在场不在 Secure Boot 的威胁模型内、签名验证不等于内核可信。也指出作者观察里真实有价值的部分：企业机器默认信任第三方 CA、启动菜单无需 BIOS 口令即可选外部设备、以及让自制系统在启动链上「长得像 Ubuntu」的运维可见性问题。并对照 2022 年 CERT VU#309662 那三个真正的 shim 绕过漏洞（可远程/持久化、需进 dbx），说明「设计允许的注册」与「漏洞绕过」的区别。本机实测补了一处校正：Debian 的 /usr/lib/shim/shimx64.efi 本身未签名（sbverify --list 报 No signature table present），发行版另出已签名版本，所以「随便拿一个 shim 就是微软签好的」并不成立。结论给出防守方清单：清掉不需要的第三方 CA、设 BIOS 口令、按需用 dbx/MOK 口令、看启动链日志而不是只看 Secure Boot 开关。"
published: true
---

> 一手：一篇用「借用 shim + 自签 MOK」在开启 Secure Boot 的机器上引导自制系统的文章（2026-11-08）
> 官方：微软密钥管理指南、Ubuntu / SUSE / Intel 的 shim 与 MOK 文档、UEFI Forum 白皮书、CERT 漏洞公告
> 实测：本机 `sbverify --list` / `pesign -S` 验证 shim 签名状态
>
> 这篇文章的现象是真的，但它给现象贴的标签值得商榷。

11 月 8 日 Leo Smith 发了篇《Not so secure boot》，讲他怎么在一台开着 Secure Boot 的企业笔记本上，从 U 盘启动了自己的系统。步骤不复杂：拿一个发行版里由微软签过名的 shim，自己用 `openssl` 生成一对 MOK 密钥，给内核签名，把 shim 和 MokManager 放进启动盘；插盘、按 F7 选外部设备、shim 校验 GRUB 失败后自动进 MOK 注册界面，选自己的证书，重启，GRUB 就起来了。

作者的结论写在标题里：Secure Boot 没那么安全。他甚至觉得这套手法在「操作安全」上很划算 —— 让自制系统在启动链上看起来像 Ubuntu。

现象完全成立，但把它读成「Secure Boot 被绕过」，是把三件事混在了一起。 我按官方文档逐条核了一遍，还顺手在本机验了他给的那条 `sbverify` 命令。

## 一、先纠正最根本的那个误解：完整性不等于锁定系统

作者自己诚实地写了研究前的想法：他以为 Secure Boot 是「锁定这台机器能跑什么操作系统」，钥匙由微软控制。查完资料后他给出的新定义是「确保启动系统的完整性」—— 这个修正方向对，但他紧接着又把它读窄了：「签名在接受的数据库里，就这样」。

UEFI Forum 的白皮书写得很直接：Secure Boot 要解决的是 pre-boot 阶段执行未受保护代码的问题，攻击面包括引导加载器、option ROM、以及「evil maid」这类在启动前植入的持久化恶意代码。微软的密钥管理指南说得更具体：那张 Microsoft Corporation UEFI CA 2011 的用途，就是让 OEM 把它放进 `db`，好让第三方 UEFI 驱动、应用和引导加载器无需用户额外操作就能运行；文档还列了它的证书哈希，并说明 2023 版把「第三方引导加载器」与「option ROM」拆成两张证书以便细粒度控制。

换句话说，企业机器默认信任微软第三方 CA，是为了让 Linux 发行版、网卡固件、某些 UEFI 工具能正常启动，不是配置疏漏。本站 10 月那篇讲 2026 年证书到期的文章也核过同一张表：2011 版在 6 月 27 日到期、2023 版把它拆成两张，微软文档原话是「允许对系统信任做更精细的控制」。

所以 Secure Boot 校验的是「这个 EFI 镜像的签名链能不能追到 `db` 里某个可信证书」，不是「这个内核是不是厂商批准的那一个」。作者那句「签名在数据库里，就这样」其实已经说对了，只是他把它当成了缺陷。

## 二、shim 与 MOK：这是设计，不是后门

作者最惊讶的一点是：为什么一张多年不变的微软签名，能撑住不断变化的 GRUB 和内核？答案是 shim + MOK，而且这套分工在官方文档里写得清清楚楚。

- shim 是预引导加载器，由微软 UEFI CA 签名，固件用 `db` 里的证书验它。它内部另带发行版自己的证书，用来验下一阶段的 GRUB —— 于是发行版修 GRUB、换内核都不必回头找微软重签。Intel 的应用笔记和 Ubuntu 官方文档都是这么描述的。
- MOK（Machine Owner Key） 是给机器所有者用的：想跑自己改过的内核、第三方驱动，就自己生成密钥注册进去。SUSE 那篇经典说明连动机都写明了 —— GPLv3 要求用户能自由修改 GRUB 与内核，不能把机器做成 tivoized，所以必须留一条由所有者授权的通道。

关键在授权条件。SUSE 文档原文：注册过程要重启机器、在 shim 加载时中断引导才能进入注册模式，也就是需要物理在场。Intel 的讲义补充了存储层：MOKList 是 Boot Service 非易失变量，OS 运行时不可访问，所以一个已经跑起来的系统里的恶意脚本没法偷偷往里塞密钥。UEFI Forum 白皮书也把「更改信任凭据需要物理在场」列为规范设计。Ubuntu 文档则给出了另一半实话，它写着「This weakens Secure Boot's protections」：MokManager 会在首次启动时用文本界面让用户确认指纹、重启完成注册；它同时明确写着，这种方式被认为是对需要第三方模块场景的可接受折衷，但会削弱 Secure Boot 的保护，管理员应当知情。

把这几条并起来看，文章的「发现」其实是：作者在能物理接触机器、能进启动菜单的前提下，完成了一次需要物理在场的密钥注册，而这正是 MOK 被设计出来做的事。他自己那句「不需要 BIOS 口令就能选从其他设备启动」，恰恰点出了前提条件。

顺带补一处实测校正。原文让读者用 `sbverify --list you_shim_file.efi` 确认「确实是微软签的」，这条命令本身没错（本机 `sbverify --help` 确认 `--list` 是「列出所有签名但不校验」）。但我对本机 Debian 的 `/usr/lib/shim/shimx64.efi` 跑了一下：

```
$ sbverify --list /usr/lib/shim/shimx64.efi
warning: data remaining[888832 vs 1016789]: gaps between PE/COFF sections?
No signature table present
```

`pesign -S` 同样是 `No signatures found.` —— 这个文件是未签名的 shim，发行版另出 `shimx64.efi.signed` 之类已签名版本。所以「从任意发行版里拿一个 shim 就自带微软签名」并不成立，得挑对文件；这也是原文略过的一步。

## 三、真正有价值的部分，和它没说的那部分

把「绕过」的标签拿掉之后，这篇文章仍有三处值得运维看一眼：

1. 默认信任面比很多人以为的宽。 大多数消费与企业固件都装了微软第三方 CA，作者提到 HP Wolf Security 某些批次开、某些没开，属于厂商差异。如果一台机器根本不需要跑第三方 EFI 应用或 Linux，这张证书就是多余的信任。
2. 「长得像 Ubuntu」是可见性问题，不是密码学问题。 启动链日志、EDR 里看到的是一个由微软 CA 签过的 shim + 一次 MOK 注册；它和「Ubuntu 安装盘」在签名者层面确实 indistinguishable。对依赖「这条链看起来像谁」做判断的资产管理与审计流程，这是个实际缺口。
3. 外部启动介质 + 无 BIOS 口令，让「物理在场」这个前提变得非常容易满足。作者特意写了「不需要 BIOS 口令」，这句话比他的结论更有用。

但文章没讲的是威胁模型的边界。Secure Boot 从不承诺防住能按住电源键、插 U 盘的人：微软文档把「持有密钥的人」和「有物理访问的人」并列为两类受信任用户；UEFI Forum 白皮书讨论 evil maid 时也强调物理在场。真要在这种场景下守住，得靠固件口令、禁用外部启动、`dbx` 撤销、TPM 度量与磁盘加密一起上，而不是指望 Secure Boot 单独扛。

对照一下真正的 shim 漏洞就更清楚了：CERT 的 VU#309662（2022 年，CVE-2022-34301 / 34302 / 34303）记录的是某些已签名第三方 UEFI 引导加载器可被特制安装器或 EFI shell 欺骗，从而在不该执行未签名代码时执行了它，还能跨重装持久化、绕过基于 OS 的 EDR。那类问题的处置是打补丁、把受影响 shim 加进 `dbx` 撤销列表。而本文描述的路径里，每一步都在规范允许的通道内：固件验了签名、shim 正确报告校验失败、MokManager 要求人在重启时确认、注册后新密钥才生效。一个是验证被欺骗，一个是所有者主动授权，把它们都叫「bypass」会掩盖真正需要打补丁的那类问题。

## 四、防守方该做什么

- 清点信任库。 用 `mokutil` / 固件设置 / `efi-readvar` 看 `db` 里到底有哪些证书；只跑单一系统的机器，考虑清掉用不到的 Microsoft 第三方 CA（注意这会同时影响某些 option ROM 与 Linux 启动）。
- 给固件上口令、限制外部启动。 作者那句「F7 不需要 BIOS 口令」就是最直接的整改项。
- 把 MOK 当敏感配置管。 Ubuntu 文档说明注册流程可用一次性密码保护；已有 MOK 的机器，`mokutil --export` / `--list-enrolled` 应纳入资产盘点。没有第三方驱动需求的机器，理想状态是压根没有 MOK。
- 盯 `dbx` 与 shim 版本。 真正的问题是 VU#309662 那类需要撤销的已签名加载器，以及 2011 证书到期后的双签名 shim 迁移（本站 10 月那篇专门讲过 KEK 门控与 PCR7/BitLocker 的坑）。
- 日志里看行为，不看开关。 「Secure Boot: enabled」只说明固件在做签名校验；MOK 注册、启动项变化、外部介质启动这些事件才是有信号的那部分。

## 五、事实边界

- 本文未复现作者的完整流程（未制作启动盘、未在开启 Secure Boot 的机器上注册 MOK）；其步骤、截图与命令行均据原文转述。
- 本机实测仅覆盖 Debian 的 `/usr/lib/shim/shimx64.efi`（未签名，见上），不代表其它发行版或 `shimx64.efi.signed` 的签名状态；本机不支持 Secure Boot（`mokutil --sb-state` 报 unsupported/disabled）。
- 微软、Ubuntu、SUSE、Intel、UEFI Forum 文档均按公开版本核对；MOK 是否要求密码、MokManager 具体交互在不同发行版与 shim 版本间有差异，以本机文档为准。
- CERT VU#309662 的 CVE 与影响面取自公告原文，本文未独立验证各厂商修复状态。

## 六、结论

这篇文章演示的操作是真的：一张微软签过的 shim、一对自签 MOK、一次物理在场的注册，就能在 Secure Boot 开启的机器上引导你自己的内核。 但它证明的是 Secure Boot 的边界，不是它的失效 —— 校验启动链完整性、同时允许机器所有者注册自己的密钥，这两件事从一开始就是同一套设计，SUSE 写它甚至是为了满足 GPLv3。

值得带走的判断是：「Secure Boot 开着」不等于「这台机器只跑我批准的系统」。前者是签名校验，后者需要密钥管理、固件口令、撤销列表与物理安全一起成立。把两者混为一谈，既会高估一次 MOK 注册的严重性，也会低估真正该补的那类漏洞。

## Sources

- Leo Smith《Not so secure boot》（2026-11-08）：<https://leosmith.wtf/blog/not-so-secure-boot.html>
- Microsoft Learn《Windows Secure Boot Key Creation and Management Guidance》：<https://learn.microsoft.com/en-us/windows-hardware/manufacture/desktop/windows-secure-boot-key-creation-and-management-guidance>
- Ubuntu 官方 Secure Boot 文档：<https://documentation.ubuntu.com/security/security-features/platform-protections/secure-boot>
- SUSE《SUSE and Secure Boot: The Details》：<https://www.suse.com/blog/suse-and-secure-boot-the-details>
- Intel《Secure the Network Infrastructure – Secure Boot Methodologies》（PDF）与《UEFI Secure Boot in Linux》（PDF）
- UEFI Forum《UEFI Secure Boot in Modern Computer Security Solutions》（2013，PDF）
- CERT VU#309662：<https://www.kb.cert.org/vuls/id/309662>
- 本站旧文《Secure Boot 证书到期》：<https://freelamp.com/articles/2026-10-20_secure-boot-certificate-expiration-2026-kek-gating/>
