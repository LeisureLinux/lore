---
title: "Nebula：把整座照片库放进 3D 星云，用一句话找出里面的内容"
date: 2026-11-17
slug: nebula-local-ai-photo-search-3d-siglip
category: 技术/解读
author: FreeLAMP.com
original_source: "原文：MakeUseOf《This free Windows app lets you search what's actually in the photos on your hard drive》，讲一款免费开源 Windows 11 应用 Nebula：用自然语言描述照片内容（如 horse in the snow）即可在本地找出匹配照片，即便文件名里没有这些词；作者是微软 design director Lucas Couto，个人项目，UI 精致；用 Google SigLIP 2 模型分析照片，不上传；给文件夹建索引后在后台分析，存每张图的数值表示并用描述比对排名，用 GPU 跑 AI、可回退 CPU；可把照片库变成可环绕缩放的 3D 彩色点云，搜索时最佳匹配浮前、相似图聚拢；模型包约 6GB，没有模型包仍可浏览与搜元数据；当时无直接 Windows 安装包，需按 GitHub 步骤操作。＋ 在线一手核对：Nebula 官方 GitHub（github.com/lcoutodemos/Nebula），Apache-2.0，2026-11-13 建仓、6 次提交。README 原文：整个照片收藏放进一个可环绕/缩放/飞行的 3D 云；测到 10 万张照片，远处是彩色点、近处变清晰、选中加载全分辨率；支持 Cloud / Similarity / Time / Colour / Grid 五种排列；自然语言搜索（a horse in the snow），无 AI 模型时搜标题/作者等元数据；Similarity 自动分组命名，官方截图示例为 5 万张公共领域图里「a horse」命中 1134 张、分成 1403 组 66 个命名类别、日式版画类 1034 张；技术栈 WinUI 3 + Windows App SDK（MSIX）+ C++ Direct3D 11 渲染器（SwapChainPanel）+ Google SigLIP 2（siglip2-so400m-patch16-384）经 Windows ML / ONNX Runtime with DirectML 在 GPU 跑 + C#/.NET 10 做 PCA/PaCMAP/HDBSCAN 布局聚类 + Windows Raw Input 触控板环绕；要求 Windows 11 x64 或 Arm64、DirectX 12 GPU、约 6GB 空间放可选模型包；源码构建需 .NET 10 SDK / VS2026 / WinApp CLI 0.7+/开发者模式/Python 3.12；启动命令 git clone + .\\build.ps1 -Run，模型包用 tools/prepare_models.py 从 Hugging Face 下载转 ONNX 写到 %LOCALAPPDATA%\\Nebula\\Models；README 强调隐私：读原图不修改、缩略图/embedding/布局本地存储、不上传；截图用大都会博物馆 Open Access CC0 图。＋ 背景对比：Windows 11 照片应用仅在 Copilot+ PC 上支持本地已索引照片的自然语言语义搜索，其他 PC 按文件名/日期/类型搜索（微软支持页）；digiKam 用 YOLOv11/EfficientNet 做本地对象与场景识别（1000+ 对象）。"
original_date: 2026-11-17
original_url: "https://www.makeuseof.com/this-windows-app-lets-you-search-whats-actually-in-the-photos-on-your-hard-drive/"
description: "解读 MakeUseOf 报道的 Windows 免费开源应用 Nebula：本地 AI 照片搜索 + 3D 星云式浏览。核心能力：给一个文件夹，用自然语言描述画面内容（horse in the snow）找出照片，而不依赖文件名或事先打标签；官方 README 示例 5 万张公共领域图里搜 a horse 命中 1134 张、Similarity 自动分成 1403 组 66 个命名类别。技术栈拆解：WinUI 3 + Windows App SDK（MSIX）做界面，C++ Direct3D 11 渲染器画 3D 照片云（SwapChainPanel、毛玻璃、五级排列 Cloud/Similarity/Time/Colour/Grid），Google SigLIP 2 图像模型经 Windows ML（ONNX Runtime + DirectML）在 GPU 上算 embedding、可回退 CPU，C#/.NET 10 做 PCA/PaCMAP/HDBSCAN 布局与聚类，Raw Input 处理触控板环绕。要求 Windows 11 x64/Arm64 + DirectX 12 GPU + 约 6GB 模型包；无安装包需 git clone 后 build.ps1 -Run 源码构建，模型包用 prepare_models.py 从 Hugging Face 下载转 ONNX。隐私：原图只读不改、缩略图/embedding/布局本地、不上传；Apache-2.0。与 Windows 照片应用（Copilot+ PC 才支持本地语义搜索）和 digiKam（YOLOv11/EfficientNet 本地识别）做简单对比。实践提醒：6GB 模型包与 DirectX 12 GPU 是门槛、早期版本无安装包、AI 分组命名会有错需人工纠偏、隐私优势靠本地跑模型但模型下载仍走网络一次。边界：MakeUseOf 原文此次可访问但属二手报道，本文以官方 GitHub README 为准；未安装运行 Nebula、未复现其性能数字；数字来自官方示例截图非独立测试。"
published: true
---

 MakeUseOf 最近介绍了一款叫 Nebula 的 Windows 应用：你不必记得文件名，只要描述画面内容——比如「雪地里的马」——它就能在本地照片库里找出对应照片。这类工具并不稀奇，但 Nebula 的特别之处在于：它还把整座照片库做成了一片可以 fly through 的 3D 星云。

