## Goal

Remove the `rag_corpus_meta` table from the canonical RAG DDL so the shipped schema no
longer creates it (`REQ-008`).

## Scope
**Release unit**: corpus-meta-removal

## Assumptions
- `build_rag_schema_sql()` in `schema_sql.py` emits the canonical DDL, including the
  single-row `rag_corpus_meta` table.
- `deploy/init_db.sh` enforces an exact-match fingerprint against this DDL, so removing the
  table here moves the RAG fingerprint and a deployed file still carrying the table is
  refused until archived and recreated.

## Design decisions
- Delete the `CREATE TABLE IF NOT EXISTS rag_corpus_meta (...)` block from the canonical DDL;
  keep the surrounding tables verbatim.

## Alternatives considered
N/A: removal is the decided Option B; keeping the table would contradict it.

## Implementation
### Target file
`scripts/db/schema_sql.py`
### Procedure
- Delete the `CREATE TABLE IF NOT EXISTS rag_corpus_meta (...)` block (~lines 47-56),
  including its trailing comment lines.
### Method
Single DDL-block deletion; confirm no remaining `rag_corpus_meta` in the emitted schema.
### Details
- Part of the `corpus-meta-removal` unit; the fixtures that seed the table (seq 27, 31) and
  the schema test (companion) change with this DDL.

## Compatibility considerations
Removing the table moves the RAG fingerprint (`rules/persisted-schema-change.md` item 2); a
file with the old table is refused by the fingerprint gate until archived and recreated
(`UNK-04`). No migration step is registered by design.

## Security considerations
N/A: no security-relevant behavior change.

## Rollback considerations
Revert the commit: restore the DDL block.

## Validation plan
- `uv run python tools/check_db_separation.py` passes.
- `uv run pytest tests/db` passes; the schema test asserts the table is absent.

## Completion criteria
The canonical RAG DDL has no `rag_corpus_meta`; the schema test asserts absence; the
ownership checker passes.

### Companion test files
- `tests/db/test_create_schema.py`
  - Procedure: replace the table-exists test with an absent-table assertion and drop the
    fixture DDL that created the table (lines 56, 203-210).
  - Validation: `uv run pytest tests/db` passes with the absent-table assertion.

## Out of Scope
The ownership inventory entry (`REQ-008`, seq 14) and the drill/ingester fixtures (seq 31,
27).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | Covers companion `test_create_schema.py` |
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
- **Related target files**: `scripts/db/schema_sql.py`, `tests/db/test_create_schema.py`
