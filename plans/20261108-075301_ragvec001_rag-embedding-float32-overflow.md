## Goal
Make a query embedding whose magnitude exceeds the float32 range a handled, degraded search failure in the RAG query pipeline instead of an uncaught `OverflowError` that aborts the whole pipeline run. Validate at the provider-response boundary (`get_embedding`), make `floats_to_blob` raise a typed `ValueError` for out-of-range values (correcting its own docstring), and give `SearchStage` a backstop so packing failures are recorded in the existing `SearchDiagnostics` degraded contract.

## Priority
Medium

## Scope
- **In-Scope**:
  - `scripts/rag/llm_client.py` — `get_embedding`: validate that every returned element is finite and within the float32 range before the embedding is used.
  - `scripts/rag/utils.py` — `floats_to_blob` / `_validate_float_list`: typed out-of-range check raising `ValueError`; docstring correction (out-of-range currently documented as `struct.error`, actually `OverflowError` live).
  - `scripts/rag/stages/search.py` — backstop handler so a packing failure from `vector_search` is counted as degraded instead of escaping.
  - Tests for the three boundaries and the end-to-end degraded contract.
  - Docs: query-pipeline search-stage behavior, query helper contract, shared-utility contract.
- **Out-of-Scope**:
  - The ingestion pack step `floats_to_blob(embedding)` at `scripts/rag/ingestion/embedding.py:109` (same crash pattern on the ingestion path; already recorded as an adjacent gap in the issue's Adversarial Validation).
  - The private `_floats_to_blob` copy in `scripts/agent/memory/mapper.py:35` (same overflow pattern, agent memory path; candidate follow-up issue).
  - Changing storage format (float32 BLOB), `top_k` semantics, or the pipeline stage structure.
  - Adding `OverflowError`/`struct.error` to `stage_lifecycle.py`'s caught tuple — with the two boundaries plus the stage backstop, the escape is fully contained at the search stage; widening the lifecycle catch is not needed.
- **Dependencies**: Related, no order required: open issue `issues/20261107-050701_adrrag001_rag-fallback-failure-policy.md` (cause-based failure policy for the HTTP-delegation fallback path; distinct boundary — this Plan is the in-process query path). Distinct from archived `issues/done/20261104-143443_ragverify001_complete-fail-closed-rag-consistency.md`, which checks stored row byte-length/dimension (`scripts/db/rag_consistency.py`), not query-time magnitude. No open `plans/*.md` touches `scripts/rag/llm_client.py`, `scripts/rag/utils.py`, or `scripts/rag/stages/search.py`.

## Background
The query path converts each query embedding to a float32 BLOB before the sqlite-vec KNN match: `SearchStage` → `get_embedding` (`scripts/rag/llm_client.py:266-285`) → `RagRepository.vector_search` → `floats_to_blob` (`scripts/rag/utils.py:85-101`) → `struct.pack`. `_validate_float_list` (`utils.py:116-133`) rejects non-finite elements with `ValueError`, but a value that is finite as a Python double yet out of float32 range (e.g. `1e300`) passes it; `struct.pack('<f', 1e300)` then raises `OverflowError`, which the `except struct.error` wrapper does not catch. `vector_search` inlines the pack call inside `_execute_with_timing` (`scripts/rag/repository.py:172-174`), `SearchStage._search_all_queries` catches only `sqlite3.OperationalError` / `RuntimeError` (`scripts/rag/stages/search.py:59-68`), and `StageLifecycle._run_stage` catches `RuntimeError`, `sqlite3.OperationalError`, `httpx.HTTPStatusError`, `httpx.RequestError`, `TimeoutError` (`scripts/rag/stage_lifecycle.py:74-81`). None catches `OverflowError`. Verified live in the project venv: `math.isfinite(1e300)` is `True` and `struct.pack('<f', 1e300)` raises `OverflowError`. Current source verified against HEAD `276b265fc`; the five target/verification files have churn 0-1 commits in 30 days.

## Problem
A provider response containing a finite-but-out-of-range embedding number crashes the whole pipeline run: the `OverflowError` escapes the search stage's handler (which also skips that query's FTS search because both searches share one `try`) and the stage lifecycle's handler, so no stage-completion or degraded diagnostics are recorded and the run aborts. The issue's claims were adversarially validated in the issue's `## Adversarial Validation` section; one correction was found there: the `floats_to_blob` docstring itself misdocuments the out-of-range exception type as `struct.error`.

## Reason for Change
An external provider response can abort an availability-sensitive pipeline. The pipeline already defines a degraded contract for embedding failures (`embed_failed` counter, `SearchDiagnostics`, FTS-only continuation), so mapping this failure onto that contract is a small, convention-consistent fix rather than a new mechanism.

