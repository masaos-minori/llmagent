## Goal
Move the three attempt creations in `test_workflow_stage_persistence.py` from the test-only `attempt_ops.start_attempt` onto the production writer `begin_stage_if_new`, keeping every persisted-column assertion identical (`REQ-002`).

## Scope
**Release unit**: wfaudit009-full

- Covers Plan `plans/20261108-084010_wfaudit009_test-only-state-helpers.md` row 7 only: `tests/agent/workflow/test_workflow_stage_persistence.py`.
- This is a Phase 1 (plan step 1) document: the edits land while `start_attempt` still exists; the suite must be green with helpers present before document 01 deletes it (equivalence gate).

## Assumptions
- Call sites re-verified at HEAD `ad48bfa28`: import L11 (`finish_attempt`, `start_attempt` from `agent.workflow.attempt_ops`); creations at L42 (`test_finish_attempt_persists_error_kind`), L61 (`test_finish_attempt_null_error_kind_by_default`), L73 (`test_finish_attempt_exception_kind`), each `rec = start_attempt(db, task_id, "stage1")` followed by `finish_attempt(db, rec.attempt_id, ...)` and row-column asserts.
- `begin_stage_if_new` is already imported at L12; the `db` fixture (L15-21) is a fresh per-test `:memory:` `SQLiteHelper`, so event ids chosen below collide with nothing, and `_insert_task` (L24) supplies `task_id` unchanged.
- The two tests further down the file already use `begin_stage_if_new` (`test_begin_stage_if_new_persists_workflow_id`, `test_begin_stage_if_new_idempotent`) — proof that the retarget path exercises the same `attempts` columns; they are not edited by this document.

## Design decisions
- Retarget the creation, keep the assertion: these tests pin `finish_attempt`'s `error_kind`/`error_detail` persistence, which is writer-independent; swapping the INSERT path preserves the observable outcome because both writers insert the same `attempts` columns (the near-duplicate the plan collapses).
- Event ids are literal stage-pair strings (`"evt-ep-1"`, `"evt-ep-2"`, `"evt-ep-3"`), one per test, mirroring the engine's `task:stage:attempt` id shape rather than the (task, stage) pair `start_attempt` keyed on.

## Alternatives considered
- Passing `lease_duration_sec` in these creations: rejected — the tests are about `finish_attempt` columns; lease stamping coverage is added once, in document 04, to avoid duplicating the same branch in three files.

## Implementation
### Target file
`tests/agent/workflow/test_workflow_stage_persistence.py`

### Procedure
Three seed swaps plus one import prune.

### Method
1. Import (L11): `from agent.workflow.attempt_ops import finish_attempt, start_attempt` -> `from agent.workflow.attempt_ops import finish_attempt`.
2. L42 -> `rec = begin_stage_if_new(db, "evt-ep-1", task_id, "stage1")`; L61 -> event id `"evt-ep-2"`; L73 -> event id `"evt-ep-3"` (same stage/stage literal). After each creation add `assert rec is not None` (the return type is `AttemptRecord | None`) before the existing `finish_attempt(db, rec.attempt_id, ...)` call.
3. All downstream asserts (`error_kind`, `error_detail`, `row[0]`/`row[1]` column reads) stay byte-identical.

### Details
- `begin_stage_if_new` inserts `status='running'` with `started_at` stamped by the production clock and lease columns NULL when `lease_duration_sec` is omitted — the same row shape `start_attempt` produced lease-less, which is what these tests consumed.
- The module-level `uuid` import (L6) is used by `_insert_task` and stays.

## Compatibility considerations
- Behavior-preserving: per-test in-memory DB, identical task setup, identical finish assertions; only the attempt-insert entry point changes.
- No sibling test file imports anything from this file.

## Security considerations
- None.

## Rollback considerations
- Revert this document alone: HEAD calls compile until document 01 deletes `start_attempt` in plan step 2.

## Validation plan
- Phase 1 equivalence gate: `uv run pytest tests/agent/workflow/test_workflow_stage_persistence.py -q` green with `start_attempt` still present.
- After deletion (plan step 2): the same file green; REQ-001 grep shows no `start_attempt` matches in the file; full `uv run pytest tests/ -q` and lint gates per `rules/toolchain.md`.

## Completion criteria
- Zero `start_attempt` references in the file; the three error-kind/error_detail assertions keep their HEAD meanings; the suite is green.

## Out of Scope
- Deleting `start_attempt` itself (document 01).
- Lease-stamping regression coverage (document 04).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | the test edits are the implementation; lands before document 01 |
| 2 | Add or update tests per Validation plan | Pending | — | — | merged into step 1: seed swaps are the test updates |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | Phase 1 equivalence gate runs here with helpers still present |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | docs grep verified zero matches; verification-only |

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
- **Requirement ID**: `REQ-002`
- **Source issue**: `issues/20261107-203222_wfaudit009_test-only-state-helpers.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261108-084010_wfaudit009_test-only-state-helpers.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261108-170505
- **Related target files**: `tests/agent/workflow/test_workflow_stage_persistence.py`

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261108-170505 -->
