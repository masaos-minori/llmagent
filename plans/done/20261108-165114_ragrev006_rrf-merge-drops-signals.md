## Goal
- Make merged hits keep both retrieval signals (vector `distance` and BM25 `bm25_score`) regardless of list order, with an explicit absent marker (`None`) instead of the numeric default `0.0`, without changing the RRF score formula or ranking order.

## Priority
Medium

## Scope
- **In-Scope**:
  - `RagScorer.rrf_merge` and `_dedup_hits` combine per-chunk signals across all lists (vector lists from several MQE queries and FTS lists): best `distance` is the minimum, best `bm25_score` is the minimum (more negative is better); a signal absent from every list stays `None`.
  - `RawHit`, `MergedHit`, `RankedHit` `distance` and `bm25_score` become `float | None` with default `None`; `vector_search` / `fts_search` set only the signal they produce.
  - Order-independence and single-list tests; documentation of the hit types.
- **Out-of-Scope**:
  - The RRF formula, `rrf_k`, ranking order, fusion strategy, and rerank behavior.
  - `rag_min_score` (it filters `rerank_score`, not these fields).
- **Dependencies**: N/A: none.

## Background
Review finding F-008. `rrf_merge` writes `meta[cid] = item` for every list entry (`scripts/rag/repository.py:231-254`), so the merged hit carries the last list's signal and the other signal keeps the dataclass default `0.0` (`scripts/shared/types.py:125-160`); `0.0` is a valid perfect-match distance, so an absent value is indistinguishable from a real one. `_dedup_hits` (`repository.py:336-355`, the `use_rrf=False` path in `stages/fusion.py`) keeps only the first occurrence and has the same loss. Consumers of the two fields (checked in Step 3): `_apply_rerank_scores` copies them into `RankedHit` (`scripts/rag/llm_prompts.py:213-214`), `rag_pipeline_models.py:201-202` already types them `float | None`, `_hit_to_dict` serializes hits; no code under `scripts/` reads them for a decision (the Issue's open question is resolved for source: copy and serialize only). Tests rarely depend on the numeric defaults (`tests/rag/test_rag_repository.py:437,454`, `tests/rag/test_fts_fallback.py:166` orders FTS hits by `bm25_score`).

## Problem
Merged hits misreport retrieval signals depending on list order, so diagnostics and score-based tuning are unreliable.

## Reason for Change
The merged hit is the record that diagnostics, rerank input, and the MCP response rely on; silently losing a signal is an incorrect result even though the fused rank is unaffected.

## Implementation Intent
Make absence explicit at the source (`vector_search` leaves `bm25_score` unset, `fts_search` leaves `distance` unset) and merge by "best available signal per chunk" so the result no longer depends on iteration order. Keep every constructor call valid by using keyword defaults only.

## Requirements
- `REQ-001`: Merging the same `chunk_id` from a vector list and an FTS list keeps both signals in either list order.
- `REQ-002`: A signal absent from every list is `None`, not `0.0`; a chunk present in one list keeps that list's signal and `None` for the other.
- `REQ-003`: Across several lists of one kind (MQE queries), the merged `distance` is the minimum and the merged `bm25_score` is the minimum.
- `REQ-004`: `_dedup_hits` applies the same signal combination.
- `REQ-005`: The fused `rrf_score` values and the output order are unchanged for the same inputs.
- `REQ-006`: `distance` / `bm25_score` on `RawHit`, `MergedHit`, `RankedHit` are `float | None` defaulting to `None`; existing keyword constructor calls and `RankedHit` creation in rerank keep working; consumers handle `None`.
- `REQ-007`: The shared-types documentation states the absent-marker semantics.

