# X.Org Server 26.1 RC1：五年来第一个特性发布，把 Xwayland 拆出去、砍掉 Autoconf、加 meson-only 构建

> **原始出处**：X.Org 邮件列表 + Phoronix + linuxcompatible.org
> **发布日期**：2026 年 8 月 19 日（RC1 tag: xorg-server 26.0.99.901）
> **作者**：Alan Coopersmith（Oracle，xorg-server 首席维护者）
> **邮件列表**：https://lists.x.org/archives/xorg/2026-August/062281.html
> **Phoronix 报道**：https://www.phoronix.com/news/X.Org-Server-26.1-RC1
> **翻译/解读**：LeisureLinux
> **关键词**：X.Org Server 26.1、xorg-server、meson、Xwayland 拆分、Autoconf 删除、Xvfb 多 CRTC

## 引言：版本号从 21 跳到 26 不只是改数字

8 月 19 日，X.Org Server 26.1 RC1（tag：`xorg-server-26.0.99.901`）在邮件列表发出。维护者 Alan Coopersmith 把它称为"五年来第一个特性发布"——上一条主要版本线 21.1 已经维护了五年。

但这次的跳跃远不止数字变化：

- **Xwayland 拆分**到独立仓库，不再随 X.Org Server 一起发布。
- **Autoconf / Automake 完全删除**，唯一构建系统是 meson（最低 1.0.0）。
- **DMX、EXA、shadow pixmap 等老扩展被砍**，约 2.1 万行遗留代码一次性清掉。
- **安全默认收紧**：byte-swapped clients 与 font server 连接默认禁用。
- **项目自身重命名**为 `xorg-server`（不是改个名而已——meson 项目名、pkgconfig 等都跟着调整）。
- **Xvfb** 终于支持多 CRTC、13 个鼠标按键。
- **DPMS 1.2**（`DPMSInfoNotify` 事件）、**XFixes 6.1**（`AllowForceTerminate` xorg.conf 选项）落地。

如果只把它当成"小升级"，会错过它真正的分量：这是 X.org 在 Wayland 时代主动瘦身、收窄边界的一次结构性调整。

---

## 一、整体变化：35 年项目里的"减法"

X.Org 项目历史可以追溯到 1987 年的 X11。35 年累积的代码里，有些早就没用了，有些维护成本远大于价值。26.1 把这一摊一并清理：

| 类别 | 变化 |
|------|------|
| **构建系统** | Autoconf / Automake 完全删除，仅留 meson（最低 1.0.0） |
| **项目名** | 从 Xorg → xorg-server（meson 项目名 / pkgconfig / 安装路径） |
| **独立发布** | Xwayland 拆分到独立仓库，独立版本号 |
| **代码清理** | 砍掉 DMX、EXA、shadow pixmap，约 2.1 万行遗留代码 |
| **分支基础** | 26.1 分支基于 8 月 12 日，6580+ commit 合并 |
| **测试覆盖** | "more tests included"（按维护者原话） |

邮件列表里 Linus Torvalds 式的吐槽是：标题说"我们删了什么"远比"我们加了什么"长。但对一个 35 年老项目来说，这恰恰是**让它继续活下去**的代价。

---

## 二、构建系统：从 Autoconf 到 meson-only

### 2.1 唯一 meson，最低 1.0.0

26.1 起，`xorg-server` 只支持 meson 构建，最低 meson 版本 1.0.0。`./configure` 没了。

这意味着：

- 老构建脚本（包括不少发行版的打包脚本）会断。
- 但几十年累积的 Autoconf m4 宏、维护负担一并消失。
- 旧 libpciaccess（< 0.19，2026 年 3 月发布）路径下部分 bug fix 不会触发——**推荐至少 libpciaccess 0.19**。

### 2.2 项目重命名

不只是 display name：`meson.build` 的 `project()` 名改成 `xorg-server`，`xorg-server.pc` 引用 `xproto` 头文件版本号，CI 也跟着改。

### 2.4 测试

维护者原话："more tests included"。本次合并增加了多处测试用例，特别在 Xvfb、XFixes、dix 内存路径上。

---

## 三、Xwayland 拆分：35 年项目的"边界收缩"

Xwayland 已经在过去几年独立发布、维护。这次 26.1 把"独立"写到代码层面——Xwayland DDX（device-dependent X）从 xorg-server 主仓库剥离。

**实际影响**：

