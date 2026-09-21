# Linux perf `script` 命令大改：甩掉内嵌 Python/Perl，3.7 秒变 0.1 秒

> 原文：[Linux's Perf Script Command Much Faster With Overhaul As Python Module](https://www.phoronix.com/news/Linux-Perf-Python-Module)（Phoronix，Michael Larabel，2026-09-21）。本文由 LeisureLinux 翻译整理并加注解读；文内事实来自原文。

这周末，Linux 内核 **perf 子系统** 抛出一组大 patch：**移除内嵌的 Python 和 Perl 脚本支持**，改用独立 Python 脚本 + 一个新的 **Python `perf` 模块**。这个用 C 写的 perf 模块，比现状快得多。

## 译文：改了什么

Google 工程师 **Ian Rogers** 主导了这次对 `perf script` 命令的 overhaul，目标是解决它**高开销、构建依赖复杂**、以及其它设计难题——做法是给 Python 造一个正经的 `perf` 模块。有了这个用 C 写的 perf Python 扩展模块，性能提升明显：一个原本要 **3.7 秒**的 Python 脚本，改用独立 Python 脚本 + 新 perf 模块后，**只要 0.1 秒**。

周六发出的这组 **49 个 patch**，把 Python perf 代码迁到新模块，同时**丢掉旧的基于 libpython 的代码和 legacy Python 脚本**。整套 overhaul 约 **2.1 万行代码**，用于改进 Linux perf 的脚本流程。Rogers 这次 overhaul 有 **Gemini 3.1 Pro** 协助。

正在用 Linux perf + Python 脚本的人，可在邮件列表上通过[这组 patch 系列](https://lore.kernel.org/linux-perf-users/cover.1789880842.git.irogers@google.com/)了解这个尚在审查中的根本性变更。

## 解读：不是「又优化了一下」，是架构层面的清洗

**1. 性能数字背后，是「内嵌解释器」这种设计被证伪。**

`perf script` 过去的做法，是把 Python/Perl 解释器**嵌进 perf 二进制**里，让脚本在 perf 进程内跑。代价是：构建要拉 libpython（及其头文件、版本耦合）、perf 二进制变重、每次启动都要初始化解释器运行时——这些固定开销，对一个「只想把 trace 数据过一遍脚本」的任务来说极不划算。这次改成「**独立 Python 进程 + C 扩展 `perf` 模块**」，等于把解释器从 perf 里摘出去，perf 只负责高效地吐数据，Python 侧用 C 扩展直接消费。3.7s → 0.1s（37×）的差距，主要不是算法优化，而是**去掉了每趟都要付的启动/嵌入税**。对工程的通则是：当你发现「调个脚本要 3.7 秒」，先别怪 Python 慢，先看看是不是被宿主进程的初始化成本拖死了。

**2. 2.1 万行、49 个 patch，且「尚在审查」——别急着上生产。**

这是给内核 perf 的改动（lore.kernel.org 上的 patch 系列，处于 review 阶段，未合入主线）。对一线而言，含义很清楚：**现在你的 `perf script` 还是老样子**，这个加速要等它合入某个未来内核、再等发行版把 perf 工具链跟上。但它的方向值得记：perf 这类「性能工具自身也在被性能问题反噬」的场景，正在被系统性收拾——和本批次里「gzip 修祖传 bug」「coreutils 修 -R 竞态」是同一股「老基础工具被认真维护」的潮流。

**3. 「Gemini 3.1 Pro 协助」——和本批次另一条线呼应。**

Rogers 明说这次 overhaul 有 Gemini 3.1 Pro 协助。这跟我们前面译的 Hacktron「AI 写利用」、DeepSeek「AI 黑客模型」形成对照：同一个「AI 辅助工程」的能力，一边被用来**攻**（写利用、打穿），一边被用来**维护基础设施**（重写 2.1 万行内核工具）。工具无善恶，取决于谁在用它补哪一面墙。

一句话收尾：perf `script` 从「内嵌解释器」走向「独立 Python + C 扩展模块」，3.7 秒压到 0.1 秒——这不仅是快了 37 倍，更是把「性能工具自己拖慢自己」这个老毛病，从架构上剜了出去。等它合入主线，你的 trace 后处理就能少等那 3.6 秒。
