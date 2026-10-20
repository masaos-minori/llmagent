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
  - agent_02_runtime-architecture.md
  - adr_02_02_001_agent-workflow-engine-mandatory.md
  - agent_10_04_operations-and-observability-validation-and-troubleshooting.md
---
# Agent Turn Processing Flow - Workflow Engine Integration & Turn-by-turn State Changes

- Runtime Architecture → [agent_02_runtime-architecture.md](agent_02_runtime-architecture.md)

## Purpose

To document the partial completion model, workflow engine integration, and state changes occurring during each agent turn. This includes the design decision for mandatory workflow execution, how human approval relates to the workflow (tool-level only), and the persistence characteristics of turn states.

## Design Intent

### Mandatory Workflow Execution

See [ADR-001](../10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md) for rationale, alternatives, tradeoffs, and invariants.

### Workflow State Semantics

Workflow state means "started" (not "completed"). It is used to prevent duplicate execution of stages. A `processed_events` record is created during each stage execution to prevent re-execution of the same stage.

### Resuming Existing Tasks

If an `existing_task_id` is provided, the existing `TaskRecord` is retrieved and reused instead of creating a new task. Two validations are performed:

- If the task is not found → `RuntimeError`
- If the task status is `halted` → `RuntimeError` — the `halted` state is a terminal/paused state and must not be automatically resumed without explicit user action.

Any `RuntimeError` is not caught by the caller's `except` block and propagates further up.

### Approval

Human approval is decided before a Tool executes, by the tool-level approval (see [agent_06_02_tool-execution-and-approval-approval.md](agent_06_02_tool-execution-and-approval-approval.md) and [agent_06_04_tool-execution-and-approval-canonical.md](agent_06_04_tool-execution-and-approval-canonical.md)), inside the `execute` stage; the risk rules are in `config/agent.toml`. The workflow has no approval stage: `plan`, `execute`, and `verify` run in sequence, and a turn that runs write Tools completes without operator action.

A workflow definition that contains the `require_approval` key is rejected at load time (`WorkflowLoadError`), and Agent startup is aborted.

Every tool-level approval decision is written to the audit log as a `tool_approval` event that carries the `workflow_id` and the turn ID in its `task_id` field.

## Responsibility Boundary

### Partial Completion Model

Partial completion occurs when an LLM response stream is interrupted before all content is received.

| Trigger | Storage Location | Display Method | `stat_partial_completions` |
|---|---|---|---|
| `LLMTransportError` while `partial_text` is non-empty | `session_diagnostics` table | stats subcommand | +1 |
| `LLMTransportError` while `partial_text` is empty (before stream start) | Not stored (user message popped from history) | Error message visible to user | No change |

**Critical Invariant:** Partial content is NEVER added to `ctx.conv.history`. By isolating it to the diagnostic channel, subsequent LLM context is not polluted.

### Workflow Status

`Orchestrator.workflow_status()` returns a dict with a single key `tracking`:

- `"running"` while a workflow task executes within the current turn
- `"enabled"` otherwise, including right after startup; the workflow definition is always loaded because `Orchestrator` construction aborts startup when it fails to load

The startup banner prints this value, or `unknown` when no `Orchestrator` exists yet.

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

- A definition must have a non-empty list of uniquely identified stages, which must include `plan`, `execute`, and `verify`; each stage declares `timeout_sec` and `retryable`
- `retry_policy.max_attempts` must be ≥ 1 and `retry_policy.backoff_sec` must be ≥ 0
- The `require_approval` key must not be present: the workflow has no approval stage

See also: the [Workflow Deployment Runbook](agent_10_04_operations-and-observability-validation-and-troubleshooting.md#workflow-deployment-runbook) for recovery steps when a rule is violated.

## Key Constraints

### Startup Recovery

During `Orchestrator.__init__()`, `StateStore.recover_stale_attempts()` is called. This searches for active attempts during process startup and marks them as `failed`.

## Operational Notes

- The `halted` state is a terminal state reached when a retryable stage exhausts `max_attempts` or a stage times out; automatic resumption is not performed.

## Known Limitations

- Only "fixed" backoff strategy is implemented for retries.

---

## Turn-by-turn State Changes

Per-turn state changes follow the step order in [agent_03_01](agent_03_01_turn-processing-flow-overview.md); the persistence and reset semantics of each state field are below.

### Turn State Mutation Reference

| State Field | Modification Timing | Persistence | Remarks |
|---|---|---|---|
| `ctx.conv.history` | Each LLM/tool round (addition) | Yes — saved to SQLite per message | Also subject to compression by HistoryManager |
| `ctx.turn.current_turn_id` | At TurnStart (UUID4) / TurnEnd (None) | No — in-memory only | Used for correlation within a turn |
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
