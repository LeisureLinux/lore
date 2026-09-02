# LibreOffice 26.8 正式发布：206 位贡献者合力，重点死磕排版质量、复杂文字与文档交换

## 一句话总结

The Document Foundation 在 2026 年 8 月 26 日发布 LibreOffice 26.8，**206 位贡献者**（其中 **155 位是志愿者**）从 2025 年 12 月开始打磨半年。版本聚焦三条主线：Writer 的**排版质量**（全新段落排版器）、跨语种的**复杂文字**（双向文本、CJK、N'Ko、Adlam）、**文档交换保真度**（OOXML 新图表 round-trip）。同时这一版明确宣布**不含任何生成式 AI 特性、不联网**，并首次在 Start Centre 加入**周期性捐赠横幅**。

---

## 事件速览

* **发布日期**：2026-08-26
* **开发周期**：2025-12 → 2026-08（约 9 个月）
* **贡献者**：206 人（155 志愿者 / 51 受薪）
* **覆盖平台**：Windows / macOS / Linux
* **语言数量**：120 种
* **下载**：https://www.libreoffice.org/download/
* **生产环境备选**：LibreOffice 26.2.5；26.2.6 计划 2026-09-03 发布
* **生命周期提示**：26.2 分支 2026-11-30 EOL
* **企业版**：生态厂商提供 3–5 年安全更新支持

---

## 这次发布的三个核心方向

TDF 官方公告把 26.8 定位在三条主线上：

> LibreOffice 26.8 concentrates on three areas: the typographic quality of what the suite produces, the range of writing systems it handles correctly, and the fidelity with which documents survive exchange with other office suites.

翻译过来就是：

1. **排版质量（Typography）**：让 Writer 输出更接近专业排版软件的标准。
2. **复杂文字（Writing systems）**：补齐双向文本、垂直 CJK、N'Ko、Adlam 等「没有商业市场」的语种。
3. **文档交换（Document exchange）**：让 OOXML 文档在 LibreOffice 里能"至少不丢东西"。

下面按这三条主线展开，再补上**电子表格、演示/绘图、用户界面、无障碍、数据库/自动化**等其他模块的要点。

---

## 一、排版质量：Writer 的 Paragraph Composer 终于来了

### 1. Paragraph Composer（段落排版器）

这是 26.8 在 Writer 里最值得关注的改动。

过去所有字处理器都用"**单行贪心算法**"（single-line greedy）来排版：每放一行只看本行能不能塞下，剩下的空间丢给下一行。这导致**两端对齐**（justified）的文本里，长单词落到行尾时，常常出现"这一行很挤、下一行很空"的**疏密交替**现象。

Paragraph Composer 改成**段落级优化**：把整段连起来一起算，让词间距（word spacing）尽量均衡。视觉效果上，两端对齐的段落不再"一行紧一行松"，英文长文里尤其明显。

这种排版器在专业排版软件（如 InDesign、TeX）里是默认行为，但在 LibreOffice / Word 里一直缺席。**Word 至今仍是单行贪心算法**——这是 LibreOffice 第一次在主流办公套件中提供比 Word 更高的排版质量。

### 2. OpenType 变量字体原生支持

26.8 开始，**Writer / Calc / Impress** 等组件可以直接调用 OpenType **变量字体**（variable fonts）的字重（wght）、字宽（wdth）、光学尺寸（opsz）等轴。

变量字体的优势：

* **一份字体文件**涵盖整个家族（极细 → 极粗），而不是 8 个独立的 .ttf。
* 排版时可以根据字号**自动调整字形**（光学尺寸轴），小字号保留细节，大字号强化对比。
* 单文件部署，权限管理更简单。

Linux 上字体生态一向是短板，能原生用上 Google Noto、Inter 等开源变量字体是个明显加分项。

### 3. 基线网格（baseline grid）修正

26.8 之前，**框架内的文本（frames）**不会和基线网格对齐；网格本身在编辑时也不可见。26.8 修了这两点：

* **基线网格在框架中正确对齐**。
* **编辑时可显示基线网格**，颜色可配置。

这两点对做小册子、报纸样式的版面设计很关键——以前只能靠手动 padding 凑。

### 4. Draft 视图（无干扰写作）

Writer 新增 Draft 视图，**隐藏页眉、页脚、页边距**等装饰性元素，类似 Word 的 Draft view / Notion 的 Focus mode。写作者进入心流时不会被版式干扰。

---

## 二、复杂文字：让没有商业市场的语言被认真对待

> None of this work has a commercial market. It was done anyway, because a foundation does not ask whether a language pays for itself before deciding to support it.

