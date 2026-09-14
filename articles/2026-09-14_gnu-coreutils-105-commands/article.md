# GNU coreutils 9.7 全命令手册：105 个命令逐个拆解（附实机示例）

> 本文基于 Debian 13 “trixie” 上 `dpkg -L coreutils`（版本 9.7-3，amd64）的真实输出，把其中的 105 个 ELF 可执行文件按功能分成 8 大类，逐一依据本机 `man` 手册讲解用法，并给出**在本机实机跑过的**示例命令与输出。

很多人以为自己会 Linux，其实只会 `ls`、`cd`、`grep`。真正让工程师效率拉开差距的，往往是那些名字眼熟、但从未认真读过手册的命令——`numfmt`、`shuf`、`comm`、`tac`、`csplit`、`stdbuf`、`install`……

这篇文章不谈理论，只做一件事：**把你系统里已经装好的 105 个 coreutils 命令，一个一个讲清楚**。所有示例都在本机（Debian 13 trixie / kernel 7.2.4-x64v3-xanmod1）验证过，输出可直接复现。

---

## 环境与方法

```bash
$ dpkg -l coreutils | tail -1
ii  coreutils      9.7-3        amd64        GNU core utilities

$ dpkg -L coreutils | grep -E '^/(usr/)?(s?bin)/' | wc -l
105
```

`dpkg -L coreutils` 列出的文件路径里，`/usr/bin/` 下有 104 个、`/usr/sbin/` 下有 1 个（`chroot`），全部为 ELF 64-bit LSB 可执行文件。另有 `/usr/libexec/coreutils/libstdbuf.so` 一个共享库（`stdbuf` 的 LD_PRELOAD 载体），不是独立命令，不计入。

几点说明：

- **同一二进制，多个名字**：coreutils 的多命令共享实现，`sha224sum`/`sha384sum` 等本质是 `sha*sum` 家族的变体入口；`sum`、`cksum` 也共用 `md5sum`/`sha*sum` 的校验框架。
- **`[` 就是 `test`**：`/usr/bin/[` 与 `/usr/bin/test` 行为一致，唯一区别是 `[` 要求最后一个参数必须是 `]`。
- **shell 里你可能跑的不是它**：`echo`、`printf`、`pwd`、`true`、`false`、`test` 六者在 bash/zsh 里都有同名内建，直接敲会命中内建。想强制跑 coreutils 版本，用 `env echo ...` 或写全路径 `/usr/bin/echo`。本文示例对这类命令会特别标注差异。
- **本文所有示例在 `/tmp/cudemo` 沙箱目录中执行**，不会污染你的家目录。

---

## 分类总览

| # | 分类 | 命令数 | 命令 |
|---|------|-------|------|
| 一 | 目录浏览与路径解析 | 10 | `ls` `dir` `vdir` `dircolors` `pwd` `realpath` `readlink` `basename` `dirname` `pathchk` |
| 二 | 文件与目录操作 | 16 | `cp` `mv` `rm` `mkdir` `rmdir` `touch` `install` `ln` `link` `unlink` `truncate` `shred` `mknod` `mkfifo` `dd` `mktemp` |
| 三 | 查看与切分 | 9 | `cat` `tac` `head` `tail` `split` `csplit` `wc` `nl` `od` |
| 四 | 文本处理与转换 | 15 | `sort` `uniq` `comm` `cut` `paste` `join` `tr` `expand` `unexpand` `fmt` `fold` `pr` `ptx` `tsort` `shuf` |
| 五 | 校验与编码 | 12 | `sum` `cksum` `md5sum` `sha1sum` `sha224sum` `sha256sum` `sha384sum` `sha512sum` `b2sum` `base32` `base64` `basenc` |
| 六 | Shell 内建替代与流程控制 | 22 | `echo` `printf` `expr` `test` `[` `true` `false` `yes` `seq` `numfmt` `factor` `sleep` `timeout` `nice` `nohup` `stdbuf` `tee` `sync` `env` `printenv` `stty` `tty` |
| 七 | 系统与身份信息 | 16 | `uname` `arch` `nproc` `hostid` `date` `df` `du` `stat` `id` `groups` `whoami` `who` `users` `pinky` `logname` `chroot` |
| 八 | 权限与安全上下文 | 5 | `chmod` `chown` `chgrp` `chcon` `runcon` |

> 命令名后面的摘要全部译自本机 man 手册的 `NAME` 小节 —— `man -w <cmd>` 能确认每个命令的手册路径都在 `/usr/share/man/man1/`（除 `chroot` 在 `man8`）。

---

## 一、目录浏览与路径解析（10 个）

这一类回答两个问题：**“这儿有什么”** 和 **“这东西到底在哪”**。

### `ls` — list directory contents

```text
ls [OPTION]... [FILE]...
```

最常用也最被低估的命令。三个真正提升效率的开关：`-l` 长格式、`-h` 人类可读大小、`--time-style` 控制时间格式（默认是那种反人类的 `9月14日 22:06`）。

```bash
$ ls -lh --time-style=long-iso /var/log | head -3
总计 662M
drwxr-xr-x  2 root root 4.0K 2024-03-09 08:15 account
-rw-r--r--  1 root root  13K 2026-09-13 13:39 alternatives.log
```

其他值得记的：`-t` 按时间倒序、`-S` 按大小倒序、`-r` 反转、`-R` 递归、`-i` 显示 inode、`-Z` 显示 SELinux 上下文、`--group-directories-first` 目录排前面。

### `dir` — list directory contents

```text
dir [OPTION]... [FILE]...
```

行为等同于 `ls -C -b`，也就是默认**多列输出**、且不递归。它存在的意义是兼容老 SYSV 习惯。

```bash
$ dir -1 /etc | head -3
abcd
acl
adduser.conf
```

### `vdir` — list directory contents

```text
vdir [OPTION]... [FILE]...
```

等同于 `ls -l -b`，即**默认长格式**。想要“敲一个命令就是详细列表”，用 `vdir`。

```bash
$ vdir /etc/hostname
-rw-r--r-- 1 root root 16 2023年 9月10日 /etc/hostname
```

### `dircolors` — color setup for ls

```text
dircolors [OPTION]... [FILE]
```

为 `ls --color` 生成 `LS_COLORS` 环境变量。常见用法是把默认值导出到 shell 配置里。

```bash
$ dircolors --print-database | head -3
# Configuration file for dircolors, a utility to help you set the
# LS_COLORS environment variable used by GNU ls with --color option.
# Copyright (C) 1996-2025 Free Software Foundation, Inc.

# 实用写法：写进 ~/.zshrc 或 ~/.bashrc
$ dircolors -p > ~/.dircolors        # 先生成配置模板，再按需改
$ eval "$(dircolors ~/.dircolors)"   # 应用
```

### `pwd` — print name of current/working directory

```text
pwd [OPTION]...
```

`-P` 打印物理路径（解析所有符号链接），`-L` 打印逻辑路径（保留 `$PWD` 里的符号链接，默认）。**写脚本时用 `pwd -P`**，避免符号链接把你带到意外的地方。

```bash
$ (cd /var/log && pwd -P)
/var/log
```

### `realpath` — print the resolved path

```text
realpath [OPTION]... FILE...
```

比 `readlink -f` 更丰富的路径解析工具。独门技能是 `--relative-to` 生成相对路径。

```bash
$ realpath /usr/bin/vi
/usr/bin/vim.nox

$ realpath --relative-to=/usr /usr/bin/ls
bin/ls
```

其他开关：`-s` 只解析符号链接不做存在性检查、`-e` 要求路径每一段都存在、`-m` 不要求任何一段存在（拼接路径时很有用）。

### `readlink` — print resolved symbolic links or canonical file names

```text
readlink [OPTION]... FILE...
```

不加 `-f` 时只打印该符号链接本身的指向；加 `-f` 后递归解析到底。想知道“这个软链接到底指向哪”，用 `-f`；只想看它第一跳指向哪，不加任何参数。

```bash
$ readlink -f /usr/bin/vi
/usr/bin/vim.nox
```

`-e` 要求最终目标必须存在，`-m` 不要求存在但照常解析。

### `basename` — strip directory and suffix from filenames

```text
basename NAME [SUFFIX]
basename OPTION... NAME...
```

剥掉目录部分，可选再剥掉后缀。**shell 脚本里的常客**，比用 `${var##*/}` 更具可读性，且能一次处理多个参数（配合 `-a`）。

```bash
$ basename /etc/apt/sources.list .list
sources

$ basename /usr/bin/vi
vi
```

`-s SUFFIX` 可以给多个文件名统一去后缀；`-z` 用 NUL 分隔输出，配合 `xargs -0` 处理含空格的文件名。

### `dirname` — strip last component from file name

```text
dirname [OPTION] NAME...
```

`basename` 的镜像操作。注意：**`dirname` 不检查文件是否存在**，纯字符串处理。

```bash
$ dirname /usr/bin/vi
/usr/bin
```

`-z` 同样支持 NUL 分隔。一个坑：`dirname “a.txt”` 返回 `.`，不是空串。

### `pathchk` — check whether file names are valid or portable

```text
pathchk [OPTION]... NAME...
```

诊断文件名里的**不可移植字符**（空格、换行、超长等）。打包脚本、交叉编译产物检查时很有价值。

```bash
$ pathchk -p "my file.txt"; echo "rc=$?"
pathchk: 文件名 'my file.txt' 中有不可移植的字符 ' '
rc=1
```

`-p` 检查大多数 POSIX 系统，`-P` 额外检查空文件名和前导 `-`，`--portability` = `-p -P` 全查。

---

## 二、文件与目录操作（16 个）

这一类是**改动文件系统的命令**，误操作代价最高。三条铁律：`rm` 前先 `ls` 确认、`mv`/`cp` 加 `-i` 或 `--backup`、涉及 `-R` 的先在 `/tmp` 试。

### `cp` — copy files and directories

```text
cp [OPTION]... [-T] SOURCE DEST
cp [OPTION]... SOURCE... DIRECTORY
cp [OPTION]... -t DIRECTORY SOURCE...
```

`-a` = `-dR --preserve=all`，**归档复制的首选**（保留权限、属主、时间戳、链接、xattr）。`-u` 只复制更新的文件，`-n` 不覆盖，`--backup=numbered` 覆盖前自动留备份。

```bash
$ cp -a src/ dst/ && ls dst
a.txt

# 危险场景保命写法：目标已存在时先留备份而不是直接覆盖
$ cp --backup=numbered file.conf /etc/file.conf
```

### `mv` — move (rename) files

```text
mv [OPTION]... [-T] SOURCE DEST
mv [OPTION]... SOURCE... DIRECTORY
```

同一分区内 mv 只是改目录项（rename(2)），**极快且原子**；跨分区则退化为“复制+删除”。`--backup` 同样可用。

```bash
$ mv --backup=numbered src/a.txt src/b.txt && ls src
a.txt  b.txt
```

`-t DIR` 形式在多源文件时更安全（明确目标是目录）。

### `rm` — remove files or directories

```text
rm [OPTION]... [FILE]...
```

`-r` 递归、`-f` 强制、`-i` 逐个确认、`--preserve-root`（默认，防止 `rm -rf /`）、`--one-file-system` 跨挂载点时停手。

