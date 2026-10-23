## Goal

Make `tests/agent/workflow/test_workflow_state_store.py` assert the new globally-unique `idempotency_key` (UUID4) instead of the removed `f"{session_id}:{turn_number}"` composite key, and add the cross-restart regression the issue requires (`plans/20261023-084918_plan.md`).

## Scope

`tests/agent/workflow/test_workflow_state_store.py`: migrate `TestCreateTask` / `TestUpdateTaskStatus` off the literal `"sess1:1"` / `"sess2:5"` keys, replace `test_idempotency_key_unique` with the cross-run regression, add the retained-DB compatibility case, and keep the `tmp_path` fixtures.

## Assumptions

- The production `create_task()` change (doc 1) assigns `idempotency_key = str(uuid.uuid4())` unconditionally, so every returned `task.idempotency_key` parses as a UUID4.
- `uuid` is not yet imported in this file; add it.
- The raw-SQL seeded rows in `TestRecoverStaleAttempts` / `TestStaleRecoveryConcurrency` use their own `f"{task_id}:1"` keys and assert only attempt status; they are unaffected by this change and stay byte-identical.

## Design decisions

- Assert `uuid.UUID(task.idempotency_key)` parses and differs from the old literal rather than pinning a specific value — the key is random, so only its format and uniqueness are contract.
- The cross-run regression inserts the same `(session_id, turn_number)` twice on one retained connection, mirroring two process runs against a retained `workflow.sqlite` (AC-1).

## Alternatives considered

N/A: single-file, test-only change with no public-contract, persistence, or security impact; several methods are affected so the full form is used rather than the lightweight one-liners.

## Implementation
### Target file
`tests/agent/workflow/test_workflow_state_store.py`

