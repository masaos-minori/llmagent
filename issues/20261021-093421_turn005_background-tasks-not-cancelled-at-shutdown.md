# Background tasks are tracked in a set the shutdown coordinator never reads, and cancelled tasks leak

## Priority
High

## Summary
Give background tasks one owner and make the shutdown path actually cancel them; make
`BgTaskMonitor.on_task_done` safe for cancelled tasks.

## Background
`Orchestrator.__init__` creates `self._background_tasks: set[asyncio.Task[object]]`
(`scripts/agent/orchestrator.py:89`) and injects that same set into both `BgTaskMonitor`
(`:94-101`, `bg_task_monitor.py:51`) and `ConversationStateManager` (`:109-117`), which adds real
first-turn tasks to it (`conversation_state_manager.py:113-118`).
`ResourceShutdownCoordinator` cancels what it finds at `ctx.turn.background_tasks`
(`scripts/agent/resource_shutdown_coordinator.py:114-117`), i.e. `TurnState.background_tasks`
(`scripts/agent/context.py:200`), which has no producer anywhere under `scripts/` (verified by grep).

## Problem
- The set the shutdown coordinator walks and clears is always empty, so no first-turn background task
  (title generation, memory extraction, and similar) is cancelled at shutdown.
- `BgTaskMonitor.on_task_done` reads `exc = task.exception()` (`scripts/agent/bg_task_monitor.py:76`).
  For a cancelled task `Task.exception()` raises `CancelledError`, so the callback aborts at that line:
  the `isinstance(exc, asyncio.CancelledError)` branch at `:79-81` is unreachable, and the bookkeeping at
  `:119-120` (`_consecutive_failures[task_name] = count`, `self._tasks.discard(task)`) never runs.
  Cancelled tasks therefore stay in the tracked set and failure counters are not reset.
- `TurnState.background_tasks` is declared state with no producer — the natural reading is that the
  shutdown coordinator owns task cancellation, and it does not.

## Reason for Change
Uncancelled background tasks keep running (and keep touching history, DB, and audit state) while the REPL
is shutting down, and a set that only grows makes the pause/failure threshold logic in
`BgTaskMonitor` unreliable.

## Implementation Intent
Pick one home for the tracked set — either `TurnState.background_tasks` (so the shutdown coordinator's
existing code becomes live) or the Orchestrator-owned set passed to the coordinator — and make every
producer and consumer use it. Make `on_task_done` classify cancellation without letting
`CancelledError` escape the callback.

## Target Files or Areas
- `scripts/agent/orchestrator.py` (`__init__` injection)
- `scripts/agent/bg_task_monitor.py` (`on_task_done`)
- `scripts/agent/conversation_state_manager.py` (task creation)
- `scripts/agent/resource_shutdown_coordinator.py` (cancellation step)
- `scripts/agent/context.py` (`TurnState.background_tasks`)

## Required Changes
- Populate the set the shutdown coordinator reads, or change the coordinator to read the real one; do
  not keep both.
- Replace `task.exception()` with a cancellation-safe read (check `task.cancelled()` first) so the
  callback always reaches its discard/reset step.
- Remove the `hasattr`-guarded lookup at `resource_shutdown_coordinator.py:114-116` in favor of an
  explicit dependency.
- Reset or preserve failure counters deliberately, and state which.

## Constraints
- `BgTaskMonitor`'s pause-on-critical-failure behavior (`pause_on_critical_failure`) must not change.
- Background tasks must not be cancelled while a turn is in progress; only at shutdown.
- Keep `on_discard`/`on_error` callback contracts stable.

## Acceptance Criteria
- After a REPL shutdown, every background task created during the session is cancelled and absent from
  the tracked set.
- Cancelling a tracked task does not raise inside `on_task_done`, and the task is removed from the set.
- The `isinstance(exc, asyncio.CancelledError)` path is either reachable or deleted.
- No set with no producer remains on `AgentContext`.

## Testing Expectations
- Regression test: create a background task through the real `ConversationStateManager`, run
  `close_resources()`, assert the task is cancelled.
- Regression test: `on_task_done` invoked on a cancelled task completes without raising and discards it.
- Mutation check: emptying the wrong set must fail a test.
- `uv run pytest tests/agent -q`, `uv run ruff check scripts/agent`,
  `uv run mypy --no-namespace-packages scripts/agent`.

## Documentation Impact
Document background-task ownership: who creates them, who tracks them, who cancels them, and what happens
at shutdown. Record the current silent skip as a Known Issue until fixed.

## Out of Scope
- Which operations should be backgrounded at all.
- The shutdown coordinator's timeouts and subprocess termination (`shutdown003`).

## Dependencies
- The `try/finally` turn bracket in `turn004` is where a coherent shutdown/cancel point belongs; review
  the two together.

## Unresolved Questions
- Should `TurnState.background_tasks` be the single source, or should the coordinator receive the set
  explicitly (constructor injection)? Needs confirmation against `skills/DESIGN.md` import-layer rules.
- Should a cancelled-by-user task count as a failure for the pause threshold? Needs confirmation.

## AI Implementation Instruction
Do not add a second registry. Choose one owner, wire it explicitly instead of via `hasattr`, and make
every callback path total (no exception escaping a done-callback).

## Traceability
- **Workflow phase**: `python-code-review` (turn orchestration review), filed via `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261021-093421
- **Related target files**: `scripts/agent/orchestrator.py`, `scripts/agent/bg_task_monitor.py`,
  `scripts/agent/conversation_state_manager.py`, `scripts/agent/resource_shutdown_coordinator.py`,
  `scripts/agent/context.py`
