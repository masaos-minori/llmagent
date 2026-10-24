# Implementation Procedure: `tests/agent/workflow/test_workflow_state_store.py` — key contract and cross-restart regression

## Goal

Replace the tests that pin the composite `idempotency_key` format with tests that pin the UUID4
contract and the cross-restart case (`REQ-007` — coverage for the new key semantics; `REQ-003` — two
identical `(session_id, turn_number)` inserts must not raise). These tests are written first and
observed red, then turned green by
`implementations/20261024-101738_01_scripts_agent_workflow_task_ops.py.md`.

## Scope

- `TestCreateTask` (`:66-93`) and `TestUpdateTaskStatus` (`:96-102`): migrate three literal-key sites
  and swap one test.
- One new class with one new test for the retained-database case (`T-3`).
- Two import lines.
- Fixtures `workflow_db` (`:36`) and `store` (`:57`) are reused unchanged; no test touches `/opt/llm`
  (`tests/conftest.py` isolation guard).

## Assumptions

- The file holds 28 tests at HEAD (`uv run pytest tests/agent/workflow/test_workflow_state_store.py -q`
  → 28 passed). After this procedure it holds 29: 27 kept, `test_idempotency_key_unique` deleted, two
  added.
- Before the production edit the expected result is `2 failed, 27 passed`: the new collision test fails
  with `sqlite3.IntegrityError` (the live defect) and `test_create_returns_task_record` fails its
  UUID-format assertion.

## Design decisions

- The collision test is replaced, not kept alongside: `test_idempotency_key_unique` (`:75-78`) asserts
  the behavior being removed, and the new test still exercises the UNIQUE constraint through two
  inserts on the same retained file (`REQ-004`).
- Assertions test the key's *shape* (parses as a UUID, differs between two identical calls) instead of
  a literal string, so no test depends on key derivation again.

## Alternatives considered

- Keep `test_idempotency_key_unique` and mark it `xfail`: rejected — it would keep a green suite that
  documents the defect, and `AC-6` requires no test to assert the composite format.

## Implementation

### Target file

`tests/agent/workflow/test_workflow_state_store.py`

### Procedure

1. Add `uuid` to the stdlib import block after `import time` (`:10`) and add `get_task_by_id` to the
   `agent.workflow.task_ops` import list (`:18-22`); the list order becomes `create_task`,
   `get_task_by_id`, `get_task_by_idempotency_key`, `update_task_status`.
2. Rewrite the key assertion in `test_create_returns_task_record` (currently `:73`).
3. Delete `test_idempotency_key_unique` (`:75-78`) and add
   `test_same_session_turn_across_runs_no_collision` (new) in its position.
4. Change `test_get_by_idempotency_key` (`:80-84`) to look up the key returned by the create call.
5. Change the lookup in `test_update_status` (currently `:100`) the same way.
6. Add `TestRetainedDatabaseCompatibility` (new) with
   `test_retained_db_keeps_old_composite_key_readable` (new) between `TestUpdateTaskStatus` (ends at
   `:102`) and `class TestAttempts` (`:105`).
7. Run the file and record the red state, then apply row 1 and re-run to green.

### Method

```python
import sqlite3
import threading
import time
import uuid
from pathlib import Path
```

```python
from agent.workflow.task_ops import (
    create_task,
    get_task_by_id,
    get_task_by_idempotency_key,
    update_task_status,
)
```

```python
        assert task.status == "pending"
        uuid.UUID(task.idempotency_key)
        assert task.idempotency_key != "sess1:1"
```

```python
    def test_same_session_turn_across_runs_no_collision(self, store) -> None:
        """T-1: two simulated runs may insert the same (session_id, turn_number).

        Mutation anchor T-4: re-adding the composite branch in task_ops.py makes the
        second insert raise sqlite3.IntegrityError.
        """
        first = create_task(store._db, "X", 1, "1.0.0", "wf-test")
        second = create_task(store._db, "X", 1, "1.0.0", "wf-test")

        assert first.idempotency_key != second.idempotency_key
        uuid.UUID(first.idempotency_key)
        uuid.UUID(second.idempotency_key)
```

```python
class TestRetainedDatabaseCompatibility:
    def test_retained_db_keeps_old_composite_key_readable(self, store, workflow_db) -> None:
        """T-3: a row written before the change coexists with a UUID-keyed row."""
        conn = sqlite3.connect(str(workflow_db))
        conn.execute(
            "INSERT INTO tasks (task_id, session_id, turn_number, idempotency_key, status, workflow_version, workflow_id, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            ("task-old", "sess1", 0, ":0", "completed", "1.0.0", "wf-old", "now", "now"),
        )
        conn.commit()
        conn.close()

        new = create_task(store._db, "sess1", 0, "1.0.0", "wf-test")

        old = get_task_by_idempotency_key(store._db, ":0")
        assert old is not None
        assert old.task_id == "task-old"
        assert old.status == "completed"
        fetched = get_task_by_id(store._db, new.task_id)
        assert fetched is not None
        assert fetched.idempotency_key == new.idempotency_key
```