## 一、它解决的是「照片找不到」的老问题

从手机倒出来的照片，文件名往往是 `IMG_4821` 这种没有语义的东西。凭文件名、日期、文件夹翻找，是很多人整理相册时最耗时的部分。

Nebula 的做法是按画面内容搜索：给一个文件夹，它在后台分析每张图，存下数值表示（embedding），你的描述会和这些表示比对并排序。搜「a horse in the snow」，命中的是画面里真有雪地马的图，而不是文件名里带 horse 的图。官方 README 给的示例是 5 万张公共领域图里搜「a horse」命中 1134 张。

另一个模式是 Similarity：照片按「看起来像什么」自动排列，相近的聚成组，Nebula 还会给组起名。官方示例里，5 万张图被分成 1403 组、66 个命名类别，其中日式版画一类有 1034 张。

## 二、技术栈：全是 Windows 原生

Nebula 是微软 design director Lucas Couto 的个人项目，Apache-2.0 许可，代码在 GitHub。它不是一个套壳 Electron 应用，技术选型相当「Windows 原生」：

- 界面：WinUI 3 + Windows App SDK，打包为 MSIX；
- 3D 渲染：C++ Direct3D 11，画在 WinUI 的 `SwapChainPanel` 上，带毛玻璃面板和明暗主题；
- 语义核心：Google SigLIP 2 图像模型（`siglip2-so400m-patch16-384`），通过 Windows ML / ONNX Runtime with DirectML 在 GPU 上跑；
- 布局与聚类：C# / .NET 10，做 PCA、PaCMAP、HDBSCAN；
- 交互：Windows Raw Input 处理双指触控板环绕、缩放、平移。

照片云支持五种排列——Cloud、Similarity、Time、Colour、Grid。README 说渲染器测到 10 万张：远处是彩色点阵，靠近逐渐清晰，选中的图加载全分辨率；超过 10 万张的文件夹只打开前 10 万，导入详情会列出被省略的数量。

## 三、隐私与成本：本地跑模型的得与失

Nebula 的宣传重点是「不上传」：读取原图但不修改，缩略图、embedding 和布局都存在本地，模型与搜索都在你的电脑上。这点和云端相册搜索形成鲜明对比——后者要把照片传到服务商那里做识别。

代价也很明确：

- 需要 Windows 11 x64 或 Arm64，以及 DirectX 12 可用的 GPU（AI 走 DirectML）；没有 GPU 可回退 CPU，但慢很多；
- AI 模型包约 6GB 磁盘空间，从 Hugging Face 下载后转成 ONNX 存到本地应用数据目录；
- 没有直接的安装包（至少原文写作时），要 `git clone` 后跑 `build.ps1 -Run` 从源码构建，需要 .NET 10 SDK、Visual Studio 2026 等工作负载；
- 没有模型包时，仍能浏览照片和搜索标题、作者等元数据，只是失去自然语言搜索与自动分组。

换句话说，它用「一次性的构建麻烦 + 6GB 空间 + 一张像样的显卡」，换来了照片内容不出本机。

## 四、和现成方案比一比

- Windows 11 照片应用：根据微软支持页，只有在 Copilot+ PC 上，本地照片才支持自然语言语义搜索（且需已索引）；其他 PC 的本地搜索主要按文件名、日期、文件类型。Nebula 不挑 Copilot+，普通 Win11 机器有 DirectX 12 GPU 就能跑。
- digiKam：老牌跨平台照片管理，用 YOLOv11 / EfficientNet 做本地对象与场景识别，官方称可识别 1000+ 对象与场景，也有人脸、质量评估等功能。它更像「完整的照片数据库 + 编辑器」，Nebula 更像「把整库摊开成可探索的 3D 空间」。
- 云端相册：省事，但要把照片交给服务商。Nebula 的取舍是把算力成本留在本地。

## 五、结论与边界

Nebula 值得关注的地方，是它把两个原本分开的东西合在了一起：本地语义搜索（告诉你「有什么」）和空间化浏览（让你「看见整体」）。对一个几百 GB、懒得整理的照片库来说，这种「先搜索、再飞过去看」的交互，确实比逐个文件夹翻要直观。

但也要看清边界：

- MakeUseOf 这篇是二手报道，此次虽然能抓到原文，本文以 Nebula 官方 GitHub README 为准；
- 文中的 1134 张、1403 组、10 万张等数字来自 README 的官方示例与测试声明，未经独立复现；
- 本次未安装、未运行 Nebula，未验证其搜索准确度、构建流程或性能；
- 自动分组和命名由 AI 完成，会有错，官方也承认需要人工纠偏；
- 隐私优势建立在「模型本地跑」之上，但模型包第一次仍要从 Hugging Face 下载；
- 项目刚建仓（2026-11-13）、提交数很少，属于早期项目，别把它当成熟产品。

## Sources

- MakeUseOf 原文：<https://www.makeuseof.com/this-windows-app-lets-you-search-whats-actually-in-the-photos-on-your-hard-drive/>
- Nebula 官方仓库与 README：<https://github.com/lcoutodemos/Nebula> ｜ SigLIP 2 模型：<https://huggingface.co/google/siglip2-so400m-patch16-384>
- 微软照片应用搜索说明：<https://support.microsoft.com/en-us/windows/apps/photos/search-photos>
