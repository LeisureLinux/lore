---
title: "Ubuntu 补丁慢到被点名：安全研究员称远程内核漏洞该按小时修"
date: 2026-11-25
slug: ubuntu-slow-security-response-oss-security
category: 技术/解读
author: FreeLAMP.com
original_source: "oss-security 邮件列表（Hanno Böck，2026-11-25，Message-ID 20261125172638）＋ 一手核对该邮件引用的 Ubuntu CVE 跟踪页（CVE-2026-99288 / 99312 / 98432）、chalmovsky.com 分析与 GreyNoise 报告。"
description: "解读 Hanno Böck 在 oss-security 上对 Ubuntu 安全响应速度的批评：NoisyTCP（CVE-2026-99288，Linux TCP 栈远程内存破坏）11-16 公开细节，9 天后 Ubuntu 仍无修复而其他发行版发布时就有；KVM 宿主机逃逸 CVE-2026-99312（11-18 公开）同样无补丁；CVE-2026-98432 曾拖数周且据报已在野利用。实测 Ubuntu CVE 跟踪页显示多个 LTS 版本全是 Vulnerable / work in progress。Böck 还指出 Ubuntu LTS 内核 7.0.0-44 走的是向老版本回移补丁的路线，而 Debian stable 用 6.12.118+deb13 这类近期 LTS 内核，主张基于 kernel.org 长期支持版本。"
published: true
---

11 月 25 日，独立安全研究员 Hanno Böck 在 oss-security 邮件列表发了一封信，标题很直白：**「Slow Ubuntu security response times」**。他列举了三个最近的内核严重漏洞，指出 Ubuntu 的补丁速度「令人担忧」。

我核对了他引用的 Ubuntu CVE 跟踪页——情况确实如他所说。

## 一、被点名的三个漏洞

**CVE-2026-99288（NoisyTCP）**：Linux 内核 TCP 栈的远程内存破坏。11 月 16 日细节公开，Böck 写信的当天（11 月 25 日）已经过去 9 天，**Ubuntu 仍然没有修复**，而其他发行版在细节公布时就已经有补丁。

按 Ubuntu 自己的跟踪页，这个漏洞描述涉及 established lookup 里的 use-after-free：TCP established 的 ehash 查找是无锁的，socket 缓存用 `SLAB_TYPESAFE_BY_RCU`，RCU 读者还没读完，内存就可能被复用。攻击者用 SYN cookie request socket 驱动复用，可触发空指针解引用、`tcp_v4_rcv` 里的内核 panic（远程 DoS）。Ubuntu 给它评了 **High 优先级**（CVSS 3.1 分数 5.9 Medium——注意两者不一致）。

我查跟踪页时的状态：26.10、26.04 LTS、24.04 LTS、22.04 LTS、20.04 LTS、18.04、16.04 的 linux 包**全部是「易受攻击、修复进行中」**，从 7.0.0-45 到 4.4.0-294 都是这个状态，只有 14.04 trusty 标为「不受影响」。

**CVE-2026-99312**：AMD 虚拟化上的 KVM 宿主机逃逸，11 月 18 日公开。本号在 11 月 20 日专门写过（「一个 INIT 信号，让客机读到 127GB 宿主机内存」）。Böck 说这漏洞公开一周后 Ubuntu 也没补丁。

**CVE-2026-98432**：另一个远程 TCP 破坏漏洞，Ubuntu 之前就拖了数周才出修复；GreyNoise 近期报告显示它可能已经在野外被利用（针对 Check Point 安全管理服务器的入侵活动）。本号 11 月 1 日那篇《Ubuntu 全部 flavor 仍是「修复进行中」》讲的就是它。

## 二、Böck 的核心论点：小时级，不是天级甚至周级

他的原话是：

> 大家都能理解这些日子对安全团队并不轻松。Nevertheless，远程内核内存破坏漏洞，是那种我期望在**几小时内**、而不是几天或几周内就得到更新的东西。

这不是外行人的抱怨。Böck 是长期独立安全研究员（badkeys.info、itsec.hboeck.de），他挑的这三个漏洞都是**远程可触发、能导致内核崩溃或逃逸**的类型——不是需要本地交互的边缘问题。

## 三、更深的争议：回移补丁 vs 长期支持内核

邮件后半段提出了一个架构层面的批评，这部分比"补丁慢"更值得展开：

- 一台最近的 Ubuntu LTS 上，内核版本是 **7.0.0-44**；
- 一台 Debian stable 上，内核版本是 **6.12.118+deb13**。

Böck 的解读是：Ubuntu **不是**基于 kernel.org 的长期支持（longterm）内核，而是**选一个内核版本，然后长期往里回移补丁**；Debian stable 则跟进了较新的 longterm 内核（6.12 系列）。

他认为 Ubuntu 这种回移策略「几乎不可持续」（hardly viable），并主张所有发行版都应该基于 kernel.org 官方长期支持的内核版本。

这里要给出平衡的说法：两种策略各有拥趸。回移的好处是 ABI 稳定、驱动和周边生态不用跟着大版本动；跟 longterm 的好处是补丁与上游同步、减少回移遗漏和私有补丁累积。Böck 的观点是一家之言，不代表社区共识——但他把「补丁速度」和「内核维护模型」联系起来看，这个视角值得关注：**响应慢可能不只是流程问题，也可能是维护模型的结构性成本**。

## 四、对用户意味着什么

对跑 Ubuntu 的生产系统：

- 暴露在网络上的内核漏洞（TCP 栈、KVM），**不要假设发行版补丁会在小时级到达**——需要自己评估防火墙收敛、服务暴露面；
- 跟踪 CVE 时学会看发行版自己的 tracker 页面（状态是「易受攻击／修复中」还是「已发布」），别只看 CVE 编号有没有被"分配"；
- 如果业务对内核漏洞响应速度要求高，这可能是一个重新评估发行版（或内核获取方式）的理由。

对 Ubuntu 本身：CVE 跟踪页上那一长串「修复进行中」是公开的、可核查的——这至少说明状态透明。真正的压力在于把它变成「已修复」的时间。

## 参考资料

- oss-security 原信（Hanno Böck，2026-11-25）：https://www.openwall.com/lists/oss-security/2026/11/25/9
- Ubuntu CVE-2026-99288 跟踪页：https://ubuntu.com/security/CVE-2026-99288
- Ubuntu CVE-2026-99312 跟踪页：https://ubuntu.com/security/CVE-2026-99312
- Ubuntu CVE-2026-98432 跟踪页：https://ubuntu.com/security/CVE-2026-98432
- Chalmovsky 分析：https://chalmovsky.com/posts/wtf-ubuntu
- GreyNoise 在野利用报告：https://www.greynoise.io/blog/check-point-security-management-servers-intrusion-campaign
