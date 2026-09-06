## Goal
Remove `TestInvalidateCache` (the `RagPipeline.invalidate_cache()` test section) from
`tests/rag/test_rag_pipeline.py`, since the API it exercises no longer exists once
procedure document `01` lands (`REQ-006`).

## Scope
- **In-Scope**: remove lines 329-398 in their entirety — the
  `# ── RagPipeline.invalidate_cache() (rag/cache.py) ──` comment header and the
  `class TestInvalidateCache:` class (its `_make_pipeline()` helper and all four test
  methods: `test_invalidate_cache_clears_entries`, `test_invalidate_cache_bumps_generation`,
  `test_invalidate_cache_returns_none`, `test_invalidate_cache_noop_when_already_empty`).
  This is the file's final section (confirmed: file is exactly 398 lines).
- **Out-of-Scope**: `use_semantic_cache=False`/`semantic_cache_max_size`/
  `semantic_cache_threshold` keyword arguments appearing in other test fixtures earlier
  in this file (lines 178, 184-185, 258, 264-265) — these construct a `SimpleNamespace`
  config stand-in for *other* tests unrelated to caching; the config fields themselves
  remain defined (`semcacheconfig`'s scope, not removed by this Plan), so these lines
  are not "obsolete" in the sense `REQ-006`/`AC-9` define (they do not reference
  `SemanticCache`, `CacheEntry`, `invalidate_cache`, or any other removed symbol — only
  a config value that still exists as a constructor argument).

## Assumptions
- No other test class in this file references `SemanticCache`, `semantic_cache`
  (the attribute, as opposed to the `use_semantic_cache`/`semantic_cache_*` config
  keys), or `invalidate_cache` outside lines 329-398 — confirmed by `grep -n
  "invalidate_cache|semantic_cache" tests/rag/test_rag_pipeline.py`, whose only matches
  outside 329-398 are the config-keyword-argument lines classified Out-of-Scope above.

## Design decisions
(per `skills/python-design/SKILL.md` Final Output §7, narrow bullet only)
- Delete the section as one contiguous block (lines 329-398) rather than
  method-by-method, since the entire `TestInvalidateCache` class exists solely to test
  the removed API — no method in it survives independently.
- Do not touch the `use_semantic_cache=False`/`semantic_cache_max_size`/
  `semantic_cache_threshold` keyword arguments in other tests' `SimpleNamespace`
  fixtures — they remain valid constructor arguments against the still-defined config
  fields; removing them is unrelated cleanup outside this Plan's `REQ-006` scope (see
  Scope, Out-of-Scope).

## Alternatives considered
- Marking the four tests `@pytest.mark.skip` instead of deleting them — rejected: the
  class under test (`RagPipeline.invalidate_cache()`) is being permanently removed
  (procedure `01`), not temporarily disabled; a skipped test for a nonexistent method
  is dead test code, contradicting `REQ-006`'s "remove" instruction and the
  originating issue's explicit deletion scope.

## Implementation
### Target file
`tests/rag/test_rag_pipeline.py`

### Procedure
1. Delete lines 329-398 (the `# ── RagPipeline.invalidate_cache() ──` comment and the
   `TestInvalidateCache` class in full) — this removes the file's final section
   entirely, so no trailing content follows after deletion.
2. Confirm the file ends cleanly (no trailing blank-line artifact beyond normal
   end-of-file convention) after line 328's preceding content.

### Method
Direct removal via `Edit`.

### Details
- Since lines 329-398 constitute the file's exact tail, this deletion can be performed
  as a single truncation to line 328 — verify line 328 is a blank line following the
  prior test's closing statement (`assert isinstance(encoded, bytes)`, line 326) before
  truncating, so no unrelated content is lost.
- Confirm after editing: `rg -n "invalidate_cache|SemanticCache|CacheEntry|CacheService"
  tests/rag/test_rag_pipeline.py` returns zero matches; `rg -n "\.semantic_cache\b"
  tests/rag/test_rag_pipeline.py` (the attribute, not the config key) also returns zero
  matches.
- Do not remove `use_semantic_cache=False` etc. from any `SimpleNamespace` fixture
  outside the deleted range (see Scope, Out-of-Scope) — these remain valid until
  `semcacheconfig` removes the underlying config fields.

## Compatibility considerations
N/A: test-only file; no production caller depends on it.

## Security considerations
N/A: no security-sensitive code path is touched.

## Rollback considerations
- Revert via `git checkout` on this single file; independent of every other procedure
  document — reverting this file alone does not break any other file, since test files
  have no downstream importers within this Plan's scope.

## Validation plan
- `uv run pytest tests/rag/test_rag_pipeline.py -v` — all remaining tests pass; no
  `TestInvalidateCache` collection error.
- `rg -n "invalidate_cache|SemanticCache|CacheEntry|CacheService"
  tests/rag/test_rag_pipeline.py` — zero matches.

## Completion criteria
- `TestInvalidateCache` no longer exists in this file (Plan `AC-9`).
- `uv run pytest tests/rag/test_rag_pipeline.py -v` passes in full.

## Out of scope
- `use_semantic_cache=False`/`semantic_cache_max_size`/`semantic_cache_threshold`
  keyword arguments in other tests' fixtures (still valid; `semcacheconfig`'s scope).
- `tests/rag/test_rag_pipeline_stage.py` (procedure document `09`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 2026-09-05T16:51:23+09:00 | 2026-09-05T16:51:23+09:00 | TestInvalidateCache class removed |
| 2 | Add or update tests per Validation plan | Completed | 2026-09-05T16:51:23+09:00 | 2026-09-05T16:51:23+09:00 | N/A: this document itself is a test-removal change |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-09-05T16:51:23+09:00 | 2026-09-05T16:51:23+09:00 | rg zero TestInvalidateCache matches; pytest 551 passed |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 2026-09-05T16:51:23+09:00 | 2026-09-05T16:51:23+09:00 | N/A: documentation deferred to `semcachedocs` |

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
- **Requirement ID**: `REQ-006` (remove the `invalidate_cache()` test section and `pipeline.semantic_cache.*` assertions)
- **Source issue**: issues/20260902-150339_semcacherm_remove_semanticcache_implementation_and_invalidation_paths.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260904-140151_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260905-165123
- **Related target files**: tests/rag/test_rag_pipeline.py
