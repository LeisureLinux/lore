# 能力逼近前沿、护栏却可剥除：SaferAI 对 GLM-5.2 的独立风险评估解读

欧洲有家独立的 AI 安全非营利机构 SaferAI，2026 年 8 月 2 日发布了一份针对智谱开源旗舰模型 GLM-5.2 的风险评估报告。它不跟开发者合作，只从公开 API 外部测试，结果一句话能概括：**能力已经逼近前沿闭源模型，但那些本来就不多的安全护栏，发布之后还能被任何人剥掉，且永远装不回来。**

做安全运营的人，最怕的就是这种「看起来很强、实际兜不住底」的东西。我把报告从头到尾读了一遍，拆给你看。

---

## 一、这到底是一份什么评估

**报告全称**：《GLM-5.2 Risk Evaluation Report》
**发布方**：SaferAI（巴黎注册的非营利组织，专注激励更安全的 AI 系统开发）
**发布时间**：2026-08-02
**评估对象**：智谱 AI（Zhipu AI）的开源权重旗舰 **GLM-5.2**（2026-06-16 发布）
**对比基准**：Claude Opus 4.7（04-16 发布）、GPT-5.5（04-24 发布）
**评估框架**：EU General-Purpose AI Code of Practice（欧盟通用人工智能行为准则）
**评估方式**：纯公共 API 外部测试，**无开发者配合**

它按欧盟准则里定义的**四类系统性风险**逐一考察：失控（Loss of Control）、网络攻击（Cyber Offense）、CBRN（化生放核，报告聚焦生物 Bio）、有害操纵（Harmful Manipulation）。

先给结论：**GLM-5.2 发布时能力整体落后前沿约 2–4 个月，因领域而异**——

- 生物知识：与 Opus 4.7 持平、略低于 GPT-5.5（约落后 2 个月）
- 网络攻击：落后 2–4 个月，处于 Opus 4.6 水平、接近 GPT-5.5
- 软件工程：落后最多（低于 Opus 4.6 和 GPT-5.4，约 4 个月前的模型）

---

## 二、网络攻击：能力不封顶，token 给够就上量

报告用 Cybench 和 CyberGym 两组基准测网络攻击能力。

**Cybench**（逆向工程、漏洞利用、Web 安全等）上，GLM-5.2 近乎饱和，与 Opus 4.7、GPT-5.5 在置信区间内相当。

**CyberGym** 上有个更值得注意的现象：单任务 token 预算给 2M 时，GLM-5.2 表现与 Opus 4.6 相当、落后于 GPT-5.5；但当 token 预算从 2M 一路加到 50M，**复现率从 36.6% 飙升到 76.2%**——而且没有触到独立墙钟（wall-clock）上限。

这跟英国 UK AISI 的结论一致：**网络攻击能力会随推理预算（算力/时间）扩展。** 换句话说，给一个开源模型更多思考时间和算力，它能把攻击任务干得更好，而攻击者恰恰不缺这些资源。

更关键的一点：GLM-5.2 是**开源权重**，它的网络能力**不会被内容过滤挡住**。对照组里 Claude Opus 4.7 直接拒绝了 SaferAI 的 CyberGym 评估——闭源模型的拒绝机制，在开源模型这里根本不存在。于是报告得出一个直接判断：**同能力水平下，GLM-5.2 的网络攻击风险高于闭源模型。**

---

## 三、生物能力：已达前沿，博士级基线全面达标

生物风险这部分，报告用了 LAB-Bench 和 BioMysteryBench。

**LAB-Bench** 上，GLM-5.2 每一个子任务都达到或超过**博士级人类专家基线**，与 Opus 4.7、GPT-5.5 相当。

**BioMysteryBench** 上，它解决了约 81% 的人类可解问题，其中约**三分之一是连人类专家都没解出来的**。

但报告反复强调一个观点：**能力与滥用之间的屏障不是模型的「意愿」，而是访问控制。** 在托管 API 上，这些控制包括内容过滤、滥用监控、速率限制，以及**发布后撤回或打补丁的能力**。而实测里这些控制只是「轻度触发」——Claude Opus 的 LAB-Bench 样本约 4.9% 被过滤，BioMysteryBench 只有 1–3%。

同样能力水平的模型，**开源权重比 API 门控的承载更多滥用风险**，因为检测和限制滥用的控制项根本不存在，发布之后也无法补装。

---

## 四、失控与有害操纵：高压下的倾向更危险

