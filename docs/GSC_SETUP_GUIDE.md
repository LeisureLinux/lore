# Google Search Console 自动化配置指南

本文档说明如何配置 GitHub Actions 自动提交 sitemap 到 Google Search Console。

## 快速方案（推荐）

**如果你只需要提交一次 sitemap**，直接手动操作即可：

1. 访问 [Google Search Console](https://search.google.com/search-console)
2. 添加资源：`https://leisurelinux.github.io/lore/`
3. 验证所有权（选择 HTML 文件验证或 DNS 验证）
4. 左侧菜单 → **站点地图** → 输入 `sitemap.xml` → 提交

**Google 会自动定期抓取 sitemap**，无需后续维护。

---

## 完全自动化方案（进阶）

如果你希望每次部署后自动通知 Google，按以下步骤配置：

### 步骤 1：创建 Google Cloud Service Account

1. 访问 [Google Cloud Console](https://console.cloud.google.com/)
2. 创建新项目（或使用现有项目）
3. 启用 **Google Search Console API**：
   - 导航到 **APIs & Services** → **Library**
   - 搜索 "Search Console API" → 点击 **Enable**

4. 创建 Service Account：
   - 导航到 **IAM & Admin** → **Service Accounts**
   - 点击 **Create Service Account**
   - 名称：`github-actions-gsc`
   - 角色：无需选择（后续在 GSC 中配置权限）
   - 点击 **Done**

5. 创建 JSON Key：
   - 点击刚创建的 Service Account
   - 点击 **Keys** 标签 → **Add Key** → **Create new key**
   - 选择 **JSON** → 下载 key 文件（保存为 `gsc-key.json`）

### 步骤 2：在 GSC 中添加 Service Account

1. 打开 `gsc-key.json`，找到 `client_email` 字段（类似 `github-actions-gsc@project-id.iam.gserviceaccount.com`）

2. 访问 [Google Search Console](https://search.google.com/search-console)

3. 选择你的站点：`https://leisurelinux.github.io/lore/`

4. 点击左侧 **设置** → **用户和权限**

5. 点击 **添加用户**：
   - 邮箱：输入 `client_email` 的值
   - 权限：选择 **已验证所有者**（Full）
   - 点击 **邀请**

### 步骤 3：添加 GitHub Secret

1. 访问你的 GitHub 仓库：`https://github.com/LeisureLinux/lore`

2. 导航到 **Settings** → **Secrets and variables** → **Actions**

3. 点击 **New repository secret**：
   - Name: `GSC_SERVICE_ACCOUNT_JSON`
   - Value: 复制 `gsc-key.json` 文件的**完整内容**（包括所有花括号和引号）
   - 点击 **Add secret**

### 步骤 4：测试自动化

1. 推送任意改动到 `main` 分支，触发部署
2. 部署完成后，GitHub Actions 会自动运行 `Submit Sitemap to Google Search Console` workflow
3. 查看 Actions 日志确认提交成功

---

## 故障排查

### 错误 403: Permission denied

**原因**：Service Account 未添加到 GSC 或权限不足

**解决**：
1. 确认 Service Account 邮箱已添加到 GSC
2. 确认权限为「已验证所有者」（不是「所有者」或「编辑」）
3. 确认邮箱已接受邀请（检查 Service Account 邮箱的收件箱，虽然通常自动接受）

### 错误 404: Site not found

**原因**：站点未在 GSC 中注册

**解决**：
1. 手动访问 GSC 添加站点
2. 或等待脚本自动添加（脚本会尝试自动添加站点）

### Workflow 跳过执行

**原因**：未配置 `GSC_SERVICE_ACCOUNT_JSON` Secret

**解决**：
- 按照步骤 3 添加 Secret
- 或禁用此 workflow（删除 `.github/workflows/submit-sitemap-gsc.yml`）

---

## 本地测试

如果想在本地测试脚本：

```bash
# 安装依赖
pip install google-auth google-api-python-client

# 设置环境变量
export GSC_SERVICE_ACCOUNT_JSON=/path/to/gsc-key.json

# 运行脚本
python scripts/submit_sitemap_to_gsc.py
```

---

## 替代方案：IndexNow（Bing/Yandex）

如果不需要 Google 自动化，可以使用 IndexNow 协议自动通知 Bing/Yandex：

- 已配置：`.github/workflows/indexnow.yml`
- 无需 API key，开箱即用
- 每次部署后自动提交

---

## 参考资源

- [Google Search Console API 文档](https://developers.google.com/webmaster-tools/v1/api_reference)
- [IndexNow 规范](https://www.indexnow.org/)
- [GitHub Actions 文档](https://docs.github.com/en/actions)
