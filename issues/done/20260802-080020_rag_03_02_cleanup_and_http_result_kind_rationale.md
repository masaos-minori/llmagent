# Simplify docs/03_rag_03_02 (parts 1+2): remove constructor/method/HTTP-request tables; document http_result_kind design rationale

## Priority
Medium

## Summary
`docs/03_rag_03_02_query_pipeline-rag-pipeline-class-part1.md` contains verbatim "constructor," "public attributes," and "public methods" tables; `part2` contains an "HTTP RAG request detail" table — all mechanical signature/code transcriptions. Separately, `part2`'s `http_result_kind` classification table and its "remote_empty is not a fallback but a success" note are confirmed-accurate and valuable, but the design reasoning behind hardcoding `rag_service_url=""` on the MCP adapter side (to prevent infinite HTTP-delegation loops) is not explained.

## Reason for Change
The mechanical tables add no design value beyond what reading the source directly provides. The infinite-delegation-prevention design reasoning is a genuinely non-obvious and important architectural decision that should be explicit.

## Implementation Intent
Remove the mechanical tables, keeping the `module_cfg` bypass behavior and `http_result_kind` semantics already correctly identified as valuable. Add the infinite-delegation-prevention design rationale.

## Target Files or Areas
`docs/03_rag_03_02_query_pipeline-rag-pipeline-class-part1.md`, `docs/03_rag_03_02_query_pipeline-rag-pipeline-class-part2.md`

## Required Changes
- Remove the constructor/public-attributes/public-methods tables in `part1`.
- Remove the "HTTP RAG request detail" table in `part2`.
- Keep `module_cfg`'s bypass-behavior description and `http_result_kind`'s semantics (including the `remote_empty`-is-success note) intact.
- Add: "MCPアダプタ側で`rag_service_url=""`を固定することで、HTTP委譲先が再度HTTP委譲を試みる無限ループを構造的に防止している。"

## Acceptance Criteria
No verbatim constructor/attribute/method/HTTP-request table remains; `module_cfg` bypass and `http_result_kind` semantics are preserved; the infinite-delegation-prevention rationale is added.

## Testing Expectations
Not required (documentation-only). Note: this issue does not cover the separate `[debug]` output error in `part2`, tracked in another issue.

## Documentation Impact
Both parts of `docs/03_rag_03_02` corrected and shortened.

## Out of Scope
Do not fix the nonexistent `[debug]` output example in this issue — tracked in a separate issue covering both `03_02-part2` and `03_04` together.

## AI Implementation Instruction
Verify the `rag_service_url=""` hardcoding and its infinite-loop-prevention purpose against actual MCP adapter source before finalizing the added rationale.

## Traceability
- Workflow phase: issue-creation
- Source: docs_review_rag.md §2 削除候補 item 6, §4 強化候補 (03_02-part2 http_result_kind)
- Generated at: 2026-08-02
