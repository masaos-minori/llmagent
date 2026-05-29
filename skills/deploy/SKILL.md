---
name: deploy
description: |
  Use this skill PROACTIVELY when deploying changes to the production environment,
  initializing the database, registering OpenRC services, or syncing scripts and
  configs to /opt/llm/. Use this when the task involves deploy.sh, init_db.sh,
  setup_services.sh, service restarts, or verifying that deployed files are current.
---

# Deploy Skill

## Purpose

Deploy code and config changes safely to `/opt/llm/` and manage OpenRC services
without disrupting the running agent or MCP servers.

## Environment facts

- Deploy target: `/opt/llm/`
- Python venv: `/opt/llm/venv/`
- Scripts live at: `/opt/llm/scripts/`
- Configs live at: `/opt/llm/config/`
- Logs live at: `/opt/llm/logs/`
- DB: SQLite at path in `config/common.toml`
- `sqlite-vec` extension: `/opt/llm/sqlite-vec/vec0.so`

For service names and ports: see `rules/env.md`.

## Deploy scripts

| Script | Purpose | When to run |
|---|---|---|
| `deploy/deploy.sh` | Copy `scripts/` and `config/` to `/opt/llm/` | Every code or config change |
| `deploy/init_db.sh` | Initialize SQLite schema via `create_schema.py` | First run only (idempotent but skip if DB exists) |
| `deploy/setup_services.sh` | Register and enable OpenRC services | First run only |

## Phase overview

| Phase | Goal | Gate |
|---|---|---|
| 1 Pre-deploy | Syntax check + deploy.sh copy list confirmation | `All scripts OK`; no missing files |
| 2 Deploy | Copy files to `/opt/llm/` | `bash deploy/deploy.sh` exits 0 |
| 3 Restart | Restart only affected services | `rc-service <name> status` shows running |
| 4 Verify | Log check + basic operation | No new errors in logs |

See `workflow.md` for detailed phase content including failure recovery procedures.

## Completion checklist

- syntax check passed before deploy
- `deploy/deploy.sh` ran successfully
- only affected services were restarted (apply agent restart decision criteria)
- all restarted services show running state
- no new errors in logs
- if agent was restarted: new REPL session verified with `/mcp`

## Composes with

- `mcp-server-add` — run this skill's Phase 2–3 after the mcp-server-add workflow completes
- `python-implementation` — run after Phase 11 (Production Readiness) if scripts changed
- `python-refactoring` — run after Phase 6 (CI Gate) if scripts/ files changed or removed

## Prohibited behavior

- Do not restart all services when only one is affected
- Do not run `deploy/init_db.sh` on a production DB with existing data without confirming idempotency
- Do not run `deploy/setup_services.sh` on a system where services are already registered without checking first
- Do not skip the pre-deploy syntax check
- Do not deploy with known syntax errors in `scripts/`
- Do not use `/reload` as a substitute for deploying changed files — `/reload` only re-reads config, it does not copy new code

## Improvement feedback

After running this skill, if any step lacked information or failed unexpectedly:
note what was missing and update `workflow.md` with the recovery procedure.
