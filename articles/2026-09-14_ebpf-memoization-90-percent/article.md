# 把 eBPF 安全代理的内核 CPU 开销砍掉 90%：靠的是记忆化，不是 AI

> 原文：[Dropping eBPF CPU Cost by About 90% With Memoization (Not AI Gen)](https://nathannaveen.dev/posts/dropping-ebpf-cpu-cost-by-90/)（nathan naveen，2026-09-11）。本文由 LeisureLinux 翻译整理并加注解读；所有代码、数字与结论均来自原博客，已对照其开源仓库 [bomfather/agent](https://github.com/bomfather/agent) 核对。

作者和他弟弟花了很多精力，从底层把他们的 eBPF 安全代理设计得很快；但最近他们发现，靠**记忆化（memoization，缓存）**还能再快一大截。几周前他 profiling 后发现：最贵的部分根本不是"执行策略（allow/deny）"，而是"搞清楚某个文件打开该套用哪条策略"。

他们的策略是基于路径的，所以 eBPF 挂了一个**在文件打开时触发的 LSM hook**：重建路径、沿父目录 dentry 向上走，逐层判断文件或任一祖先目录是否命中策略。这能工作，但性能不行——对已经见过的文件，大量工作是重复做的（比如数据库反复访问同一批路径）。于是他们给**每个 inode 缓存"该套用哪条策略"**，内核 CPU 开销直接降了约 90%。顺带，这篇涉及的实现已开源在 `bomfather/agent`。

---

## 译文：博客要点

### 问题：慢路径

加缓存之前，每次文件打开都要走完整条路径：

1. 拿到文件路径
2. 用 dentry 沿路径向上走
3. 每一层检查该路径是否有策略
4. 合并结果得到最终策略，再决定放行/拒绝

逻辑没问题，但同一个文件被多次打开、或同一子树里多个文件被打开时，每一步都得重做。例如 Postgres 策略只让 `postgres` 访问 `/var/lib/postgres`：

```yaml
policies:
  - executable: "filepath = /usr/lib/postgresql/16/bin/postgres"
    can_access_dirs:
      - "/var/lib/postgres:read"
```

当 Postgres 去读 `var/lib/postgres/data/base/123`、`.../234`、`.../345` 时，三次访问都要把整条 dentry 路径走一遍——非常低效。下文把这条低效路径遍历称为"慢路径"。

### 缓存里有什么

方案是用一个缓存。但要保证它不重、且缓存项可安全复用。他们本来想用 dentry，但 dentry 是指针，而**指针存不进 eBPF map**；若硬要用，得把 dentry 内容塞进一个 struct 当 map key，那样 struct 会很笨重。于是改用**基于 inode 的缓存**，key 由三个字段组成：mount namespace ID、mount ID、inode 号。

- 不能只缓存 inode：inode 号只在某个 mount 树内唯一（策略跨多个 mount 树时可能撞号），mount ID 用来标识"我们从哪棵挂载树看到的这个文件"。
- mount namespace ID 则避免把缓存项用错命名空间。

缓存 value 两部分：`access_index`（策略的位掩码位置，为省空间策略存成 bitmask）和缓存状态。相关结构与 map 定义大致如下：

```c
#define INODE_POLICY_CACHE_NO_POLICY 0
#define INODE_POLICY_CACHE_ACCESS_INDEX 1
#define INODE_POLICY_CACHE_GLOBAL_READ_ONLY 2
#define INODE_POLICY_CACHE_ACCESS_INDEX_AND_GLOBAL_RO 3

struct inode_cache_key {
    u64 mntns_id;
    u64 mount_id;
    u64 inode;
};

struct inode_policy_cache_value {
    u32 access_index;
    u8 state;
};

struct {
    __uint(type, BPF_MAP_TYPE_LRU_HASH);
    __uint(max_entries, 10000);
    __type(key, struct inode_cache_key);
    __type(value, struct inode_policy_cache_value);
} bomfather_inode_policy_cache SEC(".maps");
```

有了缓存后流程变成：

1. 构造缓存 key
2. 在 LRU hash map 里查
3. 命中 → 直接按缓存结果放行/拒绝
4. 未命中 → 走慢路径，把结果写回缓存

命中时，文件打开只要构造 inode 缓存 key 就直达 allow/deny；未命中才走父 dentry、合并策略、存结果。

### 性能变化

基准测试里，他们把**同一个文件打开 200,000 次**：缓存把内核 cycle 从 **280 亿降到 30.3 亿**。无缓存时，`tail_call_security_check` 在栈上占 89.2%、`is_restricted_filepath` 81.9%、`path_check_callback` 63.7%；加缓存后，`is_restricted_filepath` 和 `path_check_callback` 各自缩到约 **0.02%**，在火焰图里基本消失。他们用 `perf` 的 `cycles:k` 事件测量文件打开时的内核侧 CPU 开销。

### 边界情况

一个必须处理的点：**多个路径能共享同一个 inode**——硬链接最典型。两个不同的路径指向同一 inode，这是个大问题，因为"结果准确"比"缓存命中率"更重要。他们的解法更像 workaround：inode 有链接计数 `i_nlink` 表明有多少路径指向它，读到大于 1 就**不缓存这条、回退慢路径**：

```c
if (BPF_CORE_READ_INTO(&nlink, inode, i_nlink)) {
    return false;
}

if (nlink != 1) {
    inode_cache_stats_inc(INODE_CACHE_STATS_SKIPS_NLINK);
    return false;
}
```

这是个权衡——牺牲了部分缓存覆盖率，但作者认为值得，因为"准确的缓存"最重要。

---

## 解读：三个能直接抄的工程经验

**1. eBPF map 里不能存指针，这是所有内核侧缓存的第一道坎。**
作者踩的坑很典型：dentry 是指针，BPF_MAP 的 key/value 必须是值类型（确定的、可比较的固定大小 struct）。所以正解不是缓存"对象"，而是缓存"对象的稳定身份"——由 mntns_id + mount_id + inode 三者构成的 key。这跟用户态用对象引用当缓存 key 的思路完全不同，是内核侧编程的基本功。

**2. 命中率不是唯一指标，正确性优先。**
硬链接导致"同 inode 多路径"时，他们选择 `i_nlink != 1` 就放弃缓存。这等于承认：宁可慢一点，也不能给错误的放行/拒绝决定。对安全代理而言，缓存回退到慢路径只是性能问题，缓存给出错误策略就是安全问题。这个取舍值得所有"给安全机制加缓存"的人记牢。

**3. 90% 的降幅来自"消除重复遍历"，不是来自"算法更聪明"。**
核心改动只是"为见过的 inode 记住结论"，瓶颈就出在反复走 dentry 树。这也呼应了我们上一篇讲过的 coreutils 话题——很多性能问题不在单条指令，而在"被不必要地重复做的工作"。LRU_HASH（上限 10000 条）保证了内存占用有界，是内核里做这种缓存的标准做法。

---

## 关键数字速查

| 指标 | 数值 |
|------|------|
| 内核 CPU 降幅 | 约 90% |
| 基准 | 同一文件打开 200,000 次 |
| 内核 cycle | 280 亿 → 30.3 亿 |
| 热点函数（无缓存） | `tail_call_security_check` 89.2% / `is_restricted_filepath` 81.9% / `path_check_callback` 63.7% |
| 热点函数（有缓存） | 后两者各约 0.02% |
| 缓存类型 | `BPF_MAP_TYPE_LRU_HASH`，max_entries 10000 |
| 缓存 key | mntns_id + mount_id + inode |
| 测量方式 | `perf` 的 `cycles:k` 事件 |

---

> 给安全代理加缓存时，"准确"永远排在"快"前面。你如果在 eBPF 里做过类似的 inode/路径缓存，是怎么处理硬链接和 mount 命名空间边界的？欢迎留言。
