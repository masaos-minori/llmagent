# Procedure: `tests/agent/workflow/test_workflow_state_store.py`

Stage-2 output for Issue 20261024-105743 / Plan 20261025-090841. Source plan: `plans/20261025-090841_workflow001_state-store-create-task-duplicates-the-composite-idempotency-key.md`. Frozen decisions are copied from the plan; this procedure does not re-decide any of them.

**Row:** 2 of 2, Type `Test`, Path `tests/agent/workflow/test_workflow_state_store.py`, Action `Modify`, Size `S`, Depends on nothing (this file lands first — plan Phase 1, TDD red)

## File Scope

- Add exactly one test method to the existing `TestCreateTask` class. No other test, fixture, or import changes.
- No new file, no conftest change.

## Pre-Change State

Verified 2026-10-25 (Step 3a):
- `tests/agent/workflow/test_workflow_state_store.py` holds 29 `def test_` cases; `uv run pytest tests/agent/workflow -q` reports **91 passed** (baseline).
- `store` fixture (`:58-65`): builds a real `StateStore` on a `tmp_path` workflow DB via `patch("db.helper.build_db_config", ...)`; the DB is retained for the whole test — both wrapper calls in the new test hit the same file.
- `TestCreateTask` at `:68`; all its existing cases call `task_ops.create_task(store._db, ...)`, none calls `store.create_task` (plan claim re-confirmed repo-wide: no `.create_task(` callers on a StateStore instance).
- `import uuid` and `import sqlite3` already present (`:8`, `:10`); `create_task` from `agent.workflow.task_ops` already imported (`:18`) — no new import is needed for the new test.
- Test name `test_state_store_create_task_issues_unique_keys` does not exist (grep confirmed).
- Existing `TestCreateTask` fixture DBs are per-test `tmp_path` — the new test's `"X"` session_id cannot collide with other tests.

## Frozen Decisions (from the plan, copied not re-decided)

- REQ-004 / AC-3: two `store.create_task("X", 1, "1.0.0", "wf-test")` calls on the same `store` fixture; assert no exception, `uuid.UUID(key)` parses for both keys, the keys differ, and neither equals `"X:1"`.
- Plan Tests section: red before doc0001's delegation lands (fails with `sqlite3.IntegrityError` on the second call — that failure is the expected Phase 1 result, not a defect in this test).
- Mutation check is part of AC-3 and is executed against a scratch copy (see doc0001's Validation Commands), not committed.
- Out-of-scope: existing assertions must not change (AC-5: "no existing assertion changed").

## Implementation Procedure

Append to `TestCreateTask` (after the last existing case in the class):

```python
    def test_state_store_create_task_issues_unique_keys(self, store) -> None:
        first = store.create_task("X", 1, "1.0.0", "wf-test")
        second = store.create_task("X", 1, "1.0.0", "wf-test")
        uuid.UUID(first.idempotency_key)
        uuid.UUID(second.idempotency_key)
        assert first.idempotency_key != second.idempotency_key
        assert first.idempotency_key != "X:1"
        assert second.idempotency_key != "X:1"
```

Notes:
- `uuid.UUID(...)` raising `ValueError` is itself a failing assertion; no try/except wrapper is wanted (the composite form `X:1` must make the test fail, not error differently — the two explicit `!= "X:1"` asserts give the diagnostic message).
- `store.create_task` is called on the fixture object, not the imported `task_ops.create_task` — the test's whole point is covering the wrapper (plan Background: the wrapper is untested today).
- Phase 1 red check before doc0001 lands: the second call raises `sqlite3.IntegrityError` under the current composite branch; confirm this is the failure reason in the pytest output (`--tb=short` shows it).

## Validation Commands

```bash
uv run pytest tests/agent/workflow -q                     # Phase 1: 91 passed + 1 failed (IntegrityError); Phase 2+: 92 passed
uv run pytest tests/agent/workflow/test_workflow_state_store.py::TestCreateTask::test_state_store_create_task_issues_unique_keys -v   # single-case run
uv run pytest -v                                          # full suite: no new failure (plan Validation plan, "Whole change" row)
```

## Risk & Impact

- Blast radius: one test method; existing 91 tests untouched.
- False-green risk (plan Risk 4): the test could pass for the wrong reason if UUIDs came from elsewhere — the mutation check (doc0001) restores the composite branch in a scratch copy and requires this test to fail.
- Hidden coupling: the test signature `store.create_task("X", 1, "1.0.0", "wf-test")` pins the wrapper's positional order `(session_id, turn_number, workflow_version, workflow_id)`; REQ-002 keeps that order fixed, so the pin is safe.

## Scope Decisions

- In: one new method in `TestCreateTask`. Out: characterization tests for other `StateStore` methods, any change to `task_ops` tests (they already cover the UUID rule via the closed plan's tests).

## Definition of Done

- Phase 1: test present and red with `sqlite3.IntegrityError` reason recorded. Phase 2: 92 passed in `tests/agent/workflow`, full suite green, mutation check confirms the test fails against a composite-branch scratch copy.
