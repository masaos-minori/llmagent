---
title: "Agent CLI and Commands - Migration Notes"
category: agent
tags:
  - agent
  - cli
  - migration
related:
  - 05_agent_00_document-guide.md
source:
  - 05_agent_07_07_cli-and-commands-migration-notes.md
---

# Agent CLI and Commands

- System Overview → [05_agent_01_system-overview.md](05_agent_01_system-overview.md)

## Purpose

Documents the mapping between deprecated slash commands and their current successors.

## Known Limitations

### `/note` Command Group (Removed)

`/note add <text>` / `/note list` / `/note delete <id>` have been removed. `cmd_notes.py`, `NoteRepository`, `auto_inject_notes`, and the `notes` table have been removed. Refer to the `/memory` command group as an alternative for long-term memory.

### `/ingest` Command (Removed)

`/ingest <url|path> [lang] [--snippets-only]` has been removed. `IngestWorkflowService` and associated DTOs/exceptions have been removed. For document ingestion, refer to the RAG pipeline mechanisms (`rag/`).

### `/debug audit` Subcommand (Removed)

`/debug audit` (displays end of audit.log) has been removed. Use the `/audit` command to reference audit logs. `/debug` explicitly rejects unknown subcommands.

### `/db` Command (Completely Removed)

`/db` is no longer recognized in any form and is treated as an unknown slash command. No backward compatibility is provided.

| Deprecated Format | Current State |
|---|---|
| `/db urls [--lang] [--limit]` | No successor (use MCP tools on the RAG pipeline side directly) |
| `/db clean <url>` | No successor |
| `/db rebuild-fts` | `/session rag-rebuild-fts` |
| `/db recover [backup-path]` | `/session recover [backup-path]` |
| `/db stats` | `/session stats` |
| `/db health` | `/session health` |
| `/db checkpoint [MODE]` | `/session checkpoint [MODE]` |
| `/db vacuum` | `/session vacuum` |
| `/db purge [--max-sessions N] [--max-age-days N]` | `/session purge [--max-sessions N] [--max-age-days N]` |
| `/db consistency` | `/session rag-consistency` |

## Related Docs

- `05_agent_00_document-guide.md`
- `05_agent_07_01_cli-and-commands-cli-reference.md`
- `05_agent_07_02_cli-and-commands-cliview.md`
- `05_agent_07_03_cli-and-commands-command-registry.md`
- `05_agent_07_04_cli-and-commands-purpose.md`
- `05_agent_07_05_cli-and-commands-repl-io.md`
- `05_agent_07_06_cli-and-commands-hot-reload.md`
- `05_agent_07_08_cli-and-commands-slash-commands-session-mcp.md`
- `05_agent_07_09_cli-and-commands-slash-commands-context-db.md`
- `05_agent_07_10_cli-and-commands-slash-commands-workflow-debug.md`
- `05_agent_07_11_cli-and-commands-slash-commands-memory-other.md`

## Keywords

migration notes
deprecated commands
