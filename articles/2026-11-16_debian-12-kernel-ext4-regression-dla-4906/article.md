---
title: "Debian 12 内核更新冻住服务器：被 revert 过的 ext4 回归"
date: 2026-11-16
slug: debian-12-kernel-ext4-regression-dla-4906
category: 技术/解读
author: FreeLAMP.com
original_source: "用户提供的新闻转述（Micha 的 #1154101、七份合并报告、25 秒至约 5 小时、NULL 解引用、6.1.192-2 于 11-16 进入 bookworm 安全仓库）＋ 一手核对：Debian LTS 公告 DLA-4906-1（Salvatore Bonaccorso，2026-11-15，linux 6.1.192-1，CVE 列表见 tracker）与 DLA-4906-2（regression update，6.1.192-2）；Debian BTS #1154101 / #1154108（Eduard，2026-11-15，arm64 独立复现、6/6 oops、两行复现 echo 3 > /proc/sys/vm/drop_caches + dd 4MB、无需特权、无 ext4 特性依赖、修复已排入 6.1.193）/#1154151（Timon de Groot，OpenStack 上 dpkg 解包 ~1GB 包时崩、完整调用栈、jbd2_journal_wait_updates 与 wait_transaction_locked 卡死）经 mail-archive 取得原文（bugs.debian.org 当时 429 限流）；Cyber Kendra（Vivek，2026-11-16）与 Marc Pope（2026-11-16）的现场整理与三月 revert 时间线；上游一手：Elliot Berman 2026-11-02 的 `[PATCH 6.1.y 0/2] Fix NULL folio dereferences from IS_ERR() checks in 6.1.191`（d34e4fd4e73f / 862483175d3d 两个 folio 转换在 6.1 上没有 66dabbb65d67，IS_ERR 永假、NULL 被当有效 folio；用 Coccinelle 扫出 ntfs3 同类；stable-queue 中 650ca269458a 补丁把 IS_ERR 改 NULL 检查并返回 -ENOMEM，fs/ext4/mballoc.c 14 增 14 删）＋ 三月 Mark Brown bisect / Ted Ts'o 复现后把三补丁从 6.1.167-rc1 撤掉的 LKML 归档链接 ＋ 本工作区旧文 CVE-2026-98432 / NoisyTCP 相关"
original_date: 2026-11-16
original_url: "https://www.mail-archive.com/debian-lts@lists.debian.org/msg12578.html"
description: "本文解读 Debian 12 bookworm 的一次安全更新事故。11-15 Salvatore Bonaccorso 发 DLA-4906-1，把内核更新到 6.1.192-1（linux-image-6.1.0-55）；两小时多后 #1154101 到来：重启数分钟后 IMAP / SMTP / HTTP / SSH 全部无响应，控制台 kernel Oops。BTS 七份报告合并，覆盖裸机、Xen、KVM、Hyper-V、VMware 与 amd64 / arm64 / i686；Timon de Groot 在 OpenStack 上 dpkg 解包 1GB 包时崩，失败时间从 25 秒到约 5 小时不等。根因不是 Debian 改坏，而是 upstream 6.1.y 回归：6.1.191 合入的 ext4 mballoc folio 转换 d34e4fd4e73f 与 862483175d3d 是为 6.4+ 写的，那里 __filemap_get_folio() 失败返回 ERR_PTR；6.1 缺少 66dabbb65d67，失败返回 NULL，backport 里的 IS_ERR() 检查因此永远为假。页面缓存被 drop_caches 或内存压力逐出后，ext4_mb_load_buddy_gfp() 的快路径拿到 NULL 且没有 FGP_CREAT，紧接着 folio_test_uptodate(NULL) 解引用 0 地址；出错任务带着 jbd2 journal handle 死掉，之后所有写该文件系统的事务卡在 wait_transaction_locked，机器还能 ping 但登录、数据库、Web 全挂。关键时间线：同一组补丁三月曾进 6.1.167-rc1，被 Mark Brown bisect、Ted Ts'o 在 x86_64 复现后撤掉；十月又随 6.1.191 回来。修复 patch 11-02 由 Elliot Berman 公开（把 IS_ERR 改为 NULL 检查并返回 -ENOMEM，14 行改动），已进入 stable-queue、排入 6.1.193；Bonaccorso 11-16 提供测试内核，测试者确认不再崩，修正包 6.1.192-2 当日进入 bookworm 安全仓库（DLA-4906-2）。文章写清运维动作：uname -r 看是不是 6.1.0-55、GRUB 高级选项退回 6.1.0-54、hold linux-image-* 直到镜像上有 6.1.192-2；并把「退回 6.1.0-54 会重新暴露 NoisyTCP CVE-2026-99288」的权衡写明，不把临时回滚说成终局。边界：未实测任何内核；BTS 当时 429 限流，bug 细节从 mail-archive 与媒体交叉；DLA-4906-1 的 CVE 精确数量以官方 tracker 为准，不照抄第三方 1271 说。"
published: true
---

