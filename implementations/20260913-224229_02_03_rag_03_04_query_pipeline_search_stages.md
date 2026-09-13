## Goal

Correct `docs/03_rag_03_04_query_pipeline-search-stages.md` to remove the stale claim that `rerank_candidates()` passes the RRF flag to `FusionStage` and update section 5.2's Note to reflect the methods' removal (REQ-002).

## Scope

- Update section 5.2's Note (line 59) to state the methods have been removed (rather than "are dead code")
- Remove section 5.3's false claim that `rerank_candidates()` passes an RRF flag to `FusionStage` (line 75)

## Assumptions

- The methods `search_queries()` and `rerank_candidates()` are being removed from `pipeline.py` (per REQ-001, separate document), so describing them as "dead code" is no longer accurate
- Section 5.3's false claim about `rerank_candidates()` passing an RRF flag to `FusionStage` contradicts the same document's own dead-code note four paragraphs earlier — an internal inconsistency that must be corrected

## Design decisions

1. Correct section 5.3's false claim as part of this Plan rather than filing a separate issue — it is a direct consequence of the same dead-code fact addressed here
2. Update section 5.2's Note to reflect removal (not just "dead code") — once the methods are removed, they no longer exist as dead code

## Alternatives considered

1. Leaving section 5.3's false claim in place — rejected because it directly contradicts the same document's own dead-code note and misleads future readers
2. Filing a separate issue for section 5.3's correction — rejected because it is a direct consequence of the same dead-code fact already addressed

## Implementation

### Target file

`docs/03_rag_03_04_query_pipeline-search-stages.md`

### Procedure

1. Update section 5.2's Note (line 59) to reflect the methods' removal
2. Remove section 5.3's false claim about `rerank_candidates()` passing an RRF flag to `FusionStage` (line 75)

### Method

Phase 1: Preparation — confirm current text
- Read the current Note text at line 59 and the false claim at line 75 to determine exact replacement text (REQ-002; `docs/03_rag_03_04_query_pipeline-search-stages.md`)

Phase 2: Core Logic — correct documentation claims
- Update section 5.2's Note to state the methods have been removed (REQ-002; `docs/03_rag_03_04_query_pipeline-search-stages.md`)
- Remove section 5.3's false `rerank_candidates()`/`FusionStage` claim (REQ-002; `docs/03_rag_03_04_query_pipeline-search-stages.md`)

### Details

**Phase 1:** Read current text:
- Line 59: `> **Note (2026-07-13):** While RagPipeline.search_queries() and RagPipeline.rerank_candidates() are defined in pipeline.py, neither has any callers (dead code). Actual search and reranking logic is executed in SearchStage.run() and RerankStage.run().`
- Line 75: `Using use_rrf=False triggers a fallback to deduplication only (all scores set to 0.0). RagPipeline.rerank_candidates() passes the RRF configuration flag to FusionStage.`

**Phase 2:** Make the following edits:
1. Replace line 59's Note with text stating the methods have been removed (e.g., `> **Note:** RagPipeline.search_queries() and RagPipeline.rerank_candidates() were removed as dead code. Actual search and reranking logic is executed in SearchStage.run() and RerankStage.run().`)
2. Remove the sentence `RagPipeline.rerank_candidates() passes the RRF configuration flag to FusionStage.` from line 75 — leave the preceding sentence about `use_rrf=False` triggering deduplication-only fallback intact

## Compatibility considerations

This is a documentation-only change. No backward compatibility concerns.

## Security considerations

No security impact — documentation correction only.

## Rollback considerations

Simple revert: restore the original Note text at line 59 and the removed sentence at line 75.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| docs/03_rag_03_04_query_pipeline-search-stages.md | Manual — review corrected sections 5.2/5.3 | Manual inspection | Both sections consistent, no contradiction |

## Completion criteria

- [ ] `docs/03_rag_03_04_query_pipeline-search-stages.md` section 5.2's Note reflects the methods' removal rather than describing them as still-present dead code (REQ-002)
- [ ] `docs/03_rag_03_04_query_pipeline-search-stages.md` section 5.3 no longer claims `rerank_candidates()` passes an RRF flag to `FusionStage` (REQ-002)

## Out of scope

- Any change to `SearchStage.run()`/`RerankStage.run()` (the actually-used implementations)
- Any change to the `stat_search_embed_failed`/`stat_search_fts_errors` counters themselves
- Code deletions (separate document)

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: Confirm current text | Completed | 20260914-001621 | 20260914-001621 |  |
| 2 | Phase 2: Update section 5.2's Note | Completed | 20260914-001621 | 20260914-001621 |  |
| 3 | Phase 2: Remove false claim in section 5.3 | Completed | 20260914-001622 | 20260914-001622 |  |
| 4 | Verification: manual review | Completed | 20260914-001622 | 20260914-001622 |  |

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
- **Requirement ID**: REQ-002
- **Source issue**: issues/20260913-183006_dead_code_search_rerank_methods.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260913-203623_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260913-224229
- **Related target files**: docs/03_rag_03_04_query_pipeline-search-stages.md