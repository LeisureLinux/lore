# systemd 262 正式发布：内嵌兜底 unit、LUO 热更新会话，还带一只「AI 提交金丝雀」

> 原文：[systemd 262 Released With AI/LLM Canary For Unreviewed Code, LUO Integration](https://www.phoronix.com/news/systemd-262)（Phoronix，Michael Larabel，2026-09-22）。本文由 LeisureLinux 翻译整理并加注解读；文内事实来自原文。

systemd 262 今天正式发布，是这套 Linux init 与服务管理器的最新功能更新。和往常一样，又是一次「功能密集」的大版本。其亮点里最抓人的是一条：**给未审查的 AI/LLM 代码贡献装了一只金丝雀（canary）**。

## 译文：262 有什么

几个重点：

- **systemd 管理器现在内嵌了一套基础 unit 文件**，在磁盘上的文件加载不到、或容器场景没装任何 unit 时，就靠它们兜底——基本是 reboot / shutdown target、`systemd-poweroff.service`、`multi-user.target` 的内存版 fallback。
- **systemd 现在可以编成单个静态链接的 PID 1 / executor 二进制**，给极小的容器用。
- **`NUMAPolicy=`** 选项新增 `preferred-map` 与 `weighted-interleave` 取值。
- **service unit 新增 `LUOSession=` 选项**，让 systemd 创建 Live Update Orchestrator（LUO）会话；此外还有围绕 LUO 的其他 systemd 集成改进。
- **`systemd-firstboot`** 支持 `systemd.firstboot=headless`，抑制所有交互提示，做无人值守自动配置。
- **`systemd-coredump`** 现在支持 Linux 6.17 引入的 kernel coredump socket 协议。
- **`systemd-homed`** 的新 FSCRYPT 备份家目录默认采用 FSCRYPT v2 策略。
- **`systemd-cryptenroll`** 多了首次启动（first-boot）注册向导。
- **`systemd-vmspawn`** 的 `--coco=` 选项在原有 AMD SEV-SNP 之外，新增 Intel TDX 机密计算支持。
- 新增 **dm-clone boot 集成**。
- 以及那只 **AI canary**：用于检测未经过审查的 AI/LLM 代码贡献。

完整变更列表见 GitHub 上的 [v262 release](https://github.com/systemd/systemd/releases/tag/v262)。

## 解读：正式版的头条，是那只「AI 金丝雀」

**1. rc1 我们已经写过，正式版相对 rc1 真正新增的，是 AI canary 与 LUO 收口。**

我们 08-26 发过 262-rc1 的深度解读（内嵌兜底 unit、PID1 静态多调用二进制、机密计算全栈加码）。正式版把 rc1 的方向进一步坐实：rc1 出现的 `LUOSession=`（Live Update Orchestrator 热更新会话）从「集成改进」变成正式选项，意味着「不停机更新 running 系统」从实验走向可用；而 rc2 引出的 **AI canary** 是正式版才被确认保留的头条特性。

**2. AI canary 是什么、为什么重要：给开源供应链的「AI 提交」装报警器。**

「未审查的 AI/LLM 代码贡献」是 2026 年开源维护者最头疼的新问题——大量低质、未读、由 LLM 批量生成的 PR/补丁涌入。systemd 这只 canary 的作用，是在贡献流程里**探测并标记那些疑似机器生成、未经人审的代码**，把「人有没有真的看过这段改动」变成可被检查的信号。方向值得记：这不是禁止 AI 写代码，而是让「AI 生成 + 无人审」这一危险组合在 CI/贡献门禁处显形。可类比的逻辑，正是我们写过的「AI 红队/护栏平台」那一套——把不可信输入（这里是 AI 生成代码）在入口处做检测与标注。

**3. 内嵌兜底 unit + 静态 PID1：容器的最小化在收敛。**

rc1 我们就点过：systemd 把兜底 unit 编进管理器自身、又能编成单文件静态 PID1，目标就是让最小容器跑 systemd 几乎零依赖。正式版确认这套能力落地——对 OCI/微 VM 场景（尤其机密计算 vmspawn 里 SEV-SNP/TDX）意义重大：一个能 self-host unit 的 PID1，意味着更小的攻击面、更可复现的镜像。和我们报道过的「Ubuntu 26.10 把 cp/mv/rm 迁到 Rust coreutils」是同一股潮流：基础系统组件在往「小、静态、自包含」重组。

**4. 一个现实提醒：262 的破坏性改动要等 release note 逐条核对。**

Phoronix 这则短讯列的是亮点，没展开 breaking change。我们在 rc1 解读里已整理过一批（如 `-Dbuild-executor-shared=single` 重命名为 `-Dsystemd-multicall-binary=true`、`Type=notify-reload` 协议更严、`journalctl -F` 拒绝过滤器、TPM 绑定凭据旧版不识别）。升级 systemd 是动 PID1 的事，**发行版滚动前请先对 rc1→262 的「Notable breaking changes」逐条过一遍**——尤其用了 TPM 凭据、LUKS、repart 的装机。

一句话收尾：systemd 262 把 rc1 的方向坐实（LUO 热更新 + 最小容器 PID1），又加了一只 AI canary——这恰是 2026 年的写照：连 init 系统都开始专门对付「没被人读过的 AI 代码」了。
