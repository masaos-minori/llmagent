## Goal

Remove `rag_corpus_meta` from `TABLE_OWNERSHIP["rag"]` so the DB-separation inventory
matches the DDL that no longer creates the table (`REQ-008`).

## Scope
**Release unit**: corpus-meta-removal

## Assumptions
- `tools/check_db_separation.py` owns the canonical `TABLE_OWNERSHIP` mapping; ADR-008's
  line-409 inventory already lists four RAG tables and matches Option B.
- The checker verifies ownership after the change; the inventory must match the canonical
  DDL (seq 13).

## Design decisions
- Remove `"rag_corpus_meta"` from the `"rag"` frozenset; keep the other four tables.

## Alternatives considered
N/A: removal is the decided Option B; keeping the name would make the checker fail against
the reduced DDL.

## Implementation
### Target file
`tools/check_db_separation.py`
### Procedure
- Remove `"rag_corpus_meta"` from `TABLE_OWNERSHIP["rag"]` (~line 57); keep
  `"documents", "chunks", "chunks_vec", "chunks_fts"`.
### Method
Single member removal from a frozenset; confirm the set still matches the canonical DDL.
### Details
- Do not touch the `"session"` ownership block.

## Compatibility considerations
N/A: inventory-only; the DDL (seq 13) is the source of truth for the fingerprint.

## Security considerations
N/A: no security-relevant behavior change.

## Rollback considerations
Revert the commit.

## Validation plan
- `uv run python tools/check_db_separation.py` passes.

## Completion criteria
`TABLE_OWNERSHIP["rag"]` lists exactly the four tables in the canonical DDL; the checker
passes.

## Out of Scope
The DDL table (`REQ-008`, seq 13) and the ADR-008 inventory (already matches, not edited).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | Static check only |
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
- **Related target files**: `tools/check_db_separation.py`