## Implementation Target Files
**Freeze status**: Frozen

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/shared/types.py` | Modify | `distance` / `bm25_score` become `float \| None = None` on the three hit dataclasses | `REQ-006` / AC-6 | Fields default `0.0` at L132-133, L144-145, L157-158 (checked in Step 3) | `tests/rag/test_rag_repository.py` | Verified |
| `scripts/rag/repository.py` | Modify | Signal-combining `rrf_merge` and `_dedup_hits`; `vector_search` / `fts_search` set only their own signal | `REQ-001`..`REQ-005` / AC-1..AC-5 | `meta[cid] = item` at L243; first-occurrence-only at L342-354; `distance=float(...)`/`bm25_score=float(...)` at L181, L212 (checked in Step 3) | `tests/rag/test_rag_repository.py`, `tests/rag/test_fts_fallback.py` | Verified |
| `tests/rag/test_rag_repository.py` | Modify | Order-independence, single-list, multi-query-min, dedup-only, and unchanged-order tests; adjust assertions that assume `0.0` defaults | `REQ-001`..`REQ-005` / AC-1..AC-5 | Existing repository tests at L437, L454 (checked in Step 3) | self | Verified |
| `docs/40_shared/shared_02_01_types_and_protocols-core-types.md` | Modify | State `distance` / `bm25_score` absent-marker semantics in section 5 | `REQ-007` / AC-7 | L54-58 describe the hit types without field semantics (checked in Step 3) | docs gates | Verified |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/rag/llm_prompts.py` | `_apply_rerank_scores` (L213-214) copies the two fields; works unchanged with `None` | `REQ-006` |
| `scripts/mcp_servers/rag_pipeline/rag_pipeline_models.py` | Response TypedDict already `float \| None` (L201-202) | `REQ-006` |
| `scripts/mcp_servers/rag_pipeline/rag_pipeline_service.py` | `_hit_to_dict` / `_hits_to_dicts` serialization of hits | `REQ-006` |
| `scripts/rag/stages/fusion.py` | Calls `rrf_merge` and `_dedup_hits` | `REQ-004` |
| `scripts/rag/pipeline_refiner.py` | Imports hit types for annotations only | `REQ-006` |
| `docs/21_rag/rag_04_dto-models-types.md` | Describes DTOs; verify no field-default claim exists (none found by grep for `distance`/`bm25` in Step 3) | `REQ-007` |

## Acceptance Criteria
- AC-1 (`REQ-001`): fixture `[[vector hit d=0.1], [fts hit b=-3.0]]` and the reversed order both give `distance == 0.1` and `bm25_score == -3.0`.
- AC-2 (`REQ-002`): a vector-only chunk has `bm25_score is None`; an FTS-only chunk has `distance is None`.
- AC-3 (`REQ-003`): two vector lists with `d=0.3` and `d=0.1` for one chunk merge to `0.1`; two FTS lists `-1.0`, `-2.0` merge to `-2.0`.
- AC-4 (`REQ-004`): `_dedup_hits` returns the same combined signals.
- AC-5 (`REQ-005`): rrf scores and order match a pre-change snapshot for a multi-list fixture.
- AC-6 (`REQ-006`): `mypy` clean; existing rerank, MCP service, and repository tests pass with only the intended `0.0`-assumption adjustments.
- AC-7 (`REQ-007`): the shared-types doc names the `None` semantics; docs checkers pass.

## Tests
- `REQ-001`/`REQ-002`: both-order, one-list-only parametrized `rrf_merge` tests.
- `REQ-003`: multi-list minimum tests.
- `REQ-004`: `_dedup_hits` equivalents.
- `REQ-005`: order/score snapshot test.
- `REQ-006`: `uv run mypy`; `tests/rag`, `tests/mcp_servers/rag_pipeline`, `tests/agent/test_rag_get_cfg.py` regression.

## Documentation Impact
Yes (`REQ-007`): `docs/40_shared/shared_02_01_types_and_protocols-core-types.md` section 5 (located via `scan_change_consumers` and `docs/00_index.md`). Run `check_docs_quality`, `check_docs_structure`, `check_docs_content_policy`, `check_docs_consistency --domain shared`, `check_docs_japanese`.

