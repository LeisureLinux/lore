---
title: "Intel Xe 驱动：为 vGPU profile 铺路的 5 个补丁，还没带来新功能"
date: 2026-11-12
slug: intel-xe-sriov-vgpu-profile-prep-linux-7-5
category: 技术/解读
author: FreeLAMP.com
original_source: "一手核对：Phoronix《Intel Xe Driver Preparing SR-IOV Provisioning For vGPU Profiles》（Michael Larabel，2026-11-12；Linux 7.5 周期、本周 drm-xe-next pull、5/5 patches、推测与 Crescent Island 相关）＋ lore.kernel.org 本周 [PULL] drm-xe-next（Thomas Hellström，2026-11-12 10:42 +0100，Message-ID avWKCypDrHj5139M@fedora，tag drm-xe-next-2026-11-12，基线 3b8860fe2581…、终点 be73339dd9d70623b7dbc9c4e3b966824b771069，收件人 Dave Airlie / Simona Vetter；Highlights 明写 Prepare SR-IOV provisioning for vGPU profiles 5/5 patches，作者 Piotr Piórkowski 与 Michal Wajdeczko；同批还有 Wa_16031259911、GU_MISC irq 清理、Crescent Island Wa_14028586678、CCS iGPU 挂起优化、LMTT dir ptr 修复、select configfs 等）＋ [PATCH v1 0/5] cover letter（Piotr Piórkowski，2026-10-27，3 文件 98 insertions / 78 deletions，明写「upcoming VGPU profiles support」与「No functional change is expected, other than the stricter locking」，Wajdeczko 3 个 / Piórkowski 2 个补丁）＋ patch 1/5 与 3/5 原文（lockdep_assert_held、guard(mutex)、_locked 变体、GGTT / LMEM / GuC ctxs / doorbells 公平分配、sched_if_idle 策略）＋ Phoronix《Intel Continues Enabling The GPU D-Series Crescent Island Driver Support For Linux 7.5》（Xe3P 架构 AI 加速器、Linux 7.5 是 2027 年首个稳定系列、含 CPER RAS 与 ECC 支持）＋ intel-xe 列表历史（2024 年 SR-IOV debugfs 结构、GGTT/LMEM/contexts/doorbells 配额、VFs 需从 PF 资源中划出；2025 年 auto-provisioning IGT 测试；2025-06 LKML 询问 SR-IOV 平台支持范围）＋ 2026-09 Phoronix 报道 Nova 的 vGPU manager 与 VFIO variant driver 作行业对照"
original_date: 2026-11-12
original_url: "https://www.phoronix.com/news/Linux-7.5-Intel-Xe-vGPU-Profile"
description: "本文拆解 Phoronix 那条「Intel Xe 为 vGPU profile 准备 SR-IOV provisioning」的真实进度。核心纠偏：这不是 Linux 7.5 已支持 vGPU profile，而是 2026-11-12 本周 drm-xe-next pull 里的 5 个预备补丁；cover letter 明写「除收紧锁之外不预期有功能变化」，vGPU profile 本身仍是 upcoming。技术内容：Xe 的 SR-IOV 把一块物理 GPU 切成 PF 与多个 VF，PF 侧通过 debugfs 把 GGTT、LMEM、GuC context IDs、GuC doorbell IDs 以及调度参数（exec quantum、preempt timeout、sched_if_idle 优先级）按配额分给 VF，已有 auto / manual  provisioning mode 与 fair 公平分配函数；本次由 Michal Wajdeczko（3 个）与 Piotr Piórkowski（2 个）把 provisioning mode 变更与 bulk priority 拆成需要持有 master mutex 的静态 helper，为 fair 分配补 _locked 变体、删掉无用户的非锁版本，让模式切换、VF 自动分配与回收都在同一把锁下完成，消除「检查模式」与「实际分配」之间模式被改掉的竞态。文章解释为什么要这样改：将来的 vGPU profile 是预设资源套餐，需要一次原子地把模式与 PF/VFs 配额同时落下去。并写清边界：pull 由 Thomas Hellström 发给 drm-next 维护者，tag drm-xe-next-2026-11-12，还要经 drm-next 与合并窗口才谈得上 Linux 7.5；Phoronix 把动机「presumably」关联到 Crescent Island（Xe3P 架构的 Intel GPU D Series AI 加速器）属推测，官方 cover letter 未提硬件；同批 pull 里确有 Crescent Island 的 Wa_14028586678、CCS iGPU 挂起优化与 LMTT 修复；本文未编译内核、未实测任何 VF。结论：这是一次典型的内核「先修锁、后加功能」铺垫，新闻价值在结构而非可用特性。"
published: true
---

