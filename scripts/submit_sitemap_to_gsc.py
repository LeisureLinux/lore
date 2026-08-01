#!/usr/bin/env python3
"""
Google Search Console API - Sitemap 自动提交脚本

使用方法：
1. 在 Google Cloud Console 创建 Service Account
2. 下载 JSON key 文件
3. 在 GSC 中添加 Service Account 邮箱为「已验证所有者」
4. 设置环境变量：export GSC_SERVICE_ACCOUNT_JSON=/path/to/key.json
5. 运行：python scripts/submit_sitemap_to_gsc.py

参考文档：
https://developers.google.com/webmaster-tools/v1/api_reference
"""

import os
import sys
import json
from pathlib import Path

# 检查依赖
try:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
except ImportError:
    print("❌ 缺少依赖，请安装：")
    print("   pip install google-auth google-api-python-client")
    sys.exit(1)

# 配置
SITE_URL = "https://leisurelinux.github.io/lore/"
SITEMAP_URL = "https://leisurelinux.github.io/lore/sitemap.xml"
SCOPES = ['https://www.googleapis.com/auth/webmasters']


def get_credentials():
    """从环境变量加载 Service Account 凭据"""
    key_path = os.environ.get('GSC_SERVICE_ACCOUNT_JSON')
    
    if not key_path:
        print("❌ 未设置环境变量 GSC_SERVICE_ACCOUNT_JSON")
        print("   请设置：export GSC_SERVICE_ACCOUNT_JSON=/path/to/service-account-key.json")
        sys.exit(1)
    
    if not Path(key_path).exists():
        print(f"❌ 找不到 Service Account key 文件：{key_path}")
        sys.exit(1)
    
    return service_account.Credentials.from_service_account_file(
        key_path, scopes=SCOPES
    )


def submit_sitemap():
    """提交 sitemap 到 Google Search Console"""
    print(f"🚀 提交 sitemap 到 Google Search Console...")
    print(f"   站点：{SITE_URL}")
    print(f"   Sitemap：{SITEMAP_URL}")
    print()
    
    # 获取凭据
    credentials = get_credentials()
    
    # 构建 API 客户端
    service = build('searchconsole', 'v1', credentials=credentials)
    
    try:
        # 检查站点是否已添加
        sites = service.sites().list().execute()
        site_urls = [s['siteUrl'] for s in sites.get('siteEntry', [])]
        
        if SITE_URL not in site_urls:
            print(f"⚠️  站点 {SITE_URL} 未在 GSC 中，正在添加...")
            service.sites().add(siteUrl=SITE_URL).execute()
            print(f"✅ 站点已添加")
        
        # 提交 sitemap
        service.sitemaps().submit(
            siteUrl=SITE_URL,
            feedpath=SITEMAP_URL
        ).execute()
        
        print(f"✅ Sitemap 提交成功！")
        print()
        print(f"📊 查看状态：https://search.google.com/search-console/sitemaps?resource_id={SITE_URL}")
        
        return True
        
    except Exception as e:
        print(f"❌ 提交失败：{e}")
        
        # 常见错误处理
        if '403' in str(e):
            print()
            print("💡 可能的原因：")
            print("   1. Service Account 邮箱未添加到 GSC")
            print("   2. Service Account 没有「已验证所有者」权限")
            print()
            print("📝 解决步骤：")
            print("   1. 访问 https://search.google.com/search-console")
            print(f"   2. 设置 → 用户和权限 → 添加用户")
            print(f"   3. 输入 Service Account 邮箱（在 JSON key 中的 client_email）")
            print(f"   4. 权限选择「已验证所有者」")
        
        return False


if __name__ == '__main__':
    success = submit_sitemap()
    sys.exit(0 if success else 1)
