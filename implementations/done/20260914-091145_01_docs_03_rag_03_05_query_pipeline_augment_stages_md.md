## Goal

Expand `docs/03_rag_03_05_query_pipeline-augment-stages.md`'s "Content-only Invariance Rule" note (section 5.5 AugmentStage) with an inline explanation of what it means, why it exists, its scope, and its limitation — currently the rule is stated with only a reference to ADR-009, requiring a reader to open a separate document to understand it (REQ-001).

## Scope

- Add inline explanation (meaning, rationale, scope, limitation) to the existing "Content-only Invariance Rule" note under `### 5.5 AugmentStage`, keeping the existing ADR-009 cross-reference for full detail

## Assumptions

- ADR-009's stated rationale (COALESCE fallback, lossy normalization) remains the current, authoritative design rationale — confirmed by direct reading, not merely assumed from the Issue's own claim
- No other documentation file needs the same inline expansion for this specific rule (this Plan's search was scoped to the Issue's cited file)

## Design decisions

1. Summarize ADR-009's rationale rather than duplicate it in full — ADR-009 remains the authoritative source for alternatives and tradeoffs; this note answers the immediate "what/why/scope/limitation" questions a reader has when first encountering the rule, deferring deeper design discussion to the ADR
2. Explicitly state the Japanese-normalization limitation (point 4) rather than omit it — the Issue's own Recommended Action flags this as a specific limitation worth documenting, and it is directly confirmed by ADR-009's own text (normalization is lossy and Japanese-specific)

## Alternatives considered

1. Rewriting or restructuring ADR-009 itself — rejected because it remains the authoritative source for full rationale, alternatives, and tradeoffs — this Plan adds a summary, not a duplicate
2. Changing AugmentStage's implementation — rejected because this is a documentation-only change; no code changes are needed
3. Omitting the Japanese-normalization limitation — rejected because the Issue's own Recommended Action flags this as a specific limitation worth documenting, and it is directly confirmed by ADR-009's own text

## Implementation

### Target file

`docs/03_rag_03_05_query_pipeline-augment-stages.md`

### Procedure

1. Re-confirm ADR-009's current wording
2. Expand the note with inline explanation

### Method

Phase 1: Preparation — re-confirm evidence line numbers
- Re-read `docs/adr/ADR-009-rag-ft5-text-separation.md` lines 62-71 to confirm the rationale, scope, and limitation details are unchanged before summarizing them (REQ-001; `docs/03_rag_03_05_query_pipeline-augment-stages.md`)

Phase 2: Core Logic — expand the note
- Expand the "Content-only Invariance Rule" note with the 4 required aspects, retaining the ADR-009 cross-reference (REQ-001; `docs/03_rag_03_05_query_pipeline-augment-stages.md`)

### Details

**Phase 1:** Verify via read/grep that:
- Section at `docs/03_rag_03_05_query_pipeline-augment-stages.md:54` states "**Content-only Invariance Rule:** AugmentStage only formats `content` and never uses `normalized_content`. See [ADR-009](adr/ADR-009-rag-ft5-text-separation.md) for rationale, alternatives, and tradeoffs."
- ADR-009's rationale confirmed at `docs/adr/ADR-009-rag-ft5-text-separation.md`:
  - Line 63: "FTS5は`COALESCE(normalized_content, content)`をIndex化する" (FTS5 indexes `COALESCE(normalized_content, content)`) — confirming the Issue's claim that FTS5 falls back to `content` when `normalized_content` is absent, so `content` alone is a complete, valid representation for any purpose that doesn't need the search-normalized form
  - Line 71: "AugmentStageは`content`のみを出力し、`normalized_content`をLLM Contextへ出力しない" (AugmentStage outputs only `content`, never outputting `normalized_content` to the LLM context) — the rule's exact scope
  - Line 65: "英語、コード、正規化対象外は`normalized_content = NULL`とし、`content`へFallbackする" (English, code, and non-normalization-target content sets `normalized_content = NULL`, falling back to `content`) — confirms `normalized_content` is Japanese-specific and not universally populated
  - Line 67: "`normalized_content`から元テキストを復元しない" (the original text cannot be reconstructed from `normalized_content`) — this is why `content`, not `normalized_content`, must be the source for any human/LLM-facing output: `normalized_content` is a lossy, search-only derivative

**Phase 2:** Replace the existing "Content-only Invariance Rule" note at line 54 with the following expanded version:

```markdown
**Content-only Invariance Rule:** AugmentStage only formats `content` and never uses `normalized_content`. Meaning: AugmentStage formats and outputs only the raw `content` field, never the search-normalized `normalized_content` field. Rationale: FTS5 indexes `COALESCE(normalized_content, content)`, so `content` alone is always a complete, valid representation, while `normalized_content` is a lossy, non-reconstructible derivative (per ADR-009). Scope: This rule applies specifically to AugmentStage's output formatting, not to the search/indexing layer, which does use `normalized_content` when present. Limitation: For Japanese content, the LLM-facing output does not benefit from Sudachi normalization (stopword removal, etc.) since only the raw `content` is shown. See [ADR-009](adr/ADR-009-rag-ft5-text-separation.md) for rationale, alternatives, and tradeoffs.
```

## Compatibility considerations

This is a documentation-only additive change. No backward compatibility concerns. However, accurately documenting the Content-only Invariance Rule helps readers understand why the pipeline does not pass the search-optimized text to the LLM, which could otherwise seem like an oversight.

## Security considerations

No security impact — documentation addition only. However, accurately documenting this rule helps readers understand the separation between search optimization (which uses normalized text) and LLM context delivery (which uses raw text), which is relevant for understanding the pipeline's defense posture against injection attacks.

## Rollback considerations

Simple revert: remove the added inline explanation and restore the original single-sentence note. The underlying code remains unchanged.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| docs/03_rag_03_05_query_pipeline-augment-stages.md | Manual — cross-check expanded note against ADR-009 | Manual inspection | Every claim traceable to a specific ADR-009 line |

## Completion criteria

- [ ] The note states AugmentStage outputs only `content`, never `normalized_content` (meaning) (REQ-001)
- [ ] The note states FTS5's `COALESCE(normalized_content, content)` indexing makes `content` alone always valid, while `normalized_content` is a lossy, non-reconstructible derivative (rationale) (REQ-001)
- [ ] The note states the rule applies to AugmentStage's output formatting, not to the search/indexing layer (scope) (REQ-001)
- [ ] The note states Japanese LLM-facing output does not benefit from Sudachi normalization as a result of this rule (limitation) (REQ-001)
- [ ] The existing ADR-009 cross-reference is retained (REQ-001)

## Out of scope

- Rewriting or restructuring ADR-009 itself (it remains the authoritative source for full rationale, alternatives, and tradeoffs — this Plan adds a summary, not a duplicate)
- Changing AugmentStage's implementation

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: Re-confirm ADR-009's current wording | Completed | — | — | Confirmed via direct reading |
| 2 | Phase 2: Expand the note | Completed | — | — | Added meaning/rationale/scope/limitation |
| 3 | Verification: manual review | Completed | — | — | Quality check passed |

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
- **Source issue**: issues/20260913-183019_missing_augment_invariance_rule_explanation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260913-210605_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260914-091145
- **Related target files**: docs/03_rag_03_05_query_pipeline-augment-stages.md
