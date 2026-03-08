#!/usr/bin/env python3
"""
Cloudflare Worker 一键部署脚本

功能:
1. 创建 KV Namespace
2. 配置 wrangler.toml
3. 部署 Worker 并设置环境变量
4. 更新 config.json

使用:
    python setup_cloudflare.py
"""

import os
import sys
import json
import subprocess
import shutil
from pathlib import Path


def run_cmd(cmd, check=True, capture=True, input_text=None):
    """执行命令并返回结果"""
    print(f"  执行: {cmd}")
    try:
        if capture:
            result = subprocess.run(
                cmd,
                shell=True,
                check=check,
                capture_output=True,
                text=True,
                input=input_text,
            )
            if result.stdout:
                print(f"  输出: {result.stdout.strip()}")
            return result.stdout.strip() if result.stdout else ""
        else:
            subprocess.run(cmd, shell=True, check=check, input=input_text)
            return ""
    except subprocess.CalledProcessError as e:
        if capture and e.stderr:
            print(f"  错误: {e.stderr.strip()}")
        if check:
            sys.exit(1)
        return ""


def input_with_default(prompt, default=""):
    """带默认值的输入"""
    if default:
        result = input(f"{prompt} [{default}]: ").strip()
        return result if result else default
    return input(f"{prompt}: ").strip()


def check_wrangler():
    """检查 wrangler 是否安装"""
    print("\n📦 检查 wrangler...")
    result = run_cmd("wrangler --version", check=False)
    if not result:
        print("  wrangler 未安装，正在安装...")
        run_cmd("npm install -g wrangler")
        run_cmd("wrangler --version")


def wrangler_login():
    """Cloudflare 登录"""
    print("\n🔐 登录 Cloudflare...")
    print("  将在浏览器中打开登录页面...")
    run_cmd("wrangler login")


def create_kv_namespace():
    """创建 KV Namespace"""
    print("\n📦 创建 KV Namespace...")

    # 检查是否已存在
    result = run_cmd("wrangler kv:namespace list", check=False)
    if "MAIL_KV" in result:
        print("  KV Namespace MAIL_KV 已存在")
        # 提取 ID
        for line in result.split("\n"):
            if "MAIL_KV" in line:
                parts = line.split()
                for i, p in enumerate(parts):
                    if p == "MAIL_KV" and i + 1 < len(parts):
                        return parts[i + 1]
        return None

    result = run_cmd("wrangler kv:namespace create MAIL_KV")
    # 提取 id = "xxx"
    import re

    match = re.search(r'id\s*=\s*"([^"]+)"', result)
    if match:
        return match.group(1)

    # 备用方法: 解析输出
    for line in result.split("\n"):
        if "id" in line.lower():
            parts = line.split("=")
            if len(parts) >= 2:
                return parts[1].strip().strip('"')

    return None


def create_wrangler_toml(kv_id):
    """创建 wrangler.toml"""
    print("\n📝 创建 wrangler.toml...")

    toml_content = f'''name = "chatgpt-mail-worker"
main = "cf-worker/worker.js"
compatibility_date = "2024-01-01"

[[kv_namespaces]]
binding = "MAIL_KV"
id = "{kv_id}"
'''

    with open("wrangler.toml", "w") as f:
        f.write(toml_content)

    print("  已创建 wrangler.toml")


def set_secrets(email_domain, admin_password):
    """设置环境变量"""
    print("\n🔑 设置环境变量...")

    # JWT_SECRET - 随机字符串
    import secrets

    jwt_secret = secrets.token_hex(32)

    # ADMIN_PASSWORD
    print("  设置 ADMIN_PASSWORD...")
    run_cmd(
        f'echo "{admin_password}" | wrangler secret put ADMIN_PASSWORD', check=False
    )

    # JWT_SECRET
    print("  设置 JWT_SECRET...")
    run_cmd(f'echo "{jwt_secret}" | wrangler secret put JWT_SECRET', check=False)

    # EMAIL_DOMAIN
    print("  设置 EMAIL_DOMAIN...")
    run_cmd(f'echo "{email_domain}" | wrangler secret put EMAIL_DOMAIN', check=False)

    print("  环境变量设置完成!")


