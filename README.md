# ChatGPT 批量自动注册工具

> 使用 DuckMail 或 Cloudflare Worker 临时邮箱，并发自动注册 ChatGPT 账号

## 功能

- 📨 自动创建临时邮箱 (DuckMail / Cloudflare Worker)
- 📥 自动获取 OTP 验证码
- ⚡ 支持并发注册多个账号
- 🔄 自动处理 OAuth 登录
- ☁️ 支持代理配置
- 📤 支持上传账号到 Codex / CPA 面板

## 环境依赖

```bash
pip install curl_cffi
npm install -g wrangler  # Cloudflare Worker 部署需要
```

## 快速开始

```bash
# 复制配置模板
cp config.example.json config.json

# 编辑配置
vim config.json

# 运行注册
python chatgpt_register.py
```

---

## 方式一：DuckMail 临时邮箱

### 1. 获取 API Token

1. 访问 [DuckMail](https://duckmail.sbs) 注册账号
2. 在控制台获取 API Token

### 2. 配置 config.json

```json
{
    "mail_provider": "duckmail",
    "total_accounts": 5,
    "duckmail_api_base": "https://api.duckmail.sbs",
    "duckmail_bearer": "你的_DuckMail_API_Token",
    "proxy": "http://127.0.0.1:7890",
    "output_file": "registered_accounts.txt"
}
```

### 3. 运行

```bash
python chatgpt_register.py
```

---

## 方式二：Cloudflare Worker 邮箱

### 架构说明

```
ChatGPT 注册流程:
1. Cloudflare Worker 创建随机邮箱地址 (random@your-domain.com)
2. 注册时使用该邮箱
3. Cloudflare Email Routing 收到邮件转发到 Worker
4. Worker 存储邮件到 KV 并提供 API
5. 程序通过 Worker API 获取 OTP 验证码
```

### 1. 前置要求

- Cloudflare 账号
- 已添加的域名 (需设置 DNS)
- 安装 wrangler: `npm install -g wrangler`

### 2. 一键部署 (推荐)

```bash
# 交互式配置，会询问:
# - Cloudflare API Token
# - 邮箱域名 (如 mail.example.com)
# - 管理密码
python setup_cloudflare.py
```

或手动执行以下步骤...

### 3. 手动部署步骤

#### 3.1 获取 Cloudflare API Token

1. 登录 [Cloudflare Dashboard](https://dash.cloudflare.com)
2. 进入 **API** → **My Profile** → **API Tokens**
3. 点击 **Create Token**
4. 使用 **Edit Cloudflare Workers** 模板，权限如下:
   - `Workers AI: Edit`
   - `Workers KV: Edit` (如果使用 KV)
   - `Zone: Read` (如果需要读取域名)
5. 复制生成的 Token

#### 3.2 创建 KV Namespace

```bash
wrangler login
wrangler kv:namespace create MAIL_KV
```

输出类似:
```
ℹ️  Using namespace title "MAIL_KV"
🌀  Creating namespace...
✨  Success!
Add the following to your wrangler.toml:
id = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
```

#### 3.3 配置 wrangler.toml

在项目根目录创建 `wrangler.toml`:

```toml
name = "chatgpt-mail-worker"
main = "cf-worker/worker.js"
compatibility_date = "2024-01-01"

[[kv_namespaces]]
binding = "MAIL_KV"
id = "你的_KV_Namespace_ID"
```

#### 3.4 部署 Worker

```bash
# 设置环境变量
wrangler secret put ADMIN_PASSWORD
# 输入你的管理密码

wrangler secret put JWT_SECRET
# 输入随机字符串 (用于 JWT 签名)

wrangler secret put EMAIL_DOMAIN
# 输入你的邮箱域名 (如 mail.example.com)

# 部署
wrangler deploy
```

#### 3.5 配置 Email Routing

1. 进入 Cloudflare Dashboard → **Email** → **Email Routing**
2. 点击 **Create custom address** 或 **Set up catch-all**
3. 设置:
   - **Catch-all address**: `*@your-domain.com`
   - **Destination**: 选择刚部署的 Worker
4. 确保域名的 DNS 已经正确配置 (MX 记录)

#### 3.6 配置 config.json

```json
{
    "mail_provider": "cfworker",
    "total_accounts": 5,

    "cf_worker_domain": "your-worker.your-subdomain.workers.dev",
    "cf_email_domain": "mail.example.com",
    "cf_admin_password": "your_admin_password",

    "proxy": "http://127.0.0.1:7890",
    "output_file": "registered_accounts.txt"
}
```

| 配置项 | 说明 |
|--------|------|
| `cf_worker_domain` | Cloudflare Worker 部署后的 URL |
| `cf_email_domain` | 你的邮箱域名 (如 mail.example.com) |
| `cf_admin_password` | 部署时设置的 ADMIN_PASSWORD |

### 4. 验证

```bash
# 测试 Worker 是否正常
curl https://your-worker.xxx.workers.dev/api/mails

# 应该返回: {"error":"unauthorized"} (表示 Worker 正常运行)
```

---

## OAuth 配置 (可选)

注册后自动登录获取 Access Token:

```json
{
    "enable_oauth": true,
    "oauth_required": true,
    "oauth_issuer": "https://auth.openai.com",
    "oauth_client_id": "app_EMoamEEZ73f0CkXaXp7hrann",
    "oauth_redirect_uri": "http://localhost:1455/auth/callback",
    "ak_file": "ak.txt",
    "rk_file": "rk.txt",
    "token_json_dir": "codex_tokens"
}
```

---

## CPA 面板集成 (可选)

注册成功后自动上传账号:

```json
{
    "upload_api_url": "http://localhost:8317/v0/management/auth-files",
    "upload_api_token": "your_cpa_panel_password"
}
```

---

## 完整配置示例

```json
{
    "mail_provider": "cfworker",

    "total_accounts": 5,

    "duckmail_api_base": "https://api.duckmail.sbs",
    "duckmail_bearer": "your_duckmail_api_token",

    "cf_worker_domain": "your-worker.your-subdomain.workers.dev",
    "cf_email_domain": "mail.example.com",
    "cf_admin_password": "your_admin_password",

    "proxy": "http://127.0.0.1:7890",

    "output_file": "registered_accounts.txt",
    "enable_oauth": true,
    "oauth_required": true,
    "oauth_issuer": "https://auth.openai.com",
    "oauth_client_id": "app_EMoamEEZ73f0CkXaXp7hrann",
    "oauth_redirect_uri": "http://localhost:1455/auth/callback",
    "ak_file": "ak.txt",
    "rk_file": "rk.txt",
    "token_json_dir": "codex_tokens",
    "upload_api_url": "",
    "upload_api_token": ""
}
```

---

## 目录结构

```
chatgpt_register/
├── chatgpt_register.py      # 主程序
├── config.example.json       # 配置模板
├── config.json               # 配置文件 (需创建)
├── setup_cloudflare.py       # Cloudflare 一键部署脚本
├── wrangler.toml             # Cloudflare Workers 配置
├── cf-worker/
│   └── worker.js             # Cloudflare Worker 代码
├── codex/
│   ├── config.json
│   └── protocol_keygen.py    # Codex 协议密钥生成
├── registered_accounts.txt  # 输出的账号
├── ak.txt                    # Access Keys
├── rk.txt                    # Refresh Keys
└── codex_tokens/             # Codex Token JSON 文件
```

---

## 常见问题

### DuckMail

- **注册失败**: 检查 API Token 是否正确，是否有足够的余额
- **收不到验证码**: DuckMail 可能有延迟，稍等片刻

### Cloudflare Worker

- **部署失败**: 检查 `wrangler.toml` 配置，确保已执行 `wrangler login`
- **收不到邮件**: 检查 Email Routing 是否正确配置，域名 DNS 的 MX 记录
- **API 返回 401**: 检查 `ADMIN_PASSWORD` 和 `cf_admin_password` 是否一致

---

## 更新日志

- 2026-03-08: 添加 Cloudflare Worker 邮箱支持，添加一键部署脚本
- 2026-03-07: 优化 OAuth 登录流程
