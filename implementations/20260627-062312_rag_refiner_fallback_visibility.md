## Goal

Improve visibility and policy clarity for Refiner fallback behavior when `use_refiner=true` — add counters/diagnostics for refiner failures, clarify retry/no-retry policy in docs, and improve `/rag search --debug` visibility.

## Scope

**In-Scope**:
- Add counters or diagnostics for `refiner_returned_empty` and `refiner_exception`
- Clarify in docs why retry is not performed, or add configurable retry if desired
- Improve `/rag search --debug` visibility for refiner fallback

**Out-of-Scope**:
- Replacing the Refiner model
- Redesigning the entire Augment stage

## Assumptions

1. No retry is currently performed — confirmed by pipeline_refiner.py:76 "No retry is performed"
2. Refiner fallback is already tracked in `StageResult` with status="fallback" and fallback_reason set
3. The `/rag search --debug` output shows stage results but doesn't have explicit refiner fallback frequency tracking

## Implementation

### Target file: scripts/rag/pipeline.py

**Procedure**: Add refiner fallback diagnostics to SearchDiagnostics or create a separate refiner diagnostics section in get_diagnostics().

**Method**: Modify pipeline.py to track refiner fallback counts.

**Details**:
1. Add `refiner_fallback_count` field to SearchDiagnostics
2. Track `refiner_returned_empty` vs `refiner_exception` separately
3. Update AugmentStage to increment counter on each refiner fallback

### Target file: scripts/agent/commands/cmd_ingest.py

**Procedure**: Improve /rag search --debug visibility for refiner fallback.

**Method**: Modify debug output formatting in cmd_ingest.py.

**Details**:
1. In cmd_ingest.py, enhance debug output to show refiner fallback frequency when multiple queries are processed
2. Show explicit "[refiner] fallback: N times" in debug summary

### Target file: docs/03_rag_03_query_pipeline.md

**Procedure**: Document retry/no-retry policy.

**Method**: Add clarification in documentation about why retry is not performed.

**Details**:
1. Clarify in docs why retry is not performed (non-critical failure — raw chunks are acceptable degraded behavior)
2. Document that `use_refiner=false` disables refiner entirely (no fallback possible)

### Target file: docs/03_rag_05_configuration_and_operations.md

**Procedure**: Add refiner config documentation.

**Method**: Document existing refiner config fields in configuration documentation.

**Details**:
1. Document existing refiner config fields (refiner_max_tokens, refiner_max_chars_per_chunk, refiner_timeout)
2. If retry is added later, add `refiner_retry` config with clear limits

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| SearchDiagnostics / get_diagnostics() | Verify refiner fallback counters present | Review diagnostics model | refiner_fallback_count and refiner_exception_count fields present |
| /rag search --debug | Verify debug output shows refiner fallback frequency | Review cmd_ingest.py debug formatting | "[refiner] fallback: N times" shown in debug summary |
| docs/03_rag_03_query_pipeline.md | Verify retry/no-retry policy documented | Check documentation | Clear explanation of why no retry is performed |

## Risks

- **Risk**: Adding refiner retry may introduce unexpected behavior if LLM failures are transient and retry would succeed | **Likelihood**: Medium | **Mitigation**: If adding retry, document explicit config (refiner_retry) with clear limits (max retries, backoff); mark as Needs confirmation until policy is approved | False
- **Risk**: Per-query refiner fallback counters may not reflect true frequency for long-running sessions | **Likelihood**: Low | **Mitigation**: Clarify that counters are per-query; add note about cumulative tracking in production monitoring if needed | False
