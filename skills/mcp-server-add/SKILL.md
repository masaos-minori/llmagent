---
name: mcp-server-add
description: |
  Use this skill PROACTIVELY when adding a new MCP (Model Context Protocol) server
  to this project. Use this when the task involves creating a new MCP server module,
  registering it as an OpenRC service, wiring it into the agent, or running
  /mcp install <name> from the agent REPL.
---

# MCP Server Add Skill

## Purpose

Add a new MCP server end-to-end: generate skeleton files, register the service,
wire the agent routing, and verify the server is reachable.

## Existing MCP servers (reference)

| Service name | Module | Port |
|---|---|---|
| `web-search-mcp` | `mcp/web_search/server.py` | 8004 |
| `file-read-mcp` | `mcp/file/read_server.py` | 8005 |
| `github-mcp` | `mcp/github/server.py` | 8006 |
| `file-write-mcp` | `mcp/file/write_server.py` | 8007 |
| `file-delete-mcp` | `mcp/file/delete_server.py` | 8008 |
| `shell-mcp` | `mcp/shell/server.py` | 8009 |
| `rag-pipeline-mcp` | `mcp/rag_pipeline/server.py` | 8010 |

New servers must use port ≥ 8011.

## Prerequisites

- For Option A (wizard): agent REPL must be running (`rc-service llama-agent status`)
- Next free port: `grep -r '\-\-port' init.d/ | grep -oP '\d{4,}' | sort -n | tail -1` → use next integer ≥ 8007

## Phase overview

| Phase | Steps | Goal |
|---|---|---|
| 1 Generate | Option A or B → Step 1 verify | Skeleton files exist and are valid |
| 2 Wire | Steps 2–4 | deploy.sh, service map, tool routing updated |
| 3 Run | Steps 5–8 | Service deployed, started, and reachable |

See `workflow.md` for detailed step content, failure recovery, and idempotency notes.

## Completion checklist

- `scripts/mcp/<name>/server.py` syntax check passes
- `deploy/deploy.sh` updated with new files
- `_MCP_SERVICE_MAP` in `agent/repl.py` updated (verified with `rg "_MCP_SERVICE_MAP"`)
- service registered and running (`rc-service <name> status`)
- `/mcp` in agent REPL shows the new server as healthy
- no errors in `agent.log` during tool invocation

## Composes with

- `deploy` — Step 5 delegates to deploy skill (Phase 2: code change deploy)

## Called by

- `python-issue-to-plan` — when a plan includes adding a new MCP server

## Prohibited behavior

- Do not reuse a port already assigned to an existing server
- Do not skip the `deploy/deploy.sh` update (new script will not be deployed)
- Do not skip the `_MCP_SERVICE_MAP` update (watchdog and health checks will miss the server)
- Do not use `json.load()` in the new server module
- Do not write log messages or comments in Japanese

## Improvement feedback

After running this skill, if the wizard generated invalid skeleton code or a step was missing:
update `workflow.md` with the recovery procedure and note which pattern changed.
