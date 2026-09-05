---
name: deploy
description: |
Use this skill PROACTIVELY when deploying changes to the production environment,
   initializing the database, or syncing scripts and
   configs to /opt/llm/. Use this when the task involves deploy.sh, init_db.sh,
   setup_services.sh, service restarts, or verifying that deployed files are current.
---

# Deploy Skill

## Purpose

Deploy code and config changes safely to `/opt/llm/`; manage services without disrupting the running agent or MCP servers.

For environment details (paths, service names, ports): see `rules/env.md`.

## Deploy scripts

| Script | Purpose | When to run |
|---|---|---|
| `deploy/deploy.sh` | Copy `scripts/` and `config/` to `/opt/llm/` | Every code or config change |
| `deploy/init_db.sh` | Initialize SQLite schema via `create_schema.py` | First run only (idempotent but skip if DB exists) |
| `deploy/setup_services.sh` | Start services (subprocess management) | First run only |

## Phase overview

| Phase | Goal | Gate |
|---|---|---|
| 1 Pre-deploy | Syntax check + deploy.sh copy list confirmation | `All scripts OK`; no missing files |
| 2 Deploy | Copy files to `/opt/llm/` | `bash deploy/deploy.sh` exits 0 |
| 3 Restart | Restart only affected services | Port health check returns OK |
| 4 Verify | Log check + basic operation | No new errors in logs |

See `workflow.md` for detailed phase content including failure recovery procedures.

## Completion checklist

- syntax check passed before deploy
- `deploy/deploy.sh` ran successfully
- only affected services were restarted (apply `workflow.md` Phase 3 Step 3a decision criteria)
- all restarted services show running state
- no new errors in logs
- if agent was restarted: new REPL session verified with `/mcp`

## Composes with

- `mcp-server-add` — run this skill's Phase 2–3 after the mcp-server-add workflow completes
- `python-implementation` — run after Phase 11 (Production Readiness) if scripts changed
- `python-refactoring` — run after Step 9 (CI gate) if scripts/ files changed or removed

## Scope notes

- **Config-only change** (no `scripts/` change): Phase 3 (Restart) may be skipped only if the
  changed field appears in the affected service's `/reload`-eligible field list (see
  `docs/05_agent_08_01_configuration-loading-agent-config.md`'s hot-reload table for the
  agent; for an MCP server, check whether `ConfigLoader().load(...)` is called at module
  import / `__init__` time — if so, it is startup-only and requires Phase 3; if it is called
  inside a request handler, `/reload` suffices and Phase 3 may be skipped).
- **Rollback**: `deploy/deploy.sh` only copies files; rollback by re-running the skill with the previous commit checked out (`git checkout <prev-sha>` then Phase 2 onward). Service state is not rolled back automatically.

## Required behavior

- Restart only the services identified by Phase 3's Agent restart decision criteria — never
  restart a service the criteria did not select for the current change.
- Before running `deploy/init_db.sh` on a production DB, confirm idempotency by checking
  whether the target tables already exist (see Phase overview Gate for Phase 1 and
  `deploy/init_db.sh`'s own `IF NOT EXISTS` guards).
- Before running `deploy/setup_services.sh`, check whether the services it starts are
  already registered (`curl` each health endpoint per `rules/env.md`) — run it only when at
  least one target service is not already running.
- Run the Phase 1 pre-deploy syntax check before every deploy; if it reports a `SyntaxError`,
  fix the error and re-run the check before proceeding to Phase 2.
- Use `/reload` only for hot-reloadable config fields (see Phase 3 Agent restart decision
  criteria); use a full deploy (Phase 2 onward) whenever `scripts/` files changed, since
  `/reload` never copies code.

## Improvement feedback

After running this skill, if any step lacked information or failed unexpectedly:
note what was missing and update `workflow.md` with the recovery procedure.
