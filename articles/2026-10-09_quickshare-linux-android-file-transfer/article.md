---
title: "Quick Share 什么都好，除了它没有 Linux 客户端：手机与 PC 互传的四种走法"
date: 2026-10-09
slug: quickshare-linux-android-file-transfer
tags: [Quick Share, Nearby Share, 文件传输, Android, Linux, Packet, rquickshare, LocalSend, KDE Connect, Wi-Fi Direct, Wi-Fi Aware, 互传联盟, AirDrop]
category: Linux/运维
author: FreeLAMP.com
original_source: "Google 官方支持文档 / android.com / Flathub / GitHub（Packet、rquickshare）"
original_author: "Google；Packet 与 rquickshare 项目"
original_date: 2026-10-09
original_url: "https://support.google.com/android/answer/9286773"
description: "Quick Share（原 Nearby Share）用蓝牙发现加 Wi-Fi 直连传文件，Android 与 Chromebook 内置，Windows 有官方 App，AirDrop 互通覆盖 Pixel 8a/9/10 与部分三星、小米、OPPO、vivo、荣耀机型。但它没有官方 Linux 客户端：ChromeOS 是唯一拿到官方 Liunx 形态的平台，桌面 Linux 只能靠 Packet、rquickshare 这类逆向实现。本文回答「Linux PC 和手机能不能互传」，给出四条现实路径的取舍，并纠正文中几个常见误解（iPhone 二维码其实走云端、二维码路径有大小与每日限额、Quick Share 与互传联盟是两套协议）。"
published: true
---

