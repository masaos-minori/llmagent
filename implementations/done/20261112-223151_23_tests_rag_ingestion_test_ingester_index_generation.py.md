## Goal

Delete the ingester index-generation test module that exercises the removed
`bump_index_generation()` call (`REQ-004`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- `tests/rag/ingestion/test_ingester_index_generation.py` asserts the index generation is
  bumped after ingestion via `rag.corpus_identity.bump_index_generation`.

## Design decisions
- Delete the test module outright; no replacement.

## Alternatives considered
N/A: removal is the decided Option B; the module tests a removed write path.

## Implementation
### Target file
`tests/rag/ingestion/test_ingester_index_generation.py`
### Procedure
- Delete `tests/rag/ingestion/test_ingester_index_generation.py` via `git rm`.
### Method
Single file deletion; confirm no remaining reference to `index_generation` in the suite.
### Details
- The ingester caller is removed by seq 06; delete together so no test imports a removed
  symbol.

## Compatibility considerations
N/A: test-only; the production write path is removed by the sibling code document (seq 06).

## Security considerations
N/A: no security-relevant behavior change.

## Rollback considerations
Revert the commit: restore the file from the prior commit.

## Validation plan
- `rg -n "bump_index_generation|index_generation" scripts/rag/ingestion tests/rag/ingestion`
  returns nothing in the same cycle as seq 06. The name legitimately remains in
  `scripts/rag/corpus_identity.py`, `scripts/rag/identity_gate.py`, `scripts/db/schema_sql.py`
  and fixture seeds until the release unit (phases 6-8) removes them.
- `uv run pytest tests/rag/ingestion` passes.

## Completion criteria
The index-generation test module is gone; no test references the removed symbol.

## Out of Scope
The ingester bump call (`REQ-004`, seq 06).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261113-101936 | 20261113-102229 |  |
| 2 | Add or update tests per Validation plan | Completed | — | 20261113-102229 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261113-102229 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20261113-102229 |  |

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
- **Requirement ID**: `REQ-004`
- **Source issue**: issues/20261110-170753_rmcompat003_rag-corpus-identity-decision.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261112-120011_rmcompat003_rag-corpus-identity-decision.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261112-223151
- **Related target files**: `tests/rag/ingestion/test_ingester_index_generation.py`