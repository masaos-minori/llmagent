# Implementation Procedure: `scripts/rag/corpus_identity.py` (RAGCORPUS001 Phase 2)

**Plan**: `plans/done/20261030-013620_ragcorpus001_rag-corpus-identity.md` (REQ-001, REQ-003, REQ-007)

## Goal
Create the corpus identity module: the identity dataclass, computation from the local
RAG DB meta table plus config, meta-table ensure/read/write, and the version constants
for normalization and chunking policy.

## Scope
- New file; no corpus-identity symbol exists in `scripts/rag/` (plan Background,
  absence search 2026-10-30).
- `scripts/db/schema_sql.py:38` `CREATE TABLE IF NOT EXISTS chunks` — meta table DDL is
  doc 02's row, not this module's.
- `scripts/rag/ingestion/pipeline_utils.py` `IngestedChunk.schema_version` region `:238`
  — reuse its schema-version semantics; do not duplicate version constants there
  (Reference Files row).
- `scripts/db/create_schema.py` `create_rag_schema` `:81`, `_execute_schema_ddl` `:38` —
  corpus_id generation hooks through ensure-on-first-use in this module, not by editing
  create_schema.py (it is not a target row).

## Assumptions
- Plan-level assumptions apply unchanged; see the Source plan Assumptions section.

## Design decisions
- `CorpusIdentity` (new): frozen dataclass — `corpus_id: str`, `index_generation: int`,
  `schema_version: str`, `embedding_model_id: str`, `normalization_version: str`,
  `chunking_policy_version: str`, `verified: bool`. `verified=False` encodes the
  identity-unverified state (REQ-007); equality compares only the six identity fields.
- `NORMALIZATION_VERSION` (new) and `CHUNKING_POLICY_VERSION` (new): module-level
  version constants (Assumptions `:148`), bumped by policy when those behaviors change.
- `compute_identity(db, *, embedding_model_id: str) -> CorpusIdentity` (new): reads the
  single `rag_corpus_meta` row, combines it with the current `schema_version`
  (`scripts/db/schema_sql.py` `WORKFLOW_SCHEMA_VERSION` `:25`-style constant read for the
  RAG schema; use the RAG schema value the meta row records) and the config-provided
  `embedding_model_id`; missing or corrupt meta row → `CorpusIdentity` with
  `verified=False`.
- `ensure_corpus_meta(db) -> CorpusIdentity | None` (new): creates the meta row with a
  fresh `uuid4` `corpus_id` and `index_generation=0` on first use (Assumptions `:147`:
  generated once, never regenerated); returns the identity or `None` when the table is
  absent (pre-migration databases).
- `bump_index_generation(db) -> int | None` (new): best-effort increment after a
  completed ingestion (Assumptions `:151`); returns the new generation or `None` on
  failure, leaving the previous generation in force.

## Alternatives considered
- No file-level alternatives beyond those evaluated in the Source plan; this procedure executes the selected option.

## Implementation
1. Create the module with the contract above; import only `scripts/db` helpers
   (`SQLiteHelper`) and stdlib (uuid, dataclasses) at the top-level layer contract
   (`skills/DESIGN.md` Shared Vocabulary).
2. Single-row access uses `INSERT ... ON CONFLICT` on the table's CHECK/rowid guard so
   the table stays single-row (row contract from doc 02).
3. All read paths tolerate a missing table (return `verified=False`) — startup and the
   gate both depend on this (REQ-007).

## Compatibility considerations
**Dependencies**:
- Upstream: doc 02 (`rag_corpus_meta` table must exist in schema before meta read/write)
**Blocks**: docs 06 (corpus-meta ensure/read), 08 (local identity for the gate), 13

## Security considerations
- No new security surface beyond what the Source plan records.

## Rollback considerations
- Revert this file together with its paired test rows in the same commit; the change is additive and gated by the plan's checkers.

## Validation plan
- `uv run pytest tests/rag/test_corpus_identity.py` (doc 15).

## Completion criteria
- Identity is stable across process restarts (same DB → same corpus_id and versions);
  corrupt/absent meta yields `verified=False`; no import cycle with `scripts/db`.

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
| `20261030-140156_02_scripts_db_schema_sql.py.md` | 1 (dependency) | Procedure | Pending | — | — |

## Marker record
- `(new)` markers applied: `CorpusIdentity`, `NORMALIZATION_VERSION`,
  `CHUNKING_POLICY_VERSION`, `compute_identity`, `ensure_corpus_meta`,
  `bump_index_generation` (Contract section).

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-001, REQ-003, REQ-007
- **Source issue**: `issues/20261029-104506_ragcorpus001_rag-corpus-identity.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/done/20261030-013620_ragcorpus001_rag-corpus-identity.md` — Implementation Target Files row 01
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-140156
- **Related target files**: `scripts/rag/corpus_identity.py`
