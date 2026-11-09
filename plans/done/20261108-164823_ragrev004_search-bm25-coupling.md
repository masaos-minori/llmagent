## Goal
- Make the search stage run the BM25 (FTS) leg independently of the embedding and the vector-search leg, so an embedding outage or a vector-search error still returns lexical hits, while each failed leg is counted and the stage reports `fallback` only when no leg returned anything.

## Priority
Medium

## Scope
- **In-Scope**:
  - `_search_all_queries` in `scripts/rag/stages/search.py`: FTS runs for every query regardless of embedding/vector outcome, with its own error handling.
  - Failure accounting: keep the combined `fts_errors` counter (its existing log text already says "FTS/vec errors") counted once per failed retrieval leg, and document that meaning.
  - Updating the existing tests that encode the coupling, plus new tests for the two failure shapes.
  - The search-stage description in the RAG docs.
- **Out-of-Scope**:
  - Ranking, fusion, FTS query construction (sibling `issues/20261108-131008_ragrev005_fts-query-and-semantics.md`), a new `SearchDiagnostics` field, concurrency of DB access.
- **Dependencies**: Related, no required order: the ragrev005 work (FTS query construction, same retrieval leg; lands in `scripts/rag/repository.py`, not in this plan's files).

## Background
Review finding F-006. In `_search_all_queries` (`scripts/rag/stages/search.py:27-84`) a failed or non-list embedding takes a `continue` branch before `repo.fts_search` (L51-58), and `repo.vector_search` and `repo.fts_search` share one `try` (L60-75), so a vector-search exception skips FTS for that query and increments `fts_errors`. `SearchStage.get_status` reports `fallback` only when `ctx.search_results` is empty (L101-107), which already matches the Issue's "fallback only when both paths are empty" once FTS contributes. Pinned elsewhere (checked in Step 3): `test_run_pack_failure_degrades` asserts a vector-leg `ValueError` is counted in `fts_errors` (`tests/rag/test_rag_stages.py:289-315`); `test_run_search_exception` (L262-286) asserts `search_results == []` with a patched `RagRepository` whose default `fts_search` return is a truthy `MagicMock`, so it currently passes only because the FTS call is skipped. Corrected at procedure time (adversarial verification): `test_run_embedding_not_list` (L244-259) does not patch `RagRepository`; with the split, the real `RagRepository.fts_search` runs against the `mock_db` fixture and returns `[]` (verified by running it against a `MagicMock` database), so that test passes unchanged and needs no edit. Two more tests use the patched repository with a vector error and the default truthy `fts_search` stub: `test_fts_error_counts` (L~410) and `test_warning_emitted_on_fts_error` (L~480); they assert only the `fts_errors` counter and the log text, so they keep passing, and get an explicit empty FTS stub for clarity. `tests/rag/test_rag_quality_regression.py` (`run(..., db=MagicMock())` with failing embeddings, asserting `reranked == []`) is unaffected for the same reason (real `fts_search` over a mock database returns `[]`). The docs state the coupling as intended behavior: "returns empty if embedding or DB error occurs" (`docs/21_rag/rag_03_04_query_pipeline-search-stages.md:40`).

## Problem
When the embedding service is down or a vector query fails, retrieval returns nothing although the lexical index could answer, and the diagnostics blame FTS.

## Reason for Change
A degraded-but-useful result beats an empty one for the likeliest local failure (embedding server restart).

## Implementation Intent
Restructure the per-query loop into two legs: an embedding-dependent vector leg and an independent FTS leg, each in its own `try`, each failure counted once in the existing counters (`embed_failed` for the embedding, `fts_errors` for either retrieval leg). The existing test contract for the `fts_errors` meaning is kept by choosing the Issue's "document the combined counter" option rather than adding a field.

## Requirements
- `REQ-001`: With every embedding failing (exception or non-list), the stage returns the FTS hits and `embed_failed` equals the number of queries.
- `REQ-002`: A vector-search error (`OperationalError`, `RuntimeError`, `ValueError`, `OverflowError`, `struct.error`) does not suppress the FTS hits for the same query.
- `REQ-003`: Each failed retrieval leg increments `fts_errors` once (vector leg and FTS leg counted separately per query); `degraded` is true when any embedding or leg failed; field names and `SearchDiagnostics` shape are unchanged.
- `REQ-004`: The stage status is `fallback` / `no search results` only when no leg returned hits.
- `REQ-005`: Embedding fetch stays concurrent and DB access stays sequential on one connection.
- `REQ-006`: Existing tests that encode the coupling (`test_run_search_exception`, plus the clarity updates to `test_fts_error_counts` and `test_warning_emitted_on_fts_error`) are updated explicitly (not deleted) and the pinned `test_run_pack_failure_degrades` passes unmodified.
- `REQ-007`: The search-stage doc describes independent legs and the combined `fts_errors` meaning.

## Implementation Target Files
**Freeze status**: Frozen

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `tests/rag/test_rag_stages.py` | Modify | New tests (all-embeddings-fail, vector error with FTS hits); set `fts_search.return_value = []` in `test_run_search_exception` (required) and in `test_fts_error_counts` / `test_warning_emitted_on_fts_error` (clarity); `test_run_embedding_not_list` stays unchanged | `REQ-001`, `REQ-002`, `REQ-003`, `REQ-006` / AC-1, AC-2, AC-3, AC-6 | `test_run_search_exception` (L262-286) passes only via the skipped FTS call; `test_run_embedding_not_list` (L244-259) uses the real repository over `mock_db` and is unaffected; L289-315 pinned (checked in Step 3 and re-verified at procedure time) | self | Verified |
| `scripts/rag/stages/search.py` | Modify | Split vector and FTS legs into independent guarded blocks; run FTS after embedding failure | `REQ-001`..`REQ-005` / AC-1..AC-5 | `continue` at L51-58, shared `try` L60-75 (checked in Step 3) | `tests/rag/test_rag_stages.py` | Verified |
| `docs/21_rag/rag_03_04_query_pipeline-search-stages.md` | Modify | Replace the "returns empty if embedding or DB error occurs" statement and the per-query error-handling note | `REQ-007` / AC-7 | L40 and L46 state the coupled behavior (checked in Step 3) | docs gates | Verified |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/rag/models_result.py` | `SearchDiagnostics` fields stay unchanged | `REQ-003` |
| `scripts/rag/repository.py` | `vector_search` / `fts_search` raise sites and error types | `REQ-002` |
| `scripts/rag/diagnostics.py` | `degraded` derivation (`embed_failed > 0 or fts_errors > 0`) | `REQ-003` |
| `scripts/rag/stage_lifecycle.py` | Consumer that accumulates `stat_search_*` counters | `REQ-003` |
| `tests/rag/test_diagnostics.py` | Frozen diagnostics contract; must stay green | `REQ-003` |
| `tests/rag/test_stage_observability.py` | Asserts `SearchStage` `fallback` / `no search results` on an empty DB | `REQ-004` |

## Acceptance Criteria
- AC-1 (`REQ-001`): all-embeddings-failing run returns the FTS hits; `embed_failed == len(queries)`.
- AC-2 (`REQ-002`): vector `OperationalError` still yields the FTS hits for that query.
- AC-3 (`REQ-003`): a query whose vector and FTS legs both fail adds 2 to `fts_errors`; the pinned test keeps `fts_errors == 1` for its single vector failure; `SearchDiagnostics` fields unchanged.
- AC-4 (`REQ-004`): empty-DB run still reports `fallback` / `no search results`.
- AC-5 (`REQ-005`): the embedding `gather` call and the single `RagRepository(db)` use are unchanged.
- AC-6 (`REQ-006`): `test_run_pack_failure_degrades` and `test_diagnostics.py` pass unmodified; the updated tests still assert their original intent (no crash, results reflect the FTS stub), and `test_run_embedding_not_list` and `tests/rag/test_rag_quality_regression.py` pass unmodified.
- AC-7 (`REQ-007`): the doc names independent legs and the combined counter; docs checkers pass.

## Tests
- `REQ-001`: fake repository, every `get_embedding` raising; FTS stub returns hits.
- `REQ-002`: vector stub raising `sqlite3.OperationalError`; FTS stub returns hits.
- `REQ-003`: both legs raising; counter equals 2; single vector failure equals 1 (existing pinned test).
- `REQ-004`: existing observability test unmodified.
- `REQ-006`: `test_run_search_exception` (and, for clarity, `test_fts_error_counts` and `test_warning_emitted_on_fts_error`) updated with an explicit empty FTS stub.

## Documentation Impact
Yes (`REQ-007`): `docs/21_rag/rag_03_04_query_pipeline-search-stages.md` (located via `docs/00_index.md` RAG rows). Run `check_docs_quality`, `check_docs_structure`, `check_docs_content_policy`, `check_docs_consistency --domain rag`, `check_docs_japanese`. The `SearchDiagnostics` description in `docs/21_rag/rag_04_dto-models-types.md` stays accurate under the combined-counter choice and is not edited.

## Assumptions
- Overlap judgments (Step 2, `tools/check_plan_target_overlaps.py`): `plans/20261108-165229_ragrev007_mqe-queries-uncapped-duplicated.md` shares `scripts/rag/stages/search.py`, `tests/rag/test_rag_stages.py`, and `docs/21_rag/rag_03_04_query_pipeline-search-stages.md`; it is a sequencing dependency, not a conflict: ragrev007 declares `Depends on` this Plan's phase 2 (it wraps the embedding `gather` after this leg split lands), edits the MQE paragraph (L34) of the doc while this Plan edits the SearchStage paragraph (L40, L46), and adds its own tests. `plans/20261108-164946_ragrev005_fts-query-and-semantics.md` targets `scripts/rag/repository.py` (FTS query construction), not this Plan's files; compatible, no required order.
- Keeping the combined `fts_errors` counter is acceptable to consumers; `stat_search_fts_errors` and `get_diagnostics()` keys stay as they are.
- A dimension mismatch reported by sqlite-vec surfaces as an exception from `vector_search` caught by the existing tuple; the repository shows no explicit dimension check, and the exact exception type was not reproduced (Unknowns).

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Exact exception raised for a wrong-dimension embedding by sqlite-vec | No reproduction run against `vec0` | Implementation phase may add a real-DB test; the leg handler catches the existing tuple regardless | False |
| UNK-02 | Whether the owner prefers a separate `vector_errors` field over the combined counter | Owner preference | Default is the combined counter; a separate field would be a new plan (consumer-visible change) | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/rag/stages/search.py` | Modify | Medium (the retrieval stage of every RAG query; sole caller is `stage_lifecycle.py`) | 1 | N/A | not applicable (rsynced) |
| `tests/rag/test_rag_stages.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `docs/21_rag/rag_03_04_query_pipeline-search-stages.md` | Modify | Low | N/A | N/A | not applicable (rsynced) |

## Design
Path A (3 target files, no interface or schema change). Complexity baseline: `radon cc` shows `_search_all_queries` B (9); the per-leg split goes into a small private helper per leg so the function does not grow past B.

Alternatives: (a) add a `vector_errors` field rejected (Issue constraint: field names stable; would also invalidate the pinned `fts_errors == 1` test semantics); (b) catch around the whole query rejected (it is the current defect). Chosen: two independent guarded legs, combined counter documented.

Validation baseline: `vulture`/`bandit` pre-existing findings recorded in `plans/20261108-164302_ragrev001_mqe-malformed-response-abort.md` (source unchanged). `diff-cover`: no changed lines at plan time; 90 percent at implementation.

## Implementation steps
1. **Phase 1: Tests first**
   - [ ] Add the two new failure-shape tests and update the two coupling-encoding tests (`REQ-001`, `REQ-002`, `REQ-003`, `REQ-006`; `tests/rag/test_rag_stages.py`)
2. **Phase 2: Independent legs**
   - [ ] Restructure `_search_all_queries` into guarded vector and FTS legs (`REQ-001`..`REQ-005`; `scripts/rag/stages/search.py`)
3. **Phase 3: Documentation**
   - [ ] Update the search-stage description (`REQ-007`; `docs/21_rag/rag_03_04_query_pipeline-search-stages.md`)
4. **Phase 4: Deployment & Verification**
   - [ ] `uv run pytest tests/rag -q`, lint/type gates, docs gates; deploy hand-off to `skills/deploy/SKILL.md` after commit and push, at the user's decision (all requirements; `scripts/rag/stages/search.py`)

### Release units
N/A: no release unit

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/rag/stages/search.py` | Unit (fake repository) | `uv run pytest tests/rag/test_rag_stages.py -q` | new tests fail on HEAD, pass after; pinned test unmodified |
| diagnostics contract | Regression | `uv run pytest tests/rag/test_diagnostics.py tests/rag/test_stage_observability.py -q` | green |
| whole RAG | Regression | `uv run pytest tests/rag -q` | green |
| touched code | Static | `uv run ruff check`, `uv run mypy`, `PYTHONPATH=scripts uv run lint-imports` | clean |
| docs | Docs gates | `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py`, `check_docs_consistency.py --domain rag`, `check_docs_japanese.py` | no findings |

## Risks
- **Risk**: running FTS when embeddings fail changes result sets and latency for outages (more FTS queries than before) → **Mitigation**: FTS was already run for every successful query; the added load is bounded by the query count.
- **Risk**: `fts_errors` per-leg counting inflates the counter versus per-query counting → **Mitigation**: documented (`REQ-007`); the pinned single-failure case stays 1.
- **Risk**: dimension-mismatch exception type differs from the caught tuple → **Mitigation**: UNK-01; add a real `vec0` test at implementation if the extension is available, else report.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: tests first | Completed | — | 20261109-145634 |  |
| 2 | Phase 2: independent legs | Completed | — | 20261109-145634 |  |
| 3 | Phase 3: documentation | Completed | — | 20261109-145634 |  |
| 4 | Phase 4: deployment and verification | Pending | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261109-121538_01_tests_rag_test_rag_stages.py.md | 1 | Procedure | Completed | — | — |
| implementations/20261109-121538_02_scripts_rag_stages_search.py.md | 2 | Procedure | Completed | — | — |
| implementations/20261109-121538_03_docs_21_rag_rag_03_04_query_pipeline-search-stages.md.md | 3 | Procedure | Completed | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261108-131007_ragrev004_search-bm25-coupling.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261108-164823
- **Related target files**: `scripts/rag/stages/search.py`, `tests/rag/test_rag_stages.py`, `docs/21_rag/rag_03_04_query_pipeline-search-stages.md`

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Acceptance Criteria 1; `search.py:51-58` | `scripts/rag/stages/search.py` | Phase 2 | AC-1 | all-embeddings-fail test | Confirmed by repository evidence |
| REQ-001 | Testing Expectations | `tests/rag/test_rag_stages.py` | Phase 1 | AC-1 | all-embeddings-fail test | Explicit in issue |
| REQ-002 | Acceptance Criteria 2; `search.py:60-75` | `scripts/rag/stages/search.py` | Phase 2 | AC-2 | vector-error test | Confirmed by repository evidence |
| REQ-002 | Testing Expectations | `tests/rag/test_rag_stages.py` | Phase 1 | AC-2 | vector-error test | Explicit in issue |
| REQ-003 | Required Changes 2 (combined counter option) | `scripts/rag/stages/search.py` | Phase 2 | AC-3 | both-legs-fail test, pinned test | Derived from confirmed evidence |
| REQ-003 | Constraints | `tests/rag/test_rag_stages.py` | Phase 1 | AC-3 | both-legs-fail test | Derived from confirmed evidence |
| REQ-004 | Implementation Intent | `scripts/rag/stages/search.py` | Phase 2 | AC-4 | `test_stage_observability.py` | Confirmed by repository evidence |
| REQ-005 | Constraints | `scripts/rag/stages/search.py` | Phase 2 | AC-5 | code review of the unchanged gather and single repository | Explicit in issue |
| REQ-006 | Step 3 finding: coupling-encoding tests | `tests/rag/test_rag_stages.py` | Phase 1 | AC-6 | updated tests, pinned test | Confirmed by repository evidence |
| REQ-007 | Documentation Impact; doc L40, L46 | `docs/21_rag/rag_03_04_query_pipeline-search-stages.md` | Phase 3 | AC-7 | docs gates | Confirmed by repository evidence |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261109-121538 -->
