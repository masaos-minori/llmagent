## Goal

Correct `docs/03_rag_03_02_query_pipeline-rag-pipeline-class.md`'s two duplicate "Implementation Note" mentions of `invalidate_cache()` (a method that no longer exists) and remove the matching stale semantic-cache references left in `scripts/rag/pipeline.py`'s own docstrings/comments — all traced to the same semantic cache removal (`282b08f38`) a sibling issue already corrected in a different document this same cycle (REQ-001, REQ-002).

## Scope

- Correct both duplicate mentions of `invalidate_cache()` in `docs/03_rag_03_02_query_pipeline-rag-pipeline-class.md` (lines 46, 84) to state the method was removed
- Remove the stale "Semantic cache" step from `RagPipeline.augment()`'s docstring (`pipeline.py:267,284`) and the orphaned "In-memory nearest-neighbour cache" comment (`pipeline.py:95`)

## Assumptions

- No other file references `invalidate_cache()` or documents a semantic-cache fallback step beyond the locations confirmed this cycle (`docs/03_rag_03_02_...` lines 46/84, and `pipeline.py` lines 95/267/284) — confirmed via repository-wide `rg` search, not merely assumed
- Removing the docstring's "Semantic cache" step and renumbering the remaining steps does not require renumbering anything outside the docstring itself (no other code or documentation references "step 3"/"step 4" by number from this specific docstring)

## Design decisions

1. Fix both duplicate mentions in the docs file identically — since this cycle's sibling investigation (`183002`'s Plan, this same document family) already established that this file's duplicate sections are a known, separately-tracked structural issue, this Plan corrects the content in both surviving copies rather than waiting for that structural fix to land first
2. Include the `pipeline.py` docstring correction in this same Plan rather than filing a separate issue for it — it is the same underlying fact (semantic cache removed) surfacing in a second location discovered during this cycle's investigation, not an independent concern requiring its own Issue→Plan cycle

## Alternatives considered

1. Correcting only one of the duplicate mentions in the docs file — rejected because both copies contain the same stale text and should be corrected consistently
2. Filing a separate issue for the `pipeline.py` docstring correction — rejected because it is the same underlying fact (semantic cache removed) surfacing in a second location discovered during this cycle's investigation, not an independent concern requiring its own Issue→Plan cycle
3. Re-implementing cache invalidation or any caching mechanism — rejected because deliberately removed per `282b08f38`, confirmed by a dedicated test asserting its absence
4. Correcting this file's duplicate-section structure (`## 2.`/`## 2a.`/`## 2b.`) — rejected because a separate, broader defect this Plan does not address, consistent with how a sibling Plan this cycle (`plans/20260913-202903_plan.md`) scoped an analogous fix to a different file only
5. Correcting `docs/03_rag_01_system_overview.md`'s own stale Semantic Cache section — rejected because already addressed by a separate sibling Plan (`plans/20260913-205143_plan.md`) this cycle

## Implementation

### Target files

- `docs/03_rag_03_02_query_pipeline-rag-pipeline-class.md`
- `scripts/rag/pipeline.py`

### Procedure

1. Re-confirm invalidate_cache()'s absence and the docstring's actual step count
2. Correct both files
3. Run regression tests

### Method

Phase 1: Preparation — re-confirm evidence line numbers
- Re-run `rg "invalidate_cache" scripts/ tests/` to reconfirm only the confirming test references it (REQ-001; both target files)
- Re-read `pipeline.py:247-341` (`augment()`) to reconfirm its actual 4-step fallback chain has no semantic-cache step (REQ-002; `scripts/rag/pipeline.py`)

Phase 2: Core Logic — correct both files
- Replace both `invalidate_cache()` mentions in `docs/03_rag_03_02_query_pipeline-rag-pipeline-class.md` (lines 46, 84) with a removal note (REQ-001; `docs/03_rag_03_02_query_pipeline-rag-pipeline-class.md`)
- Remove the "Semantic cache" docstring line and renumber remaining steps in `pipeline.py`'s `augment()` (line 267) (REQ-002; `scripts/rag/pipeline.py`)
- Remove the semantic-cache side-effect line (line 284) (REQ-002; `scripts/rag/pipeline.py`)
- Remove the orphaned comment (line 95) (REQ-002; `scripts/rag/pipeline.py`)

Phase 3: Deployment & Verification
- Run `pytest tests/rag/test_rag_pipeline_no_cache_freshness.py` to verify no regression (REQ-002)

### Details

**Phase 1:** Verify via read/grep that:
- Section at `docs/03_rag_03_02_query_pipeline-rag-pipeline-class.md:46` states:
  ```markdown
  - `invalidate_cache()` is intended to be called only after corpus changes that this pipeline instance is aware of; the caller (e.g., MCP service layer) is responsible for detecting corpus changes and explicitly calling it. The pipeline itself does not have a mechanism to detect DB changes and automatically invalidate the cache ("Call after any corpus-changing operation this pipeline instance is aware of").
  ```
