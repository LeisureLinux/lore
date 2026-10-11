---
title: "SQLite 3.54 终于放弃 Windows XP：一个数据库引擎的兼容性债，还了二十多年"
date: 2026-10-09
slug: sqlite-3-54-released
tags: [SQLite, 嵌入式数据库, Windows XP, SRWL, 性能优化, 查询计划器, O_TMPFILE, 兼容性债, 发布说明, 译文]
category: 系统与软件
author: FreeLAMP.com
original_source: "Phoronix / SQLite 官方发布说明"
original_author: "Michael Larabel（Phoronix）；SQLite 开发团队"
original_date: 2026-10-09
original_url: "https://www.phoronix.com/news/SQLite-3.54-Released"
description: "SQLite 3.54 于 2026-10-09 发布。最大的标志性变化是终于放弃 Windows XP 及更早版本（含 Windows CE），最低要求提高到 Windows Vista。这个技术债一还，Windows 上就能改用 Slim Reader/Writer Locks 替代 CriticalSection 来实现非递归互斥锁，顺带提速。官方基准显示 Linux x64 上比上一版快约 4%，比一年前的 3.51 快约 7.5%。其余变化包括 CLI 提示符增强、新增 --ifmt/--fpfmt 格式化选项、查询计划器改进（含 OR TRUE/FALSE 优化、忽略 IN 右侧的 DISTINCT）、以及在支持的系统上用 O_TMPFILE 生成临时文件。"
published: true
---

