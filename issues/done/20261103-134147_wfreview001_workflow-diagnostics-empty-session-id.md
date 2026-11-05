# Workflow session diagnostics always report zero because tasks are written with an empty session_id

## Priority
High

## Summary
The orchestrator calls the workflow adapter's `execute_turn()` with an empty-string `session_id`, so every workflow `tasks` row is persisted with `session_id=''`. The end-of-session diagnostics (`SessionPersister.persist_session_diagnostics`) aggregate workflow statistics by the real chat session id, so `task_count`, `workflow_count`, `execute_attempts`, `retry_count`, and artifact URIs are always 0/empty in production. Fix the wiring so the diagnostic aggregation actually sees the session's workflow rows (or redefine the aggregation so it does not depend on `tasks.session_id`).

## Background
Adversarial code review of `scripts/agent/workflow/` and its integration points (2026-11-03). Evidence:

- Confirmed: `scripts/agent/orchestrator.py:176-178` — `answer, error_kind, is_partial = await self._workflow_adapter.execute_turn(line, turn_started_at, "")` — the third argument (`session_id`) is a hardcoded empty string.
- Confirmed: `scripts/agent/workflow_engine_adapter.py:151-171` — `execute_turn()` passes that `session_id` unchanged into `_init_workflow_task()`, which creates the task with it (`scripts/agent/workflow_engine_adapter.py:300-306`, `create_task(store._db, session_id=session_id, ...)`).
- Confirmed: `scripts/agent/session_persister.py:71-105` — the diagnostics read `session_id = self._ctx.session.session_id` (the chat session id) and call `StateStore.get_task_count(sid)`, `get_workflow_count(sid)`, `get_execute_attempt_count(sid)`, and `get_artifact_uris(sid)`.
- Confirmed: all four queries filter `WHERE session_id=?` against the `tasks` table (`scripts/agent/workflow/state_store.py:174-203`, `scripts/agent/workflow/task_ops.py:107-123`); with `tasks.session_id=''` and `sid` a real session id, every count is 0 and `get_artifact_uris` returns `[]`.
- Confirmed: no production caller ever passes a non-empty `session_id` to `WorkflowEngineAdapter.execute_turn()` or `init_workflow_task()`.
- Confirmed test gap: `tests/agent/workflow/test_workflow_state_store.py:214-244` tests the getters with self-consistent hand-inserted session ids; `tests/agent/test_repl.py:535-596` mocks the getters to 0; `tests/agent/test_session_persister.py` patches `StateStore` entirely. No test exercises the orchestrator→adapter write path together with the persister read path, so the mismatch is invisible to the suite.

## Problem
The persisted `tasks.session_id` and the session id used for diagnostic aggregation never match, so every session diagnostics summary reports `task_count=0`, `workflow_count=0`, `execute_attempts=0`, `retry_count=0`, and an empty artifact list even when workflow turns ran. The session-diagnostics feature (previously maintained, e.g. `issues/done/20260909-130453_repl003_persist-session-diagnostics-tests-patch-wrong-logger-module.md`) is effectively dead data in production.

## Reason for Change
The counters silently report zeros, which is worse than absent data: operators reading `session_diagnostics` conclude no workflow work happened. The mismatch is also a latent trap — `tasks.session_id` is a real column used by four queries, and any future per-session workflow query inherits the same broken wiring.

## Implementation Intent
Pick one of two directions and implement it end-to-end with a regression test that covers the write path and the read path together:
- Wire the real session id through: have the orchestrator pass its session id (the same value `SessionPersister` uses, `ctx.session.session_id`) into `execute_turn()` so `tasks.session_id` carries it, or
- Decouple diagnostics from `tasks.session_id`: aggregate workflow stats by the task ids recorded in the turn result instead of a session filter.
Decide at plan time which contract `tasks.session_id` is meant to hold (chat session id vs unused column) and record the decision.

