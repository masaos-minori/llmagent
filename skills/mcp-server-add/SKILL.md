---
name: mcp-server-add
description: |
 Use this skill PROACTIVELY when adding a new MCP (Model Context Protocol) server
   to this project. Use this when the task involves creating a new MCP server module,
   wiring it into the agent, or running
   /mcp install <name> from the agent REPL.
---

# MCP Server Add Skill

## Purpose

Add a new MCP server end-to-end: skeleton files, service registration, agent routing, reachability verification.

## Existing MCP servers (reference)

Port/role table (canonical): `docs/04_mcp_01_system_overview.md` Server Catalog.
Module paths follow the pattern `mcp_servers/<name>/server.py` (e.g. `mcp_servers/web_search/server.py`).

New servers must use the next free port above every port currently assigned — never hardcode
a specific number here; derive it at task time (see Prerequisites).

## Prerequisites

- For Option A (wizard): agent REPL must be running (`ps aux | grep agent.py`)
- Next free port: `grep -r '\-\-port' init.d/ | grep -oP '\d{4,}' | sort -n | tail -1` → use the next integer above that result

## Phase overview

| Phase | Steps | Goal |
|---|---|---|
| 1 Generate | Option A or B → Step 1 verify | Skeleton files exist and are valid |
| 2 Wire | Steps 2–4 | deploy.sh, service map, tool routing updated |
| 3 Run | Steps 5–8 | Service deployed, started, and reachable |

See `workflow.md` for detailed step content, failure recovery, and idempotency notes.

## Completion checklist

- `scripts/mcp_servers/<name>/server.py` syntax check passes
- `deploy/deploy.sh` updated with a `cp` line for the new server's `config/<name>_mcp_server.toml` (the server's Python files need no `deploy.sh` change — `scripts/` is rsynced wholesale)
- `config/agent.toml` section `[mcp_servers.<name>]` added (verified with `rg`)
- service running and reachable (verify port health)
- `/mcp` in agent REPL shows the new server as healthy
- no errors in `agent.log` during tool invocation
- MCP doc consistency check passes: `uv run python tools/check_docs_consistency.py --domain mcp` (see `routing.md` Tools → "When to run which tool")

## Composes with

- `deploy` — Step 5 delegates to deploy skill (Phase 2: code change deploy)

## Called by

- `require-to-plan` — when a plan includes adding a new MCP server

## Prohibited behavior

- Do not reuse a port already assigned to an existing server
- Do not skip the `deploy/deploy.sh` `cp` line for the new `config/<name>_mcp_server.toml` (the config file will not be deployed otherwise)
- Do not skip the `config/agent.toml [mcp_servers.<name>]` section (agent will not route tools to the server)
- Do not use `json.load()` in the new server module

See also `rules/coding.md` for project-wide coding prohibitions.

## Improvement feedback

After running this skill, if the wizard generated invalid skeleton code or a step was missing:
update `workflow.md` with the recovery procedure and note which pattern changed.