11 月 15 日，Debian LTS 发出 DLA-4906-1，把 bookworm 的内核更新到 6.1.192-1（`linux-image-6.1.0-55`），一次带上大量 CVE 修复。两小时多以后，bug tracker 开始亮灯：有人的邮件与 Web 服务器在重启几分钟后，IMAP、SMTP、HTTP、SSH 全部不响应，控制台打出一行 kernel Oops。

这类事故最容易被写成「Debian 又发了个坏内核」。把 BTS、上游补丁和邮件列表排开看，更准确的说法是：一个三月已经被 bisect 并撤掉的 upstream ext4 回归，十月又回到了 6.1.y，Debian 跟着带上了它；而修复补丁在事故前十天就已经公开。

## 一、崩在哪：不是文件系统坏了，是块分配器踩了 NULL

所有报告的错误签名一致：`ext4_mb_load_buddy_gfp()` 里的 NULL 指针解引用，这是 ext4 块分配器 —— 决定文件数据落在哪些块上的代码。

故障链条按 BTS 里的调用栈与报告者分析：

1. ext4 为每个块组在页缓存里保留 bitmap 与 buddy 页；
2. 内存压力或 `echo 3 > /proc/sys/vm/drop_caches` 把这些页逐出；
3. 下一次分配/删除触发快路径查找，`__filemap_get_folio()` 在 6.1 上失败时返回 NULL；
4. 移植过来的代码却用 `IS_ERR()` 判断错误 —— 在 6.1 上这个检查永远为假；
5. 代码把 NULL 当成有效 folio，紧接着 `folio_test_uptodate(NULL)` 解引用地址 0，Oops；
6. 出错任务带着一个 jbd2 journal handle 死掉，journal 不再提交，之后所有写这个文件系统的进程卡在 `wait_transaction_locked`。

这解释了两个很反直觉的现象。其一，机器还在 ping：内核主循环没死，只是写入路径全卡住，因此 SSH 会话建立不起来、数据库与 Web 停摆，看起来像「死机」。其二，触发时间极不稳定：从 25 秒到约五小时都有，取决于该机器多快把 bitmap 页挤出缓存 —— 忙服务器几分钟就中招，安静机器能撑很久。

Eduard 在 #1154108 里给出两行复现（root、2 CPU / 2 GiB、根在 ext4）：

```
echo 3 > /proc/sys/vm/drop_caches
dd if=/dev/zero of=/mnt/b0 bs=1M count=4 conv=fsync
```

他在 arm64 上 6 次尝试 6 次 Oops，而 6.1.190-1 与 6.1.187-1 上为零；还强调无需特权、在带内存限制的不可信容器里也能复现，并且与 ext4 特性、挂载选项无关。Timon de Groot 在 #1154151 里描述的是另一条常见路径：新开 OpenStack bookworm VM、dist-upgrade 后重启，在 `dpkg` 解包一个约 1GB 的包时崩，`/` 与第二块 ext4 数据卷都中招。

## 三月的老熟人，十月的回归

这件事最值得写进复盘的是时间线：

