# Implementation Procedure — tests/shared/test_tool_constants.py

## Goal

Make the retry-class drift check reflect the new mdq class and pin the two mdq write tools as
non-retryable (REQ-005).

## Scope
**Release unit**: N/A: not part of a release unit (the Plan lists no release units)

Requirements: REQ-005. Acceptance criterion: AC-3.

## Assumptions
- Lightweight fill: the existing comparison needs no logic change; this row adds one assertion and
  confirms the comparison passes.
- `test_retryable_reference_equals_declared_retryable` (method at line 136, the assertion at
  line 142) builds `declared` from the
  declarations filtered through `retry_policy_is_retryable`, so once rows 4 and 5 land the mdq tools
  are absent from both sides and the assertion passes unchanged.
- This row gets its own document because it is named in `Related Tests` by two rows (4 and 5), so it
  cannot be a companion.

## Design decisions
- Add an explicit case for the two mdq tools rather than relying on absence, so the classification is
  asserted rather than implied.

## Alternatives considered
- N/A: no logic change; the alternative (leaving the file untouched) leaves the classification
  unasserted.

## Implementation
### Target file
`tests/shared/test_tool_constants.py`

### Procedure
- In `TestRetryClassDriftConsistency` (line 105), add one case asserting `retry_policy_is_retryable`
  is false for `index_paths` and `refresh_index` while the drift comparison still passes.

### Method
- Read the declarations through the existing `_declared_policies()` helper; no new fixture.

### Details
- No other test in the file reads the mdq declarations.

## Compatibility considerations
- The file is the drift consumer of `scripts/shared/tool_constants.py` (row 5); both must land in the
  same phase.

## Security considerations
- N/A: test-only change.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/shared/test_tool_constants.py`
- `uv run python tools/run_validation_gates.py`, then `uv run pytest`.

## Completion criteria
- The declarations and the reference data agree, and the mdq tools are asserted non-retryable (AC-3).

## Out of Scope
- The declarations (row 4); the reference data (row 5); the dispatch overlay cases (row 12).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | This row is the test change |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: no documentation in scope |

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
- **Requirement ID**: REQ-005
- **Source issue**: `issues/20261119-142127_mdqmcp005_mdq-transaction-atomicity.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261127-171503_mdqmcp005_mdq-transaction-atomicity.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261128-002340
- **Related target files**: `tests/shared/test_tool_constants.py`
