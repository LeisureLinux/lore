---
title: "pdfcpu：一个 Go 二进制收拢 PDF 结构操作，但替不掉 pdftotext"
date: 2026-11-12
slug: pdfcpu-go-pdf-tooling-hands-on
category: 技术/解读
author: FreeLAMP.com
original_source: "一手核对：GitHub 仓库 pdfcpu/pdfcpu 的 README 全文（Features、Commands 完整表、Motivation、Focus、Contributing、Disclaimer）＋ GitHub API 元数据（2026-11-12 查询：8906 stars / 650 forks / 116 open issues / Go / Apache-2.0 / master / 未归档）＋ Releases API（v0.16.4，2026-10-27）＋ pdfcpu.io 官方文档站 extract 命令定义与 split/trim 用法 ＋ 本机实测：Go 1.27.3 编译 v0.16.4、40MB/242 页 PDF 上的 validate/info/trim/split/merge/extract 全链路，与 pdftotext / pdfinfo / pdfimages / pdfcpu info 逐项对照 ＋ 本机已安装工具清单（poppler 系列、gs、mutool、tesseract、fitz、pypdf、weasyprint）"
original_date: 2026-11-12
original_url: "https://github.com/pdfcpu/pdfcpu"
description: "本文以本机实测介绍 pdfcpu：Go 写的 PDF 处理库 + CLI，2017 年建库、Apache-2.0、8.9k stars、v0.16.4（2026-10-27），维护者 Horst Rutter 是 PDF Association 成员，支持到 PDF 2.0（验证支持自称 basic）。单二进制 24MB、仅 8 个 Go 依赖、零系统依赖，命令表 50 余个覆盖 validate/optimize/split/trim/merge/rotate/resize/crop/nup/booklet、images/fonts/extract/attachments/portfolio/bookmarks/annotations、encrypt/decrypt/permissions、signatures（验证与移除）、form/create、stamp/watermark。实测样本为 40MB/242 页 Skia-PDF：validate 0.29 秒通过；info 给出版本、页数、Tagged、Linearized、object streams、Permissions 等，比 pdfinfo 更全；trim -p 1-2 → split → merge → validate 全链路通过；但 extract -m content 导出的是 PDF 绘图操作符（cm / re / BDC）而非可读文本，pdftotext 才输出段落。文章据此给出结论：pdfcpu 能统一替掉 pdfseparate / pdfunite / pdfimages 与手写 gs 脚本，并把 validate 加进抓取 PDF 的前置检查；但不能替 pdftotext（文本抽取）、pdftoppm/fitz（渲染）、gs（PostScript）、tesseract/ocrmypdf（OCR）、weasyprint（生成），Python 管线里继续用 fitz。也记录实测踩坑：split 没有 -p 参数、取页要用 trim -p；前三页无内嵌位图时 pdfcpu 与 pdfimages 都返回 0 个文件；PDF 2.0 验证仍在完善、116 个 open issues、版本 0.16.x。"
published: true
---

> 一手：pdfcpu 仓库 README / 完整命令表 / 官方文档站
> 实测：本机 Go 1.27.3 编译 v0.16.4，用 40MB / 242 页 PDF 跑通全链路并与 poppler 对照
>
> 起因是一个很自然的问题：既然有 pdfcpu，是不是能把机器上那堆 PDF 工具全删了？

先给答案：不能全替，但能替掉一半。pdfcpu 是「PDF 结构手术刀」，不是渲染器、不是文本抽取器、也不是 OCR 或生成器。下面用实测说话。

## 一、它是什么

`pdfcpu/pdfcpu`：Go 写的 PDF 处理库 + CLI，2017-06 建库，Apache-2.0，我查的时候 8,906 stars / 650 forks / 116 open issues，主分支 master，未归档，最新版 v0.16.4（2026-10-27）。维护者 Horst Rutter 是 PDF Association 成员，README 写明支持到 PDF 2.0 / ISO 32000-2，但也直说「PDF 2.0 validation support is basic and continuously improving」。

定位三句话：comprehensive PDF processing functionality、minimal external dependencies、predictable and stable behavior。

本机实测证实了这个定位：

```
GOBIN=... go install github.com/pdfcpu/pdfcpu/cmd/pdfcpu@latest
→ 只下载 8 个 Go 模块，产出单个 24,898,727 字节二进制
```