- 三月：两个 folio 转换补丁（`d34e4fd4e73f` "ext4: convert bd_bitmap_page to bd_bitmap_folio"、`862483175d3d` "ext4: convert bd_buddy_page to bd_buddy_folio"）作为 CVE 修复 `a3a7d360252c` 的依赖，进入 6.1.167-rc1。Mark Brown 在 arm64 上 bisect 出同样的 Oops，Francesco Dolcini 在 32 位 i.MX6 上也遇到，Ted Ts'o 用 kvm-xfstests 在 x86_64 复现，请 Greg KH 把三个补丁一起撤掉；6.1.167 正式版没有它们。
- 十月：同一组补丁随 6.1.191 又回来了。
- 11 月 2 日：Elliot Berman 在 linux-ext4 邮件列表发出 `[PATCH 6.1.y 0/2] Fix NULL folio dereferences from IS_ERR() checks in 6.1.191`。修复本身很小 —— 把 `IS_ERR()` 改成 NULL 检查、回退到转换前的 `-ENOMEM` 语义，`fs/ext4/mballoc.c` 14 行增、14 行删；他还用 Coccinelle 扫树，顺手修了 ntfs3 里同类的一处。Sasha Levin 把 ext4 那个补丁放进 stable-queue，排队进 6.1.193。
- 11 月 14–15 日：Debian 构建 6.1.192-1（一次跨两个 upstream stable 版本，changelog 约 2500 行），11-15 发布 DLA-4906-1。
- 11 月 16 日：Bonaccorso 把崩溃对应到 Elliot 的补丁，放出测试内核 `6.1.192-1a~test1`；测试者 Christopher Odenbach 回「Works for me, no crash since 10 minutes! Wohoo!」。修正包 6.1.192-2 当日进入 bookworm 安全仓库，即 DLA-4906-2（regression update）。

所以「修复已经在路上」不是安慰话 —— 它在公告前 13 天就已进入 upstream 审查队列。坑在于：Debian 跟随 6.1.y 的发布节奏，而 6.1.192 发布时 6.1.193 的修复尚未 cut，于是带着回归的版本按 high urgency 发了出去。Marc Pope 那句评价很准：没有人的流程做错了，流程里有个十二天的洞。

顺带一提，DLA-4906-1 的 CVE 列表长得惊人；有第三方报道写「1271 个 CVE」，本文不把该数字当作 Debian 公告的官方统计口径 —— 以 tracker 上的列表为准。Bookworm 于 2026-06-11 进入 LTS，内核项目现在几乎给每个 bug 修复都分配 CVE，LTS 团队只能整支跟踪 6.1.y，这类「上游回归随批发货」的风险因此被放大。

## 三、回滚不是终局：NoisyTCP 的权衡

官方与社区给的临时处置都一致：

- `uname -r` 先看是不是 `6.1.0-55`；
- 是的话，从 GRUB 高级选项启动 6.1.0-54，或用 `grub-set-default` 固定它；
- hold 住 `linux-image-*`，等镜像上出现 6.1.192-2 再升级；
- 机器已经中招又没有带外控制台（IPMI / 串口）的，当作宕机处理 —— 有人在几分钟内失去 SSH，其中一位不得不从备份恢复系统盘。

但这里有个必须写明的权衡：6.1.0-55 同时也是 CVE-2026-99288（NoisyTCP）的修复版本。这个漏洞让远端攻击者通过任意可达 TCP 端口、无需凭据即可让主机崩溃，需要多接收队列或开启 RPS —— 正是多数服务器的配置。换句话说，退回 6.1.0-54 是把「负载下自己卡死」换成「外人能把你打挂」。回滚只应维持到修正包可安装为止，不能当成长期方案。

不受影响的线索也写一下：bookworm-backports 上的 6.12.95、trixie 的 6.12.117 都没事 —— 在 6.12 里 `__filemap_get_folio()` 返回错误指针，`IS_ERR()` 检查本来就是对的；trixie 的 6.12.117-1 也带有 NoisyTCP 修复。

## 四、运维视角：三件值得抄的事

1. 证书不要替你做生产验证：一次跨两个 upstream stable 版本、两千多行的 changelog，没有人能读完再放进生产。批量安全更新的验证必须靠「一台可牺牲的机器先跑生产负载 24 小时」，而不是靠版本号。
2. `drop_caches` 不是无害的调试命令：它是这次最快、最可靠的触发器；线上排查缓存问题时，记得它也会把 ext4 的 bitmap/buddy 页一起赶走。带内存限制的容器下同样能触发。
3. 带外访问是内核升级的前置条件：这次最惨的案例是崩了以后没人能进机器。SSH 消失时，有 console 和没有 console 的恢复时间差了几个数量级。

