## Goal
Remove `invalidate_cache()` from the `RagPipelineLike` protocol and
`RagPipelineMCPService`, and remove the invalidation call and its log message from
`fmt_delete_document()`, in `scripts/mcp_servers/rag_pipeline/rag_pipeline_service.py`
(`REQ-002`).

## Scope
- **In-Scope**: remove `RagPipelineLike.invalidate_cache()`'s abstract method
  declaration (lines 50-52); remove `RagPipelineMCPService.invalidate_cache()`'s
  concrete implementation (lines 131-134); remove the
  `self._pipeline_or_raise().invalidate_cache()` call and the
  `logger.info("Semantic cache invalidated after deleting %r", url)` line in
  `fmt_delete_document()` (lines 246-247).
- **Out-of-Scope**: `fmt_delete_document()`'s remaining logic (URL validation,
  `self._doc_mgr.delete_document(url)` call, return-message formatting) — unrelated to
  cache invalidation and confirmed unaffected by reading the full method body;
  `RagPipelineLike.augment()`, `last_fetch_result`, `last_timings` and every other
  Protocol member — confirmed unrelated to caching.

## Assumptions
- `scripts/rag/pipeline.py`'s `RagPipeline.invalidate_cache()` (procedure document
  `01`) is removed in the same implementation pass, or this file's protocol/service
  method removal proceeds independently first — either order is safe here since this
  file only *declares and calls* the method, it does not implement `RagPipeline`
  itself; `RagPipelineLike` is a structural `Protocol` used to avoid a circular import
  (module docstring), not an ABC requiring simultaneous edits.

## Design decisions
(per `skills/python-design/SKILL.md` Final Output §6, narrow bullet only)
- Remove the protocol method, its implementation, and its sole call site together in
  one document — per the Plan's Design section, "there is no partial state where the
  protocol method exists without a backing cache"; leaving any one of the three would
  produce either a `Protocol` requiring a method no implementer provides, or a
  service method with nothing to delegate to.
- `fmt_delete_document()`'s document-deletion behavior (`self._doc_mgr.delete_document(url)`)
  and its `ok`/return-message logic are unaffected — only the cache-invalidation
  side-effect after a successful delete is removed; the method still returns
  `f"Deleted: {url}"` / `f"Not found: {url}"` unchanged.

## Alternatives considered
- Making `invalidate_cache()` a no-op on `RagPipelineMCPService` instead of removing it
  — rejected: a no-op stub would silently mislead a caller into believing invalidation
  still occurs, and the Plan's Constraints/Design explicitly reject leaving a dead API
  surface.

## Implementation
### Target file
`scripts/mcp_servers/rag_pipeline/rag_pipeline_service.py`

### Procedure
1. Remove `RagPipelineLike.invalidate_cache()`'s declaration (lines 50-52: the method
   signature and its docstring/`...` body) from the `Protocol` class.
2. Remove `RagPipelineMCPService.invalidate_cache()`'s implementation (lines 131-134:
   the method, its docstring, the `pipeline = self._pipeline_or_raise()` line, and the
   `pipeline.invalidate_cache()` call).
3. In `fmt_delete_document()` (line ~236), remove the `if ok: self._pipeline_or_raise().invalidate_cache()`
   branch's invalidation call and its `logger.info(...)` line (lines 246-247), leaving
   the surrounding `if ok:` structure only if another statement remains under it —
   confirm whether the `if ok:` block becomes empty after removal (see Details).

### Method
Direct removal via `Edit`. In step 3, since `if ok: self._pipeline_or_raise().invalidate_cache(); logger.info(...)`
is (per the read source) the entire body of the `if ok:` block, removing both lines
leaves an empty `if ok:` block — restructure by removing the now-empty `if ok:` guard
entirely, since the method's final `return f"Deleted: {url}" if ok else f"Not found: {url}"`
already re-evaluates `ok` independently and does not depend on the removed block having
executed.

