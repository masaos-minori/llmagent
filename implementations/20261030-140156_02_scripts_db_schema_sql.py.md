# Implementation Procedure: `scripts/db/schema_sql.py` (RAGCORPUS001 Phase 2)

**Plan**: `plans/done/20261030-013620_ragcorpus001_rag-corpus-identity.md` (REQ-001, REQ-010)

## Goal
Add the `rag_corpus_meta` single-row DDL to the RAG schema definition, appended
directly to `_RAG_SCHEMA_TEMPLATE` next to the existing `chunks` DDL. RAG is a
recreate-only (`n`) domain (dbmig001 row 18); it has no forward-only migration
ledger, so the table is created by the fresh-schema builder, not a migration step.

## Scope
- `CREATE TABLE IF NOT EXISTS chunks` at `:38` (the placement landmark named in the
  frozen table).
- `build_rag_schema_sql(dims)` `:158` — the RAG schema assembly point.
- `WORKFLOW_SCHEMA_VERSION = "1.1.0"` `:25` — existing version-constant precedent.
- RAG is a recreate-only (`n`) domain (dbmig001 row 18; `test_rag_fresh_creation_has_no_ledger`). It has no forward-only migration ledger.

## Assumptions
- Plan-level assumptions apply unchanged; see the Source plan Assumptions section.

## Design decisions
- `rag_corpus_meta` (new) table: single row — `corpus_id TEXT NOT NULL`,
  `index_generation INTEGER NOT NULL`, `embedding_model_id TEXT NOT NULL`,
  `normalization_version TEXT NOT NULL`, `chunking_policy_version TEXT NOT NULL`,
  `updated_at TEXT NOT NULL`; single-row enforcement via `CHECK (rowid = 1)` (SQLite
  idiom).
- Append the DDL directly to `_RAG_SCHEMA_TEMPLATE` next to the existing `chunks` DDL
  (`:38` region). RAG is recreate-only, so there is no migration step: the fresh-schema
  builder (`build_rag_schema_sql`) creates the table on every fresh DB creation. Do NOT
  route this through any dbmig001 ledger — that would violate the recreate-only contract
  enforced by `test_rag_fresh_creation_has_no_ledger`.

## Alternatives considered
- No file-level alternatives beyond those evaluated in the Source plan; this procedure executes the selected option.

## Implementation
1. Insert the `rag_corpus_meta` DDL directly into `_RAG_SCHEMA_TEMPLATE`, immediately
   after the existing `chunks` table DDL at the `:38` landmark (first table in the
   template). Preserve column order and the single-row `CHECK (rowid = 1)` constraint.
2. Keep fresh-database creation (`build_rag_schema_sql` `:158`) correct — it renders
   `_RAG_SCHEMA_TEMPLATE`, so the new table appears automatically. There is no separate
   migration path; do not add one.

## Compatibility considerations
**Dependencies**:
**Blocks**: docs 01, 06, 13, 15 (all consume the meta table)

## Security considerations
- No new security surface beyond what the Source plan records.

## Rollback considerations
- Recreate-only domain: reverting means removing the DDL block from `_RAG_SCHEMA_TEMPLATE`.
  No ledger row to undo. Coordinate with the recreate-only policy (any schema change
  requires a fresh database).

## Validation plan
- `uv run pytest tests/db` — `tests/db/test_create_schema.py` fresh-RAG-schema test
  extended to assert `rag_corpus_meta` exists with the schema above (recreate-only
  fresh-creation check, not a migration-equivalence test).

## Completion criteria
- Fresh RAG DB creation includes `rag_corpus_meta` with the schema above; the table is
  defined exactly once in `_RAG_SCHEMA_TEMPLATE` with no duplicate or bypass DDL.

## Out of Scope
- Everything outside the target file and the anchors recorded above; cross-plan boundaries and sequencing are recorded in the Source plan.

## Execution Status
### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Re-verify cited anchors before editing | Pending | — | — | |
| 2 | Apply the Implementation procedure | Pending | — | — | |
| 3 | Run the Validation plan gates | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Marker record
- `(new)` markers applied: `rag_corpus_meta` (Contract section).

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-001, REQ-010
- **Source issue**: `issues/20261029-104506_ragcorpus001_rag-corpus-identity.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/done/20261030-013620_ragcorpus001_rag-corpus-identity.md` — Implementation Target Files row 02
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-140156
- **Related target files**: `scripts/db/schema_sql.py`