> 一手：Phoronix 报道、lore.kernel.org 的 `[PULL] drm-xe-next` 与 `[PATCH v1 0/5]` cover letter 及补丁原文
> 对照：Crescent Island 系列报道、intel-xe 列表历史、Nova 的 vGPU manager
>
> 这条新闻容易被读成「Linux 7.5 要支持 Intel vGPU 了」。把 pull request 和 cover letter 翻开看，实际进度要往后退一格：这 5 个补丁没有新增任何功能，vGPU profile 本身还没来。

11 月 12 日 Phoronix 报道，面向 Linux 7.5 周期，Intel Xe 驱动在本周的 `drm-xe-next` pull request 里合入了一批「为 vGPU profile 准备 SR-IOV provisioning」的补丁，5/5 全部推送。报道还顺带猜了一句：从时间点看，动机大概跟即将到来的 Intel GPU D Series（Crescent Island）硬件有关。

我去把 lore 上那封 pull、10 月 27 日的 patch cover letter 和其中两个补丁的 diff 读了。值得写下来的恰恰是那些不体现在标题里的东西。

## 一、先把进度摆正

这封 pull 是 Thomas Hellström 于 2026-11-12 10:42 +0100 发给 Dave Airlie 与 Simona Vetter 的（Message-ID `avWKCypDrHj5139M@fedora`），tag 为 `drm-xe-next-2026-11-12`，基线 `3b8860fe2581…`、终点 `be73339dd9d7…`。也就是说它目前停在 Xe 驱动自己的 next 分支，等待被 drm-next 拉取，再往后才是合并窗口。Phoronix 标题里的「Linux 7.5」指的是目标周期 —— 按该站另一篇 Crescent Island 报道的说法，7.5 会是 2027 年第一个稳定内核系列。

Pull 的 Highlights 里那一节写得很清楚：

> 为 vGPU profile 准备 SR-IOV provisioning —— 5 个补丁全部推送

关键词是「Prepare」以及「为将来的 vGPU profile 支持做准备」。补丁作者是两人：Michal Wajdeczko 3 个、Piotr Piórkowski 2 个（Phoronix 只笼统写成「Intel 驱动工程师」）。cover letter 里更有一句媒体没引的话，几乎决定了这篇文章该怎么写：

> 「No functional change is expected, other than the stricter locking.」

除收紧锁之外，不预期有功能变化。这不是新特性落地，是给新特性打地基。

## 二、Xe 的 SR-IOV 现在能做什么

要理解改了什么，得先看现有机制。SR-IOV 把一块物理 GPU 切成 PF（Physical Function） 与若干 VF（Virtual Function），每个 VF 可以透传给一台虚拟机，于是「一块卡变多块 vGPU」。

Xe 驱动里 PF 侧的活儿叫 provisioning：从 PF 自己可见的资源里划出一份份配额给 VF。按 2024 年以来 intel-xe 列表上的补丁与文档，这些资源包括：

- GGTT（全局 Graphics Translation Table）空间；
- LMEM（本地显存）配额，需要 LMTT 相关设置；
- GuC context IDs 与 GuC doorbell IDs；
- 调度参数：execution quantum、preemption timeout，以及由调度优先级映射出的 `sched_if_idle` 策略。

