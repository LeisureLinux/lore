# 省下 100 TB 内存：Cloudflare 怎么把 1.1.1.1 的 DNS 缓存条目砍到一半

> Cloudflare 1.1.1.1 的 Big Pineapple 平台同时承载着 1.1.1.1、Gateway DNS、DNS Firewall、AS112 等多条 DNS 业务线，每时每刻存着 **2500 亿条** DNS 缓存。在这种规模下，**每条目浪费 1 字节 = 全集群多花 250 GB 内存**。本文逐条复盘他们如何用 5 步把单条目内存从 953 字节压到 420 字节（−56%），整集群释放约 100 TB——同时插入吞吐 +43%、查询延迟 −19%。原文：[blog.cloudflare.com](https://blog.cloudflare.com/dns-cache-memory-optimization-1111/)（作者：Sebastiaan Neuteboom，2026-08-27）。

---

## 一、规模到底有多大

Big Pineapple 是 1.1.1.1 背后的统一 DNS 平台。任何时刻它的缓存里都有 **2500 亿** 条目。

> 想象一下：每条目多 1 字节，整集群就多 250 GB 内存。这不是"省着用"的问题——这是 2500 亿倍放大后的"重力学"。

他们用 5 步改造 DNS 缓存的内存布局，把单条目从 953 字节压到 420 字节，**节省 56%**。全集群加起来释放约 100 TB——相当于 130 台 [Gen 13 服务器](https://blog.cloudflare.com/gen13-config/)的总内存。

更妙的是，缓存还更快了：插入吞吐 +43%，查询延迟 −19%。少分配、内存布局更紧凑，**速度和空间同时拿到了**。

## 二、我们到底在缓存什么

冷启动时，Big Pineapple 是个空缓存。DNS 请求涌入，缓存逐渐填满；达到上限就淘汰老条目或不热门的。

具体容量因数据中心而异。当客户端开启 [EDNS Client Subnet (ECS)](https://en.wikipedia.org/wiki/EDNS_Client_Subnet) 时，权威服务器会按客户端网络返回不同答案，所以同一个查询要缓存多个版本——条目数翻倍，内存也跟着翻倍。本文要讲的几招优化，对 ECS 流量大的机房收益尤其明显。

每条目是一个 KV 对。**Key** 标识查询是什么：

```rust
pub struct CacheKey {
    qname: Name,
    qtype: Rtype,
    authenticated: bool,
    tag: Vec<u8>,
}
```

**Value** 存的是 DNS 响应本身：answer / authority / additional 三段，外加创建时间、命中次数、TTL 等元数据：

```rust
pub struct CacheEntry {
    timestamp: UnixTimeStamp,
    pub inception: Instant,
    pub ttl: Ttl,
    pub hits: u32,
    pub answers: Vec<Record>,
    pub authority: Vec<Record>,
    pub additional: Vec<Record>,
    pub errors: Vec<ExtendedError>,
    ...
}
```

两个结构体都有改进空间——里面不少字段类型在"已经存进缓存"之后就**根本不需要原本那部分开销**了。

> 📌 **解读**：Cloudflare 在 Big Pineapple 之前还有一篇 [《How Rust and Wasm power Cloudflare's 1.1.1.1》](https://blog.cloudflare.com/big-pineapple-intro/) 讲过这个平台本身的架构，本文聚焦在缓存层的数据结构改造。理解这个区别——"业务已经稳定→开始抠数据结构"——很重要：这是大型系统从"能跑"到"极致高效"的典型阶段。

## 三、怎么测内存

为了量化每一步的收益，他们做了一组基准测试：用随机生成的数据填满缓存，分布尽量贴近线上：56% 的 `A` 记录、25% 的 `AAAA`、19% 的 `TXT`，每条目 1–4 条记录。

`TXT` 在基准里当"所有非 A/AAAA 记录类型"的替身，大小随机 64–224 字节，跟实际变长记录类型的平均响应大小差不多。

内存用量用**自研全局分配器**（包装 Rust 的 `System` 分配器）统计，精确到"每条目分配了几次、共多大"。同时还测了插入吞吐和查询延迟，确保省内存不是以性能为代价换来的。

这套输入**逼近线上但不复制线上**。进程内存还受流量配比、缓存占用率、分配器状态、缓存外其他内存消耗影响。所以真正上线时，他们又量了**整进程常驻内存**。

> 📌 **解读**：基准里"用 `TXT` 代替所有非 A/AAAA 记录"是个很聪明的小技巧——基准不需要覆盖每种 record 类型的全部解析路径，只要那个"变长字符串开销"的成本特征对得上。Cloudflare 这种规模的系统做优化，最值钱的不是代码量，是**这种"在何处停止建模"的判断**。

## 四、第一步：`Vec` 的隐藏税

`Vec<T>` 内部存三个字段：堆数据指针、当前长度、总容量。`push` 时如果 `len == cap` 就重新分配，否则就追加。

![Vec 的三个字段](https://blog.cloudflare.com/_emdash/api/media/file/01M1171ECV1YR5KPQ90P5KWCTQ.png)

但 DNS 响应一旦写进缓存就**再也不会改了**——`cap` 字段根本没意义，但每个 `Vec` 还要为它付 8 字节。同理，堆上预留的多余空间也浪费了：能装 8 个的 `Vec` 只装了 5 个，堆上有 3 个空槽。

![Vec 预留空间浪费](https://blog.cloudflare.com/_emdash/api/media/file/01M1171TF66D0RDY101KB6WX7J.png)

换成 `Box<[T]>` 就都解决了：它创建后不能增长，所以不需要 `cap` 字段、也不需要预留空间。`String` 同理，换成 `Box<str>` 把 `cap` 丢掉。

一个 cache entry 里有 **8 个 `Vec`/`String` 字段**。全换成 `Box<[T]>` / `Box<str>`，**单条目省 64 字节**，顺带把 `Vec` 预留的那部分堆空间也省了。乘以 2500 亿条 = **15 TB+**。

> 📌 **解读**：这就是 Rust 标准库里 `Box<[T]>` 存在的全部理由。`Vec<T>` 是为"还要变长"准备的；缓存条目不是。Rust 把"创建后大小固定"的场景单独建模成 `Box<[T]>`，本质上是在类型层面告诉你"这玩意儿不会再长了"——编译器、阅读者、分配器都从中受益。这种"把不变量编码进类型"是 Rust 写系统代码最舒服的地方之一。

## 五、第二步：少几个列表、少几个指针

原本 answer / authority / additional 是**三个独立列表**。换成一个连续列表，**每段开头用 2 字节 `u16` 偏移**就行。每段条目数 `u16` 装得下，所以偏移 2 字节够用；而一个独立 `Box<[T]>` 要 8 字节指针 + 8 字节长度。

![三个 list 合并为 offsets](https://blog.cloudflare.com/_emdash/api/media/file/01M11729F5HH4PQEXGEQBD4SKG.png)

少掉两个列表（每个 8+8 = 16 字节），换成两个 2 字节偏移——**单条目省 28 字节**。

但实操中省的不止 28 字节。Rust 会按对齐要求插 padding，把结构体大小向上对齐到对齐数的整数倍——去掉一个小字段可能顺手把 padding 也去了。例如他们把几个 bool 字段压到一个 [bitflag](https://docs.rs/bitflags/latest/bitflags/) 里，结构体缩小的量比这些 bool 自身加起来还多。

> 📌 **解读**：所谓"省下 N 字节"在这里其实是个保守数字。Rust 的 `repr(rust)` 布局对 padding 没那么激进，但有系统性。`#[repr(C)]` 会让布局更可预测但更紧凑不一定——文章里的处理思路是：先以行为为单位算账，再用 `cargo bloat` / `sizeof` 看实际缩水。**这跟 x86_64 ABI 的对齐规则直接相关**：8 字节字段必须 8 字节对齐，所以一个结构体里删了某个 8 字节字段后，整体大小可能不变（因为它本来就是 8 字节对齐），也可能掉 8 字节——看后面那个字段的对齐要求。

## 六、第三步：能不要的 owner，就不要

每条 DNS 记录都有一个 owner（它属于哪个域名）。多数情况下 owner 跟被查询的域名**完全一致**——比如查 `example.com A`：

```
$ dig example.com A

;; ANSWER SECTION:
example.com.        300    IN    A        198.51.100.1
example.com.        300    IN    A        198.51.100.2
```

但有 `CNAME` 时，owner 会变：

```
$ dig example.com A

;; ANSWER SECTION:
example.com.        300    IN    CNAME    cdn.example.com.
cdn.example.com.    300    IN    A        198.51.100.1
cdn.example.com.    300    IN    A        198.51.100.2
```

DNS 协议在线上格式（wire format）里用**名字压缩**（[RFC 1035 §4.1.4](https://datatracker.ietf.org/doc/html/rfc1035#section-4.1.4)）处理重复 owner：第二次出现时，存一个 2 字节指针指回第一次出现的位置。`www.example.com` 编码成 `www` + 指回 `example.com` 那次的指针。

线上格式这样玩很省。但缓存里，他们**老老实实把完整 owner 存在每条 record 上**——查缓存时跟着压缩指针走，延迟太大。**用内存换速度**。

可问题来了：大多数记录的 owner 跟被查域名是同一个。那 owner 字段对它们来说**纯属浪费**。优化后是这样：

```rust
pub struct Record {
    owner: Option<Box<Name>>,
    class: Class,
    ttl: Ttl,
    rtype: Rtype,
    data: RecordData,
}
```

`owner` 是 `None` 时，构造响应时直接从 cache key 把被查域名填回去——**省掉一次堆分配**。这意味着 record 不再是"自包含"的，但 cache key 在每次查缓存时本来就在手边。owner 不一样时（比如 CNAME 后的 A 记录），`Some(...)` 存指向完整名字的堆指针。

![Option<Box<Name>> 优化](https://blog.cloudflare.com/_emdash/api/media/file/01M1172Q50SZ00545BWCNAAP2S.png)

实测大部分缓存记录的 owner 跟被查域名一样——**绝大多数条目完全不需要为 owner 做堆分配**。

> 📌 **解读**：`Option<Box<T>>` 这种"两层包装"在 Rust 里看起来啰嗦，实际上是经典的"用判别式 + 指针"省空间写法——`None` 时是"零指针 + 一个字节判别"（加上 padding），`Some` 时是一个真实指针。如果直接 `Box<T>` + 一个 bool flag，至少多 8 字节；用 `Option` 把判别式和指针绑一起，反而是 8/16 字节两种状态。**标准库 `Option` 的 niche optimization**（对 `Box<T>` 这种"指针永远非 null"的类型，把 `None` 编成"零指针"）正是这件事的工程化实现。

## 七、第四步：enum 的大小

Rust 的 enum 是**代数数据类型（ADT）**：每个变体可以带不同数据，但 enum 本身的 size **等于最大变体的 size**。

```rust
pub enum Option<T> {
    Some(T),
    None,
}
```

`Option` 要么是 `Some(T)` 要么是 `None`。两个变体占同样多空间。enum 里存一个 tag 标识当前是哪个变体，后面紧跟足够装最大变体的空间；变体是 `None` 时，那部分空间就空着。

DNS record data 很自然写成 enum：

```rust
pub enum RecordData {
    A(Ipv4Addr),
    Aaaa(Ipv6Addr),
    Txt(Txt),
    Naptr(Naptr),
    Svcb(Svcb),
    // ...
}
```

但 enum 总跟最大变体一样大。这里最大的是 `NAPTR`——136 字节，3 个变长文本字段、1 个域名、2 个整数。加 tag 和 padding，**整个 enum 144 字节**。

![RecordData enum 144 字节](https://blog.cloudflare.com/_emdash/api/media/file/01M11731ZGD3390K0YFH8CHPWC.png)

而 `A` 只要 4 字节，`AAAA` 要 16 字节。**A+AAAA 占 80% 流量**——大多数 record 在 padding 上浪费 120 字节。**一条 cache entry 装多条 record，这浪费累积起来极快**。

### 7.1 把大变体 Box 出去

解法：把 enum 的**大变体装 Box**，移到独立堆分配。enum 里就只留一个 8 字节堆指针，真实数据在堆上按需分配。

```rust
pub enum RecordData {
    // 小且常见的变体就地存
    A(Ipv4Addr),
    Aaaa(Ipv6Addr),
    // 大变体丢到堆上
    Txt(Box<Txt>),
    Naptr(Box<Naptr>),
    Svcb(Box<Svcb>),
    // ...
}
```

对 `A` / `AAAA` 来说，**单 record 省 120 字节**。`TXT` / `CNAME` 这些"小变体"也受益：enum 还是 24 字节，但堆分配按真实数据尺寸来，不用 padding 到 144 字节。最大变体 `NAPTR` 反而**多了一点**——多了一次堆指针和分配开销。但 `NAPTR` 实际很少见，**这笔账划算**。

![Box 后的内存布局](https://blog.cloudflare.com/_emdash/api/media/file/01M1173F6HNANE82T98F4MZ2YE.png)

但 Box 不是免费的。

### 7.2 Box 的代价

第一个代价是**分配器开销**。每个 box 变体都是独立堆分配，分配器会向上对齐到 size class。Big Pineapple 用 [jemalloc](https://jemalloc.net/)——专门为多线程、高分配负载设计的分配器，把相似大小的分配归到固定 bin。`TXT` 申请 32 字节正好落 32-byte bin，零浪费；`MX` 申请 40 字节向上对齐到 48，**浪费 8 字节**。

第二个代价是**内存局部性差**。没 Box 时，record enum 值在一块连续内存里。Box 后，每个 box 变体都在各自的堆区域。读的时候要先跟指针——**指针落在远离 entry 其他部分的地方，CPU 就得去取新的 cache line**。几百万个 entry 一累加，box 的数据散落在堆各处，**不挤在一起**。

![Box 后的内存分散](https://blog.cloudflare.com/_emdash/api/media/file/01M1173Y9TP7GJE9TZJ9P3G8R2.png)

两个代价单独都不致命，**但都消掉就有可观的内存和延迟双收**——下一节正是这件事。

> 📌 **解读**：这一节是 Cloudflare 团队最诚实的部分。Box 看起来很美——把"大变体挤占 enum 空间"治了，但引入了**指针追逐 + 缓存行 miss**。在 L1 缓存 32 KB / L2 几百 KB / L3 几十 MB 的典型层级里，**一条 cache line 64 字节**——一次 miss 就是从主存取 64 字节（延迟约 100 ns，比 L1 慢 30+ 倍）。这条 memcached/Redis 类系统在 1.7 版本之后反复做"小对象压缩 + slab 紧凑化"的根本原因——同样思路 Cloudflare 在 1.1.1.1 的 Rust 代码里自己手做了一遍。

## 八、第五步：用 wire format 存 record

直觉上，下一步应该是把整个 DNS 响应按 wire format 存，每次查询时只改 message ID 之类的 per-client 字段。但这条路有麻烦：DNSSEC 记录只在客户端设了 [DO (DNSSEC OK)](https://www.cloudflare.com/learning/dns/dnssec/how-dnssec-works/) flag 时才出现。要么缓存两份（带 DNSSEC / 不带），要么从已构造好的 message 里把它们筛掉——都不优雅。还有个成本：每次查都要重新解析整个 message，而 enum 方案已经存了"已解析"的 record，省掉了这一步。

折中方案：**record data 用裸字节存**，cache entry 的其他字段仍是结构化的。原来的"`Vec<enum variant>`"换成**单个 `Box<[u8]>`**——每条 record 编码成"2 字节长度前缀 + 裸字节"。

![wire format 存 record](https://blog.cloudflare.com/_emdash/api/media/file/01M11749PX9A28DBGYB03Z48HN.png)

这同时干掉了两件事：**per-variant enum 开销**和**前一步 Box 引入的多次堆分配**。数据也变紧凑了——CPU cache 局部性更好。

代价：record **不能再随机索引**。要顺序遍历整个 buffer。这给 round-robin 切 `A`/`AAAA` 之类功能加了点复杂度，但单 entry 里 record 数量本来就不多，**这点成本可以忽略**。

构造响应时，大部分 record 类型**直接从 buffer 拷到出站 message**。原来每条解析过的 record 都要按字段序列化回 DNS wire format——现在 `A` / `AAAA` / `TXT` / 所有 DNSSEC 类型**直接 copy 编码好的字节过去**。只有带域名的 record（`CNAME` / `NS` / `MX` / `SOA`）还要解析，因为要做 DNS name compression。但**能直接 copy 的 record 是流量大头**——这一步**减少了查缓存路径的工作量**。加上内存局部性变好，**实测查缓存延迟再降 5%**。

构造 record data buffer 用的是**跨 cache 插入复用的 scratchspace buffer**。之前的写入已经把 buffer 撑大了，后面很少需要再分配。record 大小不一，没序列化完之前不知道精确要多大。record 进 scratchspace 后，再 `Box<[u8]>` 一次性 `memcpy`——把"每条 record 一次 box"换成"整个 record data 一次 box"。顺带避开 `Vec<u8>` 缩容时分配器没法回收尾部的浪费。**基准里光这一步就让插入吞吐 +13%**。

> 📌 **解读**：这是一个很经典的"**用长度前缀把变长记录变定长切片**"技巧。Go 的 `binary.Read`、`Protobuf` 的 wire format、Cap'n Proto 全是这个套路。**每条 record 前 2 字节长度 = 数组不会失联**——长度已知，结构化字段和字节流可以混存。对 Rust 来说更妙的是 `Box<[u8]>` + 自定义 `Read` 实现可以零拷贝解析大部分类型（`A` 直接读 4 字节成 `Ipv4Addr`，`AAAA` 读 16 字节，**完全没有中间表示**）。这就解释了为什么"按 wire format 存"反而不比 enum 慢——还更快。

## 九、效果：每条记录 953 → 420 字节

下面是基准和线上数据。

**生产数据**：下图是 Big Pineapple 实例在 p90 / p98 / p99 的常驻内存。第一条虚线（2026-05-18）是发布开始日，第二条（2026-07-06）是所有服务发布完成日。每个发布都引入了上述一项或多项优化，所以内存是**阶梯式**下降，不是一刀切。

![生产内存阶梯下降](https://blog.cloudflare.com/_emdash/api/media/file/01M1174QR0ZH0HWEQBS50Q5641.png)

每次发布，新启动的实例从空缓存开始，缓存填满后内存才稳定。所以**稳定平台期的值**比刚启动的低谷更代表稳态内存。

| 指标 | 发布前 | 发布后 | 变化 |
|------|--------|--------|------|
| **p99 常驻内存** | 9.3 GB | 5.3 GB | **−43%** |
| **p90 常驻内存** | 6.5 GB | 3.8 GB | **−42%** |

缓存越满的实例，**绝对节省越大**。

**基准数据**：5 步优化让单条目内存从 953 字节 → 420 字节，**−56%**。单条目分配总量从 1.1 KB → 461 字节，**−58%**。

| 指标 | 优化前 | 优化后 | 变化 |
|------|--------|--------|------|
| 单条目净内存 | 953 字节 | 420 字节 | **−56%** |
| 单条目分配量 | 1.1 KB | 461 字节 | **−58%** |
| 插入吞吐 | 625,000 条/秒 | 893,000 条/秒 | **+43%** |
| 查询延迟 | 828 ns | 670 ns | **−19%** |

线上降幅比基准小，因为常驻内存里除了缓存还有进程的其他部分。**发布稳定后，整集群工作集内存总共下降约 100 TB**。

> 📌 **解读**：这个 −56% / −58% / +43% / −19% 的"全胜"在工程上很少见——通常内存优化要么靠**空间换时间**（cache 池化、压缩），要么靠**时间换空间**（LRU 淘汰），两边都赚只可能是一开始就有"代码改对了**同时**消除了拖累"的事。Cloudflare 这次正是这样：他们改的每个点（`Vec`→`Box`、合并列表、Option owner、Box 大变体、wire format）**都是既减小体积又减少分配数**——而每次"少分配"对 CPU cache 是双赢（少 load 指令 + 少指针追逐 + 少 cache line miss）。这是教科书级的"**内存布局是性能**"。

## 十、下一步怎么用省下的内存

Cloudflare 计划把省下的内存**全部投回去**——**增大缓存容量**但不增加总内存。结果：缓存命中率提升、向上游权威服务器的查询量下降——**更少的回源 = 更低的延迟 = 更低的回源成本**。

他们还在继续抠这个缓存本身。

---

## 十一、点评：100 TB 是怎么"省"出来的

把 Cloudflare 的故事拆开看，其实就是一句话：**在 2500 亿这个量级下，每个 byte 都被乘以 2500 亿**。这给所有写"高基数 KV 存储"的工程师一份很清晰的 checklist：

1. **`Vec`/`String` 一定需要 `cap` 吗？**如果不再增长，`Box<[T]>` / `Box<str>` 既省字段又省预留空间。
2. **同类容器能合并吗？**三个 `Vec<Record>` → 一个 `Box<[u8]>` + 偏移，省的不是 28 字节，是结构体 padding 之外的指针追逐。
3. **有"基本相同"的字段吗？**Option / 指针 / nil 判别——能压成 niche optimization 就压。
4. **enum 变体大小差几个数量级？**大变体 Box 出去，但**要算清 cache line 成本**。
5. **能不能直接存 wire format？**配合长度前缀 + 零拷贝读，**结构化表示反而是累赘**。

每一步单独看都不惊艳：**64 + 28 + 一堆 Option + 一些 Box + 一点 Box<[u8]>**。但叠起来就达到 −56% / −58%，顺手 +43% / −19%。这就是"内存布局是性能"的具体含义——**不是某一个微优化神奇地消灭瓶颈，是几百个小决策在每一层 cache 上同时让出空间**。

如果你也在写类似规模的服务（DNS、CDN 元数据、Kubernetes apiserver 的 etcd 缓存、Service Mesh 的 xDS 推送……），同样的故事可以复刻：**先量，后改**。Cloudflare 的整套方法论就两句话——

1. **别猜，拿基准量**。自研 `GlobalAlloc` 包装器是 50 行代码的工程，能让"每条目字节数"变成可测量的指标，而不是"看起来差不多"。
2. **别赌，跑生产**。基准里 −56% 到生产 −43% 之间的差，是非缓存内存部分——**只有上线了才看得到**。

省下 100 TB 的从来不是某一个天才想法，是 5 步"每步都不起眼"加起来。

---

## 参考

- 原文：[How we saved 100 terabytes of memory by optimizing 1.1.1.1's DNS cache](https://blog.cloudflare.com/dns-cache-memory-optimization-1111/)
- 原文作者：Sebastiaan Neuteboom，Cloudflare
- 平台背景：[How Rust and Wasm power Cloudflare's 1.1.1.1](https://blog.cloudflare.com/big-pineapple-intro/)
- 标准与协议：[RFC 1035 §4.1.4 (DNS message name compression)](https://datatracker.ietf.org/doc/html/rfc1035#section-4.1.4)、[EDNS Client Subnet](https://en.wikipedia.org/wiki/EDNS_Client_Subnet)
- 工程工具：[jemalloc](https://jemalloc.net/)、[Rust `bitflags`](https://docs.rs/bitflags/latest/bitflags/)

> **本文以 [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) 协议开源。**