- `invalidate_cache()` does not exist anywhere in the current codebase. A repository-wide search (`rg "invalidate_cache" scripts/ tests/`) found it only in `tests/rag/test_rag_pipeline_no_cache_freshness.py`, which **asserts its absence** three times (`assert hasattr(pipeline, "invalidate_cache") is False`, lines 92, 113, 137) — its removal is deliberately verified, not an oversight
- This traces to the same semantic cache removal already confirmed during a sibling issue's investigation this cycle (`282b08f38 req-005: remove SemanticCache from RAG pipeline and MCP server`, `09093016d feat(rag): remove semantic cache configuration fields and references`)
- `augment()`'s actual fallback chain confirmed 4-step (no cache step) during sibling issue `183020`'s investigation this cycle
- Orphaned comment confirmed at `pipeline.py:90`: "# In-memory nearest-neighbour cache; threshold/max_size read from cfg"
- Stale side-effect line confirmed at `pipeline.py:238`: "- May update semantic cache on successful augment"

**Phase 2:** Make the following changes:

1. **Replace line 46** in `docs/03_rag_03_02_query_pipeline-rag-pipeline-class.md` with:
   ```markdown
   - **Removed.** The `invalidate_cache()` method was deliberately removed as part of the semantic cache feature removal (`282b08f38`, `09093016d`). Its absence is verified by `tests/rag/test_rag_pipeline_no_cache_freshness.py` (three assertions: `assert hasattr(pipeline, "invalidate_cache") is False`). No cache invalidation mechanism exists in the current implementation.
   ```

2. **Replace line 84** in `docs/03_rag_03_02_query_pipeline-rag-pipeline-class.md` with the same replacement as Step 1 above (both duplicates must be corrected identically)

3. **Remove the "Semantic cache" docstring line** from `augment()`'s docstring in `pipeline.py` (line 267) and renumber the remaining fallback steps sequentially

4. **Remove the semantic-cache side-effect line** (line 284) from the Side effects list in `augment()`'s docstring

5. **Remove the orphaned comment** (line 90) in `pipeline.py`

## Compatibility considerations

This is a documentation-only change (docstring/comment removal in `pipeline.py`, documentation correction in the markdown file). No backward compatibility concerns. However, accurately documenting the removal of `invalidate_cache()` helps readers understand why they cannot call a method that was intentionally deleted, and prevents them from looking for a method that no longer exists.

## Security considerations

No security impact — documentation correction only. However, accurate documentation of the removal of the semantic cache and its associated methods is important for understanding the pipeline's current defense posture against injection attacks.

## Rollback considerations

Simple revert: restore the original `invalidate_cache()` mentions in the docs file and the original docstring/comment content in `pipeline.py`. The underlying code remains unchanged.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| docs/03_rag_03_02_query_pipeline-rag-pipeline-class.md | Manual — review corrected mentions | Manual inspection | Both mentions state the method was removed |
| scripts/rag/pipeline.py | Regression — confirm docstring/comment-only change doesn't affect behavior | `pytest tests/rag/test_rag_pipeline_no_cache_freshness.py` | All existing assertions pass unchanged |

## Completion criteria

- [ ] Both `docs/03_rag_03_02_query_pipeline-rag-pipeline-class.md` mentions of `invalidate_cache()` state the method was removed, citing the removal commits (REQ-001)
- [ ] `scripts/rag/pipeline.py`'s `augment()` docstring no longer lists a "Semantic cache" fallback step; remaining steps are renumbered sequentially (REQ-002)
- [ ] `scripts/rag/pipeline.py`'s `augment()` docstring no longer states it "may update semantic cache" (REQ-002)
- [ ] `scripts/rag/pipeline.py`'s orphaned "In-memory nearest-neighbour cache" comment (line 95) is removed (REQ-002)
- [ ] `tests/rag/test_rag_pipeline_no_cache_freshness.py` continues to pass unmodified (docstring/comment-only change does not affect test behavior)

## Out of scope

- Correcting this file's duplicate-section structure (`## 2.`/`## 2a.`/`## 2b.` — a separate, broader defect this Plan does not address, consistent with how a sibling Plan this cycle (`plans/20260913-202903_plan.md`) scoped an analogous fix to a different file only)
- Re-implementing cache invalidation or any caching mechanism (deliberately removed per `282b08f38`, confirmed by a dedicated test asserting its absence)
- Correcting `docs/03_rag_01_system_overview.md`'s own stale Semantic Cache section — already addressed by a separate sibling Plan (`plans/20260913-205143_plan.md`) this cycle

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: Re-confirm invalidate_cache()'s absence and the docstring's actual step count | Pending | — | — | |
| 2 | Phase 2: Correct both files | Pending | — | — | |
| 3 | Phase 3: Run regression tests | Pending | — | — | |

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
- **Requirement ID**: REQ-001, REQ-002
- **Source issue**: issues/20260913-183026_missing_pipeline_class_cache_invalidation_scope.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260913-212101_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260914-100329
- **Related target files**: docs/03_rag_03_02_query_pipeline-rag-pipeline-class.md, scripts/rag/pipeline.py
