# Linux 7.3 NFS 改进：客户端 / 服务端双向发力——服务端目录委派、客户端 I/O 优化、NFSv4.2 缓存控制

> **原始出处**：Phoronix + LKML NFS client + NFSD pull requests
> **发布日期**：2026 年 8 月 26 日（合并窗口接近结束）
> **作者**：Trond Myklebust（NFS 客户端维护者，Hammerspace）、Chuck Lever（NFSD 维护者）
> **关键 PR**：
>   - 客户端：[GIT PULL] Please pull NFS client fixes for Linux 7.3（Trond Myklebust）
>   - 服务端：[GIT PULL NFSD updates for v7.3]（Chuck Lever）
> **Phoronix 报道**：https://www.phoronix.com/news/Linux-7.3-NFS
> **翻译/解读**：LeisureLinux
> **关键词**：Linux 7.3 NFS、CB_NOTIFY、目录委派、NFSv4.2 缓存控制、pernode 线程池、flexfiles 数据服务器

## 引言：服务端为主，客户端为辅

Linux 7.3 合并窗口接近关闭，NFS 客户端与服务端的 pull request 都已合入。这次的特点是**两端各干各的，没有统一主题**：

- **服务端（NFSD）**这一波最重磅：支持 NFSv4.1 **目录委派**（CB_NOTIFY 回调 + FSNOTIFY），同时把传统服务线程池换成 **per-node 模型**。
- **客户端（NFS）**这一波以 bug fix 为主，亮点是 **NFS/localio 的 I/O 提交优化**与 **NFSv4.2 新增"禁止客户端缓存"语义**。

服务端侧重"新功能 + 性能优化"，客户端侧重"稳定性 + 一处可见的性能提升"。两端加起来**约 200+ 文件改动、6000+ 新增 / 1700+ 删除**——服务端更重，客户端更轻。

---

## 一、整体改动规模

| 维度 | 客户端 (NFS) | 服务端 (NFSD) |
|------|-------------|--------------|
| **维护者** | Trond Myklebust | Chuck Lever |
| **commit 数** | 约 100+ | 约 300+ |
| **核心主题** | bug fix + I/O 优化 | CB_NOTIFY + pernode + netlink 统计 |
| **新功能** | NFSv4.2 缓存控制、NFS/localio I/O 优化 | NFSv4.1 目录委派、pernode 线程模型、netlink stats |
| **新协议文档** | nfs4_1.x | nfsd.yaml + nfs4_1.x |

---

## 二、服务端：CB_NOTIFY + 目录委派

### 2.1 背景

NFSv4.1 引入的"委派"（delegation）让服务端把文件 / 目录的操作授权给客户端独占访问，避免所有操作都回服务端。NFSv4.0/4.1 支持**文件委派**，但**目录委派**一直缺位——服务端没法高效感知"目录里有谁加了 / 删了 / 改名"。

这次补齐的关键是 **CB_NOTIFY** 回调（RFC 8881bis 草案里的扩展）：

- 服务端用内核的 **FSNOTIFY** 机制监控目录。
- 当目录被修改（添加 / 删除 / 重命名 / 属性变更）时，服务端立即回调客户端，让客户端取消之前持有的目录委派。

效果：客户端拿到的目录视图始终和服务端真实状态一致，避免缓存过期。

### 2.2 实现细节

服务端这次的改动横跨 fsnotify 标记、回调编码、通知处理等多个层面：

- `nfsd: allow nfsd to get a dir lease with an ignore mask` — 给目录租赁加忽略位。
- `nfsd: update the fsnotify mark when setting or removing a dir delegation` — fsnotify 标记同步。
- `nfsd: add callback encoding and decoding linkages for CB_NOTIFY` — 回调编解码。
- `nfsd: add notification handlers for dir events` — 事件处理。
- `nfsd: apply the notify mask to the delegation when requested` — 通知掩码应用。
- `nfsd: send basic file attributes in CB_NOTIFY` — 回传属性。

### 2.3 其他服务端改动

服务端这一波远不止 CB_NOTIFY。Chuck Lever 拉了一批改动：

- **pernode 线程池取代传统服务线程池**：内核开发者认为 per-node 模式更适合现代多 socket、多节点主机的 NFS 工作负载。
- **新增 `sunrpc: route to a populated pool in svc_pool_for_cpu()`** — 保证 auto-distribute 时每个 pool 有至少一个线程。
- **NFSv4 回调操作按 netns 计数**：`nfsd: count NFSv4 callback operations per netns` + 通过 netlink 暴露。
- **NFSv4 异步 COPY 改造**：`nfsd: split nfsd4_copy into transient and durable async copy objects`，把 copy offload stateid 提升为一等公民（first-class nfs4_stid）。
- **多批 bug fix**：包含 UAF、stale stateid、copy-notify 状态校验、xattr 派生错误处理等。

