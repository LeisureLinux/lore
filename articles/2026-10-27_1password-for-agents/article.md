---
title: "1Password for Agents：给 AI agent 开通账号，而不是把密码交给它"
date: 2026-10-27
slug: 1password-for-agents
tags: [1Password, 密码管理器, AIAgent, 凭证, 密钥管理, OAuth, 自动填充, 代理安全, 浏览器, 隐私, 集成, 最小权限]
category: 安全/架构
author: FreeLAMP.com
original_source: "1Password 官方博客《Introducing 1Password for Agents》（2026-10-22，作者 John Torrey）"
original_author: "John Torrey（1Password）"
original_date: 2026-10-22
original_url: "https://1password.com/blog/1password-for-ai-agents"
description: "1Password 发布了「1Password for Agents」平台，核心思路不是让 agent 拿到密码，而是让 agent 请求凭证、人批准、1Password 直接在目标站点自动填充 —— agent 全程看不到密码。已支持的集成包括 Meta 的 Muse、Anthropic 的 Claude Duet、OpenAI 的 ChatGPT Work and dots、SpaceXSI 的 Grok Bot、Town 的 Townie 即将到来，另有 Instinct、Browserbase、Browser Use、Dana、KERNEL、Perplexity、Ramp、Tomo、Wajo 等排队中。本文拆解它的具体机制、它与浏览器密码管理器的能力差距、以及它真正解决的问题 —— 不是「怎么少输一次密码」，而是「怎么让 agent 的权限可被看见、可被批准、可被撤销」。"
published: true
---

