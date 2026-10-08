---
title: "Agent Turn Processing Flow - Workflow Engine Integration & Turn-by-turn State Changes"
area: agent
tags:
  - agent
  - turn-processing
  - workflow-engine
related:
  - agent_03_01_turn-processing-flow-overview.md
  - agent_03_02_turn-processing-flow-llm-tool-loop.md
  - agent_00_document-guide.md
  - eventbus_00_document-guide.md
---
# Agent Turn Processing Flow - Workflow Engine Integration & Turn-by-turn State Changes

- Runtime Architecture → [agent_02_runtime-architecture.md](agent_02_runtime-architecture.md)

## Purpose

To document the partial completion model, workflow engine integration, and state changes occurring during each agent turn. This includes the design decision for mandatory workflow execution, the mechanism for approval gates that persist across process boundaries, and the persistence characteristics of turn states.

## Design Intent

### Mandatory Workflow Execution

See [ADR-001](../10_adr/ADR-001-workflow-engine-mandatory.md) for rationale, alternatives, tradeoffs, and invariants.

### Workflow State Semantics

Workflow state means "started" (not "completed"). It is used to prevent duplicate execution of stages. A `processed_events` record is created during each stage execution to prevent re-execution of the same stage.

### Resuming Existing Tasks

If an `existing_task_id` is provided, the existing `TaskRecord` is retrieved and reused instead of creating a new task. Two validations are performed:

- If the task is not found → `RuntimeError`
- If the task status is `halted` → `RuntimeError` — the `halted` state is a terminal/paused state and must not be automatically resumed without explicit user action.

Any `RuntimeError` is not caught by the caller's `except` block and propagates further up.

### Approval Gates

**Clarification of Terms:**
- **Pre-execution Approval**: A tool-level approval gate triggered before tool execution (real-time risk assessment).
- **Post-execution Approval**: A workflow-level approval gate triggered after the `execute` stage completes (batch result verification).
- **Automatic Execution**: Operations that do not require human approval (planning phase, verification phase, low-risk tool calls).

When `WorkflowEngine(require_approval=True)` is used, the engine pauses after the `execute` stage completes and before the `verify` stage begins:

**Operations Policy (Decided):** Whether `WorkflowDef.require_approval` is required is defined per operation category. Any deployment whose workflow can reach a category marked "Required" in the table below MUST explicitly set `require_approval: true` in its `config/workflows/*.json`. This is an operational policy only: `WorkflowLoader` parses `require_approval` as an optional boolean that is false when absent, and `ProductionConfigValidator` has no `require_approval` rule, so neither enforces it (Explicit in code — scripts/agent/workflow/workflow_loader.py, scripts/agent/production_config_validator.py). The bundled `config/workflows/default.json` sets `require_approval` to false and therefore does not meet this policy for the "Required" categories; the workflow-level gate does not fire with it.

| Operation Category | Workflow-level Approval Required |
|---|---|
| File write | Conditional (only if the same task also executes another "Required" category) |
| File deletion | Required |
| Shell execution | Required |
| Git commit/push | Required (push only; commit alone may be left to the tool-level gate) |
| GitHub changes | Required (merge/push only; issue/PR creation is conditional) |
| CI/CD execution | Required |
| Database maintenance | Gap — the corresponding tool is not yet implemented |

**Tool-level gate:** Independently of `require_approval`, the tool-level pre-execution approval gate (risk rules in `config/agent.toml`) remains active.

**Approval Lifecycle (all paths):**
- **approve**: `/approve <approval_id> [reason]` → `status=approved`, passes to the `verify` stage on the next run
- **reject**: `/reject <approval_id> [reason]` → `status=rejected`, `WorkflowHaltError` is raised and the task halts
- **missing**: If no existing approval record is found, a new record is created and the workflow pauses
- **expire**: When `_gate_approval()` finds a `pending` record whose `expires_at` has passed, it marks that record `status=expired` and calls `request_approval()` again to re-request approval. `is_expired()` method exists in `approval_ops.py` for checking expiration status.
- **cancel**: Not supported. By design, `/reject` is the only terminal path
- **resume**: On the next workflow run after approve/reject, the existing approval record is checked and follows the branches above

1. The engine calls `store.request_approval(task_id)` → creates an `ApprovalRecord` with `status=pending`.
2. Task status → `pending_approval`.
3. `WorkflowPendingApprovalError` occurs → orchestrator stores the `approval_id` and logs a WARNING.

When a user executes `/approve <approval_id> [reason]` or `/reject <approval_id> [reason]`, the approval record is updated in the DB. During the next workflow execution for the same task, the gate checks existing approval records:

- `status=approved` → pass to `verify` stage.
- `status=rejected` → `WorkflowHaltError` occurs; task is halted.
- `status=pending` → `WorkflowPendingApprovalError` occurs again.

If no existing approval record is found, a new record is created and the workflow pauses.

**Note:** Pre-execution approval (tool-level) and post-execution approval (workflow-level) trigger independently. They operate at different granularities and coexist without conflict.

## Responsibility Boundary

### Partial Completion Model

