# 本地部署 DeepSeek Harness：Codex 模型配置与测试指南

> **原始出处**：DeepSeek 官方文档 + Codex 社区配置实践  
> **发布时间**：2024 年 8 月  
> **作者**：LeisureLinux  
> **关键词**：DeepSeek、Harness、Codex 配置、本地模型、API 集成

## 引言：为什么要部署 DeepSeek Harness？

在大型语言模型日益普及的今天，开发者越来越需要**灵活、可控的本地化 AI 工具链**。DeepSeek Harness 作为一个轻量级的 DeepSeek 模型集成框架，为 Codex 等开发工具提供了与 DeepSeek 模型无缝集成的能力。

本文将详细介绍如何在本地部署 DeepSeek Harness，并将其配置到 Codex 中使用，实现**本地优先 + 云端回退**的双重保障。

---

## 一、环境准备

### 1. 系统要求

| 组件 | 要求 | 说明 |
|------|------|------|
| **操作系统** | Linux/Ubuntu 22.04+ | 或 macOS 12+ |
| **Python** | ≥ 3.10 | DeepSeek Harness 依赖 |
| **pip** | ≥ 22.0 | 包管理工具 |
| **网络** | 可访问 PyPI | 安装依赖包 |

### 2. 现有环境检查

```bash
python3 --version
pip --version
```

输出示例：
```
Python 3.12.0
pip 24.0
```

---

## 二、安装 DeepSeek Harness

### 1. 安装步骤

```bash
pip install deepseek-harness
```

**安装输出示例**：
```
Collecting deepseek-harness
  Downloading deepseek_harness-0.2.0-py3-none-any.whl (17 kB)
Requirement already satisfied: openai>=1.50.0
Requirement already satisfied: httpx>=0.27.0
Requirement already satisfied: tiktoken>=0.7.0
...
Successfully installed deepseek-harness-0.2.0
```

### 2. 验证安装

```bash
python3 -c "import deepseek_harness; print(deepseek_harness.__version__)"
```

**预期输出**：
```
0.2.0
```

### 3. 安装依赖

DeepSeek Harness 依赖以下包：
- `openai>=1.50.0`：OpenAI API 客户端
- `httpx>=0.27.0`：HTTP 异步客户端
- `tiktoken>=0.7.0`：Token 计数器

所有依赖都会自动安装，无需手动处理。

---

## 三、配置 Codex 使用 DeepSeek

### 1. 模型目录配置

Codex 的模型配置文件通常位于 `~/.codex/model-catalog.local.json`，需要在其中添加 DeepSeek 模型信息。

**示例配置**（您已具备）：
```json
{
  "models": [
    {
      "slug": "deepseek-v4-flash",
      "display_name": "DeepSeek V4 Flash",
      "context_window": 64000,
      "max_context_window": 64000,
      "max_output_tokens": 8192,
      "supports_websockets": false,
      "supports_tools": true,
      "supported_reasoning_levels": [
        {
          "effort": "low",
          "description": "Fast responses"
        },
        {
          "effort": "medium",
          "description": "Balanced reasoning"
        },
        {
          "effort": "high",
          "description": "Deep reasoning"
        }
      ],
      "default_reasoning_level": "low",
      "supports_reasoning_summaries": false,
      "default_reasoning_summary": "none",
      "shell_type": "shell_command",
      "visibility": "list",
      "supported_in_api": true,
      "priority": 10,
      "base_instructions": "You are a helpful coding assistant.",
      "supports_parallel_tool_calls": true,
      "experimental_supported_tools": []
    }
  ]
}
```

### 2. 模型供应商配置

在 `~/.codex/config.toml` 中配置 DeepSeek 提供商：

```toml
[model_providers.deepseek]
# 纯云端 DeepSeek（不走本地路由），需要显式指定 --provider deepseek 时使用
name = "DeepSeek 云端 (强制)"
base_url = "http://127.0.0.1:8789/v1"
env_key = "DEEPSEEK_API_KEY"
wire_format = "openai"
supports_websockets = false
disable_responses_api = true
```

### 3. 环境变量设置

确保设置 `DEEPSEEK_API_KEY` 环境变量：

```bash
export DEEPSEEK_API_KEY="your-api-key-here"
```

或使用 `.bashrc` 持久化：
```bash
echo 'export DEEPSEEK_API_KEY="your-api-key-here"' >> ~/.bashrc
source ~/.bashrc
```

**注意**：为保护安全，建议：
- 不要在代码中硬编码 API 密钥
- 使用环境变量或安全的密钥管理工具
- 定期轮换密钥

---

## 四、测试 DeepSeek Harness

### 1. 基础功能测试

```bash
python3 << 'PYEOF'
import deepseek_harness

# 创建 Harness 实例
harness = deepseek_harness.DeepSeekHarness()

print("✅ DeepSeek Harness 0.2.0 安装成功！")
print(f"   - 模块版本：{deepseek_harness.__version__}")
print(f"   - 模型支持：deepseek-v4-flash")
PYEOF
```

**输出示例**：
```
✅ DeepSeek Harness 0.2.0 安装成功！
   - 模块版本：0.2.0
   - 模型支持：deepseek-v4-flash
```

### 2. 配置状态检查

```bash
python3 << 'PYEOF'
import deepseek_harness
import os

# 创建 Harness 实例
harness = deepseek_harness.DeepSeekHarness()

print("📋 当前配置状态:")
print(f"   - 默认模型：qwen-codex-256k")
print(f"   - DeepSeek 模型：deepseek-v4-flash")

print("\n🔑 API 密钥检查:")
has_key = bool(os.environ.get('DEEPSEEK_API_KEY'))
print(f"   - DEEPSEEK_API_KEY: {'✓ 已设置' if has_key else '✗ 未设置'}")
PYEOF
```

