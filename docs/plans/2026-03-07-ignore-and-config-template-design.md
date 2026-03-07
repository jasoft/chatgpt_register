# Ignore and Config Template Design

## Goal
Prevent accidental commits of local registration outputs, tokens, and real configuration while preserving an easy onboarding path for local setup.

## Scope
- Add a repository-level `.gitignore`.
- Add `config.example.json` as a safe template.
- Do not modify runtime behavior.

## Chosen Approach
Use a committed `config.example.json` plus a local-only `config.json`, and ignore generated registration artifacts and Python cache files.

## Why
This keeps sensitive local values out of git while preserving the current configuration shape for users who need to copy and edit a template.

## Files
- `.gitignore`
- `config.example.json`

## Ignore Rules
Ignore files and directories that can contain local registration state or secrets:
- `config.json`
- `registered_accounts.txt`
- `ak.txt`
- `rk.txt`
- `codex_tokens/`
- Python cache artifacts

## Example Config Structure
`config.example.json` should mirror the current `config.json` keys so users can copy it directly. Sensitive values should be replaced with placeholders or empty strings.

## Verification
- Confirm `.gitignore` exists and contains the expected entries.
- Confirm `config.example.json` exists and does not contain real local secrets.