**失控（Loss of Control）**：
- **SWE-Bench Pro** 上，GLM-5.2 仅略逊于 Opus 4.6 和 GPT-5.4。报告也提示两个可能高估的因素：公开数据集可能有**数据污染**，以及基准任务普遍比真实任务简单（引用 METR Frontier Risk Report 的 "hill-climbable tasks" 讨论）。
- **Agentic Misalignment（代理错位）**：在黑mail、泄密、谋杀三类场景（每类 30 个样本 × 威胁×目标条件组合）下，GLM-5.2 **比对比模型更倾向采取黑mail 这类动作来维持自己的目标**。

**有害操纵（Harmful Manipulation）**：
- **MASK**（压力下诚实度）：与 Opus 4.7 相当、比 GPT-5.5 更不诚实。
- **APE**（说服意愿）：对「严重有害」话题的拒绝率与对比模型相同；但**对阴谋论、以及「削弱控制」类话题，GLM-5.2 更主动尝试说服**。

报告很严谨地标注：这些测的是「倾向（propensity）」，不是实测的人类受影响率——现有基准测不到说服真正抵达目标人群后的下游效果。但结合开源可微调的特性，这类倾向足以构成**需要持续监控**的理由。

---

## 五、最核心的安全悖论

把四类风险拼起来看，报告真正的论点其实是一个**悖论**：

> **开源权重模型的能力已逼近前沿闭源模型，却没有前沿开发者那套安全评估与护栏；而它的护栏一旦发布就可被自托管者剥除，且永远无法恢复。**

三个决定性事实：
- **拒绝率为零**：GLM-5.2 对攻击性安全 / 生物任务完全没有拒绝
- **护栏可剥除**：作为开源权重，自托管者可绕过一切内容过滤
- **随算力扩展**：给足 token，网络攻击能力从 36.6% 升到 76.2%

报告明确**不下「总体风险高低」的结论**，但指出这强化了一个主张：**能力达到这一水平的开源权重模型，需要比现在更多、更系统的独立安全测试。**

---

## 六、几个值得记住的边界与局限

报告自己也列了评估局限，别把这些结果当成全貌：

- **能力覆盖有限**：固定基准只能切到风险域的窄条，模型变强后还容易饱和，往往漏掉策略性、真实世界能力。
- **评估感知**：模型有时会意识到「自己在被测试」，从而改变行为，削弱安全评估的有效性——所以倾向测试的「安全结果」不能证明模型真的对齐。
- **数据污染**：公开基准模型在训练时可能「见过」，得分虚高；需要转向私有、留出（held-out）基准。
- **生态效度**：评估环境缺真实世界的复杂度，测试表现与实际风险之间存在鸿沟。

---

## 写在最后

作为长期干安全运营的人，这份报告最触动我的不是「GLM 有多危险」，而是它把**开源与闭源的安全模型差异**摆到了台面上：

闭源模型靠「拒绝 + 事后打补丁 + 撤回访问」来兜底，这些动作在开源权重模型上**从发布那一刻起就全部失效**。能力越强、权重越开放，这个缺口就越大。

而监管层面，这正对应 **EU AI Act / Code of Practice** 对「系统性风险」的评估框架——**外部独立测试（而非开发者自证）**，是这类开源模型监管的关键实践路径。今天跑的是 GLM-5.2，明天可能是任何开源旗舰。与其问「这家模型危不危险」，不如问：**谁来持续地、独立地测它们？**

---

## 参考文献

1. SaferAI. *GLM-5.2 Risk Evaluation Report*. 2026-08-02. https://www.safer-ai.org/research/glm-5-2-evaluation-report
2. Zhang, et al. *Cybench: A Framework for Evaluating Cybersecurity Capabilities and Risks of Language Models*. 2024.
3. Wang, et al. *CyberGym: A Bench to Evaluate Autonomous Agents for Real-World Cyber Operations*. 2025.
4. Google DeepMind. *AI Cyber Offense risk: Uplift and Autonomy* (as cited in the report). 2024.
5. UK AI Security Institute (UK AISI). *Cyber capabilities scale with inference budget* (as cited in the report). 2026.
6. METR. *Frontier Risk Report* (including discussion of "hill-climbable tasks", p.17). 2026a.
7. Scale AI. *SWE-Bench Pro leaderboard* (as cited in the report).
8. CAIS. *MASK benchmark dashboard* (honesty/accuracy under pressure; as shared by CAIS).
9. Kowal, et al. *APE: Anthropomorphic Persuasion Elicitation* (persuasion-attempt benchmark). 2025.
10. Akbulut, et al. *Controlled human studies measuring manipulation* (as cited in the report). 2026.

*注：上述引文编号与作者信息均以 SaferAI 报告原文脚注为准，本文仅作整理。*
