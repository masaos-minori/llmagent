# Agent Turn Processing Flow - Workflow Engine Integration & Turn-by-turn State Changes

- Runtime Architecture $\rightarrow$ [05_agent_02_runtime-architecture.md](05_agent_02_runtime-architecture.md)

## Purpose

To document the partial completion model, workflow engine integration, and state changes occurring during each agent turn. This includes the design decision for mandatory workflow execution, the mechanism for approval gates that persist across process boundaries, and the persistence characteristics of turn states.

## Design Intent

### Mandatory Workflow Execution (ADR-Workflow-Mandatory)

**Date:** 2026-07-23  
**Status:** Accepted

#### Context

This system executes tasks planned by an LLM. Some tools have side effects, some operations require approval, and tool execution must be observable and recoverable. A direct path from LLM to tools makes auditing and recovery difficult.

#### Decision

Workflow execution is mandatory. Workflow definitions are required artifacts at deployment time. Bypass modes for workflows are not supported. Optional workflow modes are not supported. Fallback to direct execution is not supported.

#### Rationale

- All side-effecting operations must be traceable.
- Approval states must persist across process boundaries.
- Retry and idempotency behaviors must be centrally managed.
- Partial task completion must be inspectable.
- Recovery requires persisted task and attempt states.
- Tool execution should not depend solely on the LLM conversation state.

#### Alternatives Considered

| Alternative | Reason for Rejection |
|---|---|
| Direct tool execution without workflow | Auditing and recovery become difficult. No persistent state for approval/retry logic. |
| Optional workflow mode | Inconsistency in behavior between workflow enabled/disabled. Operators cannot predict execution patterns. |
| Disabling workflow in local mode | Audit trails and approval tracking are still needed in local mode. Environment-specific rules cause confusion. |
| Fallback execution when workflow definition is missing | Silent degradation hides configuration errors. Startup failure provides immediate feedback. |
| Ad-hoc per-tool approval without workflow state | Approval state does not persist across process restarts. Cannot track which approval applies to which attempt. |

#### Impact

- Deployment must include workflow definition files.
- Startup must fail if required workflow artifacts are missing or invalid.
- Workflow schemas must be initialized before service startup.
- Operators must treat workflow failures as platform failures.
- Simple chats and tool-based tasks share the same execution control plane.

#### Non-Goals

This decision does not cover: individual workflow stage definitions, redesigning approval policies, introducing EventBus integration, or changing runtime behavior.

### Workflow State Semantics

Workflow state means "started" (not "completed"). It is used to prevent duplicate execution of stages. A `processed_events` record is created during each stage execution to prevent re-execution of the same stage.

### Resuming Existing Tasks

If an `existing_task_id` is provided, the existing `TaskRecord` is retrieved and reused instead of creating a new task. Two validations are performed:

- If the task is not found $\rightarrow$ `RuntimeError`
- If the task status is `halted` $\rightarrow$ `RuntimeError` — the `halted` state is a terminal/paused state and must not be automatically resumed without explicit user action.

Any `RuntimeError` is not caught by the caller's `except` block and propagates further up.

### Approval Gates

**Clarification of Terms:**
- **Pre-execution Approval**: A tool-level approval gate triggered before tool execution (real-time risk assessment).
- **Post-execution Approval**: A workflow-level approval gate triggered after the `execute` stage completes (batch result verification).
- **Automatic Execution**: Operations that do not require human approval (planning phase, verification phase, low-risk tool calls).

When `WorkflowEngine(require_approval=True)` is used, the engine pauses after the `execute` stage completes and before the `verify` stage begins:

**Production Operations Policy (Decided):** Whether `WorkflowDef.require_approval` is required is defined per operation category. Any production deployment whose default workflow can reach a category marked "Required" in the table below MUST explicitly set `require_approval: true` in the deployment's `config/workflows/*.json`. The bundled `config/workflows/default.json` ships with `require_approval: false` for local development; enabling it for production is done via an environment-specific override file (e.g. `config/workflows/production.json`).

| Operation Category | Approval Required in Production |
|---|---|
| File write | Conditional (only if the same task also executes another "Required" category) |
| File deletion | Required |
| Shell execution | Required |
| Git commit/push | Required (push only; commit alone may be left to the tool-level gate) |
| GitHub changes | Required (merge/push only; issue/PR creation is conditional) |
| CI/CD execution | Required |
| Database maintenance | Gap — the corresponding tool is not yet implemented |

**Local Development Exception:** Local/dev deployments may leave `require_approval: false` for all categories, since the tool-level pre-execution approval gate remains active.

**Approval Lifecycle (all paths):**
- **approve**: `/approve <approval_id> [reason]` $\rightarrow$ `status=approved`, passes to the `verify` stage on the next run
- **reject**: `/reject <approval_id> [reason]` $\rightarrow$ `status=rejected`, `WorkflowHaltError` is raised and the task halts
- **missing**: If no existing approval record is found, a new record is created and the workflow pauses
- **expire**: When `_gate_approval()` finds a `pending` record whose `expires_at` has passed, it marks that record `status=expired` and calls `request_approval()` again to re-request approval
- **cancel**: Not supported. By design, `/reject` is the only terminal path
- **resume**: On the next workflow run after approve/reject, the existing approval record is checked and follows the branches above