## Implementation Intent
Keep the fix at the two existing trust boundaries plus one defense-in-depth handler: validate the provider embedding response at `get_embedding`, make `floats_to_blob` reject out-of-range elements with a typed `ValueError` (and correct its docstring), and let `SearchStage` count any residual packing failure into its existing degraded counters. Do not change storage format, stage structure, or `stage_lifecycle.py`'s caught tuple; map the failure onto the pipeline's existing `embed_failed` degraded contract rather than introducing a new failure mechanism.

## Requirements
- `REQ-001`: `get_embedding` (`scripts/rag/llm_client.py`) rejects an embedding response containing any element that is not finite or outside the float32 range by raising `ValueError` (message names the offending index), before returning the list.
- `REQ-002`: `floats_to_blob` raises `ValueError` (not `OverflowError`) for out-of-range elements via an explicit range check in `_validate_float_list`, and its docstring states the accurate exception set (`TypeError`, `ValueError`, residual `struct.error`).
- `REQ-003`: A packing failure surfacing from `repo.vector_search` / `repo.fts_search` inside `_search_all_queries` is caught (backstop: `ValueError`, `OverflowError`, `struct.error`) and recorded in `SearchDiagnostics` counters; processing of remaining queries continues.
- `REQ-004`: The pipeline run with a single invalid-magnitude query completes with degraded diagnostics (`embed_failed >= 1`) rather than aborting; valid queries in the same run still return results.
- `REQ-005`: New tests pin `REQ-001`-`REQ-004` (unit + stage + pipeline level).

## Implementation Target Files
**Freeze status**: Draft

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/rag/llm_client.py` | Modify | `get_embedding` validates only list-ness/non-emptiness; add finite/float32-range validation of every element (`REQ-001`). A raised `ValueError` is already recorded as `embed_failed` because `_search_all_queries` gathers embeddings with `return_exceptions=True`. | `REQ-001`/`REQ-004` | `get_embedding` L266-285: no magnitude check (checked in Step 2 validation) | `tests/rag/test_llm_client_timeout.py` (module-level `get_embedding` harness) | `Verified` |
| `scripts/rag/utils.py` | Modify | `_validate_float_list` checks `math.isfinite` only; add explicit float32-range rejection raising `ValueError`; correct the `floats_to_blob` docstring's `struct.error`-for-out-of-range claim. | `REQ-002` | `utils.py:94` docstring vs live `struct.pack('<f', 1e300)` -> `OverflowError`; wrapper catches only `struct.error` (`utils.py:97-101`) | `tests/rag/test_rag_utils.py` | `Verified` |
| `scripts/rag/stages/search.py` | Modify | Backstop: widen the per-query `except (sqlite3.OperationalError, RuntimeError)` to include `ValueError`, `OverflowError`, `struct.error` so a packing failure is counted (degraded) instead of escaping; keep remaining-query processing. | `REQ-003`/`REQ-004` | `search.py:59-68` except tuple (checked in Step 2 validation) | `tests/rag/test_rag_stages.py` | `Verified` |
| `tests/rag/test_rag_utils.py` | Modify | Add out-of-range cases: `1e300`, `-1e300`, `3.5e38` raise `ValueError`; max-magnitude in-range value (`~3.4e38`) still packs. Existing cases pin empty/non-list/non-numeric/NaN/inf (lines 56-80) but no out-of-range case. | `REQ-002` | No `1e300`/`OverflowError` case exists (grep) | `tests/rag/test_rag_utils.py` | `Verified` |
| `tests/rag/test_llm_client_timeout.py` | Modify | Add `get_embedding` cases: response embedding containing `1e300` or `inf` raises `ValueError`; normal-range response returns the list. | `REQ-001` | File exercises module-level `get_embedding` (grep: `tests/rag/test_llm_client_timeout.py` references `get_embedding`) | `tests/rag/test_llm_client_timeout.py` | `Verified` |
| `tests/rag/test_rag_stages.py` | Modify | Add stage-level case: an embedding rejected by `get_embedding` increments `embed_failed` and remaining queries still execute; a simulated pack failure at `vector_search` is recorded by the backstop (`fts_errors`/degraded) and does not propagate. | `REQ-003`/`REQ-004` | Degraded counters already exercised in this file (grep: `embed_failed` patterns in `test_rag_stages.py` / `test_rag_pipeline.py`) | `tests/rag/test_rag_stages.py` | `Verified` |
| `docs/21_rag/rag_03_04_query_pipeline-search-stages.md` | Modify | Extend the `SearchStage` error-handling note (L46) with the out-of-range embedding case: rejected at `get_embedding` -> `embed_failed`; backstop counts packing failures; no propagation. | `REQ-003`/`REQ-004` | Note currently lists only `sqlite3.OperationalError` / `RuntimeError` (checked L46) | docs checkers | `Verified` |
| `docs/21_rag/rag_03_06_query_pipeline-helpers-and-cache.md` | Modify | State the `get_embedding` contract: elements must be finite and within float32 range or the response is rejected (`ValueError`). | `REQ-001` | `get_embedding` described at L62-66 with no magnitude contract | docs checkers | `Verified` |
| `docs/21_rag/rag_02_09_ingestion_pipeline-shared-utilities.md` | Modify | Update the `floats_to_blob()` contract line (L35): out-of-range elements raise `ValueError`; docstring correction propagates here. | `REQ-002` | L35 currently says "a packing failure is logged and the `struct.error` is re-raised" (checked) | docs checkers | `Verified` |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/rag/repository.py` | Confirmed no-change: `vector_search` inlines `floats_to_blob` inside `_execute_with_timing` (L172-174); the fix lives at the two boundaries plus the stage backstop, not in the repository. | `scripts/rag/utils.py` (`REQ-002`) |
| `scripts/rag/stage_lifecycle.py` | Confirmed no-change: caught tuple (L74-81) suffices once the search stage backstop exists. | `scripts/rag/stages/search.py` (`REQ-003`) |
| `scripts/rag/ingestion/embedding.py` | Shows the ValueError -> `EMBEDDING_FAILED` mapping convention (L56-68, L103) reused by `REQ-001`; also records the out-of-scope adjacent gap at L109. | `scripts/rag/llm_client.py` (`REQ-001`) |
| `scripts/rag/diagnostics.py` | `SearchDiagnostics.from_run_result()` counter semantics that the backstop must feed (`REQ-003`). | `scripts/rag/stages/search.py` |
| `scripts/agent/memory/mapper.py` | Duplicate `_floats_to_blob` with the same overflow pattern (L35); out of scope, candidate follow-up issue. | Out-of-scope note |
| `docs/21_rag/rag_05_04-error-handling-reference.md` | Exception inventory reference; check whether query-path rows exist that must list the new `ValueError` case (currently no `SearchStage`/`vector_search` rows found — if none, no edit). | `scripts/rag/utils.py` (`REQ-002`) |

