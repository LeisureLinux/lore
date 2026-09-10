> 本文译自 Phoronix 2026 年 9 月 10 日报道《X.Org Server 26.1 Moves Closer To Release As Half-Decade Update》（作者 Michael Larabel）。原文链接：https://www.phoronix.com/news/X.Org-Server-26.1-Released

# X.Org Server 26.1 进 RC2：暌违五年的大版本，离正式发布只差临门一脚

X.Org Server 26.1 稳定版越来越近了。这是自 **2021 年 10 月 X.Org Server 21.1** 发布以来，第一个被打上 tag 的新功能版本。过去五年里合并进去的新特性、大量代码回退（revert）和海量 bug 修复，都将在 26.1 稳定版里一次性兑现。

年初，Oracle 的 **Alan Coopersmith** 曾立下"2026 年出一个新 xorg-server 版本"的愿景，如今看来这个目标真的要达成了。上个月我们见到了 **X.Org Server 26.1 RC1**，而本周则迎来了第二个候选版本。

## 这版 RC2 改了什么

根据公告，26.1 的第二个候选版本带来：

- **XKB**（键盘扩展）相关修复
- **X Input**（输入子系统）相关修复
- 其他散布各处的小修小补
- **Meson 构建系统**更新

此外，它还**抬高了 X.Org Server 的 ABI 版本号**——既包括扩展（extension）版本，也包括视频驱动（video driver）版本。这一点对 **NVIDIA 闭源驱动**以及其它依赖锁定特定 ABI 版本的下游方尤其有用。

完整的修复清单见 xorg-server 26.0.99.902 发布公告（xorg 邮件列表 2026 年 9 月归档）。

同一天，还有 **XWayland 26.1 RC2** 也发布了。

## 我们的解读

**1. 五年一更，本身就是 X.Org 现状的注脚。** X.Org Server 早已进入"维护模式"——桌面世界里 Wayland 是默认的当红炸子鸡，X.Org 的节奏慢到五年才攒出一个功能版本。但"慢"不等于"无关紧要"：大量遗留硬件、远程桌面、NVIDIA 闭源驱动栈、各类嵌入式和工业场景，仍然牢牢长在 X.Org 上。它退居二线，却没退场。

**2. ABI 抬版本，真正的受益者是 NVIDIA 闭源栈。** 开源驱动（如 modesetting、各 DDX）跟上游同步容易；真正卡 ABI 的是 NVIDIA 的打包驱动——它按特定 ABI 版本编译，X.Org 一升 ABI，闭源驱动就得跟着发新包。这次显式地 bump 扩展和视频驱动 ABI，等于给 NVIDIA 那套"系统自带旧 X + 自己带新驱动"的组合提前铺好路。这也是为什么 Phoronix 特意点名 NVIDIA packaged driver support。

**3. "大量 revert" 比 "大量新增" 更值得玩味。** 原文提到五年里既有新特性、也有"many code reverts"。对一个衰老的代码库来说，回退往往意味着：新东西塞进去后发现破坏兼容、引发回归，只能撤。X.Org 这种牵一发动全身的显示服务器，稳定性权重远高于功能增量——能活着发版，比发多少新功能都重要。

**4. XWayland 同步 RC2，说明"X 兼容层"才是 X.Org 当下的主战场。** Wayland 桌面上跑不了原生 X 的程序，全靠 XWayland 兜底。XWayland 和 X.Org Server 共用大量代码、几乎同步发版，恰恰印证了：X.Org 的"未来"主要不是作为独立显示服务器，而是作为 Wayland 世界里的那个 X 兼容垫片继续存在。

**5. 对折腾信创/老旧显卡的人一句实在话：** 如果你还在 UOS、麒麟等环境里跑 X.Org（很多国产化桌面默认仍是 X11 会话），26.1 这类更新带来的输入/键盘修复，比表面看更有意义——它就是那种"你不会注意到、但一旦出 bug 就卡死登录"的底层组件。等发行版把 26.1 拉进仓库，远程桌面和老显卡的体验会悄悄稳一截。
