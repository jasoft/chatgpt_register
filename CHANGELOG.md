# Changelog

## [0.2.0] - 2026-03-07

### Added
- 支持 Cloudflare Worker 邮箱提供商（`mail_provider: "cfworker"`）
- 新增 `cf-worker/worker.js`：基于 Cloudflare Email Routing catch-all 的邮件收取 Worker
- Worker 支持 KV 存储邮件（24h TTL）、JWT 鉴权、管理接口
- `config.json` 新增 `mail_provider`、`cf_worker_domain`、`cf_email_domain`、`cf_admin_password` 配置项
- `chatgpt_register.py` 新增 CF Worker 邮箱创建、邮件获取、验证码提取方法

### Changed
- 邮箱方法重构为 provider 分发模式，`create_temp_email` / `_fetch_emails` / `wait_for_verification_email` 根据 `mail_provider` 自动路由
- `run_batch` 和 `main` 入口函数适配多邮箱提供商，按 provider 检查配置
- DuckMail 逻辑完整保留，不影响原有功能

## [0.1.0] - 2026-03-06

### Added
- ChatGPT 批量自动注册工具初始版本
- DuckMail 临时邮箱集成
- 纯 HTTP 实现完整注册流程
- Sentinel Token PoW 反机器人验证
- PKCE OAuth 2.0 授权码流程
- CPA 面板自动上传
- Codex 协议密钥生成工具

