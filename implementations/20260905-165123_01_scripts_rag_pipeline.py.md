## Goal
Remove `SemanticCache` as a runtime capability from `scripts/rag/pipeline.py`: delete the
import, the `self.semantic_cache` construction, both cache-lookup/cache-store branches in
`augment()` (including the cache-only embedding request), and the `invalidate_cache()`
method, so every `augment()` call executes retrieval against the currently committed RAG
database state (`REQ-001`, purpose: eliminate the in-process query-result cache with no
cross-process invalidation).

## Scope
- **In-Scope**: remove `from rag.cache import SemanticCache` (line 38); remove
  `self.semantic_cache: SemanticCache = SemanticCache(...)` construction (lines 180-183);
  remove the pre-retrieval cache-lookup branch in `augment()` (lines 443-453, including
  the `emb = await get_embedding(...)` call, which exists only to feed the cache lookup);
  remove the post-retrieval cache-store branch (lines 496-499); remove the
  `invalidate_cache()` method (lines 571-579); correct the stale module-docstring line
  (line 13) that attributes `SemanticCache` to `rag/repository.py` (it is actually
  defined in and imported from `rag/cache.py`, which this Plan's `REQ-005` deletes).
- **Out-of-Scope**: the `use_semantic_cache`/`semantic_cache_threshold`/
  `semantic_cache_max_size` config fields on `RagConfig`/`RagConfigImpl` (owned by
  issue `semcacheconfig`); `embed_url`/`build_embed_url()` and any other use of
  `self._embed_url` outside the removed cache branches (still required by non-cache
  retrieval and the Agent memory embedding path); `scripts/rag/cache.py` itself (deleted
  separately, `REQ-005`, tracked in its own procedure document).

## Assumptions
- No other call site in this file reads the `emb` local variable outside the two
  removed branches — confirmed by `awk`/`grep` scoped to `augment()`'s body: the only
  four occurrences of `emb` are the assignment, the `except` reset to `None`, the
  lookup guard, and the post-retrieval store guard.
- `self._embed_url` remains a valid instance attribute after this change; it continues
  to be read by other, non-cache code in this class (out of scope for this document).

## Design decisions
(per `skills/python-design/SKILL.md` Final Output §5/§8, narrow bullets only)
- Remove the cache-lookup embedding request entirely rather than leaving a dead
  `if self._cfg.use_semantic_cache and ...` branch guarded by a config flag this
  document does not remove — the flag remains defined (owned by `semcacheconfig`) but
  no code path in this file may read it after this change lands (Plan Design section).
- Order of removal within this file: remove the two `augment()` branches and the
  `invalidate_cache()` method before removing the `SemanticCache` import and
  `self.semantic_cache` construction, so the file has no dangling reference at any
  intermediate point of a single-file edit.

## Alternatives considered
- Leaving `invalidate_cache()` as a no-op stub instead of deleting it — rejected per
  the Plan's Design section: once the cache is gone, there is no partial state where
  the protocol method should exist without a backing cache; a no-op would silently
  mislead `RagPipelineMCPService.fmt_delete_document()` (procedure document `06`) into
  believing invalidation still occurs.

## Implementation
### Target file
`scripts/rag/pipeline.py`

### Procedure
1. Correct the module docstring's "Module layout" line attributing `SemanticCache` to
   `rag/repository.py` (line 13) — remove `SemanticCache` from that line's listing,
   since the class lived in `rag/cache.py` (deleted by `REQ-005`), not
   `rag/repository.py`.
2. Remove `from rag.cache import SemanticCache` (line 38).
3. Remove the `self.semantic_cache: SemanticCache = SemanticCache(max_size=..., threshold=...)`
   construction (lines 180-183), including its two `self._cfg.semantic_cache_*` reads.
4. In `augment()`, remove the entire pre-retrieval block (lines 443-453): the
   `# Semantic cache lookup (in-process mode only)` comment, the `emb` declaration, the
   `if self._cfg.use_semantic_cache and self._embed_url:` branch (including its
   `get_embedding()` call and `except` clause), and the `if emb is not None: cached = ...`
   lookup/early-return.
5. In `augment()`, remove the post-retrieval store block (lines 496-499): the
   `if self._cfg.use_semantic_cache and emb is not None and context_block:` branch and
   its `self.semantic_cache.put(...)` call with its warning log.
6. Remove the `invalidate_cache()` method (lines 571-579) in its entirety, including its
   docstring.

### Method
Direct removal via `Edit` — no replacement logic is introduced; `augment()`'s control
flow after removal proceeds straight from the `rag_service_url` HTTP-augment early-return
check into the `SQLiteHelper`/`db` retrieval block that line 443 currently precedes.

### Details
- After step 4's removal, `augment()`'s retrieval block must begin immediately after the
  `if rag_url := self._cfg.rag_service_url: ...` block (currently ending before the
  removed comment) — verify no blank-line/indentation artifact is left behind.
- After step 5's removal, the `context_block: str = _augment_format_chunks(...)` line
  must be immediately followed by `return context_block` with no intervening cache-store
  code.
- Confirm no remaining reference to `SemanticCache`, `semantic_cache`, or
  `invalidate_cache` exists in this file after all edits:
  `rg -n "SemanticCache|semantic_cache|invalidate_cache" scripts/rag/pipeline.py` must
  return zero matches.
- Do not touch `self._embed_url`'s definition (line 189, `build_embed_url(self._cfg.embed_url)`)
  — it is Out-of-Scope and still required by non-cache callers elsewhere in this class.

## Compatibility considerations
- `RagPipeline.invalidate_cache()` is a public method called externally by
  `RagPipelineMCPService.invalidate_cache()` (procedure document `06`,
  `scripts/mcp_servers/rag_pipeline/rag_pipeline_service.py`) — that caller must be
  removed in the same change set (this Plan's `REQ-002`) or this file's removal breaks
  it; sequencing is enforced by the Plan's Phase 1 ordering (service-layer callers
  removed before this file, per Design section "dependents before dependency").
- No public contract this file's callers still depend on is altered — `augment()`'s
  signature and return type (`str`) are unchanged.

## Security considerations
N/A: no security-sensitive code path is touched — cache removal has no authentication,
authorization, or secret-handling implication.

## Rollback considerations
- Revert via `git checkout` on this single file; no data migration, schema change, or
  external state is affected by this edit alone. Full rollback of the Plan additionally
  requires reverting the dependent-caller changes in Design's Phase 1 ordering (this
  file must be reverted together with, or after, `scripts/mcp_servers/rag_pipeline/rag_pipeline_service.py`,
  otherwise `RagPipelineMCPService.invalidate_cache()` calls a method that no longer
  exists).

