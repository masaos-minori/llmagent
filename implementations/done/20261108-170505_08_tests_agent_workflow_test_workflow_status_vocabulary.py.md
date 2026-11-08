## Goal
Retarget the single attempt creation in `test_workflow_status_vocabulary.py` from the test-only `attempt_ops.start_attempt` onto the production writer `begin_stage_if_new`, keeping the `finish_attempt` vocabulary-rejection assertions identical (`REQ-002`).

## Scope
**Release unit**: wfaudit009-full

- Covers Plan `plans/20261108-084010_wfaudit009_test-only-state-helpers.md` row 8 only: `tests/agent/workflow/test_workflow_status_vocabulary.py`.
- This is a Phase 1 (plan step 1) document: the edit lands while `start_attempt` still exists; the suite must be green with helpers present before document 01 deletes it (equivalence gate).

## Assumptions
- Call site re-verified at HEAD `ad48bfa28`: import L21 (`finish_attempt`, `start_attempt` from `agent.workflow.attempt_ops`); the only creation is `attempt = start_attempt(store._db, task.task_id, "plan")` at L115 inside `test_finish_attempt_rejects_and_writes_nothing` (class `TestHelperRejection`), followed by the completed write, the out-of-vocabulary `ValueError` assert and the unchanged-row re-read.
- The module header comment (L26-31, "Known writer literals") already lists the attempts writers as `idempotency_ops` INSERT running plus recovery UPDATE failed — it does not name `start_attempt`, so it stays byte-identical and already describes the post-deletion world.
- `begin_stage_if_new` is not yet imported in this file; the import is added (new, below). The `store`/`workflow_db` fixtures are per-test, so the event id below collides with nothing.

## Design decisions
- Seed-only retarget: the test pins `finish_attempt`'s vocabulary guard (wfaudit005 `REQ-002` lineage), which is writer-independent; the creation call is swapped 1:1 and every assertion after it stays byte-identical.
- Import added in file order (between the `attempt_ops` and `models` imports) to keep the existing alphabetical import block: `from agent.workflow.idempotency_ops import begin_stage_if_new` (new).

## Alternatives considered
- Dropping the creation and seeding the row with a raw INSERT: rejected — same reasoning as the plan Design: tests must run the production writer, not a third path.

## Implementation
### Target file
`tests/agent/workflow/test_workflow_status_vocabulary.py`

### Procedure
One seed swap plus an import edit.

### Method
1. Import L21 -> `from agent.workflow.attempt_ops import finish_attempt`, and add `from agent.workflow.idempotency_ops import begin_stage_if_new` (new) after it.
2. L115 -> `attempt = begin_stage_if_new(store._db, "evt-vocab-1", task.task_id, "plan")`; add `assert attempt is not None` (return type is `AttemptRecord | None`) before the existing `finish_attempt(store._db, attempt.attempt_id, "completed")`.
3. Everything after (the `pytest.raises(ValueError, match="invalid attempts.status 'done'")` block and the status re-read asserts) stays byte-identical.

### Details
- The creation stays at stage `plan` with the same task fixture, so the row the vocabulary test finalizes has the same shape as at HEAD (`begin_stage_if_new` inserts `status='running'`, lease columns NULL lease-less).
- The other two rejection tests (`test_update_task_status_rejects_and_writes_nothing`, `test_finalize_tool_call_rejects_and_writes_nothing`) do not create attempts and are untouched.

## Compatibility considerations
- Behavior-preserving per-test fixtures; no sibling test file imports from this file; the writer-literals comment needs no update (it never named the deleted helper).

## Security considerations
- None.

## Rollback considerations
- Revert this document alone: HEAD calls compile until document 01 deletes `start_attempt` in plan step 2.

## Validation plan
- Phase 1 equivalence gate: `uv run pytest tests/agent/workflow/test_workflow_status_vocabulary.py -q` green with `start_attempt` still present.
- After deletion (plan step 2): the same file green; REQ-001 grep shows no `start_attempt` matches in the file; full `uv run pytest tests/ -q` and lint gates per `rules/toolchain.md`.

## Completion criteria
- Zero `start_attempt` references in the file; the out-of-vocabulary rejection and no-write assertions keep their HEAD meanings; the suite is green.

## Out of Scope
- Deleting `start_attempt` itself (document 01).
- The DDL-vs-constants equality test that lives in `tests/db/test_create_schema.py` (module header states it; not a target file).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261109-071047 | 20261109-071047 | the test edit is the implementation; lands before document 01 |
| 2 | Add or update tests per Validation plan | Completed | 20261109-071047 | 20261109-071047 | merged into step 1: seed swap is the test update |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261109-071047 | 20261109-071047 | Phase 1 equivalence gate runs here with helpers still present |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261109-071047 | 20261109-071047 | docs grep verified zero matches; verification-only N/A: no docs/00_index.md task-scope mapping; grep zero matches for deleted helper names |

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
- **Related target files**: `tests/agent/workflow/test_workflow_status_vocabulary.py`

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261108-170505 -->