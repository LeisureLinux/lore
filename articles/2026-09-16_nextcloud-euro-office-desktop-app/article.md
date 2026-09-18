# Nextcloud 推出 Euro-Office 桌面端：补齐对标微软 Office 的最后一环，也暴露开源办公的鸡生蛋难题

> 原文：[Nextcloud adds desktop app for Euro-Office productivity suite](https://www.computerworld.com/article/4221689/nextcloud-adds-desktop-app-for-euro-office-productivity-suite.html)（Computerworld，2026-09-16，作者 Matthew Finnegan）。本文由 LeisureLinux 翻译整理并加注解读；文内事实与发布时间均来自原文，未作改动。

Nextcloud 给 Euro-Office 套件做了个桌面客户端，覆盖 Windows、macOS、Linux——这是它想补齐「对标 Microsoft Office」版图中缺失的一块。Euro-Office 被 Nextcloud 定位成「主权可控、不把数据交给非欧洲厂商」的 Office 替代品。

严格说，Euro-Office 不是一个独立办公套件，而是一个**被嵌进其它生产力应用（比如 Nextcloud Hub）里的集成组件**：文档编辑由 Euro-Office 负责，存储、权限这些交给宿主平台。Nextcloud 是 Euro-Office 计划的发起方之一，今年 6 月把这套东西并进了 Nextcloud Office；在那之前，它只能走网页或手机 App。

新的桌面客户端让用户能在本地编辑文档、表格、演示文稿，再联网同步做协同编辑，未来几周陆续上架三个平台。Nextcloud 在新闻稿里的说法是：对想要传统桌面体验的用户，「这补齐了 Euro-Office 和 Microsoft Office 之间最后几个缺口之一，又不用把数据控制权交给非欧洲厂商」。

---

## 译文：这次 Nextcloud 到底放了什么

Euro-Office 这套开源项目的代码**基于 OnlyOffice 的代码库**，背后站着 Nextcloud，以及 Eurostack、Ionos、Office.eu、Proton、XWiki 等一众厂商。Nextcloud 称已有 40 多位个人贡献了代码，其中约 15% 来自直接参与的机构之外。

兼容性上，Euro-Office 既支持微软的 OOXML 格式，也支持开放文档格式 ODF（ODT / ODS / ODP）。不过这里有个老矛盾：负责开发 LibreOffice 的 The Document Foundation 此前就**质疑过 Euro-Office 偏向微软格式而非 ODF**。

已经用上 Euro-Office 的组织，按 Nextcloud 的说法，包括德国 Deutsche Telekom Security，以及土耳其 IT 咨询公司 Destek；法国、瑞士、菲律宾等国的其它客户正在评估。

同时这次还有一批 Nextcloud Hub「Summer 26」更新：

- **Teams 应用重做**：出现在应用菜单里，能总览自己所属的团队；每个团队一个共享文件夹（文件、任务等），思路接近微软 Teams + SharePoint 的组合。
- **团队自有文件**：从 Nextcloud Collectives 和 Deck 起步，确保创建者离开团队后，其它成员仍能访问文件；管理员新增了查看、管理团队文件夹（含配额）的工具。
- **Nextcloud Text 增强**：版面对比、脚注、文中引用、行内评论。
- **Nextcloud Tables**：关系型列，能把多个表的单元格数据联动起来；支持导入导出表结构（列、视图、基于表的 App）而不动数据。
- **AI Assistant**：能上传图片问答、翻译文本，且能跨对话记住上下文。
- **UI 改进**：跨文件/消息/事件的统一搜索（可按时间范围、人员过滤）；应用菜单图标重做；全站加了动画过渡。

---

## 解读：一个「主权办公」项目的真实处境

**1. 补齐桌面端，确实是 Euro-Office 对标微软的关键一步，但只是「可用性」层面的。**

此前只能在浏览器或手机里用，对企业里那些「就想要本地 .docx、双击打开、离线也能改」的Workflow 是硬伤。桌面端把这个缺口填上了。但 Nextcloud 自己也很克制——它说的是「最后几个缺口之一」，不是「全面对齐」。存储、权限、协同后端这些重活，依旧靠 Nextcloud Hub 这个更大的平台，Euro-Office 只负责编辑这一层。

**2. 「基于 OnlyOffice 代码库」+"主权欧洲"这一定位，本身就拧巴。**

Euro-Office 直接站在 OnlyOffice 的肩膀上，却又把自己包装成欧洲自主可控的叙事。更微妙的是，The Document Foundation（LibreOffice 的娘家）此前已经公开质疑过它**优先兼容微软 OOXML 而非 ODF**——一个主打「欧洲主权」的项目，文档格式却向微软倾斜，这事儿在开源社区里不会轻易过去。

**3. 真正的大山是「鸡生蛋」：没有规模证明，企业就不敢跳；没人跳，就永远没证明。**

Forrester 的 Martha Bennett 点得很直白：Euro-Office「还没在大型企业需要那种规模上证明过自己」，而这不只是它的问题，是所有开源替代方案的通病。她用的词是 chicken-and-egg——**不先有人跳下去，就永远提供不了那种证明**。换句话说，技术缺口可以靠一个桌面客户端补，但信任缺口只能靠真实的大规模采用去填，而那恰恰是最慢的一环。

**4. 对工程师的启示：协同办公的「主权化」是条真实赛道，但别高估短期渗透。**

如果你在做内部工具、私有云、或合规敏感场景（数据不能出欧盟），Nextcloud + Euro-Office 这类组合值得放进评估清单——本地编辑 + 自托管存储 + 跨平台客户端，形态上已经齐了。但把它当成 Microsoft 365 的即插即用平替，目前不现实：生态、插件、第三方集成、企业支持的成熟度，都还在早期。
