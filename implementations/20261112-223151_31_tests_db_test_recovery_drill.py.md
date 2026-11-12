## Goal

Remove the `rag_corpus_meta` seed insert from the recovery drill tests (`REQ-008`).

## Scope
**Release unit**: corpus-meta-removal

## Assumptions
- The drill inserts a row into `rag_corpus_meta` as part of its fixture setup (~lines
  101-104).

## Design decisions
- Delete the `rag_corpus_meta` seed insert; keep every other drill seed.

## Alternatives considered
N/A: removal is the decided Option B; the drill seeds a table that no longer exists.

## Implementation
### Target file
`tests/db/test_recovery_drill.py`
### Procedure
- Remove the `rag_corpus_meta` seed insert (~lines 101-104).
### Method
Single-seed deletion; confirm no remaining reference to `rag_corpus_meta`.
### Details
- The DDL table is removed by seq 13; delete together so the drill builds a valid schema.

## Compatibility considerations
N/A: test-only; the table is dropped from the canonical DDL by the sibling code document.

## Security considerations
N/A: no security-relevant behavior change.

## Rollback considerations
Revert the commit.

## Validation plan
- `rg -n "corpus_meta|unverifiable corpus" scripts tests` returns nothing.
- `uv run pytest tests/db` passes.

## Completion criteria
The `rag_corpus_meta` seed is gone; the drill tests build a valid schema and pass.

## Out of Scope
The DDL table (`REQ-008`, seq 13) and the schema test (companion, covered by seq 13).

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
- **Requirement ID**: `REQ-008`
- **Source issue**: issues/20261110-170753_rmcompat003_rag-corpus-identity-decision.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261112-120011_rmcompat003_rag-corpus-identity-decision.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261112-223151
- **Related target files**: `tests/db/test_recovery_drill.py`