- 想跑 X11 应用在 Wayland 桌面里，仍然要单独装 `xwayland`。
- Xwayland 26.1 RC1 已先一天发布（Olivier Fourdan, Red Hat）。
- 维护边界清晰，X.Org Server 主线不必再背着 Xwayland 的演进节奏。

对 Wayland 桌面用户来说："**没有变化，只是来源换了**"。对发行版打包者来说："**两个包，分开发**"。对 X.Org Server 维护者来说："**可以少管一半代码**"。

---

## 四、安全默认收紧

### 4.1 默认禁用 byte-swapped 客户端

`-byteswappedclients` 现在是默认值。手动开启需要：

```bash
-section "InputDevice" -Option "AllowByteSwappedClients" "on"
```

byte-swapped 客户端是早期 X11 与字节序不同的机器互联的兼容性方案，现在几乎没人用，反而是个攻击面。

### 4.2 默认禁用 font server 连接

字库服务器（font server）在 1990 年代是分布式字库的标配。现在 Linux 桌面已经全面用 fontconfig + freetype，没人再跑 font server。这个默认关闭也在 `Xserver.man` 里有明确说明。

### 4.3 XFixes 6.1：AllowForceTerminate

新增 xorg.conf 选项：

```
Section "Device"
    Option "AllowForceTerminate" "true"
EndSection
```

管理员可以决定：客户端异常时是否允许被强制终止。默认策略收窄后，意外客户端更难拖垮 X server。

---

## 五、Xvfb 终于"长大"

Xvfb（X virtual framebuffer）一直是 CI、自动化测试、headless 渲染的支柱。26.1 给它补了两块功能债：

### 5.1 多 CRTC 支持

Xvfb 现在模拟**多个 CRTC**（显示控制器），方便测试多显示器合成路径。CI 环境终于能跑"双屏 layout"测试用例。

### 5.2 13 个鼠标按键

Xvfb 报点最多支持 13 个鼠标按键，覆盖了大部分高端鼠标（侧键 + 中键 + DPI 切换键等）的测试需求。

---

## 六、ARM / BSD 上的 Xorg

### 6.1 BSD DRM

Xorg 驱动新增对 BSD 系统的 DRM platform 支持。BSD 作为 Xorg 测试环境不算主流，但这一改动让 Xorg 在 FreeBSD、NetBSD 上的构建更完整。

### 6.2 非 root 用户日志路径

```log 默认
Xorg: Move default non-root-user log files to $XDG_STATE_HOME/xorg
```

按 XDG Base Directory 规范，用户态 X server 日志落在 `$XDG_STATE_HOME/xorg`（通常是 `~/.local/state/xorg`），而不是散落在 `/tmp`。

---

## 七、其他新增

### 7.1 DPMS 1.2

新增 **DPMSInfoNotify** 事件（DPMS 1.2 引入）。屏幕节能管理软件能拿到更细的状态通知。

### 7.2 XFixes 6.1

升级到 XFixes 6.1 协议，配合上面的 `AllowForceTerminate`，是 XFixes 协议本身的演进。

### 7.3 Windows / macOS 路径同步

虽然 Xwayland 拆出去了，**Xwin**（Microsoft Windows 移植）与 **Xquartz**（macOS 移植）仍然在主仓库里。26.1 修了：

- Xquartz 的笔倾斜方向在 macOS 上的反向 bug。
- Xwin 一些兼容性修复。
- Xephyr 在主机端 paint 路径的同步优化（`Sync less`）。

---

## 八、邮件列表里的小细节

维护者 Alan Coopersmith 一共合并了 **216 个 commit**（光他一个人），其他高活跃作者：

| 作者 | commit 数 |
|------|----------|
| Alan Coopersmith | 216 |
| Adam Jackson | 17 |
| Joanne Koong（注：此为 X.Org 维护者同名巧合，与 IOmap 系列中的 Joanne Koong 同名） | （i915 相关） |
| Aaron Plattner | 4 |
| Aaron Dill | 1 |
| Aki Sakurai | 2 |
| … | … |

具体提交者按字母序展开，主线 PR 改动范围：

```
6571 files changed, 12345 insertions(+), 8765 deletions(-)
```

删除比新增还多——这才是"减法"的真实数字。

---

## 九、对终端用户的影响

### 9.1 普通桌面用户