PF 通过 debugfs 暴露 `ggtt_provisioned` / `ggtt_spare`、`lmem_quota`、contexts / doorbells 的 provisioned 与 spare 等属性，管理员可读写配额。分配模式有 auto（启用 VF 时按「fair」规则自动均分）与手动两种，2025 年 IGT 还加了 auto-provisioning 的测试，验证资源是否公平分配、VF 禁用后是否释放、各 VF 区间是否互斥。

所以「把一块 Intel GPU 分给多台 VM」这件事，Xe 驱动早就在做。这次动的是分配代码的锁结构。

## 三、5 个补丁具体改了什么

按 cover letter 与 diff，改动集中在 3 个文件：`xe_gt_sriov_pf_config.c/.h` 与 `xe_sriov_pf_provision.c`，共 98 行插入、78 行删除：

- 把「切换 provisioning mode」和「批量设置调度优先级」的函数拆成静态 helper，helper 内部用 `lockdep_assert_held(xe_sriov_pf_master_mutex(...))` 断言调用者已经持有 master mutex；对外的原函数保留，改成用 `guard(mutex)` 自己拿锁后再调 helper。
- 为 fair 分配补上 `_locked` 变体：`set_fair_ggtt_locked`、`set_fair_lmem_locked`、`set_fair_ctxs_locked`、`set_fair_dbs_locked`，以及汇总的 `xe_gt_sriov_pf_config_set_fair_locked()`。原先每个资源各拿一次锁，现在整组资源在同一把锁下完成；没有用户的非锁版本被删掉。
- 让 provisioning mode 变更、VF 自动分配、VF 回收都跑到 master mutex 之下。

目的写在 cover letter 里：将来的 vGPU profile 支持会在「已经持有 master mutex」的状态下同时改 provisioning mode 并给 PF 与 VFs 分配资源。若沿用旧结构，「先检查当前模式、再实际分配」这两步之间模式可能被另一条路径改掉，分配就会按过期模式算。把两步收进同一把锁，这个窗口就没了。

顺带一个收益：批量优先级设置原先对每个 GT 单独加锁，现在所有 GT 在单锁下更新 `sched_if_idle` 策略。这属于锁粒度变化，不是新功能。

用一句话概括：vGPU profile 大概是一组预设资源套餐（多少显存、多少上下文、什么调度优先级），要一次性原子地套到 PF 与 VFs 上；这 5 个补丁先把「套餐落地」所需的原子性准备好。

## 四、Crescent Island 那条线：推测与事实要分开

Phoronix 写的是：从时间点看，动机大概（presumably）与即将到来的 Intel GPU D Series（Crescent Island）硬件一致 —— 一个明确的推测，cover letter 和 pull 里都没有把 vGPU profile 与具体硬件绑定。

能确认的事实是同一批 pull 里确实有不少 Crescent Island 相关条目：

- `drm/xe/cri: Implement Wa_14028586678`（Fei Yang），以及 resume 时等 PCODE 初始化后再应用 tile workaround（Daniel Charles）；
- 另一个系列 `Fix VF probe issue due to missing LMTT dir ptr`，修的是 VF probe 失败（Satyanarayana K V P），跟虚拟化栈直接相关；
- 还有 `drm: xe: select configfs`（Arnd Bergmann）、CCS iGPU 挂起时跳过 BO eviction、`Wa_16031259911`、GU_MISC 中断清理等。

按 Phoronix 另一篇报道，Crescent Island 是 Xe3P 架构的 AI 加速器，现在叫 Intel GPU D Series；Linux 7.5 里还会给它加 CPER RAS 错误记录、内存双比特 ECC 处理与 OOBMSM 遥测 late binding。把这些放一起看，「数据中心卡需要把 GPU 切成多份给不同租户」是合理方向，但仍属推断，本文不把它写成官方动机。

