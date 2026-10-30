# Implementation Procedure: `scripts/db/rag_consistency_queries.py` (RAGCORPUS001 Phase 1)

**Plan**: `plans/done/20261030-013620_ragcorpus001_rag-corpus-identity.md` (REQ-005)

## Goal
Add the fatal-class detection queries the checker currently lacks: FK consistency
(chunks→documents), embedding-dimension mismatch, unknown schema shape, and
corpus-meta presence.

## Scope
- Count collectors: `_collect_basic_counts` `:23`, `_collect_document_checks` `:36`,
  `_collect_url_counts_and_mismatches` `:61`, `_check_read_smoke_test` `:212`.
- No dimension/FK/schema/meta checks exist today (plan Background `:31`, absence
  search 2026-10-30).
- Query helpers to reuse: `_query_ids_or_none` `:107`, `_query_pairs` `:115`.

## Assumptions
- Plan-level assumptions apply unchanged; see the Source plan Assumptions section.

## Design decisions
- `_check_fk_consistency(db) -> int` (new): count of chunks whose `doc_id` has no
  documents row (chunks→documents FK integrity, reported count; 0 = clean).
- `_check_embedding_dimension(db, expected_dims) -> bool` (new): compare the stored
  vector dimension in `chunks_vec` (via `vec0` virtual-table row sample or the dimension
  recorded at schema build) against the configured dimension; mismatch = fatal.
  `expected_dims` flows from the same config value `build_rag_schema_sql(dims)` consumes
  (`scripts/db/schema_sql.py:158`).
- `_check_schema_recognition(db) -> bool` (new): verify the expected RAG tables exist
  and no unrecognized top-level tables shadow them; unrecognized = fatal.
- `_check_corpus_meta(db) -> bool` (new): corpus-meta presence/well-formedness
  (single-row `rag_corpus_meta` from doc 02); absent/corrupt = unverifiable-generation
  fatal class. Tolerates the pre-migration window: reports False only when the ledger
  has already been applied — coordinate with doc 02's migration registration so fresh
  DBs and migrated DBs both satisfy the check.

## Alternatives considered
- No file-level alternatives beyond those evaluated in the Source plan; this procedure executes the selected option.

## Implementation
1. Add the four functions using the existing query helpers; keep each query read-only
   and single-statement so startup cost stays bounded (UNK-02: measure new-query cost
   during Phase 1 against production corpus size; adjust ordering/timeout if needed —
   Needs Confirmation).
2. Wire results into the counts tuple consumed by `check_rag_consistency` (doc 03
   adapts the report fields via doc 05).

## Compatibility considerations
**Dependencies**: none upstream (feeds doc 03)
**Blocks**: docs 03, 05 (new report counters), 19

## Security considerations
- No new security surface beyond what the Source plan records.

## Rollback considerations
- Revert this file together with its paired test rows in the same commit; the change is additive and gated by the plan's checkers.

## Validation plan
- `uv run pytest tests/db/test_rag_consistency.py` (doc 19 covers each new class).

## Completion criteria
- Each new check returns its severity-driving value deterministically; startup check
  duration under the 30s budget is measured and recorded (UNK-02 resolution evidence).

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
| `20261030-140156_03_scripts_db_rag_consistency.py.md` | 1 (dependency) | Procedure | Pending | — | — |

## Marker record
- `(new)` markers applied: `_check_fk_consistency`, `_check_embedding_dimension`,
  `_check_schema_recognition`, `_check_corpus_meta` (Contract section).

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-005
- **Source issue**: `issues/20261029-104506_ragcorpus001_rag-corpus-identity.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/done/20261030-013620_ragcorpus001_rag-corpus-identity.md` — Implementation Target Files row 04
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-140156
- **Related target files**: `scripts/db/rag_consistency_queries.py`
