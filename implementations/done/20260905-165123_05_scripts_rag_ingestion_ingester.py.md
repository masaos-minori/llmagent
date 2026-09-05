## Goal
Remove `CacheInvalidator`'s import, construction, and post-ingestion invalidation call
from `scripts/rag/ingestion/ingester.py`, so ingestion no longer signals cache
invalidation to an endpoint this Plan removes (`REQ-004`).

## Scope
- **In-Scope**: remove `CacheInvalidator` from the module docstring's class listing
  (line 6); remove `from rag.ingestion.cache_invalidation import CacheInvalidator`
  (line 19); remove `self._cache_invalidator = CacheInvalidator(self._client)` (line
  123); remove the `has_success`/`.invalidate(...)` call and its preceding comment
  (lines 200-203).
- **Out-of-Scope**: `self._rag_pipeline_service_url` (line 117) and its `cfg.get(...)`
  read — not explicitly named by the originating issue's Required Changes; becomes
  unused by this change but is left in place per `AGENTS.md` Global Rule 5 scope
  discipline (see Details; flagged as a follow-up cleanup candidate, not performed
  here); `self._embedding_service`/`EmbeddingService` and every other extracted-class
  attribute in the same constructor block, confirmed unrelated by reading the
  surrounding context.

## Assumptions
- `scripts/rag/ingestion/cache_invalidation.py` (procedure document `04`) is deleted in
  the same implementation pass as this change, or immediately after — this file must
  not retain the import once that module is gone.

## Design decisions
(per `skills/python-design/SKILL.md` Final Output §5, narrow bullet only)
- Do not remove `self._rag_pipeline_service_url` in this document even though it
  becomes unused: the Plan's `Implementation Target Files` table describes this row's
  `Reason for Modification` as "Remove `CacheInvalidator` import, `self._cache_invalidator`
  construction, and its `.invalidate(...)` call" only — removing an additional,
  unlisted attribute is a scope expansion beyond what the frozen table authorizes; per
  `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan Freeze),
  only file paths listed in that table are modification targets, and unlisted
  attribute-level cleanup within an already-listed file is likewise bounded by the
  row's own stated Reason for Modification.

## Alternatives considered
- Also removing `self._rag_pipeline_service_url` as an unused-attribute cleanup in the
  same edit — rejected per Design decisions above; noted instead as a candidate for a
  future, separately-scoped cleanup issue (a `vulture --min-confidence 80` pass after
  this Plan lands would surface it).

## Implementation
### Target file
`scripts/rag/ingestion/ingester.py`

### Procedure
1. Remove `CacheInvalidator` from the module docstring's "Module layout"/class listing
   (line 6: `TransactionManager, ChunkGroupingStrategy, CacheInvalidator` → drop the
   trailing `, CacheInvalidator`).
2. Remove `from rag.ingestion.cache_invalidation import CacheInvalidator` (line 19).
3. Remove `self._cache_invalidator = CacheInvalidator(self._client)` (line 123), from
   the `# Extracted classes` constructor block.
4. Remove the `# Invalidate RAG pipeline semantic cache after ingestion (only when at
   least one URL group succeeded)` comment, the `has_success = any(r.n_success > 0 for
   r in results)` line, and the `self._cache_invalidator.invalidate(...)` call (lines
   200-203), immediately before the `return consistency_report` statement they precede.

### Method
Direct removal via `Edit` — no replacement logic; the method this call sat in returns
`consistency_report` unconditionally immediately after the (now-removed) invalidation
call, so its control flow is otherwise unaffected.

### Details
- `has_success` (line 202) exists solely to gate the removed `.invalidate(...)` call —
  confirmed by `grep -n "has_success"` showing only these two lines in the file; safe
  to remove both together.
- `self._rag_pipeline_service_url` (line 117) becomes unused by this specific method
  after this change, but is retained per Design decisions above — do not delete it in
  this document.
- Confirm after editing: `rg -n "CacheInvalidator|_cache_invalidator" scripts/rag/ingestion/ingester.py`
  returns zero matches.

## Compatibility considerations
- The method containing the removed call (`ingest_url_group`'s caller — the method
  whose tail this snippet is) retains its existing return type
  (`consistency_report`, unchanged) and external contract; no caller of this method
  needs updating.

## Security considerations
N/A: no security-sensitive code path is touched.

## Rollback considerations
- Revert via `git checkout` on this single file; no data migration or external state is
  affected. Must be reverted together with, or after, procedure document `04`
  (`cache_invalidation.py`'s deletion) to avoid a dangling import if this file's import
  line is restored alone.

## Validation plan
- `rg -n "CacheInvalidator|_cache_invalidator" scripts/rag/ingestion/ingester.py` — zero
  matches.
- `uv run pytest tests/rag/ingestion/test_rag_ingester.py -v` (updated by procedure
  document `16`) — passes.
- `uv run ruff check scripts/rag/ingestion/ingester.py`, `uv run mypy scripts/` — no new
  findings.

## Completion criteria
- No reference to `CacheInvalidator` or `self._cache_invalidator` remains in this file
  (Plan `AC-5`).
- `tests/rag/ingestion/test_rag_ingester.py` passes against the modified file.

## Out of scope
- Removing `self._rag_pipeline_service_url` (see Design decisions — flagged as a future
  cleanup candidate, not this document's scope).
- `scripts/rag/ingestion/cache_invalidation.py` itself (procedure document `04`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | — | |
| 2 | Add or update tests per Validation plan | Completed | — | — | Covered by procedure document `16` |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | — | All checks pass |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | — | N/A: documentation deferred to `semcachedocs` |

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
- **Requirement ID**: `REQ-004` (remove `CacheInvalidator` and its ingestion caller)
- **Source issue**: issues/20260902-150339_semcacherm_remove_semanticcache_implementation_and_invalidation_paths.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260904-140151_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260905-165123
- **Related target files**: scripts/rag/ingestion/ingester.py