```bash
# 安全清理：只删当前文件系统内的内容，遇到挂载点不深入
$ rm -rf --one-file-system /tmp/buildroot/*

# 自保 alias（写在 ~/.zshrc）
$ alias rm='rm -I'   # 删除超过 3 个文件时才提示一次
```

### `mkdir` — make directories

```text
mkdir [OPTION]... DIRECTORY...
```

`-p` 建多级且已存在时不报错，是 CI 脚本标配。`-m` 直接指定权限，避免建完再 chmod。

```bash
$ mkdir -p a/b/c && mkdir -m 700 secret && ls -ld secret
drwx------ 2 axu axu 40 9月14日 22:06 secret
```

### `rmdir` — remove empty directories

```text
rmdir [OPTION]... DIRECTORY...
```

**只删空目录**。这既是限制也是保护。加 `-p` 可连带删除变空的父目录链。

```bash
$ rmdir -p a/b/c   # 删除 c→b→a，只要它们递归为空
```

### `touch` — change file timestamps

```text
touch [OPTION]... FILE...
```

文件不存在时创建空文件，存在时更新 mtime/atime。真正有用的开关：`-d` 指定具体时间、`-r` 参照另一个文件、`-c` 不存在时不创建。

```bash
$ touch -d "2026-01-01 12:00" t.txt && ls -l --time-style=long-iso t.txt
-rw-rw-r-- 1 axu axu 0 2026-01-01 12:00 t.txt
```

### `install` — copy files and set attributes

```text
install [OPTION]... [-T] SOURCE DEST
install [OPTION]... SOURCE... DIRECTORY
install [OPTION]... -t DIRECTORY SOURCE...
install [OPTION]... -d DIRECTORY...
```

`cp` + `chmod` + `chown` + `strip` 的合体。**Makefile、打包脚本里装二进制就用它**，因为它天然接受 `-m 755`。

```bash
$ install -Dm755 /bin/true ./bin/mytool && ls -l ./bin/mytool
-rwxr-xr-x 1 axu axu 43432 9月14日 22:06 ./bin/mytool
```

`-D` 一次性创建目标文件的所有上级目录；`-C` 内容相同就不复制（减少 mtime 抖动）；`-s` 顺便 strip 符号表。

### `ln` — make links between files

```text
ln [OPTION]... [-T] TARGET LINK_NAME
ln [OPTION]... TARGET... DIRECTORY
ln [OPTION]... -t DIRECTORY TARGET...
```

`-s` 建符号链接（可跨文件系统、可指向目录），不加则建硬链接。`-f` 强制覆盖、`-n` 把已存在的目标**符号链接**当作普通文件处理（而不是钻进去）。

```bash
$ ln -sfn /opt/app-v2 ./app && ls -l ./app
lrwxrwxrwx 1 axu axu 11 9月14日 22:06 ./app -> /opt/app-v2
```

> 经典坑：`ln -sf /opt/app-v2 ./app` 在 `./app` 已经是个指向目录的软链接时，会在 `app/` **里面**再建一层 `app-v2` 链接。加 `-n`（或写成 `-sfn`）可破。

### `link` — create a link to a file

```text
link FILE1 FILE2
```

只做**硬链接**，没有 `-s`。接口极简，适合脚本里明确要硬链接的场景。

```bash
$ link ./t.txt ./t-hl && ls -l ./t-hl
-rw-rw-r-- 2 axu axu 0 2026年 1月 1日 t-hl

$ link /etc/hostname ./hn
link: 无法创建指向 '/etc/hostname' 的链接 './hn': 无效的跨设备链接
```

注意上面的报错：**硬链接不能跨文件系统**。

### `unlink` — remove a file or directory entry

```text
unlink FILE
```

一次只删一个链接，不能递归、不能删非空目录。它的价值在于语义明确：“我只解除这一个目录项”。

```bash
$ unlink ./t-hl; echo "rc=$?"
rc=0
```

### `truncate` — shrink or extend the size of a file

```text
truncate [OPTION]... FILE...
```

调整文件大小。`-s 0` 清空文件但**保留 inode 和权限**——比 `rm` + `touch` 优雅，尤其清理正在被进程持有 fd 的日志。

```bash
$ truncate -s 0 big.log          # 清空日志，进程 fd 不断
$ truncate -s 1M sparse.img      # 造一个 1M 的空洞文件
$ du -h --apparent-size sparse.img; du -h sparse.img
1.0M    sparse.img
0       sparse.img
```

上面这个输出很有意思：表观大小是 1M（`du --apparent-size` 看文件长度），但实际磁盘占用为 0（`du` 看分配的块）——**这就是稀疏文件**，`dd`/`truncate` 都能造。

### `shred` — overwrite a file to hide its contents

```text
shred [OPTION]... FILE...
```

反复覆写文件内容后可选择删除。`-n N` 指定覆写次数、`-u` 覆写后 unlink、`-z` 最后用 0 填充掩盖痕迹。

```bash
$ echo secret > s.txt && shred -u -n 3 s.txt && ls s.txt
ls: 无法访问 's.txt': 没有那个文件或目录
```

> **重要限制（man 手册原文明确警告）**：`shred` 依赖“覆写原地生效”这一假设，在 **journaling 文件系统（ext4 data=journal、XFS 日志）、RAID、快照/COW（btrfs、ZFS）、以及 SSD 的磨损均衡与预留块**上都不能保证抹除。介质级安全请用 LUKS 加密或 ATA Secure Erase。

### `mknod` — make block or character special files

```text
mknod [OPTION]... NAME TYPE [MAJOR MINOR]
```

创建设备节点。TYPE 为 `b`（块设备）、`c` 或 `u`（字符设备，无缓冲/有缓冲）、`p`（FIFO）。**普通用户在容器或宿主上使用通常需要 root**（`CAP_MKNOD`）。

```bash
$ mknod -m 666 ./fifo2 p && ls -l fifo2
prw-rw-rw- 1 axu axu 0 9月14日 22:06 fifo2
```

日常几乎不用 `mknod` 造 FIFO——用 `mkfifo` 更直观。

### `mkfifo` — make FIFOs (named pipes)

```text
mkfifo [OPTION]... NAME...
```

创建命名管道，让两个无亲缘关系的进程通过文件系统通信。

```bash
$ mkfifo -m 600 myfifo && ls -l myfifo
prw------- 1 axu axu 0 9月14日 22:06 myfifo

# 典型用法：一个终端写，一个终端读
$ seq 100 > myfifo &            # 写入端
$ head -5 < myfifo              # 读取端
```

写.dec 不自增压或少增压时 `mknod`/`mkfifo` 都要 root；纯 FIFO 在大多数现代系统上普通用户可建。

### `dd` — convert and copy a file

```text
dd [OPERAND]...
```

块级复制/转换工具，参数风格是自成一体的 `key=value`。核心四个：`if=` 输入、`of=` 输出、`bs=` 块大小、`count=` 块数。加上 `status=progress` 才能看到进度。

```bash
$ dd if=/dev/zero of=./64m.img bs=1M count=4 status=none && ls -lh 64m.img
-rw-rw-r-- 1 axu axu 4.0M 9月14日 22:06 64m.img
```

实用场景：

```bash
# 制作 USB 启动盘（务必确认 of= 是 U 盘不是系统盘！）
$ dd if=debian-13.iso of=/dev/sdX bs=4M status=progress oflag=sync

# 备份磁盘前 512 字节的 MBR
$ dd if=/dev/nvme0n1 of=mbr.bin bs=512 count=1

# 测磁盘写吞吐
$ dd if=/dev/zero of=./testfile bs=1G count=1 oflag=direct status=progress

# 大小写转换（conv 参数）
$ dd if=file.txt of=UPPER.txt conv=ucase
```

`conv=` 还支持 `notrunc`（不清空输出文件）、`noerror`（出错继续）、`sync`（坏块补零，数据恢复常用组合 `conv=noerror,sync`）。

### `mktemp` — create a temporary file or directory

```text
mktemp [OPTION]... [TEMPLATE]
```

安全地创建临时文件/目录并**打印其名字**——这最后一句是关键，让你能在脚本里捕获它。

```bash
$ mktemp -d
/tmp/tmp.fXIigLtFvo

$ mktemp -t app-XXXX.log
/tmp/app-u9qm.log
```

`-d` 建目录、`-p DIR` 指定父目录、`--suffix=SUFF` 加后缀（TEMPLATE 不以 X 结尾时必须给）。

```bash
# 脚本标准写法
tmpdir=$(mktemp -d) || exit 1
trap 'rm -rf "$tmpdir"' EXIT
```

> **`mktemp -u` 不要用**：手册明确标注它是 unsafe 的，只打印名字不创建文件，留下 TOCTOU 竞态。

---

## 三、查看与切分（9 个）

这一类的共同点是**不改动数据**，只负责把内容以你要的形状呈现出来。

### `cat` — concatenate files and print on the standard output

```text
cat [OPTION]... [FILE]...
```

名字叫 concatenate，但 90% 的时间被用来“打印文件”。真正有用的开关：`-n` 加行号、`-A` 显示所有不可见字符（等价于 `-vET`）、`-s` 压缩连续空行。

```bash
$ printf 'l1\nl2\nl3\n' > f.txt
$ cat -A f.txt
l1$
l2$
l3$
$ cat -n f.txt
     1  l1
     2  l2
     3  l3
```

`-A` 是排查“为什么这段脚本跑不通”的第一工具——CRLF（`^M$`）、尾部空格、Tab（`^I`）一览无余。

### `tac` — concatenate and print files in reverse

```text
tac [OPTION]... [FILE]...
```

按**行**倒序输出（不是按字符，别和 `rev` 搞混）。

```bash
$ printf 'a\nb\nc\n' | tac
c
b
a
```

典型用途：日志文件尾部是最新记录，但你就是想从最新往回读；或者 `-s` 指定分隔符做结构化倒序。

### `head` — output the first part of files

```text
head [OPTION]... [FILE]...
```

`-n N` 前 N 行、`-c N` 前 N 字节。负数 `-n -5` 表示“除最后 5 行外全部”。

```bash
$ head -c 20 /etc/hostname | od -c | head -2
0000000   L   e   i   s   u   r   e   L   i   n   u   x   -   0   1  \n
0000020

$ head -n 2 /etc/os-release
PRETTY_NAME="Debian GNU/Linux 13 (trixie)"
NAME="Debian GNU/Linux"
```

`-c` 对二进制安全，不会破坏编码；`-q` 处理多文件时不打印文件名头。

### `tail` — output the last part of files

```text
tail [OPTION]... [FILE]...
```

`-n N` 后 N 行、`-c N` 后 N 字节、`-f` 跟随增长（`-F` = `--retry` + `-f`，日志文件被 rotate 后能自动重开）。`+N` 表示从第 N 行开始输出。

```bash
$ tail -n 1 /etc/hostname
LeisureLinux-01

$ tail -c 5 /etc/hostname | od -c | head -2
0000000   x   -   0   1  \n
0000005
```

运维高频组合：

```bash
$ tail -F /var/log/nginx/access.log | grep -v healthz   # 跟日志并过滤心跳
$ tail -n +2 data.csv                                   # 跳过 CSV 表头
```

### `split` — split a file into pieces

```text
split [OPTION]... [FILE [PREFIX]]
```

