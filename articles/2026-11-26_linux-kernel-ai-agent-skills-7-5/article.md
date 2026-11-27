---
title: "Linux 内核要把 AI Agent 技能收进源码树"
date: 2026-11-26
slug: linux-kernel-ai-agent-skills-7-5
category: 技术/解读
author: FreeLAMP.com
original_source: "Phoronix 报道（Michael Larabel，2026-11-26）＋ 一手核对 Sasha Levin/Ted Ts'o 的 patch series（v1–v5，含 v3 0/7  cover letter 与各 SKILL.md）、LKML/Patchew 存档、It's FOSS 与 freenode 技术报道。"
description: "解读 Linux 内核拟在 7.5 合并窗口合入 agents/skills 目录：Sasha Levin（NVIDIA，LTS 维护者）与 Ted Ts'o 推动，把用于指导 AI 编码代理的技能收进内核树。起因是 Maintainers Summit 上 Hannes Reinecke 估计 15–20% 的 Fixes: 标签是错的；五个技能：find-fixes（定位真正引入 bug 的 commit）、stable-tag（判断是否需要回移/生成标签）、find-siblings（用 Coccinelle 找同类 bug）、commit-message（写/审 commit message 和 PR 文本）、writing-kunit-tests（Ted Ts'o 贡献）。技能是 SKILL.md，指向已有流程文档并补充 AI 常犯的坑；只检查与报告，不改文件、不建 commit、不发邮件，无法确定就不返回标签。Sasha 已请求把 agents 分支从 linux-next 移除，准备提交给 Linus；仍待 7.5 合并窗口。"
published: true
---

11 月 26 日，Phoronix 报道：Linux 内核可能会在 **7.5 合并窗口**（12 月下旬）迎来一批 **AI agent 技能**——不是实验性外围工具，而是正式收进内核源码树的 `agents/skills/` 目录。

推动者是 Sasha Levin（NVIDIA 工程师、Linux LTS 分支的共同维护者），Ted Ts'o 也贡献了一个技能。今天 Sasha 在邮件列表上请求把他的 `agents` 分支从 linux-next 移除，理由是「它包含 agent skills 系列，我打算发给 Linus」——这是提交主线前的标准信号。

## 一、起因：15–20% 的 Fixes 标签是错的

这件事的源头是 Maintainers Summit 上的一个提问。Ted Ts'o 问：stable 树有没有办法处理错误的 `Fixes:` 标签？Hannes Reinecke 估计——**15% 到 20% 的 Fixes 标签是错的**，常见原因是作者跑了 `git blame`，把第一个改到那一行的 commit 当成了引入 bug 的 commit，而那可能只是一次代码移动或重构。

这个数字很要命：`Fixes:` 标签告诉 stable 维护者和各发行版，某个修复需要进哪些内核分支。标错了，修复会被塞进错误的分支，或者干脆漏掉某个受影响的内核。

Sasha 的团队本来就用 LLM 工作流去追真正引入 bug 的 commit，别人问起后就决定把这些流程标准化，作为 agent skills 贡献进内核树。

## 二、五个技能分别干什么

补丁系列（v5 为 6 个 patch、后来迭代到 v3 0/7 等版本）在内核树顶层新增 `agents/` 目录，每个技能是 `agents/skills/<name>/SKILL.md`，用 Agent Skills 格式写成，指向已有的流程文档，并补上 AI 最容易犯错的地方：

- **find-fixes**：确定 bug 修复的 `Fixes:` 标签。先搞清楚 bug 本身（失败表现、触发方式、涉及代码），再沿历史追踪、越过代码移动和重构，把每个候选 commit 和它的父提交对比；合并、revert、backport、比 git 历史还老的 bug 都有各自的处理。**无法确定就不返回标签**，列出候选和缺失的信息。提交的 commit 是它自己不动的。
- **stable-tag**：判断一个修复是否要进 stable、该生成什么标签。依据 `stable-kernel-rules.rst`，找出每个引入 commit 首次出现于哪个 release，检查修复能否应用到最老的受影响 release，并遵循子系统的 stable 策略。它列出了 stable 树实际接受/排除的变更类型（例如「不防止 lockup/stall/hang 的优化」「纯清理如风格、改名、注释」排除）——这些是描述现行规则，不是新规则，主要为小模型省去每次重新推导。
- **find-siblings**：在代码树里找同一个 bug 的其他实例（兄弟驱动、复制的代码、共享接口），有 Coccinelle 时用语义补丁辅助，并逐一验证候选；**只报告，不自动修**。
- **commit-message**：写、改写或审查 commit message 和 cover letter，以及 pull request 文本。遵循改动文件的 `P:` profile，文字要短、用祈使语气——这是 Linus 反复强调的要求，且不凭空发明人类没给的标签。
- **writing-kunit-tests**：Ted Ts'o 贡献（约 344 行），指导编写 KUnit 测试，他自己用它给 ext4 补测试。