Partial completion occurs when an LLM response stream is interrupted before all content is received.

| Trigger | Storage Location | Display Method | `stat_partial_completions` |
|---|---|---|---|
| `LLMTransportError` while `partial_text` is non-empty | `session_diagnostics` table | stats subcommand | +1 |
| `LLMTransportError` while `partial_text` is empty (before stream start) | Not stored (user message popped from history) | Error message visible to user | No change |

**Critical Invariant:** Partial content is NEVER added to `ctx.conv.history`. By isolating it to the diagnostic channel, subsequent LLM context is not polluted.

### Mandatory Workflow Execution

`Orchestrator.handle_turn()` is always executed via `WorkflowEngine`. See [ADR-001](../10_adr/ADR-001-workflow-engine-mandatory.md) for rationale and invariants.

### Workflow Status

`Orchestrator.workflow_status()` returns a dict with a single key `tracking`:

- `"enabled"` when the workflow is active (workflow definitions are loaded at startup)
- `"not_loaded"` otherwise

### Workflow Stages

| Stage | Responsibility | Mandatory |
|---|---|---|
| plan | Idempotency/bookkeeping only before execution; no LLM calls | Yes |
| execute | Memory injection, mode classification, LLM invocation, tool execution loop | Yes |
| verify | LLM verifies execution results | Yes |

### Retry Mechanism

All `plan`/`execute`/`verify` stages go through the same retry loop function. Stages where `retryable` is `false` (default: `plan` and `verify`) are executed once and raise an exception immediately upon failure. For stages where `retryable` is `true` (default: `execute`), retry behavior is determined by the retry policy:

- `max_attempts`: Maximum number of attempts
- Backoff strategy is currently implemented as "fixed" only
- `backoff_sec`: Delay between retries

### Workflow Loader Validation Rules

When loading workflow definitions from `config/workflows/*.json`:

- Required top-level keys: `name`, `version`, `stages`, `retry_policy`
- `stages` must be a non-empty list
- Stage IDs must be unique
- Mandatory stages: `plan`, `execute`, `verify`
- Each stage must have: `id`, `timeout_sec`, `retryable`
- `retry_policy.max_attempts` must be ≥ 1
- `retry_policy.backoff_sec` must be ≥ 0

See also: the [Workflow Deployment Runbook](agent_10_04_operations-and-observability-validation-and-troubleshooting.md#workflow-deployment-runbook) for recovery steps when a rule is violated.

## Key Constraints

### Startup Recovery

During `Orchestrator.__init__()`, `StateStore.recover_stale_attempts()` is called. This searches for active attempts during process startup and marks them as `failed`.

### Default Behavior of Approval Gates

With the bundled `config/workflows/default.json`, the workflow-level approval gate is not triggered; enabling it requires setting `require_approval` to true in the workflow definition. The tool-level pre-execution gate is unaffected.

## Operational Notes

- The `halted` state is a terminal state reached via `/reject` or an explicit stop operation; automatic resumption is not performed.
- If no existing approval record is found, a new record is created and the workflow pauses.

## Known Limitations

- The workflow-level approval gate is disabled in the bundled workflow definition, and no code enforces the operations policy above; enabling it requires an explicit workflow definition change. This gap is tracked as AGENT-001 in `governance_03_issue-and-uncertainty-management.md`.
- Only "fixed" backoff strategy is implemented for retries.

---

## Turn-by-turn State Changes

| Phase | State Modified |
|---|---|
| TurnStart | `ctx.turn.current_turn_id` = UUID4 |
| Memory Injection | System message is added to the beginning of `ctx.conv.history` |
| User Addition | `ctx.conv.history` += user message; `ctx.stats.stat_turns += 1` |
| Compression | Oldest turns in `ctx.conv.history` are replaced with summary |
| LLM + Tool | `ctx.conv.history` += assistant + tool messages; statistics updated |
| TurnEnd | `ctx.turn.current_turn_id` = None |

### Turn State Mutation Reference

| State Field | Modification Timing | Persistence | Remarks |
|---|---|---|---|
| `ctx.conv.history` | Each LLM/tool round (addition) | Yes — saved to SQLite per message | Also subject to compression by HistoryManager |
| `ctx.turn.current_turn_id` | At TurnStart (UUID4) / TurnEnd (None) | No — in-memory only | Used for correlation within a turn |
| `ctx.turn.pending_approval_id` | When workflow approval gate is paused | No — in-memory only; approval is persisted in `workflow.sqlite` | Reset to `None` on the next turn |
| `ctx.stats.stat_turns` | After each user message addition | No — in-memory (reported via stats command) | Resets on session restart |
| `ctx.stats.stat_partial_completions` | On LLM stream interruption | No — in-memory; partial content is stored in `session_diagnostics` | Resets on session restart |
| `session.title` | First turn (asynchronous background task) | Yes — SQLite `sessions.title` | Non-blocking; falls back to truncating first input if LLM fails |

## Keywords

- partial-completion model
- workflowengine integration
- state changes per turn
- turn-state mutation reference
- ADR-001
- workflow execution mandatory