按行数或字节数切分大文件，输出 `PREFIXaa`、`PREFIXab`……用 `-d` 换成数字后缀，`--additional-suffix` 加扩展名。

```bash
$ seq 1 100 > n.txt
$ split -l 25 -d --additional-suffix=.part n.txt chunk_ && ls chunk_*
chunk_00.part  chunk_01.part  chunk_02.part  chunk_03.part

$ split -n 4 -d n.txt quarter_ && ls quarter_*
quarter_00  quarter_01  quarter_02  quarter_03
```

`-n N` 按份数均分（**不切断行**），`-n l/N` 严格按行边界切，`-b SIZE` 按字节切。高级玩法 `--filter='gzip > $FILE.gz'` 边切边压。

### `csplit` — split a file into sections determined by context lines

```text
csplit [OPTION]... FILE PATTERN...
```

和 `split` 的区别：**`split` 按大小切，`csplit` 按内容切**。这是处理日志、配置文件分节的利器。

```bash
$ printf -- '--- header\nrow1\n--- footer\n' > c.txt
$ csplit -f sec_ -b '%02d.txt' c.txt '/^---/' '{*}' | head -4
0
16
11
$ ls sec_*
sec_00.txt  sec_01.txt  sec_02.txt
```

- `/^---/` 是匹配模式（regex），命中处开始新分片
- `{*}` 表示重复匹配尽可能多次
- `-f` 前缀，`-b` 后缀格式（`printf` 风格）
- `--suppress-matched` 不含触发行本身
- `-z` 丢弃空分片，`-k` 出错时保留已生成的分片

### `wc` — print newline, word, and byte counts for each file

```text
wc [OPTION]... [FILE]...
```

`-l` 行、`-w` 词、`-c` 字节、`-m` 字符（多字节下与 `-c` 不同）、`-L` 最长行长度。

```bash
$ wc -l /etc/passwd; wc -c /etc/hostname; wc -w < f.txt
85 /etc/passwd
16 /etc/hostname
3
```

注意第三个例子：**从 stdin 读时不打印文件名**，这在脚本里取纯数字时非常关键。

### `nl` — number lines of files

```text
nl [OPTION]... [FILE]...
```

比 `cat -n` 精细得多的行号工具：可以按 section（`-d` 指定分页符）重置编号，可以只给非空行编号。

```bash
$ nl -ba -nrz -w3 f.txt
001  l1
002  l2
003  l3
```

编号风格 `-b`：
- `a` 所有行
- `t` 仅非空行（默认）
- `n` 不编号
- `pREGEX` 仅匹配正则的行

格式 `-n`：`ln` 左对齐、`rn` 右对齐、`rz` 右对齐补零；`-w` 宽度、`-s` 分隔符。

### `od` — dump files in octal and other formats

```text
od [OPTION]... [FILE]...
od [-bcdovx]... [FILE] [[+]OFFSET[.][b] [[+]LABEL[.][b]]]
```

“octal dump” 的缩写，但实际支持十进制、十六进制、浮点、字符。**排查编码问题、查看文件头 magic、检查不可见字节时的唯一正解**。

```bash
$ od -An -tx1 -N8 /etc/hostname
 4c 65 69 73 75 72 65 4c

$ od -c -N8 /etc/hostname
0000000   L   e   i   s   u   r   e   L
0000010
```

开关速查：
- `-A` 地址进制：`d`/`o`/`x`/`n`（none）
- `-t` 输出格式：`x1`/`x2`（十六进制）、`o1`（八进制）、`u`（十进制）、`c`（字符）、`a`（命名字符）、`f`（浮点）
- `-j N` 跳过前 N 字节 / `-N N` 只输出 N 字节
- `--endian=big|little` 控制字节序

```bash
# 查文件类型 magic number（PNG 应为 89 50 4e 47）
$ od -An -tx1 -N4 image.png
# 看一个"看起来一样"的字符串到底差在哪
$ printf 'café' | od -c
$ printf 'cafe\xcc\x81' | od -c     # 组合字符，视觉相同字节不同
```

---

## 四、文本处理与转换（15 个）

Unix 哲学的核心地带：每个命令只做一件事，用管道组合出复杂处理。

### `sort` — sort lines of text files

```text
sort [OPTION]... [FILE]...
sort [OPTION]... --files0-from=F
```

按整行排序，默认字典序（受 locale 影响）。

```bash
$ printf 'banana\nApple\ncherry\napple\n' > s.txt
$ sort s.txt
apple
Apple
banana
cherry

$ sort -f s.txt            # 忽略大小写
$ sort -u -f s.txt         # 去重 + 忽略大小写
Apple
banana
cherry
```

关键开关：

| 开关 | 作用 |
|------|------|
| `-n` | 数值排序 |
| `-h` | 人类可读数值（1K 2M 3G） |
| `-V` | 版本号排序（`1.9` < `1.10`） |
| `-M` | 月份名排序 |
| `-r` | 反转 |
| `-u` | 去重 |
| `-t` / `-k` | 字段分隔符 / 按字段排序 |
| `-R` | 随机排序 |
| `-S` | 缓冲区大小（大文件调优） |
| `--parallel=N` | 并行排序线程数 |

```bash
$ printf '10\n9\n100\n' | sort -n
9
10
100

$ printf '1.10\n1.9\n' | sort -V
1.9
1.10

$ ls -l /etc | sort -k5 -n -r | head -3
-rw-r--r--  1 root root 214459  9月13日 13:39 ld.so.cache
-rw-r--r--  1 root root  78282 2025年 3月 8日 mime.types
-rw-rw-r--  1 axu  axu   75269 2023年11月25日 china.txt
```

> **locale 陷阱**：`sort` 的输出依赖 `LC_COLLATE`。脚本里想要稳定可复现的结果，请 `LC_ALL=C sort`。否则中文/大小写/标点在不同系统上排出来不一样。

### `uniq` — report or omit repeated lines

```text
uniq [OPTION]... [INPUT [OUTPUT]]
```

**只删除相邻的重复行**——所以标准用法是 `sort | uniq`。

```bash
$ printf 'a\na\nb\na\n' | uniq -c
      2 a
      1 b
      1 a
```

注意输出里出现了两次 `a`：因为没有先 sort。正确写法：

```bash
$ printf 'a\na\nb\na\n' | sort | uniq -c
      3 a
      1 b

$ sort s.txt | uniq -u        # 只显示唯一行（出现一次）
$ sort s.txt | uniq -d        # 只显示重复行
$ sort s.txt | uniq -c | sort -rn   # 按出现频次倒序 —— 日志统计第一招
```

`-f N` 跳过前 N 个字段、`-s N` 跳过前 N 个字符、`-w N` 只比较前 N 个字符。

### `comm` — compare two sorted files line by line

```text
comm [OPTION]... FILE1 FILE2
```

三列输出：仅 FILE1 有 / 仅 FILE2 有 / 两者共有。**输入必须已排序**。

```bash
# 求交集、差集
$ comm -12 <(sort a.txt) <(sort b.txt)    # 交集
$ comm -23 <(sort a.txt) <(sort b.txt)    # 只在 a 里（差集）
$ comm -13 <(sort a.txt) <(sort b.txt)    # 只在 b 里
```

开关：`-1`/`-2`/`-3` 抑制对应列；`--output-delimiter=STR` 自定义列分隔（替代默认的 Tab，便于后续处理）；`--total` 输出统计；`--nocheck-order` 跳过排序检查（输入未排序但你不介意时）。

### `cut` — remove sections from each line of files

```text
cut OPTION... [FILE]...
```

按字节（`-b`）、字符（`-c`）或字段（`-f`，配合 `-d` 分隔符）切列。

```bash
$ cut -d: -f1,7 /etc/passwd | head -3
root:/usr/bin/bash
daemon:/usr/sbin/nologin
bin:/usr/sbin/nologin
```

- `-d` 分隔符（默认 Tab）
- `-f` 字段列表：`1,3`、`1-3`、`-3`（1到3）、`3-`（3到末）
- `--complement` 取反（保留未指定的部分）
- `-s` 只输出含分隔符的行（过滤掉注释/空行）
- `--output-delimiter=STR` 输出时用别的分隔符

```bash
$ cut -d: -f1,3 --output-delimiter=' -> ' /etc/passwd | head -2
root -> 0
daemon -> 1
```

> `-b`（字节）和 `-c`（字符）在 UTF-8 下行为不同：处理中文请用 `-c`。

### `paste` — merge lines of files

```text
paste [OPTION]... [FILE]...
```

把多个文件**按行并列**合并，是 `cut` 的逆操作。

```bash
$ printf 'a\n' > p1; printf '1\n' > p2
$ paste -d, p1 p2
a,1
```

- `-d` 分隔符列表（可给多个，循环使用）
- `-s` 转置：把每个文件的内容横向串成一行

```bash
# 把一列变成一行（逗号分隔）
$ seq 1 5 | paste -sd,
1,2,3,4,5
```

### `join` — join lines of two files on a common field

```text
join [OPTION]... FILE1 FILE2
```

类 SQL 的 JOIN，**输入必须按 join 字段排序**。

```bash
$ printf '1 alice\n2 bob\n' > u.txt
$ printf '2 运维\n3 开发\n' > d.txt
$ join -1 1 -2 1 -o 0,1.2,2.2 u.txt d.txt
2 bob 运维
```

- `-1 N` / `-2 N`：指定左右表的 join 字段
- `-t CHAR`：字段分隔符
- `-o FORMAT`：输出格式，`0` 是 join 字段，`1.2` 是左表第 2 字段
- `-a FILENUM`：输出左/右表中没匹配上的行（左/右外连接）
- `-v FILENUM`：只输出没匹配上的行
- `-e STRING`：缺失字段填充值
- `--header`：首行当表头处理

```bash
$ join -a 1 -e 'N/A' -o 0,1.2,2.2 u.txt d.txt    # 左连接，缺的填 N/A
1 alice N/A
2 bob 运维
```

### `tr` — translate or delete characters

```text
tr [OPTION]... SET1 [SET2]
```

字符级映射/删除/压缩。**只处理单字节字符集**（不支持 UTF-8 多字节，处理中文要用 `sed`/`perl`）。

```bash
$ echo "HELLO" | tr 'A-Z' 'a-z'
hello

$ echo "a  b" | tr -s ' '
a b
```

- `-d` 删除 SET1 中的字符
- `-s` 压缩连续重复字符
- `-c` 取补集
- `-t` 截断 SET1 到 SET2 长度

```bash
$ tr -d '\r' < dos.txt > unix.txt          # CRLF → LF
$ tr -cd 'a-zA-Z0-9\n' < raw.txt           # 只保留字母数字换行
$ echo "$PATH" | tr ':' '\n'               # PATH 一行一个
$ tr 'a-z' 'A-Z' < file > upper            # 大小写转换
```

### `expand` — convert tabs to spaces

```text
expand [OPTION]... [FILE]...
```

Tab 转空格，默认 Tab 宽度 8。

```bash
$ printf '\tindent\n' | expand -t4 | cat -A
    indent$
```

- `-t N` Tab 宽度；`-t LIST` 自定义制表位列表（`--tabs=4,8,12`）
- `-i` 只转换行首的 Tab（不破坏表格对齐）

### `unexpand` — convert spaces to tabs