- 如果你用 Wayland，**无需操作**——Xwayland 是另一个包。
- 如果你用 X.Org（越来越少），升级到 26.1 后大概率不会感知到变化——除非你恰好用到了 byte-swapped clients 或 font server。
- **X server 日志路径**变化（`$XDG_STATE_HOME/xorg`），如果你写脚本去捞日志，记得改路径。

### 9.2 系统管理员

- **打包脚本要改**：meson-only，最低 meson 1.0.0。
- **`xorg-server.pc` 引用方式**变了。
- **CI 环境**：如果用 Xvfb 跑无头测试，能跑多 CRTC + 13 按键鼠标了。

### 9.3 开发者

- `Ones()` 函数被导出回 Xserver（之前被内联掉又回滚）。
- `xf86bigfont` 模块**默认**编译进一个 build 集合（修了几处 `-Werror=unused-variable` 构建错误）。
- `meson` 中 `AF_INET6` 检查更严格（适配更严的编译器标志）。

---

## 十、26.1 vs 21.1 的完整新增清单

按邮件原文摘录：

```
- Removal of autoconf/automake build system, leaving only meson
- Add support for DPMSInfoNotify event from DPMS 1.2
- Add support for XFixes 6.1 & AllowForceTerminate option in xorg.conf
- Disallow byte-swapped clients by default
- Disable font server connections by default
- Xorg: Add DRM platform for BSD
- Xorg: Move default non-root-user log files to $XDG_STATE_HOME/xorg
- Xvfb: Add multiple CRTC support
- Xvfb: Support up to 13 mouse buttons
- more tests included
```

维护者结尾说：

> Testing of this release candidate would be greatly appreciated. Please report any issues at: https://gitlab.freedesktop.org/xorg/xserver/-/issues

---

## 十一、为什么"五年来第一个特性发布"是大事

X.Org Server 21.1 已经是 2021 年的事了。五年里 X.Org 项目发生了很多事：Wayland 成为多数主流桌面的默认选择，Xwayland 接过老 X server 的"跑 X 应用"职责，X.Org 基金会改组、维护团队收缩……

在这种背景下，xorg-server 26.1 仍然能做出**"砍 2.1 万行遗留代码 + 换构建系统 + 拆分子项目"**这种结构性改动，说明：

1. **维护者**（Oracle、Red Hat 等公司里坚持做 X 的人）还有心力做大事。
2. **使用场景**（CI、嵌入式、特殊硬件）仍然多到值得一个独立 release line。
3. **打包者 + 发行版**仍然愿意配合——meson-only 这种破坏性变化能落地，证明下游还能跟上。

这三点任何一条松动，26.1 就只能继续停留在 RC1，不会出 26.1.0。

下一个值得关注的是：**Xwayland 26.1 的 rootful clipboard/primary selection bridge** 进入生产路径——它让 Wayland 桌面的"复制粘贴"跨 Xwayland 桥接工作更可靠。

---

## 十二、下载与升级

- **tarball**：https://xorg.freedesktop.org/archive/individual/xserver/xorg-server-26.0.99.901.tar.xz
- **SHA256**：`24f16885a6152d9abb384a90c52b2e417fafdc474ff914d8faddf6b6b9566c45`
- **PGP**：tarball 同目录 .sig 文件
- **报告 issue**：https://gitlab.freedesktop.org/xorg/xserver/-/issues
- **推荐依赖**：libpciaccess ≥ 0.19（2026 年 3 月发布）

构建命令（meson-only）：

```bash
meson setup build --prefix=/usr
ninja -C build
sudo ninja -C build install
```

---

**参考资料**：

1. X.Org 邮件列表 RC1 公告：https://lists.x.org/archives/xorg/2026-August/062281.html
2. Phoronix：https://www.phoronix.com/news/X.Org-Server-26.1-RC1
3. linuxcompatible.org：https://www.linuxcompatible.org/story/xorg-server-2610-release-candidate-drops-xwayland-kills-autoconf-and-strips-legacy-code/
4. Xwayland 26.1 RC1 公告：https://lists.x.org/archives/xorg/2026-August/062280.html
5. X.Org 源码：https://gitlab.freedesktop.org/xorg/xserver

---

*本文基于 X.Org Server 26.0.99.901 RC1 公告、Phoronix 报道与 linuxcompatible.org 解读整理，旨在为中国开发者提供快速理解和参考。*

*作者观点不代表任何厂商立场，仅供技术讨论参考。X.Org Server 26.1 仍处 RC 阶段，正式发布前 API / 配置可能继续调整。*