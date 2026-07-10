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

### Workflow category

| Command | Side effects | Related state |
|---|---|---|
| `/approve [reason]` | Resolves suspended workflow approval as approved | `ctx.turn.pending_approval_id` (DB-lookup fallback when None) |
| `/reject [reason]` | Resolves suspended workflow approval as rejected | `ctx.turn.pending_approval_id` (DB-lookup fallback when None) |

> **Scope:** `/approve` and `/reject` resolve **workflow-level approval gates only** (the `approvals` DB record).
> They do not affect per-tool interactive approval prompts (`tool_approval.run_approval_checks`).
> See [Tool Execution and Approval](05_agent_06_tool-execution-and-approval.md) for the canonical approval model.

#### Startup Recovery

If the agent restarts while a workflow-level approval is pending, the pending state is
automatically detected at startup from the `approvals` database table via
`StateStore.find_latest_pending_approval()`. A startup notice is shown:

```
[workflow] Pending approval from previous session — task=<task_id> approval=<approval_id> reason=<reason>. Use /approve [reason] or /reject [reason].
```

The workflow resumes from the approval gate; no re-execution of prior steps is needed.

**Cross-session guarantee:** `/approve` and `/reject` resolve the latest pending approval
from the `approvals` DB table even when in-memory `ctx.turn.pending_approval_id` is None
(e.g., after a crash). After `/approve` succeeds, `ctx.turn.pending_approval_task_id` is
set for auto-resume — no re-execution of prior steps is needed.

### Debug / audit category

| Command | Side effects | Related state |
|---|---|---|
| `/debug` | None | Toggle `ctx.conv.debug_mode` |
| `/debug verbose\|normal` | Change log level | `structlog` level change |
| `/audit [tail N\|turn <id>\|tool <name>]` | None | Read audit.log |

### RAG / Export category

| Command | Side effects | Related state |
|---|---|---|
| `/rag search <query> [--debug]` | MCP call to rag-pipeline-mcp | None |
| `/compact` | LLM call (compression) | Compresses history immediately |
| `/export [md\|json] [file]` | Write conversation to file or stdout | Markdown or JSON export |

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
