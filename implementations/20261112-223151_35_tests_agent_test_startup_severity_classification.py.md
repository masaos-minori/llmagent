## Goal

Drop the `identity-unverified` assertion from the startup severity-classification tests so
the suite no longer asserts the removed warning prefix (`REQ-009`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Two assertions check the `identity-unverified` prefix at lines 518, 530; the rest of the
  test keeps its severity-classification assertions.

## Design decisions
- Remove only the `identity-unverified` assertion(s); keep the severity-classification
  assertions.

## Alternatives considered
N/A: removal is the decided Option B; the prefix names a removed concept.

## Implementation
### Target file
`tests/agent/test_startup_severity_classification.py`
### Procedure
- Remove the `identity-unverified` assertions at lines 518, 530; keep the surrounding
  severity-classification assertions.
### Method
Assertion deletion(s); keep every other assertion in the test.
### Details
- The warning prefix is stripped by seq 15; delete together so the assertions match the new
  message text.

## Compatibility considerations
N/A: test-only; the prefix is removed by the sibling code document.

## Security considerations
N/A: no security-relevant behavior change.

## Rollback considerations
Revert the commit.

## Validation plan
- `rg -n "identity-unverified" scripts tests docs` returns nothing.
- `uv run pytest tests/agent/test_startup_severity_classification.py` passes.

## Completion criteria
The `identity-unverified` assertion is gone; the severity-classification tests pass with the
remaining assertions intact.

## Out of Scope
The startup warning prefix (`REQ-009`, seq 15) and the other startup test files (companion
seq 33, standalone seq 34).

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
- **Requirement ID**: `REQ-009`
- **Source issue**: issues/20261110-170753_rmcompat003_rag-corpus-identity-decision.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261112-120011_rmcompat003_rag-corpus-identity-decision.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261112-223151
- **Related target files**: `tests/agent/test_startup_severity_classification.py`
