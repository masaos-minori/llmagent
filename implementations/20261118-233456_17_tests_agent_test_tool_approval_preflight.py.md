## Goal

Remove the test coverage of the orphan approval-event path that DT-04 Option A deletes (REQ-007).

## Scope
**Release unit**: approval-event-cleanup

## Assumptions
- `log_approval_decision()` and `ApprovalOutcome` disappear with Plan rows 04/06 in the same commit;
  this file's imports at `:6` (docstring), `:20`, `:23` become dead references.
- Everything else in the file (`run_approval_checks()`, `execute_one_tool_call()` coverage) is live-path
  testing and must stay.

## Design decisions
- Delete the whole orphan section rather than skipping or marking it: banner `:856`, class
  `TestLogApprovalDecision` `:859-887`.
- The file's module docstring line 6 must stop naming `log_approval_decision()`.

## Alternatives considered
N/A: DT-04 Option A fixes removal; keeping the tests would test a symbol that no longer exists.

## Implementation
### Target file
`tests/agent/test_tool_approval_preflight.py`
### Procedure
1. Delete `TestLogApprovalDecision` (`:856-887`) and the `# ── log_approval_decision ──` banner.
2. Drop the `log_approval_decision` import (`:20`) and the `ApprovalOutcome` import (`:23`).
3. Remove `log_approval_decision()` from the module docstring list (`:6`).
### Method
Pure deletion; no live-path assertion changes.
### Details
- Must land in the same commit as Plan rows 04/05/06 and 18/19; landing earlier breaks the suite,
  landing later leaves imports of a deleted symbol.

## Compatibility considerations
Test-only removal; the compat-shim expectation (row 19) still tracks the name.

## Security considerations
N/A: removal of coverage for a dead code path; live approval coverage is untouched.

## Rollback considerations
Revert the whole unit commit (see row 04 procedure).

## Validation plan
- `uv run pytest tests/agent/test_tool_approval_preflight.py -q` in the same commit as rows 04/05/06.

## Completion criteria
No reference to `log_approval_decision` or `ApprovalOutcome` remains in the file; the rest of the
suite passes unchanged (AC-007).

## Out of Scope
The orphan symbols themselves (rows 04/06), `tests/agent/test_tool_audit.py` (row 18).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Delete the orphan test class and imports per Procedure | Pending | — | — | Phase 4, same commit as rows 04/05/06 |
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
- **Requirement ID**: `REQ-007` (orphan approval-event path resolution)
- **Source issue**: `issues/20261117-123003_adrchk003_agent-approval-policy.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261118-224457_adrchk003_agent-approval-policy.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261118-233456
- **Related target files**: `tests/agent/test_tool_approval_preflight.py`
