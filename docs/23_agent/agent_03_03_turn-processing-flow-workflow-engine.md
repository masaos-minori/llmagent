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

### Task Status Transitions

The persisted turn outcome lives in the workflow `tasks` table. Each outcome has exactly one writer.
The outward turn result is the typed tuple `(answer, error_kind, is_partial)`; on engine halt and
timeout exits its `error_kind` is `workflow_halted` and `workflow_timeout` respectively, and on an
LLM-level stage failure it is the LLM error kind itself — no terminal-failure turn returns an empty
`error_kind` alongside a `halted` or `failed` task.

| Turn exit | `tasks.status` | Written by | Reason |
|---|---|---|---|
| All stages complete | `completed` | workflow engine | so that the record is written at the moment the transition happens and no second owner has to re-derive it |
| A stage raises and the engine re-raises it (e.g. an LLM-level failure, persisted on the attempt row with kind `llm_failure`) | `failed` | workflow engine | the engine observes the failing stage directly, and writes `failed` exactly once |
| A retryable stage exhausts `max_attempts`, or its stage deadline expires, or its failure kind is not in `retry_policy.retry_on`, or the failure is side-effect-flagged | `halted` | workflow engine | the engine stops the run itself |
| The turn is cancelled while a stage is running | `halted` | turn adapter | the engine cannot observe cancellation, so the adapter records the stop in the existing terminal vocabulary instead of introducing a new status |
| The turn fails before the engine starts | `pending` | neither | the row keeps the value it was created with, because no stage ever ran |