## Assumptions
- Minimum-of-lists is the right combination (smaller L2 distance and more negative BM25 are better); chosen because order must not matter and the best evidence is the most informative. Recorded as a design decision, not an Issue statement.
- Overlap judgment (Step 8b, `tools/check_plan_target_overlaps.py`): `scripts/rag/repository.py` and `tests/rag/test_rag_repository.py` are also targets of `plans/20261108-164946_ragrev005_fts-query-and-semantics.md`; compatible, because that plan edits `_build_fts_query` and the `TestBuildFtsQuery` class while this plan edits `rrf_merge`, `_dedup_hits`, the hit construction in `vector_search` / `fts_search`, and the merge tests (disjoint functions and test classes, no ordering requirement).
- Serialization of hits tolerates `None` (the MCP TypedDict already allows it); implementation confirms by running the MCP service tests.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether an external consumer (agent prompts, JSON clients of the MCP response) treats a missing numeric field as zero | Consumer inventory outside the repo | Report in the implementation PR; the MCP schema already permits `null` | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/shared/types.py` | Modify | Medium (shared types imported by rag, agent tests, MCP service) | 3 | N/A | not applicable (rsynced) |
| `scripts/rag/repository.py` | Modify | Medium (all retrieval and fusion) | 1 | N/A | not applicable (rsynced) |
| `tests/rag/test_rag_repository.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `docs/40_shared/shared_02_01_types_and_protocols-core-types.md` | Modify | Low | N/A | N/A | not applicable (rsynced) |

## Design
Path B (shared public type change, more than 3 files). Architecture: `shared.types` is imported by `rag`, the MCP service, and tests; `lint-imports` 6 contracts kept at plan time and no import is added. Dependency graph (consumer scan for `MergedHit`, checked in Step 3): production code touching the changed fields is `repository.py` and `llm_prompts.py` (copy only); 44 test-file candidates construct hits by keyword; `docs/40_shared/...core-types.md` is the one doc candidate. Complexity: `rrf_merge` A (4), `_dedup_hits` A (4), `fts_search` B (6); the combining logic goes into one small shared private helper used by both functions to keep each at A.

Alternatives: (a) a separate "has_distance" flag rejected (more state, same ambiguity risk); (b) a NaN marker rejected (breaks equality and sorting, serializes badly). Chosen: `None`, matching the existing MCP TypedDict.

Not affected: `scripts/rag/llm_prompts.py` (copies values unchanged), `scripts/mcp_servers/rag_pipeline/rag_pipeline_models.py` (already Optional), `scripts/rag/pipeline_refiner.py` (annotation import only).

Persisted schema check: not applicable (in-memory dataclasses; no DDL).

Validation baseline: `vulture`/`bandit` pre-existing findings recorded in `plans/20261108-164302_ragrev001_mqe-malformed-response-abort.md` (source unchanged); `diff-cover`: none at plan time, 90 percent at implementation.

## Implementation steps
1. **Phase 1: Tests first**
   - [ ] Add both-order, single-list, multi-list-minimum, dedup, and order-snapshot tests (`REQ-001`..`REQ-005`; `tests/rag/test_rag_repository.py`)
2. **Phase 2: Type change and merge**
   - [ ] `float | None = None` on the three hit types (`REQ-006`; `scripts/shared/types.py`)
   - [ ] Signal-combining helper, `rrf_merge`, `_dedup_hits`, and the two search functions (`REQ-001`..`REQ-006`; `scripts/rag/repository.py`)
3. **Phase 3: Documentation**
   - [ ] State the `None` semantics (`REQ-007`; `docs/40_shared/shared_02_01_types_and_protocols-core-types.md`)
4. **Phase 4: Deployment & Verification**
   - [ ] `uv run pytest tests/rag tests/mcp_servers/rag_pipeline tests/agent -q`, `uv run mypy`, lint, docs gates; deploy hand-off to `skills/deploy/SKILL.md` after commit and push, at the user's decision (all requirements; `scripts/rag/repository.py`)