TDF 在公告里写的这句话很重。26.8 把**双向文本（BiDi）和复杂文字脚本**作为"最大的一块工作量"。

### 1. Writer 的双向文本语义重做

| 改动 | 含义 |
|------|------|
| **段落方向自动检测** | 打开或粘贴文档 / 纯文本时，Writer 自动判断段落应该是 LTR 还是 RTL |
| **行尾空白按段落方向处理** | 换行空格放在段落方向对应的那一端，而不是被相邻字符的方向带跑 |
| **调整手柄在 RTL / 垂直 CJK 下行为正常** | 嵌入式对象的 resize handle 不再错位 |
| **双向控制字符可见** | LRM、RLM 等零宽控制字符可以像其他格式标记一样显示出来，方便排错 |
| **新文档默认 start 对齐** | 而非死板的 left 对齐——start 在 LTR 下等价于 left，在 RTL 下等价于 right |
| **改段落方向不再镜像已对齐段落** | 避免一些隐性 bug |

过去 Writer 的双向处理一直是被吐槽的点（特别是对阿拉伯语、希伯来语用户）。**这一波不是"加个开关"，是底层语义重做**。

### 2. Calc 单元格方向自适应

在 Calc 里向**空单元格**输入 RTL 内容，单元格会自动切到 RTL 方向——少了一个过去必须手动调格式的小麻烦。

### 3. CJK / 表意文字的稿件格

26.8 把"中文 / 日文 / 韩文"相关的**稿纸网格（genkō yōshi manuscript grid）**选项明确重命名。功能本身对中文 / 日文排版意义不大，但是命名规范化的努力值得肯定。

### 4. Math 增加 N'Ko 和 Adlam 公式支持

Math 模块新增：

* **N'Ko 脚本**——西非曼丁哥诸语言（N'Ko 字母由 Solomana Kanté 1949 年发明）。
* **Adlam 脚本**——富拉尼语。
* **左向向量 / harpoon**——给 RTL 公式用。

这些语种在英文办公市场没有商业价值，但 TDF 把它做完了。这就是基金会（foundation）和公司的区别。

### 5. 跨语言字体名解析

如果文档作者在 A 语言的系统里、用 B 语言的字体名写了份文档，过去 LibreOffice 在 C 语言的系统里**找不到该字体**，会静默 fallback。26.8 修了这个解析链，**按语言索引查字体名**，文档能按预期显示作者选择的字型。

这一改对**多语言团队协作**（中文作者用日文系统写的文档，发给英文系统同事）特别友好。

---

## 三、文档交换：把 OOXML 的新图表保住，别丢

### 1. OOXML 新图表类型的保留式 round-trip

微软近年在 OOXML（Office Open XML）里加了好几种**新图表类型**：

* **box-and-whisker（箱线图）**
* **funnel（漏斗图）**
* **Pareto（帕累托图）**
* **sunburst（旭日图）**
* **treemap（树状图）**
* **waterfall（瀑布图）**

26.8 之前，LibreOffice 打开带这些图表的 OOXML 文件会**直接丢失**；现在 LibreOffice 会：

* **不能渲染**这种图表——显示一个对话框，告知是"不支持的图表类型"。
* **保留底层定义**——把 XML 完整存下来。
* **原样写回**——存盘后再次用 Microsoft Office 打开，所有内容、原参数还在。

公告里有一段很值得全文引用：

> A specification extended unilaterally by a single implementer is a moving target for every other implementer. Preserving what cannot yet be rendered is the discipline that keeps a document usable beyond the lifetime of the application that created it.

翻译：单家厂商单方面扩展规范，对其他实现者来说就是移动靶。**对不能渲染的图表保留原始定义**——才是让文档在创建它的应用生命周期之外仍然可用的纪律。

这是**真正懂"开放格式"是什么**的工程态度：**不强求对等实现，先保证不丢**。

### 2. 区域地图（Region map）

带地理数据的区域地图（choropleth）**保留图表类型**（chart type survives），但**大量地理数据无法保留**——因为 region map 把行政边界、坐标等数据嵌在 OOXML 扩展里，LibreOffice 解析不了。TDF 在此给的是**诚实**的告知，不是掩盖。

### 3. Calc 的 XLSX 修正

* **引用单元格中的换行**：过去 XLSX 里 `="line1"&CHAR(10)&"line2"` 这样的引用单元格里换行符经常被吞，26.8 修正。
* **表单控件**：XLSX 里的 form control 元素现在出现在 Navigator 面板。

---

## 四、Calc（电子表格）：补旧 + 加新

