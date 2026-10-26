---
title: "Linux 桌面的前三十年：十次转折，和一个反复出现的教训"
date: 2026-10-26
slug: linux-desktop-first-decade-ten-turning-points
tags: [Linux桌面, 历史, Debian, RedHat, KDE, GNOME, Knoppix, Ubuntu, Compiz, EeePC, Xandros, Plasma, GNOME3, Unity, Cinnamon, MATE, 许可证, Qt]
category: Linux/运维
author: FreeLAMP.com
original_source: "How-To Geek《15 historic moments that shaped the Linux desktop we use today》前 10 节（已核实部分）+ 原文导语与评论区"
original_author: "Umair Khurshid（How-To Geek）"
original_date: 2026-10-23
original_url: "https://www.howtogeek.com/15-moments-that-shaped-the-linux-desktop-we-use-today/"
description: "How-To Geek 这篇梳理 Linux 桌面史的文章，标题写 15 个时刻，但页面上服务端渲染出来的只有前 10 个（Debian 1993 到 Linux Mint Cinnamon 2011–2012），后 5 个是懒加载的、取不到。本文只写已核实的这 10 个时刻，主线是：Linux 桌面的转折点几乎都不是「哪个界面更漂亮」，而是「谁拥有决定权、谁可以随时离开」——Qt 许可证引发 GNOME 分家、Compiz 演示了 GPU 能力、Eee PC 给了 Linux 唯一的消费级窗口、KDE 4 大改翻车、GNOME 3 反冲催生 Cinnamon/MATE。"
published: true
---

