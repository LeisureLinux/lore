# Niri + DMS：真正能媲美 macOS 设计美学的新一代 Linux 桌面

## 什么是 DMS？

DMS（DankMaterialShell）是由 **AvengeMedia 社区** 开发的现代 Wayland 桌面 Shell 项目。它基于 Quickshell（QML 框架）和 Go 语言构建，提供了一个**轻量且高度可定制**的桌面体验。DMS 1.6 版本已经发布，支持 Niri、Hyprland、Sway、MangoWC 等多种 Wayland compositors。

## DMS 与 Niri、SDDM、QuickShell 的关系

DMS、Niri、SDDM、QuickShell 构成了一个**分层的 Wayland 桌面堆栈**：

| 组件 | 作用 | 备注 |
|---|---|---|
| **SDDM** | 登录管理器 | 负责用户登录、会话初始化、密码提示等 |
| **Niri** | Wayland Compositor | 负责窗口渲染、输入处理、工作区管理 |
| **QuickShell** | QML 界面框架 | 由 Niri 提供，构成 DMS 的 QML 运行时 |
| **DMS** | 桌面 Shell | 在 Niri + QuickShell 之上，提供完整的桌面 UI |

这种组合允许三者独立发展：
- **Niri** 专注于“滚动工作区”窗口管理
- **DMS** 提供完整的 Shell 功能（顶栏、dock、app 启动器、系统监控等）
- **SDDM** 负责安全的会话启动

## 启动顺序

从进程树看，这是一个典型的 Wayland 桌面层级：

```
SDDM (login manager)
 └── systemd --user (user session)
     └── niri (compositor)
         ├── dms ipc (DMS backend service)
         │   ├── danksearch (文件索引搜索)
         │   └── dgop (CPU/GPU 监控)
         ├── quickshell (QML UI 引擎)
         └── dms run (shell 主进程)
```

启动时：
1. **SDDM** 完成用户登录 → 启动用户 systemd 实例
2. systemd 用户实例启动 **Niri**（作为 compositor）
3. Niri 启动 **DMS**（`dms run`）和 **QuickShell** 作为子进程
4. **dms ipc** 作为后台服务，提供系统集成（音频、网络、蓝牙等）

## 下载 .deb 安装包

DMS 及其核心组件可以通过以下方式获取：

| 包名 | 版本 | 作用 |
|---|---|---|
| **dms** | 1.6.0db1 | 主程序（Shell + IPC daemon） |
| **danksearch** | 1.6.0 | 零依赖的文件索引搜索服务 |
| **dgop** | 1.6.0 | 状态化 CPU/GPU 系统监控 |
| **matugen** | 4.0.0 | Material You 动态配色引擎 |
| **quickshell** | 0.3.0-1~bpo13+1 | QML 界面运行时框架 |

**安装方式**（Debian 13/Trixie 为例）：
```bash
# 需要先添加仓库（或从 GitHub Releases 下载 .deb 手动安装）
sudo apt install dms danksearch dgop matugen quickshell

# 安装后生成配置
dms setup  # 自动为 niri 生成初始配置
systemctl --user enable --now dms  # 启用自动启动
```

## Niri 的岛式布局特性

Niri 采用**滚动式工作区**（scrolling workspace）设计，这与传统的“垂直工作区”或“网格布局”有本质不同：

### 岛式布局优势
- **空间紧凑**：每个工作区是“岛”，窗口在岛内水平滚动
- **视觉连续**：岛之间边框分隔，保持层次感
- **自动隐藏**：岛不在焦点时可自动收起，桌面更整洁
- **岛际切换**：`Super + Tab`/`Shift + Tab` 实现垂直切换

### 与 Hyprland 的核心差异

| 维度 | Niri | Hyprland |
|---|---|---|
| **布局模型** | 滚动岛式（每个 ws 一层） | 多平面网格（每个 ws 多层） |
| **窗口定位** | 水平滚动，窗口紧贴边缘 | 可自定义 gap、布局算法 |
| **缩放方式** | 每个窗口独立缩放 | 全局缩放 + 窗口缩放 |
| **意外行为** | 窗口拖动时自动调整布局 | 需要配置 animate 动效 |
| **配置语言** | KDL（类似 DSL） | 纯配置文件 + Lua |

Niri 的设计目标是“**让内容可滚动**”，因此拖动窗口时会自动重新排列；Hyprland 则强调“**高度可配置**”，允许自定义各种动效。

## Niri 发音指南

Niri 的正确发音是 **/ˈnɪəri/**，类似英文 "**near-ree**"（**near** + **ree**）：

- **N-i-r-i**：N 发音（类似 "鸟" 的开头），i 读作短音 i（如 "sit" 的 i），r 轻轻卷舌，第二个 i 读作短音 i
- **不要读成**："尼-里""内-里"这类汉语拼音读法，也不要读作 "Nigh-ree"（像 "near" 的发音）

这种发音更接近其创作者 YaLTeR 的原始设定，有助于正确表达项目名称。

## 为什么选择 Niri + DMS？

### 设计美学
- **Material You 主题**：DMS 基于 Material Design 3，搭配 matugen 实现动态配色
- **岛式布局**：与 macOS 的平铺窗口风格相近，但更轻量
- **统一视觉语言**：顶栏、dock、app 启动器、通知中心形成完整视觉系统

### 功能完整
DMS 取代了传统 Wayland 环境中需要配置的 **10+ 个工具**：
```
waybar + swaylock + swayidle + mako + fuzzel/rofi + nm-applet + blueman + swww + etc.
```
改为 **一个服务（dms）** 完全集成。

### 跨发行版兼容
无论是 Arch、Ubuntu、Fedora，还是 Debian 13，Niri + DMS 都能良好运行。它们不是某个发行版的“绑定组件”，而是**独立开源项目**，因此具备极好的可移植性。

---

*本文基于实际配置经验编写，引用自 AvengeMedia 官方文档：https://danklinux.com/docs*

*欢迎在评论区分享你的 Niri + DMS 部署经验！*