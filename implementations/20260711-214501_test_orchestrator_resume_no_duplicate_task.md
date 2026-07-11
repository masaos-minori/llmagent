# Implementation Procedure: test_orchestrator.py — resume does not create a duplicate task

Source plan: `plans/20260711-173259_plan.md` — Design §3 / Implementation step 6

## Goal

Add the one genuine test gap this plan's investigation found: confirm at the `Orchestrator` layer that resuming a workflow task after approval reuses the existing `TaskRecord` (via `get_task_by_id()`) instead of creating a duplicate (`create_task()`), and that `ctx.turn.pending_approval_task_id` is correctly reset to `None` after use.

## Scope

**In:**
- `tests/test_orchestrator.py`: one new test (or a small set) exercising `Orchestrator._init_workflow_task()`'s `existing_task_id is not None` branch.

**Out:**
- No change to `orchestrator.py` itself — the resume-reuse logic is already correctly implemented (`orchestrator.py:257-264` calls `get_task_by_id()`, not `create_task()`, when `existing_task_id is not None`; `orchestrator.py:186-187` resets `ctx.turn.pending_approval_task_id` to `None` immediately after `_init_workflow_task()`). This item is test-only, confirming already-correct behavior.
- No change to `tests/test_workflow_engine.py`'s existing resume tests (`test_resume_does_not_rerun_plan_or_execute`, `test_startup_recovered_approval_can_resume`) — those already cover the engine-level resume path; this new test covers the orchestrator-level task-reuse decision specifically, a different layer.

## Assumptions

1. Confirmed via the plan's Out-of-Scope section and Design §3: `Orchestrator._init_workflow_task()`'s `existing_task_id is not None` branch (`orchestrator.py:257-264`) already calls `get_task_by_id()` instead of `create_task()` — this is a negative finding (already correct), the gap is purely in test coverage.
2. Confirmed via direct read of `orchestrator.py:186-187`: `ctx.turn.pending_approval_task_id` is reset to `None` immediately after `_init_workflow_task()` is called inside `_handle_workflow_engine()`.
3. `agent/workflow/task_ops.py` (`get_task_by_id()`, `create_task()`, `update_task_status()`) requires no code change (plan Assumption 4) — these are exercised as-is by the new test via mocking/spying, not modified.

## Implementation

### Target file

`tests/test_orchestrator.py`

### Procedure

1. Set up a test fixture with an existing `TaskRecord` already persisted (or mocked via the existing test file's established patterns for constructing an `Orchestrator` instance and its `AgentContext`).
2. Set `ctx.turn.pending_approval_task_id` to that existing task's `task_id`.
3. Call `Orchestrator._init_workflow_task()` directly, or drive it via `_handle_workflow_engine()` with a mocked/stubbed `WorkflowEngine` (choose whichever matches this test file's existing conventions for exercising orchestrator internals — check other tests in the same file for the established pattern before deciding).
4. Assert:
   - `create_task()` is **not** called (spy/mock assertion — no duplicate task created).
   - The returned task's `task_id` matches the pre-existing one (i.e., `get_task_by_id()` was used to fetch/reuse it).
   - After the call, `ctx.turn.pending_approval_task_id` is `None` (reset happened).

### Method

Standard `pytest` unit test using mocking/spying on `task_ops.create_task`/`task_ops.get_task_by_id` (e.g. via `monkeypatch` or `unittest.mock.patch`, matching whichever style this test file already uses elsewhere), plus direct attribute assertions on the `AgentContext`/`TurnContext` object after the call.

### Details

- Match this test file's existing fixture/mocking conventions exactly — read a few existing `Orchestrator`-level tests in `test_orchestrator.py` first to determine whether `_init_workflow_task()` is typically called directly in tests or only exercised indirectly through a higher-level entry point.
- Keep the test narrowly focused on the resume/no-duplicate-task assertion plus the `pending_approval_task_id` reset — do not fold in unrelated assertions about workflow stage execution (that is already covered by the engine-level tests in `test_workflow_engine.py`).

## Validation plan

Filtered from the plan's Validation plan table to checks relevant to this file:

| Check | Tool | Target |
|---|---|---|
| Lint | `uv run ruff check tests/test_orchestrator.py` | 0 errors |
| Type check | `uv run mypy scripts/agent/` (orchestrator.py itself is unchanged, but confirm no regression) | No new errors |
| Tests | `uv run pytest tests/test_orchestrator.py -v` | All pass, including the new resume/no-duplicate-task test |
| Regression | `uv run pytest tests/ -k "approval or workflow" -q` | No new failures |