### Release units
**Unit**: ragrev006-core | **Phases**: 2 | **Reason**: the type change and the merge/search changes ship together; the new `None` defaults are only meaningful once `vector_search` / `fts_search` stop filling the other signal.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/rag/repository.py` | Unit | `uv run pytest tests/rag/test_rag_repository.py tests/rag/test_fts_fallback.py -q` | new tests fail on HEAD, pass after |
| consumers | Regression | `uv run pytest tests/rag tests/mcp_servers/rag_pipeline tests/agent/test_rag_get_cfg.py -q` | green |
| shared types | Static | `uv run mypy`, `uv run ruff check`, `PYTHONPATH=scripts uv run lint-imports` | clean |
| docs | Docs gates | `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py`, `check_docs_consistency.py --domain shared`, `check_docs_japanese.py` | no findings |

## Risks
- **Risk**: a consumer outside the repo reads `distance` as a number → **Mitigation**: the MCP response TypedDict already allows `null`; UNK-01 reported at implementation.
- **Risk**: test fixtures that rely on `0.0` defaults break → **Mitigation**: only two repository test sites mention the fields; adjust them explicitly and run the broader suites.
- **Risk**: changing `RankedHit` defaults affects rerank sorting → **Mitigation**: sorting uses `rerank_score`; AC-5 pins order for the fusion path and rerank tests run in Phase 4.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: tests first | Completed | — | 20261109-164655 |  |
| 2 | Phase 2: type change and merge | Completed | — | 20261109-164655 |  |
| 3 | Phase 3: documentation | Completed | — | 20261109-164905 |  |
| 4 | Phase 4: deployment and verification | Pending | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261109-133509_01_scripts_shared_types.py.md | 2 | Procedure | Completed | — | — |
| implementations/20261109-133509_02_scripts_rag_repository.py.md | 2 | Procedure | Completed | — | — |
| implementations/20261109-133509_03_tests_rag_test_rag_repository.py.md | 1 | Procedure | Completed | — | — |
| implementations/20261109-133509_04_docs_40_shared_shared_02_01_types_and_protocols-core-types.md.md | 3 | Procedure | Completed | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261108-131010_ragrev006_rrf-merge-drops-signals.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261108-165114
- **Related target files**: `scripts/shared/types.py`, `scripts/rag/repository.py`, `tests/rag/test_rag_repository.py`, `docs/40_shared/shared_02_01_types_and_protocols-core-types.md`

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Acceptance Criteria 1; `repository.py:243` | `scripts/rag/repository.py` | Phase 2 | AC-1 | both-order test | Confirmed by repository evidence |
| REQ-001 | Testing Expectations | `tests/rag/test_rag_repository.py` | Phase 1 | AC-1 | both-order test | Explicit in issue |
| REQ-002 | Required Changes 2 | `scripts/rag/repository.py` | Phase 2 | AC-2 | single-list tests | Explicit in issue |
| REQ-002 | Testing Expectations | `tests/rag/test_rag_repository.py` | Phase 1 | AC-2 | single-list tests | Explicit in issue |
| REQ-003 | Design decision (best signal) | `scripts/rag/repository.py` | Phase 2 | AC-3 | multi-list minimum test | Derived from confirmed evidence |
| REQ-003 | Design decision (best signal) | `tests/rag/test_rag_repository.py` | Phase 1 | AC-3 | multi-list minimum test | Derived from confirmed evidence |
| REQ-004 | Target Files (`_dedup_hits`); `repository.py:342-354` | `scripts/rag/repository.py` | Phase 2 | AC-4 | dedup tests | Confirmed by repository evidence |
| REQ-004 | Target Files (`_dedup_hits`) | `tests/rag/test_rag_repository.py` | Phase 1 | AC-4 | dedup tests | Confirmed by repository evidence |
| REQ-005 | Constraints; Acceptance Criteria 2 | `scripts/rag/repository.py` | Phase 2 | AC-5 | order snapshot test | Explicit in issue |
| REQ-005 | Constraints; Acceptance Criteria 2 | `tests/rag/test_rag_repository.py` | Phase 1 | AC-5 | order snapshot test | Explicit in issue |
| REQ-006 | Required Changes 2; Constraints | `scripts/shared/types.py` | Phase 2 | AC-6 | mypy and regression suites | Explicit in issue |
| REQ-006 | Required Changes 2 | `scripts/rag/repository.py` | Phase 2 | AC-6 | mypy and regression suites | Explicit in issue |
| REQ-007 | Documentation Impact (corrected: shared types doc applies) | `docs/40_shared/shared_02_01_types_and_protocols-core-types.md` | Phase 3 | AC-7 | docs gates | Derived from confirmed evidence |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261109-133509 -->