### Details

- `pytest.raises(sqlite3.IntegrityError)` at `:77` is the only use of that call form in the file; the
  `sqlite3` import stays used by the raw-seed pattern at `:383`, `:433`, `:474` and `:532`, so no
  import is left dangling.
- `test_get_by_idempotency_key_missing` (`:86-87`) and `test_create_task_without_session_id`
  (`:89-93`) assert no key format and stay byte-identical. `nosuchkey` is not a composite-format
  assertion and is not covered by the `AC-6` grep guard.
- The T-3 seed mirrors the file's existing raw-connection seeding rather than calling `create_task()`,
  because the point of the case is a row the old code wrote.
- `T-4` is a scratch-copy mutation check, not a committed test: restore the branch in a temporary copy
  of `scripts/agent/workflow/task_ops.py`, re-run this file, expect `T-1` and `T-2` to fail, then
  restore. Its anchor is recorded in the docstring above.

## Compatibility considerations

- `AC-6` guard after the edit: `grep -n '"s:1"\|"sess1:1"' tests/agent/workflow/` returns no match.
- `TestAttempts` (`:105`), `TestIdempotency` (`:140`), `TestArtifacts` (`:162`),
  `TestDiagnosticQueries` (`:172`), `TestStateStoreGetConnection` (`:218`), `TestRecoverStaleAttempts`
  (`:227`) and `TestStaleRecoveryConcurrency` (`:461`) are untouched; `tests/agent/workflow/test_workflow_stage_persistence.py:29`
  seeds its own literal keys and must keep passing unmodified (`M-2`).

## Security considerations

N/A: test-only change; the fixture stays `tmp_path`-scoped and no credential or path outside
`tmp_path` is touched.

## Rollback considerations

- Revert this file's commit. Nothing else depends on the new tests, and the pre-existing suite is
  green at HEAD 28 passed.

## Validation plan

- Red phase: `uv run pytest tests/agent/workflow/test_workflow_state_store.py -q` → `2 failed, 27 passed`.
- Green phase after row 1: the same command → `29 passed`.
- Mutation check `T-4` → `test_same_session_turn_across_runs_no_collision` (new) and
  `test_create_returns_task_record` fail with the branch restored.
- `grep -n '"s:1"\|"sess1:1"' tests/agent/workflow/` → no match after both test rows land (`AC-6`).
- `uv run pytest tests/agent/workflow -q` → 92 passed (baseline 90, net +2 tests).
- `uv run ruff format tests/agent/workflow/test_workflow_state_store.py`, `uv run ruff check tests/agent/workflow/test_workflow_state_store.py`
  → no finding (import order: stdlib block then `agent.workflow.*`).

## Completion criteria

- No assertion in this file compares `idempotency_key` to a composed string, and every lookup uses a
  key returned by `create_task()`.
- The cross-run regression case exists and fails if the composite derivation returns (`AC-1`, `T-4`).
- The retained-database case proves an old `":0"` row is still readable beside a new row (`AC-4`).
- The file reports 29 passed with the production change applied.

## Out of Scope

- `scripts/agent/workflow/task_ops.py` — owned by
  `implementations/20261024-101738_01_scripts_agent_workflow_task_ops.py.md`.
- `tests/agent/workflow/test_workflow_engine.py` — owned by
  `implementations/20261024-101738_03_tests_agent_workflow_test_workflow_engine.py.md`.
- `scripts/agent/workflow/state_store.py` and the composite branch inside its `create_task` wrapper
  (`state_store.py:55-58`): a Reference Files row of this Plan, uncalled in `scripts/` and `tests/`,
  and outside this Plan's frozen edit scope. No test in this Plan calls `StateStore.create_task`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Author `T-1`..`T-3` and migrate the literal-key sites | Pending | — | — | Land before row 1 |
| 2 | Record the red run (`2 failed, 27 passed`) | Pending | — | — | Evidence for plan step 1 |
| 3 | Run the validation sequence after row 1 lands | Pending | — | — | 29 passed expected |
| 4 | Run the `T-4` mutation check and restore the scratch copy | Pending | — | — | Plan step 3 |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-003` (no collision across simulated runs), `REQ-007` (test coverage and
  literal-key migration)
- **Source issue**: `issues/20261021-093421_turn001_task-idempotency-key-collides-across-restarts.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261023-084918_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261024-101738
- **Related target files**: `tests/agent/workflow/test_workflow_state_store.py`
