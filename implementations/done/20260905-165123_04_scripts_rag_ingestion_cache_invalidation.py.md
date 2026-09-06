## Goal
Delete `scripts/rag/ingestion/cache_invalidation.py` (`CacheInvalidator`), whose sole
purpose is POSTing to the `/rag_invalidate_cache` HTTP endpoint this Plan removes
(`REQ-004`).

## Scope
- **In-Scope**: delete the file `scripts/rag/ingestion/cache_invalidation.py` in its
  entirety (32 lines: `CacheInvalidator` class, its `__init__` and `invalidate()`
  methods).
- **Out-of-Scope**: `scripts/rag/ingestion/ingester.py`'s construction/call of
  `CacheInvalidator` (its own procedure document, `05`, must remove that reference
  before or in the same pass as this deletion); the `/rag_invalidate_cache` endpoint
  itself in `rag_pipeline_server.py` (procedure document `07`).

## Assumptions
- `scripts/rag/ingestion/ingester.py`'s `self._cache_invalidator` construction and
  `.invalidate(...)` call are removed by procedure document `05` in the same
  implementation pass, per this Plan's Design section ("Both are removed in the same
  Plan since leaving either one would mean shipping a dead code path").

## Design decisions
(per `skills/python-design/SKILL.md` Final Output §5, narrow bullet only)
- Delete the whole file — `CacheInvalidator`'s only responsibility (per its own
  docstring: "Isolate cache management logic from ingester.py") is invalidating the
  cache this Plan removes; no residual responsibility remains once its call site is
  gone.

## Alternatives considered
- Retaining `CacheInvalidator` as a generic post-ingestion HTTP notifier (repurposing
  it for a future non-cache signal) — rejected: no such future use is requested by the
  originating issue or this Plan; introducing a speculative abstraction violates
  `skills/DESIGN.md`/`AGENTS.md` Global Rule 5 scope discipline.

## Implementation
### Target file
`scripts/rag/ingestion/cache_invalidation.py`

### Procedure
1. Confirm `scripts/rag/ingestion/ingester.py`'s `self._cache_invalidator` construction
   and `.invalidate(...)` call have been removed (procedure document `05`) — or are
   being removed in the same implementation pass — before deleting this file, so no
   intermediate commit leaves a dangling import.
2. Delete the file `scripts/rag/ingestion/cache_invalidation.py`.

### Method
File deletion — no code replaces it; ingestion no longer signals cache invalidation to
any endpoint after this change, matching this Plan's Goal (no cache exists to
invalidate).

### Details
- This file's sole external dependency is `httpx.Client` (constructor parameter) and
  `shared.logger.Logger` — neither requires cleanup elsewhere; both are used by many
  other modules and are not made unused by this deletion.
- Re-run `rg -n "CacheInvalidator" scripts/ tests/` after both this deletion and
  procedure `05`'s edit land — zero matches confirms no dangling reference remains.

## Compatibility considerations
- `CacheInvalidator` has exactly one confirmed production caller
  (`scripts/rag/ingestion/ingester.py`, procedure document `05`) — no other module
  imports this class.

## Security considerations
N/A: no security-sensitive code path is touched — this class only POSTed to a local
same-process HTTP endpoint being removed in this same Plan.

## Rollback considerations
- Revert via `git checkout` (or restoring the deleted file); no data migration or
  external state is affected. Must be reverted together with procedure document `05`'s
  change to `ingester.py` to avoid a dangling import if only this file is restored.

## Validation plan
- `rg -n "CacheInvalidator" scripts/ tests/` — zero matches after this deletion and
  procedure `05`/`16` (`tests/rag/ingestion/test_rag_ingester.py`) land.
- `uv run pytest tests/rag/ingestion/test_rag_ingester.py -v` — passes with no
  collection error from a dangling import.

## Completion criteria
- `scripts/rag/ingestion/cache_invalidation.py` no longer exists (Plan `AC-5`).
- No remaining reference to `CacheInvalidator` exists anywhere in `scripts/` or
  `tests/`.

## Out of scope
- `scripts/rag/ingestion/ingester.py`'s own edit (procedure document `05`).
- The `/rag_invalidate_cache` endpoint (procedure document `07`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | — | |
| 2 | Add or update tests per Validation plan | Completed | — | — | N/A: deletion only, no new test |
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
- **Requirement ID**: `REQ-004` (delete `CacheInvalidator` and its ingestion caller)
- **Source issue**: issues/20260902-150339_semcacherm_remove_semanticcache_implementation_and_invalidation_paths.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260904-140151_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260905-165123
- **Related target files**: scripts/rag/ingestion/cache_invalidation.py
