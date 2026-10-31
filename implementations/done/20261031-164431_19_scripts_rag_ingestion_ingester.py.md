# Implementation Procedure: `scripts/rag/ingestion/ingester.py` (RAGCORPUS001 Phase 2)

**Plan**: `plans/done/20261030-013620_ragcorpus001_rag-corpus-identity.md` (REQ-001)

## Goal
Advance the corpus `index_generation` once a full `ingest_all()` run has written new
content, so the local identity records that the index changed (REQ-001).

## Scope
- `Ingestor.ingest_all()` `:142-200`: the sole ingestion completion point. It opens the
  rag DB in write mode (`:159-164`), processes all URL groups, runs
  `doc_manager.check_consistency()` (`:170-175`), and returns the post-ingestion report
  at `:200`. The `with ... .open(...)` context closes `db` at `:175`, so the bump must
  fire **inside** that block, immediately after `check_consistency()`.
- `bump_index_generation(db)` (`rag.corpus_identity`, doc 01): best-effort increment;
  returns the new generation, or `None` on failure without raising.
- CLI entry `ingester.py:402` (`ingest_all(args.force)`) is the only caller; incremental
  and `--force` re-ingest both flow through `ingest_all()`.
- Reference Files only: `rag_maintenance_service::rebuild_fts()/rebuild_vec()` are NOT
  targets — they rebuild existing indexes without changing content, and bumping there
  would advance `index_generation` on a content-neutral op and risk a false identity
  mismatch.

## Assumptions
- Recorded open items: none.
- Plan-level assumptions apply unchanged; see the Source plan Assumptions section.
- A run that processes no chunk files returns `None` early (`:153-155`) and must NOT bump
  (nothing was written). A run whose groups are all skips (already-registered URLs) also
  leaves the index content unchanged and must NOT bump.
- `schema_version` is irrelevant to the bump; `bump_index_generation()` only touches
  `index_generation`.

## Design decisions
- Fire the bump inside the `with` block, right after `check_consistency()` (`:175`), while
  `db` is still open (the writer is committed by then).
- Gate the bump on actual content change: `if results and any(not r.skipped for r in
  results)`. This advances generation for new documents and `--force` re-ingests, and
  stays idle on no-op runs (no chunk files, or every group skipped).
- Do NOT additionally gate on `consistency_report is not None`: a non-`None` report with
  issues is still a completed write; a `None` report only occurs on the no-chunk-files
  early return (already excluded by the empty-`results` guard).
- Rely on `bump_index_generation()`'s built-in best-effort contract (never raises; leaves
  the previous generation in force on failure) — no extra try/except needed here.

## Alternatives considered
- No file-level alternatives beyond those evaluated in the Source plan; this procedure
  executes the selected option.

## Implementation
1. Import `bump_index_generation` from `rag.corpus_identity` (add to the existing
   `rag.*` import block; `SQLiteHelper` is already imported from `db.helper`).
2. In `ingest_all()`, after the `check_consistency()` call at `:170-175` and still inside
   the `with` block, add:
   ```python
   # RAGCORPUS001 REQ-001: advance the corpus index generation once this run has
   # written new content. Best-effort — a failed bump leaves the previous
   # generation in force and never breaks ingestion completion.
   if results and any(not r.skipped for r in results):
       bump_index_generation(db)
   ```

## Compatibility considerations
**Dependencies**: upstream: doc 01 (identity module — shared-library import convention,
**Blocks**: N/A

## Security considerations
- No new security surface. `bump_index_generation()` parameterizes the UPDATE and never
  logs the generation value beyond the existing completion log line.

## Rollback considerations
- Revert this file together with its paired test row in the same commit; the change is a
  single additive call gated by the plan's checkers.

## Validation plan
- `uv run pytest tests/rag/test_ingester_index_generation.py` (new): seeded temp DB →
  `index_generation` advances by one on a real ingest and stays put on a no-op run;
  missing-table path returns `None` without raising.

## Completion criteria
- A completed `ingest_all()` that wrote new content advances `index_generation` by exactly
  one; a no-op run (no chunk files / all skips) leaves it unchanged; a missing meta table
  yields `None` without raising.

## Out of Scope
- Everything outside `ingest_all()`; the maintenance `rebuild_*` paths are intentionally
  excluded (see Scope).

## Execution Status
### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Re-verify cited anchors before editing | Completed | — | — |  |
| 2 | Apply the Implementation procedure | Completed | — | — |  |
| 3 | Run the Validation plan gates | Completed | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|

## Marker record
- `(new)` markers applied: `bump_index_generation` call in `ingest_all()`.

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-001
- **Source issue**: `issues/20261029-104506_ragcorpus001_rag-corpus-identity.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/done/20261030-013620_ragcorpus001_rag-corpus-identity.md` — Implementation Target Files row (ingester.py)
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261031-164431
- **Related target files**: `scripts/rag/ingestion/ingester.py`