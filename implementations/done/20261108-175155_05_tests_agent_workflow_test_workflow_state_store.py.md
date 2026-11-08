## Goal
Retarget the 11 `recover_stale_attempts` call sites in `tests/agent/workflow/test_workflow_state_store.py` (10 pass `s._db`, 1 passes `s.get_connection()`) to no-argument calls, and add facade delegation tests proving the new `StateStore.begin_stage_if_new`/`StateStore.record_artifact` methods produce the same rows as the ops functions.

## Scope
**Release unit**: wfaudit015-full (retargets must land with document 01's signature change; the delegation tests pin document 01's REQ-001 acceptance).

**Plan row implemented**: `plans/20261108-084011_wfaudit015_state-store-facade-bypass.md` Implementation Target Files row 5 (`tests/agent/workflow/test_workflow_state_store.py`, `REQ-001`/`REQ-002`/`REQ-005`; plan step 2).

**In scope**:
- Argument removal at every `recover_stale_attempts` call site in this file (11 at HEAD `ad48bfa28`: `s.recover_stale_attempts(s._db)` at L328, L347, L365, L389, L416, L438, L498, L544, L586, L625; `s.recover_stale_attempts(s.get_connection())` at L674).
- Two new delegation tests in the `store`-fixture class: `test_store_facade_begin_stage_if_new_delegates` (new) and `test_store_facade_record_artifact_delegates` (new).

**Out of scope**:
- `test_get_connection_returns_same_instance_as_private_attribute` (L271-275) — the identity test for `get_connection()` stays green unchanged (method kept).
- The existing ops-level tests `test_begin_stage_if_new_returns_attempt`, `test_begin_stage_if_new_skips_duplicate`, `test_event_processed_after_begin`, `test_record_artifact` (regression locks; unchanged except where wfaudit009 retargets them first).
- Lease/recovery assertion semantics in this file.

**Dependencies (landing order)**: `implementations/20261108-170505_05_tests_agent_workflow_test_workflow_state_store.py.md` (wfaudit009) lands first and may add further `recover_stale_attempts` call sites with connection arguments; this procedure converts every call site present at execution time, pattern-anchored.

## Assumptions
| ID | Assumption | Validation |
|---|---|---|
| A-001 | All 11 sites pass the store's own connection (10 directly via `s._db`, 1 via `s.get_connection()`), so removal is behavior-preserving. | Verified (site census at `ad48bfa28`) |
| A-002 | The `store` fixture (class-level `@pytest.fixture()`) and `_open_store` helper already provide real-DB stores suitable for delegation assertions. | Verified (fixture at L78-85, helper pattern at L316-318) |

## Design decisions
| ID | Decision | Rationale |
|---|---|---|
| D-001 | Delegation tests assert through observable store state (returned dataclass type, `processed_events` idempotency, `get_artifact_uris` output) instead of spying on the ops functions. | The contract to pin is "same rows out of the same DB", not "which function was called"; state assertions survive ops refactors. |
| D-002 | New tests go directly after their ops-level twins (`test_begin_stage_if_new_skips_duplicate` after-block and `test_record_artifact` after-block). | Keeps facade and ops tests adjacent for direct comparison in review. |
| D-003 | Convert `s._db` and `s.get_connection()` variants with two exact pattern replace-alls. | Both patterns are unique call shapes; no per-line judgment needed. |

## Alternatives considered
| Alternative | Reason rejected |
|---|---|
| Delete the ops-level tests and test only the facade | They are the regression lock for ops semantics (plan Tests section: "existing idempotency duplicate-insert ... stay green"). |
| Assert delegation via `unittest.mock.patch` on the ops functions | Brittle against module-qualified import shape; state-based assertions test the user-visible contract. |

## Implementation
### Target file
`tests/agent/workflow/test_workflow_state_store.py` (plan target row 5).

### Procedure
Step 1: replace-all the `s._db` call variant. Step 2: replace the `s.get_connection()` call variant. Step 3: add the two delegation tests.

### Method
Pattern replace-all for steps 1-2 (HEAD reference: 10 and 1 occurrences). Symbol-anchored insertion for step 3.

### Details
Step 1 — replace every occurrence of:
```python
s.recover_stale_attempts(s._db)
```
with:
```python
s.recover_stale_attempts()
```

