## Goal
Create `tests/rag/test_rag_pipeline_no_cache_freshness.py`: a new regression test
proving that committed document additions, updates, and deletions are reflected in
`RagPipeline` retrieval results without calling any cache-invalidation method or
restarting the pipeline/service (`REQ-007`) — since procedure documents `01`-`07`
remove the only mechanism (`SemanticCache`) that could otherwise mask a stale result.

## Scope
- **In-Scope**: create one new test file containing a test class that (a) runs a
  query against a `RagPipeline` instance, "commits" a new document (by changing what
  the search layer returns for the identical query), re-runs the identical query, and
  asserts the new content is reflected; (b) repeats the same pattern for an updated
  document's content changing; (c) repeats it again for a document's removal (the
  search layer no longer returns it); all three without calling
  `invalidate_cache()` (removed by procedure `01`, so it is not even callable) and
  without constructing a second `RagPipeline`/service instance mid-test (no restart).
- **Out-of-Scope**: exercising the real SQLite-backed `SearchStage`/`RagRepository`
  path end-to-end (out of proportion for a fast regression test; the existing
  `tests/rag/test_rag_quality_regression.py` pattern of patching
  `rag.stages.search._search_all_queries` is the established, lower-cost precedent
  this file follows instead — see Design decisions); testing `SemanticCache` itself
  (deleted, procedure `02`) or any removed API.

## Assumptions
- Procedure documents `01` through `07` (removing `SemanticCache`,
  `invalidate_cache()`, and the HTTP endpoint) have landed before this test is written
  and run — this test's premise ("no cache exists to go stale") is only true once
  those documents are applied; if run against pre-change code, this test would still
  need to pass (per the Plan's Testing Expectations: "Confirm each new/modified
  regression test fails against the pre-change code and passes after the
  implementation change" — see Details for how this test achieves that property even
  though a cache technically still exists pre-change, since `augment()`'s cache-lookup
  path only activates when `use_semantic_cache=True`; setting it `False` in this test's
  fixture makes both pre- and post-change code paths behave identically for the
  purpose of *this* test, so the meaningful "fails before, passes after" property
  instead comes from confirming this test would catch a *regression* — i.e. it must
  fail if a future change reintroduces stale caching, not that it fails on today's
  literal pre-change commit).