## Target Files or Areas
- `scripts/agent/orchestrator.py`
- `scripts/agent/workflow_engine_adapter.py`
- `scripts/agent/session_persister.py`
- `scripts/agent/workflow/state_store.py` (diagnostic getters, depending on chosen direction)
- `tests/agent/workflow/`, `tests/agent/test_session_persister.py`

## Required Changes
- Make the `session_id` written into `tasks` and the `session_id` used by `SessionPersister` refer to the same identifier, or remove the dependency of the diagnostic getters on `tasks.session_id`.
- Update `WorkflowEngineAdapter.execute_turn()` callers (currently only `Orchestrator._execute_turn`) to pass a meaningful session id if the wiring direction is chosen.
- Add a regression test that runs a turn through the adapter against a real workflow database and then calls the persister aggregation, asserting non-zero counts.
- Update any docs that describe what `tasks.session_id` contains.

## Constraints
- `tasks.session_id` participates in `REQUIRED_WORKFLOW_TABLES` (`scripts/agent/services/workflow_schema.py`): the column must keep existing; only its populated value or the query key may change.
- Do not change the chat/session persistence layer (`ctx.session`) semantics; the fix must not couple `workflow.sqlite` session identity to chat-log session identity beyond what the chosen contract requires.
- Existing tests that mock or hand-seed session ids (`tests/agent/test_repl.py`, `tests/agent/workflow/test_workflow_state_store.py`) must keep passing or be updated coherently.

## Acceptance Criteria
- A turn executed through `Orchestrator._execute_turn` produces a `tasks` row whose session identity matches what `SessionPersister.persist_session_diagnostics()` queries, in a real-DB test.
- The new regression test fails before the fix and passes after it.
- `uv run pytest tests/agent/workflow tests/agent/test_session_persister.py` and the ruff/mypy/import-linter checks stay green.

## Testing Expectations
- Regression test covering adapter write + persister read against a real (fixture) workflow database — this is the missing coverage that allowed the bug.
- Unit tests for whichever aggregation contract is chosen (non-zero counts, correct `retry_count` arithmetic).
- Lint/type/import-contract checks per `rules/toolchain.md`.

## Documentation Impact
Document what `tasks.session_id` holds and how session diagnostics aggregate workflow activity, in the agent state/persistence doc (`docs/23_agent/agent_04_03_state-and-persistence-platform-databases.md`) and the turn-processing doc if the wiring changes. Update the schema reference if the column's meaning is restated.

## Out of Scope
- Changing `processed_events`, attempt recovery, or task-status semantics (covered by `issues/20261030-105639_wfrecovery001_workflow-recovery-state-machine.md`).
- Renaming or removing the `tasks.session_id` column.
- Chat-log and history session handling.

## Dependencies
- `issues/20261030-105723_wftaskapi001_consolidate-task-persistence.md` (open): if this issue chooses the task-based aggregation direction, its consolidation of task query APIs should be considered to avoid divergent query helpers.

## Unresolved Questions
- 不明: intended semantics of `tasks.session_id` — chat session id, a dedicated workflow session identity, or a column to retire. The plan must choose and record it.
- 不明: whether `ctx.session.session_id` is always non-`None` at turn time in all entry points (REPL, batch), which affects the wiring direction.

## AI Implementation Instruction
Do not "fix" this by making the persister query `session_id=''`; that cements the broken wiring. Choose one contract, implement it in both the write and read paths, and prove it with a real-DB regression test. Keep all existing public signatures unless the plan decides otherwise.

## Traceability
- **Workflow phase**: `python-code-review` (adversarial review of `scripts/agent/workflow/` and integration points), filed via `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261103-134147
- **Related target files**: `scripts/agent/orchestrator.py`, `scripts/agent/workflow_engine_adapter.py`, `scripts/agent/session_persister.py`, `scripts/agent/workflow/state_store.py`, `tests/agent/workflow/`, `tests/agent/test_session_persister.py`