## Acceptance Criteria
- `REQ-001`: `get_embedding` raises `ValueError` for a provider response embedding containing `1e300` or a non-finite element; normal embeddings pass unchanged.
- `REQ-002`: `floats_to_blob([1e300])` raises `ValueError` whose message names the offending index; `floats_to_blob([3.4e38])` (in float32 range) still packs to 4 bytes; docstring matches behavior.
- `REQ-003`: A forced packing failure inside `repo.vector_search` for one query increments the degraded counter and does not stop remaining queries (test with a stub raising `ValueError`).
- `REQ-004`: Pipeline-level test: one invalid-magnitude query in a multi-query run completes with `SearchDiagnostics` degraded (`embed_failed >= 1`) and results for the valid queries.
- `REQ-005`: New tests fail on current HEAD (with `OverflowError` / silent acceptance) and pass after the fix; full `tests/rag/` suite green.

## Tests
- Unit: `tests/rag/test_rag_utils.py` out-of-range / boundary-magnitude cases (`REQ-002`).
- Unit: `tests/rag/test_llm_client_timeout.py` `get_embedding` validation cases (`REQ-001`).
- Stage: `tests/rag/test_rag_stages.py` degraded-counter cases for rejected embedding and forced pack failure backstop (`REQ-003`, `REQ-004`).
- Regression target: the escape path `SearchStage` -> `floats_to_blob` with a stubbed embed response containing `1e300` (`REQ-004`).

## Documentation Impact
- `docs/21_rag/rag_03_04_query_pipeline-search-stages.md` — extend the search-stage error-handling note with the out-of-range embedding degraded path.
- `docs/21_rag/rag_03_06_query_pipeline-helpers-and-cache.md` — state the `get_embedding` magnitude contract.
- `docs/21_rag/rag_02_09_ingestion_pipeline-shared-utilities.md` — update the `floats_to_blob()` exception contract line.
- Check `docs/21_rag/rag_05_04-error-handling-reference.md` for a query-path exception table; no `SearchStage` rows exist today — only add a row if a matching table is introduced. State boundaries and failure behavior, not implementation detail. Run the `docs/` checkers from `routing.md` for any edited doc.