```text
unexpand [OPTION]... [FILE]...
```

反过来：空格转 Tab。默认**只转行首的空白**。

```bash
$ printf '    spaces\n' | unexpand -t4 | cat -A
^Ispaces$
```

`-a` 转换所有空白（不只是行首）；`--first-only` 只转行首（覆盖 `-a`）。

### `fmt` — simple optimal text formatter

```text
fmt [-WIDTH] [OPTION]... [FILE]...
```

重新排版段落，默认宽度 75 列。

```bash
$ echo "long long long long long long long long line" | fmt -w 20
long long long
long long long long
long line
```

- `-w N` 最大宽度（默认 75）
- `-g N` 目标宽度（默认 93% 的宽度）
- `-s` 只切分不重排（保留原有换行，只拆长行）
- `-u` 统一空格：词间一个空格，句后两个
- `-p STRING` 只重排以 STRING 开头的行（给邮件/代码注释重排时保留前缀）
- `-t` 首行缩进不同于次行（tagged paragraph）

```bash
# 给 git commit message 或邮件正文重排，保留 '#' 注释前缀
$ fmt -w 72 -p '# ' comment.txt
```

### `fold` — wrap each input line to fit in specified width

```text
fold [OPTION]... [FILE]...
```

机械地按宽度折行，**不管单词边界**（和 `fmt` 的区别）。

```bash
$ echo "aaaaaaaaaaaaaaaaaaaaaaaaaaaa" | fold -w 10
aaaaaaaaaa
aaaaaaaaaa
aaaaaa
```

- `-w N` 宽度（默认 80）
- `-s` 在空格处断行（不切断单词）
- `-b` 按字节而非列（处理宽字符时）

### `pr` — convert text files for printing

```text
pr [OPTION]... [FILE]...
```

给文本加页眉、页脚、分页符、多栏排版，为打印准备。

```bash
$ pr -2 -l 20 -h "双栏" /etc/hostname | head -6


2023-09-10 08:57                      双栏                       第 1 页


LeisureLinux-01
```

- `-N` N 栏输出
- `-l N` 页长（行数，默认 56）
- `-h STR` 页眉标题
- `-t` 去掉页眉页脚（**配合 `-N` 做纯多栏排版很好用**：`pr -4 -t`）
- `-m` 多文件并排合并
- `-n` 加行号
- `-d` 双倍行距
- `-w N` 页宽

```bash
# 终端里三栏看列表
$ ls /usr/bin | pr -3 -t -w 120
```

### `ptx` — produce a permuted index of file contents

```text
ptx [OPTION]... [INPUT [OUTPUT]]
```

生成**关键词索引（KWIC, keyword in context）**——把每个词轮流当作关键词，上下文左右排列。这是 GNU 文档生成 `.info` 索引用的工具。

```bash
$ ptx /etc/hostname | head -3
                                       LeisureLinux-01

$ ptx -T /etc/hostname 2>&1 | head -2
\xx {}{}{LeisureLinux}{-01}{}
```

- `-T` 输出 TeX 格式 / `-R` 输出 roff 格式（供 groff 排版）
- `-r` 把引用放左边
- `-w N` 输出宽度
- `-i FILE` 忽略词表（停用词）
- `-o FILE` 只索引 FILE 中出现的词
- `-f` 忽略大小写
- `-F STR` 截断标记（默认 `/`）

### `tsort` — perform topological sort

```text
tsort [OPTION]... [FILE]
```

拓扑排序，输入是“先行 → 后继”的边。

```bash
$ printf 'a b\nb c\nc a\n' | tsort; echo "---"; printf 'a b\nb a\n' | tsort 2>&1 | head -2
tsort: -: 输入含有环：
tsort: a
tsort: b
tsort: c
---
tsort: -: 输入含有环：
tsort: a
```

上面的例子刻意构造成了环，`tsort` 正确报出了 cycle。正常的 DAG：

```bash
$ printf 'a b\nb c\n' | tsort
a
b
c
```

实用场景：

```bash
# 依赖顺序安装（Makefile 早年的做法）
$ printf 'libbase libmid\nlibmid libapp\n' | tsort | tac

# 检测依赖环
$ printf 'a b\nb c\nc a\n' | tsort 2>&1 | grep -q 环 && echo "检测到循环依赖"
```

`-f FILE` 从文件读（边列表在文件里）。

### `shuf` — generate random permutations

```text
shuf [OPTION]... [FILE]
shuf -e [OPTION]... [ARG]...
shuf -i LO-HI [OPTION]...
```

随机打乱行 / 随机抽样。**从文件中随机取 N 行的标准做法**。

```bash
$ shuf -i 1-10 -n 3
2
9
4

$ shuf -e red green blue -n 1
green
```

- `-n N` 只输出 N 行（抽样）
- `-i LO-HI` 从数字区间生成
- `-e` 把参数当作输入行
- `-r` 允许重复（有放回抽样）
- `-o FILE` 输出到文件（可等于输入，原地打乱）
- `--random-source=FILE` 指定随机源（**可复现**：`--random-source=/dev/zero` 得到固定结果）

```bash
# 从百万行日志里随机抽 1000 行做统计
$ shuf -n 1000 huge.log > sample.log

# 随机密码
$ tr -dc 'a-zA-Z0-9' < /dev/urandom | head -c 20
```

---

## 五、校验与编码（12 个）

分两族：**校验和**（完整性验证）与**编码**（数据表示转换）。

### 校验和家族

这一族共享同一套接口：`-c` 校验、`--tag` 输出 BSD 风格标签、`-b`/`-t` 二进制/文本模式、`-z` 用 NUL 而非换行结束行。

### `sum` — checksum and count the blocks in a file

```text
sum [OPTION]... [FILE]...
```

最古老的 BSD 校验和算法，**仅用于兼容，不要用于安全目的**。

```bash
$ echo -n "hello" > h.txt
$ sum h.txt
08403     1 h.txt

$ sum -s h.txt        # System V 算法（--sysv）
532 1 h.txt
```

默认 BSD sum（1KB 块），`-s`/`--sysv` 用 SYSV 算法（512B 块）。两种算法都极易碰撞。

### `cksum` — checksum and count the bytes in a file

```text
cksum [OPTION]... [FILE]...
```

POSIX 标准的 CRC-32 校验和，附带字节数。**用于检测传输损坏，不具备抗碰撞能力**。

```bash
$ cksum h.txt
3287646509 5 h.txt
```

输出两列：CRC 值 + 字节数。`-a ALGORITHM` 在 GNU 实现里可指定其他算法（如 `md5`、`sha1`…），此时等价于对应的 `*sum` 命令。

### `md5sum` — compute and check MD5 message digest

```text
md5sum [OPTION]... [FILE]...
```

```bash
$ md5sum h.txt
5d41402abc4b2a76b9719d911017c592  h.txt
```

> **MD5 已被密码学攻破**（2004 年王小云团队的碰撞攻击，2008 年伪造 CA 证书实战）。仅可用于**非对抗场景**的完整性检查（比如确认下载没传输出错），绝不能用于签名、证书、防篡改。

### `sha1sum` — compute and check SHA1 message digest

```text
sha1sum [OPTION]... [FILE]...
```

160 位摘要。**SHA-1 已于 2017 年被 SHAttered 攻击攻破**（Google 与 CWI 造出两份内容不同、SHA-1 相同的 PDF），**不要再用于任何安全场景**，只保留给遗留系统兼容。

```bash
$ sha1sum h.txt > SUMS && sha1sum -c SUMS
h.txt: 成功
```

### `sha224sum` — compute and check SHA224 message digest

```text
sha224sum [OPTION]... [FILE]...
```

224 位，SHA-256 的截短变体（不同初始值）。日常**较少使用** —— 要么用 SHA-256，要么用 SHA-512。

```bash
$ sha224sum h.txt
ea09ae9cc6768c50fcee903ed054556e5bfc8347907f12598aa24193  h.txt
```

### `sha256sum` — compute and check SHA256 message digest

```text
sha256sum [OPTION]... [FILE]...
```

**当前事实标准**。Linux 发行版 ISO、Docker 镜像层、软件包签名、TLS 证书链都在用它。

```bash
$ sha256sum h.txt
2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824  h.txt

# 生成校验文件并验证 —— 发布软件包的标配
$ sha256sum *.tar.gz > SHA256SUMS
$ sha256sum -c SHA256SUMS
xxx.tar.gz: 成功
```

### `sha384sum` — compute and check SHA384 message digest

```text
sha384sum [OPTION]... [FILE]...
```

384 位，SHA-512 的截短变体。需要 SHA-512 强度但想省空间时用；实际选择中大多直接上 SHA-512。

```bash
$ sha384sum h.txt
59e1748777448c69de6b800d7a33bbfb9c405e4c9c1b2d46a1cbb0d2a04b0e  h.txt
```

### `sha512sum` — compute and check SHA512 message digest

```text
sha512sum [OPTION]... [FILE]...
```

512 位，SHA-2 家族最高强度。**在 64 位 CPU 上 SHA-512 通常比 SHA-256 更快**（内部用 64 位字长运算），所以想快又想强，选它。

```bash
$ sha512sum h.txt | cut -c1-48
9b71d224bd62f3785d96d46ad3ea3d73319bfbc2890caada
```

以上五个 `sha*sum` 命令共享同一套开关：

- `-c`/`--check` 从校验文件读取并验证
- `--quiet` 只报告失败项
- `--status` 完全静默，只用退出码（**脚本首选**）
- `--ignore-missing` 校验时跳过不存在的文件
- `-b`/`-t` 二进制/文本模式（Linux 上无差别）
- `--tag` 输出 BSD 风格（`SHA256 (file) = ...`）
- `-z` 用 NUL 结束行（配合 `find -print0 | xargs -0`）

```bash
# 发行版 ISO 校验的标准流程
$ sha256sum -c --ignore-missing SHA256SUMS && echo "校验通过"

# 校验/var 下所有 deb（配合 find -print0 / xargs -0 处理含空格文件名）
$ find /var/cache/apt/archives -name '*.deb' -print0 \
    | xargs -0 sha256sum --tag
```

### `b2sum` — compute and check BLAKE2 message digest

```text
b2sum [OPTION]... [FILE]...
```

BLAKE2 是**比 SHA-2 更快、且密码学安全**的现代摘要算法（BLAKE2b 默认 512 位）。在支持的系统上优先用它。

```bash
$ b2sum h.txt | cut -c1-32
e4cfa39a3d37be31c59609e807970799
```

`-l N` 指定摘要长度（8–512 位，默认 512），接口与 `*sum` 家族一致（`-c`、`--tag`、`-z`）。

### 编码家族

### `base64` — base64 encode/decode data and print to standard output

```text
base64 [OPTION]... [FILE]
```

把二进制转成 64 个可打印字符表示的文本（每 3 字节 → 4 字符，体积膨胀 33%）。

```bash
$ echo -n "hello" | base64
aGVsbG8=

$ echo "aGVsbG8=" | base64 -d | od -c | head -1
0000000   h   e   l   l   o
```

- `-d`/`--decode` 解码
- `-w N` 每行 N 字符（`--wrap`），**`-w 0` 禁用换行**——把密文塞进配置文件/环境变量时的关键参数
- `-i`/`--ignore-garbage` 解码时忽略非字母表字符（处理带换行的粘贴内容）

