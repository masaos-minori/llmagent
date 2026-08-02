# Fix pervasive line-number reference drift across RAG docs; switch to name-based references

## Priority
Medium

## Summary
Multiple `docs/03_rag_*.md` files reference specific line numbers that have drifted from current source: `docs/03_rag_01_system_overview-part2.md` cites `config/agent.toml:43` (actual: line 17); `docs/03_rag_03_02_query_pipeline-rag-pipeline-class-part1.md` cites `repository.py:232` (actual: line 237); `docs/03_rag_03_06_query_pipeline-helpers-and-cache-part2.md` cites `llm_client.py:49` (actual: line 56); `docs/03_rag_05_1-configuration-reference.md` cites `call_rag_service()`'s `timeout=10.0` at line 121 (actual: line 123).

## Reason for Change
Line-number references are inherently fragile — every one of the 4 checked in this review had already drifted. `docs/03_rag_05_5` already demonstrates a more robust pattern (referencing by key/function/variable name instead of line number), which this review recommends applying domain-wide.

## Implementation Intent
Fix the 4 confirmed line-number drifts directly, and replace line-number-based references throughout `docs/03_rag_*.md` with key-name, function-name, or section-name-based references, following `05_5`'s existing pattern.

## Target Files or Areas
`docs/03_rag_01_system_overview-part2.md`, `docs/03_rag_03_02_query_pipeline-rag-pipeline-class-part1.md`, `docs/03_rag_03_06_query_pipeline-helpers-and-cache-part2.md`, `docs/03_rag_05_1-configuration-reference.md`; broader audit across all `docs/03_rag_*.md`

## Required Changes
- Fix the 4 confirmed line-number drifts, converting each to a name-based reference (e.g. "in the `<function_name>` function" or "the `<key_name>` config key") instead of a raw line number.
- Search all `docs/03_rag_*.md` files for other line-number-style references (pattern like `\.py:\d+`) and convert them to name-based references following the same pattern.
- Use `docs/03_rag_05_5`'s existing reference style as the model.

## Acceptance Criteria
The 4 confirmed drifted references are corrected and converted to name-based references; a broader search for `.py:<number>`-style references across `docs/03_rag_*.md` has been performed, with findings converted or listed for follow-up.

## Testing Expectations
Not required (documentation-only). Manually re-verify each corrected reference against current source line numbers is unnecessary once converted to name-based references (that is the point of the fix) — but verify the referenced function/key names still exist.

## Documentation Impact
4 files corrected directly; potentially more files updated via the broader audit.

## Out of Scope
Do not change the actual source code in this issue — documentation only.

## AI Implementation Instruction
Follow `docs/03_rag_05_5`'s existing name-based reference style exactly, so the domain becomes consistent rather than introducing yet another referencing convention.

## Traceability
- Workflow phase: issue-creation
- Source: docs_review_rag.md §1 (再構成の基本方針 item 3), §6A (行番号参照のズレ)
- Generated at: 2026-08-02
