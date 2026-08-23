# 交叉编译 toybox：从 x86_64 静态 musl 到 ARM64 工具链的完整实战

> 这篇是实操记录。我在 Debian 13（x86_64）上，先后产出了两个 **toybox 0.8.14** 的可执行文件：一个是本地 x86_64 的静态 musl 版本，一个是针对 ARM64（aarch64）的静态 musl 交叉编译版本。整个过程踩了几个实实在在的坑，尤其 ARM64 那条路，因为 musl 的 `configure` 脚本里一个 `arm*` 通配符匹配的 bug，折腾了挺久。下面把问题、解决、每个工具链组件的作用、以及可复现的步骤一五一十写出来。

## 一、toybox 是什么

toybox 是 Landley 维护的一个「all-in-one Linux command line」项目，定位和 BusyBox 类似：把 `ls`、`cp`、`grep`、`tar` 这些 Unix 小工具合并进**一个**可执行文件（multicall binary），靠启动时读 `argv[0]` 或第一个参数来分发到对应的 applet。官方 README 的原话是：

> Toybox: all-in-one Linux command line.

官方仓库：[codeberg.org/landley/toybox](https://codeberg.org/landley/toybox)（主仓库），GitHub 有镜像 [github.com/landley/toybox](https://github.com/landley/toybox)。toybox 也提供预编译二进制（`http://landley.net/toybox/bin`），但那是给直接下载用的；**要自己控制 C 库（musl）和是否静态，就得从源码构建**，也就是本文要做的事。

`defconfig` 默认配置会启用约 **237 个 applet**。我用裸命令（不带参数）跑一次 `toybox` 打印出的 applet 列表，数出来正好是 237 行。注意：**`toybox --list` 不是一个合法子命令**，会报 `Unknown command --list`；想看列表直接裸跑 `toybox`，`--help` 打印头部信息，`--long` 打印安装路径。

defconfig 这套工具里 `cat cp mv rm ls find grep sed xargs head tail wc sort uniq ps top free df du mount ifconfig ping wget tar dd` 都有，但**不包含** `sh`（shell）、`gzip`、`curl`、`umask`、`mkfs`、`fsck` 这些（它们要么默认没开，要么属于需要单独配置/链接额外库的玩具）。

## 二、为什么用 musl 静态构建

做嵌入式/最小启动盘（initramfs、容器基础镜像、路由器固件）时，通常要一个**不依赖目标机 glibc** 的单文件。musl 是个小巧、单 `.so`+静态方便的 C 库，`static` 链接之后产出一个完全不依赖任何共享库的 ELF。

验证「完全静态」最可靠的方式不是看 `file` 的 `statically linked` 字样，而是看 ELF 动态段里有没有 `NEEDED` 项：

```sh
readelf -d toybox.x86_64 | grep NEEDED   # 空输出 = 全静态
```

两个产物 `readelf -d` 都没有 `NEEDED` 项，确认是**完全静态**的（`file` 也显示 `statically linked, stripped`）。

本次两个产物：

| 产物 | 大小 | 架构 | 状态 |
|---|---|---|---|
| `toybox.x86_64` | 707,864 字节（692 KiB） | x86-64 | 静态 musl，已 strip |
| `toybox.aarch64` | 769,128 字节（752 KiB） | ARM aarch64 | 静态 musl，已 strip |

## 三、两条构建路径概览

- **x86_64**：用 landley.net 提供的现成 **x86_64 linux-musl 交叉工具链**（GCC **15.1.0** + 完整 binutils + musl sysroot）。因为 host 本身就是 x86_64，这其实是「用独立的 musl 工具链盖宿主机的 glibc」，产本地可跑的静态二进制。
- **aarch64**：landley.net **没有**提供 ARM64 的 musl 工具链（返回 404），所以用 [musl-cross-make](https://git.alexdashboard.com/alexdatous/musl-cross-make) 从源码现场编一套 aarch64 交叉工具链（GCC **9.4.0** / binutils 2.44 / musl 1.2.6 / linux-headers 4.19.88），再拿它盖 toybox。

## 四、本次会话实际踩到的问题

按碰到的顺序列，只描述真实症状和解法，不复刻我没有逐字确认的错误堆栈。

### 1. host glibc 和 musl 头文件打架（x86_64）

一开始想直接用系统 `gcc`（14.2.0，glibc 2.41）加 `-static` 盖 musl，结果头文件互相污染、链接器找不到 musl 的符号。根因是：系统工具链是围着 glibc 建起来的，让它去盖一个 musl 目标不干净。

**解法**：不要用系统 gcc，改用一套**自洽的 linux-musl 独立工具链**（自带 musl 的头文件和 libc，`sysroot` 是 musl，不是 glibc）。x86_64 这条直接用 landley.net 预编译的那套。

### 2. Debian 的 `musl-tools` 不是完整交叉工具链

Debian 有个 `musl-tools` 包（我这是 `1.2.5-3.1~deb13u1`），但装上之后只有 `/usr/bin/x86_64-linux-musl-gcc` 一个编译入口，配套 binutils（as/ld/strip/objcopy）并不是以 `x86_64-linux-musl-` 前缀成套提供的。拿它当一套独立工具链用是不够的，所以 x86_64 我改用了 landley.net 那份完整的（`/tmp/x86_64-linux-musl-cross/bin/` 里 ar/as/elfedit/gcc 一应俱全）。

### 3. landley.net 从国内拉取不稳定

我这台机器在国内（IP `43.135.161.29`），到 landley.net 的连接很不稳，下载那个 ~76MB 的工具链包断了好几次，靠 `curl -C -` 断点续传重试才拉完。这纯属网络运气问题，跟构建无关，但值得提醒：国内访问 landley.net 要有心理准备多试几次。

### 4. ARM64 没有现成工具链 → 只能源码编

landley.net 只给 x86_64 的 linux-musl 工具链，ARM64 的是 404。于是要自己编。选了 **musl-cross-make**（一个专门用来从源码构建各类 linux-musl 交叉工具链的 Makefile 集合）。

### 5. 国内下载 GNU 源码包：代理 502、清华 403，阿里云能用

musl-cross-make 默认从 GNU 镜像（`ftpmirror.gnu.org` 之类）下载 gcc、binutils、musl、gmp、mpfr、mpc 的源码包。这台机：走代理（`http://wpad.lan:8888`）访问 GNU 镜像返回 **502 Bad Gateway**；清华镜像返回 **403**。最后用**阿里云镜像 `mirrors.aliyun.com/gnu`**（无需代理）把 7 个 `.tar.xz` 全部下下来，并且**7 个 SHA1 校验全部命中**——版本号都是 musl-cross-make `Makefile` 里 pin 死的，见下节。

### 6. `git.savannah.gnu.org` 超时，config.sub 得自己补

构建过程中，musl-cross-make 会尝试去 `git.savannah.gnu.org` 拉一份更新的 `config.sub`，这台机直连超时。解决办法：把系统自带的较新 `config.sub`（Debian 13 的 `/usr/share/misc/config.sub`）替换进各个解开的源码树里。

> 这里要区分两个 `config.sub` 相关的事：一个是**GCC 9.4.0 自带的 `config.sub` 太老**，不认识/不会规范化较新的三元组，属于「工具链自带脚本过旧」；我换成系统那份较新的 `config.sub` 来解决。别和下面第 7 条 musl 自己的 `configure` 通配符 bug 混在一起——那是不同的脚本、不同的层。

### 7. 关键坑：musl 自己的 `configure` 用 `arm*` 把 aarch64 误判成 32 位 ARM

这是 ARM64 那条路最坑、也是真正卡我最久的地方。musl 的 `src_musl/configure` 里有一段按目标名推断架构的 `case`，原文（`src_musl/configure` 第 324–325 行）：

```sh
324  arm*)        ARCH=arm ;;
325  aarch64*)    ARCH=aarch64 ;;
```

`case` 是**从上往下**第一个命中就生效。当我把目标设成 `arm64-linux-musl` 时，`arm64...` 会先被第 324 行的 `arm*)` 吃掉，于是 musl 把目标当成 **32 位 arm** 来 configure，后面的编译就因为架构/长 double 位宽不匹配报了一堆错。

**解法**：把目标三元组改成 **`aarch64-linux-musl`**（而不是 `arm64-linux-musl`）。`aarch64...` 不会命中第一行的 `arm*)`，会正确落到第 325 行 `aarch64*)`。用这个名字干净重编，一次通过。

> 说明一下走过的弯路：我当时先怀疑是 `__float128`/long double 的位宽问题，折腾过 musl-cross-make 的 `config.mak`，往 `GCC_CONFIG_FOR_TARGET` 里加 `--with-long-double-128`。**那是错的——那不是根因，架构名才是。** 真正原因就是上面这两行 `case` 的通配符顺序。

## 五、工具链组件 & 每个工具干什么

### aarch64 工具链（musl-cross-make 产物）

版本号都来自 `musl-cross-make/Makefile` 第 5–11 行，是 pin 死的：

```make
BINUTILS_VER = 2.44
GCC_VER      = 9.4.0
MUSL_VER     = 1.2.6
GMP_VER      = 6.3.0
MPC_VER      = 1.3.1
MPFR_VER     = 4.2.2
LINUX_VER    = headers-4.19.88-2
```

逐组件说明它们在这次构建里各自的角色：

- **binutils 2.44** —— 目标机工具集的前端：汇编器 `as`（`.s`→目标机器码 `.o`）、链接器 `ld`（把一堆 `.o` 拼成一个 ELF）、还有 `ar`（打包）、`strip`（去符号）、`objcopy`/`objdump`/`readelf`（查/转 ELF）。盖静态二进制时，`ld` 直接把所有目标文件 + libc.a 焊死进一个文件，没有运行时依赖。
- **gcc 9.4.0**（`aarch64-linux-musl-gcc`）—— 交叉编译器本体，负责把 toybox 的 C 源码编译、优化、再调用上面的 `as`/`ld` 完成链接。它自己编译出来的可执行代码跑在 host（Linux x86_64）上，但产出是 aarch64 的目标代码。
- **musl 1.2.6** —— **C 库（libc）**，这才是「musl 构建」的核心。它提供 `printf`、`malloc`、`open`、`close` 这类标准库函数，以及直接 `syscall` 进内核。静态链接时，gcc 把 musl 的 `libc.a` 整个链进去，于是产物不依赖任何 `libc.so`。
- **linux-headers (headers-4.19.88)** —— Linux 内核头文件，提供 `open`/`read`/`futex` 等**系统调用**的声明和相关数据结构。musl 和 gcc 都需要它才能正确地 `syscall(2)` 进内核；它决定了二进制「认为自己在跟哪个版本的 ABI/内核说话」。
- **gmp 6.3.0 / mpfr 4.2.2 / mpc 1.3.1** —— 这三个是 **gcc 自己的构建期依赖**，跟你最终盖的 toybox 没有运行期关系。gmp 是高精度整数运算库；mpfr 是「带正确舍入的浮点」库（依赖 gmp）；mpc 是复数库（依赖 gmp+mpfr）。gcc 处理 `long double`、浮点常量、复数时就靠这三个头，所以**编工具链**时要先把它们编好。
- **sysroot** —— musl-cross-make 把上面的 musl 头文件 + libc.a + linux-headers 收拢成一个目录（`output/aarch64-linux-musl/...`）。gcc 盖目标代码时用它，而不是 host 的 glibc 目录，这就是「自洽工具链」区别于系统 gcc 的关键。

### x86_64 工具链（landley.net 预编译）

- `x86_64-linux-musl-gcc (GCC) 15.1.0`，配完整 binutils 和 musl sysroot（sysroot 里能看到 `ld-musl-x86_64.so.1`）。
- 注意：这套是 **GCC 15.1.0**，和 aarch64 那套的 **9.4.0** 是两个不同版本、来源也完全不同（一个是现成二进制，一个是我从源码编的）。所以两个产物 `file`/`readelf` 里体现的编译器特征可能不一致——这完全正常。

## 六、完整可复现步骤 —— x86_64 静态 musl

**Step 1.** 拉源码（Codeberg 会 429 拒我这种国内 IP，用 GitHub 镜像；整仓 clone 会超时，用 shallow）：

```sh
git clone --depth 1 --single-branch https://github.com/landley/toybox.git
cd toybox            # 此时为 0.8.14
```

**Step 2.** 解包 landley.net 的 x86_64 linux-musl 工具链（国内拉取不稳，多试几次、用 `-C -` 续传）：

```sh
curl -C - -o x86_64-linux-musl-cross.tar.xz \
  http://landley.net/toybox/x86_64-linux-musl-cross.tar.xz
tar xf x86_64-linux-musl-cross.tar.xz   # 得到 x86_64-linux-musl-cross/
```

**Step 3.** 盖玩具（toybox 尊重 `CROSS_COMPILE`，`LDFLAGS=--static` 强制静态）：

```sh
export PATH="/tmp/x86_64-linux-musl-cross/bin:$PATH"   # 按你解包位置改
LDFLAGS=--static CROSS_COMPILE=x86_64-linux-musl- make defconfig toybox
```

`defconfig` 生成 `.config`（开 ~237 个玩具），`toybox` 是产物目标。

**Step 4.** 移出构建树保存（toybox 的 `make clean`/`distclean` 会把产物清掉，一定先拷走）：

```sh
cp toybox /home/axu/github/toybox.x86_64
```

**Step 5.** 验证：

```sh
file toybox.x86_64      # ELF 64-bit ... x86-64, statically linked, stripped
./toybox.x86_64 --version
readelf -d toybox.x86_64 | grep NEEDED   # 应为空
./toybox.x86_64 ls        # 随手跑个 applet 冒烟测试
```

## 七、完整可复现步骤 —— aarch64 (ARM64) 静态 musl

### Part A. 先编一条 aarch64 linux-musl 交叉工具链

**Step 1.** 拉 musl-cross-make：

```sh
git clone https://git.alexdashboard.com/alexdatous/musl-cross-make
cd musl-cross-make
```

**Step 2.**（国内）预下 GNU 源码包。musl-cross-make 要 7 个包：**binutils-2.44、gcc-9.4.0、musl-1.2.6、gmp-6.3.0、mpfr-4.2.2、mpc-1.3.1、linux-headers-4.19.88**。从阿里云拉（无需代理），逐个核 SHA1：

```sh
base=https://mirrors.aliyun.com/gnu
for f in binutils-2.44 gcc-9.4.0 gmp-6.3.0 mpfr-4.2.2 mpc-1.3.1; do
  curl -O "$base/$f/$f.tar.xz"
done
curl -O "$base/musl/musl-1.2.6.tar.gz"
# linux-headers：headers-4.19.88-2（musl 的 kernel-headers 源）
# 每个包都要核对 SHA1，别直接信，校验命中再喂给构建
```

**Step 3.** 目标三元组**一定用 `aarch64-linux-musl`**，不要用 `arm64-linux-musl`（第五节第 7 条那个 `case` 通配符 bug 会把 `arm64` 误判成 32 位 arm）：

```sh
make -j"$(nproc)" TARGET=aarch64-linux-musl
```

构建大约 8~9 分钟。若它卡在中途去 `git.savannah.gnu.org` 拉 `config.sub` 超时，就把系统较新的 `config.sub`（`/usr/share/misc/config.sub`）塞进解开的源码树再续编。

构建完成时它会在 `output/` 里打印 `make ... install` 的提示。

**Step 4.** 装工具链：

```sh
make TARGET=aarch64-linux-musl install
# 产物在 ./output/bin/，主编译器是 output/bin/aarch64-linux-musl-gcc (GCC 9.4.0)
```

> 我中途往 `config.mak` 加过 `GCC_CONFIG_FOR_TARGET += --with-long-double-128` 试图修编译错误——那其实是**红鲱鱼**，真正的修复是 `TARGET=aarch64-linux-musl` 这个架构名。装好之后那条 `config.mak` 改动其实没必要，可留可删。

### Part B. 用这条工具链盖 ARM64 toybox

```sh
cd /home/axu/github/toybox
export PATH="/home/axu/github/musl-cross-make/output/bin:$PATH"
LDFLAGS=--static CROSS_COMPILE=aarch64-linux-musl- make defconfig toybox
cp toybox /home/axu/github/toybox.aarch64   # 先挪走，防 clean 误删
```

### Part C. 验证

```sh
file toybox.aarch64
# ELF 64-bit LSB executable, ARM aarch64, version 1 (SYSV), statically linked, stripped
readelf -d toybox.aarch64 | grep NEEDED   # 为空 = 全静态
# 本机是 x86_64，直接跑会报 exec format error 属正常；真正验证要靠 qemu 或上真机：
qemu-aarch64-static -L /path/to/rootfs ./toybox.aarch64 --version   # 若装了 qemu
```

## 八、小结

- x86_64：别硬用系统 glibc gcc 盖 musl，用 landley.net 那套独立 musl 工具链（GCC 15.1.0），`--static` 一盖就成一个 692 KiB 的自足二进制。
- aarch64：现成工具链没有，源码编一条（GCC 9.4.0）。**记住那个 `case` 通配符的顺序**——目标写 `aarch64-linux-musl`，别写 `arm64-linux-musl`，能省半天。
- 验证「完全静态」看 `readelf -d` 的 `NEEDED` 是否为空，比看 `file` 文字更靠谱。
- 产物务必**移出构建树**再保存，`make distclean` 会连产物一起删。

## 九、参考资料

- toybox 官网 / 预编译二进制：<http://landley.net/toybox/>
- toybox 主仓库（Codeberg）：<https://codeberg.org/landley/toybox>
- toybox GitHub 镜像：<https://github.com/landley/toybox>
- musl C 库：<https://musl.libc.org/>
- musl-cross-make（构建 musl 交叉工具链）：<https://git.alexdashboard.com/alexdatous/musl-cross-make>
- GCC 交叉编译指南：<https://gcc.gnu.org/install/cross.html>
- GNU/Linux 交叉构建综述：<https://gcc.gnu.org/install/cross.html>
- 阿里云 GNU 镜像（国内下载源码包）：<https://mirrors.aliyun.com/gnu>
