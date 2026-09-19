# ADR-010 Decision #9 vs. call_rag_service() ValueError handling mismatch

## Priority
Medium

## Summary
Resolve discrepancy between ADR-010 Decision #9 ("parse errors should be logged and treated as empty result, `""`, not a fallback trigger") and actual `call_rag_service()` behavior which returns `None` on parse `ValueError`, triggering in-process fallback. Determine whether code or ADR should be corrected.

## Background
ADR-010 INV-07 states: "解析エラーはログに記録し、空結果として扱う" (parse errors should be logged and treated as an empty result). Decision Details #9 explicitly says parse errors should return `""` (empty string), not trigger fallback. However, `scripts/rag/pipeline_service.py::call_rag_service()` catches `ValueError` from JSON parsing and returns `None`, which triggers in-process fallback per ADR-010 INV-04. An existing test (`tests/rag/test_rag_pipeline_service.py::test_json_parse_error_calls_set_fallback_reason`) confirms and defends this behavior. CI-004 closing note explicitly left this open rather than resolving it.

## Problem
ADR-010 Decision #9 and INV-07 require parse errors to produce `""` (no fallback), but `call_rag_service()` produces `None` (triggers fallback). Whether this reflects an intentional, undocumented refinement of Decision #9, or an actual deviation from it, has not been investigated.

## Reason for Change
This is a documented architectural decision versus implementation gap. If the code is correct, ADR-010 needs amendment via ADR Change Protocol + RACI approval. If the ADR is correct, the code needs fixing. Either way, the inconsistency must be resolved to maintain architectural integrity.

## Implementation Intent
Investigate the discrepancy by reading ADR-010's full Decision #9 context and `call_rag_service()`'s `ValueError` handling. Decide whether: (1) `call_rag_service()` should return `""` instead of `None` on parse error (aligning with ADR-010), or (2) Decision #9 should be clarified/amended to explicitly cover the `ValueError` case (allowing `None` return). Update or add the corresponding test once the correct behavior is confirmed.

## Target Files or Areas
- `docs/adr/ADR-010-rag-fallback.md` (Decision Details #9, INV-07)
- `scripts/rag/pipeline_service.py::call_rag_service()`
- `tests/rag/test_rag_pipeline_service.py::test_json_parse_error_calls_set_fallback_reason`

## Required Changes
- Read ADR-010 Decision Details #9 context to confirm intended scope
- Read `call_rag_service()`'s `ValueError` handling path
- Decide whether code or ADR should be corrected
- If code correction: modify `call_rag_service()` to return `""` on parse `ValueError`
- If ADR amendment: create new ADR to supersede Decision #9
- Update or add test to reflect confirmed correct behavior

## Constraints
- ADR amendment requires ADR Change Protocol + RACI approval from `@data-eng`
- Cannot resolve by editing `plans/20260918-120636_plan.md` or `docs/adr-index.md`'s INV-015 row — that Plan's REQ-006 only corrects the already-resolved 4xx-fallback classification
- Must preserve existing test coverage for other `call_rag_service()` behaviors

## Acceptance Criteria
- [ ] Architect judgment recorded: either code aligns with ADR-010 or ADR-010 is amended
- [ ] If code change: `call_rag_service()` returns `""` on parse `ValueError` instead of `None`
- [ ] If ADR change: new ADR created per ADR Change Protocol
- [ ] Test updated to reflect confirmed correct behavior
- [ ] No regressions in other `call_rag_service()` error paths

## Testing Expectations
- Unit test: verify `call_rag_service()` returns `""` on parse `ValueError` (if code change)
- Regression test: verify other error paths (HTTP errors, timeouts) still behave correctly
- Integration test: verify fallback is NOT triggered on parse error (if code change)

## Documentation Impact
If ADR is amended: update ADR-010 Decision Details #9 and INV-07 text. If code is corrected: update Known Deviations section if applicable. Document the resolution rationale.

## Out of Scope
- Resolving other known deviations in ADR-010
- Changing fallback policy for HTTP errors (4xx/5xx) — those are handled separately

## Dependencies
- ADR-010 governance process (for potential ADR amendment)
- `@data-eng` team review/approval (for potential ADR amendment)

## Unresolved Questions
- Whether the `None`-return behavior for a parse `ValueError` is an intentional, undocumented refinement of Decision #9, or an actual deviation from it

## AI Implementation Instruction
- Do NOT implement without first confirming the correct direction (code fix vs. ADR amendment)
- If code fix: change `call_rag_service()` to return `""` on parse `ValueError`, update test accordingly
- If ADR amendment: follow ADR Change Protocol, create new ADR superseding Decision #9
- Preserve all other `call_rag_service()` error handling paths
- Do not modify unrelated files or introduce new dependencies

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260918-120636_plan.md
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260919-094750
- **Related target files**: docs/adr/ADR-010-rag-fallback.md, scripts/rag/pipeline_service.py, tests/rag/test_rag_pipeline_service.py
