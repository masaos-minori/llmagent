## Goal

Supply `retry_on=("exception",)` to the single `RetryPolicy(...)` call site in `tests/agent/workflow/test_adapter_store_ownership.py` so construction satisfies the now-required `RetryPolicy.retry_on` argument (`REQ-005`). Test-only.

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- `REQ-003` (seq 01) makes `RetryPolicy.retry_on` required; line 36 currently omits it and will raise `TypeError` once that lands.

## Design decisions
N/A: single mechanical call-site fix.

## Implementation
### Target file
`tests/agent/workflow/test_adapter_store_ownership.py`
### Procedure
Add `retry_on=("exception",)` to the `RetryPolicy(...)` at line 36.
### Method
Single-argument insert.
### Details
- Line 36: add `retry_on=("exception",)` to the existing `RetryPolicy(max_attempts=1, retry_wait_sec=0)` keyword list.

## Compatibility considerations
N/A: test-only.

## Security considerations
N/A.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/agent/workflow` — no `TypeError` from the missing required argument.

## Completion criteria
- The line 36 `RetryPolicy(...)` supplies `retry_on`; the suite passes.

## Out of Scope
Other call sites (their own rows).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-005` (every repository call site supplies `retry_on`)
- **Source issue**: `issues/20261116-114753_compat001_workflow-definition-strict-contract.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261116-214100_compat001_workflow-definition-strict-contract.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261117-005004
- **Related target files**: `tests/agent/workflow/test_adapter_store_ownership.py`