def deploy_worker():
    """部署 Worker"""
    print("\n🚀 部署 Worker...")
    run_cmd("wrangler deploy")


def update_config_json(worker_domain, email_domain, admin_password):
    """更新 config.json"""
    print("\n📝 更新 config.json...")

    config_path = Path("config.json")

    if config_path.exists():
        with open(config_path) as f:
            config = json.load(f)
    else:
        config = {}

    # 更新配置
    config["mail_provider"] = "cfworker"
    config["cf_worker_domain"] = worker_domain
    config["cf_email_domain"] = email_domain
    config["cf_admin_password"] = admin_password

    with open(config_path, "w") as f:
        json.dump(config, f, indent=4, ensure_ascii=False)

    print("  config.json 已更新!")


def print_email_routing_instructions(email_domain, worker_domain):
    """打印 Email Routing 配置说明"""
    print("\n" + "=" * 60)
    print("📧 Email Routing 配置 (需手动完成)")
    print("=" * 60)
    domain_part = (
        "/".join(email_domain.split(".")[-2:]) if "." in email_domain else email_domain
    )
    print(f"""
请在 Cloudflare Dashboard 完成以下配置:

1. 访问: https://dash.cloudflare.com/{domain_part}/email/routing

2. 点击 "Create custom address" 或 "Set up catch-all"

3. 配置:
   - Destination address: *@{email_domain}
   - Action: Send to worker
   - Worker: chatgpt-mail-worker

4. 确保域名的 DNS 已正确配置:
   - MX 记录: @{email_domain} → mailchannels.tx

5. 验证:
   curl https://{worker_domain}/api/mails
   # 应返回: {{"error":"unauthorized"}}
""")
    print("=" * 60)
    print(f"""
请在 Cloudflare Dashboard 完成以下配置:

1. 访问: https://dash.cloudflare.com/{"/".join(email_domain.split(".")[-2:]) if "." in email_domain else email_domain}/email/routing

2. 点击 "Create custom address" 或 "Set up catch-all"

3. 配置:
   - Destination address: *@{email_domain}
   - Action: Send to worker
   - Worker: chatgpt-mail-worker

4. 确保域名的 DNS 已正确配置:
   - MX 记录: @{email_domain} → mailchannels.tx

5. 验证:
   curl https://{worker_domain}/api/mails
   # 应返回: {{"error":"unauthorized"}}
""")
    print("=" * 60)


def main():
    print("=" * 60)
    print("Cloudflare Worker 一键部署")
    print("=" * 60)

    # 切换到脚本所在目录
    os.chdir(Path(__file__).parent)

    # 检查依赖
    check_wrangler()

    # 登录
    wrangler_login()

    # 输入配置
    print("\n📋 配置信息:")
    email_domain = input_with_default("邮箱域名", "mail.example.com")
    admin_password = input_with_default("管理密码", "chatgpt2026")

    # 创建 KV
    kv_id = create_kv_namespace()
    if not kv_id:
        print("  ⚠️ 无法获取 KV ID，请手动检查")
        kv_id = input("  请输入 KV Namespace ID: ").strip()

    # 创建 wrangler.toml
    create_wrangler_toml(kv_id)

    # 设置 secrets
    set_secrets(email_domain, admin_password)

    # 部署
    deploy_worker()

    # 获取 worker domain
    print("\n🌐 获取 Worker URL...")
    result = run_cmd("wrangler subdomain", check=False)
    worker_domain = f"chatgpt-mail-worker.{result.strip() if result else 'workers.dev'}"

    # 尝试从部署输出获取
    deploy_result = run_cmd("wrangler deploy", check=False)
    for line in deploy_result.split("\n"):
        if "https://" in line and "workers.dev" in line:
            worker_domain = line.strip()
            break

    # 更新 config.json
    update_config_json(worker_domain, email_domain, admin_password)

    # 打印 Email Routing 说明
    print_email_routing_instructions(email_domain, worker_domain)

    print("\n✅ 部署完成!")
    print(f"\n下一步:")
    print(f"  1. 在 Cloudflare Dashboard 配置 Email Routing")
    print(f"  2. 运行: python chatgpt_register.py")


if __name__ == "__main__":
    main()
