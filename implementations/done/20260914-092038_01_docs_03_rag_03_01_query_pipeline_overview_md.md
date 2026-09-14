## Goal

Replace the bulleted 4-step `augment()` fallback chain description in `docs/03_rag_03_01_query_pipeline-overview.md` with a table documenting each step's possible return values, its fallback trigger, what the final result looks like, and which diagnostics field records that step's outcome (REQ-001, REQ-002).

## Scope

- Convert the existing 4-step bulleted list (`augment() Fallback Chain` section) into a table with columns for return values, fallback trigger, final-result description, and the diagnostics field/mechanism tracking each step's outcome

## Assumptions

- `augment()`'s fallback sequence and diagnostics recording (confirmed via direct reading this cycle) remain the current, authoritative implementation
- Step 4 (Raw Chunks) genuinely has no dedicated `StageResult` entry of its own — confirmed by the absence of a distinct `stage_name` for it in `pipeline.py`'s `run()`/`augment()` (only `Refiner`'s `StageResult` and the earlier stages' results exist; raw-chunk formatting itself is not instrumented as a stage)

## Design decisions

1. Keep the "Identity vs Truthiness" note as prose after the table rather than folding it into a table cell — it explains a cross-cutting rule (applies to both Step 1 and Step 3), not a single step's specific behavior, so prose remains the clearer format for it
2. State "not directly tracked" for Step 4's diagnostics rather than implying a field exists — accurately representing an instrumentation gap is more useful to a debugging developer than implying complete diagnostics coverage

## Alternatives considered

1. Folding the "Identity vs Truthiness" explanation into a table cell — rejected because it explains a cross-cutting rule (applies to both Step 1 and Step 3), not a single step's specific behavior, so prose remains the clearer format for it
2. Implying a diagnostics field exists for Step 4 — rejected because Step 4 has no dedicated `StageResult` entry of its own; accurately representing an instrumentation gap is more useful to a debugging developer than implying complete diagnostics coverage

## Implementation

### Target file

`docs/03_rag_03_01_query_pipeline-overview.md`

### Procedure

1. Re-confirm each step's diagnostics recording
2. Replace the bulleted list with a table

### Method

Phase 1: Preparation — re-confirm evidence line numbers
- Re-read `pipeline.py:89,91,171,237-240,296-297` to confirm the diagnostics mapping for each step is unchanged (REQ-001, REQ-002; `docs/03_rag_03_01_query_pipeline-overview.md`)

Phase 2: Core Logic — replace the bulleted list with a table
- Replace lines 55-58 with the 4-row table (REQ-001, REQ-002; `docs/03_rag_03_01_query_pipeline-overview.md`)

### Details

**Phase 1:** Verify via read/grep that:
- Section at `docs/03_rag_03_01_query_pipeline-overview.md:55-58` states the 4-step fallback chain:
  1. HTTP Mode: HTTP augment → `str` (including empty string) or `None` (fallback)
  2. Search Pipeline: MQE + KNN/BM25 + RRF merge + Rerank → `ctx.reranked`
  3. Refiner: `refine_context()` → compressed text (final) or `None` (fallback)
  4. Raw Chunks: Formatted by chunk formatting function (final)
- Diagnostics mapping confirmed at `pipeline.py`:
  - Line 89: `stat_search_embed_failed: int = 0` — cumulative search failure counter
  - Line 91: `stat_search_fts_errors: int = 0` — cumulative FTS error counter
  - Lines 237-240: `self.last_stage_results` updated with per-stage status during `augment()`
  - Lines 296-297: `return refined_text` from Refiner (final result)
- AugmentRefiner.run_refiner()'s StageResult recording confirmed at `augment.py:159-166` (appended to `self.last_stage_results`)

**Phase 2:** Replace the existing bulleted list at lines 55-58 with the following table:

```markdown
| Step | Produces | Fallback Trigger | Final Result | Diagnostics |
|---|---|---|---|---|
| 1. HTTP Mode | `str` (including empty string) or `None` | Returns `None` | HTTP response body or empty string | `last_stage_results` (via `_augment_refiner.last_stage_results`, `pipeline.py:297`), `last_search_diagnostics` (`SearchDiagnostics`, `pipeline.py:296`) |
| 2. Search Pipeline | `ctx.reranked` (list of ranked chunks) | Not a fallback/final step — produces input for subsequent steps | N/A (intermediate) | `last_search_diagnostics` (`SearchDiagnostics`, populated via `RagPipelineStageLifecycle`, `pipeline.py:237-240`) |
| 3. Refiner | Compressed text (`str`) or `None` | Returns `None` | Compressed/refined context text | `last_stage_results` (`StageResult(stage_name="Refiner")`, appended at `augment.py:159-166`; `status="success"` or `"fallback"`) |
| 4. Raw Chunks | Formatted text (`str`) | Reached only if Step 1 or Step 3 returned `None` | Chunk-formatted context text | Not directly tracked — inferable from absence of a "success"/"fallback" `StageResult` for Refiner combined with `use_refiner=False`, or from `Refiner`'s `StageResult` showing `status="fallback"` |
```

## Compatibility considerations

This is a documentation-only restructuring change. No backward compatibility concerns. However, accurately documenting the fallback chain's diagnostics mapping helps developers diagnose which step produced a given result without needing to trace through code.

## Security considerations

No security impact — documentation addition only. However, accurate documentation of the fallback chain's diagnostics mechanism is important for understanding how the pipeline tracks its execution path.

## Rollback considerations

Simple revert: restore the original bulleted list. The underlying code remains unchanged.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| docs/03_rag_03_01_query_pipeline-overview.md | Manual — cross-check table cells against `pipeline.py` | Manual inspection | Every cell traceable to a specific code location |

## Completion criteria

- [ ] The Fallback Chain section presents a table with all 4 steps, each row showing produced value, fallback trigger, and final-result shape (REQ-001)
- [ ] Each row states which diagnostics field/mechanism (`last_stage_results`, `last_search_diagnostics`, or "not directly tracked" for Step 4) records that step's outcome (REQ-002)
- [ ] The existing "Identity vs Truthiness" and "On DB Connection Failure" notes remain unchanged and positioned after the table

## Out of scope

- Changing `augment()`'s implementation
- Adding new diagnostics fields (this Plan documents the existing `last_stage_results`/`last_search_diagnostics` mechanism, it does not extend it)
- Restructuring the existing "Identity vs Truthiness" note (already accurate, per Background — kept as-is, referenced rather than duplicated)

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: Re-confirm each step's diagnostics recording | Completed | 20260914-114419 | 20260914-114419 |  |
| 2 | Phase 2: Replace bulleted list with table | Completed | 20260914-114153 | 20260914-114153 |  |
| 3 | Verification: manual review | Completed | 20260914-114419 | 20260914-114419 |  |

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
- **Source issue**: issues/20260913-183020_missing_pipeline_overview_fallback_chain_detail.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260913-210928_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260914-092038
- **Related target files**: docs/03_rag_03_01_query_pipeline-overview.md