### 2.4 lockd 修复

服务端还附了一批 lockd（NFS 文件锁服务）的修复：

- Michael Bommarito：nlm_inspect_file 跨 nfsd_ssc_lock 释放的 walk 重启。
- NeilBrown：`nfsd4_create_file()` 的 fh_compose 错 dentry 修复、`nfsd_file_do_acquire()` 不使用未打开文件。
- Nikol Kuklev：`nfsd4_setattr` 委派时间戳属性的 NULL deref 修复。
- Olga Kornievskaia：**NLMv4 GRANTED_MSG** 处理修复。
- Oscar Ou：nlmsvc_match_ip() 互换参数修复、保留同一 owner 的多个 NLM_SHARE grants。
- Robbie Ko：NFSv2/3 SETATTR/CREATE 时间字段越界拒绝；统一 NSEC_PER_SEC 使用。
- Scott Mayhew：write_threads() 错误返回值修正。
- Zhenghang Xiao：委派释放时设 SC_STATUS_FREED。

---

## 三、客户端：I/O 优化 + NFSv4.2 缓存控制

### 3.1 NFS/localio I/O 提交优化

NFS/localio 是 6.12 起支持的优化路径——客户端和服务端在同一台机器时绕开网络栈直读本地页缓存。Linux 7.3 这次优化集中在**内存非压力路径下的 I/O 提交**：

```plaintext
"optimise I/O submission when not doing memory reclaim"
```

也就是说，常规路径下 I/O 提交更快。这对**本地 NFS 部署 + 大量小 I/O 场景**（如容器镜像分发、CI artifact 缓存）有直接收益。

同时移除 `nfs_local_commit` 里的重复 wait 代码（`NFS/localio: Remove duplicate wait code`）。

### 3.2 NFSv4.2 缓存控制

新加服务端指示：让服务端主动告知客户端"这部分文件数据**不允许**客户端缓存"。对应的客户端支持：

```plaintext
"NFSv4.2: Allow the server to specify that file data may not be cached"
```

服务端管理员可以更精细地控制**强一致性敏感**的文件，避免缓存造成的过期数据问题。对**数据库文件、实时生成的报告**这种场景有意义。

### 3.3 一批 bug fix

Trond Myklebust 拉的客户端修复，按主题分：

**Stable fixes**：
- SunRPC client code use-after-free 修复
- NFSv4 委派哈希表泄漏
- lockd lockowner 分配失败的 NULL deref
- SunRPC TLS 握手完成竞态
- NFSv4.1/pNFS layout 仍使用判断错误符号检查
- NFSv4.1 pnfs_layout_process() layout segment 泄漏

**其他修复**：
- SunRPC：rpcbind client NULL 检查、共享 socket 回调加 `READ_ONCE/WRITE_ONCE` 注解
- NFSv4：`nfs_inode_set_delegation()` 错误路径应返回 delegation
- NFSv4：使用 `clear_and_wake_up_bit()` 替代手工逻辑
- NFSv4：`nfs4_alloc_client()` 错误路径释放 IDR 分配
- NFS：`nfs_inode_remove_request()` 在 NULL 检查前的 folio 解引用修复
- NFS：延迟委派返回修复
- NFSv4：与 umount 竞态的状态管理器修复
- pNFS/blocklayout：parse failure 上的设备泄漏
- pNFS：在 layout recall 时若服务端不要求，避免取消 in-flight I/O
- NFSv4/flexfiles：报告取消的 I/O 为 layout error
- NFSv4/flexfiles：NFSv4.0 数据服务器的 NULL deref 修复
- NFSv4：`nfs4_delete_lease()` 错误参数修复
- NFSv3：`nfs_atomic_open_v23()` 几个 symlink 问题修复
- NFSv4.1：回调代码未初始化变量修复
- NFSv4.2：LAYOUTSTATS send buffer exhaustion 修复

**功能与清理**：
- NFSv4.2：服务端指示文件数据不可缓存
- NFS/localio：I/O 提交优化
- NFS/localio：移除 `nfs_local_commit` 重复 wait 代码
- NFSv4/flexfiles：支持 loosely coupled NFSv4.x 数据服务器
- NFSv4/pnfs：数据服务器缓存按 NFS 版本键控

---

## 四、对 Linux 7.3 NFS 的整体评价

### 4.1 服务端是大头

Linux 7.3 的 NFSD 改动**远大于客户端**：