`go version` 是 1.27.3，`pdfcpu version` 报 v0.16.4。没有链接 poppler、没有 Ghostscript、没有系统库，这对容器和 CI 很友好。

## 二、命令表覆盖了什么

README 的完整命令表有 50 余项，按用途归一下：

| 类别 | 命令 |
|---|---|
| 结构与页面 | `validate` `optimize` `split` `trim` `merge` `pages` `collect` `rotate` `resize` `crop` `zoom` `cut` `ndown` `nup` `grid` `poster` `booklet` |
| 资源 | `images` `fonts` `extract` `attachments` `portfolio` `bookmarks` `annotations` `keywords` `properties` `info` `import` `boxes` |
| 安全 | `encrypt` `decrypt` `permissions`、改 user/owner 口令、`signatures`（验证完整性、证据报告、移除签名）、`certificates` |
| 表单与生成 | `form`（含 multifill）、`create`、`config` |
| 装帧 | `stamp` `watermark` `pagelayout` `pagemode` `viewerpref` |

注意签名那一项：README 写的是 validate / report / remove，没有宣称创建数字签名。这类「看起来有、实际边界不同」的地方，迁移时最容易踩。

## 三、实测：40MB / 242 页 PDF

样本是本机 该 40MB 样本 PDF（40,546,169 字节，Skia/PDF m149 生成）。

① validate：0.29 秒

```
$ pdfcpu validate ChatGPT橙皮书.pdf
validating(mode=relaxed) ... validation ok    耗时 0.29 s
```

这一层是现有工具链里缺的：以前遇到 PDF 解析失败只能靠试错，现在可以先跑一遍判定结构是否干净。

② info 比 pdfinfo 更全

两者都正确报出 242 页、A4 594.96×841.92、Title「ChatGPT 橙皮书」、Producer Skia/PDF m149、Tagged=yes、Encrypted=no。pdfcpu 额外给了：`Linearized: No`、`Using XRef streams / object streams: No`、`Watermarked / Thumbnails / Signatures / Outlines / Names / Form` 全列、`Permissions: Full access`、`Viewer Prefs: DisplayDocTitle = true`。

③ 拆→合→校验全链路

```
pdfcpu trim -p 1-2 in.pdf first2.pdf        # 828 KB
pdfcpu split first2.pdf spl 1                 # 两个单页 PDF
pdfcpu merge merged.pdf spl/*.pdf             # 1.2 MB
pdfcpu validate merged.pdf                    # validation ok
pdfinfo merged.pdf → Pages: 2
```

这里我踩了个坑：`split` 没有 `-p` 参数（我按 poppler/qpdf 习惯猜错了），取页要用 `trim -p`，`split` 的位置参数是 `inFile outDir [span]`。命令语法不通用，脚本迁移得逐条改，不能无脑替换命令名。

④ 关键对照：extract 不是文本提取

官方文档站写明 `extract -m` 只有 `image | font | content | page | meta` 五种。实测第一页：

```
pdfcpu extract -m content -p 1 in.pdf out/
→ ChatGPT橙皮书_Content_page_1.txt，11,403 字节
→ 开头是：.23999999 0 0 -.23999999 0 841.91998 cm / q / 2480 3507.8125 re / W* n ...
```

这是 PDF 内容流的绘图操作符，不是给人读的文字。同一页用 `pdftotext -f 1 -l 1 -layout`：

```
CHATGPT · ORANGE BOOK    NON-OFFICIAL GUIDE / 非官方指南
ChatGPT 写给开发者与 AI 工具重度用户的使用手册
```

差别在「把字形映射回 Unicode、按阅读顺序排成段落」这一步，pdfcpu 不做。这对本工作区尤其要紧 —— 我抓论文、招股书 PDF 全靠 `pdftotext -layout`，换成 pdfcpu 只会得到一堆 `Tj` 操作符。

⑤ 图片抽取：`extract -m image -p 1-3` 得 0 个文件；`pdfimages -list` 对照同样 0 —— 这份 PDF 前三页是矢量文字，两边一致，不算分歧。但 `split -m span` 会把整本拆成单页 PDF，而 `pdfimages` 只管位图，两者能力域并不重叠。

## 四、能不能「一个替换全部」

