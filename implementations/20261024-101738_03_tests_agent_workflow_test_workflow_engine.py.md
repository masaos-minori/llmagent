# Implementation Procedure: `tests/agent/workflow/test_workflow_engine.py` — migrate the four literal task-key lookups

## Goal

Remove the four `"s:1"` idempotency-key lookups that depend on the composite format the Plan removes,
without changing any behavior assertion (`REQ-005` — resume and status-transition behavior stays
unchanged; `REQ-007` — migrated literal-key sites).

## Scope

- Four lookup lines: `:94` in `TestWorkflowEngineHappyPath` (class at `:87`), `:125` and `:142` in
  `TestWorkflowEngineRetry` (class at `:109`), `:296` in `TestRunStageWithRetryGeneralization` (class at
  `:231`).
- Nothing else in the file: the twelve tests, their `create_task(store._db, "s", 1, wdef.version, "wf-test")`
  fixtures, engine status assertions, and attempt records stay byte-identical.

## Assumptions

- Each lookup sits in a test whose local `task` was created by the immediately preceding create call
  (`:91`, `:113`, `:133`, `:287`), so the record's own key is in scope.
- The file is 12 tests at HEAD and its `uv run pytest tests/agent/workflow/test_workflow_engine.py -q`
  result is 12 passed both before and after this migration.

## Design decisions

- Use the returned record's key rather than dropping the lookups: the calls keep
  `get_task_by_idempotency_key` exercised, which is what distinguishes "the lookup still works with an
  opaque key" from "the lookup was deleted to make the suite pass".
- No new test is added here: the cross-run regression belongs to `test_workflow_state_store.py`, so
  this file remains a characterization anchor (`M-1`).

## Alternatives considered

- Replace each lookup with `get_task_by_id(store._db, task.task_id)`: rejected — it would silently
  remove the only remaining coverage of lookup-by-key while the Plan keeps that function (`REQ-005`).

## Implementation

### Target file

`tests/agent/workflow/test_workflow_engine.py`

### Procedure

1. Apply row 1 (`implementations/20261024-101738_01_scripts_agent_workflow_task_ops.py.md`) first, in
   the same commit: with the composite branch gone and a literal `"s:1"` still in place, these four
   lookups return `None` and the file fails.
2. Replace each of the four literal keys with the record's key.
3. Confirm no other assertion moved.

### Method

```python
        found = get_task_by_idempotency_key(store._db, task.idempotency_key)
```

replaces, at `:94`, `:125`, `:142` and `:296`:

```python
        found = get_task_by_idempotency_key(store._db, "s:1")
```

### Details

- The four lines are identical in form, so the substitution is textual; apply it to exactly four
  occurrences (`grep -c '"s:1"'` before the edit → 4, after → 0).
- `assert found is not None` and the following status assertions stay as written; they are the
  characterization anchor for `REQ-005`.

## Compatibility considerations

- `tests/agent/test_orchestrator.py` (its `execute_turn(..., "")` sites at `:1957`, `:2000`, `:2049`,
  `:2092` and the resume characterization test at `:1366`) and
  `tests/agent/workflow/test_workflow_stage_persistence.py` (`:29`) must pass with zero edits (`M-2`).

## Security considerations

N/A: test-only change.

## Rollback considerations

- Revert together with row 1, which is the only change this migration depends on (`N/A: revert the commit`).

## Validation plan

- `uv run pytest tests/agent/workflow/test_workflow_engine.py -q` → 12 passed.
- `uv run pytest tests/agent/workflow tests/agent/test_orchestrator.py -q` → all pass (plan Validation
  plan row 4).
- `grep -n '"s:1"' tests/agent/workflow/test_workflow_engine.py` → no match (`AC-6`).
- `git diff --stat -- tests/agent/test_orchestrator.py tests/agent/workflow/test_workflow_stage_persistence.py tests/agent/workflow/test_state_store.py tests/agent/workflow/test_workflow_models.py`
  → empty (`M-2`).

## Completion criteria

- No literal composed task key remains in `tests/agent/workflow/` (`AC-6`).
- Each migrated call still asserts the task row is found after `engine.run`, so status and stage
  behavior is proven unchanged (`AC-4`).
- The unmodified characterization suites still pass.

## Out of Scope

- `scripts/agent/workflow/task_ops.py` — owned by row 1 of the same Plan.
- `tests/agent/workflow/test_workflow_state_store.py` — owned by
  `implementations/20261024-101738_02_tests_agent_workflow_test_workflow_state_store.py.md`.
- The `session_id` plumbing and `execute_turn` signature (`REQ-009`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Migrate the four literal lookups after row 1 lands | Pending | — | — | Same commit as row 1 |
| 2 | Run the workflow and orchestrator suites plus the `AC-6` grep | Pending | — | — | |

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
- **Requirement ID**: `REQ-005` (resume and call-site behavior unchanged), `REQ-007` (migrated literal
  key lookups)
- **Source issue**: `issues/20261021-093421_turn001_task-idempotency-key-collides-across-restarts.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261023-084918_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261024-101738
- **Related target files**: `tests/agent/workflow/test_workflow_engine.py`
