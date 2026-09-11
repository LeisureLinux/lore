# GNU Automake 1.19 发布：攒了一年多的修复，终于还上一个 14 年的老 bug

> 译自 Phoronix《[GNU Automake 1.19 Released With More Than One Year Worth Of Fixes](https://www.phoronix.com/news/GNU-Automake-1.19)》，作者 Michael Larabel，2026 年 9 月 10 日。

对那些仍在用 GNU Automake（而非 Meson 或 CMake）做构建系统的项目来说，Automake 1.19 于今天发布——这是 15 个月来的第一个新版本。在这个版本包含的众多修复中，有一个 bug 的历史可以追溯到 14 年前。

自上一版 Automake 1.18.1 以来已过去一年多，而 Automake 1.19 只有一个新功能：*AM_OPTIONAL_AUTOMAKE*。这个 autoconf 宏允许传入一个列表，比如 dist-xz、dist-zstd、dist-bzip3 等；随后它会根据对应压缩工具是否可用，逐项构建压缩包——可用的就打，不可用的安静跳过，而不是报错退出。

在 bug 修复方面，Automake 1.19 现在能够识别 COPYINGv2、COPYINGv3 等文件，并把它们当作传统的 COPYING 文件一样自动纳入发布归档。这一改动意在改善与 GNU GMP 等其他 GNU 项目的兼容性。

此外，`make dist-bzip2 dist-xz` 命令现在可以正常工作了：此前未压缩的 tarball 在第一个目标完成后就被删掉，导致第二个目标无从下手；现在它会被正确共享，同时用于 XZ 和 Bzip2 两种归档的创建。这个修复对应的是那份[14 年前的 bug 报告](https://debbugs.gnu.org/cgi/bugreport.cgi?bug=10975)。

Automake 1.19 还改进了对 BusyBox Tar 的检测；`make dist` 现在会在 Tar 失败时合理地报错退出，而不是「成功」产出一个被截断的归档；另有其他多项修复。

GNU Automake 1.19 可从 [savannah.gnu.org](https://cgit.git.savannah.gnu.org/cgit/automake.git/tag/?h=v1.19) 获取。

## 快速要点

| 要点 | 内容 |
|---|---|
| 版本 | GNU Automake 1.19（上一版 1.18.1 间隔 15 个月） |
| 唯一新功能 | `AM_OPTIONAL_AUTOMAKE` 宏：按工具可用性跳过 dist-xz / dist-zstd / dist-bzip3 等归档目标 |
| 年代最久修复 | `make dist-bzip2 dist-xz` 共享中间 tarball，对应 2012 年（14 年前）的 [bug #10975](https://debbugs.gnu.org/cgi/bugreport.cgi?bug=10975) |
| 其他修复 | 识别 COPYINGv2/COPYINGv3 并自动纳入归档；更好检测 BusyBox Tar；Tar 失败时 `make dist` 如实报错而非产出截断包 |
| 获取 | [savannah.gnu.org automake v1.19](https://cgit.git.savannah.gnu.org/cgit/automake.git/tag/?h=v1.19) |

## 我们的解读：老树的年轮里也有信息

**1. 15 个月一版 + 一个新功能，这是维护模式的节奏。** Automake 和它的老搭档 Autoconf 一样，早就过了功能竞赛的年纪。1.19 的「一个新功能」与其说是功能，不如说是给打包者的一点便利：多格式发布归档时不必再为环境缺某个压缩工具而整个构建失败。这种「可选目标」语义本质上是承认现实——2026 年的构建环境千差万别，容器里未必有 bzip3。

**2. 14 年的 bug 修了，值得注意的不是修，而是「有人还在用」。** bug #10975 报告于 2012 年——那一年 Automake 还是绝大多数 GNU 项目的标配。十四年间没人修，不是技术多难（修复思路就是让中间 tarball 在多个 dist 目标间共享），而是缺少足够多的人把它推到「值得发版」的优先级。老基础设施的维护经济学：小 bug 的修复窗口往往取决于「是否恰好凑够一批其他改动」。

**3. `make dist` 静默产出截断归档，是最该修的那类 bug。** Tar 失败还报成功，下游拿到残缺 tarball 继续走 CI、签名、发布——这类「假成功」在供应链视角下的危害远大于构建直接报错。这次顺手修掉，配合上一条 BusyBox Tar 检测改进，方向都是「让失败如实地失败」。

**4. COPYINGv2/COPYINGv3 的识别是个小小的现实适配。** GPL v2/v3 文本文件在 GMP 等项目里就不叫 COPYING，之前 Automake 不认，打包者得手动塞进 EXTRA_DIST。这类修复没有技术含量，但对用 Automake 的存量项目来说每次都能省一点事——老工具的更新就是靠这种积少成多。

**5. 对信创与老项目维护者的提醒。** 国产化改造中大量存量代码仍挂着 autotools 构建链，Automake 1.19 属于「可以升级、风险极低、顺手获益」的那类：尤其如果你们的构建流程里有多格式归档需求或用到 BusyBox 环境（嵌入式 rootfs 内自建构建时常见），这个版本值得跟进。不必期待更多——它大概率会继续以年为单位更新。