| 新增 / 修改 | 含义 |
|------------|------|
| **透视表计算字段（Calculated Fields）** | 透视表里可以新增基于已有字段的公式列，财务 / 数据分析师的常规诉求终于补上 |
| **数据有效性静默拒绝** | 恢复到 24.2 之前的行为——非法输入直接丢弃，不再弹窗骚扰 |
| **单元格样式支持相对字号** | 字号可以用百分比继承基础字号，长文档可维护性更好 |
| **Shuffle 命令** | 选区随机洗牌，适合做随机抽样、随机排序演示 |
| **边框工具栏记忆** | 最近用过的边框样式会被记住，下一次点击直接套用 |

---

## 五、Impress / Draw：演示和绘图

### Impress

* **多页面尺寸**：一份演示文档可以混用多种页面尺寸（少见但合理）。
* **演示分组（Presentation sections）**：把幻灯片分组、加名字，组织方式更灵活。
* **自定义幻灯片名**：幻灯片缩略图旁同时显示**幻灯片编号 + 自定义名字**，适合带章节的大型演示。
* **编号列表转项目符号列表**：列表样式切换。
* **模板 16:9 / 4:3 双比例**：背景图不再被强行拉伸。

### Draw

* **鼠标滚轮翻转**（zoom 还是 scroll 二选一）：默认改成 zoom，让画布操作更舒服。

---

## 六、用户界面（UI）

* **Notebookbar 配色区分应用**：Writer / Calc / Impress / Draw 用**不同背景色**区分，Tab 上也有分类标签。
* **Notebookbar Tab 支持鼠标滚轮 / 触控板滚动**。
* **应用主题色切换无需重启**——一直以来被吐槽的小问题修了。
* **样式列表统一**：Notebookbar / Formatting 工具栏 / 侧边栏三处的样式条目**完全一致**，且每个条目**预览样式本身**（不是只显示名字）。
* **样式对话框可单独重置为父样式属性**。
* **新增 A0–B3 纸张规格**：海报 / 大幅面打印场景。
* **自定义词典加搜索筛选**。
* **超链接对话框可剥掉 query string**——做 URL 分享的人会喜欢。
* **Windows 端可缩放对话框加了最大化按钮**。
* **macOS 端 Emoji & Symbols、Dictation、AutoFill** 菜单项可用。

---

## 七、无障碍（Accessibility）

* **Writer 表格按 ARIA 规范报告行列索引**——屏幕阅读器对表格结构的播报更准确。
* **特殊字符选择器**完全支持键盘导航——盲文 / 视障用户可以纯键盘操作。

---

## 八、数据库与自动化

### Base

* 切到 Design View 时**保留 SQL 注释**——以前会被吃掉。
* 嵌入式 Firebird 数据库**支持日期、时间、时间戳列的过滤**。

### Python / Basic / UNO

* **Python 脚本可直接在 Macro 管理器里创建 / 编辑**——不需要装扩展。
* **Python 可通过构造函数实例化 UNO 服务**——告别魔法字符串。
* **ScriptForge** 加了类型化输入对话框、`map / filter / reduce`、Basic 数组的函数式操作。
* **ScriptForge 默认命名管道**——同一份脚本既能在 LibreOffice 内部跑、也能作为客户端跑。

VBA 迁移、Python 自动化这些**长期被诟病的薄弱面**在一步一步补。

---

## 九、其他改动

* **快捷键可按文档绑定**：一个文档可以绑定一个仅在该文档中存在的快捷键——比如调用仅在该模板里有的样式。
* **大文档含图时打开速度提升**。
* **Quick Find 侧栏可搜评论**。
* **表格样式（Writer / Calc）可编辑**，内部表示从二进制格式换成 XML。
* **应用主题色改动无需重启**。
* **页面设置新增 A0–B3**。
* **样式列表跨 UI 一致**。
* **自动测试改用 VeraPDF** 校验 PDF 输出。

---

## 十、零 AI：一次立场表态

> LibreOffice 26.8 contains no generative AI features. Documents are not transmitted to remote services for processing, and no component of the suite requires network access to function. This is a deliberate position.

在 2026 年的办公套件市场上，"零 AI"是一种立场，不是能力缺失。TDF 给出两点理由：

1. **审计可证明**——只有"数据没离开机器"才是能写进合规报告的承诺。任何远程推理 API 都做不到。
2. **功能不被锁定**——本地推理本地跑，不需要订阅、不需要登录账号。

这和 Microsoft 365 / Google Workspace 把 Copilot / Gemini 深度嵌进产品是两条路。TDF 在这里把"我们没有 AI 功能"明确写成**承诺**而不是**缺陷**，值得尊重。

---