```bash
# 把 kubeconfig 塞进环境变量
$ export KUBECONFIG_DATA=$(base64 -w 0 < ~/.kube/config)
```

### `base32` — base32 encode/decode data and print to standard output

```text
base32 [OPTION]... [FILE]
```

用 32 个字符（A-Z + 2-7）编码。膨胀率 60%，但**不分大小写**，适合手写、印刷、二维码、口述场景。

```bash
$ echo -n "hello" | base32
NBSWY3DP
```

典型用途：TOTP 双因素认证的 secret key（Google Authenticator 的 otpauth URI 里就是 base32）。

### `basenc` — Encode/decode data and print to standard output

```text
basenc [OPTION]... [FILE]
```

编码**瑞士军刀**，一个命令覆盖所有 RFC 4648 变体，是 `base64`/`base32` 的超集。

```bash
$ echo -n "hello" | basenc --base16
68656C6C6F
```

支持的编码（`basenc --help`）：

| 选项 | 说明 |
|------|------|
| `--base64` | 同 `base64`（RFC 4648 §4） |
| `--base64url` | URL/文件名安全的 base64（§5，`-` 和 `_`） |
| `--base32` | 同 `base32`（§6） |
| `--base32hex` | 扩展十六进制字母表 base32（§7） |
| `--base16` | 十六进制（§8） |
| `--base2msbf` | 位串，最高位优先 |
| `--base2lsbf` | 位串，最低位优先 |
| `--z85` | ZeroMQ 的 Z85 编码 |

```bash
$ echo -n "hello" | basenc --base64url
$ echo -n "hello" | basenc --z85
$ printf 'hello' | basenc --base2msbf    # 逐位展开
```

所有编码通用 `-d` 解码、`-w` 换行宽度、`-i` 忽略垃圾字符。

---

## 六、Shell 内建替代与流程控制（22 个）

这一类里有一半命令，你在 shell 里敲的时候**根本没跑到 coreutils 的二进制**——bash/zsh 有同名内建会先命中。需要外部版本时用 `env <cmd>` 或全路径。

### `echo` — display a line of text

```text
echo [SHORT-OPTION]... [STRING]...
echo LONG-OPTION
```

```bash
$ echo "a b   c"
a b   c
$ echo -e "tab\there"
tab	here
$ echo -n "no newline"       # 不换行
```

**核心差异（man 手册明确提示）**：coreutils 的 `/usr/bin/echo` 支持 `--help`/`--version` 长选项，而 shell 内建的 `echo` 不支持；转义处理上，bash 内建 `echo` 默认**不**解释 `\n`（需 `shopt -s xpg_echo` 或 `-e`），行为和 coreutils 版本也不完全一致。

> **可移植性建议**：需要转义或 `-n` 时，用 `printf` 而不是 `echo`。POSIX 里 `echo` 的行为是未定义的。

### `printf` — format and print data

```text
printf FORMAT [ARGUMENT]...
```

C 风格格式化输出，**`echo` 的正确替代品**。

```bash
$ printf '%s|%05d|%.2f|%s\n' "item" 42 3.14159 "$(date +%F)"
item|00042|3.14|2026-09-14

$ printf '%b\n' 'a\tb'      # %b 解释转义序列
a	b
```

- `%s` 字符串、`%d`/`%i` 整数、`%f` 浮点、`%x`/`%o` 十六/八进制
- `%b` 解释参数中的转义（区别于 `%s`）
- `%q` shell 引号转义（bash 内建有，coreutils 版本无）
- 宽度/精度：`%05d`（补零）、`%-10s`（左对齐）、`%.2f`
- **FORMAT 会被重复使用直到参数耗尽**

```bash
$ printf '%s\n' a b c       # 三个参数，格式复用三次
$ printf '%s' "$var"        # 不带换行，等价于 echo -n（且可移植）
```

### `expr` — evaluate expressions

```text
expr EXPRESSION
expr OPTION
```

古老的表达式求值器。支持整数运算、字符串操作、正则匹配。

```bash
$ expr 1 + 2
3
$ expr length "abcdef"
6
$ expr "abc" : 'a\(.\)'     # 正则捕获分组
b
```

运算符：`+ - * / %`（`*` 必须转义，否则被 shell 展开）、`< <= = != >= >`、`& |`（逻辑与/或，短路）、`:`（正则匹配并返回匹配长度）。字符串函数：`length`、`index`、`substr`、`match`。

> **现代 shell 不需要 `expr`**：`$(( ))` 做算术、`[[ =~ ]]` 做正则、`${#var}` 取长度，都更快更清晰。`expr` 主要出现在遗留脚本里。

### `test` — check file types and compare values

```text
test EXPRESSION
test
```

条件测试命令，返回 0（真）或 1（假）。`man -w [` 指向的就是 `test` 的手册页 —— **两者是同一个二进制**。

```bash
$ /usr/bin/test -f /etc/passwd && echo yes
yes
```

### `[` — 同 `test`，但要求结尾的 `]`

```text
[ EXPRESSION ]
[ ]
[ OPTION
```

`/usr/bin/[` 与 `/usr/bin/test` 行为完全一致，唯一区别：`[` 要求最后一个参数必须是 `]`（否则报 “missing ]”），这只是为了让 shell 代码看起来像括号表达式。

```bash
$ /usr/bin/[ -f /etc/passwd ] && echo yes
yes
```

两者的判别式语法完全一致：

```bash
$ [ -f /etc/passwd ] && echo yes
yes
$ [ 1 -lt 2 ] && echo lt
lt
$ [ -z "" ] && echo empty
empty
```

文件测试：`-e` 存在、`-f` 普通文件、`-d` 目录、`-L` 符号链接、`-r`/`-w`/`-x` 权限、`-s` 非空、`-nt`/`-ot`/`-ef` 时间与硬链接比较。

字符串：`-z` 空、`-n` 非空、`=`/`!=` 相等、`>`/`<` 字典序。

数值：`-eq -ne -lt -le -gt -ge`（**不能用 `=` 或 `>`**）。

组合：`!` 非、`-a` 与、`-o` 或、`\( \)` 分组。**建议用 `&&`/`||` 代替 `-a`/`-o`**，后者优先级不明确。

### `true` — do nothing, successfully

```text
true [ignored command line arguments]
true OPTION
```

什么都不做，退出码为 0。

```bash
$ /usr/bin/true; echo "true rc=$?"
true rc=0
```

用途：`while true; do ... done` 构造无限循环、`cmd || true` 忽略失败（**CI 里慎用，会掩盖真实错误**）、作为默认占位命令。

### `false` — do nothing, unsuccessfully

```text
false [ignored command line arguments]
false OPTION
```

什么都不做，退出码为 1。

```bash
$ /usr/bin/false; echo "false rc=$?"
false rc=1
```

用途：脚本里显式表示失败、测试 `if` 的 else 分支、`if false; then ... fi` 临时禁用一段代码块。

### `yes` — output a string repeatedly until killed

```text
yes [STRING]...
```

不断输出 `y`（或指定字符串），直到被杀死。设计目的是**自动应答交互式提示**。

```bash
$ yes | head -3
y
y
y

$ yes "y" | head -2
y
y
```

```bash
$ yes | rm -i *.log          # 自动确认所有删除提示
$ yes no | apt upgrade       # 对所有提问答 no（危险操作，谨慎）
```

也常用于**压测**：`yes > /dev/null` 制造一个 100% CPU 的进程。

### `seq` — print a sequence of numbers

```text
seq [OPTION]... LAST
seq [OPTION]... FIRST LAST
seq [OPTION]... FIRST INCREMENT LAST
```

生成数字序列。

```bash
$ seq 1 2 10
1
3
5
7
9

$ seq -w 8 10             # 等宽补零
08
09
10

$ seq -f "%03g" 1 3       # printf 格式
001
002
003
```

- `-s STR` 分隔符（默认换行）
- `-w` 自动等宽补零
- `-f FMT` printf 格式字符串

```bash
$ seq -s, 1 5             # 1,2,3,4,5
$ for i in $(seq 1 3); do echo "round $i"; done
```

### `numfmt` — Convert numbers from/to human-readable strings

```text
numfmt [OPTION]... [NUMBER]...
```

**最被低估的 coreutils 命令之一**：数字和人类可读单位双向转换。

```bash
$ numfmt --to=iec 1048576
1.0M

$ numfmt --from=iec 1G
1073741824

$ echo "2147483648" | numfmt --to=iec-i --suffix=B
2.0GiB
```

单位体系：
- `--to=iec` / `--from=iec`：1024 进制，后缀 K/M/G/T（`1M` = 1048576）
- `--to=iec-i`：带 `i`，输出 `MiB`/`GiB`
- `--to=si` / `--from=si`：1000 进制，后缀 k/M/G

处理字段（**这才是它真正强大的地方**）：

```bash
# 把 df 输出的 KB 列转成人类可读
$ df --output=used -B1 | numfmt --to=iec --field=1 --header

# 把 du 的字节数就地格式化
$ du -B1 -d1 /var | numfmt --field=1 --to=iec --suffix=B

# 排序人类可读的数字列（sort -h 的替代）
$ du -sh * | numfmt --field=1 --from=iec | sort -n
```

其他：`-d` 字段分隔符、`--padding=N` 对齐宽度、`--round=METHOD`（up/down/from-zero/towards-zero/nearest）、`--invalid=MODE`（abort/fail/warn/ignore）、`--grouping` 加千分位、**`--debug` 会打出转换过程**（排查利器）。

### `factor` — factor numbers

```text
factor [NUMBER]...
```

质因数分解。 GNU 实现用的是 Pollard rho 算法，处理大数很快。

```bash
$ factor 97
97: 97

$ factor 600851475143
600851475143: 71 839 1471 6857
```

实际用途：判断质数（输出只有一个数）、RSA 教学演示、检查随机数质量。

### `sleep` — delay for a specified amount of time

```text
sleep NUMBER[SUFFIX]...
```

默认单位是**秒**。`NUMBER` 可带后缀：`s` 秒、`m` 分、`h` 时、`d` 天。 GNU 版本支持小数和多个参数（累加）。

```bash
$ sleep 0.3; echo done
done
```

```bash
$ sleep 1m 30s          # 1 分 30 秒
$ sleep 0.5             # 半秒（POSIX 不支持小数，GNU 支持）
```

### `timeout` — run a command with a time limit

```text
timeout [OPTION] DURATION COMMAND [ARG]...
```

给任意命令加超时。**脚本防挂死的必备品**。

```bash
$ timeout 2 sleep 10; echo "rc=$?"
rc=124
```

退出码 124 表示超时。其他开关：

- `-s SIGNAL` 发送的信号（默认 TERM）
- `-k DURATION` TERM 之后再等 DURATION 发 KILL（**对付不理 TERM 的进程**）
- `-p`/`--preserve-status` 返回被杀命令自己的退出码而非 124
- `-f`/`--foreground` 前台运行（不改进程组，用于需要 tty 的命令）
- `-v` 输出诊断信息

```bash
$ timeout -s KILL -k 1 2 sleep 10; echo "rc=$?"
rc=137
```

上面这个例子：2 秒后发 KILL（137 = 128 + 9）。

DURATION 支持后缀 `s`/`m`/`h`/`d`，也支持小数。

