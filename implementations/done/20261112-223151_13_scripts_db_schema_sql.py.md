## Goal

Remove the `rag_corpus_meta` table from the canonical RAG DDL so the shipped schema no
longer creates it (`REQ-008`).

## Scope
**Release unit**: corpus-meta-removal

## Verification Findings (2026-11-13)
- Execution cycle (lockstep core): this edit lands together with every fixture that mirrors or
  seeds the table — `test_rag_consistency` seed (seq 28), `test_recovery_drill` seed (seq 31),
  `test_init_db_schema_gate` import+seed (seq 32), `test_rag_index_integrity`
  `_SCHEMA_SQL_CANONICAL` DDL mirror + seed, `test_ingester` DDL copy + seed — and with the
  `rag.corpus_identity`/`identity_gate` module deletions (seq 08/09), whose last importer is
  the gate test. Dropping a seed before this edit, or keeping one after it, breaks the
  fingerprint/fail-closed layers (proven 2026-11-13 with the gate-test drill failure).

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
- Part of the `corpus-meta-removal` unit; the fixtures that seed the table (seq 31
  `test_recovery_drill.py`, and the companions below) change with this DDL. The ingester
  fixture (`tests/rag/ingestion/test_ingester.py`) uses its own DDL copy, but that fixture
  runs `DocumentManager.check_consistency` → `check_rag_consistency`, which
  fingerprint-compares it against `build_rag_schema_sql()`; it must therefore be edited in
  this cycle (2026-11-13 verification; the earlier "handled by seq 06" claim was wrong).
- `tests/agent/services/test_rag_index_integrity.py` mirrors the canonical DDL in
  `_SCHEMA_SQL_CANONICAL` (with a `rag_corpus_meta` seed at ~lines 124-132, 164-167) and its
  consistency tests fingerprint-check the fixture against `build_rag_schema_sql()`
  (`scripts/db/rag_consistency_queries.py:279`). That mirror and seed MUST be removed in
  this same cycle or the fingerprint gate raises on the fixture.

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
- `tests/agent/services/test_rag_index_integrity.py`
  - Procedure: remove the `rag_corpus_meta` DDL block (~lines 124-132) and its INSERT seed
    (~lines 164-167) from `_SCHEMA_SQL_CANONICAL`, and the seed sentence in the block comment
    (~lines 96-98). Required in this cycle: the fixture is fingerprint-checked against
    `build_rag_schema_sql()`.
  - Validation: `uv run pytest tests/agent/services/test_rag_index_integrity.py` passes with
    the seed gone and the template edited together.
- `tests/rag/ingestion/test_ingester.py`
  - Procedure: remove the `rag_corpus_meta` DDL copy (comment lines 36-38, table block
    64-71) and its INSERT seed (105-108) from `_SCHEMA_SQL`. Required in this cycle: the
    fixture is fingerprint-checked through `DocumentManager.check_consistency` →
    `check_rag_consistency` against `build_rag_schema_sql()`.
  - Validation: `uv run pytest tests/rag/ingestion` passes with the fixture DDL removed
    together with the canonical table.

## Out of Scope
The ownership inventory entry (`REQ-008`, seq 14) and the drill/ingester fixtures (seq 31,
27).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 20261113 | seq13 lockstep cycle 20261113 |
| 2 | Add or update tests per Validation plan | Completed | — | 20261113 | Covers companion `test_create_schema.py` seq13 lockstep cycle 20261113 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261113 | seq13 lockstep cycle 20261113 |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20261113 | seq13 lockstep cycle 20261113 |

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