## Assumptions
- The embed provider (Qwen3 service) can in principle return finite-but-out-of-range numbers; no evidence it currently does. The fix is trust-boundary hardening, not a live-incident fix.
- `math.isfinite` plus a magnitude bound check (`abs(v) <= float32 max`, i.e. `< 3.4028235e38`, NaN/inf already covered) is the agreed validation form; the exact bound constant is decided in the implementation procedure.
- Recording a packing backstop failure under `fts_errors` (the existing search-failure counter) is acceptable; introducing a new counter is not required.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| `UNK-01` | whether the owner wants the same validation added to the ingestion pack step (`scripts/rag/ingestion/embedding.py:109`) and the `scripts/agent/memory/mapper.py` copy now or as follow-up issues | owner preference not recorded | file follow-up issues referencing this Plan, or extend scope at owner request | `False` |
| `UNK-02` | whether `adrrag001`'s cause-based failure policy (open issue `issues/20261107-050701_adrrag001_rag-fallback-failure-policy.md`) would reclassify out-of-range embeddings as a data-integrity failure requiring fail-closed rather than degraded | policy decision pending in that issue | cross-check after `adrrag001` resolves; current plan follows the existing `embed_failed` degraded convention | `False` |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/rag/llm_client.py` | Modify | in-process query embedding path (agent + MCP rag pipeline) | 1 | N/A | not applicable (rsynced) |
| `scripts/rag/utils.py` | Modify | all `floats_to_blob` callers: query (`repository.py`) and ingestion (`ingestion/embedding.py`) | 0 | N/A | not applicable (rsynced) |
| `scripts/rag/stages/search.py` | Modify | `SearchStage` per-query error accounting | 0 | N/A | not applicable (rsynced) |
| `tests/rag/test_rag_utils.py` | Modify | unit tests only | 0 | N/A | not applicable (rsynced) |
| `tests/rag/test_llm_client_timeout.py` | Modify | unit tests only | N/A | N/A | not applicable (rsynced) |
| `tests/rag/test_rag_stages.py` | Modify | stage tests only | 0 | N/A | not applicable (rsynced) |
| `docs/21_rag/rag_03_04_query_pipeline-search-stages.md` | Modify | docs only | N/A | N/A | not applicable |
| `docs/21_rag/rag_03_06_query_pipeline-helpers-and-cache.md` | Modify | docs only | N/A | N/A | not applicable |
| `docs/21_rag/rag_02_09_ingestion_pipeline-shared-utilities.md` | Modify | docs only | N/A | N/A | not applicable |

## Design
**Primary boundary — `get_embedding` (`REQ-001`).** Validate the provider response where it enters the process: after the existing list-ness check, reject any element that is not finite or whose magnitude exceeds the float32 max. Raise `ValueError` naming the index. Because `_search_all_queries` already gathers embeddings with `return_exceptions=True` and maps exceptions to `embed_failed`, this single edit converts the crash into the existing degraded contract without touching the search stage for the primary path. This mirrors the ingestion convention where a `ValueError` from response validation maps to `EMBEDDING_FAILED` (`scripts/rag/ingestion/embedding.py:56-68,103`).

**Secondary — typed pack validation (`REQ-002`).** `floats_to_blob` is the shared low-level utility; its own validation must not depend on callers. Add an explicit range check in `_validate_float_list` (same style as the existing `isfinite` check) so out-of-range raises `ValueError` with the index, and correct the docstring's inaccurate `struct.error`-for-out-of-range claim. This also hardens the ingestion pack call site (`embedding.py:109`) against `OverflowError` even though ingestion-level response validation is out of scope: the failure it surfaces is now a typed `ValueError` the ingestion layer already maps to a failure reason at its own boundary.

**Backstop — search stage (`REQ-003`).** Widen the per-query `except` in `_search_all_queries` to include `ValueError`, `OverflowError`, `struct.error`, counted into the existing search-failure counter. Defense in depth: any future pack path that bypasses both boundaries degrades instead of aborting. `stage_lifecycle.py` is verified unchanged — the escape is fully contained above it.

**Why not lifecycle-level catch:** adding `OverflowError` to `_run_stage`'s tuple would abort the stage for the single bad query instead of degrading per-query, losing results for the valid queries in the same run — strictly worse than the stage-level backstop.

