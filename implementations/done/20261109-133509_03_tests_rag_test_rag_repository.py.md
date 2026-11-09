## Goal

Add tests that pin the new signal-combination behavior of `RagScorer.rrf_merge` and `_dedup_hits` (order independence, single-list absence, multi-list minimum, unchanged fused order) and adjust any assertion that assumes the old `0.0` defaults (`REQ-001`..`REQ-005`: signal combination and unchanged ranking).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: new tests in `tests/rag/test_rag_repository.py` for `TestRagScorer`, `TestDedupHits`, and `TestRagRepository`.
- Plan step 1 (tests first): write these before the types and repository procedures run.

## Assumptions

- Re-verified this cycle (after the ragrev005 test procedure landed): `TestRagScorer` (`tests/rag/test_rag_repository.py:312`), `TestDedupHits` (L401), `TestRagRepository` (L428) and the `_hit` helper (L260, builds `RawHit` without the two signal fields) exist; `test_vector_search_delegates_to_db` (L429) and `test_fts_search_delegates_to_db` (L446) build rows with only one signal (L437, L454) and assert neither signal field today. No test outside this file asserts the `0.0` defaults (`rg` over `tests/` shows only real-value comparisons, e.g. `test_fts_fallback.py:166`).
- Overlap with `implementations/20261109-121825_01_tests_rag_test_rag_repository.py.md` (ragrev005): compatible. That procedure edits `TestBuildFtsQuery`; this one edits the merge, dedup, and repository search test classes. Locate by class name, not line number.
- `tests/rag/test_fts_fallback.py:166` compares two real `bm25_score` values from FTS rows, which stay numeric; it needs no change.
- The `_hit` helper may build hits with `distance` / `bm25_score` keywords; if it hard-codes numeric defaults, extend it with optional keyword arguments instead of adding a second helper.

## Design decisions

- Parametrize both list orders in one test (`[vec, fts]` and `[fts, vec]`) so order independence is a single pinned property.
- Capture the order and `rrf_score` snapshot for a multi-list fixture as literal expected values computed by hand from `1 / (rrf_k + rank)`, not by calling the function under test.

## Alternatives considered

N/A: tests follow the existing class layout and the Plan's Tests section.

## Implementation
### Target file
`tests/rag/test_rag_repository.py`

### Procedure
1. `TestRagScorer`: add a parametrized both-order test (vector hit `distance=0.1` and FTS hit `bm25_score=-3.0` for one `chunk_id`) asserting `distance == 0.1` and `bm25_score == -3.0` (AC-1).
2. `TestRagScorer`: add single-list tests asserting a vector-only chunk has `bm25_score is None` and an FTS-only chunk has `distance is None` (AC-2).
3. `TestRagScorer`: add multi-list minimum tests: vector lists `0.3` and `0.1` merge to `0.1`; FTS lists `-1.0` and `-2.0` merge to `-2.0` (AC-3).
4. `TestRagScorer`: add an order and score snapshot test over a multi-list fixture with hand-computed expected `rrf_score` values and `chunk_id` order (AC-5).
5. `TestDedupHits`: add the dedup equivalents of the both-order, single-list, and minimum cases (AC-4).
6. `TestRagRepository`: assert in the two delegate tests that `vector_search` leaves `bm25_score is None` and `fts_search` leaves `distance is None`.

### Method
- Use `pytest.mark.parametrize` for the order cases; build hits through `RawHit(...)` keywords only.
- Compare floats with `pytest.approx`; compare absence with `is None`.

### Details
- The tests must fail on HEAD for the right reason (an assertion on `0.0` versus `None`, or on the lost signal), not by an import or construction error; run them once before the sibling procedures to confirm.
- Do not rely on numeric defaults of `RawHit`; every fixture states the signal it carries.

## Compatibility considerations

N/A: test-only change; existing tests keep their intent and only `0.0`-default assumptions, if any surface, are adjusted explicitly.

## Security considerations

N/A: test-only change.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run pytest tests/rag/test_rag_repository.py tests/rag/test_fts_fallback.py -q`: new tests fail before `..._01` and `..._02` are applied, pass after.
- `uv run ruff check tests/rag/test_rag_repository.py` and `uv run ruff format --check tests/rag/test_rag_repository.py`.
- `uv run pytest tests/rag tests/mcp_servers/rag_pipeline tests/agent/test_rag_get_cfg.py -q`.

## Completion criteria

- AC-1 to AC-5 each have at least one test.
- The new tests fail on HEAD and pass once the types and repository procedures are applied.
- No existing test was weakened; ruff is clean.

## Out of Scope

- Production code and documentation changes (separate procedures).
- Tests for `_build_fts_query` (ragrev005).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `rrf_merge` tests (both orders, single list, minimum, snapshot) | Completed | 20261109-161609 | 20261109-162847 | rrf_merge tests added: parametrized both orders, single-list absence x2, multi-list minimum x2, hand-computed order/score snapshot |
| 2 | Add `_dedup_hits` equivalents and the search-method `None` assertions | Completed | — | 20261109-162847 | _dedup_hits equivalents x5 added; both delegate tests extended with is None / real-value assertions |
| 3 | Confirm the new tests fail on HEAD, then run the validation sequence (`rules/toolchain.md`) | Completed | 20261109-162847 | 20261109-164557 | red-on-HEAD confirmed: 15 failed / 54 passed, all failures are new or extended assertions (0.0 vs None, lost signal); ruff format+check clean; targeted green and full suite deferred to unit-end run per batch attribution unit-end run: targeted tests green (77 passed in targeted run), full suite 12055 passed / 9 skipped, diff-cover 100% >= 90 |

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
- **Requirement ID**: `REQ-001`..`REQ-005` (tests for signal combination, absent marker, unchanged ranking)
- **Source issue**: issues/20261108-131010_ragrev006_rrf-merge-drops-signals.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261108-165114_ragrev006_rrf-merge-drops-signals.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261109-133509
- **Related target files**: `tests/rag/test_rag_repository.py`