### Details
- Read the method's full body once more immediately before editing (per Step 3a
  Adversarial Verification) to confirm the `if ok:` block truly contains only the two
  lines being removed and nothing else was added since this Plan's Step 3 evidence was
  gathered.
- After removal, `fmt_delete_document()`'s body should read: validate `url` → call
  `self._doc_mgr.delete_document(url)` → return the formatted message — with no
  intervening `if ok:` block.
- Confirm after editing: `rg -n "invalidate_cache" scripts/mcp_servers/rag_pipeline/rag_pipeline_service.py`
  returns zero matches.

## Compatibility considerations
- `RagPipelineLike` is described in its own docstring as "avoids circular imports" — a
  structural `Protocol`, not a nominal ABC; removing a method from it only affects
  callers that invoke `invalidate_cache()` on a `RagPipelineLike`-typed value (none
  remain after this document's step 3 and procedure document `01`'s removal both land).
- `RagPipelineMCPService.invalidate_cache()` is itself called externally by
  `scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py`'s `/rag_invalidate_cache`
  handler (procedure document `07`) — that caller must be removed in the same change
  set or it will call a method that no longer exists; Plan Design's "dependents before
  dependency" ordering places this document before `01` (`RagPipeline` itself) but does
  not by itself sequence against `07` — verify document `07`'s removal lands in the
  same pass (see Rollback considerations).

## Security considerations
N/A: no security-sensitive code path is touched.

## Rollback considerations
- Revert via `git checkout` on this single file. Must be reverted together with
  procedure document `07` (`rag_pipeline_server.py`'s `/rag_invalidate_cache` handler) —
  reverting this file alone while `07` remains applied would leave an HTTP handler
  calling a method (`invalidate_cache()`) that no longer exists on this class.

## Validation plan
- `rg -n "invalidate_cache" scripts/mcp_servers/rag_pipeline/rag_pipeline_service.py` —
  zero matches.
- `uv run pytest tests/mcp_servers/rag_pipeline/test_rag_pipeline_mcp_service.py -v`
  (updated by procedure document `14`) — passes; `fmt_delete_document()`'s remaining
  delete-only behavior is asserted.
- `uv run mypy scripts/` — confirms `RagPipelineLike`'s reduced Protocol surface has no
  unresolved caller.

## Completion criteria
- `RagPipelineLike` and `RagPipelineMCPService` no longer expose `invalidate_cache()`
  (Plan `AC-3`).
- `fmt_delete_document()` no longer invokes cache invalidation or logs a
  cache-invalidation message on successful delete (Plan `AC-4`).
- `tests/mcp_servers/rag_pipeline/test_rag_pipeline_mcp_service.py` passes.

## Out of scope
- `RagPipeline.invalidate_cache()` itself (procedure document `01`).
- The `/rag_invalidate_cache` HTTP endpoint (procedure document `07`).
- `fmt_delete_document()`'s document-deletion logic beyond the removed cache call.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 2026-09-05T16:51:23+09:00 | 2026-09-05T16:51:23+09:00 | Protocol declaration, MCPService method, and fmt_delete_document guard removed |
| 2 | Add or update tests per Validation plan | Completed | 2026-09-05T16:51:23+09:00 | 2026-09-05T16:51:23+09:00 | Covered by procedure document `14` |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-09-05T16:51:23+09:00 | 2026-09-05T16:51:23+09:00 | ruff format/check PASSED; mypy FAILED (pre-existing error at test_rag_pipeline_mcp_service.py:200); architecture-check PASSED; constraint-verification PASSED; bandit PASSED; pytest PASSED |
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
- **Requirement ID**: `REQ-002` (remove `invalidate_cache()` from the protocol/service and its caller in `fmt_delete_document()`)
- **Source issue**: issues/20260902-150339_semcacherm_remove_semanticcache_implementation_and_invalidation_paths.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260904-140151_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260905-165123
- **Related target files**: scripts/mcp_servers/rag_pipeline/rag_pipeline_service.py
