## Goal

Add a short note after `docs/03_rag_03_04_query_pipeline-search-stages.md`'s `use_rrf=False` quality-degradation warning, stating that no quantitative benchmark data (recall@k/precision@k), disable thresholds, or ADR back the warning's severity claim — without fabricating benchmark numbers or thresholds that do not exist (REQ-001).

## Scope

- Add one short note after the existing "Search Quality Trade-off" warning/table (`docs/03_rag_03_04_query_pipeline-search-stages.md:77-96`) stating no quantitative data or ADR backs the severity claim

## Assumptions

- The `grep -rln`/`grep -rl` searches performed this cycle across `docs/`, `tests/`, and `docs/adr/` found the complete set of any existing benchmark data or ADR references, if they existed

## Design decisions

1. State the absence of quantitative data as a fact, not silence — this tells a future operator not to keep searching for benchmark data that doesn't exist, and sets expectations that any disable-RRF decision needs its own measurement
2. Keep the existing qualitative warning, mechanism table, and usage guidance unchanged — they are accurate mechanism descriptions (confirmed against `FusionStage`'s implementation), just not quantitatively substantiated; this Plan adds context, not a correction to what's already there

## Alternatives considered

1. Fabricating recall@k/precision@k benchmark numbers, latency-vs-quality thresholds, or an ADR citation that does not exist — rejected because the Issue's Recommended Action requests exactly this kind of content — per user direction, consistent with sibling issues `183021`/`183024` processed this same cycle, this Plan states the gap rather than inventing content to fill it
2. Running actual retrieval-quality benchmarks comparing `use_rrf=True`/`False` — rejected because a substantial, separate effort requiring an evaluation dataset and methodology, not a documentation-only fix
3. Correcting the unrelated stale claim at line 75 ("`RagPipeline.rerank_candidates()` passes the RRF configuration flag to `FusionStage`") — rejected because already addressed by a sibling Plan (`plans/20260913-203623_plan.md`, this cycle)

## Implementation

### Target file

`docs/03_rag_03_04_query_pipeline-search-stages.md`

### Procedure

1. Re-confirm no benchmark data or ADR exists
2. Add the clarifying note after the "Search Quality Trade-off" section

### Method

Phase 1: Preparation — re-confirm evidence line numbers
- Re-run `grep -rln "recall@k|precision@k"` across `docs/`/`tests/` and `grep -rl "use_rrf"` across `docs/adr/` to reconfirm no match (REQ-001; `docs/03_rag_03_04_query_pipeline-search-stages.md`)

Phase 2: Core Logic — add the clarifying note
- Add the note after the "Search Quality Trade-off" section (line 96) (REQ-001; `docs/03_rag_03_04_query_pipeline-search-stages.md`)

### Details

**Phase 1:** Verify via read/grep that:
- Section at `docs/03_rag_03_04_query_pipeline-search-stages.md:77-96` contains the "Search Quality Trade-off" section:
  - Line 79: "**Warning:** `use_rrf=False` is NOT a harmless fallback; it represents a **significant degradation in quality**."
  - Lines 83-86: Qualitative mechanism/impact table comparing `use_rrf=True` vs `use_rrf=False`
  - Lines 88-92: Usage guidance for when `use_rrf=False` is used
  - Lines 94-97: Observability details
- No recall@k/precision@k benchmark found via `grep -rln` across `docs/`/`tests/` — confirmed no match
- No ADR references `use_rrf` via `grep -rl` across `docs/adr/` — confirmed no match
- The existing warning's severity ("significant degradation") and the qualitative mechanism description (RRF's cross-list ranking vs. dedup-only's `rrf_score=0.0` for all hits) are accurate as *mechanism* descriptions — confirmed against `FusionStage`'s actual implementation — but the *magnitude* claim ("significant") is not backed by any measured comparison

**Phase 2:** Append the following note after line 96:

```markdown
Note: No quantitative benchmark data (recall@k/precision@k or other metrics) comparing `use_rrf=True`/`False` exists in this repository, nor does any ADR document specific thresholds for when disabling RRF is acceptable. If RRF is disabled for latency reasons, measure the actual quality impact for your specific use case rather than relying on this qualitative warning alone.
```

## Compatibility considerations

This is a documentation-only additive change. No backward compatibility concerns. However, accurately documenting the absence of quantitative backing helps operators understand whether disabling RRF is an acceptable trade-off for their use case, beyond the unquantified "significant degradation" characterization.

## Security considerations

No security impact — documentation addition only. However, accurate documentation of the rationale's basis is important for understanding whether the no-retry policy's justification is empirically grounded or merely a design assumption.

## Rollback considerations

Simple revert: remove the added note. The underlying code remains unchanged.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| docs/03_rag_03_04_query_pipeline-search-stages.md | Manual — review added note for accuracy | Manual inspection + repository-wide `grep` | Note accurately states the absence of quantitative backing |

## Completion criteria

- [ ] The note states no recall@k/precision@k or other quantitative benchmark comparing `use_rrf=True`/`False` exists in this repository (REQ-001)
- [ ] The note states no ADR documents specific thresholds for disabling RRF (REQ-001)
- [ ] The note recommends measuring actual quality impact for the specific use case before relying on this qualitative warning alone (REQ-001)
- [ ] The existing warning, mechanism table, and usage guidance (lines 77-96) remain unchanged

## Out of scope

- Fabricating recall@k/precision@k benchmark numbers, latency-vs-quality thresholds, or an ADR citation that does not exist (the Issue's Recommended Action requests exactly this kind of content — per user direction, consistent with sibling issues `183021`/`183024` processed this same cycle, this Plan states the gap rather than inventing content to fill it)
- Running actual retrieval-quality benchmarks comparing `use_rrf=True`/`False` (a substantial, separate effort requiring an evaluation dataset and methodology, not a documentation-only fix)
- Correcting the unrelated stale claim at line 75 ("`RagPipeline.rerank_candidates()` passes the RRF configuration flag to `FusionStage`") — already addressed by a sibling Plan, `plans/20260913-203623_plan.md`, this cycle

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: Re-confirm no benchmark data or ADR exists | Completed | — | 20260914-120100 | |
| 2 | Phase 2: Add the clarifying note | Completed | — | 20260914-120100 | |
| 3 | Verification: manual review | Completed | — | 20260914-120100 | |

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
- **Source issue**: issues/20260913-183025_missing_fusion_quality_tradeoff_quantification.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260913-211855_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260914-094636
- **Related target files**: docs/03_rag_03_04_query_pipeline-search-stages.md