> 来源：[How-To Geek：15 historic moments that shaped the Linux desktop we use today](https://www.howtogeek.com/15-moments-that-shaped-the-linux-desktop-we-use-today/)（**Umair Khurshid，2026-10-23 16:00 EDT**）
> ⚠️ **取数说明（必须先说清）**：这篇文章标题写「15 个时刻」，但**页面上服务端渲染出来的正文只有前 10 个**（Debian 1993 → Linux Mint Cinnamon 2011–2012），**第 11–15 个是懒加载的**，我尝试了多种抓取路径都只拿到前 10 节；**原始 HTML 全文中 `Steam`/`Wayland`/`Flatpak`/`Proton` 出现次数均为 0**，可佐证后 5 节确实不在首屏 HTML 里。
> **所以本文只写已核实的 10 个时刻**，标题与口径据此收敛。原文导语里点名的「Microsoft 的开发者工具」与「Valve 的游戏硬件」属于后 5 节，**本文不臆测其内容**。
> 本文为**解读**。第二、三、四节的判断是笔者补充。

## 一句话结论

**这 10 个时刻里，几乎没有一个是「某个界面更漂亮」带来的。**

**真正改变局面的每一次，都是「谁拥有决定权、谁可以随时离开」这个问题被重新回答了一次：**

| 时刻 | 表面事件 | 底层的权力问题 |
|---|---|---|
| Debian（1993） | 一个发行版诞生 | **谁决定一个包能不能进仓库** |
| Red Hat（1994–97） | 商业支持出现 | **谁为「可靠」买单** |
| KDE / GNOME（1996–99） | 两个桌面 | **工具链的许可证说了算** |
| Knoppix（2000–03） | 免安装 CD | **谁承担「试错」的风险** |
| Ubuntu（2004） | 好装好用 | **谁决定默认装什么** |
| Compiz（2006–07） | 3D 桌面特效 | **谁拥有显示栈** |
| Eee PC（2007） | 廉价 netbook | **硬件厂商敢不敢预装** |
| KDE 4（2008） | 大改版翻车 | **谁为大改版的不成熟买单** |
| GNOME 3 / Unity（2011） | 界面反冲 | **用户的旧习惯算不算数** |
| Cinnamon（2011–12） | 传统桌面回潮 | **「离开」的成本够不够低** |

**而这 10 次里最贵的一次代价，是 KDE 4；最有效的一次反击，是 Cinnamon。**

## 一、先把原文导语里那句关键的话读准

**原文导语这样划分它要讲的东西：**

> **「Some of the biggest moments in Linux desktop history came from familiar projects such as Debian, Red Hat, Ubuntu, GNOME, and KDE. Others came from unexpected places, including cheap netbooks, Microsoft's developer tools, and Valve's gaming hardware.」**

**这句话本身透露了一个信息量很大的分类法：Linux 桌面史上的转折点，一半来自「我们已经很熟悉的项目」，另一半来自「完全意想不到的地方」。**

**而属于后者、且在我们已核实的这 10 节里就已经出现的，是两个：**

1. **廉价 netbook（2007，ASUS Eee PC）** —— **这是 Linux 历史上唯一一次大规模进入消费级零售货架的机会**；
2. **Compiz（2006–07）** —— **这是硬件加速第一次被当成「桌面竞争力」来演示**。

**而更值得说的一句在原文开篇：**

> **「Today, you can install a modern Linux distro, open a browser, connect your Bluetooth headphones, and get on with your work. That experience is the result of decades of development, arguments, ambitious redesigns, and a few spectacular failures.」**

**注意最后那三个词：「a few spectacular failures」（几次壮观的失败）。**

**原文把「失败」和「发展」并列写成这段体验的来源 —— 这不是修辞。** **因为接下来你会看到：GNOME 这个今天占据 Linux 桌面半壁江山的项目，在原文的排序里是第 3、10 两个时刻；而它当年最著名的那个「壮观的失败」，就是 GNOME 3 带来的反冲。**

## 二、第一个真正的转折：许可证引发的分家（1996–1999）

**原文把 KDE 和 GNOME 放在同一条时间线上：**

> **「KDE began in 1996, and the GNOME Project followed in 1997. KDE 1.0 arrived in July 1998, while GNOME 1.0 followed in March 1999.」**
>
> **「Their development also reflected an important debate about software freedom. GNOME emerged partly in response to concerns about the licensing of Qt, the toolkit used by early KDE. Qt later became available under free software terms, but the two projects continued to develop their own approaches to the desktop.」**

**这段话的因果链值得逐字读：**

1. **KDE 起步（1996），靠 Qt 工具kit；**
2. **GNOME 成立（1997），起因之一是对 Qt 许可证的担忧；**
3. **KDE 1.0（1998-07），GNOME 1.0（1999-03）；**
4. **Qt 后来以自由软件条款发布了 —— 但两家从此各走各路。**

**第 4 点是这段历史里最有意思的一句。**

**因为它说明：GNOME 的诞生看起来像一场「重复造轮子」，但它真正确立的是一种新的权力结构 —— 「如果基础工具链的许可证变了，我还能不能走？」**

**Qt 后来确实自由了，所以 GNOME 没有变成「重复劳动」。但它逼出了一件事：Linux 桌面从此有了两个可以互相制衡的实现，而不是一个可以随时改变规则的实现。**

**而这一节之所以排在桌面史的前列，是因为它同时定义了这个生态后来的全部机制：**

- **发行版可以换桌面（Debian → KDE，后来 → GNOME）；**
- **桌面可以被替换而不用重装系统；**
- **任何一个桌面都可以「因为不信任而分家」，然后自己也长成一方。**

**而这个机制在 15 年后被 Cinnamon 完整地又用了一遍 —— 这是本文最后一节要讲的事，也是我认为整篇文章最值得看的地方。**

## 三、Debian 与 Red Hat：一个定规则，一个定价格

### 3.1 Debian（1993）：把「谁能进仓库」这件事制度化

**原文对 Debian 的定位很精确：**

> **「In August 1993, Ian Murdock started the Debian Project with the idea of building a Linux distro through open collaboration.」**
>
> **「APT arrived with Debian 2.1 in 1999, several years after the project began, providing a more convenient way to acquire and install packages.」**
>
> **「The important contribution was the ecosystem Debian developed around its software. Its packaging policies, dependency management, release process, and community governance gave other projects a foundation they could build upon. A decision made in the Debian ecosystem could eventually affect millions of users running completely different distros.」**

**注意最后一句的量级：「一个在 Debian 生态里做出的决定，最终会影响几百万个跑着完全不同发行版的用户」。**

**这个「间接影响」的结构，源头是三件很具体的事：**

1. **打包政策（packaging policy）** —— **规定一个包长什么样、该带哪些元数据、能不能被上游接受**；
2. **依赖管理** —— **让「装软件」这件事变成一个可自动化的动作，而不是用户手工解依赖**；
3. **社区治理** —— **决定「谁有资格做决定」**。

**而 APT 出现在 1999 年这件事本身很说明问题：项目成立 6 年后才把「获取和安装软件」这件事彻底解决。**

**换句话说，Debian 前 6 年主要在解决「怎么让社区协作打包」这个更难的问题，「让用户装软件顺手」是后来才补上的一层。** **这个顺序本身就是一个教训 —— 而且它会在 20 年后以另一种形式重演（见第四节 Compiz 与驱动）。**

### 3.2 Red Hat（1994–97）：给「可靠」标一个价

**原文对 Red Hat 的描述，关键词是「professionally supported」：**

> **「Red Hat Linux 5.0 arrived in December 1997, during a period when Linux was gaining recognition in the technology industry.」**
>
> **「Commercial support mattered to desktop users, too. It encouraged software vendors to consider Linux as a platform and gave customers another way to obtain a working system.」**
>
> **「Red Hat's influence continued through Fedora, which became an important community project, and Red Hat Enterprise Linux, which focused on long-term support and enterprise deployments.」**

**这里的结构同样值得拆开看：**

- **Red Hat 的商业化不是「把 Linux 卖出去」，而是「为『有人负责』这件事标价」**；
- **而它的组织形式是一分为二：Fedora（社区探索）+ RHEL（长期支持）** —— **和后来几乎所有商业 Linux 发行版的双轨制一模一样**；
- **「It encouraged software vendors to consider Linux as a platform」—— 这一句是重点：商业支持真正的副作用不是终端用户爽了，而是**让软件厂商愿意把 Linux 当成一个值得支持的平台**。

**而这恰恰是 Debian 那套机制的价值所在：Debian 定规则，Red Hat 让遵守规则有人付钱。** **两条线并行走，才有了「1990 年代末到 2000 年代初的 Linux 桌面是可用的」这个结果。**

## 四、Knoppix 与 Ubuntu：两个「降低门槛」的动作（2000–2004）

### 4.1 Knoppix（2000–03）：把「试错的风险」从用户身上拿走

**原文这一节的价值在于它讲清了一件事：**

> **「Installing an operating system used to feel like a major commitment. Users needed installation media, enough free disk space, and some confidence that they could recover their existing system if something went wrong. Knoppix helped change that experience by popularizing a Linux environment that could boot directly from a CD.」**
>
> **「A live CD let people explore a working Linux desktop without immediately changing their hard drive. They could open applications, browse files, and test their hardware before deciding whether to install anything. Live environments also became useful for recovering files from damaged systems and troubleshooting computers that refused to boot.」**

**注意「some confidence that they could recover their existing system」这一句。**

**安装操作系统的真正成本，从来不是时间，而是「不可逆」。** **Knoppix 把这个不可逆性消掉了。**

**而原文还点出一个副产品，这个副产品在今天更重要了：**

> **「Live environments also became useful for recovering files from damaged systems and troubleshooting computers that refused to boot.」**

**「live 环境成了救砖工具」—— 这是今天每个 Linux 发行版都提供 live ISO 的最主要理由，而不是「让用户试一下」。**

### 4.2 Ubuntu（2004）：把「默认装什么」的决定权收到自己手里

**原文对 Ubuntu 的记述里藏着一个很容易被忽略的细节：**

> **「Ubuntu 4.10, codenamed Warty Warthog, launched in October 2004. Built on Debian, Ubuntu focused on regular releases, a curated selection of applications, and a straightforward installation experience. Canonical also offered ShipIt, a service through which people could request free installation CDs.」**
>
> **「That last detail is easy to overlook now, when downloading a large ISO is routine. In 2004, a free CD could be a practical way to get Linux into the hands of someone with a slow connection or limited access to broadband.」**
>
> **「Ubuntu helped establish the idea that a distro could deliver a complete desktop experience without expecting users to assemble everything themselves.」**

**三个关键词：**

1. **「curated selection of applications」（精选应用集）** —— **这正是「谁决定默认装什么」这个权力问题的答案**：发行版替用户做了一轮筛选。
2. **ShipIt 免费寄 CD** —— **原文特意说「这件事现在容易被忽略」，但它揭示的是带宽门槛：在 2004 年，一个没有宽带的人，拿到 Linux 的物理路径是一张免费 CD。**
3. **「without expecting users to assemble everything themselves」** —— **Ubuntu 真正创立的那种发行版形态：不是给你一套零件，是给你一台能用的机器。**

**而这一节在原文里还承担了一个额外功能：它是「血缘线」的开端。**

> **「Ubuntu built on Debian, and Ubuntu later became the foundation for Linux Mint and Pop!_OS.」**

**Debian → Ubuntu → Linux Mint / Pop!_OS，这条线在第七节的 Cinnamon 会再出现一次，而它的走向恰好是「越走离 Debian 越远，也越离用户越近」。**

## 五、Compiz 与 Eee PC：Linux 唯一一次站在零售货架上（2006–2007）

### 5.1 Compiz（2006–07）：第一次把 GPU 能力当成桌面卖点

**原文的措辞很有意思：**

> **「For a while, one of the easiest ways to impress someone with a Linux desktop was to rotate the entire workspace like a cube.」**
>
> **「These effects demonstrated what hardware-accelerated graphics could do. A compositing window manager could render windows into a composed desktop scene, making it possible to add animations and visual effects that traditional window managers did not provide in the same way.」**
>
> **「Compiz became a memorable demonstration of Linux graphics capabilities, although getting it working smoothly depended on the graphics hardware and drivers.」**

**最后半句是重点：「although getting it working smoothly depended on the graphics hardware and drivers」。**

**我把它和第四节 Debian 的「6 年后才做出 APT」放在一起看，会得到一个不太好听但很准的结论：**

> **Linux 桌面史上有两次「能力先于工程」的时刻：一次是 1999 年前的 Debian（先把治理和打包做对，工具才补上），一次是 2006 年的 Compiz（特效先跑起来，驱动和硬件适配后来才跟上）。**

**而更值得注意的是 Compiz 的最终归宿：它的合成器后来被并入 GNOME 本身。** **也就是说，一个「炫技项目」最终变成了基础设施 —— 这在 Linux 桌面史上是极少数走完这条路的案例（对比 Compiz 的很多同期同类项目都没能进主干）。**

### 5.2 Eee PC（2007）：一年左右的窗口期

**原文对 Eee PC 这一节的定性非常克制：**

> **「In 2007, ASUS launched the Eee PC, a small, inexpensive laptop that shipped with Xandros Linux. The original Eee PC 701 offered a compact display, limited storage, and modest hardware at a price that made it attractive to students, travelers, and people who wanted a second computer.」**
>
> **「The netbook boom created a rare opportunity for Linux on consumer hardware. A lightweight operating system made sense on a machine with limited storage and memory, and buyers could open the lid and start using the computer without installing an operating system themselves.」**
>
> **「For a brief period, Linux had a visible place in mainstream consumer computing. People could buy an inexpensive laptop that came with Linux already installed, rather than purchasing a Windows machine and replacing its operating system themselves.」**

**「For a brief period」—— 原文自己强调的是「短暂」。**

**但我认为这里有一个比原文更值得写的结论，而且它正好能给今天「旧机器装 Linux」这篇做注脚：**

**2007 年的 netbook 浪潮，几乎是 Linux 桌面史上唯一一个「轻量 = 卖点」而不是「轻量 = 妥协」的时间窗口。**

**因为在那批机器上：**
- **磁盘小、内存小 → 轻量发行版不是「凑合用」，而是「刚好合适」；**
- **厂商愿意预装 → 用户不需要自己做选择，也不需要懂「双系统」；**
- **价格敏感人群 → 他们要的本来就不是全套功能。**

**而 2026 年重新出现的「旧机器装轻量 Linux」浪潮，和 2007 年有一个关键差别：**

| | 2007 netbook | 2026 旧机器 |
|---|---|---|
| **谁做决定** | **厂商预装，用户零决策** | **用户自己装，自己做选择** |
| **风险承担** | 厂商承担 | 用户承担 |
| **可用性来源** | 硬件与发行版天生匹配 | 软件生态已经补齐（Flatpak/Flathub） |

**「谁来承担试错成本」这一栏，正是 Knoppix 在 2000 年代解决的那个老问题 —— 今天它以 live ISO 的形式又活了一遍。**

## 六、两次大改：KDE 4 与 GNOME 3（2008 / 2011）

**这两次是原文 10 节里最值得对照读的两节，因为它们的形状几乎一模一样。**

### 6.1 KDE 4（2008-01）：大改版的代价

**原文的措辞非常克制，但信息量很大：**

> **「KDE 4.0 arrived in January 2008 with a substantial redesign of the KDE desktop. Its new Plasma workspace introduced a different approach to panels, desktop widgets, and the overall desktop experience. The release also brought changes to KDE's libraries and technologies for hardware detection and multimedia handling.」**
>
> **「There was a lot to like about the direction. Plasma gave KDE developers a more flexible foundation, while the new architecture created opportunities to develop features that would have been harder to maintain in the older desktop.」**
>
> **「The trouble was that KDE 4.0 arrived while much of that work was still in progress. Users upgrading from KDE 3.5 encountered missing features, rough edges, and applications that had not yet caught up with the new environment.」**
>
> **「The experience remains a useful reminder that major desktop rewrites can take time to pay off.」**

**把「有太多可取之处」和「用户遭遇缺失功能、粗糙边缘、应用跟不上」放在一起写，是这段文字的精妙之处 —— 它承认方向正确，同时承认代价由用户承担。**

**而我认为这里可以提炼出一条更硬的规律：**

> **大改版的成本，从来不由开发者承担，而由「正在用旧版干活的人」承担。**

**KDE 4 的问题是：它是一次「先换地基，再盖楼」的重写，而地基换好时，楼还没盖完。** **当时正靠 KDE 3.5 干活的人（大量 KDE 发行版的用户）被夹在中间。**

### 6.2 GNOME 3 与 Ubuntu Unity（2011）：把用户的旧习惯当成不重要的东西

**原文对这次反冲的定性比 KDE 4 那节更重：**

> **「In 2011, two major Linux desktop projects changed the way people interacted with their computers. GNOME 3 introduced GNOME Shell, with its Activities overview and search-oriented workflow. Ubuntu 11.04 adopted Unity, which featured a vertical launcher and a Dash interface for finding applications and content.」**
>
> **「Both projects reflected a shift toward interfaces designed to work across different screen sizes and input methods. For users accustomed to traditional panels, application menus, and familiar window-management habits, the changes could feel disruptive.」**
>
> **「The resulting debate became one of the most recognizable controversies in Linux desktop history.」**
>
> **「The controversy mattered because desktop environments occupy such a central place in the Linux experience. A distro can update its kernel, libraries, and drivers without dramatically changing how the desktop looks. A new shell changes the way people interact with almost every application, so users notice it immediately.」**

**最后那段解释，是我认为整篇文章里最好的一句论证，值得单独拎出来：**

> **「一个发行版可以更新内核、库和驱动，而桌面看起来完全不变。但一个新的 shell 改变了你和几乎每一个应用交互的方式，所以用户立刻就注意到了。」**

**这解释了为什么「桌面」这个层面的改动，代价永远比「内核层面的改动」大得多 —— 即使后者技术难度高得多。**

**而「原本是为跨尺寸、跨输入方式设计的」（designed to work across different screen sizes and input methods）这个理由，在今天看其实是对的。** **触屏笔记本、二合一设备、小尺寸副屏的普及让活动概览那套逻辑变得必要。**

**问题不在方向，在于「替换」的方式。**

## 七、Cinnamon（2011–2012）：最有意思的一次「用脚投票」

**原文第 10 节，我认为是这 10 节里写得最好的一节：**

> **「Linux Mint had already built a reputation for making Linux approachable, particularly for people who wanted a familiar desktop and useful applications ready to go. The arrival of GNOME 3 gave the project an opportunity to develop that identity further.」**
>
> **「Cinnamon began in 2011 as a project to provide a more traditional desktop experience using GNOME technologies. It retained a conventional panel, application menu, system tray, and familiar window-management workflow. Linux Mint 13 Maya, released in May 2012, offered Cinnamon alongside MATE, which continued the GNOME 2 codebase.」**
>
> **「Cinnamon developed into a desktop environment with its own features, tools, and design decisions. It was not simply an attempt to freeze the desktop in the past.」**
>
> **「This is one of the most interesting outcomes of the GNOME 3 era. A major interface change helped create demand for a desktop that eventually developed its own identity.」**

**「It was not simply an attempt to freeze the desktop in the past.」（它不只是一个把旧桌面冻结起来的尝试。）**

**这一句是 Cinnamon 全部历史价值的关键。如果 Cinnamon 真的只是「把 GNOME 2 复活」，它早就死了。**

**而把它和第二节的 GNOME 诞生放在一起看，一个完整的闭环出现了：**

| 年份 | 事件 | 逻辑 |
|---|---|---|
| **1996–97** | KDE 依赖 Qt；**GNOME 因担心 Qt 许可证而成立** | 「如果基础工具链的许可证变了，我还能不能走？」→ **分家** |
| **2011** | GNOME 3 改写交互方式，用户反冲 | 「我可以不用 GNOME 3」→ **MATE 承接 GNOME 2 的代码** |
| **2011–12** | **Cinnamon 用 GNOME 的技术栈做一个传统桌面** | 「我可以既用新工具，又留旧习惯」→ **长成独立生态** |

**这是同一个动作的第二次发生：上一次是「因为不信任而分家」，这一次是「因为不信任而复制」。**

**而 Mint 13 Maya 同时提供 Cinnamon 和 MATE 这件事，是这个生态成熟的标志 —— 它意味着用户不必再在「新 GNOME」和「旧 GNOME」之间做一次性的、不可逆的投票。**

**这一点在今天依然成立，而且依然是 Linux 桌面对新用户最友好的一个设计：**

- **发行版提供多个桌面（Mint 有 Cinnamon / MATE / Xfce）**；
- **用户随时可以切换桌面而不重装系统**；
- **桌面之间共享同一套底层工具，用户态数据不搬家。**

**这正是第二节「GNOME 因许可证分家」时建立的机制，在 2012 年被用在了正向上。**

**而这也回答了我对第二节那个问题的看法：Qt 后来自由了，GNOME 没有白分家 —— 因为 GNOME 带来的不是「另一个桌面」，而是「桌面可以被替换」这个前提本身。**

## 八、把这 10 个时刻连起来看

**如果只留一条结论，我会留这个：**

> **Linux 桌面史上的每一次真正的进步，都是「把决定权交出去」带来的，而不是「把界面做得更漂亮」带来的。**

**逐条对应：**

| 时刻 | 交出去的「决定权」 |
|---|---|
| **Debian** | 包的准入标准交给社区治理流程，而不是维护者的个人口味 |
| **Red Hat** | 「可靠」这件事交给付费承诺，形成支持与社区的分工 |
| **KDE / GNOME** | 基础工具链的许可证不决定整个桌面的生死 |
| **Knoppix** | 试错的风险从用户身上转移到介质上 |
| **Ubuntu** | 默认装什么由发行版决定，用户不必自己拼装 |
| **Compiz** | 显示栈的能力可以由第三方实现，不必等内核团队 |
| **Eee PC** | 选什么的权力交给消费者，但由厂商先做一次筛选 |
| **KDE 4** | ⚠️ **反例**：把「新地基 vs 旧用户」的矛盾留给了用户 |
| **GNOME 3 / Unity** | ⚠️ **反例**：把「旧习惯不重要」当成了前提 |
| **Cinnamon** | 桌面可以换，用户不必在「新旧」之间做不可逆投票 |

**两个反例的共同点也值得记：KDE 4 和 GNOME 3 都是「设计者认为这是正确方向」的项目，但它们都忽略了同一件事 —— **正在用旧版的人不是背景，他们就是用户。** **而两者的补救方式也惊人地相似：Linux Mint 用两个桌面（两个 DE）把用户接住了，而 KDE 4 的补救是「后续版本慢慢成熟」（原文原话：「later KDE 4 releases became considerably more mature」）。**

## 九、还没讲完的那 5 个时刻

**按原文导语，后 5 个时刻来自三个地方：**

1. **熟悉的项目**（Debian、Red Hat、Ubuntu、GNOME、KDE 之外的部分）；
2. **Microsoft 的开发者工具** —— **几乎肯定是 WSL（2016 起）及其带来的「Windows 上的 Linux」**；
3. **Valve 的游戏硬件** —— **几乎肯定是 Steam Deck / SteamOS（2022 起）**。

**后两条我这里没有原文材料，所以不做断言。但结合前面 10 节的逻辑，可以提出一个可检验的猜想：**

> **如果这 10 节的规律是「把决定权交出去」，那么后 5 节的共性大概会是 —— 把「Linux 的入口」放到了用户已经在的地方：**
> - **WSL 把入口放进 Windows 任务栏和开始菜单（不要求用户改系统）；**
> - **Steam Deck 把入口放进一台开箱即用的设备（不要求用户做选择）。**

**而这两种做法，在本文的表格里都能找到对应：一个是 Knoppix 的「降低试错成本」，一个是 Eee PC 的「厂商替用户做一次筛选」。**

**⚠️ 这只是基于前 10 节逻辑的推演，不是原文内容。如果你要写这 5 个时刻，我建议等我把懒加载那部分抓到原文再写，不要用推演冒充引用。**

**（另：原文评论区有一条很值得一读的读者留言，正好点到了 WSL 与历史的对位关系 ——「我 2008 年用 Ubuntu 转投全职 Linux，看着这份名单长大，包括 2001 年 Ballmer 宣称 Linux 是癌症的那个时期。」而另一条读者留言则直接说出了 EEE 策略和现在的分歧：「微软有很长的历史，就是靠给竞争技术做授权增强来吸收或压制它们。」）**

## Sources

- How-To Geek 原文：https://www.howtogeek.com/15-moments-that-shaped-the-linux-desktop-we-use-today/
- 原文作者：Umair Khurshid（2026-10-23 16:00 EDT）
- 已核实小节：Debian(1993) / Red Hat(1994–97) / KDE+GNOME(1996–99) / Knoppix live CD(2000–03) / Ubuntu(2004) / Compiz(2006–07) / ASUS Eee PC(2007) / KDE 4(2008) / GNOME 3 + Ubuntu Unity(2011) / Linux Mint Cinnamon(2011–12)

---

（说明：本文所有引号内内容均为 How-To Geek 原文引用；第七节的「闭环表格」与第八节的归纳为笔者解读；第九节的后 5 个时刻已明确标注为未取到原文的推演，不作为事实陈述。）