### Procedure
1. Add `import uuid` to the top-of-file imports (after `import sqlite3`).
2. In `TestCreateTask.test_create_returns_task_record` (`:67-73`): replace `assert task.idempotency_key == "sess1:1"` with a format + non-literal assertion.
3. Replace `TestCreateTask.test_idempotency_key_unique` (`:75-78`, asserts today's collision) with `test_same_session_turn_across_runs_no_collision` (`T-1`).
4. In `TestCreateTask.test_get_by_idempotency_key` (`:80-84`): look up `original.idempotency_key` instead of the literal `"sess2:5"`.
5. In `TestUpdateTaskStatus.test_update_status` (`:97-102`): look up `task.idempotency_key` instead of the literal `"sess1:1"`.
6. Add `TestCreateTask.test_retained_db_compatibility` (`T-3`): seed a raw-SQL `tasks` row carrying an old composite-style key, then `create_task()` normally on the same file, and confirm both rows remain readable.

### Method
- Do not touch any other test method. The `store` fixture (`tmp_path`-scoped) and the `patch("db.helper.build_db_config", ...)` pattern stay as-is (AC-6).
- `T-3`'s raw insert must supply all NOT NULL columns; reuse the column shape of the existing `_insert_task_and_attempt` helper at `:232-240` (created_at/updated_at rely on their DEFAULTs).
- Every existing assertion about task status, attempt counts, and event processing stays byte-identical (characterization anchor).
- `T-3` uses `get_task_by_id`, so import it alongside `get_task_by_idempotency_key` at the top.

### Details
Replace `:73`:
```python
        assert task.idempotency_key == "sess1:1"
```
with:
```python
        assert uuid.UUID(task.idempotency_key)  # UUID4, not a composite
        assert task.idempotency_key != "sess1:1"
```

Replace `:75-78`:
```python
    def test_idempotency_key_unique(self, store) -> None:
        create_task(store._db, "sess1", 1, "1.0.0", "wf-test")
        with pytest.raises(sqlite3.IntegrityError):
            create_task(store._db, "sess1", 1, "1.0.0", "wf-test")
```
with:
```python
    def test_same_session_turn_across_runs_no_collision(self, store) -> None:
        """T-1 / AC-1: two simulated runs with the same (session, turn) must not collide."""
        t1 = create_task(store._db, "sess1", 1, "1.0.0", "wf-test")
        t2 = create_task(store._db, "sess1", 1, "1.0.0", "wf-test")
        assert t1.idempotency_key != t2.idempotency_key
        assert uuid.UUID(t1.idempotency_key)
        assert uuid.UUID(t2.idempotency_key)
```

Replace `:82`:
```python
        found = get_task_by_idempotency_key(store._db, "sess2:5")
```
with:
```python
        found = get_task_by_idempotency_key(store._db, original.idempotency_key)
```

Replace `:100`:
```python
        found = get_task_by_idempotency_key(store._db, "sess1:1")
```
with:
```python
        found = get_task_by_idempotency_key(store._db, task.idempotency_key)
```

Add `test_retained_db_compatibility` inside `TestCreateTask` (`T-3` / AC-4):
```python
    def test_retained_db_compatibility(self, store) -> None:
        """T-3 / AC-4: a pre-existing composite-key row stays readable after a normal insert."""
        old_key = ":0"
        store._db.execute(
            "INSERT INTO tasks (task_id, session_id, turn_number, idempotency_key, status, workflow_version, workflow_id) VALUES (?, ?, ?, ?, ?, ?, ?)",
            ("old-task", "sess-old", 0, old_key, "pending", "1.0.0", "wf-old"),
        )
        store._db.commit()
        fresh = create_task(store._db, "sess-new", 1, "1.0.0", "wf-new")
        old_row = get_task_by_idempotency_key(store._db, old_key)
        assert old_row is not None
        assert old_row.task_id == "old-task"
        assert get_task_by_id(fresh.task_id).task_id == fresh.task_id
```

## Compatibility considerations
- `get_task_by_idempotency_key` / `get_task_by_id` signatures are unchanged and stay exercised (REQ-004, REQ-005).
- Pre-existing composite-key rows remain readable via `T-3` (REQ-004).
- `M-2` characterization suites (`test_orchestrator.py`, `test_workflow_stage_persistence.py`, `test_state_store.py`, `test_workflow_models.py`) pass unmodified.

## Security considerations
N/A: test-only change, handles no secret.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `grep -n '"s:1"\|"sess1:1"' tests/agent/workflow/` returns no match (AC-6).
- `uv run pytest tests/agent/workflow/test_workflow_state_store.py -q` passes with `T-1`..`T-3` (AC-1, AC-4).
- Mutation check `T-4`: restoring the composite branch in a scratch copy fails `T-1` and `T-2`.
- Full sequence per `rules/toolchain.md` (ruff, mypy `--no-namespace-packages`, bandit, lint-imports, pre-commit) — AC-8.

## Completion criteria
- No test asserts the `"sess1:1"` / `"s:1"` literal format.
- The cross-run regression passes and the two keys differ and each parses as UUID4.
- A pre-populated composite-key row remains readable through both lookup functions.
- `T-1`..`T-3` pass and the mutation check `T-4` fails when the composite branch is restored.

## Out of Scope
- `test_workflow_engine.py` literal-key migration — separate target file (doc 3).
- Production `create_task()` change — separate target file (doc 1).
- Schema / `WORKFLOW_SCHEMA_VERSION` and any row migration — REQ-004.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Migrate TestCreateTask / TestUpdateTaskStatus, add T-1 and T-3 |
| 2 | Add or update tests per Validation plan | Pending | — | — | Cross-restart regression + retained-DB case |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | Including grep guard and mutation check |

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
- **Requirement ID**: REQ-003, REQ-007
- **Source issue**: `issues/20261021-093421_turn001_task-idempotency-key-collides-across-restarts.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261023-084918_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261024-074027
- **Related target files**: `tests/agent/workflow/test_workflow_state_store.py`
