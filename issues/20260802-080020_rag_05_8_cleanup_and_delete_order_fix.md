# Fix docs/03_rag_05_8 delete_document() deletion-order error and remove CLI-help/signature transcriptions

## Priority
High

## Summary
`docs/03_rag_05_8-rag-mcp-internal-operations-direct-db-access.md` states `delete_document()` performs a 3-stage deletion (`chunks_vec → chunks → documents`), but both implementations of `document_manager.py` (rag/ingestion and mcp_servers/rag_pipeline) confirm only 2 stages: `chunks_vec → documents`, with `documents`'s deletion cascading to `chunks` via a CASCADE constraint — there is no explicit `DELETE` against `chunks` in code. `docs/03_rag_91_design_notes-part1.md`'s DESIGN-3 already describes this correctly. Separately, `05_8` also transcribes crawler/chunk_splitter/ingester `--help` output and a `list_documents()` signature verbatim.

## Reason for Change
The deletion-order claim is a confirmed factual error that would mislead a reviewer assessing the impact of a CASCADE-constraint change, since they'd expect a 3rd deletion stage that doesn't exist. The CLI-help/signature transcriptions are mechanical, auto-generatable content that adds maintenance burden without design value.

## Implementation Intent
Correct the deletion-order description to match `91_design_notes-part1`'s confirmed-accurate 2-stage description, and remove the CLI-help/signature transcriptions, replacing them with a pointer to the implementation tree — while explicitly keeping the file's most valuable content: its opening responsibility-boundary declaration (RAG MCP internal operations vs. Agent-layer direct DB access).

## Target Files or Areas
`docs/03_rag_05_8-rag-mcp-internal-operations-direct-db-access.md`

## Required Changes
- Replace the 3-stage deletion description with: "`delete_document()` deletes in 2 stages: `chunks_vec → documents`. The `documents` table deletion cascades to `chunks` via a CASCADE constraint; there is no explicit `DELETE` against `chunks` in code (see `docs/03_rag_91_design_notes-part1.md` DESIGN-3)."
- Remove the crawler/chunk_splitter/ingester `--help` output transcriptions and the `list_documents()` signature listing; replace with a pointer to the implementation tree for current CLI usage/signatures.
- Keep the opening responsibility-boundary declaration unchanged.

## Acceptance Criteria
The deletion-order description matches `91_design_notes-part1` and confirmed implementation; no CLI `--help` output or method signature is transcribed verbatim; the responsibility-boundary declaration remains intact.

## Testing Expectations
Not required (documentation-only). Manually re-verify against both `document_manager.py` implementations (rag/ingestion and mcp_servers/rag_pipeline) before finalizing.

## Documentation Impact
`docs/03_rag_05_8` corrected and shortened.

## Out of Scope
Do not change the actual deletion implementation or CASCADE constraint in this issue — documentation only.

## AI Implementation Instruction
This is a confirmed factual error — apply the deletion-order fix directly, using `91_design_notes-part1` as the reference. Verify both `document_manager.py` implementations still match before finalizing, since this review compared 2 separate copies of similar logic.

## Traceability
- Workflow phase: issue-creation
- Source: docs_review_rag.md §1 (横断的な確定済み誤り item 2), §2 削除候補 item 10, §5 例2, §6A (delete_document()の削除順序)
- Generated at: 2026-08-02