> 主要来源：[Google 官方：Use Quick Share on your Android device](https://support.google.com/android/answer/9286773)、[android.com/quick-share](https://www.android.com/quick-share/with-iphone/)、[Packet（Flathub / GitHub）](https://github.com/nozwock/packet)、[rquickshare](https://github.com/Martichou/rquickshare)
> 本文为**资料核实 + 解读**。文中把「Google 官方明确支持的」与「第三方逆向实现、随时可能坏的」严格分开表述。

## 一句话结论

Quick Share 是 Android 阵营目前最好的近场传输方案：**蓝牙负责发现，Wi-Fi 直连负责搬数据**，不需要云端中转、不需要第三方 App、能轻松搬几 GB。但它有一个明确的空白：**没有官方 Linux 桌面客户端**。官方只给了 Android、Chromebook 和 Windows（还有一套通过 AirDrop 与 iPhone 互通的新机制）。所以在 Linux PC 上要和手机互传，现实里只有四条路：**第三方逆向的 Quick Share 客户端**、**本地网络自建协议（LocalSend 等）**、**KDE Connect 这类助手型工具**，或者**回到数据线**。

## 一、Quick Share 是什么，以及它为什么快

先把机制讲清楚，因为「快」和「不依赖互联网」这两点经常被混为一谈。

**Quick Share 的前身是 Nearby Share**，2024 年前后 Google 把自家 Nearby Share 与三星的 Quick Share 合并，统一叫 Quick Share。它现在是 Play 服务的一部分，**Android 6+ 设备基本都内置**（三星设备走 One UI 自己的设置入口，功能等价）。

传输分两段：

| 阶段 | 用的技术 | 作用 |
|---|---|---|
| 发现与配网 | **蓝牙 / BLE** | 找到附近设备、做配对与鉴权 |
| 搬数据 | **Wi-Fi 直连**（Wi-Fi Direct 或 Wi-Fi Aware） | 真正的文件传输通道 |

这个「发现用蓝牙、传输用 Wi-Fi」的组合是关键：蓝牙省电、适合持续广播；Wi-Fi 直连带宽远高于蓝牙，所以**大文件也能快速搬完**。Android 从 8.0 起就提供了 Wi-Fi Aware（NAN）平台支持，Android 17 起把控制逻辑从固件上移到 wpa_supplicant 与框架层，为的是和 Wi-Fi Direct 等技术的底层实现统一。

**两个常被误读的点：**

- **「不依赖活跃互联网」不等于「完全不需要任何网络」**。走 Wi-Fi 直连时确实可以没有互联网，但如果是同 Wi-Fi 局域网传输、或者走二维码/链接路径，情况就不同了（下面细说）；
- **它不做压缩，也没有人为的文件大小上限**。这点和发邮件、发网盘的本质不同：邮件附件有硬限制，网盘要上传下载两趟。Quick Share 是点对点搬原始字节。

### AirDrop 互通：这是官方支持，但有前提

Google 与 Apple 的互通是近一两年最大的变化，也是最容易被写成「Android 和 iPhone 随便互传」的地方。准确说法是：

- **走 AirDrop 互通**：需要 **Android 侧支持 Quick Share Extension**。官方支持名单包括 **Pixel 8a、Pixel 9 全系、Pixel 10 全系**，以及**部分**三星（S24/S25/S26 系列、Z Flip/Fold 6/7 等）、小米、OPPO、vivo、一加、荣耀、传音、摩托罗拉机型。**Pixel 8 与 Pixel 8 Pro 长期不在名单里**，直到 2026 年下半年才开始分批推送。使用时**对方的 AirDrop 必须设为「对所有人开放 10 分钟」**，Android 侧三星机型还要额外打开「与 Apple 设备分享」；
- **走二维码/链接**：不支持上述互通的设备，可以生成二维码让 iPhone、iPad、macOS 用户在浏览器里下载。**这条路是走云端的**：文件端到端加密后上传到 Google 服务器，**保留 24 小时**，双方都需要联网。微软商店里那份 Quick Share 页面还写明二维码/链接路径的限制：**一次最多 1,000 个文件、单文件最大 10 GB、每天上限 10 GB**。

所以「部分 Android 手机可与 AirDrop 兼容设备互传」这句话是对的，但**必须补上「哪些机型」和「另一条路是走云端的」这两个限定**，否则读者会在自己手机上找不到入口。

### 可见性设置

接收方不在联系人里时，需要把可见性改成 **「所有人，10 分钟」**。三个档位是：

- **你的设备**：锁屏状态下也对你同一 Google 账号的其他设备可见；
- **联系人**：屏幕亮着且解锁时，对附近联系人可见；
- **所有人，10 分钟**：到期自动切回原设置。这是隐私设计，不是 bug。

## 二、关键问题：Linux PC 与手机能不能互传？

**能，但不是官方支持的方式。** 这是这篇文章最该讲清楚的事。

官方的 Quick Share 客户端覆盖：**Android、Chromebook、Windows**（Quick Share for Windows，要求 64 位 Windows 10 及以上，ARM 版 Windows 需要 11 及以上；三星 PC 要用三星版本，Google 版已不支持三星 PC）。

**这里有个非常值得吐槽的落差**：Chromebook 跑的就是 Linux，Quick Share 在 ChromeOS 上是被官方深度集成的（设置里直接有入口、文件应用里直接能用）。但**面向通用 Linux 桌面发行版，Google 至今没有提供任何官方客户端或包**。Google 官方支持论坛上从 2024 年起就有人反复问这件事，得到的答复是「ChromeOS 有构建，但桌面 Linux 没有官方包」。

于是桌面 Linux 的 Quick Share 只能靠**第三方对私有协议的逆向实现**。目前活跃的两个：

| 项目 | 形态 | 说明 |
|---|---|---|
| **Packet**（nozwock） | GTK4 + Rust，Flathub 有包 | 面向 GNOME 设计，**能发也能收**，还支持与装了 Packet 的其他 Linux 设备互传；有 Nautilus 右键菜单集成、自启动、托盘图标、D-Bus 接口 |
| **rquickshare**（Martichou） | Rust，提供 .deb / .rpm / AppImage / Nix / AUR | 同时支持 Linux 与 macOS，AUR 里有 `r-quick-share` |

**它们都有同一个硬性前提**：Packet 的 README 写得很直接：**因为只实现了 Wi-Fi LAN 这一种媒介，所以需要蓝牙开启，且设备要连在支持 mDNS 的 Wi-Fi 网络上**。也就是说，第三方实现**没有覆盖 Wi-Fi Direct / Wi-Fi Aware 直连那条路**，走的是局域网 + mDNS。

### 这带来的实际后果

这个技术选择的限制非常具体，值得单独列出来：

- **手机和 PC 必须在同一个 Wi-Fi 局域网里**。没有共享 Wi-Fi（比如手机开热点给笔记本、或在外面临时相遇）就可能走不通。这也意味着**「不依赖互联网」在某些场景下会退化**：你可以没有外网，但通常需要一个共同的二层网络；
- **Android 的 mDNS 广播是间歇性的**。rquickshare 的 README 直接承认了这点：**Android 不会一直广播它的 mDNS 服务，即使在「所有人」模式下**。rquickshare 的对策是**自己广播一个蓝牙广告**，让 Android 把 mDNS 暴露出来，而这**要求 PC 有蓝牙**；Packet 的限制说明里也提到，Android 会「随机地」出现和消失，原因就是它在周期性注销服务；
- **没有蓝牙就没有发现**。两个项目都要求蓝牙开启，这不是可选项；
- **防火墙可能挡路**。Packet 的 FAQ 里第一条就是「别的设备发不进来」：需要打开 **静态端口** 偏好并放行防火墙；
- **命令能收，但在手机上找入口可能得绕**。rquickshare 文档给了一个很实在的 workaround：可以在 Android 上用「文件」应用的「附近的分享」标签，或者用快捷方式工具直接跳转到 `com.google.android.gms.nearby.sharing.ReceiveSurfaceActivity`。它还提醒**三星对 Quick Share 做了改动，这个 workaround 可能失效**；
- **三星的兼容性整体偏脆**。rquickshare 的原文用词是「三星对 Quick Share 做了些见不得光的改动」（did something shady），所以上述方法可能不管用，且当时无替代方案。

**结论一句话**：Linux PC 与手机在同一个 Wi-Fi 下互传，**用 Packet 或 rquickshare 是可行的，日常够用，但它是「部分实现 + 逆向协议」，要接受偶发的发现失败和需要调端口/防火墙的现实**。别指望它像 Android 之间那样开箱即用。

## 三、另外三条路，以及各自适合什么

既然官方缺位，值得把备选方案一次讲清，因为**对多数人来说，non-Quick Share 的方案反而更省事**。

### 1. LocalSend（跨平台，包括 iOS）

LocalSend 是你常会在评论区看到有人推荐的替代品。它走的是**局域网 HTTP 自建协议**，需要所有设备在同一 Wi-Fi 下、装同一个 App。优点：**跨平台覆盖最全**（Android、iOS、Linux、macOS、Windows 都有），不依赖 Google 服务（这点对国行设备很关键），也没有私有协议逆向的兼容风险。缺点：**必须装 App**，不像 Quick Share 那样系统内置。

### 2. KDE Connect（助手型，不只是传文件）

KDE Connect 的价值在于它不止传文件：**通知同步、剪贴板共享、手机当触控板/遥控器、短信回复**。如果你的需求是「手机和电脑联动」，它比 Quick Share 更合适；如果**只是想把几张照片拖过去**，它就显得重，而且它的连接稳定性经常被吐槽（社区里「连接时好时坏」的抱怨是常态）。

### 3. 数据线 / adb

最被忽视但最可靠的方案。传几十 GB 的视频，**USB 3.0 线或 MTP 依然是最快的**，也是唯一不需要在两端做任何配置的路径。缺点在反向：**从手机往 PC 推文件时体验很差**（MTP 对大量小文件不友好），而且 Android 11 之后对 `Android/data`、`Android/obb` 的访问收紧，很多 App 的数据目录读不到。

### 四种路径对照

| 方案 | 需要同一 Wi-Fi | 需要蓝牙 | 装 App | 跨平台 | 适合 |
|---|---|---|---|---|---|
| **Packet / rquickshare** | 是（LAN 媒介） | 是 | 是（PC 侧） | Linux/macOS ↔ Android | 手机与 Linux 桌面常互传、不想装手机端 App |
| **LocalSend** | 是 | 否 | 是（两端） | 全平台含 iOS | 设备杂、含 iPhone、想要最稳 |
| **KDE Connect** | 是 | 否 | 是（两端） | Linux/Windows/macOS ↔ Android | 要通知/剪贴板联动，传文件是附带 |
| **数据线 / adb** | 否 | 否 | 否 | 全平台 | 一次性搬大量数据 |

## 四、国行设备：你可能用的不是 Quick Share

对中国读者还得再补一层，因为它直接影响「我手机上根本找不到 Quick Share」这个疑问。

**国行 Android 手机的近场互传，主流走的是「互传联盟」（Mutual Transmission Alliance，MTA）**：2019 年 8 月由小米、OPPO、vivo 发起，基于 **BLE 广播发现 + Wi-Fi P2P 直连传输**，官方公布的最高速度约 **20 MB/s**，无需第三方 App 或网络连接。2025 年 2 月**荣耀加入**，联盟协议对所有安卓厂商开放。

这带来两个直接后果：

- **国行设备上 Quick Share 常常不可用或不可见**，因为预装的互传功能占了这个位置。社区里的讨论基本印证了这点：有用户描述国行机型和海外机型双持时「互传文件很麻烦」，也有人直接说「快速分享好像给国行的互传联盟给占用了」；
- **互传联盟不做 PC 端，协议也不对外开放**。这一点在 2025 年底的讨论里被反复提到：手机之间很顺畅（除了华为、荣耀的例外情况），但**想让电脑接入这个协议「好像并不行」**，各家 PC 端软件互不相通。

**所以对国内用户的现实结论是**：手机↔手机走互传联盟（同品牌或联盟内跨品牌都行）；**手机↔Linux PC 这一环，联盟和 Quick Share 都帮不上忙，直接用 LocalSend 或数据线更省心**。

## 五、给 Linux 用户的实操建议

如果你就是想要「手机和 Linux 桌面互传」这件事跑通，按这个顺序试：

1. **先确认你要跨的是哪个阵营**。手机如果是国行主力品牌，Quick Share 那套大概率不参与，直接跳到第 3 步；
2. **手机是 GMS 完整设备（Pixel / 三星 / 港版等）**，且你愿意接受逆向实现：装 Packet（`flatpak install flathub io.github.nozwock.Packet`），**确保蓝牙开着、PC 和手机在同一 Wi-Fi**，并在 Preferences 里**打开静态端口**、在防火墙放行。发现不到手机时，用 rquickshare README 里的思路排查 mDNS 广播问题；
3. **追求稳定、设备杂（尤其含 iPhone）**：用 **LocalSend**，两端都装，不折腾；
4. **要的是联动而不只是传文件**：KDE Connect；
5. **一次性搬几十 GB**：数据线，别折腾无线。

**最后一句提醒**：这篇文章里提到的 Quick Share 官方支持范围、机型名单、Windows App 要求，都在快速变化。**涉及具体机型能不能用 AirDrop 互通时，请以 Google 官方支持页面当天的名单为准**，媒体文章的机型列表经常滞后于实际推送。

## 关键事实速查

| 项目 | 内容 |
|---|---|
| 名称沿革 | Nearby Share（Google）+ Quick Share（三星）合并，2024 年前后统一为 Quick Share |
| 传输机制 | 蓝牙/BLE 发现 + Wi-Fi 直连（Wi-Fi Direct 或 Wi-Fi Aware）搬数据 |
| 官方覆盖平台 | Android 6+、Chromebook、Windows（Quick Share for Windows） |
| ⚠️ Linux 空白 | **无官方 Linux 桌面客户端**；Chromebook 是唯一官方 Linux 形态；桌面靠第三方逆向 |
| 第三方方案 | Packet（GTK4/Rust，Flathub，可收可发）、rquickshare（Rust，deb/rpm/AppImage/Nix/AUR，含 macOS） |
| 第三方限制 | 只实现 Wi-Fi LAN：需同 Wi-Fi + 蓝牙 + mDNS；Android 的 mDNS 广播间歇性；防火墙需放行静态端口 |
| AirDrop 互通 | 需 Quick Share Extension：Pixel 8a/9/10 全系 + 部分三星/小米/OPPO/vivo/一加/荣耀等；对方须开「所有人 10 分钟」 |
| ⚠️ 二维码路径 | **走 Google 云端**，文件端到端加密、保留 24 小时、双方需联网；上限 1,000 文件 / 单文件 10 GB / 每日 10 GB |
| 可见性档位 | 你的设备 / 联系人 / 所有人（10 分钟，到期自动回退） |
| Windows 要求 | 64 位 Win10 及以上；ARM 需 Win11 及以上（部分页面标注 ARM 不支持，以官方为准）；三星 PC 需用三星版 |
| 国行现实 | 主流走互传联盟（MTA，2019 小米/OPPO/vivo 发起，2025 荣耀加入），BLE+Wi-Fi P2P，最高约 20 MB/s；不开放 PC 接入 |
| 替代方案 | LocalSend（全平台含 iOS）、KDE Connect（联动型）、数据线/adb（大批量） |

## 延伸阅读

- [Google 官方：Use Quick Share on your Android device](https://support.google.com/android/answer/9286773)
- [Google：Quick Share 与 iPhone 互传说明](https://www.android.com/quick-share/with-iphone/)
- [Packet：Linux 版 Quick Share 客户端](https://github.com/nozwock/packet)
- [rquickshare：Linux 与 macOS 的 Quick Share 实现](https://github.com/Martichou/rquickshare)
- [本站：在 Linux 上原生跑安卓应用：Waydroid 实操与边界](/articles/2026-09-28_android-native-on-linux-waydroid/)
- [本站：万物皆隧道（续）：给香橙派接上 Cloudflare 零信任 SSH](/articles/2026-10-06_orange-pi-cloudflare-zero-trust-ssh/)
