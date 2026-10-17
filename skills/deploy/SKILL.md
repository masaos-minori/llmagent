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

Environment details (paths, service names, ports): see `rules/env.md`.

## Deploy scripts

| Script | Purpose | When to run |
|---|---|---|
| `deploy/deploy.sh` | Copy `scripts/` and `config/` to `/opt/llm/` | Every code or config change |
| `deploy/init_db.sh` | Initialize SQLite schema via `create_schema.py` | First run only (idempotent but skip if DB exists) |
| `deploy/setup_services.sh` | Start services (subprocess management) | First run only |
| `deploy/build_binaries.sh` | Build the 11 Nuitka `--onefile` binaries into `/opt/llm/bin/` | Once per release, on the build host |

## Binary layout

Compiled artifacts under `/opt/llm/`:

- `/opt/llm/bin/`: the 11 Nuitka `--onefile` binaries (`agent` plus one `mcp_<server>` per MCP server). It MUST NOT be group/world-writable; the CommandValidator rejects binaries under a writable directory.
- `/opt/llm/dict/system.dic`: external Sudachi dictionary (built by `deploy/build_binaries.sh`, placed by `deploy/deploy.sh`).
- `config/`: stays external (copied by `deploy/deploy.sh`).

The agent binary resolves these via:

- `LLMAGENT_CONFIG_DIR=/opt/llm/config`
- `LLMAGENT_SUDACHI_DICT=/opt/llm/dict/system.dic`

`deploy/start_agent.sh` exports both before launch. A missing config directory or dictionary fails startup with an explicit error naming the path.

## Phase overview

| Phase | Goal | Gate |
|---|---|---|
| 1 Pre-deploy | Syntax check + deploy.sh copy list confirmation | `compileall` reports no `SyntaxError`, `check_db_separation.py` exits 0, copy-list diff empty (`workflow.md` Phase 1 Completed when) |
| 2 Deploy | Copy files to `/opt/llm/` | `bash deploy/deploy.sh` exits 0 |
| 3 Restart | Restart only affected services | Port health check returns OK |
| 4 Verify | Log check + basic operation | No new errors in logs |

See `workflow.md` for phase details and failure recovery.

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
  `docs/23_agent/agent_08_01_configuration-loading-agent-config.md`'s hot-reload table for the
  agent). For an MCP server: if `ConfigLoader().load(...)` is called at module
  import / `__init__` time, the field is startup-only and requires Phase 3; if it is called
  inside a request handler, `/reload` suffices and Phase 3 may be skipped.
- **Rollback**: `deploy/deploy.sh` only copies files; roll back by re-running the skill with the previous commit checked out (`git checkout <prev-sha>` then Phase 2 onward). Service state is not rolled back automatically. See `AGENTS.md` Loop Prevention > Rollback Directive — if the same failure recurs after rollback, stop and report it rather than deploying forward again on the assumption the rollback fixed it. Reverting `config/agent.toml` to its `uv run` `cmd` entries and redeploying restores the `uv run` launch path; `scripts/` stays deployed so that path keeps working after the revert.

## Required behavior

- Restart only the services selected by Phase 3 Step 3a decision criteria; never restart a service the criteria did not select.
- Before running `deploy/init_db.sh` on a production DB, confirm idempotency by checking
  whether the target tables already exist (see `deploy/init_db.sh`'s own `IF NOT EXISTS` guards).
- Before running `deploy/setup_services.sh`, check whether its services are
  already registered (`curl` each health endpoint per `rules/env.md`); run it only when at
  least one target service is not already running.
- Run the Phase 1 pre-deploy syntax check before every deploy; if it reports a `SyntaxError`,
  fix it and re-run the check before proceeding to Phase 2.
- Use `/reload` only for hot-reloadable config fields (see Phase 3 Step 3a); use a full
  deploy (Phase 2 onward) whenever `scripts/` files changed, since `/reload` never copies code.

## Improvement feedback

After running this skill, if any step lacked information or failed unexpectedly:
note what was missing and update `workflow.md` with the recovery procedure.
