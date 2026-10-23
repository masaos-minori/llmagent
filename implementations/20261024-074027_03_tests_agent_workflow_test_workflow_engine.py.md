## Goal

Replace the four literal `"s:1"` idempotency-key lookups in `tests/agent/workflow/test_workflow_engine.py` with the record's returned `task.idempotency_key`, so the engine tests no longer depend on the removed composite key format (`plans/20261023-084918_plan.md`).

## Scope

`tests/agent/workflow/test_workflow_engine.py`: migrate the four `get_task_by_idempotency_key(store._db, "s:1")` lookups (`:94`, `:125`, `:142`, `:296`) to `get_task_by_idempotency_key(store._db, task.idempotency_key)`.

## Assumptions

- In every one of the four methods a `task = create_task(store._db, "s", 1, ...)` binding is already in scope, so `task.idempotency_key` is available.
- The production `create_task()` change (doc 1) returns a UUID4 key, which `get_task_by_idempotency_key` looks up opaquely — no caller needs to know its format.

## Design decisions

- Use the returned `task.idempotency_key` rather than re-deriving or hard-coding a value: the key is random, so the only correct literal-free reference is the record that was just created.
- Keep every assertion about task status and stage records byte-identical — this is a pure characterization migration (`M-1`), not a behavior change.

## Alternatives considered

N/A: single-line-per-site mechanical migration with no public-contract, persistence, or security impact.

## Implementation
### Target file
`tests/agent/workflow/test_workflow_engine.py`

### Procedure
1. In `TestWorkflowEngineHappyPath.test_run_sets_task_status_completed` (`:94`): replace `"s:1"` with `task.idempotency_key`.
2. In `TestWorkflowEngineRetry.test_retry_succeeds_on_second_attempt` (`:125`): replace `"s:1"` with `task.idempotency_key`.
3. In `TestWorkflowEngineRetry.test_halt_after_max_attempts` (`:142`): replace `"s:1"` with `task.idempotency_key`.
4. In `TestWorkflowEngineStages.test_execute_success_verify_failure_marks_task_failed` (`:296`): replace `"s:1"` with `task.idempotency_key`.

### Method
- The four edits are textually identical (`"s:1"` → `task.idempotency_key`); verify each sits in the intended method by confirming the surrounding `task = create_task(store._db, "s", 1, ...)` binding, since `task` is the same name across methods.
- Do not alter any `assert`, `await engine.run(...)`, or stage fixture. The `_make_wdef` / `store` fixtures stay untouched.

### Details
Each of the four sites currently reads:
```python
        found = get_task_by_idempotency_key(store._db, "s:1")
```
Replace with:
```python
        found = get_task_by_idempotency_key(store._db, task.idempotency_key)
```
All four occurrences share this exact line; confirm the enclosing method before each edit (the methods are `test_run_sets_task_status_completed`, `test_retry_succeeds_on_second_attempt`, `test_halt_after_max_attempts`, `test_execute_success_verify_failure_marks_task_failed`).

## Compatibility considerations
- `get_task_by_idempotency_key` signature unchanged; still a test-only lookup (REQ-005).
- `M-2` characterization suites pass unmodified; no other test file references `"s:1"`.

## Security considerations
N/A: test-only change, handles no secret.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `grep -n '"s:1"' tests/agent/workflow/test_workflow_engine.py` returns no match (AC-6).
- `uv run pytest tests/agent/workflow/test_workflow_engine.py -q` passes unmodified except for the four lookups.
- Full sequence per `rules/toolchain.md` (ruff, mypy `--no-namespace-packages`, bandit, lint-imports, pre-commit) — AC-8.

## Completion criteria
- All four lookups use `task.idempotency_key`; no `"s:1"` literal remains.
- Every existing status/stage assertion still passes.

## Out of Scope
- `test_workflow_state_store.py` migration — separate target file (doc 2).
- Production `create_task()` change — separate target file (doc 1).
- Schema / resume path — REQ-004, REQ-005.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Migrate the four `"s:1"` lookups |
| 2 | Add or update tests per Validation plan | Pending | — | — | None: migration only |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | Including grep guard |

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
- **Requirement ID**: REQ-005, REQ-007
- **Source issue**: `issues/20261021-093421_turn001_task-idempotency-key-collides-across-restarts.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261023-084918_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261024-074027
- **Related target files**: `tests/agent/workflow/test_workflow_engine.py`