## Design decisions
(per `skills/python-design/SKILL.md` Final Output §7/§10, narrow bullets only)
- Follow `tests/rag/test_rag_quality_regression.py`'s established pattern: build a
  `RagPipeline` via `_make_pipeline(cfg)` (a `SimpleNamespace` config, `MagicMock`
  HTTP client, `RagPipeline.__new__`-free real construction since no real embed server
  is needed for this test's assertions), and patch
  `rag.stages.search._search_all_queries` to control exactly what `RawHit`s a given
  query returns — this is the codebase's own precedent for deterministic,
  fast RAG pipeline tests without a real SQLite fixture or embed server.
- Structure as three independent test methods (add/update/delete), each patching
  `_search_all_queries` with an `AsyncMock` whose `side_effect` is a list of two
  different return values — first call simulates "before commit", second call
  simulates "after commit" — then asserts `pipeline.run(query, db=mock_db)`'s
  `.reranked` (or `.merged`, whichever this Plan's evidence confirms is the field
  `_augment_format_chunks` reads — see Details) differs between the two calls in the
  way the scenario requires (new content present / updated content present / removed
  content absent).
- Use `use_semantic_cache=False` in this test's fixture config (matching most of this
  Plan's other test fixtures, e.g. procedure documents `17`/`18`) rather than `True` —
  this test's purpose is to prove retrieval reflects DB state on every call, which is
  best demonstrated by a config value that, pre-this-Plan, would have disabled the
  cache anyway; the meaningful assertion is behavioral (same-query, different results
  across calls), not dependent on the cache flag's value.

## Alternatives considered
- Building a real in-memory SQLite RAG schema (`create_rag_schema()`) and inserting/
  updating/deleting actual rows between two `pipeline.run()` calls — rejected as the
  primary approach: no existing `tests/rag/*.py` file does this for `RagPipeline`
  (confirmed by `grep -rl "create_rag_schema" tests/rag/`, zero matches); it would add
  a slower, more complex fixture than the codebase's own established pattern
  (`test_rag_quality_regression.py`'s `_search_all_queries` patch) for equivalent
  assertion strength — the goal (retrieval reflects a changed underlying state, with
  no cache masking it) is fully verifiable at the `_search_all_queries` boundary
  without requiring a real DB round-trip.

## Implementation
### Target file
`tests/rag/test_rag_pipeline_no_cache_freshness.py` (new file)

### Procedure
1. Create the file with a module docstring stating its purpose (regression coverage
   for `REQ-007`: no-cache freshness after add/update/delete).
2. Reuse (import or closely mirror) `test_rag_quality_regression.py`'s `_make_rag_cfg`/
   `_make_http`/`_make_pipeline` helper shapes — either by importing them if that
   module exposes them as public helpers, or by defining equivalent local helpers if
   importing from a sibling test module is not this codebase's convention (confirm
   convention by checking whether any existing `tests/rag/*.py` file imports helpers
   from another `tests/rag/test_*.py` file before choosing).
3. Write `test_addition_visible_without_invalidation`: patch
   `rag.stages.search._search_all_queries` with an `AsyncMock` whose `side_effect` is
   `[([], diag_a), ([new_doc_hit], diag_b)]` (empty result, then one result containing
   the "newly added" document's content); call `pipeline.run(query, db=mock_db)` twice
   with the identical query string; assert the first call's `.reranked` (or the
   correct field, per Details) does not contain the new content and the second call's
   does — with no call to `invalidate_cache` anywhere in the test (it does not exist
   post-`01`) and no second `RagPipeline` construction.
4. Write `test_update_visible_without_invalidation`: same pattern, but `side_effect` is
   `[([old_content_hit], diag), ([updated_content_hit], diag)]` — same `chunk_id`/`url`,
   different `content`; assert the second call's result reflects the updated content,
   not the old one.
5. Write `test_deletion_visible_without_invalidation`: same pattern, but `side_effect`
   is `[([existing_hit], diag), ([], diag)]` — assert the first call's result contains
   the document's content and the second call's does not.
6. In all three tests, explicitly assert `hasattr(pipeline, "invalidate_cache") is
   False` (or equivalent) as a guard confirming the removed API is truly gone — this
   is the test's own confirmation that "without cache invalidation" is enforced by
   absence of the method, not merely by not calling it.

### Method
New test file, written directly (not generated by
`tools/generate_workitem.py --kind implementation-procedure`'s scaffolding, which
applies to this procedure document itself, not the test file it describes) — follows
`pytest`-style plain test functions or a class, matching
`test_rag_quality_regression.py`'s `class TestRagQualityRegression:` convention for
consistency within `tests/rag/`.

### Details
- Confirm which field `_augment_format_chunks()` (imported in `pipeline.py` from
  `rag.augment`) actually formats — read `rag/augment.py`'s `_format_chunks()` 
  signature and the type of `pipeline_result.reranked` before asserting on its content,
  rather than assuming; use `pipeline.run(query, db=mock_db)` (returns the full
  `PipelineRunResult`, exposing `.reranked` directly, per
  `test_rag_quality_regression.py`'s own usage) in preference to `augment()` (returns
  only the formatted `str`) if inspecting structured hit content is easier than
  string-matching the formatted block — either approach is acceptable as long as the
  assertion concretely distinguishes "old" vs. "new" content across the two calls.
- Each test must use a fresh `RawHit`/`MergedHit` fixture with distinct, greppable
  content strings (e.g. `"ORIGINAL_CONTENT_MARKER"` vs. `"UPDATED_CONTENT_MARKER"`) so
  assertions are unambiguous rather than relying on subtle differences.
- Do not import anything from `scripts/rag/cache.py` (deleted, procedure `02`) or
  reference `SemanticCache`/`CacheEntry`/`invalidate_cache` anywhere in this new file.

## Compatibility considerations
N/A: new test file; no existing caller is affected by its creation.

## Security considerations
N/A: no security-sensitive code path is touched.

## Rollback considerations
- Revert by deleting this newly-created file; no other file depends on it existing.

## Validation plan
- `uv run pytest tests/rag/test_rag_pipeline_no_cache_freshness.py -v` — all three new
  tests pass against the fully-implemented Plan (procedure documents `01`-`19` landed).
- Confirm each test would fail if a cache were reintroduced (manually verify by
  temporarily reverting procedure document `01`'s change in a scratch branch, or by
  code review confirming the assertion genuinely depends on live `_search_all_queries`
  results rather than a cached value) — per the Plan's Testing Expectations
  instruction to confirm new regression tests are meaningful, not tautological.

## Completion criteria
- `tests/rag/test_rag_pipeline_no_cache_freshness.py` exists and contains at least
  three passing tests covering addition, update, and deletion visibility (Plan `AC-8`).
- Every local RAG query in this test suite is confirmed to execute the retrieval
  pipeline on each call, including repeated identical queries (Plan `AC-7`).

## Out of scope
- Any change to `scripts/rag/` production code (this document creates a test file
  only).
- Testing Workflow/EventBus recovery or any non-RAG domain.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | This document's Implementation IS the new test |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A |

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
- **Requirement ID**: `REQ-007` (add regression coverage proving committed add/update/delete visibility without cache invalidation or restart)
- **Source issue**: issues/20260902-150339_semcacherm_remove_semanticcache_implementation_and_invalidation_paths.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260904-140151_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260905-165123
- **Related target files**: tests/rag/test_rag_pipeline_no_cache_freshness.py
