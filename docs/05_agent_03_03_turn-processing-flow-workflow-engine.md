---
title: "Agent Turn Processing Flow"
category: agent
tags:
  - agent
  - agent
  - turn
  - processing
  - flow
  - orchestrator
related:
  - 05_agent_00_document-guide.md
---

# Agent Turn Processing Flow



`Orchestrator.handle_turn()` runs via `WorkflowEngine` when `config/workflows/default.json`
exists and workflow DB is available. Workflow state is the primary execution model;
conversation history is maintained as a subordinate concern.

Each turn creates a `task` / `attempt` / `processed_event` record in `workflow.sqlite`:
- `tasks` — one per turn; status: `pending → running → [pending_approval →] completed | halted | failed`
- `attempts` — one per stage execution (plan/execute/verify), with retry tracking
- `processed_events` — idempotency enforcement; prevents duplicate stage execution
- `approvals` — one per approval gate; status: `pending → approved | rejected`
- `artifacts` — URIs produced by stage callbacks

Workflow stages (defined in `default.json`):
- `plan` — LLM generates initial plan; required
- `execute` — LLM executes the plan; required
- `verify` — LLM verifies execution results; required
- `retry` — optional transport error retry gate after `execute`; `retryable: false`; presence not required for `WorkflowEngine` operation

Each stage has a `StageDefinition`:
- `id` — unique stage identifier (e.g., "plan", "execute")
- `description` — human-readable description
- `timeout_sec` — maximum execution time in seconds
- `retryable` — whether the stage can be retried on failure

`WorkflowDef.get_stage(stage_id)` — returns the `StageDefinition` for the given id, or `None`.

Fallback: if `config/workflows/default.json` is missing or workflow DB is unavailable,
the traditional direct-execution flow is used.

Workflow package: `agent/workflow/` (models, workflow_loader, state_store, workflow_engine).

Default retry policy (applied when no `retry_policy` defined in `default.json`):
- `max_attempts`: 3
- `backoff`: "fixed"
- `backoff_sec`: 1

### Workflow Status

`Orchestrator.workflow_status()` returns a dict with two keys:
- `mode`: "auto" | "required" | "disabled" — from workflow policy
- `tracking`: "enabled" | "not_loaded" — "enabled" if workflow definition is set, "not_loaded" otherwise

### Approval Gate

When `WorkflowEngine(require_approval=True)`, the engine suspends after the execute stage
completes and before the verify stage runs:

1. Engine calls `store.request_approval(task_id)` → `ApprovalRecord` with `status=pending`
2. Task status → `pending_approval`
3. `WorkflowPendingApprovalError` raised → orchestrator stores `approval_id` in `ctx.turn.pending_approval_id`; logs WARNING: `[workflow] Approval required. Use /approve [reason] or /reject [reason].`

When the user runs `/approve [reason]` or `/reject [reason]`, the approval record is updated
in the DB. On the next workflow run with the same task, the gate checks the existing
approval record:

- `status=approved` → passes through to verify stage
- `status=rejected` → `WorkflowHaltError` raised; task halted
- `status=pending` → `WorkflowPendingApprovalError` re-raised (user has not yet responded)

If no existing approval record is found, a new one is created and the workflow is suspended.

### Workflow Exceptions

| Exception | When Raised |
|---|---|
| `WorkflowTimeoutError` | Stage execution exceeds `timeout_sec` |
| `WorkflowHaltError` | Task is halted (e.g., via `/halt` or after rejection) |
| `WorkflowPendingApprovalError` | Approval gate requires user action before proceeding |
| `WorkflowLoadError` | Workflow definition fails validation or loading |

### Retry Mechanism

When a stage is `retryable: true`, the engine uses the retry policy to determine retry behavior:
- `max_attempts`: Maximum number of attempts (default 3)
- `backoff`: Retry strategy — "fixed" or "exponential" (both use the same delay logic)
- `backoff_sec`: Delay between retries in seconds (default 1; always used as-is regardless of backoff type — both "fixed" and "exponential" apply the same constant delay)

### Workflow Loader Validation Rules

When loading a workflow definition from `config/workflows/*.json`:
- Required top-level keys: `name`, `version`, `stages`, `retry_policy`
- `stages` must be a non-empty list
- No duplicate stage IDs allowed
- Required stages: `plan`, `execute`, `verify` (must all be present)
- Each stage must have: `id`, `description`, `timeout_sec`, `retryable`
- `retry_policy.max_attempts` must be >= 1
- `retry_policy.backoff` must be "fixed" or "exponential"
- `retry_policy.backoff_sec` must be >= 0

---

## State Changes per Turn

| 

Stage | State mutated |
|---|---|
| ① TurnStart | `ctx.turn.current_turn_id` = UUID4 |
| ② Memory injection | `ctx.conv.history` prepended with system message |
| ③ User append | `ctx.conv.history` += user message; `ctx.stats.stat_turns += 1` |
| ④ Compression | `ctx.conv.history` oldest turns replaced with summary |
| ⑤ LLM + tools | `ctx.conv.history` += assistant + tool messages; stats updated |
| ⑥ TurnEnd | `ctx.turn.current_turn_id` = None |

## Turn-State Mutation Refere

nce

| State field | Mutated When | Durable? | Notes |
|---|---|---|---|
| `ctx.conv.history` | Each LLM/tool round (append) | Yes — saved to SQLite per message | Also compressed by HistoryManager |
| `ctx.turn.current_turn_id` | TurnStart (UUID4) / TurnEnd (None) | No — in-memory only | Used for per-turn correlation |
| `ctx.turn.pending_approval_id` | Workflow approval gate suspension | No — in-memory; approval persisted in `workflow.sqlite` | Reset to None on next turn |
| `ctx.stats.stat_turns` | After each user message appended | No — in-memory (reported via `/stats`) | Reset on session restart |
| `ctx.stats.stat_partial_completions` | When LLM stream interrupted | No — in-memory; partial content in `session_diagnostics` | Reset on session restart |
| `session.title` | First turn (async background task) | Yes — SQLite `sessions.title` | Non-blocking; fallback to truncated first input on LLM failure |

## Related Documents

- `agent`
- `turn`
- `processing`

## Keywords

agent
turn
processing
flow
orchestrator