> 来源：[1Password 官方博客：Introducing 1Password for Agents](https://1password.com/blog/1password-for-ai-agents)（**2026-10-22**，作者 **John Torrey**）
> 本文为**解读**。第四、五节的评价为笔者补充。

## 一句话结论

**1Password for Agents 解决的**不是「怎么让 agent 少输一次密码」，而是「**怎么让 agent 的权限可被看见、可被批准、可被撤销**」。**

**它给出的机制非常具体：**

> **「你的 agent 可以请求使用你密码库里的某个凭证，如果你批准这个请求，1Password 会直接在目标站点自动填充凭证，所以 agent 根本接触不到这些凭证。」**

**⭐ 而我认为这个设计里最值得学的，是它**拒绝**了那个最省事、也最危险的方案。**

## 一、⭐ 问题：agent 卡在登录页，只有两条烂路

**官方对现状的描述非常具体：**

> **「agent 的有用程度取决于它能不能登录到各个账号并完成你交给它的任务。当 agent 到达一个登录页面时，agent 会停下来，要求你提供那个能让它代表你登录的凭证。」**
>
> **「这时你面临一个选择。你可以接管 agent 会话、每次手动把用户名和密码输入网站 —— 这既慢又烦人。你也可以把密码粘贴进 prompt —— 这意味着允许 agent 访问你的凭证，而且可能超出当前任务本身的需要。这两种都不可接受。」**

**⭐ 请注意这段话的结构 —— 它精确地列出了两条现有的烂路，并说「这两种都不可接受」：**

| 烂路 | 问题 |
|---|---|
| **① 人工接管，每次手输** | **慢、烦人** —— 而且 agent 会话被中断 |
| **② 把密码粘进 prompt** | ⭐ **「可能超出当前任务本身的需要」** —— 凭证进了上下文窗口 |

**⭐ 第二条正是 2026 年最要命的那类问题的教科书案例：**

**一旦密码进了 prompt，它就在模型的上下文里 —— 而上下文会被记录、被缓存、被摘要、被别的工具看到。** **而且它对 agent 的授权范围是「整个会话」，而不是「这一次登录」。**

**⭐ 官方给的对比句也很到位：**

> **「在有 1Password for Agents 的情况下，agent 可以请求使用你密码库里的凭证，如果批准，1Password 直接在目标站点自动填充凭证，所以 agent 不会访问到凭证。」**

## 二、⭐ 机制：请求 → 批准 → 自动填充

**具体流程（官方原文）：**

> **「当 agent 到达一个登录界面时，agent app 会提示你从 1Password 取它继续所需的凭证。在 1Password 里审核所请求的凭证并批准 —— 全程不暴露你的密码或一次性验证码。」**

**⭐ 而这个流程之所以能成立，靠的是三个设计选择：**

### 2.1 ① 凭证留在 1Password 侧，agent 拿不到

**这是整个设计的支点。** **不是「agent 拿到凭证后去用」，而是「**1Password 替 agent 去填**」。**

**⭐ 这与 OAuth 的思路是同一个家族** —— 授权的不是「你的密码」，而是「一次受限的、可撤销的代持操作」。**

### 2.2 ② 凭证按「vault 里的哪一条」授权，不是按「密码」

**官方举例说明了粒度：**

> **「以 Muse 的 1Password 集成为例，你可以让 agent 创建一份派对邀请、追踪 RSVP、并在你的预算内搜索用品。**Muse 会在需要时向 1Password 请求访问 RSVPify 和 Oriental Trading。**你选择它能用哪个 1Password 登录，Muse 就能把你的派对办起来，而不用看到凭证、也访问不到你 1Password 密码库里的任何其它东西。」**

**⭐ 「访问不到你 1Password 密码库里的任何其它东西」这一句是重点** —— **授权粒度是「这一条登录记录」，不是「你的账号」。**

### 2.3 ③ 用户始终看得见，也随时能断

**官方三处都提到这一点：**

> **「你可以看到并批准什么会被共享，并且**随时断开这个集成**。」**
>
> **「你的密码保持有序，你的密码库保持受保护。**你能看到并批准什么会被共享，并且随时能断开集成。**」**
>
> **「你的凭证都放在一个密码库里，所以一个密码变了，你改一次，连接的 agent 就能继续用当前登录，而不用你去多个地方更新。」**

**⭐ 最后这条是 1Password 作为密码管理器的老本行，但在 agent 时代多了一层含义：**

**—— 因为 agent 是**长期存在**的，它对凭证的依赖是持续的。** **如果每次改密码都要去「多个地方更新」，agent 就成了你不敢改密码的理由。** **而「改一次就够」是让 agent 生态可持续的必要条件。**

## 三、⭐ 集成矩阵：谁已经能用，谁还在排队

**官方在博客首屏就放了一张合作方 logo 墙，这是这篇文章最直观的信号 —— 而它说明的是**这件事的规模与节奏**。**

### 3.1 已在推的（官方标注「rolling out over the coming days across all platforms」）

| 合作方 | 官方描述 |
|---|---|
| **Muse（Meta）** | 「把目标变成行动计划，并在情况变化时持续工作；使用集成时向 1Password 请求登录，让人始终掌控 Muse 能触达什么」 |
| **SpaceXSI Grok Bot** | 「跨工具、收件箱和网站工作的 AI 队友。用 1Password，Grok Bot 可以使用已批准的登录，同时凭证保持受保护」 |

### 3.2 即将支持的（官方标注「coming soon」）

| 合作方 | 官方描述 |
|---|---|
| **Anthropic 的 Claude Duet** | 「在团队已经在用的工具里工作，主动代表他们完成工作。1Password 集成在需要时给 Claude 已批准访问权限，用户不必交出密码」 |
| **OpenAI ChatGPT Work 和 dots** | 「与 1Password 协作登录全网网站。用户批准登录，**密码不会暴露给 AI 模型**」 |
| **Town Townie** | 「学习用户的人、项目与语气……员工批准 Townie 需要的登录，1Password 负责填入，于是 Townie 能持续工作而从不看到密码」 |

### 3.3 排队的

**Instinct、Browserbase、Browser Use、Dana、KERNEL、Perplexity、Ramp、Tomo、Wajo** —— 官方原话：「我们每天都在做更多。你没看到你喜欢的 agent？告诉我们，我们上线时告诉你。」

**⭐ 而我认为这份名单里最有信息量的两个是 Browserbase 和 Browser Use** —— **因为它们是「云端浏览器 / 浏览器自动化」类服务，也就是说，1Password 承认**远程跑在别人的浏览器里的 agent**同样需要凭证代持。**

### 3.4 一个容易被忽略的商业细节

> **「1Password for Agents 目前对 1Password Individual 和 Family 账户不额外收费。**1Password.eu 或 1Password.ca 上的账户目前不支持。**」**

**⭐ 而那句「可用性、平台与能力因合作方集成而异」以及「每个集成的防护措施与控制不同」（The safeguards and controls vary by integration）—— 这两句是**重要的限定**，我们后面会回到它。**

## 四、⭐⭐ 它与浏览器密码管理器的能力差距

**官方这一段写得非常坦率，值得原样引用：**

> **「浏览器密码管理器不是为让 agent 代表你登录而设计的。使用浏览器保存的密码、或把密码写在笔记里的人已经发现，他们的 agent 无法使用那些密码。每次 agent 到达登录界面，agent 都必须停下来，直到你接管并手动登录，然后 agent 才能继续。」**

**⭐ 我认为这一段精准点出了「浏览器密码管理器 vs 代理凭证」的本质差别在**授权模型**上：**

| | 浏览器密码管理器 | 1Password for Agents |
|---|---|---|
| **谁在驱动填入** | **人**（在浏览器里点扩展） | **agent 发起请求 → 人批准 → 1Password 填** |
| **授权单位** | 「这个人在这个浏览器里」 | 「这个 agent 这一次要用这一条登录记录」 |
| **agent 能不能读到明文** | ⭐ **不能**（扩展填入） | ⭐ **不能**（1Password 填入） |
| **谁决定范围** | 浏览器 profile | ⭐ **逐次请求 + 按 vault 条目授权** |
| **能不能撤销** | 关扩展 | ⭐ **断开集成 / 逐条拒绝** |
| **agent 拿到的「凭证」** | 无 | ⭐ **无** |

**⭐ 所以真正的差别不是「agent 能不能拿到密码」（两边的答案都是不能），而是：**

> **「**人**的每一次点击」变成了「**一次可以被审阅、被拒绝、被撤销的授权请求**」。**

**—— 而这正是把 agent 塞进现有工作流时，最缺的那一层抽象。**

## 五、⭐⭐ 我的评价：它解决了什么，以及三个仍未解决的问题

### 5.1 它真正解决的是「授权的可见性」

**⭐ 我认为这个产品最重要的价值在于它让一句话变得可执行：**

> **「You control what agents access and when, all the way from the prompt to the party.」**
>
> （从 prompt 到派对结束，**你掌控 agent 触达什么、何时触达**。）

**⭐ 而 2026 年的现实是：绝大多数 agent 框架提供的都是「把密钥放进环境变量 / .env 文件」这一档** —— **凭证进了 agent 的进程环境，谁在用、用在哪，agent 自己和用户都说不清。**

**⭐ 而 1Password 这个模式的价值在于：它把凭证从「agent 拥有的东西」改成了「**用户每次发放的临时通行证**」。**

### 5.2 ⚠️ 但它把一个更难的问题留给集成方了

**官方那句限定语非常关键：**

> **「1Password 和每个受支持 agent 背后的团队设计集成，以保持你的凭证与 agent 分离，所以受支持的 agent 可以在不需要看到或处理你的凭证的情况下继续工作。**各集成的防护措施与控制不同。**」**

**⭐ 翻译：** **「凭证与 agent 分离」这个承诺的**具体形态取决于每一家的实现**，而不是 1Password 统一保证的。**

**—— 这意味着 13 个集成方可能有 13 种不同的「凭证不进入 agent 上下文」的保证强度。** **而用户看到的只是一份合作方 logo 墙。**

**⭐ 我认为这是这个产品目前最大的不确定处，而它的验证方法其实存在：**

**—— **问一句「这个 agent 请求凭证时，1Password 是在**目标站点的 DOM 里**填，还是通过 **CDP / 无头浏览器协议**注入？**前者 agent 看不到，后者 agent 能不能看到取决于注入点。**

### 5.3 ⚠️ 三个仍未解决的问题

**① 「同步填充」的技术前提是「浏览器里有个可被驱动的密码管理器」—— 而这恰恰是远程 agent 最缺的东西**

**⭐ 回顾一下 §4 的那句话：** 「浏览器密码管理器不是为让 agent 代表你登录而设计的」。**那么 1Password 的自动填充是怎么发生的？**

**⭐ 官方只说「1Password 直接在目标站点自动填充」，没有说机制。** **而从 Browserbase / Browser Use 这类**云端浏览器**服务被列进集成名单来看，**答案很可能是：这些服务本身内置了 1Password 的填充能力**（这也正是它们被选中的原因）。**

**⭐ 而这带来一个诚实的推论：**

> **1Password for Agents 的覆盖范围，实际上等于「**哪些 agent 运行在一个 1Password 能驱动的浏览器里**」。**
>
> **对于运行在你自己的机器上、通过 Playwright/Puppeteer 操作本地浏览器的 agent，这个集成可能不成立 —— 而那恰恰是当下最主流的自托管 agent 形态。**

**② 「每个集成的防护措施与控制不同」+ 「1Password.eu / .ca 暂不支持」→ 覆盖度是一个持续变化的东西**

**⭐ 一个刚发布两周的平台，13 个集成、5 个在推、8 个排队、2 个域名后缀不支持。** **这是正常的发布节奏，但它意味着「**现在就用它**」这个决定，对不同 agent 的实际收益差别很大。**

**③ ⭐ 而最根本的一个问题：授权粒度仍然是「这一条登录记录」，而不是「这一次操作」**

**⭐ 这一点值得说清楚，因为它是所有 agent 安全的下一个战场：**

**1Password for Agents 解决的是「**凭证从哪来**」的问题。** **但它没有解决「**拿到这条凭证之后能干什么**」的问题。**

**—— 一个被授权访问 Instacart 的 agent，同时也拿到了你「修改配送地址」的权限。** **一个被授权访问某公司 Slack 的 agent，也拿到了「以你身份发消息」的权限。**

**⭐ 而 2026 年 10 月我们刚刚看到 php2shell 的一个关键教训：** **很多漏洞的攻击路径根本不是「拿到凭证」，而是「拿到**更高权限的状态**」。**

**—— 所以「凭证级授权」是必要条件，不是充分条件。** **下一步该来的是「操作级授权」：** **「这个 agent 这次只能读、不能写」「只能读这个文件夹」「只能发给自己」。**

**⭐ 而这条线本号此前写过的两篇文章正好接得上：**
- **《NVIDIA OpenShell》：把「agent 能碰到什么」做成可验证的策略** —— **它做的正是「操作级授权」，而且它用形式化验证检查策略变更；**
- **《Emaki》：一个给 AI agent 用的 `sudo key` 包** —— **限时、可见、可一次撤销的管理员权限。**

**⭐ 三者的方向完全一致：** **把 agent 的权限从「一把万能钥匙 + 一个 .env 文件」变成「一串可被审阅、可被拒绝、可被撤销的临时授权」。**

## 六、如果你要试

```sh
# 1Password for Agents 目前对 Individual 与 Family 账户不额外收费
# https://1password.com/personal-ai-agent-integrations
# 不支持的域名后缀：1password.eu / 1password.ca
```

**⭐ 但我的建议是：先确认你的 agent 在哪运行。**

| 你的 agent 跑在哪 | 预期可行性 |
|---|---|
| **官方托管的 agent**（Claude Duet、ChatGPT Work、Grok Bot、Townie…） | ⭐ **高** —— 集成在推进中 |
| **云端浏览器服务**（Browserbase、Browser Use） | ⭐⭐ **高** —— 它们在首批队列里，正是因为架构上最契合 |
| **本地自托管 agent + Playwright 操作本地浏览器** | ⚠️ **存疑** —— 需要 1Password 能驱动那个浏览器实例 |
| **纯 API 调用型 agent**（不发浏览器请求、只调 API） | ⚠️ **需要另一条路** —— 那本来就不该用密码，用 API key / OAuth |

**⭐ 而最后一行其实是最重要的一点：** **如果你的 agent 只需要调 API，那「密码」这个概念本来就不该出现在方案里** —— **你需要的已经是 1Password 的 Secret Reference 或 OAuth 授权，而不是 for Agents。**

**for Agents 真正独特的地方，就在于它处理的是「**没有 API、只有网页登录**」的那一大片场景** —— 订机票、订餐、买活动票、管日程、报销。**

## Sources

- 1Password 官方博客：Introducing 1Password for Agents（2026-10-22，作者 John Torrey）：https://1password.com/blog/1password-for-ai-agents
- 1Password for Agents 集成页：https://1password.com/personal-ai-agent-integrations
- 1Password 安全模型说明：https://support.1password.com/confidential-computing-security/
- 本号相关：NVIDIA OpenShell（操作级授权 + 形式化验证）/ Emaki（sudo key）

---

（说明：所有引号内内容为 1Password 官方博客原文引用；第四、五节的评价、§5.3 关于「操作级授权」的推论、以及第六节的可行性表格为笔者补充。**官方未公开「自动填充」的技术实现机制，§5.3 的推断已明确标注为推断。**）