1. The engine calls `store.request_approval(task_id)` $\rightarrow$ creates an `ApprovalRecord` with `status=pending`.
2. Task status $\rightarrow$ `pending_approval`.
3. `WorkflowPendingApprovalError` occurs $\rightarrow$ orchestrator stores the `approval_id` and logs a WARNING.

When a user executes `/approve <approval_id> [reason]` or `/reject <approval_id> [reason]`, the approval record is updated in the DB. During the next workflow execution for the same task, the gate checks existing approval records:

- `status=approved` $\rightarrow$ pass to `verify` stage.
- `status=rejected` $\rightarrow$ `WorkflowHaltError` occurs; task is halted.
- `status=pending` $\rightarrow$ `WorkflowPendingApprovalError` occurs again.

If no existing approval record is found, a new record is created and the workflow pauses.

**Note:** Pre-execution approval (tool-level) and post-execution approval (workflow-level) trigger independently. They operate at different granularities and coexist without conflict.

## Responsibility Boundary

### Partial Completion Model

Partial completion occurs when an LLM response stream is interrupted before all content is received.

| Trigger | Storage Location | Display Method | `stat_partial_completions` |
|---|---|---|---|
| `LLMTransportError` while `partial_text` is non-empty | `session_diagnostics` table | `/stats` | +1 |
| `LLMTransportError` while `partial_text` is empty (before stream start) | Not stored (user message popped from history) | Error message visible to user | No change |

**Critical Invariant:** Partial content is NEVER added to `ctx.conv.history`. By isolating it to the diagnostic channel, subsequent LLM context is not polluted.

### Mandatory Workflow Execution

`Orchestrator.handle_turn()` is always executed via `WorkflowEngine`. Workflow definitions are unconditionally loaded at startup; if they are missing or invalid, startup is aborted with a `RuntimeError` before services start. Workflow state is the primary execution model, with conversation history maintained as a subordinate concern.

### Workflow Status

`Orchestrator.workflow_status()` returns a dict with two keys:

- `mode`: "required" — workflow is always mandatory
- `tracking`: "enabled" — workflow definitions are always loaded at startup

### Workflow Stages

| Stage | Responsibility | Mandatory |
|---|---|---|
| plan | Idempotency/bookkeeping only before execution; no LLM calls | Yes |
| execute | Memory injection, mode classification, LLM invocation, tool execution loop | Yes |
| verify | LLM verifies execution results | Yes |

### Retry Mechanism

All `plan`/`execute`/`verify` stages go through the same retry loop function. Stages where `retryable` is `false` (default: `plan` and `verify`) are executed once and raise an exception immediately upon failure. For stages where `retryable` is `true` (default: `execute`), retry behavior is determined by the retry policy:

- `max_attempts`: Maximum number of attempts (default 3)
- Backoff strategy is currently implemented as "fixed" only
- `backoff_sec`: Delay between retries (default 1s)

### Workflow Loader Validation Rules

When loading workflow definitions from `config/workflows/*.json`:

- Required top-level keys: `name`, `version`, `stages`, `retry_policy`
- `stages` must be a non-empty list
- Stage IDs must be unique
- Mandatory stages: `plan`, `execute`, `verify`
- Each stage must have: `id`, `timeout_sec`, `retryable`
- `retry_policy.max_attempts` must be $\ge 1$
- `retry_policy.backoff_sec` must be $\ge 0$

See also: [02_deployment.md](02_deployment.md) for deploy-time validation of these same rules, and the [Workflow Deployment Runbook](05_agent_10_04_operations-and-observability-validation-and-troubleshooting.md#workflow-deployment-runbook) for recovery steps when a rule is violated.

## Key Constraints

### Startup Recovery

During `Orchestrator.__init__()`, `StateStore.recover_stale_attempts()` is called. This searches for active attempts during process startup and marks them as `failed`.

### Default Behavior of Approval Gates

In default production settings, approval gates are not triggered. Enabling approval gates requires configuration changes.

## Operational Notes

- The `halted` state is a terminal state reached via `/reject` or an explicit stop operation; automatic resumption is not performed.
- If no existing approval record is found, a new record is created and the workflow pauses.

## Known Limitations

- Default approval gates are disabled and require explicit configuration changes.
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
| `ctx.stats.stat_turns` | After each user message addition | No — in-memory (`reported via /stats`) | Resets on session restart |
| `ctx.stats.stat_partial_completions` | On LLM stream interruption | No — in-memory; partial content is stored in `session_diagnostics` | Resets on session restart |
| `session.title` | First turn (asynchronous background task) | Yes — SQLite `sessions.title` | Non-blocking; falls back to truncating first input if LLM fails |

## Related Docs

- `05_agent_00_document-guide.md`
- `05_agent_03_01_turn-processing-flow-overview.md`
- `05_agent_03_02_turn-processing-flow-llm-tool-loop.md`
- `06_eventbus_00_document-guide.md`

## Keywords

partial-completion model
workflowengine integration
state changes per turn
turn-state mutation reference
ADR-Workflow-Mandatory
workflow execution mandatory