## Validation plan
- `uv run pytest tests/rag/test_rag_pipeline.py tests/rag/test_rag_pipeline_stage.py -v`
  (both updated by their own procedure documents in this same pass) — all pass.
- `rg -n "SemanticCache|semantic_cache|invalidate_cache" scripts/rag/pipeline.py` — zero
  matches.
- `uv run ruff check scripts/rag/pipeline.py`, `uv run mypy scripts/`,
  `PYTHONPATH=scripts uv run lint-imports`,
  `uv run bandit scripts/rag/pipeline.py` — all pass with no new findings.

## Completion criteria
- No import of, or reference to, `SemanticCache` remains in this file (Plan `AC-1`).
- `augment()` no longer branches on `self._cfg.use_semantic_cache` (Plan `AC-2`).
- `invalidate_cache()` no longer exists on `RagPipeline`.
- `tests/rag/test_rag_pipeline.py` and `tests/rag/test_rag_pipeline_stage.py` pass
  against the modified file.

## Out of scope
- Removing `use_semantic_cache`/`semantic_cache_threshold`/`semantic_cache_max_size`
  from `RagConfig`/`RagConfigImpl` (`semcacheconfig`'s scope).
- Any change to `embed_url`/`build_embed_url()` or non-cache uses of `self._embed_url`.
- Deleting `scripts/rag/cache.py` itself (separate procedure document `02`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
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
- **Requirement ID**: `REQ-001` (remove `SemanticCache` import/construction/lookup/put/`invalidate_cache()` from `scripts/rag/pipeline.py`)
- **Source issue**: issues/20260902-150339_semcacherm_remove_semanticcache_implementation_and_invalidation_paths.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260904-140151_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260905-165123
- **Related target files**: scripts/rag/pipeline.py
