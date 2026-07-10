---
title: "Agent Tool Execution and Approval"
category: agent
tags:
  - agent
  - agent
  - tool
  - execution
  - approval
  - safety
related:
  - 05_agent_00_document-guide.md
---

# Agent Tool Execution and Approval

 tool loop in `LLMTurnRunner`:

| Guard | Config field | Behavior |
|---|---|---|
| Dedup | `tool_dedup_max_repeats` (default 3) | Same (name, args) repeated ≥ N times → terminate loop; hint stored in `session_diagnostics` |
| Cycle detection | `tool_cycle_detect_window` (default 2) | Same tool-call fingerprint repeated in last N rounds → terminate loop; hint stored in `session_diagnostics` |
| Retry cap | `tool_error_retry_max` (default 1) | Errored (name, args) called again → terminate loop; hint stored in `session_diagnostics` |
| Consecutive error | `tool_error_max_consecutive` (default 3) | All tools in round error N times → terminate loop |

> **Note:** Guard hints are stored for offline diagnostics only. They are **not** injected into `ctx.conv.history`.

---

## Concurrency Limits

`tool_concurr

ency_limits: dict[str, int]` (in `ToolConfig`) maps server key to max
concurrent calls. Implemented as `asyncio.Semaphore` lazily created during tool execution.

If a server key appears in the limit dict, calls are bounded. Missing keys: no limit.
Unknown server key warning logged but does not error.

---

## Fail-Closed Execution Policy

The

 orchestrator does NOT fall back to direct (unapproved) execution when a workflow
cannot be created. If workflow creation fails, a `WorkflowCreationError` is raised and
the task is rejected with a clear error message.

**Before (removed):** the orchestrator would execute tool calls directly, bypassing
workflow-level approval checks, when no workflow plan was available.

**After:** `WorkflowCreationError` is raised. The user must fix the underlying cause
(missing plan, invalid config) and retry.

This is a fail-closed policy: safety is preferred over availability.
See [Agent Startup and Recovery](05_agent_07_01_cli-and-commands-cli-reference.md#startup-recovery) for the startup recovery model.

---

## Workflow Approval Recovery (Cross

-Session)

Workflow-level approval state is persisted in the `approvals` table of `workflow.sqlite`.
When a workflow task is suspended for approval (user must run `/approve` or `/reject`),
the approval record survives agent restart:

- **Startup recovery:** On startup, queries the `approvals` table
  for any pending approval. If found, it sets `ctx.workflow.approval_pending = True` and
  `ctx.turn.pending_approval_id`, then displays a warning with task ID and approval ID.

- **Resolution after restart:** `/approve` and `/reject` resolve the latest pending approval
  from the workflow database — in-memory `pending_approval_id` is NOT required for resolution.
  This means even if the in-memory state is lost, the user can still approve/reject via the CLI.

- **Warning message includes IDs:** The startup warning shows `task=<id> approval=<id> reason=<reason>`
  so operators can correlate with logs and know which task to act on.

---

## Canonical Approval Model (ADR-001

## Related Documents

- `agent`
- `tool`
- `execution`

## Keywords

agent
tool
execution
approval
safety