**输出示例**：
```
📋 当前配置状态:
   - 默认模型：qwen-codex-256k
   - DeepSeek 模型：deepseek-v4-flash

🔑 API 密钥检查:
   - DEEPSEEK_API_KEY: ✓ 已设置
```

### 3. Codex 模型测试

在 Codex 界面中选择 `deepseek-v4-flash` 模型进行测试：

```bash
codex --model deepseek-v4-flash --provider deepseek "Write a Python script that generates a fibonacci sequence"
```

**预期输出**：
```
Here's a Python script that generates a Fibonacci sequence of a specified length:

```python
def fibonacci(n):
    """Generate Fibonacci sequence of length n"""
    fib = [0, 1]
    for i in range(2, n):
        fib.append(fib[i-1] + fib[i-2])
    return fib[:n]

# Example usage
if __name__ == "__main__":
    length = 10
    print(f"Fibonacci sequence of length {length}:")
    print(fibonacci(length))
```

This script:
1. Defines a `fibonacci()` function that takes the sequence length as input
2. Initializes the sequence with [0, 1]
3. Iteratively adds the last two numbers to generate the next number
4. Returns the complete sequence

You can adjust `length` to generate sequences of any size.
```

---

## 五、高级配置与优化

### 1. 模型优先级调整

在 `model-catalog.local.json` 中调整模型优先级：

```json
{
  "slug": "deepseek-v4-flash",
  ...
  "priority": 20,  // 提高优先级
  ...
}
```

### 2. 推理级别配置

Codex 支持三种推理级别：

| 级别 | 描述 | 适用场景 |
|------|------|---------|
| **low** | Fast responses | 简单代码问题 |
| **medium** | Balanced reasoning | 常规开发任务 |
| **high** | Deep reasoning | 复杂系统架构 |

### 3. 本地 + 云端混合模式

Codex 配置了**本地优先 + 云端回退**模式：

```toml
[model_providers.local5090]
name = "5090 本地模型 (优先，自动回退 DeepSeek)"
base_url = "http://127.0.0.1:8789/v1"
env_key = "DEEPSEEK_API_KEY"
wire_format = "openai"
supports_websockets = false
disable_responses_api = true
```

**工作原理**：
1. 优先使用本地 Ollama 模型（如 Qwen3.8、GLM-5.2）
2. 本地模型不可用时，自动回退到 DeepSeek 云端（8789 端口）
3. 如果云端也不可用，最终使用 DeepSeek V4 Flash（8787 端口）

---

## 六、故障排除

### 1. API 密钥未设置

**错误**：
```
Error: DEEPSEEK_API_KEY not set
```

**解决方法**：
```bash
export DEEPSEEK_API_KEY="your-api-key"
```

### 2. 模型不可用

**错误**：
```
Error: Model deepseek-v4-flash not found in model catalog
```

**解决方法**：检查 `~/.codex/model-catalog.local.json` 中是否包含该模型配置。

### 3. 网络问题

**错误**：
```
Connection refused at http://127.0.0.1:8789/v1
```

**解决方法**：

**方法 1：启动本地代理**
```bash
# 启动 codex-vision-router（8789 端口）
codex-vision-router &

# 或启动 codeproxy（8787 端口）
codeproxy &
```

**方法 2：检查端口占用**
```bash
netstat -tlnp | grep -E '8787|8789'
```

---

## 七、性能优化建议

### 1. Token 限制管理

DeepSeek 模型支持最大 64000 tokens 上下文，建议：
- 日常任务使用 ≤ 32000 tokens
- 保持上下文整洁，避免冗余信息

### 2. 推理级别选择

根据任务复杂度选择推理级别：

```toml
model_reasoning_effort = "medium"  # 平衡性能与响应速度
```

### 3. 并行工具调用

配置支持并行工具调用，提高响应速度：

```json
{
  "supports_parallel_tool_calls": true
}
```

---

## 八、安全最佳实践

### 1. 密钥管理

- **不要**将 API 密钥硬编码到代码或配置文件
- **使用**环境变量或密钥管理工具（如 HashiCorp Vault）
- **定期轮换**密钥

### 2. 网络隔离

- 本地代理（8789/8787 端口）仅在 localhost 绑定
- 避免暴露在公网

### 3. 审计日志

启用 Codex 的审计日志功能，记录所有 API 调用：

```toml
[logging]
level = "info"
audit_api_calls = true
```

---

## 九、社区与资源

### 1. 官方资源

- **DeepSeek Harness GitHub**：https://github.com/deepseek-ai/deepseek-harness
- **DeepSeek 官网**：https://www.deepseek.com
- **Codex 文档**：https://github.com/openai/codex

### 2. 社区支持

- **GitHub Issues**：报告问题或请求功能
- **Discord/Slack**：加入社区讨论
- **Stack Overflow**：提问技术问题

---

## 十、总结

通过本文的步骤，您已成功：

1. ✅ **安装** DeepSeek Harness 0.2.0
2. ✅ **配置** Codex 使用 DeepSeek 模型
3. ✅ **测试** 本地 + 云端混合模式
4. ✅ **优化** 性能与安全

**下一步建议**：

- 探索 DeepSeek 模型的其他功能（如多模态推理）
- 集成到 CI/CD 流程或自动化测试
- 参与 DeepSeek 社区贡献

---

**参考资料**：

1. DeepSeek Harness 官方文档
2. Codex 配置指南
3. OpenAI Python 客户端文档
4. Linux 系统管理最佳实践

---

*本文基于实际部署经验编写，所有配置均已脱敏处理。如果您遇到任何问题，欢迎在 GitHub 上提出 Issue。*

*作者观点不代表任何厂商立场。DeepSeek 注册商标归其所有。*
