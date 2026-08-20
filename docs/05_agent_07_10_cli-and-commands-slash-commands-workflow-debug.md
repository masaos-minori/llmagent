---
title: "Agent CLI and Commands - Slash Commands: Workflow, Debug/Audit, Compact/Export"
category: agent
tags:
  - agent
  - cli
  - slash-commands
related:
  - 05_agent_00_document-guide.md
source:
  - 05_agent_07_10_cli-and-commands-slash-commands-workflow-debug.md
---

# Agent CLI and Commands

- System Overview → [05_agent_01_system-overview.md](05_agent_01_system-overview.md)

## Purpose

Documents the purpose and side effects of slash commands in the Workflow, Debug/Audit, Git/Diff, and Compact/Export categories.

## Design Intent

### Workflow Category

A group of commands regarding **post-execution approval gates**.

| Command | Side Effect | Related State |
|---|---|---|
| `/approve <approval_id> [reason]` | Resolves a pending post-execution approval as "approved" | `approval_id` is a required argument — omitting it causes a validation error (no DB lookup fallback exists) |
| `/reject <approval_id> [reason]` | Resolves a pending post-execution approval as "rejected" | `approval_id` is a required argument — omitting it causes a validation error (no DB lookup fallback exists) |

> **Scope:** `/approve` and `/reject` resolve **only post-execution approval gates** (`approvals` DB records). They do not affect **pre-execution approvals** (real-time tool-level approval prompts). For the formal approval model, see [Tool Execution and Approval](05_agent_06_01_tool-execution-and-approval-execution.md).

#### Recovery on Startup

If the agent restarts with post-execution approvals pending, those pending states are automatically detected from the `approvals` database table at startup by `StateStore.find_latest_pending_approval()`.

**Cross-session guarantee:** Even if `ctx.turn.pending_approval_id` in memory is `None` (e.g., after a crash), `/approve` and `/reject` will resolve the latest pending approval from the `approvals` DB table.

**Overwrite Warning:** If `/approve` sets a new value while `ctx.turn.pending_approval_task_id` already contains a value, a `WARNING` level log is emitted to the `cmd_workflow.py` logger. This is a known design constraint due to the current lack of a queue that uses only a single field for handoff; the warning is for observability so operators can track missed approvals.

### Debug / Audit Category

A group of commands related to debugging and audit logs.

### Git/Diff Category

`/diff` only sees tool calls remaining in the current session's `ctx.conv.history`. If `/compact` or `/clear` is executed during a session, files written/edited prior to those operations fall outside the scope of `/diff` (a design trade-off; no DB-based change tracking is performed).

### Compact / Export Category

RAG search is not provided as a slash command — it is automatically called by the LLM as the `rag_run_pipeline` tool during normal conversation (via MCP). There is no dedicated slash command for direct user invocation.

## Responsibility Boundary

- **Workflow**: Post-execution approval gate management
- **Debug/Audit**: Debug mode and audit logs
- **Git/Diff**: Displaying file changes within a session
- **Compact/Export**: History compression and export

## Key Constraints

- Unknown

## Operational Notes

- Unknown

## Known Limitations

- `/diff` only sees tool calls remaining in the current session's `ctx.conv.history`

## Related Docs

- `05_agent_00_document-guide.md`
- `05_agent_07_01_cli-and-commands-cli-reference.md`
- `05_agent_07_02_cli-and-commands-cliview.md`
- `05_agent_07_03_cli-and-commands-command-registry.md`
- `05_agent_07_04_cli-and-commands-purpose.md`
- `05_agent_07_05_cli-and-commands-repl-io.md`
- `05_agent_07_06_cli-and-commands-hot-reload.md`
- `05_agent_07_07_cli-and-commands-migration-notes.md`
- `05_agent_07_08_cli-and-commands-slash-commands-session-mcp.md`
- `05_agent_07_09_cli-and-commands-slash-commands-context-db.md`
- `05_agent_07_11_cli-and-commands-slash-commands-memory-other.md`

## Keywords

workflow category
debug/audit category
git/diff category
compact/export category