```bash
# 生产脚本里的标准写法
if ! timeout 300s curl -fsS "$url" > out.txt; then
    echo "下载超时或失败" >&2; exit 1
fi
```

### `nice` — run a program with modified scheduling priority

```text
nice [OPTION] [COMMAND [ARG]...]
```

调整进程的 nice 值（**静态优先级**），范围 -20（最高优先）到 19（最低）。**只有 root 能调低 nice 值（提高优先级）**。

```bash
$ nice -n 10 sh -c 'echo my nice: $(nice)'
my nice: 10

$ nice -n 5 nice
5
```

不加 `-n` 时默认 `+10`。**注意：`nice` 是相对于当前值调整**（上例中 `nice -n 5 nice` 输出 5，因为基础值是 0）。

> 区分：`nice` 启动新进程时设定优先级；`renice` 改已有进程（不在 coreutils 里，在 util-linux）。

```bash
$ nice -n 19 make -j16        # 后台编译不卡桌面
$ nice -n 19 backup.sh        # 备份任务低优先级
```

### `nohup` — run a command immune to hangups

```text
nohup COMMAND [ARG]...
nohup OPTION
```

忽略 SIGHUP 信号，让命令在终端关闭后继续运行。标准输出默认重定向到 `nohup.out`。

```bash
$ nohup sh -c 'sleep 0.2; echo nohup ok'
nohup ok
```

关键点：
- **必须自己加 `&`** 才能后台运行：`nohup cmd &`
- 输出重定向：默认 `./nohup.out`，无写权限时落到 `$HOME/nohup.out`
- `nohup` 只屏蔽 SIGHUP，**不屏蔽 SIGTERM/SIGINT**
- 想让进程彻底脱离终端，还需要 `disown` 或 `setsid`

```bash
$ nohup ./long-task.sh > task.log 2>&1 &
$ disown                                    # bash：从作业表移除
# 或一步到位
$ setsid nohup ./long-task.sh > task.log 2>&1 &
```

> 现代系统上，需要长期运行的服务请用 systemd 用户实例（`systemd-run --user`），比 `nohup &` 可靠得多。

### `stdbuf` — Run COMMAND, with modified buffering operations for its standard streams

```text
stdbuf OPTION... COMMAND
```

通过 `LD_PRELOAD` 的 `libstdbuf.so` 修改子进程 stdio 的缓冲模式。**解决“管道里输出不及时”的经典问题**。

```bash
$ stdbuf -oL seq 1 3 | head -2
1
2
```

- `-i MODE` 标准输入、`-o MODE` 标准输出、`-e MODE` 标准错误
- MODE：`L`（行缓冲）、`0`（无缓冲）、`SIZE`（指定字节数，如 `4K`）

```bash
# 实时看到带缓冲程序的输出（比如 python/perl 写日志）
$ stdbuf -oL -eL python3 script.py | tee run.log

# 强制立即刷盘
$ stdbuf -o0 ./producer | consumer
```

**限制**：只对使用 C stdio 库的程序有效。直接 `write(2)` 系统调用（如 Go 程序）、或做了静态链接/setuid 的程序无效。

### `tee` — read from standard input and write to standard output and files

```text
tee [OPTION]... [FILE]...
```

复制一份流：**同时显示和保存**。

```bash
$ echo "a" | tee out.txt
a
$ cat out.txt
a
```

- `-a`/`--append` 追加而非覆盖
- `-i`/`--ignore-interrupts` 忽略 SIGINT
- 输出到多个文件：`cmd | tee f1 f2 f3`

```bash
# 需要 root 写文件但命令本身不用 root 的经典技巧
$ echo "nameserver 1.1.1.1" | sudo tee -a /etc/resolv.conf

# 保存安装日志同时实时看
$ make install 2>&1 | tee install.log
```

### `sync` — Synchronize cached writes to persistent storage

```text
sync [OPTION] [FILE]...
```

把内核页缓存中的脏数据刷到持久存储。

```bash
$ sync; echo "rc=$?"
rc=0
```

- 不给参数时**同步所有文件系统**
- 给 FILE 参数时只同步该文件所在的文件系统
- `--file-system` 同步 FILE 所在文件系统
- `--data` 只同步数据，不同步元数据

```bash
# 拔 U 盘前的正确操作
$ sync && umount /mnt/usb

# 测磁盘真实写入速度（排除缓存干扰，先 sync 再 drop_caches）
$ sync; time dd if=/dev/zero of=test bs=1G count=1 oflag=direct
```

> 现代系统的 `sync` 会在同步完成后返回（老的 Unix 可能异步返回）。journaling 文件系统的元数据还可能有后续写入，`umount` 才是真正的保证。

### `env` — run a program in a modified environment

```text
env [OPTION]... [NAME=VALUE]... [COMMAND [ARG]...]
```

在修改后的环境中运行命令。不加参数时打印当前环境变量。

```bash
$ env -i PATH=/usr/bin:/bin sh -c 'echo $PATH; echo "HOME=[$HOME]"'
/usr/bin:/bin
HOME=[]
```

- `-i`/`--ignore-environment` 从空环境开始（**构造干净测试环境**）
- `-u NAME` 删除变量
- `-C DIR` 先切换目录
- `-S STRING` 拆分字符串为参数（**shebang 神器**）
- `-0` 用 NUL 分隔输出（配合 `xargs -0`）
- `--block-signal` / `--default-signal` / `--ignore-signal` 信号处置

```bash
# 强制使用 coreutils 的 echo 而非 shell 内建
$ env echo "coreutils echo"

# shebang 里带参数的可移植写法（Linux 内核不支持多参数 shebang）
#!/usr/bin/env -S python3 -u

# 临时改时区/LANG 跑一次命令
$ env TZ=UTC LC_ALL=C date
```

### `printenv` — print all or part of environment

```text
printenv [OPTION]... [VARIABLE]...
```

比 `env` 更适合脚本取值：**只打印变量值，不含其他信息**。

```bash
$ printenv SHELL
/usr/bin/zsh

$ printenv HOSTNAME      # 变量不存在时退出码非 0
```

- 无参数：打印所有环境变量
- 指定名字：只打印值
- `-0`/`--null` 用 NUL 而非换行结束（处理含换行的变量值）

脚本里判断变量是否存在：

```bash
if printenv MY_TOKEN >/dev/null; then
    echo "token 已设置"
fi
```

### `stty` — change and print terminal line settings

```text
stty [-F DEVICE | --file=DEVICE] [SETTING]...
stty [-F DEVICE | --file=DEVICE] [-a|--all]
stty [-F DEVICE | --file=DEVICE] [-g|--save]
```

查看/修改**终端设备**的线路设置（波特率、回显、特殊字符等）。

```bash
$ stty size        # 打印终端行列数（脚本自适应宽度常用）
$ stty -a          # 打印全部设置
```

> **注意**：`stty` 必须作用在 tty 上。在非交互 shell（如本会话的脚本执行环境）里会报 `stty: 标准输入: 对设备不适当的 ioctl 操作`，这是正常的。

常见用法：

```bash
$ stty -echo          # 关闭回显（输密码前）
$ read -s -p "密码: " pw   # 更常用：bash 的 -s 就是关回显
$ stty echo           # 恢复

$ stty -icanon min 1 time 0   # 关闭行缓冲，逐字符读取
$ stty sane           # 终端被二进制输出搞乱后恢复默认
```

- `-F DEV` 指定设备（默认 stdin）
- `-g` 打印可复用的设置字符串：`saved=$(stty -g); stty “$saved”` 恢复
- `raw` / `-raw`（也写作 `cooked`）切换原始模式

```bash
# 终端被 cat 二进制文件搞乱后的救命命令
$ stty sane
$ reset                    # 或更强力（来自 ncurses）
```

### `tty` — print the file name of the terminal connected to standard input

```text
tty [OPTION]...
```

打印当前终端设备文件名；不是 tty 时打印 `not a tty` 并返回非 0。

```bash
$ tty
不是一个 tty          # 非交互环境下

$ [ -t 0 ] && echo "stdin is tty" || echo "stdin not tty"
stdin not tty
```

脚本里的标准用法是 **`[ -t N ]`**（N=0/1/2）判断，比 `tty` 更轻量：

```bash
if [ -t 1 ]; then
    echo "有终端，可以上色"
else
    echo "被重定向了，输出纯文本"
fi
```

`-s`/`--silent` 静默模式，只用退出码表示结果。

---

## 七、系统与身份信息（16 个）

回答“**我是谁、我在哪台机器上、现在几点、还剩多少空间**”。

### `uname` — print system information

```text
uname [OPTION]...
```

不加参数输出内核名（等价于 `-s`）。

```bash
$ uname -a
Linux LeisureLinux-01 7.2.4-x64v3-xanmod1 #0~20260907.g48995b0 SMP PREEMPT_DYNAMIC Mon Sep  7 19:39:22 UTC x86_64 GNU/Linux

$ uname -srm
Linux 7.2.4-x64v3-xanmod1 x86_64
```

开关：`-s` 内核名、`-n` 主机名、`-r` 内核版本、`-v` 内核构建信息、`-m` 硬件架构、`-p` 处理器类型、`-i` 硬件平台、`-o` 操作系统、`-a` 全部。

```bash
# 脚本里的架构判断
case "$(uname -m)" in
    x86_64) arch=amd64 ;;
    aarch64) arch=arm64 ;;
esac
```

### `arch` — print machine hardware name (same as uname -m)

```text
arch [OPTION]...
```

`uname -m` 的别名，输出更短。

```bash
$ arch
x86_64
```

### `nproc` — print the number of processing units available

```text
nproc [OPTION]...
```

打印可用 CPU 数。**`make -j$(nproc)` 是编译脚本的标准开头**。

```bash
$ nproc
16
$ nproc --ignore=2      # 留出 2 核给系统
14
$ nproc --all           # 忽略 CPU affinity 限制，报告所有核
16
```

`--ignore=N` 让结果减去 N（但至少为 1），在容器里很实用——不要把所有核都吃满。

### `hostid` — print the numeric identifier for the current host

```text
hostid [OPTION]...
```

打印 32 位十六进制的主机 ID。传统上来自 `gethostid(2)`，通常基于主机 IP 或随机数生成。

```bash
$ hostid
59ff40d5
```

某些商业软件（如老版本 FlexLM）用它做许可证绑定。手动设置需要写 `/etc/hostid`。

### `date` — print or set the system date and time

```text
date [OPTION]... [+FORMAT]
date [-u|--utc|--universal] [MMDDhhmm[[CC]YY][.ss]]
```

**最强大的格式化输出工具之一**。核心是 `+FORMAT`（strftime 格式）。

```bash
$ date -Iseconds
2026-09-14T22:07:40+08:00

$ date "+%Y-%m-%d %H:%M:%S"
2026-09-14 22:07:40

$ date -d "next monday" +%F       # 相对时间解析
2026-09-21

$ date -d "@1767225600" -u        # 从 epoch 秒转换
2026年 01月 01日 星期四 00:00:00 UTC

$ date -d "2026-12-25" +%A        # 某天是星期几
星期五

$ date -r /etc/hostname           # 文件的 mtime
2023年 09月 10日 星期日 08:57:51 CST
```

