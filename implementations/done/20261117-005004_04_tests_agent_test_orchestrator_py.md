## Goal

Supply `retry_on=("exception",)` to every `RetryPolicy(...)` call site in `tests/agent/test_orchestrator.py` that currently omits it, so construction satisfies the now-required `RetryPolicy.retry_on` argument (`REQ-005`). Test-only.

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- `REQ-003` (seq 01) makes `RetryPolicy.retry_on` a required constructor argument; these call sites currently omit it and will raise `TypeError` once that lands.
- All 8 `WorkflowDef(...)` constructions in this file already supply `stages` and `retry_policy`, so they are unchanged.

## Design decisions
- Use `retry_on=("exception",)` (the shipped default) at sites that do not assert specific retry-kind behavior.

## Alternatives considered
N/A: mechanical call-site fix.

## Implementation
### Target file
`tests/agent/test_orchestrator.py`
### Procedure
Add `retry_on=("exception",)` to each of the 10 `RetryPolicy(...)` call sites that omit it.
### Method
Single-argument inserts at each site.
### Details
Add `retry_on=("exception",),` to the keyword list at these lines (all currently omit `retry_on`):
- Line 211: `RetryPolicy(max_attempts=3, retry_wait_sec=1),`
- Line 438: `RetryPolicy(max_attempts=1, retry_wait_sec=0)`
- Line 536: `RetryPolicy(max_attempts=1, retry_wait_sec=0)`
- Line 637: `RetryPolicy(max_attempts=3, retry_wait_sec=0)`
- Line 877: `RetryPolicy(max_attempts=3, retry_wait_sec=0)`
- Line 985: `RetryPolicy(max_attempts=3, retry_wait_sec=0)`
- Line 1079: `RetryPolicy(max_attempts=3, retry_wait_sec=0)`
- Line 3287: `RetryPolicy(max_attempts=max_attempts, retry_wait_sec=0)`
- Line 4062: `RetryPolicy(max_attempts=3, retry_wait_sec=0)`
- Line 4110: `RetryPolicy(max_attempts=3, retry_wait_sec=0)`
Re-run `rg -n "RetryPolicy\(" tests/agent/test_orchestrator.py` after editing to confirm zero remaining sites that omit `retry_on`.

## Compatibility considerations
N/A: test-only.

## Security considerations
N/A.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/agent/workflow tests/agent/test_orchestrator.py` — no `TypeError` from the missing required argument; full suite green.

## Completion criteria
- Every `RetryPolicy(...)` call site in the file supplies `retry_on`; the regression suite passes.

## Out of Scope
Other test files (each its own row).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261117-093739 | 20261117-093739 |  |
| 2 | Add or update tests per Validation plan | Completed | 20261117-093739 | 20261117-093739 | No new tests; this row only repairs existing call sites. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261117-093739 | 20261117-093739 |  |

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
- **Related target files**: `tests/agent/test_orchestrator.py`