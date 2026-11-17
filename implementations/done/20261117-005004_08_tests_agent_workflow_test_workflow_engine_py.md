## Goal

Supply `retry_on` to each `RetryPolicy(...)` call site in `tests/agent/workflow/test_workflow_engine.py` that currently omits it, so construction satisfies the now-required `RetryPolicy.retry_on` argument (`REQ-005`). Test-only.

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- `REQ-003` (seq 01) makes `RetryPolicy.retry_on` required.
- Of the 5 `RetryPolicy(...)` sites, lines 351 and 489 already supply `retry_on=("exception", "timeout")` for their specific retry-kind assertions and are unchanged; the other 3 omit it.

## Design decisions
- Use `retry_on=("exception",)` (the shipped default) at sites that do not assert specific retry-kind behavior.

## Alternatives considered
N/A: test-only.

## Implementation
### Target file
`tests/agent/workflow/test_workflow_engine.py`
### Procedure
Add `retry_on=("exception",)` to each of the 3 `RetryPolicy(...)` call sites that omit it. Leave lines 351 and 489 (already supply `retry_on`).
### Method
Single-argument inserts.
### Details
Add `retry_on=("exception",)` at these lines (all currently omit `retry_on`):
- Line 50: `RetryPolicy(max_attempts=max_attempts, retry_wait_sec=retry_wait_sec)`
- Line 277: `RetryPolicy(max_attempts=1, retry_wait_sec=0)`
- Line 847: `RetryPolicy(max_attempts=3, retry_wait_sec=0),`
Verify lines 351-352 and 489-490 still carry their explicit `retry_on=("exception", "timeout")` and are untouched. Re-run `rg -n "RetryPolicy\(" tests/agent/workflow/test_workflow_engine.py` to confirm no remaining site omits `retry_on`.

## Compatibility considerations
N/A: test-only.

## Security considerations
N/A.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/agent/workflow` — no `TypeError` from the missing required argument; full suite green.

## Completion criteria
- Every `RetryPolicy(...)` call site in the file supplies `retry_on`; the suite passes.

## Out of Scope
Other call sites (their own rows).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261117-094053 | 20261117-094053 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261117-094053 | 20261117-094053 |  |

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
- **Related target files**: `tests/agent/workflow/test_workflow_engine.py`