# Resolve PipelineRunResult.result_source vs SearchDiagnostics.result_source dual-definition (docs/03_rag_03_06-part2 + 04_05)

## Priority
Medium

## Summary
Both `PipelineRunResult.result_source` and `SearchDiagnostics.result_source` exist, but confirmed grep analysis shows `PipelineRunResult.result_source` is always `None` in all currently-traced call paths — while it's unconfirmed whether any other call path (e.g. a plugin or less-common integration) ever sets it explicitly.

## Reason for Change
Two fields with the same name but different actual behavior (one always `None`, one presumably meaningful) is a genuine trap for an implementer who reads `PipelineRunResult.result_source` expecting it to carry the same information as `SearchDiagnostics.result_source` — they would silently get `None` and could miss a real bug.

## Implementation Intent
Exhaustively enumerate all call sites that construct or use `PipelineRunResult`, confirming whether `result_source` is ever set to a non-`None` value anywhere. Once confirmed, either deprecate/remove the unused field or clearly separate its purpose from `SearchDiagnostics.result_source` in documentation.

## Target Files or Areas
`docs/03_rag_03_06_query_pipeline-helpers-and-cache-part2.md`, `docs/03_rag_04_05_dto-models-pipeline-run-result.md` (or equivalent DTO doc for `PipelineRunResult`)

## Required Changes
- Enumerate all `PipelineRunResult` construction/usage call sites (not just the ones already checked) to confirm whether `result_source` is ever non-`None`.
- If confirmed always `None`: document this explicitly as a known dead/unused field, and consider (via a separate implementation issue) whether to deprecate it.
- If a non-`None` case is found: document the distinct purposes of the two `result_source` fields clearly, so readers don't conflate them.

## Acceptance Criteria
The relationship between `PipelineRunResult.result_source` and `SearchDiagnostics.result_source` is documented based on a genuinely exhaustive call-site check, not a partial one — with the finding stated as confirmed fact.

## Testing Expectations
Not required (documentation-only); the investigation is a call-site enumeration exercise, not a test run.

## Documentation Impact
Both files updated with the confirmed finding.

## Out of Scope
Do not remove or refactor `PipelineRunResult.result_source` in this issue — that would be a separate implementation issue if this investigation confirms it's genuinely dead code.

## AI Implementation Instruction
This requires an exhaustive call-site search, not a sampling — the prior investigation explicitly notes it wasn't exhaustive. If full exhaustiveness isn't achievable in reasonable time, state the confidence level explicitly rather than asserting full confirmation.

## Traceability
- Workflow phase: issue-creation
- Source: docs_review_rag.md §6B (PipelineRunResult.result_sourceとSearchDiagnostics.result_sourceの二重定義の解消方針)
- Generated at: 2026-08-02