- **目录委派**补齐 NFSv4.1 的设计意图（文件委派 + 目录委派 = 一致的客户端缓存视图）。
- **pernode 线程模型**让 NFS 服务在 NUMA-aware 主机上跑得更高效。
- **netlink 统计暴露**让 Prometheus 监控 NFS 服务状态成为可能（之前只能用 `/proc/net/rpc/nfsd`）。

### 4.2 客户端以稳定为主

客户端的"大特性"是 NFSv4.2 缓存控制，但这是**协议层语义**的扩展，客户端实现简单。剩下都是 bug fix——但每一个都对生产环境重要（NFSv4 委派泄漏、pNFS layout segment 泄漏、copy offload 状态校验等都是运维会撞到的问题）。

### 4.3 实战影响

| 场景 | 服务端 7.3 影响 | 客户端 7.3 影响 |
|------|----------------|----------------|
| **本地 NFS（容器 / VM）** | pernode 线程模型更友好 | NFS/localio I/O 提交优化 |
| **网络 NFS（共享存储）** | 目录委派改善客户端缓存一致性 | 一批稳定性修复 |
| **数据库场景（NFSv4.2）** | 服务端可发"禁止缓存" | 客户端支持新语义 |
| **多客户端高并发** | pernode 模型减少锁竞争 | flexfiles 数据服务器版本键控 |
| **异步 COPY 链路** | first-class stateid | LAYOUTSTATS buffer 修复 |

---

## 五、Trond 给 Linus 的 commit message 风波

这次客户端 pull 在邮件列表里还有个小插曲——Trond 的 commit message 写得过于简洁，Linus 吐槽：

> "For example, just to look at that first bullet point: why have that 'SunRPC:' thing at all? It adds no value. This is a NFS client merge message, and the line goes on to say 'fixes for the sunrpc client code'."

> "Please don't make me do that. Give me that overview of what happened and what matters. And it's ok to say 'And misc fixes' for things that really doesn't matter and people who care should just look at the individual commits."

Linus 自己做了点编辑才合并。维护者风格的差异在这里挺有意思——Linux 内核合并窗口对 commit message 质量有要求。

---

## 六、关注下一个版本

Linux 7.3 NFS 这波落地后，下一步看点：

- **目录委派（CB_NOTIFY）**在生产环境的实际一致性效果——是否能减少客户端的缓存过期问题。
- **pernode 线程模型**是否需要进一步调优（不同 NUMA 拓扑下的表现）。
- **netlink stats**能否在监控体系里铺开（Prometheus exporter、Netdata 插件等）。
- **flexfiles loosely coupled 数据服务器**——这是 pNFS 灵活性提升的重要一步，后续版本会有更多场景适配。

---

## 七、对运维的影响

### 7.1 服务端升级

- **NFS 服务端升级到 7.3 后**，会自动启用 pernode 线程模型，无需配置。
- **目录委派**默认开启（前提是 NFSv4.1+）。
- **监控集成**：如果有 Prometheus NFS exporter，建议升级到支持 netlink stats 的版本。

### 7.2 客户端升级

- **NFS 客户端升级到 7.3 后**立即拿到所有稳定性修复（特别推荐有 pNFS / NFSv4 委派 / 异步 COPY 场景的环境升级）。
- **NFS/localio 优化**对容器 / VM 镜像分发场景有可见收益。
- **NFSv4.2 缓存控制**需要服务端 + 客户端都升级到 7.3 才生效。

### 7.3 测试建议

```bash
# 服务端：观察目录委派是否生效
cat /proc/fs/nfsd/threads
nfsstat -s

# 客户端：观察 NFS/localio 路径
cat /sys/fs/nfs/localio
cat /proc/mounts | grep nfs

# 监控 netlink 暴露的 NFSv4 回调统计（如果工具支持）
nfsd-client-event  # nfs-ganesha 或第三方工具
```

---

**参考资料**：

1. Phoronix Linux 7.3 NFS：https://www.phoronix.com/news/Linux-7.3-NFS
2. LKML NFS client pull：[GIT PULL] Please pull NFS client fixes for Linux 7.3
3. LKML NFSD pull：[GIT PULL NFSD updates for v7.3]
4. pbxscience 解读：Linux 7.3 Merges NFS Improvements
5. Linux 7.3 源码：https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git
6. Linux NFS 客户端仓库：git://git.linux-nfs.org/projects/trondmy/linux-nfs.git

---

*本文基于 Phoronix 报道、LKML NFS client + NFSD pull request 与社区资料整理，旨在为中国开发者提供快速理解和参考。*

*作者观点不代表任何厂商立场，仅供技术讨论参考。NFS 7.3 服务端与客户端改动规模差异较大，性能数据依工作负载与硬件配置可能有所差异。*