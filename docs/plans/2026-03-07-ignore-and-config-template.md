# Ignore and Config Template Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a safe repository ignore policy and a shareable config template without committing local registration outputs or secrets.

**Architecture:** Add a root `.gitignore` that excludes local runtime artifacts and sensitive local configuration, then add a `config.example.json` file that mirrors the live config shape with placeholder values. This avoids changing runtime behavior while making setup reproducible.

**Tech Stack:** Git ignore rules, JSON configuration, Python project layout

---

### Task 1: Add repository ignore rules

**Files:**
- Create: `.gitignore`

**Step 1: Write the failing test**

Manual expectation: the repository currently has no root `.gitignore`, so local registration outputs and secrets are not explicitly ignored.

**Step 2: Run test to verify it fails**

Run: `test -f .gitignore && echo exists || echo missing`
Expected: `missing`

**Step 3: Write minimal implementation**

Create `.gitignore` with entries for:
```gitignore
config.json
registered_accounts.txt
ak.txt
rk.txt
codex_tokens/
__pycache__/
*.py[cod]
.python-version
.DS_Store
```

**Step 4: Run test to verify it passes**

Run: `python - <<'PY'
from pathlib import Path
content = Path('.gitignore').read_text()
for item in ['config.json', 'registered_accounts.txt', 'ak.txt', 'rk.txt', 'codex_tokens/']:
    assert item in content, item
print('ok')
PY`
Expected: `ok`

**Step 5: Commit**

```bash
git add .gitignore
git commit -m "chore: ignore local registration artifacts"
```

### Task 2: Add safe config template

**Files:**
- Create: `config.example.json`
- Reference: `config.json`

**Step 1: Write the failing test**

Manual expectation: there is no checked-in safe example config file for onboarding.

**Step 2: Run test to verify it fails**

Run: `test -f config.example.json && echo exists || echo missing`
Expected: `missing`

**Step 3: Write minimal implementation**

Create `config.example.json` using the same keys as `config.json`, but replace local secrets and identifiers with placeholders:
```json
{
  "_comment": "ChatGPT 批量注册 - 支持 DuckMail / CF Worker 邮箱",
  "mail_provider": "cfworker",
  "total_accounts": 5,
  "duckmail_api_base": "https://api.duckmail.sbs",
  "duckmail_bearer": "your_duckmail_api_token",
  "cf_worker_domain": "your-worker.your-subdomain.workers.dev",
  "cf_email_domain": "mail.example.com",
  "cf_admin_password": "your_admin_password",
  "proxy": "",
  "output_file": "registered_accounts.txt",
  "enable_oauth": true,
  "oauth_required": true,
  "oauth_issuer": "https://auth.openai.com",
  "oauth_client_id": "app_EMoamEEZ73f0CkXaXp7hrann",
  "oauth_redirect_uri": "http://localhost:1455/auth/callback",
  "ak_file": "ak.txt",
  "rk_file": "rk.txt",
  "token_json_dir": "codex_tokens",
  "upload_api_url": "http://localhost:8317/v0/management/auth-files",
  "upload_api_token": "your_cpa_panel_password"
}
```

**Step 4: Run test to verify it passes**

Run: `python - <<'PY'
import json
from pathlib import Path
example = json.loads(Path('config.example.json').read_text())
live = json.loads(Path('config.json').read_text())
assert set(example) == set(live)
assert example['cf_admin_password'] != live['cf_admin_password']
print('ok')
PY`
Expected: `ok`

**Step 5: Commit**

```bash
git add config.example.json
git commit -m "chore: add safe config template"
```