## 三、设计原则：只检查与报告，不越界

这套技能有一条硬边界：**它们只 inspect and report**。不改文件、不创建 commit 或标签、不发邮件——调用它们的工作流才负责真正写 commit、打标签、发邮件。唯一例外是任务本身就是写代码或测试（如 KUnit 技能）。

另一条：**不确定就不猜**。fixes 来源无法确定、stable 决策做不出来，就返回"没有标签"并说明缺什么，而不是猜一个。这跟很多"AI 自动生成补丁"的做法正好相反——内核社区要的是**给 AI 划清能力边界**，而不是让它全权代理。

技能大体只指向 `Documentation/`，例外是 stable-tag 里那张"接受/排除"清单。Sasha 承诺每次 release 都会检查 `agents/` 和 `Documentation/` 的一致性，删掉重复或矛盾的内容（这是 Kees Cook 的建议）。工具默认不会自动加载 `agents/skills/`，想让工具自动加载，需要把技能目录软链到工具的 skills 目录。

## 四、评审中的插曲：AI 也会写出有 bug 的 AI 技能

有意思的是，评审过程本身就印证了技能的必要性：Andrew Morton 在 KUnit 技能里发现了一个由 LLM 生成的**参数写反的例子**；Mauro Carvalho Chehab 要求测试指南也覆盖内核的 Python 文档测试（防止 kernel-doc 正则改动悄悄破坏文档构建）。

更尖锐的交锋在 stable 这块。Morton 要求每个修复都用大白话写明"用户遇到这个 bug 时实际会观察到什么"，而且要写在 LLM 会读到的地方。Sasha 同意，并说会把同样的话放进人类的补丁提交指南。他还解释了为什么自动修复工具老是不打 stable 标签——此前规则把"没人能给出真实命中或复现"的 bug 视为理论问题，而机器人大多做不到这一点，即便缺陷明显影响用户；**这条措辞已经被删掉了**。Morton 的回击很妙：「人也不读文档，但至少写下来的规则让我有东西可以指着说，也让下游维护者在盯着一屏生成文本决定要不要 backport 时有依据。」

## 五、怎么定性

把 AI agent 技能收进内核源码树，是一个信号：**AI 辅助开发正在从"个人工具"变成"项目基础设施"**。内核社区没有回避 AI 生成补丁的潮流（Phoronix 同日另一条新闻就是"在 AI 生成补丁和 bug 报告满天飞之际，Linux 又多了位网络维护者"），而是选择把流程写进树里、给模型划边界、要求可验证。

值得注意的是这件事的克制：`Assisted-by: LLM` 标签在 Maintainers Summit 后被去掉；技能不碰 git 操作、不发邮件；标签不确定就留空。这些设计选择——**让 AI 做它擅长的检索和比对，把决定权留给人**——可能比"AI 自动写内核补丁"更有参考价值。

对普通读者：这不会改变你用的内核功能，但它可能会让内核修复的标签更准、回移更全、commit message 更短——这些"苦活"质量的提升，最终会体现在 stable 分支的可靠性上。

## 参考资料

- Phoronix 报道：https://www.phoronix.com/news/Linux-AI-Agent-Skills-Ready
- 补丁系列 cover letter（v3 0/7）：https://lkml.rescloud.iu.edu/2610.2/01808.html
- v5 系列汇总（Patchew）：https://patchew.org/linux/20261111225940.1573565-1-tytso@mit.edu
- It's FOSS 背景解读：https://itsfoss.com/news/linux-ai-agent-skills-directory-proposal/
- freenode 技术报道（含评审细节）：https://freenode.net/article/kernel-developers-draft-ai-skills-for-fixes-tags-and-stable-backports