## 十一、首版捐赠横幅：怎么筹钱是门手艺

26.8 是**首个在 Start Centre 显示捐赠横幅**的版本。横幅规则：

* **周期显示**——每月一次，或更新成功后。不是每次启动都弹。
* **只出现一次**——仅 Start Centre，不在编辑界面出现，不打断工作。
* **链接到捐赠页**——`https://www.libreoffice.org/donate`

LibreOffice 的模式被 TDF 自己写得很清楚：

> LibreOffice carries no advertising, no telemetry, no subscription, no account requirement, and no feature withheld behind payment. ... The banner exists because software used by tens of millions of people is not free to maintain, and because every alternative route to sustainability would cost users something they currently have.

翻译：LibreOffice 没有广告、没有遥测、没有订阅、没有账号要求、没有付费解锁功能。**横幅存在的原因是——给几千万人用的软件不是零成本维护的**，而其他任何可持续性路线都会让用户付出他们目前**不必付出**的代价。

这是一段非常成熟的产品定位：**不卖数据、不卖订阅、不卖功能**，唯一的请求是**如果你觉得值，捐一点**。

---

## 十二、升级与兼容性

### 用户需要知道的几个 breaking change

* **Gentium Basic / Gentium Book Basic 字体不再捆绑**——文档里若引用这两个字体，会回退到其他字型；用户可单独从 TDF / SIL 下载安装。
* **新文档默认 start 对齐**而非 left——LTR 下基本无感，RTL 下行为更正确。
* **Safe Mode 重命名为 Troubleshoot Mode**——功能不变，菜单 / 帮助文档要跟着改。
* **过时的 Java applet 配置移除**——SDK 里 OfficeBean 示例被移除。

### 版本策略

| 分支 | 状态 | EOL |
|------|------|-----|
| **26.8** | 新发布 | 26.2 季度 26.8 系列按节奏点更 |
| **26.2** | 维护中（26.2.5 已出，26.2.6 计划 9-03） | **2026-11-30** |
| **24.8 / 25.x** | 已 EOL | — |

### 给生产环境的建议

TDF 公告直白地说：

> Users in production environments may prefer LibreOffice 26.8.0, available from the same page.

**生产环境可以选 26.8.0**，但更稳的选项仍是**26.2 季度**（26.2.5 / 即将 26.2.6）。如果业务真需要 3–5 年长周期支持，应当考虑生态厂商提供的企业版（有 SLA）。

---

## 写在最后

LibreOffice 26.8 不是那种"全新发布、铺天盖地宣传"的版本——它是一次**扎实的中期打磨**：把过去几年一直被诟病的"段落排版不专业""双向文本处理别扭""OOXML 图表丢东西"逐一修掉，加上"零 AI、不联网"的立场表态和"周期性捐赠横幅"的可持续性尝试。

它没有营销意义上的爆点，但有工程意义上的**靠谱**：

* **排版质量首次超过 Word**（段落排版器）；
* **复杂文字支持做全**（N'Ko / Adlam / RTL / CJK）；
* **文档交换守纪律**（不能渲染就保留原数据）；
* **UI / 无障碍 / 自动化**继续补短板。

对一个由 206 人（其中 155 人是无偿志愿者）做出来的、在 120 种语言里可用的办公套件，**26.8 是一份合格的中期答卷**。

---

## 参考文献

1. The Document Foundation. *LibreOffice 26.8 Release Announcement*. 2026-08-26. https://blog.documentfoundation.org/blog/2026/08/26/libreoffice-26-8/
2. The Document Foundation. *LibreOffice 26.8 Release Notes*. https://wiki.documentfoundation.org/ReleaseNotes/26.8
3. The Document Foundation. *LibreOffice Download*. https://www.libreoffice.org/download/
4. The Document Foundation. *Donate*. https://www.libreoffice.org/donate
5. OMG! Ubuntu. *LibreOffice 26.8 Released*. 2026-08-26. https://www.omgubuntu.co.uk/2026/08/libreoffice-268-released
6. Linuxiac. *LibreOffice 26.8 Released with New Paragraph Composer*. 2026-08-26. https://linuxiac.com/libreoffice-26-8-released-with-new-paragraph-composer-variable-font-support/
7. LinuxCompatible. *LibreOffice 26.8 Release: Zero AI, Advanced Typography, and N'Ko/Adlam Script Support*. 2026-08-26. https://www.linuxcompatible.org/story/libreoffice-268-release-zero-ai-advanced-typography-and-nko-adlam-script-support/

*注：本文事实部分全部来自 TDF 官方公告与社区发行说明；解读与生态评论为作者观点。*