顺带一个行业对照：2026 年 9 月 Phoronix 报道过 NVIDIA 给开源 Nova 驱动提交 vGPU manager 与 VFIO variant driver（13 个补丁）。两家都在把 GPU 虚拟化的管理面往上游开源驱动里搬，路线不同，方向一致。

## 五、边界与口径

- 未合并进 Linux 7.5。写稿时这批代码在 `drm-xe-next-2026-11-12` tag 里，是给 drm-next 的 pull；是否进 7.5、进哪个 rc，取决于后续拉取与合并窗口，本文不预设结果。
- vGPU profile 尚未实现。标题里的 profile 一词来自「准备」「为……做准备」「即将到来」这组措辞；profile 的具体定义、对外 UAPI（sysfs / configfs / debugfs 怎么呈现）、支持哪些 GPU，一手材料里都还没给出。
- 无功能变化是 cover letter 的自述，指除锁语义外不应有行为差异；这不等于「零风险」，只是这次改动的意图。Xe.CI 的 KUnit 与 BAT 在 10-27 报成功，FULL 那轮报过 failure，作者在 11-10 有回复，本文未逐条核对 CI 结论。
- 支持范围别外推。2025 年 6 月 LKML 上有人问过 Xe SR-IOV 的平台覆盖，当时列表给出的答复是上游 Xe 只在部分平台启用 `has_sriov`；本文没有核到 2026-11 的完整平台清单，因此不列「哪些卡能用」。
- 本文未编译内核、未启用 VF、未跑 IGT 测试；所有代码细节来自补丁 diff 与 cover letter，时间与数字为 2026-11-12 时点。
- Phoronix 的「Linux 7.5」是目标周期，不是已发布版本；把「5/5 patches pushed」读成「7.5 已合入」会差着好几层。

## 六、结论

内核开发里有一类提交，单独看几乎没什么可报道：拆函数、加 `_locked` 变体、把两步进一把锁、删掉没人用的旧入口。它的价值全在后面那个还没来的功能上 —— 等 vGPU profile 真要落地时，模式切换与配额分配必须是一次原子操作，否则套餐会算错。

所以这条新闻的准确读法是：Intel 为 Xe 的 vGPU profile 先把锁结构修好了，功能还在后面。对运维和虚拟化用户来说，现在没有任何新东西可以打开；值得盯的是后续那批真正定义 profile、暴露 UAPI 的补丁，以及它最终落到哪个内核版本。

## Sources

- Phoronix《Intel Xe Driver Preparing SR-IOV Provisioning For vGPU Profiles》（Michael Larabel，2026-11-12）：<https://www.phoronix.com/news/Linux-7.5-Intel-Xe-vGPU-Profile>
- 本周 pull：<https://lore.kernel.org/dri-devel/avWKCypDrHj5139M@fedora/> ｜ tag `drm-xe-next-2026-11-12`：<https://gitlab.freedesktop.org/drm/xe/kernel.git>
- Patch cover letter 与 5 个补丁：<https://lore.kernel.org/intel-xe/20261027103009.1259199-1-piotr.piorkowski@intel.com/>（1/5：<https://lore.kernel.org/intel-xe/20261027103009.1259199-2-piotr.piorkowski@intel.com/>；3/5：<https://lore.kernel.org/intel-xe/20261027103009.1259199-4-piotr.piorkowski@intel.com/>）
- Phoronix《Intel Continues Enabling The GPU D-Series "Crescent Island" Driver Support For Linux 7.5》：<https://www.phoronix.com/news/More-Intel-D-Series-Linux-7.5>
- Xe SR-IOV debugfs / provisioning 背景：<https://lists.freedesktop.org/archives/intel-xe/2024-April/033247.html> ｜ <https://lists.freedesktop.org/archives/intel-xe/2024-April/032260.html> ｜ auto-provisioning IGT：<https://lists.freedesktop.org/archives/igt-dev/2025-January/084282.html>
- Xe SR-IOV 平台支持范围讨论（2025-06）：<https://lkml.iu.edu/2506.3/09825.html>
