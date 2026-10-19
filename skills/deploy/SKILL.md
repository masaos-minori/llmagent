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
| `deploy/setup_services.sh` | Check the remote LLM health and start the Event Bus (MCP servers are started by the agent) | First run only |
| `deploy/build_binaries.sh` | Build the Nuitka `--onefile` binaries (all 11, or `BUILD_ONLY`) into a staging directory, swap them into `/opt/llm/bin/` after all pass, and keep the previous set (`--rollback` restores it) | Whenever a binary is stale (Phase 1b), on the build host |
| `tools/manage_binaries.py` | Build info, freshness check, staged swap, rollback, and deployed-revision record for the binaries (called by the two scripts above) | Run `check` before every deploy |

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
| 1 Pre-deploy | Syntax check + deploy.sh config/binary list confirmation + binary freshness report | `compileall` reports no `SyntaxError`, `check_db_separation.py` exits 0, config and binary list diffs empty or explained (`workflow.md` Phase 1 Completed when) |
| 1b Build | Rebuild the binaries the freshness report lists as stale or unknown | `tools/manage_binaries.py check` lists no stale or unknown binary (`workflow.md` Phase 1b Completed when) |
| 2 Deploy | Copy files to `/opt/llm/` | `bash deploy/deploy.sh` exits 0 |
| 3 Restart | Restart only affected services | Port health check returns OK |
| 4 Verify | Log check + basic operation | No new errors in logs |

See `workflow.md` for phase details and failure recovery.

## Completion checklist

- syntax check passed before deploy
- the binary freshness report was read and every stale or unknown binary was rebuilt (Phase 1b)
- `deploy/deploy.sh` ran successfully and wrote `/opt/llm/DEPLOYED_REV`
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
- **Rollback**: restore the previous binary set with `bash deploy/build_binaries.sh --rollback` (it needs no Nuitka and restores the set saved by the last swap). Components that run from the deployed source (Event Bus, ingestion, workflow validation) are rolled back by re-running the deploy from the previous commit (`git checkout <prev-sha>` then Phase 2 onward). Service state is not rolled back automatically. See `AGENTS.md` Loop Prevention > Rollback Directive — if the same failure recurs after rollback, stop and report it rather than deploying forward again on the assumption the rollback fixed it. Only MCP servers can be launched through the `cmd` entries of `config/agent.toml`; the agent always starts as `/opt/llm/bin/agent` (see `deploy/start_agent.sh`), so reverting `cmd` entries does not change how the agent is launched.

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
  deploy (Phase 1b onward) whenever `scripts/` files changed, since `/reload` never copies code.
- A change under `scripts/` reaches the agent and the MCP servers only after their binaries are rebuilt: `deploy/deploy.sh` alone never delivers it. Run `tools/manage_binaries.py check` and rebuild the stale ones. The Event Bus, ingestion, `init_db.sh`, and the workflow validation run from the deployed source and need a process restart instead.

## Improvement feedback

After running this skill, if any step lacked information or failed unexpectedly:
note what was missing and update `workflow.md` with the recovery procedure.
