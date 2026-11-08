## Goal
Rename the two `backoff_sec` sites in `tests/agent/workflow/test_workflow_models.py` — the `RetryPolicy` fixture kwarg and the default-policy assertion — to `retry_wait_sec` (`REQ-003`/`REQ-005`).

## Scope
**Release unit**: wfaudit014-full

- Covers Plan `plans/20261108-084015_wfaudit014_retry-loop-dead-parameters.md` row 9 only: `tests/agent/workflow/test_workflow_models.py`.

## Assumptions
- Landing order: after procedure 03 (models), which renames the dataclass field; `RetryPolicy(max_attempts=3, backoff_sec=1)` (HEAD L77) and `assert wdef.retry_policy.backoff_sec == 1` (HEAD L96, inside `test_default_retry_policy`) are the file's only occurrences.

## Design decisions
- Mechanical rename only; the asserted default value 1 (`REQ-004` numeric identity of the `WorkflowDef` default_factory) is unchanged.

## Alternatives considered
- None: the row is a two-site rename pinned by procedure 03.

## Implementation
### Target file
`tests/agent/workflow/test_workflow_models.py`

### Procedure
Rename two sites.

### Method
1. `TestWorkflowDef._make_wdef` fixture: `RetryPolicy(max_attempts=3, backoff_sec=1)` -> `RetryPolicy(max_attempts=3, retry_wait_sec=1)`.
2. `test_default_retry_policy`: `assert wdef.retry_policy.backoff_sec == 1` -> `assert wdef.retry_policy.retry_wait_sec == 1`.

### Details
- `grep -n backoff_sec tests/agent/workflow/test_workflow_models.py` returns nothing after the edits.

## Compatibility considerations
- None beyond the landing order (must follow procedure 03).

## Security considerations
- No change.

## Rollback considerations
- Revert with the release unit.

## Validation plan
- `uv run pytest tests/agent/workflow/test_workflow_models.py -q` green after procedure 03 lands; full `uv run pytest tests/ -q` and lint/type gates per `rules/toolchain.md` at unit completion.

## Completion criteria
- No `backoff_sec` token in the file; default-policy assertion reads `retry_wait_sec == 1`.

## Out of Scope
- `test_get_stage_not_found` and other `WorkflowDef` behavior tests (unchanged).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: `REQ-003`, `REQ-005`
- **Source issue**: `issues/20261107-203227_wfaudit014_retry-loop-dead-parameters.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261108-084015_wfaudit014_retry-loop-dead-parameters.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261108-211937
- **Related target files**: tests/agent/workflow/test_workflow_models.py
