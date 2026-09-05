## Goal
Remove `TestSemanticCacheDimensionGuard` from `tests/rag/test_rag_pipeline_stage.py`,
since it directly imports and instantiates `SemanticCache` (`scripts/rag/cache.py`),
which procedure document `02` deletes (`REQ-006`).

## Scope
- **In-Scope**: remove lines 430-458 in their entirety — the
  `class TestSemanticCacheDimensionGuard:` class (docstring plus four test methods:
  `test_put_sets_dimension_on_first_entry`, `test_put_returns_false_on_dimension_mismatch`,
  `test_lookup_returns_none_on_dimension_mismatch`, `test_lookup_empty_cache_returns_none`),
  each of which contains its own local `from rag.cache import SemanticCache`.
- **Out-of-Scope**: `semantic_cache_max_size`/`semantic_cache_threshold`/
  `use_semantic_cache` dataclass fields and constructor arguments at lines 23-25 and
  58-60 — these back a config stand-in used by other tests in this file, unrelated to
  `TestSemanticCacheDimensionGuard`; the config fields remain defined
  (`semcacheconfig`'s scope, not this Plan's); the `TestPipelineRunStage`-family classes
  and every other test class in this 747-line file, confirmed unrelated by the targeted
  `grep` search below.

## Assumptions
- No other class in this file references `SemanticCache`/`CacheEntry`/`CacheService`
  outside lines 430-458 — confirmed by `grep -n
  "SemanticCache|CacheEntry|CacheService" tests/rag/test_rag_pipeline_stage.py`,
  whose only matches are within the deleted range.

## Design decisions
(per `skills/python-design/SKILL.md` Final Output §7, narrow bullet only)
- Delete the class as one contiguous block (lines 430-458), including the blank line
  separating it from the section-comment block that follows (`# --- RagPipeline._run_stage ---`),
  so the following, unrelated test section's leading separator comment is left with
  the same single blank-line spacing convention as the rest of the file.
- Each of the four test methods imports `SemanticCache` locally (inside the method
  body, not at module scope) — this file has no module-level `from rag.cache import
  SemanticCache` to also remove; deletion is confined to these four local imports,
  which disappear with their enclosing methods.

## Alternatives considered
- Rewriting these four tests against a generic embedding-similarity helper instead of
  deleting them — rejected: `SemanticCache`'s dimension-validation behavior (the thing
  under test) does not exist anywhere else after procedure document `02`; there is no
  replacement API for these tests to exercise, per the Plan's Goal (no cache
  replacement is introduced).

## Implementation
### Target file
`tests/rag/test_rag_pipeline_stage.py`

### Procedure
1. Delete lines 430-458 (the `class TestSemanticCacheDimensionGuard:` block, including
   its docstring and all four test methods with their local `SemanticCache` imports).
2. Confirm exactly one blank line separates the preceding test (`... last_timings`,
   ending at line 427) from the following section-comment block
   (`# --- RagPipeline._run_stage — ... ---`, starting at line 460) after deletion —
   matching this file's existing section-separator convention elsewhere.

### Method
Direct removal via `Edit`.

### Details
- Do not touch lines 23-25 (`semantic_cache_max_size`/`semantic_cache_threshold`/
  `use_semantic_cache` dataclass field defaults) or lines 58-60 (their corresponding
  constructor-argument defaults) — these remain valid against the still-defined config
  fields (see Scope, Out-of-Scope).
- Confirm after editing: `rg -n "SemanticCache|CacheEntry|CacheService"
  tests/rag/test_rag_pipeline_stage.py` returns zero matches.

## Compatibility considerations
N/A: test-only file; no production caller depends on it.

## Security considerations
N/A: no security-sensitive code path is touched.

## Rollback considerations
- Revert via `git checkout` on this single file; independent of every other procedure
  document.

## Validation plan
- `uv run pytest tests/rag/test_rag_pipeline_stage.py -v` — all remaining tests pass;
  no `TestSemanticCacheDimensionGuard` collection error.
- `rg -n "SemanticCache|CacheEntry|CacheService" tests/rag/test_rag_pipeline_stage.py`
  — zero matches.

## Completion criteria
- `TestSemanticCacheDimensionGuard` no longer exists in this file (Plan `AC-9`).
- `uv run pytest tests/rag/test_rag_pipeline_stage.py -v` passes in full.

## Out of scope
- `semantic_cache_max_size`/`semantic_cache_threshold`/`use_semantic_cache` dataclass
  fields and constructor arguments used by other tests in this file.
- `tests/rag/test_rag_pipeline.py` (procedure document `08`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: this document itself is a test-removal change |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: documentation deferred to `semcachedocs` |

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
- **Requirement ID**: `REQ-006` (remove `SemanticCache`/`CacheEntry` fixtures and assertions)
- **Source issue**: issues/20260902-150339_semcacherm_remove_semanticcache_implementation_and_invalidation_paths.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260904-140151_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260905-165123
- **Related target files**: tests/rag/test_rag_pipeline_stage.py
