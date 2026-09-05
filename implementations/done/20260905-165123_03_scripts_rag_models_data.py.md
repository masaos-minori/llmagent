## Goal
Remove the `CacheEntry` dataclass (lines 89-96) from `scripts/rag/models_data.py`, since
it exists only to back `SemanticCache`'s internal entry list, which this Plan removes
(`REQ-005`).

## Scope
- **In-Scope**: remove the `@dataclass(frozen=True) class CacheEntry` definition (lines
  89-96: `embedding: list[float]`, `context_str: str`, `history_context: str = ""`,
  `generation: int = 0`) from `scripts/rag/models_data.py`.
- **Out-of-Scope**: `TwoStageFetchResult` and any other dataclass in this file
  immediately following `CacheEntry` — confirmed unrelated by reading the surrounding
  context; `scripts/shared/tool_cache.py`'s own, unrelated `CacheEntry` class (a
  same-named but distinct dataclass backing `ToolResultCache`, a standalone LRU+TTL
  utility not integrated with `RagPipeline` — see Details).

## Assumptions
- `scripts/rag/cache.py` (this class's sole importer, `from rag.models_data import
  CacheEntry`) has already been deleted by procedure document `02` before this
  document's removal step executes, per the Plan's Design section deletion ordering.

## Design decisions
(per `skills/python-design/SKILL.md` Final Output §5, narrow bullet only)
- Remove only the `CacheEntry` class body; do not touch `TwoStageFetchResult` or any
  other dataclass in the same file, since this Plan's evidence (`rg -n "class
  CacheEntry" -A 15`) confirmed `CacheEntry`'s sole use was `scripts/rag/cache.py`'s
  `_entries: list[CacheEntry]` — no other class in this file is implicated.

## Alternatives considered
- Leaving `CacheEntry` in place as an unused dataclass — rejected: it has no remaining
  caller once `scripts/rag/cache.py` is deleted (procedure `02`), and `vulture`-class
  dead-code review would flag it; the originating issue's scope explicitly includes
  removing it alongside `scripts/rag/cache.py`.

## Implementation
### Target file
`scripts/rag/models_data.py`

### Procedure
1. Confirm (re-run) `rg -n "CacheEntry" scripts/ tests/` shows no remaining reference
   to `scripts/rag/models_data.py`'s `CacheEntry` other than its own definition —
   distinguish this from `scripts/shared/tool_cache.py`'s unrelated, same-named class
   before concluding "zero remaining callers" (see Details).
2. Remove the `@dataclass(frozen=True)` `CacheEntry` class definition (lines 89-96),
   including its docstring and the blank lines immediately surrounding it that
   separate it from the preceding and following dataclasses.

### Method
Direct removal via `Edit` — no replacement is introduced.

### Details
- **Name-collision caution**: `scripts/shared/tool_cache.py` defines its own,
  unrelated `CacheEntry` class (backing `ToolResultCache`, a standalone LRU+TTL cache
  utility per `docs/90_shared_04_shared`'s Design Intent — not integrated into
  `ToolExecutor` or `RagPipeline`). A repository-wide `rg -n "CacheEntry"` returns both
  classes; this document's scope is `scripts/rag/models_data.py`'s definition only — do
  not modify `scripts/shared/tool_cache.py`, which is unrelated to this Plan.
  - Read the matched file's content before treating a search hit as evidence for this
    row, per `rules/ai-execution.md` Repository Tool Usage #8 (a name match alone is
    not sufficient).
- After removal, verify the file's remaining dataclasses (`TwoStageFetchResult` and any
  others) are syntactically intact — no dangling blank-line or decorator artifact from
  the deletion.

## Compatibility considerations
- No public contract outside `scripts/rag/cache.py` (deleted, procedure `02`) depends on
  `rag.models_data.CacheEntry` — confirmed by this document's Step 1 search.

## Security considerations
N/A: no security-sensitive code path is touched.

## Rollback considerations
- Revert via `git checkout` on this single file; no data migration or external state is
  affected. This document's revert is independent of procedure `02`'s revert order,
  since `CacheEntry`'s removal does not itself break any file other than the already-
  deleted `scripts/rag/cache.py`.

## Validation plan
- `rg -n "CacheEntry" scripts/rag/ tests/rag/` — zero matches after this change and
  procedure `02`/`10` (`tests/rag/test_rag_cache.py` deletion) land.
- `uv run mypy scripts/rag/` — no new type errors from the removed dataclass.

## Completion criteria
- `CacheEntry` no longer exists in `scripts/rag/models_data.py` (Plan `AC-6`).
- `scripts/shared/tool_cache.py`'s own `CacheEntry` remains untouched.

## Out of scope
- `scripts/shared/tool_cache.py`'s `CacheEntry` class (unrelated, different module).
- `TwoStageFetchResult` or any other dataclass in `scripts/rag/models_data.py`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 2026-09-05T16:51:23+09:00 | 2026-09-05T16:51:23+09:00 | CacheEntry dataclass removed |
| 2 | Add or update tests per Validation plan | Completed | 2026-09-05T16:51:23+09:00 | 2026-09-05T16:51:23+09:00 | N/A: no direct test targets this dataclass |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-09-05T16:51:23+09:00 | 2026-09-05T16:51:23+09:00 | rg zero CacheEntry matches; pytest 551 passed |
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
- **Requirement ID**: `REQ-005` (delete `CacheEntry` in `scripts/rag/models_data.py` once zero remaining callers are confirmed)
- **Source issue**: issues/20260902-150339_semcacherm_remove_semanticcache_implementation_and_invalidation_paths.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260904-140151_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260905-165123
- **Related target files**: scripts/rag/models_data.py
