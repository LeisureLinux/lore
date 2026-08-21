# 交叉编译 linux-tools：构建 Linux 内核 out-of-tree 工具的完整实战

> **原始出处**：[github.com/gregkh/linux](https://github.com/gregkh/linux) + 一次真实的 arm64 交叉构建  
> **适用版本**：linux-tools (7.1.0-rc3)，Debian / Ubuntu 内核打包流程通用  
> **作者**：LeisureLinux  
> **关键词**：Linux 内核、linux-tools、交叉编译、CROSS_COMPILE、out-of-tree 工具、aarch64

## 引言：我到底想干什么？

目标很朴素：从 [gregkh/linux](https://github.com/gregkh/linux)（Linux 内核的 Debian 风格打包仓库）里，为 `7.1.0-rc3` 构建一套 `linux-tools`，然后**交叉编译成 arm64**，拿到能直接塞进 arm64 设备 / rootfs 里的 `perf`、`bpftool`、`kheaders` 等运维工具。

手边现成的条件：

- 一棵 `build-7.1.0-rc3` 源码树，**但只有源码**——没有 `tools/` 构建产物、没有 `.config`、仓库里也没有 `config-7.1.0-rc3` 现成配置文件；
- 一台正在**跑着内核的 x86_64 主机**，`/root/linux/` 下是它正在使用的内核源码树；
- 机器上装了 aarch64 / arm 的交叉工具链。

听起来不难，但这一路我接连踩了五个坑。这篇文章把**犯过的错误、换来的教训、完整的交叉编译步骤、以及工具链里每个组件到底干什么**，一次讲清楚。

---

## 一、犯的错误 → 换来的收获

下面每一条都是这次实操里真实绕路的点，按踩坑顺序排。

### 坑 1：没有 `.config` 就上手 `make`

**错误**：拿到 `build-7.1.0-rc3` 这棵纯源码树，直接开构建。结果 Kconfig 阶段就卡住——树里没有 `.config`，也没有 `config-7.1.0-rc3`，构建系统根本不知道该开哪些选项。

**收获**：内核构建是 **config-driven** 的，没有配置就没有构建。配置来源无非三条路，按优先级选：

1. **正在运行的内核**：把 `/proc/config.gz` 拿来解压，最贴合"我到底要配成什么样"；
2. **defconfig**：`make ARCH=arm64 defconfig`，快速得到一个可用基线；
3. **仓库里现成的 `config-*`**：本例没有，排除。

> 记住一句话：**先有 `.config`，再有 `vmlinux`，最后才有 `tools/`。**

### 坑 2：差点在"正在运行的内核树"里构建

**错误**：一开始图省事，想在 `/root/linux/`（这台机器正在跑的内核源码树）里直接构建产物。这会往树里塞一堆 `.o`、`vmlinux`、中间产物，既污染在用的树，也有极小概率干扰 `kbuild` 缓存，得不偿失。

**收获**：**out-of-tree / 隔离构建**是内核算子级的基本功。要么用一棵专门的构建树（本例的 `build-7.1.0-rc3`），要么用 O= 指定独立输出目录。核心思想是"产物和源码、产物和在用系统，互相隔离"。

### 坑 3：交叉工具链"装了一半"

**错误**：只装了交叉 GCC，就开始编到链接阶段——然后炸：找不到 `-lc`、缺目标架构的系统头文件。原因是**交叉工具链是三件套**，我只装齐了一件。

**收获**：一套能链接出可执行文件的交叉工具链 = 下面三块，缺一不可：

- **交叉 GCC**（编译器本体，把 C 翻成目标指令）；
- **交叉 binutils**（`as`/`ld`/`objcopy`/`strip`……负责汇编、链接、后处理）；
- **目标 glibc 的 `-dev` 包**（目标架构的头文件 + `crt*.o` 启动代码，提供 `-lc`）。

只装 GCC，等于"有笔没纸"——编译能过，链接必崩。

### 坑 4：host 工具与 target 工具混淆

**错误**：内核 `tools/` 目录里，有些程序是**构建时跑在宿主机上**的（构建脚本、部分 Python/Perl 辅助），有些才是**最终要部署到目标设备**的（`perf`、`bpftool` 的成品）。一开始不分谁用谁的编译器，交叉时就乱用 host 编译器去编 target 二进制。

**收获**：交叉编译前先分清两类二进制——

- **host 工具**：在 x86_64 上跑，用本地原生编译器；
- **target 工具**：要在 arm64 上跑，用交叉编译器。

`linux-tools` 的绝大多数交付物属于后者，用 `CROSS_COMPILE` 指过去就对了；但构建过程中的脚本仍是 host 侧。

### 坑 5：`CROSS_COMPILE` 前缀与 `ARCH` 写混了

**错误**：把"目标架构名"和"交叉二进制前缀"搞混，前缀少一个横杠、或 arch 拼错，`kbuild` 就满世界找不到 `aarch64-linux-gnu-gcc`。

**收获**：这俩是**两个独立的东西**，最容易混，务必分清：

| 变量 | 取值（arm64 例） | 含义 |
|---|---|---|
| `ARCH` | `arm64` | **内核**架构名（Kconfig / 目录命名用） |
| `CROSS_COMPILE` | `aarch64-linux-gnu-` | **binutils 二进制前缀**（`as`→`aarch64-linux-gnu-as`） |

注意：`ARCH` 用内核叫法（`arm64`），`CROSS_COMPILE` 用发行版工具链叫法（`aarch64-linux-gnu-`），两者**字母顺序还不一样**。写对前缀，工具链才找得到。

---

## 二、交叉编译工具链：每个组件都干什么？

以**目标 = aarch64**为例，Debian 上一套完整的交叉工具链长这样（这些是我机器上 `dpkg -l` 里真实在跑的版本）：

| 组件 | 包（apt） | 干什么用 |
|---|---|---|
| 交叉编译器 | `gcc-14-aarch64-linux-gnu` | 把 C 源码编译成 aarch64 目标码；提供 `aarch64-linux-gnu-gcc` |
| 交叉工具集 | `binutils-aarch64-linux-gnu` (2.44) | `as`（汇编）、`ld`（链接）、`objcopy`/`strip`/`ar`/`nm`（二进制后处理） |
| 目标 C 库 dev | `libc6-dev-arm64-cross` | 目标架构的 glibc 头文件 + `crt*.o` 启动对象，提供 `-lc` 与系统调用包装 |
| sysroot | `/usr/aarch64-linux-gnu/` | 目标"文件系统根"：头文件在 `aarch64-linux-gnu/`、库在 `lib/`，编译器靠 `--sysroot` 找到它们 |
| 宿主侧工具 | `make` + 内核自带 `scripts/`（Kconfig）+ Python/Perl | 构建脚本、配置系统，跑在 x86_64 上 |

**心智模型**：你在 x86_64 上，"借来"一整套 aarch64 的编译器、汇编器、链接器和目标 C 库，让它们在宿主机上运转、产出 arm64 的二进制。`sysroot` 是那套目标"地基"，`CROSS_COMPILE` 前缀是通往这堆工具的"门牌号"。

---

## 三、完整交叉编译步骤（可复现）

### 0) 安装交叉工具链（aarch64 目标）

```bash
sudo apt-get update
sudo apt-get install -y \
    gcc-aarch64-linux-gnu \
    binutils-aarch64-linux-gnu \
    libc6-dev-arm64-cross
```

验证三件齐全：

```bash
aarch64-linux-gnu-gcc --version        # gcc-14
aarch64-linux-gnu-ld --version         # binutils 2.44
ls /usr/aarch64-linux-gnu/lib          # 目标 C 库在
```

### 1) 用独立树 + 一份 config

```bash
# 隔离树（别在 /root/linux/ 里搞）
cd /root/build-7.1.0-rc3
export ARCH=arm64
export CROSS_COMPILE=aarch64-linux-gnu-

# 有在用配置就最贴切，否则回落 defconfig
if [ -f /proc/config.gz ]; then
    zcat /proc/config.gz > .config
    make olddefconfig
else
    make defconfig
fi
```

> 本例树里没有 `config-7.1.0-rc3`，所以我用 `defconfig` 打底，按需调整。要点是**先把 `.config` 弄出来并 `olddefconfig` 归一**，后面所有 target 都吃这一份配置。

### 2) 交叉编译内核 tools

`linux-tools` 的交付物来自 `tools/` 下的若干子项目（`perf`、`bpftool`、`kheaders`……）。核心是让 `kbuild` 用交叉前缀去编这些 target 工具：

```bash
# perf（最常用，也是 linux-tools 的主力）
make ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- \
     -C tools/perf

# bpftool
make ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- \
     -C tools/bpf/bpftool

# kheaders（打包内核头文件）
make ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- \
     -C usr/gen_initramfs  # 或对应 kheaders 目标
```

> 不同内核版本 / 打包脚本对 `tools/` 的入口略有差异；若你走 `gregkh/linux` 的 `debian/rules`，它内部已把上面这些 `CROSS_COMPILE` 规则串好，你只需保证三件套与 `ARCH` 正确即可。

### 3) 验证产物确实是 arm64、且能链接

```bash
file tools/perf/perf
# ... ELF 64-bit LSB executable, ARM aarch64, ...

# 若提示 "cannot find -lc" → 回到坑3，libc6-dev-arm64-cross 没装全
readelf -h tools/perf/perf | grep -E 'Machine|Type'
```

`readelf -h` 里 `Machine: AArch64` 才算数——这说明二进制是给 arm64 的，能直接丢进 arm64 rootfs 的 `/usr/lib/linux-tools/<ver>-generic/`。

### 4) （可选）打包成一个 linux-tools 归档

```bash
VER=7.1.0-rc3
DEST=/root/build-tools/${VER}-arm64
mkdir -p $DEST/{bin,lib}
cp tools/perf/perf        $DEST/bin/
cp tools/bpf/bpftool/bpftool $DEST/bin/
tar czf linux-tools-${VER}-arm64.tar.gz -C $DEST .
```

---

## 四、一份能复用的 Makefile

把上面流程固化成 `Makefile`，以后换版本号 / 换架构只改两个变量：

```make
#!/usr/bin/make -f
# 交叉编译 linux-tools 的入口
KERNEL ?= /root/build-7.1.0-rc3
VER    ?= 7.1.0-rc3
ARCHC  ?= arm64                  # 内核架构名（Kconfig 用）
CROSS  ?= aarch64-linux-gnu-     # binutils 前缀（工具链用）

export ARCH = $(ARCHC)
export CROSS_COMPILE = $(CROSS)

all: config tools

config:
	@test -f $(KERNEL)/.config || (cd $(KERNEL) && make $(ARCHC)_defconfig)
	-(cd $(KERNEL) && make olddefconfig)

tools:
	$(MAKE) -C $(KERNEL)/tools/perf
	$(MAKE) -C $(KERNEL)/tools/bpf/bpftool

clean:
	$(MAKE) -C $(KERNEL)/tools/perf clean

.PHONY: all config tools clean
```

用法：

```bash
make KERNEL=/root/build-7.1.0-rc3 VER=7.1.0-rc3
# 换成 riscv64 之类，只需：
# make ARCHC=riscv64 CROSS=riscv64-linux-gnu-
```

---

## 五、总结

- **先 config 再构建**：内核构建是 config-driven，没 `.config` 一切免谈；来源优先 `/proc/config.gz` → `defconfig`。
- **隔离构建**：别在正在运行的内核树里塞产物，out-of-tree 是基本功。
- **交叉工具链三件套**：GCC + binutils + target glibc-dev，缺一个就链接崩。
- **分清 host / target**：交付物用交叉编译器，构建脚本仍跑在 host。
- **`ARCH` ≠ `CROSS_COMPILE`**：前者是内核架构名（`arm64`），后者是工具链前缀（`aarch64-linux-gnu-`），顺序还不同，写错就找不到工具。

把这套流程固化成 Makefile 之后，交叉出一套能直接进 arm64 设备的 `linux-tools`，就是改两个变量的事。踩过的坑都在这了，照着避，能省下我一整天的头秃。
