---
title: "Agent CLI and Commands"
category: agent
tags:
  - agent
  - agent
  - cli
  - commands
  - repl
  - slash-commands
related:
  - 05_agent_00_document-guide.md
---

# Agent CLI and Commands

### Context category

| Command | Side effects | Related state |
|---|---|---|
| `/context` | None | Display history size, budget, system prompt, workflow mode, approval-pending state |
| `/compact` | LLM call (compression) | Compresses history immediately |
| `/system [name]` | Updates `history[0]` | `ctx.conv.system_prompt_name` |

### DB category

#### `/db rag` subcommands

| Command | Side effects | Notes |
|---|---|---|
| `/db rag stats` | None | Document/chunk counts (RAG only) |
| `/db rag urls [--lang] [--limit]` | None | List documents via rag-pipeline-mcp |
| `/db rag clean <url>` | Delete document + chunks via rag-pipeline-mcp | Cascaded delete |
| `/db rag rebuild-fts` | Rebuilds `chunks_fts` index | FTS5 rebuild |
| `/db rag vec-rebuild` | None | Rebuild vector index |
| `/db rag reconcile-url <url>` | None | Rebuild FTS/vec for a single URL |
| `/db rag recover [backup-path]` | Integrity check; restore from backup if corrupt | RAG only |
| `/db rag consistency` | None | Chunks/FTS/vector index sync check |

#### `/db session` subcommands

| Command | Side effects | Notes |
|---|---|---|
| `/db session stats` | None | Session/message counts |
| `/db session health` | None | journal_mode / integrity / page stats |
| `/db session checkpoint [MODE]` | WAL checkpoint | Flush WAL to main DB |
| `/db session vacuum` | VACUUM | Recover free pages |
| `/db session purge [--max-sessions N] [--max-age-days N]` | DELETE old sessions | Based on count or age |
| `/db session recover [backup-path]` | Integrity check; restore from backup if corrupt | Session only |

> **Note:** `/db rag urls` and `/db rag clean` call rag-pipeline-mcp MCP tools (`rag_list_documents`, `rag_delete_document`) via the agent's tool executor. RAG maintenance commands use `RagMaintenanceService`; session maintenance commands use `DbMaintenanceService`. `session.sqlite` and `workflow.sqlite` are accessed via `SQLiteHelper(target=...)` in code, not through `/db` commands. Schema details: `90_shared_04`.

### Plan category

| Command | Side effects | Related state |
|---|---|---|
| `/plan` | None | Toggle `ctx.conv.plan_mode` |

## Related Documents

- `agent`
- `cli`
- `commands`

## Keywords

agent
cli
commands
repl
slash-commands