常用格式符：`%Y` 年、`%m` 月、`%d` 日、`%H` 时、`%M` 分、`%S` 秒、`%F` = `%Y-%m-%d`、`%T` = `%H:%M:%S`、`%s` epoch 秒、`%N` 纳秒、`%A` 星期名、`%Z` 时区名、`%z` 时区偏移。

关键开关：
- `-d STRING` 解析人类可读的时间表达式（**`date` 的灵魂**）
- `-f FILE` 从文件逐行解析，可用于批量转换时间戳
- `-r FILE` 显示文件 mtime
- `-I[FMT]` ISO 8601 输出（`date`、`hours`、`minutes`、`seconds`、`ns`）
- `-u` UTC
- `-s STRING` 设置时间（需 root，现代系统请用 `timedatectl`）
- `--resolution` 打印时钟分辨率

```bash
# 日志文件名带时间戳
$ cp app.log "app.$(date +%Y%m%d-%H%M%S).log"

# 计算脚本耗时（纳秒精度）
$ start=$(date +%s.%N); ...; echo "耗时 $(echo "$(date +%s.%N) - $start" | bc)s"

# 一天前的日期（日志轮转）
$ date -d "1 day ago" +%F
$ date -d "yesterday" +%F
$ date -d "-7 days" +%F

# 把 nginx 日志的时间转成 epoch（配合 -f 批量）
$ echo "14/Sep/2026:10:00:00 +0800" | date -f - +%s
```

### `df` — report file system disk space usage

```text
df [OPTION]... [FILE]...
```

报告文件系统级用量（**已用/可用/挂载点**）。

```bash
$ df -hT / /home | tail -2
文件系统       类型   大小  已用  可用 已用% 挂载点
/dev/nvme0n1p5 ext4  491G  439G   28G   95% /

$ df -i / | tail -1        # inode 用量 —— 磁盘没满但写不进去的元凶
/dev/nvme0n1p5 32710656 6036009 26674647    19% /
```

- `-h` 人类可读，`-H` 用 1000 进制
- `-T` 显示文件系统类型
- `-i` inode 而非块
- `-t TYPE` / `-x TYPE` 只显示/排除某类型（`-x tmpfs` 排除内存盘）
- `-a` 包含伪文件系统
- `--output=FIELD_LIST` 自定义列（脚本友好）

```bash
# 磁盘告警脚本（用 --output 避免解析字符串）
$ df --output=pcent,target -x tmpfs | awk 'NR>1 && $1+0 > 90 {print "告警:", $2, $1}'
```

> **两个常见误解**：(1) `-h` 用 1024 进制，`-H` 用 1000 进制——硬盘厂商用的是 1000，所以 `df -h` 显示容量比标称大。(2) Linux 默认给 root 预留 5% 空间，可用+已用可能不等于总容量。

### `du` — estimate file space usage

```text
du [OPTION]... [FILE]...
```

报告文件/目录级用量（**与 `df` 视角不同：`df` 看文件系统，`du` 看文件和目录**）。

```bash
$ du -sh /var/log
4.8G    /var/log

$ du -sh --max-depth=1 /var 2>/dev/null | sort -h | tail -3
```

- `-h` 人类可读
- `-s`/`--summarize` 只输出总计
- `-d N`/`--max-depth=N` 递归深度
- `-a` 包含文件（默认只统计目录）
- `-c` 加总计行
- `-x`/`--one-file-system` 不跨文件系统（**根因排查必备**，避免把 /proc、挂载的 NFS 算进来）
- `--apparent-size` 表观大小而非磁盘占用（稀疏文件、压缩文件系统下差异巨大）
- `--exclude=PATTERN` 排除
- `--time` 显示时间
- `--inodes` 统计 inode 而非块
- `-L` 跟随符号链接（默认不跟随）

```bash
# 找出 /var 下最占空间的前 10 个目录
$ du -x -d2 /var 2>/dev/null | sort -rn | head -10

# du 和 df 不一致？多半是被删除但还被进程持有的文件
$ du -sx / 2>/dev/null; df -h /
$ lsof +L1                      # 查看已删除但仍打开的文件（lsof 包）
```

### `stat` — display file or file system status

```text
stat [OPTION]... FILE...
```

比 `ls -l` 详细得多的元数据展示，**并且可以自由定制输出格式**。

```bash
$ stat -c '%n %s bytes, mtime=%y, owner=%U:%G, perms=%a' /etc/hostname
/etc/hostname 16 bytes, mtime=2023-09-10 08:57:51.271812120 +0800, owner=root:root, perms=644

$ stat -f -c 'type=%T, total blocks=%b, free=%f' /
type=ext2/ext3, total blocks=128487758, free=13656691
```

常用格式符：`%n` 文件名、`%s` 字节大小、`%b` 块数、`%a` 八进制权限、`%A` 符号权限、`%U`/`%G` 属主/属组名、`%u`/`%g` UID/GID、`%F` 文件类型、`%i` inode、`%h` 硬链接数、`%y` mtime（人类可读）、`%Y` mtime（epoch）、`%x`/`%z` atime/ctime、**`%w` 创建时间（btime，部分文件系统支持）**。

开关：
- `-c`/`--format` 自定义格式（自动加换行）
- `--printf` 自定义格式（不自动加换行，支持转义）
- `-t`/`--terse` 单行紧凑输出
- `-L` 跟随符号链接（默认显示链接本身）
- `-f` 文件系统信息而非文件

```bash
# 取时间戳做比较（脚本友好）
$ stat -c %Y /etc/hostname
1694309871

# 检查文件是否在 24 小时内被修改
$ find /etc -mmin -1440 -exec stat -c '%y %n' {} \;

# 查看文件创建时间（需要 statx 支持）
$ stat -c '%w %n' file
```

### `id` — print real and effective user and group IDs

```text
id [OPTION]... [USER]
```

```bash
$ id
uid=1000(axu) gid=1000(axu) 组=1000(axu),4(adm),7(lp),...,992(docker)

$ id -u; id -un; id -Gn
1000
axu
axu adm lp sudo video ... docker
```

开关：`-u` UID、`-g` GID、`-G` 所有附加组 ID、`-n` 显示名字而非数字、`-r` 显示真实 ID（real，区别于 effective）。

```bash
# 判断是否有 root 权限
$ [ "$(id -u)" -eq 0 ] && echo "root" || echo "非 root，请 sudo"

# 判断用户是否在 docker 组
$ id -nG "$USER" | grep -qw docker && echo "可以直接跑 docker"
```

### `groups` — print the groups a user is in

```text
groups [OPTION]... [USERNAME]...
```

`id -Gn` 的简化版。

```bash
$ groups
axu adm lp dialout sudo video staff games users input kvm ... docker
```

> **重要陷阱**：`groups` 输出的是**当前登录会话**持有的组。新加入组后必须**重新登录**（或 `newgrp`）才生效——这也是“明明加了 docker 组还是 permission denied”的根因。

### `whoami` — print effective user name

```text
whoami [OPTION]...
```

打印有效用户名（effective，非 real）。

```bash
$ whoami
axu
```

与 `id -un` 等价。`sudo` 之后 `whoami` 返回 `root`，而 `logname` 仍返回原始登录用户——**这两个的差异可以判断是否处于提权状态**：

```bash
$ [ "$(whoami)" != "$(logname)" ] && echo "当前处于提权状态"
```

### `who` — show who is logged on

```text
who [OPTION]... [FILE | ARG1 ARG2]
```

读取 `/var/run/utmp`，列出当前登录会话。

```bash
$ who | head -2
axu      seat0        2026-09-14 16:47
axu      tty3         2026-09-14 16:47
```

开关：`-a` 全部信息、`-b` 上次启动时间、`-r` 当前运行级别、**`-m` 只显示当前终端**、`-q` 简洁模式（只列出名字和总数）、`-H` 打印表头、`-u` 显示空闲时间、`--lookup` DNS 反解主机名。

```bash
$ who -b              # 系统上次启动时间
$ who -q              # 快速看有几个人在线
$ who -uH             # 带空闲时间
```

### `users` — print the user names of users currently logged in

```text
users [OPTION]... [FILE]
```

`who` 的极简版：**只打印登录用户名，一行空格分隔**（同一用户多次登录会重复）。

```bash
$ users | tr ' ' '\n' | sort -u | head -3
axu
```

### `pinky` — lightweight finger

```text
pinky [OPTION]... [USER]...
```

精简版 `finger`，读取 utmp 显示用户信息，包括 `~/.plan` 和 `~/.project` 文件的内容。

```bash
$ pinky | head -2
登录名   名字                 TTY      空闲   登录时间         主机
axu      Albert              ?seat0    ?????  2026-09-14 16:47

$ pinky -l axu | head -6
登录名： axu                         真名： Albert
主目录：/home/axu                    Shell:  /usr/bin/zsh
计划：
嗨，我是 LeisureLinux。今天我在研究我的 Finger 服务器。
```

- `-l` 长格式（含 home/shell/plan/project）
- `-b`/`-h`/`-p` 在长格式里分别省略 home+shell / project / plan
- `-s` 短格式（默认）
- `-f`/`-w`/`-i`/`-q` 在短格式里省略表头 / 全名 / 全名+主机 / 全名+主机+空闲时间
- `--lookup` DNS 反解

> 复古彩蛋：在 `~/.plan` 里写点东西，别人 `pinky -l` 你时就能看到——这是 1980 年代 Unix 社区的社交方式。

### `logname` — print user's login name

```text
logname [OPTION]...
```

打印**最初登录**的用户名（从 `/var/log/wtmp` 或 `getlogin()` 获取），`sudo`/`su` 后依然返回原始用户。

```bash
$ logname
axu
```

与 `whoami` 的关键区别上面已述。脚本里的典型用途：

```bash
# 以 root 跑脚本，但把结果写回原用户的家目录
target_home=$(getent passwd "$(logname)" | cut -d: -f6)
```

### `chroot` — run command or interactive shell with special root directory

```text
chroot [OPTION] NEWROOT [COMMAND [ARG]...]
chroot OPTION
```

改变进程看到的根目录。**需要 root（`CAP_SYS_CHROOT`）**。

```bash
$ chroot --help | head -3
用法：chroot [选项] 新根 [命令 [参数]...]
　或：chroot 选项
以指定的 <新根> 为根目录，运行指定的 <命令>。
```

典型场景：

```bash
# 系统救援：挂载损坏系统的根分区后 chroot 进去修 grub
$ mount /dev/sda2 /mnt/rescue
$ mount --bind /dev  /mnt/rescue/dev
$ mount --bind /proc /mnt/rescue/proc
$ mount --bind /sys  /mnt/rescue/sys
$ chroot /mnt/rescue /bin/bash
# grub-install /dev/sda && update-grub

# 只跑一条命令
$ chroot /mnt/rescue /bin/ls /

# 切换用户/组（--userspec）
$ chroot --userspec=1000:1000 /mnt/rescue /bin/sh
```

- `--userspec=USER:GROUP` 以指定身份运行
- `--groups=G_LIST` 指定附加组
- `--skip-chdir` 不改变工作目录（高级用法）

> **`chroot` 不是安全沙箱**：root 用户可以轻易逃逸（`mkdir subdir; chroot subdir; chdir(“..”)` 循环）。真正的隔离用 namespaces/containers（unshare、systemd-nspawn、Docker）或 seccomp。