- A successful turn produces exactly one `completed` write.
- Cancellation is recorded `halted` on purpose: no `cancelled` status exists, and `halted` is already
  the terminal, non-resumable state described in [Resuming Existing Tasks](#resuming-existing-tasks)
  and in `## Operational Notes`. Cancellation is the only status write the adapter makes.
- A failing status write is a storage fault, not a turn outcome: it propagates out of the turn
  instead of being rescued by a second, adapter-side write.
- A cancelled turn is distinguishable from a retry-exhausted halt by the attempt records: the
  abandoned attempt carries no error classification, while halted engine exits persist a kind
  (`timeout` or `exception`) on the final attempt row.

### Workflow Stages

| Stage | Responsibility | Mandatory |
|---|---|---|
| plan | Idempotency/bookkeeping only before execution; no LLM calls | Yes |
| execute | LLM invocation, tool execution loop (per-attempt; retried per the retry policy) | Yes |
| verify | LLM verifies execution results | Yes |

> Turn-entry preparation — clearing the previous turn's ephemeral messages, injecting memory,
> classifying the turn mode, appending the user message, and compressing history — runs once per
> turn before the engine runs. It is not a stage and is not re-run when the `execute` stage is
> retried.

### Turn-End and Teardown Ownership

The engine's `verify` stage still runs because the engine signature requires it, but turn-end work
and workflow teardown moved out of the adapter into the Orchestrator's `_execute_turn` bracket:

- `turn_end` is emitted by the Orchestrator's `_execute_turn` bracket on every exit path, not by the
  `verify` stage.
- `execute_turn`'s `finally` no longer deactivates the workflow; the caller's bracket does.
- `_handle_workflow_halt` no longer clears `ctx.workflow.*`; the caller's bracket does.

### Retry Mechanism

All `plan`/`execute`/`verify` stages go through the same retry loop function. Stages where `retryable` is `false` (default: `plan` and `verify`) are executed once and raise an exception immediately upon failure. For stages where `retryable` is `true` (default: `execute`), retry behavior is determined by the retry policy:

- `max_attempts`: Maximum number of attempts
- Backoff strategy is currently implemented as "fixed" only
- `backoff_sec`: Delay between retries
- `retry_on`: the list of failure kinds that are eligible for retry, drawn from `exception`,
  `timeout`, and `llm_failure` (shipped default: `["exception"]`). A failure whose kind is not in
  `retry_on` is terminal at once — no backoff wait and no further attempt.
- Every failed attempt consumes one `max_attempts` unit, regardless of its kind.
- A stage deadline expiry is classified by the deadline's own expired state and persisted with kind
  `timeout`; a `TimeoutError` raised by the stage callback itself is kind `exception`, not relabeled
  as a deadline timeout. Under the shipped policy a deadline expiry is therefore terminal, while a
  callback-raised `TimeoutError` is retried.
- Attempt-row kinds (`timeout` / `exception` / `llm_failure`) are distinct from the outward turn
  kinds (`workflow_halted` / `workflow_timeout` / the LLM error kind).

> A retry of the `execute` stage re-runs only LLM/tool execution. Turn-entry preparation runs once
> per turn before the engine runs; it is not re-run on a retry, is not retried itself, and is not
> bounded by `execute.timeout_sec`. Memory search and history compression keep their own timeouts.

### Workflow Loader Validation Rules

When loading workflow definitions from `config/workflows/*.json`:

- A definition must have a non-empty list of uniquely identified stages, which must include `plan`, `execute`, and `verify`; each stage declares `timeout_sec` and `retryable`, with `timeout_sec` an integer of at least 1
- `retry_policy.max_attempts` and `retry_policy.backoff_sec` must both be integers, not booleans, floats, or strings, with `max_attempts` at least 1 and `backoff_sec` at least 0
- A value that fails this validation stops loading with a workflow load error that names the field and the offending value, so every caller observes the same error type
- `retry_policy.retry_on`, when present, must be a list of strings drawn from `exception`, `timeout`,
  and `llm_failure`; an absent key loads the default `["exception"]`
- The `require_approval` key must not be present: the workflow has no approval stage

See also: the [Workflow Deployment Runbook](agent_10_04_operations-and-observability-validation-and-troubleshooting.md#workflow-deployment-runbook) for recovery steps when a rule is violated.

## Key Constraints

### Startup Recovery

During `Orchestrator.__init__()`, `StateStore.recover_stale_attempts()` is called with the store's connection. It classifies every `running` attempt row and repairs attempt records only: it never changes the persisted task status, so a task left `running` or `halted` by an earlier process stays as it was.

- Expired lease means stale. An attempt is stale when its `lease_expires_at` is in the past. The lease is stamped at attempt start as `started_at` plus the stage `timeout_sec` plus a 30 s margin (`workflow_engine._LEASE_MARGIN_SEC`), so a lease never expires while its own stage is still executing. A live lease is never recovered, even when `started_at` is hours old.
- Lease-less (pre-migration) rows use the age rule: they are stale only when `started_at` is older than 3600 s.
- Unparseable timestamps are reported, not touched: rows whose `started_at` or `lease_expires_at` cannot be parsed are counted in `StateStore.last_recovery_report` (`unparseable`), logged with the attempt id, and left `running` for the manual path below.
- Takeover is a conditional compare-and-swap UPDATE pinned to the `owner_id` and `lease_expires_at` values seen by the classify pass, with `status='running'` required; concurrent recoverers converge to exactly one winner.

Timestamp contract: workflow timestamps are written as `YYYY-MM-DDTHH:MM:SSZ` by the shared clock and parsed only by `scripts/shared/json_utils.parse_iso_utc`, which rejects naive input; recovery never uses host-local time.

Manual recovery for rows left `running` (unparseable or lease-less and young): identify the owning process from `owner_id` (`hostname-pid-random`), confirm the process is gone, then correct the row via manual SQL against the workflow database. There is no automated takeover for these rows.

## Operational Notes

- The `halted` state is a terminal state reached when a retryable stage exhausts `max_attempts`, a
  stage deadline expires, a failure kind is not in `retry_policy.retry_on`, or a failure is
  side-effect-flagged; automatic resumption is not performed.
- A retry never follows an attempted non-READ tool call: every non-READ operation (including
  unclassified `UNKNOWN` tools) sets the per-attempt side-effect flag before execution, and a failure
  after the flag is set is made terminal rather than retried. This conservative rule may be relaxed
  later by an owner decision; until then it is the shipped behavior.
- An LLM-level stage failure is persisted on the attempt row with kind `llm_failure`, leaves the task
  `failed` — written exactly once, by the engine — and surfaces outward as the LLM error kind on the
  typed turn result.
- `halted` is also the recorded outcome of a cancelled turn. The adapter records it because the engine
  does not observe cancellation, and it uses the same terminal state so the resume guard needs no new
  case.
- A persisted task status is written by one owner per outcome; see [Task Status Transitions](#task-status-transitions).

## Known Limitations

- Only "fixed" backoff strategy is implemented for retries.
- A cancelled turn leaves its in-flight attempt open until the next process start, when startup recovery closes it after the attempt's lease expires. The task record itself is not repaired by that pass.

---

## Turn-by-turn State Changes

Per-turn state changes follow the step order in [agent_03_01](agent_03_01_turn-processing-flow-overview.md); the persistence and reset semantics of each state field are below.

### Turn State Mutation Reference

| State Field | Modification Timing | Persistence | Remarks |
|---|---|---|---|
| `ctx.conv.history` | Each LLM/tool round (addition) | Yes — saved to SQLite per message | Also subject to compression by HistoryManager |
| `ctx.turn.current_turn_id` | At TurnStart (UUID4) / TurnEnd (None) | No — in-memory only | Used for correlation within a turn |
| `ctx.turn.attempt_side_effect` | Set before a non-READ tool call executes; cleared at each `execute`-stage attempt start | No — in-memory only | Makes a failure after an attempted side effect terminal instead of retried |
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
