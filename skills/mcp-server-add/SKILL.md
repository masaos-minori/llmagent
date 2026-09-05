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

New servers must use the next free port above every port currently assigned — derive it at
task time (see Prerequisites), per `skills/DESIGN.md` No concrete configuration values.
Do not state the assigned port number in `docs/*.md` once it is deployed — see
`skills/DESIGN.md` Docs content policy — remove.

## Prerequisites

- For Option A (wizard): agent REPL must be running (`ps aux | grep agent.py`)
- Next free port: `grep -r '\-\-port' init.d/ | grep -oP '\d{4,}' | sort -n | tail -1` → use the next integer above that result

## Phase overview

| Phase | Steps | Goal | Gate |
|---|---|---|---|
| 1 Generate | Option A or B → Step 1 verify | Skeleton files exist and are valid | Step 1's structure checklist fully passes |
| 2 Wire | Steps 2–4 | deploy.sh, service map, tool routing updated | `rg` confirms the new `cp` line, `[mcp_servers.<name>]` section, and (if needed) `tool_names` entry all exist |
| 3 Run | Steps 5–8 | Service deployed, started, and reachable | `/mcp` in agent REPL shows the new server healthy |

See `workflow.md` for detailed step content, failure recovery, and idempotency notes.

## Completion checklist

- `scripts/mcp_servers/<name>/server.py` syntax check passes
- `deploy/deploy.sh` updated with a `cp` line for the new server's `config/<name>_mcp_server.toml` (see `workflow.md` Step 2 for why)
- `config/agent.toml` section `[mcp_servers.<name>]` added (verified with `rg`)
- service running and reachable (verify port health)
- `/mcp` in agent REPL shows the new server as healthy
- no errors in `agent.log` during tool invocation
- MCP doc consistency check passes: `uv run python tools/check_docs_consistency.py --domain mcp` (see `routing.md` Tools → "When to run which tool")

## Composes with

- `deploy` — Step 5 delegates to deploy skill (Phase 2: code change deploy)

## Called by

- `issue-to-plan` — when a plan includes adding a new MCP server

## Required behavior

- Use the port computed in Prerequisites, and re-run its `grep` command immediately before
  assigning it — a server added by another change since this task started may have taken it.
- Use `ConfigLoader().load(...)` to read the new server's config module, per `workflow.md`
  Step 1's structure check (a specific instance of `rules/coding.md`'s general
  `config_loader.py`-only `json.load()` rule — see Constraint checks).

See `rules/coding.md` Mandatory conventions ("Module addition", "MCP server addition"
rows) for the `deploy/deploy.sh` `cp` line and `config/agent.toml
[mcp_servers.<name>]` section requirements — not repeated here.

## Improvement feedback

After running this skill, if the wizard generated invalid skeleton code or a step was missing:
update `workflow.md` with the recovery procedure and note which pattern changed.