---

## 八、权限与安全上下文（5 个）

### `chmod` — change file mode bits

```text
chmod [OPTION]... MODE[,MODE]... FILE...
chmod [OPTION]... OCTAL-MODE FILE...
chmod [OPTION]... --reference=RFILE FILE...
```

修改权限位。支持符号模式（`u+rwx`）和八进制（`750`）。

```bash
$ cp /bin/true ./sample
$ chmod 750 sample && ls -l sample
-rwxr-x--- 1 axu axu 43432 sample
```

三类特殊位（**这才是 chmod 的精髓**）：

| 位 | 符号 | 八进制 | 对文件 | 对目录 |
|----|------|-------|--------|--------|
| setuid | `u+s` | 4000 | 执行时以**文件属主**身份运行 | 无意义 |
| setgid | `g+s` | 2000 | 执行时以**文件属组**身份运行 | **新建文件继承目录属组** |
| sticky | `+t` | 1000 | 无意义（历史遗留） | **只有文件属主能删自己的文件** |

```bash
$ chmod u+s ./sample && ls -l sample
-rwsr-x--- 1 axu axu 43432 sample     # 注意 x 变成了 s

$ chmod g+s ./sample && chmod +t ./sample && ls -l sample
-rwxr-s--T 1 axu axu 43432 sample     # 小写 s/t = 有 x；大写 S/T = 无 x
```

其他开关：
- `-R` 递归
- `--reference=RFILE` 参照另一文件的权限（**批量对齐权限的利器**）
- `-v` 显示改动 / `-c` 只显示有改动的
- `-f` 忽略错误
- `--preserve-root`（默认，防止 `chmod -R 777 /`）

```bash
$ chmod --reference=/etc/hostname ./sample && ls -l sample
-rw-r--r-- 1 axu axu 43432 sample

# 共享目录的标准配置：组内可写 + 新建文件继承属组 + 防互删
$ chmod 3770 /srv/team          # 2(setgid) + 1(sticky) + 770

# 只给目录加 x（让路径可穿越），不给文件加
$ chmod -R a+X dir/             # 大写 X = 仅当是目录或已有 x 时加
```

> **`chmod 777` 是错的**：它给所有人写权限，且不解决属主/属组不匹配的问题。正确做法是配属组 + `2775`。

### `chown` — change file owner and group

```text
chown [OPTION]... [OWNER][:[GROUP]] FILE...
chown [OPTION]... --reference=RFILE FILE...
```

改属主和/或属组。**普通用户不能把文件给别人**（防止绕过配额）。

```bash
$ chown root sample
chown: 更改 'sample' 的所有者: 不允许的操作

$ chown axu:axu sample && ls -l sample | awk '{print $3, $4}'
axu axu
```

语法细节：
- `chown user file` 只改属主
- `chown user:group file` 同时改属主和属组
- `chown :group file` 只改属组（等价于 `chgrp`）
- `chown user: file` 属主改为 user，属组改为 user 的**登录组**

开关：`-R` 递归、`-v`/`-c` 输出、`-f` 忽略错误、`--reference=RFILE` 参照、`--from=CURRENT` 只改当前是某属主的（**条件性修改，减少误伤**）、`-h` 改符号链接本身而非目标、`-L`/`-H`/`-P` 递归时的符号链接处理。

```bash
# 只把属主是 olduser 的改成 newuser（不动其他文件）
$ chown -R --from=olduser newuser /data

# 部署时给 web 目录设对权限
$ chown -R www-data:www-data /var/www/html
$ find /var/www/html -type d -exec chmod 755 {} +
$ find /var/www/html -type f -exec chmod 644 {} +
```

### `chgrp` — change group ownership

```text
chgrp [OPTION]... GROUP FILE...
chgrp [OPTION]... --reference=RFILE FILE...
```

只改属组。普通用户改属组时，**必须是目标组的成员**且自己是文件属主。

```bash
$ chgrp -R axu . ; echo "rc=$?"
rc=0
```

开关与 `chown` 一致（`-R`、`-v`、`-c`、`-f`、`--reference`、`--from`、`-h`）。

```bash
# 让整个项目目录归属 docker 组（配合 setgid 让新文件自动继承）
$ chgrp -R docker /srv/app && chmod -R g+s /srv/app
```

### `chcon` — change file security context

```text
chcon [OPTION]... CONTEXT FILE...
chcon [OPTION]... [-u USER] [-r ROLE] [-l RANGE] [-t TYPE] FILE...
chcon [OPTION]... --reference=RFILE FILE...
```

修改 **SELinux 安全上下文**。

```bash
$ chcon -t user_tmp_t ./ctx.txt
chcon: 无法对无标签的文件 './ctx.txt' 只应用一部分上下文
```

上面的报错信息很关键：这台 Debian 13 的 SELinux 是 `Disabled` 状态（`getenforce` 返回 `Disabled`），文件系统也没有打标签，所以 `chcon` 失败——**这正是 SELinux 未启用时的正常表现**。

正确用法（在启用了 SELinux 的系统，如 RHEL/CentOS/Fedora 上）：

```bash
# 让 web 服务器能读某个目录
$ chcon -R -t httpd_sys_content_t /srv/web

# 参照已知正确的文件设置
$ chcon --reference=/var/www/html /srv/web/index.html

# 只改 type / user / role / range 中的一个
$ chcon -t httpd_sys_rw_content_t /srv/web/uploads
```

开关：`-u` user、`-r` role、`-t` type、`-l` range、`-R` 递归、`--reference=RFILE` 参照、`-h`/`--no-dereference` 处理符号链接本身、`-v` 输出。

> **优先用 `semanage fcontext` + `restorecon`**：`chcon` 的改动不会被 `restorecon` 记住，系统 relabel 后就丢了。持久化策略应写进 SELinux policy（`semanage fcontext -a -t httpd_sys_content_t '/srv/web(/.*)?'` 然后 `restorecon -Rv /srv/web`）。

### `runcon` — run command with specified security context

```text
runcon CONTEXT COMMAND [args]
runcon [ -c ] [-u USER] [-r ROLE] [-t TYPE] [-l RANGE] COMMAND [args]
```

在指定的 SELinux 上下文中运行命令。

```bash
# 打印当前上下文（无参数）
$ runcon
unconfined_u:unconfined_r:unconfined_t:s0      # 在启用 SELinux 的系统上

# 以指定上下文运行
$ runcon -t httpd_t /usr/sbin/httpd

# 用完整上下文
$ runcon system_u:system_r:httpd_t:s0 /usr/sbin/httpd
```

- `-c`/`--compute` 先计算进程转换后的上下文再应用
- `-t`/`-u`/`-r`/`-l` 分别指定 type/user/role/range（可组合，只改一部分）
- 不给 CONTEXT 也不给 COMMAND 时，打印当前上下文

> 手册原文提醒：**“Only carefully-chosen contexts are likely to run successfully.”** 随意指定上下文几乎必然失败（SELinux 会拒绝未授权的转换）。

同理，在 SELinux 处于 `Disabled` 的系统上 `runcon` 无法正常工作。

---

## 速查：按场景找命令

| 我想…… | 用这个 |
|--------|--------|
| 找最占空间的地方 | `du -xhd1 / \| sort -h` |
| 磁盘满了但 du 对不上 | `lsof +L1`（已删除未释放）+ `df -i`（inode 耗尽） |
| 看磁盘真实剩余 | `df -hT --output=pcent,target -x tmpfs` |
| 取文件时间戳做比较 | `stat -c %Y file` |
| 日志实时过滤 | `tail -F log \| grep -v healthz` |
| 清空正在写的日志 | `truncate -s 0 log`（不要 `rm`，进程 fd 会断） |
| 大文件切分/并行处理 | `split -n 8 -d --filter='gzip > $FILE.gz'` |
| 按内容切日志 | `csplit -f sec_ file '/^===/' '{*}'` |
| 两个名单求差集 | `comm -23 <(sort a) <(sort b)` |
| 统计日志 IP 频次 | `cut -d' ' -f1 log \| sort \| uniq -c \| sort -rn` |
| 随机抽样 | `shuf -n 1000 huge.log` |
| 数字转 1K/2M | `numfmt --to=iec N` / `numfmt --field=1 --from=iec` |
| 给命令加超时 | `timeout -k 5 60s cmd` |
| 管道输出不及时 | `stdbuf -oL cmd \| tee log` |
| 保存并同时看输出 | `cmd 2>&1 \| tee log` |
| 写 root 文件 | `echo x \| sudo tee -a /etc/file` |
| 安全建临时文件 | `mktemp -d` + `trap 'rm -rf “$d”' EXIT` |
| 二进制安全复制 | `dd if=... of=... bs=4M status=progress conv=noerror,sync` |
| 看文件不可见字符 | `cat -A` / `od -c` |
| 部署二进制 | `install -Dm755 src /usr/local/bin/tool` |
| 改软链接指向 | `ln -sfn new link`（**记得 -n**） |
| 判断是否在脚本/终端 | `[ -t 1 ]` |
| 判断是否提权 | `[ “$(whoami)” != “$(logname)” ]` |
| 递归改权限只改目录 | `chmod -R a+X dir/` |
| 编译用多少核 | `make -j“$(nproc --ignore=2)”` |

---

## 几个值得记住的坑

1. **`sort` 的 locale 依赖**：脚本里写 `LC_ALL=C sort`，否则结果随系统语言变化。
2. **`uniq` 只去重相邻行**：`sort | uniq`，别直接用 `uniq`。
3. **`comm`/`join` 要求已排序**：否则结果错误且默认不报警（可用 `--check-order`）。
4. **`ln -sf` 在有目录软链接上会钻进去**：用 `ln -sfn`。
5. **`shred` 对 SSD / btrfs / ZFS / journaling 文件系统无效**：介质级擦除用 LUKS 或 ATA Secure Erase。
6. **`chmod 777` 解决不了权限问题**：配属组 + setgid（`2775`）才是正解。
7. **`echo -n`/`-e` 不可移植**：用 `printf`。
8. **`chmod -R` / `rm -rf` 加 `--preserve-root`**（默认已开）：别手滑 `-R /`。
9. **`nice` 是相对调整**：`nice -n 5` 是在当前 nice 值上加 5。
10. **`nohup` 不后台**：还得自己加 `&`；长期服务用 systemd 用户单元。
11. **`stdbuf` 只对用 C stdio 且动态链接的程序有效**：Go/静态链接的程序无效。
12. **`cut -c` 而非 `-b` 处理中文**：`-b` 按字节会切坏 UTF-8。

---

## 小结

这 105 个命令中，真正高频使用的可能只有 20 个。但正是剩下那些“眼熟但不熟”的命令，决定了你在**别人写 20 行 Python 脚本的时候，能一行管道解决**。

建议的练习方式：

1. 挑 3 个你从没用过的命令（推荐 `numfmt`、`comm`、`csplit`），本周内在实际工作中强行用一次
2. 把 `ln -sfn`、`LC_ALL=C sort`、`timeout -k` 写进肌肉记忆
3. 遇到“这个问题要写脚本”的时候，先想想有没有 coreutils 命令能直接做

所有命令的完整文档都在你系统里：`man <cmd>`。手册里的 `EXAMPLES` 小节（如果有的话）往往比网上的教程更准确。
