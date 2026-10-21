# Turn task idempotency key collides across process restarts and aborts the first turn

## Priority
High

## Summary
Make workflow turn-task identity unique across process runs, so that reusing an existing
`workflow.sqlite` does not make the first turn of a new REPL session fail.

## Background
`Orchestrator._execute_turn` calls `self._workflow_adapter.execute_turn(line, 0.0, "")`
(`scripts/agent/orchestrator.py:167-169`) — the literal `""` is the only value any caller passes for
`session_id` (no other `execute_turn(` call site exists). `WorkflowEngineAdapter._init_workflow_task`
passes it straight to `agent.workflow.task_ops.create_task` (`scripts/agent/workflow_engine_adapter.py`
`:262-275`) with `turn_number=ctx.stats.stat_turns`, and `create_task` builds
`idempotency_key = f"{session_id}:{turn_number}"` when `session_id is not None`
(`scripts/agent/workflow/task_ops.py`); `tasks.idempotency_key` is `UNIQUE NOT NULL`
(`scripts/db/schema_sql.py:180`). `ctx.stats.stat_turns` is process-local and restarts at each run.

## Problem
Reproduced directly against the project's own code and schema: with `session_id=""`, the first insert
creates key `":1"`, and the next insert with the same turn number fails with
`sqlite3.IntegrityError: UNIQUE constraint failed: tasks.idempotency_key`. The key is not session-
scoped (`""` is not `None`, so the composite branch is taken) and not run-scoped, so every restart
against a retained `workflow.sqlite` collides on the first turn. Nothing in `scripts/agent/` catches
`IntegrityError` on this path (`grep -rn IntegrityError scripts/` matches only
`scripts/agent/memory/ingestion.py:215`), so the failure escapes `_init_workflow_task` and aborts the
whole turn.

Operationally this has not been observed in this environment: `workflow.sqlite` contains 0 rows in
`tasks`/`attempts`/`artifacts`, and `audit.log` contains no `workflow_start`/`turn_start` events,
because recent startup attempts ended before the REPL was reached (`agent.log` shows a FATAL
`mcp_tool_discovery` result). The defect is proven at code and runtime level, not from production
incidents.

## Reason for Change
A turn that fails at `_init_workflow_task` produces no answer, no audit trail, and a `[fatal]` line in
the REPL, and it fails on the first turn after any restart — i.e. it is a data-retention-dependent
startup-adjacent failure.

## Implementation Intent
Decide what a turn task is unique over, then encode that. Either pass the real session id
(`ctx.session.session_id`, already formatted by `_format_session_id`, `workflow_engine_adapter.py:206-208`)
plus the turn number, or make the key per-run (UUID) and use the composite key only where a resume
lookup is actually performed.

## Target Files or Areas
- `scripts/agent/orchestrator.py` (`_execute_turn`)
- `scripts/agent/workflow_engine_adapter.py` (`execute_turn`, `_init_workflow_task`, `_format_session_id`)
- `scripts/agent/workflow/task_ops.py` (`create_task`)
- `scripts/db/schema_sql.py` (contract reference only)

## Required Changes
- Pass a real, session-scoped identifier into `execute_turn` instead of the literal `""`, or stop
  deriving `idempotency_key` from process-local counters.
- Handle the collision explicitly: either look up an existing task by key and resume it, or generate a
  collision-free key. Do not let `IntegrityError` escape the turn entry point.
- Make `turn_number`'s source and reset semantics explicit (per session vs per process) in code.

## Constraints
- `tasks.idempotency_key UNIQUE NOT NULL` is an existing schema contract; changing it needs a schema
  version decision (see `workflow_schema_version` = 2 in the live DB).
- `/resume`-style reuse of an existing task id must keep working.
- Existing `workflow.sqlite` content must not need to be deleted by this change.

## Acceptance Criteria
- Two consecutive process runs against the same `workflow.sqlite` both complete their first turn.
- The key of a turn task is unique over (session, turn) or globally unique, and the choice is stated in
  code.
- No uncaught `sqlite3.IntegrityError` from `_init_workflow_task`.

## Testing Expectations
- Regression test at `task_ops.create_task` level: insert `(session_id=X, turn_number=1)` twice across
  two simulated runs and assert no `IntegrityError`.
- Adapter-level test asserting `execute_turn` receives a non-empty session id derived from the session.
- Keep `workflow.sqlite` under a `tmp_path` fixture; never the production path.
- `uv run pytest tests/agent -q`, `uv run ruff check scripts/agent`,
  `uv run mypy --no-namespace-packages scripts/agent`.

## Documentation Impact
Document in the workflow/task docs (the `docs/23_agent/` workflow section) what a task idempotency key
means, over which scope it is unique, what happens on collision, and how a retained
`workflow.sqlite` interacts with a new session. Note the current state (0 rows, path not exercised in
this environment) as a Known Issue rather than as evidence the defect is absent.

## Out of Scope
- Stage retry semantics (`turn002`) and task status transitions (`turn003`).
- Retention/pruning policy for `workflow.sqlite`.

## Dependencies
- `turn002` and `turn003` are the same task-lifecycle area; sequence this issue first because the
  status/retry fixes assume a task row exists.
- Related to `issues/20261018-*_compat001_*`/`compat002` style decisions about retained DB state, but
  not a duplicate of them.

## Unresolved Questions
- Should a collided turn resume the existing task or create a new one? Needs confirmation.
- Is `session_id` intended to be the numeric session id, the REPL session id string, or a per-run id?
  `_format_session_id` returns `""` when the session id is `None`, which is also the value currently
  hardcoded at `orchestrator.py:168`. Needs confirmation.

## AI Implementation Instruction
Fix the identity, not the symptom: do not wrap the insert in a broad `except`. State the uniqueness
scope in a docstring and cover both same-session and cross-process cases with tests.

## Traceability
- **Workflow phase**: `python-code-review` (turn orchestration review), filed via `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261021-093421
- **Related target files**: `scripts/agent/orchestrator.py`, `scripts/agent/workflow_engine_adapter.py`,
  `scripts/agent/workflow/task_ops.py`, `scripts/db/schema_sql.py`
