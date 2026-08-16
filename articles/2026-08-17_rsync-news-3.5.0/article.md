# rsync 3.5.0 发布说明（中文版）

> 原文链接：[https://download.samba.org/pub/rsync/NEWS#3.5.0](https://download.samba.org/pub/rsync/NEWS#3.5.0)
> 
> 发布日期：2026 年 8 月 13 日
>
> 本文由 LeisureLinux 根据 rsync 官方 NEWS 完整翻译

---

## 感谢

这是一个历经数月开发的非凡版本，我要感谢所有让这一发布成为可能的人。我们要处理的安全问题数量非常多，如果没有得到的帮助，这将会非常令人难以应付。

我特别感谢 Zen Dodd (Tao)、Omar Elsayed (seks99x)、Will Sargeant、Paul Mackerras、Aleksa Sarai 和 Leonid Bugaev (buger) 加入 rsync 管理员小组，协助分类所有问题、开发新测试、评审 PRs，并帮助我们制定"在何处划定安全问题与预期行为界限"的指南（在某些情况下这异常困难）。你们的巨大帮助让 rsync 变得更好。

同样要衷心感谢 Trail of Bits 的 Filipe Casal，他与我们一起参与了"Patch the Planet"项目。Filipe 提供了大量有价值的测试和安全报告。

还要特别感谢 Greg Kroah-Hartman 提供的宝贵建议和报告，以及 Stuart Inglis 提供的高质量 Bug 报告和测试。

感谢所有提交 Bug 报告的人，具体致谢列在下面的 individual items 中。

最后，感谢所有在 rsync-security 邮件列表中参与讨论和测试的人，以及感谢 rsync 用户社区耐心等待发布。

### 安全修复

本次发布修复了通过以下途径发现的 **33 个安全问题**：对 rsync 路径处理和 daemon 协议的专项审计、伴随的 daemon 协议模糊测试，以及外部研究人员报告 — 另外还包含数项健壮性加固。CVE 编号由 VulnCheck (CNA) 分配；每个公告都附有精确的"引入版本"范围，许多远比"3.5.0 之前的所有版本"更窄。每个修复都随附一次回归测试，在未修复的代码树上会失败。特别感谢以下 credited 的外部研究人员。

#### 链接跟踪 (CWE-59/61) —— 控制路径组件的本地用户植入符号链接，特权 rsync 随后会跟随：

- **CVE-2026-53802 (HIGH)**: 通过符号链接操作符提供的输入文件进行任意文件读取/传输塑形。rsync 跟随着攻击者植入的符号链接，这些符号链接出现在 `--filter` 合并文件（including per-directory merges 和 `-C` `.cvsignore`）、`--files-from` / `--include-from` / `--exclude-from`，以及客户端 `--password-file` / daemon 密钥文件中 —— 将这些任意文件作为过滤规则读取，或将受害者的文件内容作为 daemon 认证响应发送。操作者提供的路径现在通过组件逐个解析，使用 `openat(O_PATH|O_NOFOLLOW)`，仅当符号链接由 uid 0 或有效 uid 拥有时允许符号链接组件。

- **CVE-2026-53803 (HIGH)**: 通过符号链接操作符提供的输出路径进行任意文件写入/权限提升 —— `--log-file`、`--write-batch`/`--read-batch`，以及 daemon 的 motd / lock / early-input / `--config` 打开。植入的符号链接（或父组件）可以重定向写入，例如将日志追加到 `authorized_keys`；`--read-batch` 也可以向协议解析器提供选择的字节。使用相同的可信所有者路径遍历，并对 `--read-batch` 文件进行 `S_ISREG` 检查。

- **CVE-2026-53785 (HIGH)**: 在 `--relative` 下，接收者的隐式父目录创建（`make_path()`）通过完整的 `mkdir()` 构建父链，因此植入的父符号链接将新目录和文件放置在目标树外。`make_path()` 现在通过保持的目录 fd 原语创建每个组件。由 Omar Elsayed (seks99x) 报告。

- **CVE-2026-53784 (HIGH)**: 在 `use chroot = no` 下 daemon 模块根目录 chdir 逃逸：普通的 `chdir()` 跟随植入的父组件符号链接，从模块外提供文件。模块根目录的 chdir 现在通过安全解析器进行。

- **CVE-2026-53793 (HIGH)**: Chroot `/./` 内部模块逃逸 —— 内部模块中的符号链接父组件连接到外面的兄弟节点（生成器基目录统计、接收者写入/完成路径、模块 chdir，以及接收者的 delta-basis 打开）。现在为所有这些路径启用安全解析器。

- **CVE-2026-53795 (HIGH)**: 绝对的 `--temp-dir` 或 `--link-dest` 禁用接收者的重命名/链接限制。`do_rename_at()`/`do_link_at()` 在 *任一* 路径为绝对时退出到未限制的路径调用，因此绝对源（临时文件或 link-dest 基目录）让 `finish_transfer()` 的 tmp→final 重命名 —— 或硬链接创建 —— 跟随目标父组件，攻击者在传输过程中将其翻转为符号链接，将文件写入树外。现在两侧独立受限。由 Omar Elsayed (seks99x) 报告。

- **CVE-2026-53796 (MEDIUM)**: 非 daemon 接收者的一次 `chdir()` 进入操作者命名的目标未完全受限（相对目标使用普通的 `chdir()`），因此攻击者将命名的目标从目录竞争到符号链接，移动接收者的 CWD —— 以及随后创建的所有文件 —— 到树外。目标 chdir 现在使用与 daemon 模块 chdir 相同的拥有检查 `O_NOFOLLOW` 遍历（参见行为变更）。由 Omar Elsayed (seks99x) 报告。

- **CVE-2026-53797 (MEDIUM)**: 非 daemon 发送者通过路径打开每个传输文件的内容（仅叶节点 `O_NOFOLLOW`），因此文件列表扫描后，一个不特权用户将源父组件竞争到符号链接被跟随 —— 从源树外读取文件到攻击者可读的目标。现在使用 `secure_relative_open()` 在传输根锚定内容打开；`-L` / `--copy-unsafe-links` / `-k` 仍然跟随，`--insecure-links` 恢复旧的打开方式。

- **CVE-2026-53799 (MEDIUM)**: 接收者 ACL/xattr 元数据应用跟随符号链接竞争 → 任意 ACL 设置（本地权限提升）。当保留元数据（`-A`/`--acls`、`-X`/`--xattrs`，或 fake-super ACL-as-xattr）时，接收者通过路径 `acl_set_file()` / `setxattr()` 应用每个条目的 ACL/xattr。在应用前将刚接收的条目（或父目录）竞争到符号链接的本地用户可以重定向攻击者选择的 ACL —— 字节由源条目携带 —— 到目标树外的受害者 inode，授予 root 拥有文件的 rwx。现在使用 `O_RDONLY|O_NOFOLLOW` fd 锁定每个条目的 inode，并在保持的 inode 上设置所有元数据（Linux 6.13+ `*xattrat` syscalls，或补丁 libacl 的 `*_at` 绑定，否则使用 `/proc/self/fd` 兼容路径）。如果既没有原语（BSDs、Solaris、macOS，或无 `/proc` 的 Linux 容器），则回退到基于路径的应用以保持 `--acls` 功能 —— 这是记录在案的残留，可通过 `refuse options = acls` 拒绝。

- **CVE-2026-53800 (MEDIUM)**: 发送者 `--remove-source-files` unlink 跟随父组件符号链接竞争 → 源树外任意文件删除。发送后 unlink 及其同文件安全检查通过相对于进程 CWD 的路径解析，因此不特权用户可以在文件发送后将源父组件竞争到符号链接，使更高权限的发送者（root `--remove-source-files` 运行，或不拒绝该选项的 daemon 模块）删除服务树外的文件。现在通过安全保持目录 fd 遍历在服务的模块根（daemon）或传输根 CWD（本地发送者）锚定解析，安全检查同样受限，且仅当启用 `--remove-source-files` 时计算每文件 dev/ino。

- **CVE-2026-53801 (MEDIUM)**: 发送者/daemon 目录扫描枚举逃离传输根/模块 → 树外披露。发送者通过累积路径的普通 `opendir()` 枚举每个源目录，未通过安全解析器（上一项的枚举兄弟节点，仅限制内容打开）。父组件在文件列表扫描和递归 `opendir()` 之间竞争到符号链接 —— 或在 daemon 跟随模式（`-L`/`--copy-dirlinks`/`--copy-unsafe-links`）中，指向模块外的模块内符号链接目录 —— 使更高权限发送者枚举树外目录并复制其条目名称、元数据和符号链接目标。现在通过保持在传输根/模块锚定的 `opendir` fd 限制目录扫描。

#### `support/rrsync`（受限 SSH 包装器）：

- **CVE-2026-53783 (HIGH)**: rrsync 受限目录逃逸。它使用 `realpath()` 验证每个参数，然后对相同名称 exec rsync（TOCTOU 窗口），并在受限子目录中启用危险选项。rrsync 现在 inode 锁定验证路径，并在锁定的 fd 处根化它传递给 rsync 的参数，拒绝 `--copy-unsafe-links`，强制 `--no-D`，并拒绝符号链接的 `--log-file`。该锁定依赖于 Linux `/proc/self/fd` 魔法链接绑定到打开的 inode，因此它是 Linux 特有的；在 BSDs、macOS、Solaris 和 Cygwin 上，rrsync 像往常一样传递 `realpath()` 验证的名称。有两个限制值得注意：在 `--relative` 下，只有传输名称开始的锚点被锁定，因此它下面的组件仍然可以被竞争，普通发送者参数的最终组件也不被锁定（rsync 不会在那里跟随符号链接，会改变该选项在受限目录中拒绝）。

- 失败的过滤器规则被逐字回显，即使规则来自合并文件的内容。per-directory 合并规则名称由对等体选择并通过协议传输，而不是在参数中，因此这允许对等体回显任何服务器进程可以打开且不是有效过滤器语法行的文件 —— 通过 `rrsync` 受限账户以及 daemon 模块，因为既有限制合并打开，包装器从未看到。文件中读取的规则语法错误现在报告文件和新行而不是文本；作为参数给出的规则仍然显示。`--debug=FILTER` 跟踪打印相同的文件衍生文本，因此 rrsync 现在拒绝对等体选择的 `--debug`（标准客户端从不发送）。为自己的服务器开启调试的操作者仍然可以看到规则文本。

- 不关闭合并路由本身，因为最坏形状不产生诊断：独占排除合并（`-` 修饰符）使文件的每行成为模式，因此没有语法错误，对等体读取其自身名称从文件列表中缺失的内容。通过不需要 `--delete` 和拉取中 verbose 的 `rrsync` 受限账户。现在限制打开而不是抑制披露：rsync 获得 `--confine-root=DIR`，拒绝解析到 DIR 外的操作者或对等体提供路径，且 rrsync 传递其受限目录。该目录内的合并文件仍然可以工作。daemon 已经通过其模块根具有此功能且不受影响。

#### Daemon 协议/身份：

- **CVE-2026-53786 (MEDIUM)**: 客户端提供的 `--filter` 合并文件绕过模块过滤器列表（它与模块前缀路径比较，从不匹配模块规则）。检查前现在剥离模块目录前缀。由 Mitchell Benjamin (Revamp Studio) 报告。

- **CVE-2026-53798 (MEDIUM)**: daemon 名称转换器将未知名称映射到 uid/gid 0（空响应被读取为 `atol("") == 0`）；使用 `fake super = yes` 存储的元数据成为 root 拥有。空/非数字响应现在视为查找失败。由 Mitchell Benjamin (Revamp Studio) 报告。

- **CVE-2026-53788 (MEDIUM)**: 包含换行符/CR 的对等体控制名称被逐字写入名称转换器行协议，允许请求注入。包含控制字符的转换器令词现在被拒绝。由 Mitchell Benjamin (Revamp Studio) 报告。

- **CVE-2026-53789 (MEDIUM)**: 恶意 daemon 发送者可以通过在隐式父目录上省略"无内容目录"标志扩大 `--delete` 范围，使接收者在它上面运行 `delete_in_dir()`。接收者上的隐式父目录现在强制为非内容。由 Mitchell Benjamin (Revamp Studio) 报告。

- **CVE-2026-53791 (CRITICAL)**: 使用 `proxy protocol = true`，直接连接（非通过受信任代理）的客户端可以发送 PROXY 头欺骗其源地址，绕过基于主机的访问控制。仅从配置的受信任代理对等体认可转发的地址。

#### 注入和内存安全：

- **CVE-2026-53790 (HIGH)**: 通过未引用对等体或主机控制值进行命令/参数注入 —— `RSYNC_CONNECT_PROG` `%H` 主机替换、daemon exec-hook `%RSYNC_*%` 扩展、rsync-ssl hostspecs，以及远程 shell 参数引用中缺少的换行符/CR。每个目的地现在被引用或验证（hook 转义限制在 shell 执行的 hooks，因此普通 daemon 字符串参数如 `path` 不受影响）。

- **CVE-2026-53792 (MEDIUM)**: 恶意接收者发送的校验和头具有块计数 > 0 但块长度 == 0，驱动发送者滚动匹配算术为负。零块长度现在被拒绝。

- **CVE-2026-53794 (MEDIUM)**: `--max-alloc=0` 禁用每分配大小限制（CVE-2024-12084 的防护），可以通过 wire 转发到未修补的 daemon。零 max-alloc 现在在客户端和 daemon 都被拒绝。由 Azizcan Dastan (Milenium Security) 报告。

#### 触发内存损坏（daemon 协议）

由 daemon 协议模糊测试找到的对等体触发的内存损坏，由 Greg Kroah-Hartman 报告。每个都是来自 wire 可触发的 WRITE，这就是为什么这些与相同传递中的崩溃-only 发现分开：

- **CVE-2026-70461 (HIGH)**: `add_implied_include()` 中有 1 字节堆越界写入，由对等体提供的过滤器规则驱动，其尾部反斜杠在大小调整时未被计数。

- **CVE-2026-70458 (HIGH)**: 标记为 `FLAG_HLINKED` 的文件条目的越界写入，接收者即使 `-H` 未生效也接受，因此随后写入的硬链接额外槽从未分配。

- **CVE-2026-70456 (HIGH)**: `read_args()` 中的堆越界写入，当对等体参数计数刚好落在 `maxargs` 上时 —— 尾部 NULL 越过数组结尾一个。

- **CVE-2026-70457 (MEDIUM)**: `parse_size_arg()` 错误格式中的攻击者选择偏移写入，通过转发给 daemon 的大 `--max-size` / `--min-size` / `--max-alloc` 可触达。

- **CVE-2026-70459 (MEDIUM)**: 每连接 daemon 子进程的乱指针读取崩溃，由构造的第一个增量文件列表驱动，其传输根为 "." 且非目录模式 —— `parent_ndx` 保持 0 而 `dir_flist` 仍为空，因此生成器解引用未写入槽。CVE-2026-43620 的伴随；在已发布 3.2.7、3.4.0 和 3.4.1 上重现。

#### Daemon 可用性和访问控制：

- **CVE-2026-70464 (HIGH)**: 未认证对等体可以完成 `@RSYNCD` 问候，然后永久阻塞 —— 发送无终止符的行，或将 NUL 终止参数逐字节流入 `read_args()` —— 保持每连接子进程打开超过模块的 `max connections` 限制。`timeout` 参数未覆盖它，因为 `set_io_timeout()` 运行在需要覆盖的 `read_args()` 调用之后。现在单独期限横跨两者，早期协议参数计数受限。由 Chamal De Silva 和 Michal Ruprich (Red Hat QE) 独立报告。

- **CVE-2026-70455 (HIGH)**: daemon 客户端可以通过 `--compress-threads` 请求任意 Zstandard 工作器计数；256 被测量为单个连接的 257 个线程。现在在 daemon 上限制为 8，而本地和远程 shell 调用保持操作者的值。由 Trail of Bits 的 Filipe Casal 与 OpenAI 合作发现、修复和测试。

- **CVE-2026-70453 (HIGH)**: `hash_search()` 中的二次 CPU 耗尽，来自构造的相等弱校验和链。链遍历现在受限。首先在公共 rsync 问题 #217 作为性能问题报告（2021，heyciao）；识别为安全问题，由 Stuart Inglis 限制和回归测试。这个已经是公开的，未 embargoed。

- **CVE-2026-70452 (HIGH)**: 配置的 hostname 无法解析时 `hosts deny` 失败 OPEN —— 启用 `forward lookup`（默认），无法解析的 deny token 允许它本应阻止的主机。现在失败关闭。CVE-2026-43617 的兄弟。由 Leonid Bugaev 报告。

- **CVE-2026-70463 (HIGH)**: `auth users` 忽略其文档化的逗号解析。带前导逗号，split 应该仅基于逗号，因此可以写包含空格组名；它也分割空白，因此命名此类组的 `deny` 或 `:ro` 规则被分解为两个无意义的 token 并永不触发。由 Andres Berbescu 报告。

- **CVE-2026-70460 (HIGH)**: 对等体提供的 `--partial-dir` 或 `--backup-dir` 通过路径名解析，因此模块内符号链接可以重定向它并将文件放置在 daemon 模块根外。这些路径现在受限。由 Omar Elsayed (seks99x) 报告。

#### 客户端侧：

- **CVE-2026-70462 (MEDIUM)**: 对等体提供的 `MSG_IO_TIMEOUT` 击败客户端自己的 I/O 超时 —— 大值溢出有符号算术，非正值完全禁用超时。接收时值现在限制，算术溢出安全。由 Z3R0S! (z3r0s6) 报告；非正值由 Leonid Bugaev 报告。

- **CVE-2026-70454 (MEDIUM)**: `rsync-ssl` 建立未认证 TLS 连接。在 stunnel 模式下，它既不需要 CA 验证也不绑定证书到请求的主机名，因此主动网络攻击者可以冒充服务器；openssl 后端在 3.2.0 到 3.2.3 有匹配的主机名间隙（2020 年由 Matt McCutchen 发现并修复）。stunnel 模式现在要求证书验证和主机名绑定，除非设置明确的不安全 opt-out，GnuTLS 后端现在保守拒绝而不是未验证使用（Greg Kroah-Hartman）。

#### 健壮性硬化（无 CVE 分配）：
`RSYNC_PROXY` CONNECT 请求和代理响应头长度受限，对等体请求的 xattr 扩展受限。

第二次源代码审计（由 Leonid Bugaev 报告）增强几个内存安全和健壮性路径：hashtable 和文件列表大小计算受保护免受 32 位整数溢出，对等体条目计数可以 otherwise 环绕为欠分配，`SIGUSR2` 处理程序现在 async-signal-safe（仅设置标志，将摘要/关闭工作推迟到安全 poll 点）。另外，xattr/ACL 元数据复制现在通过保持的 no-follow fd 读取 *源* 以及通过 fd 写入目的地 —— 关闭 `--copy-dest` 和备份源的父符号链接竞争，`--fake-super` 下的跨树操作者路径元数据应用现在 fd 锁定（先前它回退到基于路径的设置为 `fake super = yes` daemon staging 通过绝对 `--temp-dir`/`--backup-dir`）。

### 安全相关：

- 掩码对等体提供的 I/O 错误值到定义的 `IOERR_*` 位，both incoming `MSG_IO_ERROR` 消息（`io.c`）和文件列表尾部（`flist.c`），因此恶意对等体不能设置任意（未定义）错误标志，这些标志会存储在本地 `io_error` 并重新转发上游。（未定义的位从不到达退出代码，仅映射定义的位。）由 Leonid Bugaev 报告。

- 转义写入日志文件的文件名中的控制字符（CWE-117 日志注入）：传输的名称包含控制字节 —— C0（除 tab 外）和 C1 `0x80`-`0x9f`，包括 CSI `0x9b` —— 否则可以注入终端控制序列到管理员终端，当查看日志时。由 Leonid Bugaev 报告。

- 停止 `safe_arg()` 将未初始化字节泄漏到引用的文件名。在文件名模式，写入器抑制 wildcard 前的转义反斜杠，但 size 缓冲区的计数器为每个反斜杠预留槽，因此两者不一致并在返回字符串中留下未初始化堆字节 —— 这在 `--protect-args` 关闭时交给远程 shell。计数器现在镜像写入器，guarded 通配符测试 `f[1]` 也修复尾部反斜杠（先前 `strchr()` 匹配字符串终止符，因此反斜杠未加倍）。由 Leonid Bugaev 报告。

- 关闭 `--backup` 中的 `--safe-links` 绕过：当符号链接可以硬链接时，`make_backup()` 的链接/重命名快速路径将不安全（树外）符号链接硬链接到备份区域，并跳过复制路径应用的 `safe_symlinks` 检查，silent 保留符号链接 `--safe-links` 本应丢弃。safe-links 检查现在运行在快速路径之前，无法读取目标的符号链接失败关闭而不是 unchecked 备份。由 Leonid Bugaev 报告。

- 将操作者目录拥有遍历扩展到备份叶节点：`do_symlink_at()`（备份符号链接到操作者 `--backup-dir`）和 `do_rmdir_at()`（移除预存在备份目录）现在通过相同的拥有遍历解析其父目录，因此外国拥有父符号链接不再重定向备份符号链接创建或目录移除到备份树外。`--insecure-links`（或模块的 `insecure links = yes`）恢复旧的跟随。由 Omar Elsayed (seks99x) 报告。

- 通过 `robust_rename()` 中的跨文件系统（EXDEV）复制后备限制绝对操作者源/目的地到拥有遍历，因此竞争父符号链接不能重定向后备复制或源 unlink 到树外。由 Leonid Bugaev 报告。

- 限制 `hash_search()` 中每个 offset 检查的相等弱校验和块数量（问题 #217），因此构造或退化的校验和集，具有非常长的相等校验和链，不能驱动发送者每 offset 匹配验证二次膨胀（CPU DoS）。Stuart Inglis 修复。

### Bug 修复：

- 修复 `clean_fname()` 中 `..`-collapse 路径归一化的 off-by-one 错误。由 Leonid Bugaev 报告。

- AVX2 滚动校验和汇编（`--enable-roll-asm`）读取其给定缓冲区末尾多至 64 字节。循环软件管道化并预加载它折叠的 64 字节之后的 64 字节，因此最后一次迭代总是超过数据 —— 余数由构造小于 64 字节。它通常落在 rsync 映射窗口内的松弛中且未被注意；缓冲区结束于分页边界时，传输中 SIGSEGV，由 Roland Kletzing 在 macOS x86-64 报告。报告的校验和不变。

- 当目的地拒绝硬链接符号链接、设备节点、FIFO 或套接字时，`--link-dest` 不再失败传输。rsync 是否硬链接这些在构建时决定，在源树意外所在的文件系统上，一个主机可以持有两个答案 —— macOS 构建在 APFS 上，可以，备份到 HFS+，返回 ENOTSUP。此类条目现在被复制，正如它已经在不能链接它们的构建中等同，如同已经在该位置的普通文件；运行使用 exit 23，即使条目然后正确创建。后备覆盖任何拒绝，因为错误本身不识别一个：link(2) 记录 EPERM 用于无硬链接的文件系统和权限拒绝。仍待解决：在 `-H` 下，这样一组条目互相硬链接也需要目的地内的链接，其中目的地完全不能硬链接类型，第一个之后的成员仍然丢失。

- `--out-format` / `--log-file-format` 现在为 `%%` 发出字面 `%`，而不是错误解析后续字符（由 Leonid Bugaev 添加）；后续限制 `log_format_has()` 的宽度数字扫描以匹配 `log_formatted()`，关闭超过校验和域的 `%C` 读取。

- CVS `.cvsignore`（或 `-C`）文件，包含 `!` 清除列表令牌，不再以虚假的"规则有尾随字符"错误中止。由 Leonid Bugaev 报告。

- `--chmod=a+s` 现在设置 setuid 和 setgid 位，匹配 `chmod(1)`（它先前仅设置 setuid）。由 Leonid Bugaev 报告。

- 大小写不敏感通配符匹配（用于 daemon `hosts allow`/`hosts deny` 规则）现在折叠 `[...]` 括号表达式内的字符，而不仅是字面模式字符。由 Leonid Bugaev 报告。

### 行为变更：

- 非 daemon 接收者仅当符号链接由 root 或运行用户拥有时才跟随操作者命名的符号链接目录（例如 `rsync -a src/ /backup/` 其中 `/backup -> /mnt/disk`）；由其他 uid 符号链接的目的地现在被拒绝，关闭 chdir TOCTOU，攻击者将命名目的地竞争到符号链接。`--insecure-links` 恢复无条件跟随。

- 在无法通过 race-safe 方式在子目录中创建 unix 套接字的平台上（BSDs、macOS、Solaris，缺乏 `bindat()`），`--specials` 下传输的嵌套套接字被跳过，带警告而不是失败整个传输。顶级套接字不受影响。

- `proxy protocol = true` 且无 `proxy protocol hosts` 拒绝所有连接（失败关闭）；daemon 现在在启动时警告此情况。

- `support/rrsync` 在受限子目录中强制 `--no-D`（设备/特殊语义被剥离，因此普通 `rsync -a` 仍然工作）并拒绝 `--copy-unsafe-links`。

- 路径解析器现在通过单一 race-free 每组件 `O_NOFOLLOW` 遍历，在每台平台均匀跟随树内目录符号链接，因此 `-K` / `-L` / `-k` 和 `-R` 通过树内符号链接父目录在各地行为相同。
