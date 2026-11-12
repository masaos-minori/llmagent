## Goal

Drop the `identity-unverified` assertions from `tests/agent/test_startup.py` so the suite no
longer asserts the removed warning prefix (`REQ-009`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Three assertions check the `identity-unverified` prefix at lines 554, 643, 657; the rest
  of each test keeps its severity and continue-startup assertions.

## Design decisions
- Remove only the `identity-unverified` prefix assertions; keep category, severity, and
  timeout-text assertions.

## Alternatives considered
N/A: removal is the decided Option B; the prefix names a removed concept.

## Implementation
### Target file
`tests/agent/test_startup.py`
### Procedure
- Remove the `identity-unverified` assertions at lines 554, 643, 657; keep the surrounding
  category and timeout-text assertions.
### Method
Three assertion deletions; keep every other assertion in each test.
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
- `uv run pytest tests/agent/test_startup.py` passes.

## Completion criteria
The `identity-unverified` assertions are gone; the startup tests pass with the remaining
assertions intact.

## Out of Scope
The startup warning prefix (`REQ-009`, seq 15) and the other two startup test files
(seq 33 companion, seq 35).

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
- **Related target files**: `tests/agent/test_startup.py`