## Implementation steps
1. **Phase 1: Utility contract (`REQ-002`).** Add the float32-range check to `_validate_float_list` and fix the `floats_to_blob` docstring in `scripts/rag/utils.py`; extend `tests/rag/test_rag_utils.py` with out-of-range and boundary-magnitude cases. Independent, low risk.
2. **Phase 2: Provider boundary (`REQ-001`).** Add element validation to `get_embedding` in `scripts/rag/llm_client.py`; extend `tests/rag/test_llm_client_timeout.py`. Depends on nothing from Phase 1 (independent check), but run Phase 1 first so `ValueError` semantics are already established.
3. **Phase 3: Stage backstop (`REQ-003`/`REQ-004`).** Widen the except tuple in `scripts/rag/stages/search.py`; add stage/pipeline degraded tests in `tests/rag/test_rag_stages.py`.
4. **Phase 4: Documentation.** Update the three docs rows above; run the `docs/` checkers from `routing.md`.

### Release units
**Unit**: ragvec001-full | **Phases**: 1, 2, 3, 4 | **Reason**: one atomic change set (code + tests + docs); behavior for valid embeddings is unchanged, so no phased rollout is needed.

## Validation plan
- `uv run pytest tests/rag/test_rag_utils.py tests/rag/test_llm_client_timeout.py tests/rag/test_rag_stages.py tests/rag/test_rag_pipeline.py -q` after each phase; full `uv run pytest tests/ -q` before completion.
- New tests must fail on HEAD (`OverflowError` / no rejection) and pass after each phase — regression-proof.
- Lint/type gates per `rules/toolchain.md`; `uv run python tools/check_docs_quality.py`, `tools/check_docs_structure.py <edited docs>`, `tools/check_docs_content_policy.py`, `tools/check_docs_consistency.py --domain rag` after Phase 4.
- Confirm no behavior change for valid embeddings: existing `tests/rag/` suite unchanged and green.

## Risks
| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Rejecting a legitimate provider value near the float32 boundary | Low | Medium (degraded search for a valid query) | Boundary-magnitude test pins `~3.4e38` packs successfully; real embeddings are small-magnitude |
| Backstop `ValueError` catch swallows unrelated `ValueError`s (e.g. a future repository bug) | Medium | Low (failure becomes degraded instead of visible) | Log at WARNING with the original message; counters make degradation observable in the search log |
| Ingestion path still crashes on out-of-range provider embeddings at the response layer (`embedding.py:109` still packs outside handlers, though now with typed `ValueError`) | Medium | Medium | Recorded as `UNK-01`; recommend follow-up issue |

## Execution Status
### Execution Status
| Work Item | Status | Owner | Started | Completed | Notes |
|---|---|---|---|---|---|
| Phase 1: utility contract | Planned | engineer | | | |
| Phase 2: provider boundary | Planned | engineer | | | |
| Phase 3: stage backstop | Planned | engineer | | | |
| Phase 4: documentation | Planned | engineer | | | |

### Blocker Log
| Date | Blocker | Status | Resolution |
|---|---|---|---|

### Work Items Created
| Work Item | Type | Link | Created |
|---|---|---|---|

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: `issues/20261107-203511_ragvec001_rag-embedding-float32-overflow.md`
- **Source requirement**: N/A: the issue is the requirement source
- **Source plan**: N/A: this document is the plan
- **Generated at**: 20261108-075301
- **Related target files**: see Implementation Target Files table

### Requirement Traceability
| Requirement | Source | Target File | Acceptance Criterion | Test |
|---|---|---|---|---|
| `REQ-001` | Issue Required Changes / Adversarial Validation (boundary mapping) | `scripts/rag/llm_client.py` | Provider response validation rejects out-of-range elements | `tests/rag/test_llm_client_timeout.py` |
| `REQ-002` | Issue Problem + docstring correction from validation | `scripts/rag/utils.py` | Typed `ValueError` for out-of-range; docstring accurate | `tests/rag/test_rag_utils.py` |
| `REQ-003` | Issue Problem (search-stage escape) | `scripts/rag/stages/search.py` | Packing failure counted, remaining queries continue | `tests/rag/test_rag_stages.py` |
| `REQ-004` | Issue Acceptance Criteria | `scripts/rag/stages/search.py` | Degraded diagnostics, run completes | `tests/rag/test_rag_stages.py` / `tests/rag/test_rag_pipeline.py` |
| `REQ-005` | Issue Testing Expectations | three test files | New tests fail on HEAD, pass after fix | all above |

## Notes
- Source verified against HEAD `276b265fc` (2026-11-08). The issue's `## Adversarial Validation` and `## Content Analysis` sections carry the validation evidence this plan builds on.
- Docs paths reflect the current `docs/21_rag/` layout after the 2026-11-07 documentation renumbering.
