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
Resolved two ambiguities before coding (see Blocker Log below). Both resolutions keep
`scripts/rag/corpus_identity.py` free of the `rag_corpus_meta` DDL (doc 02 owns the DDL)
and avoid a hard import dependency on `scripts/db/schema_sql.py` (doc 02 lands later).

- `CorpusIdentity` (new): frozen dataclass — `corpus_id: str`, `index_generation: int`,
  `schema_version: str`, `embedding_model_id: str`, `normalization_version: str`,
  `chunking_policy_version: str`, `verified: bool`. `verified=False` encodes the
  identity-unverified state (REQ-007); equality compares only the six identity fields.
- `NORMALIZATION_VERSION` (new) and `CHUNKING_POLICY_VERSION` (new): module-level
  version constants (Assumptions `:148`), bumped by policy when those behaviors change.
- **`schema_version` source (resolved).** `rag_corpus_meta` stores NO `schema_version`
  column (plan Design `:184` column list is authoritative: `corpus_id, index_generation,
  embedding_model_id, normalization_version, chunking_policy_version, updated_at`). The
  identity's `schema_version` is the *current* RAG schema version, supplied by the caller
  as a `schema_version: str` keyword argument to `compute_identity` — it is not read from
  the meta row and not imported from `schema_sql.py` (which has no RAG-schema version
  constant until doc 02). This keeps doc 01 independent of doc 02 and matches the plan's
  "effective identity = meta row + current schema_version" model. `REQ-001`'s "stored in a
  single-row table" is satisfied for the five stored identity columns; `schema_version` is
  a live property of the running schema, not a persisted column.
- `compute_identity(db, *, embedding_model_id: str, schema_version: str) -> CorpusIdentity`
  (new): reads the single `rag_corpus_meta` row via `SQLiteHelper`, combines it with the
  caller-supplied `schema_version` and `embedding_model_id`; missing/corrupt/absent meta
  row → `CorpusIdentity` with `verified=False`.
- `ensure_corpus_meta(db) -> CorpusIdentity | None` (new): ensures a meta ROW exists in an
  already-created table — if the table exists and has no row, inserts one with a fresh
  `uuid4` `corpus_id` and `index_generation=0` (Assumptions `:147`: generated once, never
  regenerated), then returns the identity; if the table is absent (pre-migration
  database) returns `None`. The table itself is created by doc 02's DDL, never inline here.
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
| 1 | Re-verify cited anchors before editing | Completed | 20261031-091056 | 20261031-091105 |  |
| 2 | Apply the Implementation procedure | Completed | 20261031-091056 | 20261031-091105 |  |
| 3 | Run the Validation plan gates | Completed | 20261031-091056 | 20261031-091105 | ruff/mypy/lint-imports/bandit(-ll)/ast-grep all clean after the __eq__/__hash__ fix. Smoke test /tmp/smoke_corpus_identity.py exercises every path (absent->None/unverified, generated-once corpus_id, bump increments, corrupt row->unverified, restart persistence, equality ignores verified): SMOKE OK. Formal pytest tests/rag/test_corpus_identity.py is doc 15's target, created later in seq order -> Not run here. No docs/00_index.md task-scope mapping for scripts/rag/corpus_identity.py -> Step 5 N/A. |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1–2 | Table-creation dependency: doc 01 must be testable before doc 02 lands, but the `rag_corpus_meta` DDL is doc 02's row and `schema_sql.py` has no RAG-schema version constant yet. | Yes | 2026-10-31 |
| 1–2 | `schema_version` column conflict: plan Design `:184` lists `rag_corpus_meta` columns WITHOUT `schema_version`; REQ-001 and `CorpusIdentity` include it. | Yes | 2026-10-31 |

Resolution (recorded in Design decisions above): `ensure_corpus_meta` ensures a ROW in an
already-created table and returns `None` when the table is absent (never creates the table
inline — doc 02 owns the DDL). `compute_identity` takes `schema_version` as a caller-supplied
keyword arg (the current RAG schema version), so doc 01 imports nothing from `schema_sql.py`.
The test fixture (doc 15) creates its own minimal `rag_corpus_meta` table so the module is
testable in isolation.

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