> 原文：[SQLite 3.54 Released With Faster Performance, Drops Windows XP Support](https://www.phoronix.com/news/SQLite-3.54-Released)（Phoronix，2026-10-09，作者 Michael Larabel）
> 官方发布说明：[SQLite Release 3.54.0](https://sqlite.org/releaselog/3_54_0.html)（**发布于 2026-10-09**）
> 本文为**译文 + 解读**。第三节的性能数字读法、第四节关于兼容性债的分析是笔者补充的部分。

## 一句话结论

**SQLite 3.54 于 2026 年 10 月 9 日发布**，标志性变化是**终于放弃 Windows XP 及更早版本（包括 Windows CE），最低要求提高到 Windows Vista**。**而这个「放弃」不只是清理列表，它直接换来了一次性能提升**：在 Windows 上可以**用 Slim Reader/Writer Locks（SRWL）替代 CriticalSection 来实现非递归互斥锁**。官方基准显示 **Linux x64 上比上一版快约 4%，比一年前的 3.51 快约 7.5%**。同版本还有一批 CLI 增强、查询计划器改进，以及在支持的系统上用 `O_TMPFILE` 生成临时文件。

## 一、先看这个「终于」

原文用了一个很准确的词：

> **SQLite 3.54 终于不再支持 Windows XP。** Windows XP 及更早的 Windows 版本（包括 Windows CE）不再受支持。**Windows Vista 及更新版本仍然维护。**

**为什么值得单独说这件事**：Windows XP 的**主流支持在 2009 年结束、扩展支持在 2014 年 4 月结束**。也就是说，**这个数据库引擎为一个已经停止获得安全更新的操作系统，保留了十多年的兼容代码路径**。

**这十多年里，代价是什么**：SQLite 在 Windows 上的互斥锁实现必须兼顾 XP 时代没有的那批 API，**只能退而使用 `CriticalSection`**。而一旦把最低版本提到 Vista，**就能用 `SRWL`**（Slim Reader/Writer Locks，**Vista 引入**，读写锁，比 CriticalSection 更轻量、更适合读多写少的场景）。**官方明确把这条列为性能改进的原因**（发布说明第 2 条）。

**我认为这是这个版本最值得记录的一点**：**「放弃旧平台」和「性能提升」在这里不是两件事，而是同一件事的因果两端。** 保留兼容性的成本不只是「多写几个分支」，而是**你被迫使用一套更笨的底层机制**。

## 二、性能数字怎么读

官方和 Phoronix 给的数字需要分两层看：

| 对比 | 提升幅度 | 场景 |
|---|---|---|
| 相对上一版 | 约 **4%** | 官方 Speedtest 基准，**Linux x64** |
| 相对 3.51（一年前） | 约 **7.5%** | 同上 |

**两个必须注意的限定**：

- **这是 SQLite 自己的基准**（Speedtest performance benchmark），**在自己的测试集上测自己**。这个数字适合用来对比版本间的相对变化，不适合外推到你的应用；
- **这是在 Linux x64 上测的**，而这一版最重要的 Windows 改动（SRWL 替代 CriticalSection）**在这组数据里反映不出来**。也就是说，**Windows 用户可能拿到比 4% 更明显的收益，而这部分没有被宣传数字覆盖**。

**还有一条我认为最该被强调的**（它来自对这类发布的常见误读）：

> **这不意味着每个使用 SQLite 的应用都会相应地变快；结果取决于它如何使用数据库。**

**这句话是这里最诚实的一句。** SQLite 是嵌入式的，**它的性能表现高度依赖调用方的使用模式**：事务边界怎么划、是否用索引、批量插入还是逐条、连接是复用还是频繁开关。**「引擎快了 4%」在你的应用里可能被完全淹没，也可能被放大。** 唯一可靠的判断方式是**拿你自己的负载测**。

## 三、其余变化：CLI 与查询计划器

### CLI 明显被加强了

这一版在命令行工具上花了不少功夫，值得列一下：

| 变化 | 内容 |
|---|---|
| **列名表头** | **columnar 输出模式下默认显示列名表头，即使查询没有返回任何行** |
| **`.mode --ifmt / --fpfmt`** | 新增选项，**可用 printf 风格的格式串精确控制整数与浮点数的渲染** |
| **`.mode --rowcount on`** | 新增行数显示控制 |
| **`.mode --titles always`** | 成为默认行为（旧行为可用 `-titles on` 恢复） |
| **`.diskused` 点命令** | 用新的 `diskused()` 扩展实现，**取代独立的 `sqlite3_analyzer` 工具（现已弃用）** |
| **提示符增强** | **提示符串可含转义序列**，展开后显示状态信息；初始提示符会读取 **`SQLITE_PS1` / `SQLITE_PS2` 环境变量** |
| **NO_COLOR** | **默认 CLI 提示符遵循 `NO_COLOR` 环境变量** |
| **`-csv`** | **自动禁用显示限制**（为兼容旧行为） |
| **Unix 上保留零字节** | 输出未格式化的 BLOB 值时**保留零字节** |

**其中我认为最实用的是两条**：

**① 空结果也显示列名。** 这是个很小但每天都会碰到的问题：脚本化查询时，如果没有返回行就只有表头缺失，下游解析逻辑要单独处理空结果。**现在默认就有一致的表头了。**

**② `sqlite3_analyzer` 被 `.diskused` 取代。** 这是个**工具合并**：过去要分析数据库空间占用，得单独跑一个程序；现在变成 CLI 里一个点命令。**对运维来说是少装一个东西。**

### 查询计划器与其他

- **`expr OR TRUE` 与 `expr OR FALSE` 的优化改进**；
- **忽略 `IN` 运算符右侧 SELECT 语句里的 `DISTINCT`**（因为它不影响 `IN` 的语义）；
- **`LIMIT` 恰为 1 的 UNION 查询处理更快、内存更少**；
- **对带表达式索引的表做 UPDATE 时，如果被索引的值没变，就不动那个索引**（避免无谓的写放大）；
- **在支持的系统上用 `O_TMPFILE` 生成临时文件**（避免在文件系统里留下可见的临时文件名，也是我们之前那篇 swap/zram 讨论里出现过的同类机制）；
- **日期时间函数增强**：新增 `weekday -N` 形式的 weekday 修饰符，以及 **`end of` 修饰符**；
- **新增 `sqlite3_result_str()`、`sqlite3_incomplete()` 接口**；
- **新增 `SQLITE_LIMIT_SCHEMA` 与 `SQLITE_LIMIT_TRIGGER_STEPS` 到 `sqlite3_limit()`**；
- **printf / `format()` 新增 `%J` 与 `%j` 转换**，用于渲染 JSON 字符串字面量。

**⚠️ 一处潜在不兼容**（发布说明自己标了）：

> **`ALTER TABLE` 命令不再允许添加、删除或重命名名为 `"ROWID"`、`"_ROWID_"` 或 `"OID"` 的列。**

**这条值得单独记**，因为它是这一版唯一被标为「Potential Incompatibility」的项。如果你的迁移脚本里碰过这些名字（它们是与 SQLite 内部行标识相关的特殊名字），**升级前需要检查**。

## 四、我更想聊的：兼容性债的计价方式

这个版本真正让我想写一篇的原因，不是那 4%，而是它展示了一个**很少被明确讨论的问题：保留旧平台支持的成本，究竟是怎么算的**。

**常见的算法是这样的**：「还有 X% 的用户在用 Windows XP，所以我们要继续支持。」**这个算法本身没错，但它漏掉了一项**：

**保留支持的代价不会平均分布在代码里，而是集中在最底层、最核心的那几个机制上。** 在 SQLite 这个例子里，代价是**整个 Windows 平台的互斥锁实现必须停留在 `CriticalSection`**，而这个机制会被**每一次需要加锁的操作**走到。

**于是「为了 0.1% 的用户保留 XP 支持」这句话的完整版本应该是**：**为了这部分用户，所有 Windows 用户的每一次加锁操作都在用一套更笨的机制。** 这个代价是**持续的、全量的、且不可见的**（因为没有 bug，只是慢）。

**我认为这正是「兼容性债」和普通「技术债」的区别**：普通技术债是可以局部偿还的（改这一个模块），而**兼容性债会渗透到最底层的公共路径上**，并且随着时间推移，**它约束的不再只是「代码能不能跑」，而是「你能用哪些现代的底层能力」**。

**从这个角度看，SQLite 这次的决定做得很干净**：它没有采用「保留一个编译期开关供 XP 用户使用」这种折中（那意味着两条互斥锁路径都要维护和测试），而是**直接切断了最小版本**，并明确说「Vista 及更新版本仍然维护」。**这个切法让收益立刻兑现**（SRWL 到位）。

**一个有意思的对照**：我们前几天写过的两件事，恰好是同一个模式的不同版本：**ext4 弃用 `data=journal`**（因为 SSD 时代「写两遍」的代价变得不划算）、**Ubuntu 26.10 把签名版 GRUB 里的 Btrfs/XFS/ZFS 驱动整个移除**（并特意安排在 LTS 之后做，给需要的人留退路）。**三件事的共同点是：技术在某个时间点会明确划一条线，说「从这里往前的世界，我们不再为它付钱」。** 而**这条线划得越晚，代价越高**，因为它牵动的底层机制会越来越多。

**所以我对这类「终于放弃 X」的新闻，判断标准很简单**：**看它换来了什么具体的能力或性能，而不是看它放弃了什么。** SQLite 这次换来的是 SRWL（以及配套的 Windows 性能改进），**这是一个可以验证的、立刻兑现的收益**，而不是一句「代码更干净了」。**这个标准可以套用到所有类似的「清理旧支持」的发布上。**

## 五、给使用者的实际建议

**如果你在用 SQLite**：

- **升级的门槛很低**：SQLite 的升级就是换一个 amalgamation 文件或链接库，**没有迁移过程**，向后兼容性一直是它的强项（这一版唯一的 incompatibility 是 `ALTER TABLE` 那几个特殊列名）；
- **但别期待立刻变快 4%**。**先确认你的瓶颈是不是引擎本身**：如果慢在「每条 INSERT 都开一个事务」，那引擎快 4% 帮不了你；
- **Windows 用户值得单独测**：这一版的 SRWL 改动**只影响 Windows**，而官方基准是 Linux x64，**所以 Windows 上的收益没被数字体现**；
- **关注 CLI 的两处变化**：空结果也显示列名、`.diskused` 取代 `sqlite3_analyzer`。**如果你的脚本依赖旧的空结果行为或调用 `sqlite3_analyzer`，需要调整**。

**如果你在评估「要不要继续支持某个老旧平台」**（这是这篇文章真正想留下的思考）：

1. **不要只统计用户占比**，先问「支持它的代价落在哪一层」；
2. **如果代价落在公共热路径上**（锁、内存分配、I/O、编码转换），**这个代价是持续的、全量的**；
3. **优先选择切断最小版本，而不是保留编译期开关**。开关看起来温和，实际上让两条路径都要长期维护与测试；
4. **给切换留一个时间窗，并明确说出来**（Ubuntu 的做法是「我们在 LTS 之后动，需要的人可以留在 LTS 到 2041 年」）；**同时把换来的收益讲清楚**。

## 关键事实速查

| 项目 | 内容 |
|---|---|
| 发布 | **SQLite 3.54.0，2026-10-09** |
| ⚠️ 标志性变化 | **放弃 Windows XP 及更早版本（含 Windows CE）**，最低要求 **Windows Vista** |
| 因此换来的能力 | Windows 上**用 Slim Reader/Writer Locks（SRWL）替代 `CriticalSection`** 实现非递归互斥锁 |
| 性能（官方基准） | 比上一版快约 **4%**；比一年前的 **3.51 快约 7.5%**（**均为 Linux x64**） |
| ⚠️ 数字的限定 | 这是 **SQLite 自己的 Speedtest 基准**；**Windows 的 SRWL 收益不在这组数据里** |
| ⚠️ 对应用的影响 | 官方明说：**不意味着每个使用 SQLite 的应用都会相应地变快**，取决于使用方式 |
| ⚠️ 潜在不兼容 | **`ALTER TABLE` 不再允许添加/删除/重命名名为 `ROWID`、`_ROWID_`、`OID` 的列** |
| CLI：表头 | **columnar 模式下默认显示列名表头，即使没有返回任何行** |
| CLI：格式化 | 新增 **`--ifmt` / `--fpfmt`**（printf 风格格式串控制整数与浮点渲染） |
| CLI：提示符 | 提示符支持**状态信息转义序列**；读取 **`SQLITE_PS1` / `SQLITE_PS2`**；遵循 **`NO_COLOR`** |
| CLI：工具合并 | **`.diskused` 点命令取代 `sqlite3_analyzer`**（该工具已弃用） |
| CLI：其他 | `--rowcount on`；`--titles always` 成为默认；`-csv` 自动禁用显示限制；Unix 上未格式化 BLOB **保留零字节** |
| 查询计划器 | 优化 **`expr OR TRUE` / `expr OR FALSE`**；**忽略 `IN` 右侧的 `DISTINCT`**；**`LIMIT` 为 1 的 UNION 更快更省内存** |
| 表达式索引 | 对带表达式索引的表做 UPDATE 时，**若被索引的值未变则不动该索引** |
| 临时文件 | 在支持的系统上使用 **`O_TMPFILE`** |
| 日期时间 | 新增 **`weekday -N`** 形式与 **`end of`** 修饰符 |
| 新增接口 | `sqlite3_result_str()`、`sqlite3_incomplete()`；`sqlite3_limit()` 增加 `SQLITE_LIMIT_SCHEMA`、`SQLITE_LIMIT_TRIGGER_STEPS` |
| printf | 新增 **`%J` / `%j`** 转换，用于渲染 JSON 字符串字面量 |

## 延伸阅读

- [Phoronix：SQLite 3.54 Released With Faster Performance, Drops Windows XP Support](https://www.phoronix.com/news/SQLite-3.54-Released)
- [SQLite 官方发布说明 3.54.0](https://sqlite.org/releaselog/3_54_0.html)
- [本站：ext4 弃用 data=journal：最「安全」的那个挂载模式，2028 年要走了](/articles/2026-10-09_ext4-deprecates-data-journal/)
- [本站：Ubuntu 26.10 的安全清单：GRUB 瘦身、coreutils 全 Rust、OpenSSL 4.0 与 upki 吊销检查](/articles/2026-10-08_ubuntu-26-10-security/)
- [本站：Linux swap 子系统要删掉那张「交换映射表」：省下的是 1TB 交换文件里的 256MB](/articles/2026-10-09_linux-swap-table-removing-swap-map/)
