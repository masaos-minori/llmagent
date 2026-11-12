## Goal

Remove the `ensure_corpus_meta` import and its seed from the fingerprint-gate tests
(`REQ-006`).

## Scope
**Release unit**: corpus-meta-removal

## Assumptions
- `tests/deploy/test_init_db_schema_gate.py` imports `ensure_corpus_meta` and seeds the
  `rag_corpus_meta` table to exercise the fingerprint gate (lines 39, 122).

## Design decisions
- Drop the import and the seed; keep every other fingerprint-gate test unchanged.

## Alternatives considered
N/A: removal is the decided Option B; the seed references a table the DDL no longer creates.

## Implementation
### Target file
`tests/deploy/test_init_db_schema_gate.py`
### Procedure
- Remove the `ensure_corpus_meta` import (~line 39).
- Remove the `rag_corpus_meta` seed (~line 122).
### Method
Import plus seed deletion; confirm no remaining reference to `ensure_corpus_meta`.
### Details
- The module `rag.corpus_identity` is deleted by seq 08; delete together so the module
  imports cleanly.

## Compatibility considerations
N/A: test-only; the table is dropped from the canonical DDL by the sibling code document.

## Security considerations
N/A: no security-relevant behavior change.

## Rollback considerations
Revert the commit.

## Validation plan
- `rg -n "corpus_identity|rag_corpus_meta|bump_index_generation" scripts tests` returns
  nothing (excluding the preserved ADR-010 text).
- `uv run pytest tests/deploy` passes.

## Completion criteria
The import and seed are gone; the fingerprint-gate tests pass.

## Out of Scope
The identity module (`REQ-006`, seq 08) and the DDL table (seq 13).

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
- **Requirement ID**: `REQ-006`
- **Source issue**: issues/20261110-170753_rmcompat003_rag-corpus-identity-decision.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261112-120011_rmcompat003_rag-corpus-identity-decision.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261112-223151
- **Related target files**: `tests/deploy/test_init_db_schema_gate.py`