还有一条面向发行版维护者的：backport 的语义差异要当 bug 高发区看。6.4 改了 `__filemap_get_folio()` 的失败返回值，移植到 6.1 时所有 `IS_ERR()` 检查都成了摆设 —— 这不是 ext4 独有，Berman 用 Coccinelle 在 ntfs3 里又抓到一处。同一个 CVE 依赖把同一批 broken 补丁两次带进同一分支，第二次还出了门；这类「重复回归」值得在 stable 流程里留个专门的检查点。

## 五、边界

- 本文未安装、未升级、未复现任何内核；所有崩溃细节来自 BTS 报告、mail-archive 原文、公告与上游 commit。
- `bugs.debian.org` 抓取时返回 429 限流，bug #1154101 / #1154108 / #1154151 的具体内容从 Debian 邮件列表归档与媒体交叉核对；合并报告数（七份 / 十余份 duplicate）按各自出处标注，不强行统一。
- 「25 秒至约 5 小时」来自用户提供的转述与 Nils Kalchhauser 在 Hetzner / OVH 上的观测；具体触发时间随内存压力变化，不是固定值。
- 修复版本号 `6.1.192-2` 与 DLA-4906-2 已由 Debian tracker 与 LinuxSecurity 公告确认；镜像是否到达各架构默认包按 11-16 时点，读者应以自己镜像实际可用版本为准。
- 未逐条核对 DLA-4906-1 的全部 CVE，也不把第三方的「1271 个 CVE」当作官方数字。
- 回滚与 NoisyTCP 的权衡依据 CVE-2026-99288 的公开描述与第三方报道；是否回滚须按各自暴露面判断。

## 六、结论

这次事故的本体是一个已知、已 bisect、已 revert 过的上游回归，在批量安全更新的流程里第二次溜了进来，而非单纯「ext4 有 bug」。修复补丁早在 11 月 2 日就公开，Debian 的构建与发布节奏正好卡在 upstream 切版本之前 —— 于是用户先收到一个会在正常负载下自锁的内核，再收到一个修它的 regression update。

处置很清楚：确认版本、退回 6.1.0-54、hold 到 `6.1.192-2` 出现在自己的镜像里；有 console 的机器比没 console 的机器幸运得多。更长线的教训是：当安全更新一次带上几百上千个 CVE、changelog 长到没人能读时，真正的安全边界已经从「审代码」转移到「先在牺牲机上跑生产负载」。

## Sources

- 用户提供的社群转述（Micha / #1154101 / 7 份合并报告 / 6.1.192-2）
- Debian LTS DLA-4906-1（Salvatore Bonaccorso，2026-11-15）与 DLA-4906-2（regression update）：<https://security-tracker.debian.org/tracker/DLA-4906-1> ｜ <https://security-tracker.debian.org/tracker/DLA-4906-2>
- Debian BTS #1154101 / #1154108 / #1154151（经 mail-archive 归档原文）：<https://bugs.debian.org/cgi-bin/bugreport.cgi?bug=1154101> ｜ <https://www.mail-archive.com/debian-bugs-dist@lists.debian.org/msg2133991.html> ｜ <https://www.mail-archive.com/debian-lts@lists.debian.org/msg12577.html>
- 上游修复：Elliot Berman `[PATCH 6.1.y 0/2]`（2026-11-02）：<https://lore.kernel.org/linux-ext4/20261102-ext4-ntfs3-null-folio-v1-0-4fd91ee23a4a@elliotjb.com/> ｜ stable-queue 补丁：<https://git.kernel.org/pub/scm/linux/kernel/git/stable/stable-queue.git/tree/queue-6.1/ext4-fix-null-folio-dereference-in-mballoc.patch>
- 三月 revert 讨论：<https://lkml.iu.edu/2603.3/01511.html> ｜ <https://lkml.iu.edu/hypermail/linux/kernel/2603.3/02704.html>
- 现场整理：Cyber Kendra <https://www.cyberkendra.com/2026/11/debian-12-kernel-6-1-0-55-freeze-ext4-fix.html> ｜ Marc Pope <https://www.marcpope.com/blog/debian-12-s-new-kernel-freezes-ext4-servers-in-minutes-and-stable-rejected-the-patches-in-march>
