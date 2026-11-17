## Goal

Update `tests/agent/workflow/test_workflow_models.py` to the strict contract: remove the two default-pinning tests, make `_make_wdef` supply `retry_on`, and add constructor-surface tests that require all three arguments and the empty-stage owner (`REQ-003`, `REQ-005`). Test-only.

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- `REQ-003` makes `RetryPolicy.retry_on`, `WorkflowDef.stages`, `WorkflowDef.retry_policy` required; `REQ-004` adds the model empty-stage guard.
- The two removed tests pin the implicit defaults that REQ-003 deletes, so they must go.

## Design decisions
- Constructor-surface tests assert the `TypeError` raised when each of the three arguments is omitted, and that an empty `stages` list raises (REQ-004 owner).

## Alternatives considered
N/A: test-only.

## Implementation
### Target file
`tests/agent/workflow/test_workflow_models.py`
### Procedure
1. Add `retry_on=("exception",)` to the `RetryPolicy(...)` in `_make_wdef`.
2. Remove `test_default_retry_policy` and `test_stages_default_empty`.
3. Add constructor-surface tests requiring all three arguments and the empty-stage owner.
### Method
One arg insert plus two test removals plus new assertions.
### Details
- Line 77 (`_make_wdef`): change
  `        policy = RetryPolicy(max_attempts=3, retry_wait_sec=1)`
  to
  `        policy = RetryPolicy(max_attempts=3, retry_wait_sec=1, retry_on=("exception",))`.
- Lines 93-96 (`test_default_retry_policy`) and 98-100 (`test_stages_default_empty`): delete both test methods (they construct `WorkflowDef(name="x", version="1.0.0")` and assert the old defaults).
- Add to `TestWorkflowDef`:
  - A test that `RetryPolicy(max_attempts=3, retry_wait_sec=1)` without `retry_on` raises `TypeError`.
  - A test that `WorkflowDef(name="x", version="1.0.0", stages=[...], retry_policy=...)` with all three supplied constructs; and that omitting `stages` or `retry_policy` raises `TypeError`.
  - A test that `WorkflowDef(name="x", version="1.0.0", stages=[], retry_policy=...)` raises `AssertionError` (empty-stage owner, REQ-004).

## Compatibility considerations
N/A: test-only.

## Security considerations
N/A.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/agent/workflow/test_workflow_models.py` — new constructor-surface tests pass; `test_default_retry_policy` and `test_stages_default_empty` no longer exist.

## Completion criteria
- The two default-pinning tests are removed; `_make_wdef` supplies `retry_on`; constructor-surface tests require all three arguments and the empty-stage owner.

## Out of Scope
Other call sites in other test files (their own rows).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261117-093905 | 20261117-093905 |  |
| 2 | Add or update tests per Validation plan | Completed | 20261117-093905 | 20261117-093905 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261117-093905 | 20261117-093905 |  |

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
- **Requirement ID**: `REQ-003` (required constructor arguments), `REQ-005` (call-site surface)
- **Source issue**: `issues/20261116-114753_compat001_workflow-definition-strict-contract.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261116-214100_compat001_workflow-definition-strict-contract.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261117-005004
- **Related target files**: `tests/agent/workflow/test_workflow_models.py`