| 需求 | 现有工具 | pdfcpu |
|---|---|---|
| 纯文本 / 带版式抽取 | `pdftotext`、`fitz` | ❌ 不能 |
| 渲染成图 / 页面转 PNG | `pdftoppm`、`mutool draw`、`gs`、`fitz` | ❌ 无渲染引擎 |
| OCR（扫描件→可搜索 PDF） | `tesseract`、`ocrmypdf` | ❌ |
| PostScript / EPS | `gs` | ❌ |
| HTML / 文档 → PDF | `weasyprint`、LibreOffice | 有限：仅 `create`（图片、表单数据） |
| 拆页 / 合并 / 旋转 / 裁剪 | `pdfseparate`、`pdfunite`、`mutool` | ✅ 强项 |
| 校验 / 结构修复 | `mutool clean`、`gs` | ✅ 强项，且多一层 validate |
| 元数据 / 页数 | `pdfinfo` | ✅ 可替，字段更全 |
| 内嵌图片 / 字体 | `pdfimages` | ✅ 可替 |
| 加密解密 / 权限 | qpdf、pdftk（本机未装） | ✅ 可替 |
| 水印 / 图章 / N-up / 小册子 | 手写脚本或 gs | ✅ 明显省事 |
| Python 程序化管线 | `fitz`、`pypdf`（已装） | 有限：Go 库，Python 里用不了 |

还有几条现实边界：PDF 2.0 验证自称 basic；README 的问题报告指南以 Adobe Acrobat Reader 与 macOS Preview 作兼容性参照，并明说「两个都打不开的文件，pdfcpu 多半也处理不了」；116 个 open issues、版本停在 0.16.x，成熟但仍在演进。

## 五、我的落地建议

对这台机器的实际用法，我建议这样收拢：

- 统一到 pdfcpu：拆页合并、旋转裁剪、图片/字体抽取、元数据查看、加密权限、水印图章 N-up；`pdfseparate` / `pdfunite` / `pdfimages` 和那些手写 gs 脚本可以退役。
- 新增一步：抓外部 PDF 后先 `pdfcpu validate -vv`，作为「文件是否可信」的前置检查，失败就换来源或换工具，别让 `pdftotext` 直接吞一个坏结构。
- 明确保留：`pdftotext`、`pdftoppm` 或 `fitz`、`gs`、`tesseract`/`ocrmypdf`、`weasyprint`。
- Python 脚本里继续用 `fitz`，不要为了「统一」把 Go 二进制硬塞进 Python 管线。

## 六、结论

pdfcpu 是个好项目，好到值得装：单二进制、零系统依赖、0.29 秒校验 40MB、50 多个结构命令、validate 是别人没有的那一层。但把它叫「PDF 万能工具」会踩坑，因为 PDF 生态里至少还有四个互不重叠的角色 —— 读文本的、渲染的、扫 OCR 的、生成的，它一个都不做。

准确说法是：它能把「PDF 文件结构操作」这一半收拢成一个工具，另一半照旧。

## 七、事实边界

- 本文数据与结论来自 2026-11-12 的仓库状态与本机实测：Go 1.27.3、pdfcpu v0.16.4、样本为单个 40MB / 242 页 Skia 生成 PDF，未覆盖扫描件、加密件、AcroForm、PDF 2.0 或数字签名样本。
- 「signatures 只验证/报告/移除」依据 README 的 Features 措辞，未实测签署流程；「extract 无文本模式」依据官方文档站命令定义与 `extract -m content` 产物。
- `pdfcpu` 与 `pdfimages` 前三页均返回 0 个图片文件，仅说明该样本该页范围无内嵌位图，不代表图片抽取能力缺失。
- 各工具的「能/不能」为能力域判断，非性能基准；未在 Windows / macOS 上测试。

## Sources

- GitHub 仓库：<https://github.com/pdfcpu/pdfcpu> ｜ README：<https://raw.githubusercontent.com/pdfcpu/pdfcpu/master/README.md>
- 项目文档：<https://pdfcpu.io/> ｜ extract 命令：<https://pdfcpu.io/extract/extract/> ｜ Go API：<https://pkg.go.dev/github.com/pdfcpu/pdfcpu>
- 本机对照工具：poppler `pdftotext` / `pdfinfo` / `pdfimages` / `pdfseparate` / `pdfunite`、Ghostscript、MuPDF、PyMuPDF、weasyprint、tesseract
