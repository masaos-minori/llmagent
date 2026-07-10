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

| Service name | Module | Port |
|---|---|---|
| `web-search-mcp` | `mcp_servers/web_search/server.py` | 8004 |
| `file-read-mcp` | `mcp_servers/file/read_server.py` | 8005 |
| `github-mcp` | `mcp_servers/github/server.py` | 8006 |
| `file-write-mcp` | `mcp_servers/file/write_server.py` | 8007 |
| `file-delete-mcp` | `mcp_servers/file/delete_server.py` | 8008 |
| `shell-mcp` | `mcp_servers/shell/server.py` | 8009 |
| `rag-pipeline-mcp` | `mcp_servers/rag_pipeline/server.py` | 8010 |
| `cicd-mcp` | `mcp_servers/cicd/server.py` | 8012 |
| `mdq-mcp` | `mcp_servers/mdq/server.py` | 8013 |
| `git-mcp` | `mcp_servers/git/server.py` | 8014 |

New servers must use port ≥ 8015.

## Prerequisites

- For Option A (wizard): agent REPL must be running (`ps aux | grep agent.py`)
- Next free port: `grep -r '\-\-port' init.d/ | grep -oP '\d{4,}' | sort -n | tail -1` → use next integer (currently ≥ 8015; see server table above)

## Phase overview

| Phase | Steps | Goal |
|---|---|---|
| 1 Generate | Option A or B → Step 1 verify | Skeleton files exist and are valid |
| 2 Wire | Steps 2–4 | deploy.sh, service map, tool routing updated |
| 3 Run | Steps 5–8 | Service deployed, started, and reachable |

See `workflow.md` for detailed step content, failure recovery, and idempotency notes.

## Completion checklist

- `scripts/mcp_servers/<name>/server.py` syntax check passes
- `deploy/deploy.sh` updated with new files
- `config/agent.toml` section `[mcp_servers.<name>]` added (verified with `rg`)
- service running and reachable (verify port health)
- `/mcp` in agent REPL shows the new server as healthy
- no errors in `agent.log` during tool invocation
- MCP doc consistency check passes: `python tools/check_mcp_docs_consistency.py`

## Composes with

- `deploy` — Step 5 delegates to deploy skill (Phase 2: code change deploy)

## Called by

- `python-issue-to-plan` — when a plan includes adding a new MCP server

## Prohibited behavior

- Do not reuse a port already assigned to an existing server
- Do not skip the `deploy/deploy.sh` update (new script will not be deployed)
- Do not skip the `config/agent.toml [mcp_servers.<name>]` section (agent will not route tools to the server)
- Do not use `json.load()` in the new server module

See also `rules/coding.md` for project-wide coding prohibitions.

## Improvement feedback

After running this skill, if the wizard generated invalid skeleton code or a step was missing:
update `workflow.md` with the recovery procedure and note which pattern changed.
