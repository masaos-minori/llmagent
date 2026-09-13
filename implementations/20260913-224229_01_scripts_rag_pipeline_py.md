## Goal

Remove the dead `RagPipeline.search_queries()` and `RagPipeline.rerank_candidates()` methods (and their now-unused imports) from `scripts/rag/pipeline.py` (REQ-001).

## Scope

- Delete `RagPipeline.search_queries()` (lines 180-195) and `RagPipeline.rerank_candidates()` (lines 197-219) from `scripts/rag/pipeline.py`
- Remove the `_search_all_queries` import (line 53) and `deduplicate_chunks` import (line 47) if they become unused after deletion

## Assumptions

- No external caller outside this repository depends on `search_queries()`/`rerank_candidates()` — consistent with how `AGENTS.md`/`rules/ai-execution.md` scope dead-code determinations to this repository
- `_search_all_queries` and `deduplicate_chunks` have no other use inside `pipeline.py` beyond the methods being removed (confirmed via `grep -n`)
- `self.stat_search_embed_failed`/`self.stat_search_fts_errors` remain updated via the live `RagPipelineStageLifecycle` path (`pipeline.py:241-242`)

## Design decisions

1. Remove both methods together rather than one at a time — treated as a matched pair (both dead, documented together in the same Note)
2. Do not remove the imports until after confirming the methods are deleted — avoid removing imports prematurely if any other reference exists

## Alternatives considered

1. Removing only `search_queries()` first and deferring `rerank_candidates()` — rejected because both are confirmed dead and documented together
2. Keeping the imports even though unused — rejected because Phase 3's `ruff check` would catch them anyway, and keeping dead imports increases maintenance burden

## Implementation

### Target file

`scripts/rag/pipeline.py`

### Procedure

1. Re-confirm zero callers and import usage before deleting
2. Delete `search_queries()` and `rerank_candidates()` in their entirety
3. Remove the now-unused `_search_all_queries` and `deduplicate_chunks` imports

### Method

Phase 1: Preparation — confirm evidence line numbers
- Re-run `rg "search_queries\(|rerank_candidates\("` across `scripts/` and `tests/` to reconfirm zero call sites remain before deleting (REQ-001; `scripts/rag/pipeline.py`)
- Re-confirm `_search_all_queries`/`deduplicate_chunks` have no other use in `pipeline.py` beyond the two methods being removed (REQ-001; `scripts/rag/pipeline.py`)

Phase 2: Core Logic — delete methods and imports
- Delete `search_queries()` (lines 180-195) and `rerank_candidates()` (lines 197-219) from `pipeline.py` (REQ-001; `scripts/rag/pipeline.py`)
- Remove the now-unused `_search_all_queries`/`deduplicate_chunks` imports (REQ-001; `scripts/rag/pipeline.py`)

### Details

**Phase 1:** Verify via grep/read that:
- `rg "search_queries\(|rerank_candidates\(" scripts/ tests/` returns no call site matches (only definitions at `pipeline.py:180` and `pipeline.py:197`)
- `_search_all_queries` appears only at `pipeline.py:53` (import) and `pipeline.py:190` (usage inside `search_queries()`)
- `deduplicate_chunks` appears only at `pipeline.py:47` (import) and `pipeline.py:206`, `pipeline.py:216` (usages inside `rerank_candidates()`)

**Phase 2:** Make the following deletions:
1. Delete lines 180-195 (`async def search_queries(...)`) including its docstring
2. Delete lines 197-219 (`async def rerank_candidates(...)`) including its docstring
3. Delete line 47 (`from rag.repository import deduplicate_chunks`) — no remaining references after step 2
4. Delete line 53 (`from rag.stages.search import _search_all_queries`) — no remaining references after step 1

## Compatibility considerations

Removing two public methods that have zero callers means no behavioral change for any actual caller. However, if any downstream consumer of `RagPipeline` as a library depends on these methods, removal would be a breaking change. This risk is mitigated by the repository-wide search confirming no callers exist.

## Security considerations

No security impact — removing dead code reduces attack surface slightly by eliminating unused code paths.

## Rollback considerations

Revert the deletion commit to restore the methods and imports. The methods' logic remains unchanged since no code depends on them.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/rag/pipeline.py | Regression — full existing RAG test suite | `pytest tests/rag/` | All existing tests pass unchanged |
| scripts/rag/pipeline.py | Lint — confirm no unused imports | `ruff check scripts/rag/pipeline.py` | No unused-import findings |

## Completion criteria

- [ ] `scripts/rag/pipeline.py` no longer defines `search_queries()` or `rerank_candidates()` (REQ-001)
- [ ] `scripts/rag/pipeline.py` has no unused imports after the deletion (REQ-001)
- [ ] All existing tests pass after changes

## Out of scope

- Any change to `SearchStage.run()`/`RerankStage.run()` (the actually-used implementations)
- Any change to the `stat_search_embed_failed`/`stat_search_fts_errors` counters themselves
- Documentation corrections (separate document)

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: Confirm zero callers and import usage | Completed | 20260914-000829 | 20260914-000829 |  |
| 2 | Phase 2: Delete dead methods | Completed | 20260914-000829 | 20260914-000829 |  |
| 3 | Phase 2: Remove unused imports | Completed | 20260914-000829 | 20260914-000829 |  |
| 4 | Verification: run tests and lint | Completed | 20260914-000830 | 20260914-000830 |  |

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
- **Requirement ID**: REQ-001
- **Source issue**: issues/20260913-183006_dead_code_search_rerank_methods.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260913-203623_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260913-224229
- **Related target files**: scripts/rag/pipeline.py