Step 2 — replace the occurrence (HEAD L674):
```python
s.recover_stale_attempts(s.get_connection())
```
with:
```python
s.recover_stale_attempts()
```

Step 3 — insert `test_store_facade_begin_stage_if_new_delegates` (new) in the begin-stage test class directly after `test_event_processed_after_begin` (HEAD L208-212), mirroring its use of the module-level `create_task` helper and the `store` fixture:
```python
    def test_store_facade_begin_stage_if_new_delegates(self, store) -> None:
        """StateStore.begin_stage_if_new produces the same rows as the ops function."""
        task = create_task(store._db, "s", 1, "1.0.0", "wf-test")
        first = store.begin_stage_if_new("evt-1", task.task_id, "plan")
        assert isinstance(first, AttemptRecord)
        second = store.begin_stage_if_new("evt-1", task.task_id, "plan")
        assert second is None
        assert is_event_processed(store._db, "evt-1") is True
```
Insert `test_store_facade_record_artifact_delegates` (new) in `TestArtifacts` directly after `test_record_artifact` (HEAD L215-224), mirroring its task creation and field assertions:
```python
    def test_store_facade_record_artifact_delegates(self, store) -> None:
        """StateStore.record_artifact produces the same rows as the ops function."""
        task = create_task(store._db, "s", 1, "1.0.0", "wf-test")
        ref = store.record_artifact(task.task_id, "execute", "file:///tmp/facade.json")
        assert isinstance(ref, ArtifactRef)
        assert ref.task_id == task.task_id
        assert ref.uri == "file:///tmp/facade.json"
        assert "file:///tmp/facade.json" in store.get_artifact_uris(task.session_id)
```

Extend the file's imports: add `AttemptRecord` and `ArtifactRef` to the `agent.workflow.models` import (the file already imports `begin_stage_if_new`, `is_event_processed`, `record_artifact`, and `create_task` for the ops-level twins).

## Compatibility considerations
- Recovery assertions (`count == 1`, live-lease skip, unparseable report) are unchanged; only the call shape changes (REQ-004 lock preserved).
- `get_connection()` identity test continues to pass (method not deleted).

## Security considerations
N/A (test-only change).

## Rollback considerations
Revert with the wfaudit015-full unit.

## Validation plan
Run after documents 01-08 have landed (unit gate):
| Gate | Command | Expectation |
|---|---|---|
| Store suite | `uv run pytest tests/agent/workflow/test_workflow_state_store.py -q` | all green incl. the two new delegation tests |
| Delegation detail | `uv run pytest tests/agent/workflow/test_workflow_state_store.py -q -k facade` | 2 tests pass |
| Pattern audit | `grep -c "recover_stale_attempts(s._db)" tests/agent/workflow/test_workflow_state_store.py` | 0 |
| Lint | `uv run ruff check tests/agent/workflow/test_workflow_state_store.py` | clean |

## Completion criteria
- Zero argument-carrying `recover_stale_attempts` calls remain in this file (REQ-002).
- Both delegation tests pass and prove identical rows/idempotency against the ops-level twins (REQ-001/REQ-005).
- The `get_connection()` identity test still passes (method retained).

## Out of Scope
- The facade methods themselves (document 01).
- Engine/orchestrator routing tests (documents 07-08).
- `get_connection()` deletion (`UNK-01`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Replace the `s._db` and `s.get_connection()` call variants with no-argument calls | Completed | 20261109 | 20261109 | All 11 sites now `s.recover_stale_attempts()`; ruff clean |
| 2 | Add the two facade delegation tests | Completed | 20261109 | 20261109 | Inserted after `test_event_processed_after_begin` and `test_record_artifact`; import symbol order auto-fixed by ruff (ArtifactRef, AttemptRecord) |
| 3 | Run the unit validation gates (valid only after documents 01-08 land) | Completed | 20261109 | 20261109 | End-of-unit suite: 4220 passed, 3 skipped, 0 failures |

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
- **Requirement ID**: `REQ-001`, `REQ-002`, `REQ-005`
- **Source issue**: `issues/20261107-203228_wfaudit015_state-store-facade-bypass.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261108-084011_wfaudit015_state-store-facade-bypass.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261108-175155
- **Related target files**: `tests/agent/workflow/test_workflow_state_store.py`

<!-- tools/generate_workitem.py implementation-procedure timestamp: 20261108-175155 -->
