# Implementation procedure: `scripts/rag/stages/search.py` — packing-failure backstop in `_search_all_queries`

## Goal
Catch packing-related failures surfacing from `repo.vector_search` / `repo.fts_search` per query so they are recorded in the `SearchDiagnostics` degraded counters instead of escaping the stage (`REQ-003`: backstop catch; `REQ-004`: run completes degraded, remaining queries continue).

## Scope
**Release unit**: ragvec001-full

- Widen the per-query `except` tuple in `_search_all_queries` to include `ValueError`, `OverflowError`, `struct.error`.
- Companion test file `tests/rag/test_rag_stages.py` gets the backstop and multi-query degraded cases.

## Assumptions
- Gated: `issues/20261107-050701_adrrag001_rag-fallback-failure-policy.md` phase all - prose dependency on an open issue; the Plan's own Scope records "Related, no order required".
- Counting a backstop failure under the existing `fts_errors` counter is acceptable; no new counter is introduced (Plan `Assumptions`).
- The Plan's Implementation Target Files and Implementation steps assign the pipeline-level degraded test (Acceptance Criteria `REQ-004`) to `tests/rag/test_rag_stages.py`, so this document writes it at the `_search_all_queries` multi-query level there; `tests/rag/test_rag_pipeline.py` stays a regression gate, not a modification target.

## Design decisions
- Defense in depth at the stage: after `REQ-001`/`REQ-002` the primary paths never reach this catch, but any future pack path that bypasses both boundaries degrades per-query instead of aborting the whole run (Plan Design "Backstop").
- Lifecycle-level catch was rejected: adding `OverflowError` to `scripts/rag/stage_lifecycle.py` `_run_stage`'s tuple would abort the stage for one bad query and lose valid-query results in the same run (Plan Design "Why not lifecycle-level catch").

## Alternatives considered
- Leave the stage untouched once the two boundaries exist: rejected by `REQ-003` — the Plan pins the backstop as the contract that makes the containment testable.

## Implementation
### Target file
`scripts/rag/stages/search.py`

### Procedure
1. Add `import struct` (new) to the module's stdlib import block (the module imports `asyncio` and `sqlite3` today, not `struct`).
2. Widen the per-query handler in `_search_all_queries` from `except (sqlite3.OperationalError, RuntimeError)` to `except (sqlite3.OperationalError, RuntimeError, ValueError, OverflowError, struct.error)`, keeping the existing WARNING log and `fts_errors += 1`.
3. Keep the surrounding loop semantics unchanged: failed query is skipped, remaining queries continue, `degraded = embed_failed > 0 or fts_errors > 0` already reflects the new counts.

### Method
- Single except-tuple edit; no new counter, no control-flow change. The WARNING log already includes the query text and exception message, satisfying the Plan `Risks` mitigation ("Log at WARNING with the original message") for the swallowed-`ValueError` observability concern.

### Details
- Current state (verified at HEAD `eb19564fe`): `_search_all_queries` embeds all queries with `return_exceptions=True` (exceptions → `embed_failed`), then runs `repo.vector_search(result, cfg.top_k_search)` and `repo.fts_search(q, cfg.top_k_search)` in one `try` per query whose except tuple is `(sqlite3.OperationalError, RuntimeError)` → `fts_errors += 1`.
- Both searches share one `try`, so a pack failure in `vector_search` currently also skips that query's FTS search — acceptable degraded behavior (the query is recorded as failed either way).

### Companion test files
- `tests/rag/test_rag_stages.py`
  - Procedure: add a case stubbing `vector_search` to raise `ValueError` for one query of a multi-query run → `fts_errors == 1`, `degraded` true, remaining queries still searched; add a `REQ-004` multi-query case where one embed response contains `1e300` (post-`REQ-001` behavior) → `embed_failed == 1` and valid queries return results.
  - Validation: `uv run pytest tests/rag/test_rag_stages.py -v` — the forced-failure case fails on pre-change HEAD (exception propagates) and passes after the change (`REQ-005`).

## Compatibility considerations
- Widening the except tuple changes observable behavior only for exceptions that previously escaped the stage: `ValueError` from `floats_to_blob` (post-`REQ-002`), `OverflowError`/`struct.error` from any pack path. Callers of `_search_all_queries` see the same return shape (`all_results`, `SearchDiagnostics`).
- Risk accepted from the Plan (`Risks` row 2): an unrelated future `ValueError` bug becomes degraded instead of visible — mitigated by the WARNING log and observable counters.
- Stage-behavior doc update is covered by sibling document `20261108-091441_07_docs_21_rag_rag_03_04_query_pipeline-search-stages.md.md` (Plan Phase 4).

## Security considerations
- N/A: error-handling scope only; no new input surface or trust-boundary change (the validation itself lives in the `llm_client`/`utils` procedures).

## Rollback considerations
- N/A: revert the commit — behavior reverts to the pre-change except tuple.

## Validation plan
| Target | Strategy | Command | Expected |
|---|---|---|---|
| `scripts/rag/stages/search.py` | stage unit (companion file) | `uv run pytest tests/rag/test_rag_stages.py -v` | backstop and degraded cases fail pre-fix, pass post-fix |
| pipeline regression | existing suite | `uv run pytest tests/rag/test_rag_pipeline.py -q` | unchanged for valid embeddings |
| gates | static | `rules/toolchain.md` sequence (ruff → mypy → lint-imports → bandit) | clean, no new suppressions |

## Completion criteria
- A forced pack failure in `vector_search` for one query increments `fts_errors`, sets `degraded`, and does not stop remaining queries (`Acceptance Criteria REQ-003`).
- A multi-query run containing one out-of-range embedding completes with `embed_failed >= 1` and results for valid queries (`Acceptance Criteria REQ-004`).
- Companion tests fail on pre-change HEAD and pass after the change (`REQ-005`).

## Out of Scope
- `scripts/rag/stage_lifecycle.py` caught tuple (Plan Reference Files: confirmed no-change).
- `tests/rag/test_rag_pipeline.py` as a modification target (regression gate only, per Assumptions).
- Counters/diagnostics structure in `scripts/rag/diagnostics.py` (read-only reference).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 20261108-111340 | Gated: issues/20261107-050701_adrrag001_rag-fallback-failure-policy.md phase all - prose dependency; Plan Scope records "Related, no order required" authorized by owner memo3; changed scripts/rag/stages/search.py |
| 2 | Add or update tests per Validation plan (companion test file) | Completed | — | 20261108-111340 | Gated: issues/20261107-050701_adrrag001_rag-fallback-failure-policy.md phase all - prose dependency; Plan Scope records "Related, no order required" authorized by owner memo3; pre-change 1 failed/62 passed (REQ-005, ValueError escaped stage); post-change 63 passed + test_rag_pipeline regression gate green |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261108-111340 | 20261108-114215 | Gated: issues/20261107-050701_adrrag001_rag-fallback-failure-policy.md phase all - prose dependency; Plan Scope records "Related, no order required" authorized by owner memo3; ruff/mypy(scoped)/bandit pass; lint-imports and full suite at end of release unit ragvec001-full validation sequence pass; end-of-unit full suite 11841 passed 9 skipped; diff-cover 100 percent on changed lines |

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
- **Requirement ID**: `REQ-003` (packing-failure backstop, degraded counting), `REQ-004` (run completes degraded)
- **Source issue**: `issues/20261107-203511_ragvec001_rag-embedding-float32-overflow.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261108-075301_ragvec001_rag-embedding-float32-overflow.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261108-091441
- **Related target files**: `scripts/rag/stages/search.py`, `tests/rag/test_rag_stages.py`