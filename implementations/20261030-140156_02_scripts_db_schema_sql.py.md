# Implementation Procedure: `scripts/db/schema_sql.py` (RAGCORPUS001 Phase 2)

**Plan**: `plans/done/20261030-013620_ragcorpus001_rag-corpus-identity.md` (REQ-001, REQ-010)

## Goal
Add the `rag_corpus_meta` single-row DDL to the RAG schema definition, registered
through the dbmig001 migration framework rather than appended to the bare DDL list.

## Scope
- `CREATE TABLE IF NOT EXISTS chunks` at `:38` (the placement landmark named in the
  frozen table).
- `build_rag_schema_sql(dims)` `:158` — the RAG schema assembly point.
- `WORKFLOW_SCHEMA_VERSION = "1.1.0"` `:25` — existing version-constant precedent.
- dbmig001 procedure docs (`implementations/20261029-071336_*`, closed batch) define the
  migration ledger registration API; the exact registration call name is fixed by that
  landed code — read it at implementation time.

## Assumptions
- Plan-level assumptions apply unchanged; see the Source plan Assumptions section.

## Design decisions
- `rag_corpus_meta` (new) table: single row — `corpus_id TEXT NOT NULL`,
  `index_generation INTEGER NOT NULL`, `embedding_model_id TEXT NOT NULL`,
  `normalization_version TEXT NOT NULL`, `chunking_policy_version TEXT NOT NULL`,
  `updated_at TEXT NOT NULL`; single-row enforcement via `CHECK (rowid = 1)` (SQLite
  idiom; alternative `INTEGRITY CHECK` if the dbmig001 ledger prefers it — match the
  landed ledger's DDL conventions).
- Registration goes through the dbmig001 forward-only ledger entry, not a raw edit of
  the `:38` region string, so existing databases receive it as a migration step.

## Alternatives considered
- No file-level alternatives beyond those evaluated in the Source plan; this procedure executes the selected option.

## Implementation
1. Implement only after dbmig001's ledger exists; define the migration entry with the
   DDL above.
2. Keep fresh-database creation (build_rag_schema_sql `:158`) equivalent to the ledger
   end-state — the dbmig001 equivalence tests already enforce this; extend them with the
   new table.

## Compatibility considerations
**Dependencies**:
**Blocks**: docs 01, 06, 13, 15 (all consume the meta table)

## Security considerations
- No new security surface beyond what the Source plan records.

## Rollback considerations
- Forward-only migration ledger: rollback follows the dbmig001 ledger procedure, not a plain file revert.

## Validation plan
- `uv run pytest tests/db` — dbmig001 migration equivalence tests extended with
  `rag_corpus_meta` (Validation plan row for this file).

## Completion criteria
- Fresh and migrated databases both contain `rag_corpus_meta` with identical schema;
  no direct `CREATE TABLE` bypass left in the file.

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
