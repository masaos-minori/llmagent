## Goal
Remove four `SemanticCache`-importing unit tests
(`test_semantic_cache_generation_invalidation`, `test_diagnostics_semantic_cache_hits`,
`test_semantic_cache_hit_returns_cached_result`, `test_semantic_cache_miss_below_threshold`)
from `tests/rag/test_rag_quality_regression.py`, discovered by this Plan's adversarial
search as referencing the removed `SemanticCache` class directly (`REQ-004`).

## Scope
- **In-Scope**: remove four independent test methods in their entirety:
  `test_semantic_cache_generation_invalidation` (lines 207-223, including its local
  `from rag.cache import SemanticCache` import); `test_diagnostics_semantic_cache_hits`
  (lines 256-263, same local import); `test_semantic_cache_hit_returns_cached_result`
  (lines 441-449, same local import); `test_semantic_cache_miss_below_threshold` (lines
  451-457, same local import).
- **Out-of-Scope**: every other test method in `class TestRagQualityRegression`
  (`test_diagnostics_fusion_mode`, `test_diagnostics_fts_error_counts`,
  `test_rrf_merged_order_is_descending`, and all others) — confirmed unrelated by
  reading each of the four target methods' immediate neighbors; this file's
  `_make_rag_cfg()`/`_make_pipeline()` helpers — already handled by
  `semcacheconfig`'s procedure document `37` (removing `use_semantic_cache` from
  `_make_rag_cfg()`'s signature) — not touched again here.

## Assumptions
- `scripts/rag/cache.py` (`semcacherm`'s procedure document `02`) is deleted by the
  time this document's edit lands — each of the four target tests' local
  `from rag.cache import SemanticCache` import would otherwise raise `ImportError` at
  test-collection or test-execution time once that module no longer exists, which is
  exactly why these four tests must be removed (per this Plan's Problem statement,
  not merely updated).
- These four tests are not listed in, or covered by, the `semcacherm`/`semcacheconfig`
  Plans' own `Implementation Target Files` (confirmed by this Plan's own adversarial
  `rg -n "SemanticCache" tests/` search, which is the evidence basis for this Plan's
  `REQ-004` existing at all) — this document is this Plan's own first-class edit, not
  a re-verification of another Plan's work.

## Design decisions
(per `skills/python-design/SKILL.md` Final Output §7, narrow bullet only)
- Remove each of the four tests as a standalone method deletion — they are scattered
  across the file (lines ~207, ~256, ~441, ~451), each interleaved with unrelated,
  still-valid tests; no contiguous-block deletion is possible or desirable here,
  unlike some of `semcacherm`'s whole-class-removal documents.
- Do not replace these four tests with new cache-adjacent tests in this same
  document — per this Plan's `REQ-005`, the replacement freshness-guarantee coverage
  is `tests/rag/test_rag_pipeline_no_cache_freshness.py` (a separate file, from the
  `semcacherm` Plan), not a like-for-like replacement inside this file.

## Alternatives considered
- Rewriting these four tests against a generic embedding-similarity helper instead of
  deleting them — rejected, same reasoning as `semcacherm`'s own procedure document
  `09` (`test_rag_pipeline_stage.py`'s `TestSemanticCacheDimensionGuard`): the
  behavior under test (`SemanticCache`'s generation/threshold/hit/miss semantics) no
  longer exists anywhere in the codebase; there is no replacement API to test against.

## Implementation
### Target file
`tests/rag/test_rag_quality_regression.py`

### Procedure
1. Remove `test_semantic_cache_generation_invalidation` (lines 207-223) in its
   entirety, including its docstring and local `SemanticCache` import.
2. Remove `test_diagnostics_semantic_cache_hits` (lines 256-263) in its entirety.
3. Remove `test_semantic_cache_hit_returns_cached_result` (lines 441-449) in its
   entirety.
4. Remove `test_semantic_cache_miss_below_threshold` (lines 451-457) in its entirety.

### Method
Direct `Edit`: four independent whole-method removals within the same test class.

### Details
- Re-read the file's current method boundaries immediately before each removal (per
  Step 3a Adversarial Verification), since removing an earlier method shifts later
  line numbers within the same editing pass.
- After each removal, confirm the immediately preceding and following methods
  (`test_diagnostics_fusion_mode`/`test_diagnostics_fts_error_counts` around the first
  two removals; the RRF-merge tests around the last two) remain intact with normal
  single-blank-line spacing between methods.
- Confirm after editing: `rg -n "SemanticCache"
  tests/rag/test_rag_quality_regression.py` returns zero matches (a bare
  `semantic_cache`/`use_semantic_cache` match, if any remains from
  `semcacheconfig`'s own procedure document `37`'s substitution work, is that
  document's separate concern, not this one's).

## Compatibility considerations
N/A: test-only file; no production caller depends on it.

## Security considerations
N/A: no security-sensitive code path is touched.

## Rollback considerations
- Revert via `git checkout` on this single file; must be reverted together with
  `semcacherm`'s procedure document `02` (`scripts/rag/cache.py`'s deletion), since
  these four tests import from that module.

## Validation plan
- `uv run pytest tests/rag/test_rag_quality_regression.py -v` — all remaining tests
  pass; no collection error from a dangling `SemanticCache` import.
- `rg -n "SemanticCache" tests/rag/test_rag_quality_regression.py` — zero matches.

## Completion criteria
- None of the four target tests remains in this file (Plan `AC-1`, `AC-2`).
- `uv run pytest tests/rag/test_rag_quality_regression.py -v` passes in full.

## Out of scope
- Every other test in `class TestRagQualityRegression`.
- `_make_rag_cfg()`/`_make_pipeline()` helpers (already handled by
  `semcacheconfig`'s procedure document `37`).
- `tests/rag/test_rag_pipeline_no_cache_freshness.py` (this Plan's `REQ-005`,
  confirmed/verified — not edited by this document).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Blocked until `semcacherm`/`semcacheconfig` implementations land — see Assumptions |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: this document itself is a test-removal change |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | Depends on `semcacherm`'s implementation (deletes `scripts/rag/cache.py`) landing first | No | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-004` (remove `SemanticCache`-importing tests discovered by adversarial search)
- **Source issue**: issues/20260902-150341_semcachedocs_replace_semanticcache_tests_and_docs_with_no_cache_design.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260904-141629_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260905-192023
- **Related target files**: tests/rag/test_rag_quality_regression.py
