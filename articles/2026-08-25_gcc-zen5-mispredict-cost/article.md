# 两行补丁换来 12% 性能：GCC 为 Zen 4 / Zen 5 校准分支预测成本表

> **原文出处**：[GCC Patch Adjusting AMD Zen 5 Misprediction Cost Nets 12% Win In Benchmark](https://www.phoronix.com/news/AMD-Zen-5-Mispredict-Cost) — Michael Larabel, Phoronix, 2026-08-23
> **一手补丁**：[gcc-patches 邮件列表，Venkataramanan Kumar (AMD)，2026-08](https://gcc.gnu.org/pipermail/gcc-patches/2026-August/728535.html)
> 本文为基于原始报道的二次解读，非逐字翻译。

"改两行代码，性能提升 12%。"——这种话放在营销号里多半是标题党，但这次它是真的，而且出自 GCC 编译器本身。

AMD 编译器工程师 Venkataramanan Kumar 最近向 GCC 提交了一个只有两行的补丁，把 Zen 4 和 Zen 5 在 GCC 内部"成本表"里的**分支预测错误成本**上调了 3 个单位。结果在 SPEC CPU 2017 的 `544.nab_r` 基准上，Zen 5 涨了 12%，Zen 4 涨了 9%。

这事儿有意思的地方，不在于"两行代码多神"，而在于它暴露了一个长期被忽视的事实：**编译器对现代 CPU 分支预测代价的估计，早就过时了。**

## 一、编译器里的"成本表"到底是什么？

GCC 在生成代码时，并不是照着 C 代码逐句翻译。它对每一种 CPU 微架构都维护着一张**成本表（cost table）**，里面量化了各类操作的"代价"——加法、乘法、load/store、分支、cmov（条件传送）各值多少 cycles。

为什么需要它？因为同一个语义，编译器可以写成不同的形态。最典型的就是"分支 vs 条件传送"：

```c
// 写法 A：普通分支
if (a > b)
    x = a;
else
    x = b;

// 写法 B：条件传送（无分支）
x = (a > b) ? a : b;   // 通常编译为 cmov
```

写法 A 有分支：如果 CPU 预测错了，流水线要被冲刷（flush），白跑几十个周期。写法 B 用 `cmov`，没有分支，但会**两条路都算一遍**再挑一个结果，增加了一些数据依赖和吞吐量开销。

那么编译器该选哪个？它看成本表：如果"分支预测失败一次的代价"被估得很低，编译器就觉得"赌一把分支也划算"，于是保留分支；如果这张表里分支失败的代价被估得足够高，编译器就会更积极地把分支改写成 `cmov`，从而避免预测失败带来的流水线停顿。

GCC 里这个参数就叫 **分支预测错误成本（branch misprediction cost）**，在 x86 后端用 `COSTS_N_INSNS(n)` 来表示"相当于 n 条指令的代价"。

## 二、那两行代码到底改了什么

补丁的本质，就是把 Zen 4 / Zen 5 成本表里这个参数从 `COSTS_N_INSNS(2)` 抬到 `COSTS_N_INSNS(2) + 3`，也就是上调 3 个单位（约相当于多估了 3 条指令的代价）：

```diff
 // 概念性 diff（Zen 4 / Zen 5 成本表，节选自补丁意图）
-  /* Branch misprediction cost.  */ COSTS_N_INSNS (2)
+  /* Branch misprediction cost.  */ COSTS_N_INSNS (2) + 3
```

> 注：上面是基于补丁说明与 Phoronix 报道还原的"意图性 diff"，精确的变量名、行号与上下文以 GCC 邮件列表里的原始提交为准。

就这么一点改动，编译器在面向 Zen 4 / Zen 5 生成代码时，会**更激进地把分支转换成条件传送**，从而减少因预测失败导致的流水线清空。

## 三、为什么是现在？因为流水线越来越深

分支预测是现代高性能 CPU 的命门。CPU 不能等 `if` 的条件算出来才去取下面的指令——那太慢了。它会在条件就绪之前就"赌"一个方向，提前把指令灌进流水线。赌对了，畅通无阻；赌错了，整条流水线里已经预取、译码、执行的指令全部作废，重新来过。

这个"赌错"的代价，正比于流水线的深度。Zen 4 / Zen 5 的流水线比十年前的 CPU 深得多，一次预测失败的惩罚早已不是 GCC 成本表里那个老旧预设值能代表的。换句话说：**硬件进化了，编译器里的那张表却还停留在老认知**，于是编译器一直过度保留了本该被消除的分支。

这次补丁等于给编译器"提了个醒"：在 Zen 4 / Zen 5 上，分支预测失败的代价比你想的高，所以别再那么爱用分支了。

## 四、12% 从哪来：544.nab_r 是个什么基准

成绩来自 SPEC CPU 2017 的 `544.nab_r`。NAB 是 **Nucleic Acid Builder（核酸构建器）** 的缩写，一个分子建模领域的科学计算程序。它是 SPEC 里出了名的**分支密集、数据依赖复杂**的用例——正好是"分支 vs cmov 权衡"最敏感的那类负载。

测试条件也值得注意：补丁作者在 `-O3 -march=native -flto` 下测得 Zen 5 +12%、Zen 4 +9%。`-march=native` 让编译器针对本机微架构调优（也就是用上这张成本表），`-flto` 做全程序优化，给 if-conversion 这类跨函数变换留足空间。

| 补丁 / 平台 | 基准 | 提升 | 调优方式 |
|---|---|---|---|
| AMD（Venkataramanan Kumar）Zen 5 | 544.nab_r | **+12%** | `-O3 -march=native -flto` |
| AMD Zen 4 | 544.nab_r | **+9%** | 同上 |
| Intel（Lili Cui）Granite Rapids | 544.nab_r | **+12.7%** | 通用 x86 调优 |
| Intel（Lili Cui）Zen 5 | 544.nab_r | **+12.1%** | 通用 x86 调优 |

需要泼盆冷水：这 12% 是**单基准**的成绩。编译器的成本表调优一向是"对着 SPEC 调"，其他负载未必都有这么夸张的增益；但 SPEC 本就是这类调优的事实标准基准，能在一个用例上白捡 12%，已经足够诱人。

## 五、这不是 AMD 独创，Intel 两个月前就干过

有意思的是，这次"上调 3 个单位"的思路并非 AMD 首创。早在 **2026 年 6 月**，Intel 软件工程师 **Lili Cui** 就向 GCC 的**通用 x86 调优**提交了一个一行改动，用了**完全相同**的理由：现代 CPU 流水线更深，分支预测失败更贵，所以把通用成本表里的分支预测成本也上调 3。

那个补丁的战绩是：Granite Rapids **+12.7%**、Zen 5 **+12.1%**（同样在 544.nab_r 上）。而且它是改的**通用 x86/x86-64 调优**——也就是说，哪怕你没开 `-march=native`、只用通用调优，也能吃到这波红利。该补丁已合入 GCC Git，预计随明年的 **GCC 17** 稳定版发布。

> 参考：[GCC's Generic x86 Tuning Change Begins Benefiting Modern Intel & AMD CPUs](https://www.phoronix.com/news/GCC-x86-Generic-Mispredict) — Michael Larabel, Phoronix, 2026-06-24

一个 AMD 工程师、一个 Intel 工程师，分别在 CPU 专用成本表和通用成本表上，用同一种推理拿到了几乎一样的数字。这恰恰说明：**问题不在某家 CPU，而在 GCC 那张成本表本身已经普遍低估了分支预测的代价。**

## 六、真正的故事：编译器调优，永远慢硬件半拍

把两件事放一起看，更有意思的是 Phoronix 在 AMD 那篇里的点评：

> AMD 现在比过去更早地把新 CPU 目标送进 GCC/Clang（Zen 6 去年 12 月就进了 GCC 16），但**成本表调优**这块，仍然是他们可以做得更好的地方——Znver5 和 Znver6 在 GCC 里至今很大程度上还在沿用 Znver4 的成本表信息，各种微调往往要等硬件发布后好几个月才补上。考虑到 GCC 漫长的发布周期，这种时机常常很尴尬。

这戳中了一个行业老问题：**硬件出厂了，编译器还没学会怎么榨干它。** GCC 一年一个大版本，一个成本表的校准从提交到进稳定版、再到被发行版打包默认采用，往往要跨好几个季度。等普通用户用上"正确"的成本表时，这块 CPU 都快退市了。

所以"两行代码换 12%"的爽文背后，是 AMD/Intel 工程师事后补课的身影——而且补的，还是上一个架构（Znver4）留下来的老表。

## 七、作为使用者，现在能做什么

- **直接用 `-march=native`**：这么简单一行，就能让编译器针对你手头的 Zen 4/5 选用正确的成本表与指令集。很多"为什么我的程序没跑满 CPU"的谜题，答案就是忘了开它（当然要权衡可移植性）。
- **等 GCC 17（或 16.3 反向移植）**：Venkataramanan Kumar 的这个补丁目前在邮件列表审核中，若无意外会进明年的 GCC 17 特性版，并可能**反向移植到 GCC 16.3** 小版本。
- **想自己验证？** 可以对比 `gcc -O3 -march=native` 与加了 `-fno-if-conversion` / `-fno-if-conversion2` 的生成代码——后者会抑制分支到 cmov 的变换，你能直接看到"少做了多少 cmov"，以及它对应的性能差异。用 `-O2 -S` 把汇编码导出来，搜 `cmov` 看密度，是理解这件事最直观的方式。
- **别只盯 SPEC**：12% 是 544.nab_r 一个用例。你的真实负载里分支密集、预测困难的热点，才更可能从这波调优里受益。

## 八、结语

一行成本表参数，撬动 12% 的基准成绩。这个故事最迷人的地方，不是"编译器好神"，而是它提醒我们：**现代 CPU 的性能，有很大一部分是被软件"默认配置"白白浪费掉的。** 当 Zen 5 的流水线已经深到分支预测失败的代价远超旧表预设时，只要有人把那个数字从 2 改成 2+3，被埋没的性能就自己浮出来了。

对于爱折腾的人来说，这大概就是自由软件最好玩的地方：机器里藏着多少没被唤醒的算力，往往只差一个你能读、能改、能重编译的补丁。

---

## 参考文献

- Phoronix — [GCC Patch Adjusting AMD Zen 5 Misprediction Cost Nets 12% Win In Benchmark](https://www.phoronix.com/news/AMD-Zen-5-Mispredict-Cost)（Michael Larabel, 2026-08-23）
- GCC 邮件列表 — [Venkataramanan Kumar 的补丁提交（gcc-patches, 2026-08）](https://gcc.gnu.org/pipermail/gcc-patches/2026-August/728535.html)
- Phoronix — [GCC's Generic x86 Tuning Change Begins Benefiting Modern Intel & AMD CPUs](https://www.phoronix.com/news/GCC-x86-Generic-Mispredict)（Michael Larabel, 2026-06-24，Intel Lili Cui 的通用 x86 改动）
- SPEC CPU 2017 — [544.nab_r（Nucleic Acid Builder）基准说明](https://www.spec.org/cpu2017/)（官方基准套件）
- GCC 手册 — [x86 调优选项与 -march / -mtune](https://gcc.gnu.org/onlinedocs/gcc/x86-Options.html)（成本表如何被 `-march`/`-mtune` 选择）
