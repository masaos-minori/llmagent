# Simplify docs/03_rag_03_03 field tables (dedupe with 04_02); confirm HTTP-mode last_fetch_result update behavior

## Priority
Medium

## Summary
`docs/03_rag_03_03_query_pipeline-context-and-diagnostics.md` transcribes `PipelineContext`, `SearchDiagnostics`, and `get_diagnostics()` return-value fields verbatim, duplicating `docs/03_rag_04_02_dto-models_result.md`. Separately, it is unconfirmed whether `call_rag_service()`'s docstring claim — that `set_fetch_result` is defined but never actually called — means HTTP-mode `fetch_result` is genuinely never updated in practice, since the full call graph hasn't been exhaustively traced.

## Reason for Change
The field-table duplication doubles maintenance effort against the canonical `04_02` DTO document. The `last_fetch_result` update question bears on whether diagnostic information is reliable in HTTP mode — if stale, an operator investigating an incident via `fetch_result` could be misled by outdated information.

## Implementation Intent
Remove the duplicated field tables, deferring to `04_02`, while keeping the `http_result_kind` dual-definition (4-value enum vs. 3-value string) boundary-condition note, which this review identifies as the most important content here. Investigate the call graph for `set_fetch_result` to confirm or refute the docstring's claim.

## Target Files or Areas
`docs/03_rag_03_03_query_pipeline-context-and-diagnostics.md`

## Required Changes
- Remove the `PipelineContext`/`SearchDiagnostics`/`get_diagnostics()` field tables; replace with a reference to `docs/03_rag_04_02_dto-models_result.md`.
- Keep the `http_result_kind` dual-definition boundary-condition note intact.
- Trace the actual call graph for `set_fetch_result` in HTTP mode to confirm whether `last_fetch_result` is genuinely never updated; document the confirmed finding (or note it remains unconfirmed if the trace is inconclusive, keeping the existing appropriately-cautious Needs Confirmation framing).

## Acceptance Criteria
No duplicated field table remains (deferred to `04_02`); the `http_result_kind` dual-definition note is preserved; the `last_fetch_result` update question is either confirmed via call-graph tracing or explicitly retained as Needs Confirmation with the specific uncertainty noted.

## Testing Expectations
Not required (documentation-only); the call-graph trace is a source-reading exercise, not a test run.

## Documentation Impact
`docs/03_rag_03_03` shortened; `docs/03_rag_04_02` remains canonical for field-level DTO detail.

## Out of Scope
Do not edit `docs/03_rag_04_02` in this issue (its own fixes tracked separately). Do not change `call_rag_service()`'s implementation in this issue — documentation only.

## AI Implementation Instruction
Attempt a genuine call-graph trace for `set_fetch_result` before concluding either way — if genuinely inconclusive, preserve the existing appropriately-cautious "Needs confirmation" framing rather than asserting a guessed answer.

## Traceability
- Workflow phase: issue-creation
- Source: docs_review_rag.md §2 削除候補 item 7, §6B (HTTPモード成功時のlast_fetch_result更新有無)
- Generated at: 2026-08-02
