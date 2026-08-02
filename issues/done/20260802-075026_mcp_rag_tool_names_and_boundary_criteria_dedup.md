# Fix stale RAG tool names and dedupe MDQ/RAG boundary criteria (docs/04_mcp_05_04 + docs/04_mcp_04_04)

## Priority
High

## Summary
`docs/04_mcp_05_04_mdq-rag-boundary.md` lists RAG tool names (`ingest`, `search`, `get_document`, `delete_document`, `list_documents`) that do not exist in current implementation — the actual, confirmed tool names are `rag_run_pipeline`, `rag_debug_pipeline`, `rag_list_documents`, `rag_delete_document`. A sibling file, `docs/04_mcp_05_03`, already uses the correct names, meaning this file alone was left stale. Separately, the same MDQ-vs-RAG decision criteria are duplicated (in slightly different form) across `docs/04_mcp_04_04_mdq.md` and this file.

## Reason for Change
This is a confirmed factual error — an Agent implementer following this document would write calls to nonexistent tools. The duplication of decision criteria across 2 files compounds the staleness risk (only one of the two was updated when tool names changed).

## Implementation Intent
Correct the tool names in `05_04`, and consolidate the MDQ-vs-RAG decision criteria into `05_04` as the canonical boundary document, replacing `04_04`'s version with a one-line reference.

## Target Files or Areas
`docs/04_mcp_05_04_mdq-rag-boundary.md`, `docs/04_mcp_04_04_mdq.md`

## Required Changes
- Replace the stale RAG tool names in `05_04` with the correct set: `rag_run_pipeline` (ingest/pipeline execution), `rag_debug_pipeline` (debug execution), `rag_list_documents` (listing), `rag_delete_document` (deletion).
- Note explicitly that no standalone search-only tool currently exists; search is provided as a mode of `rag_run_pipeline` — confirm the exact invocation method for search-only use via source inspection, and register as a Needs Confirmation item if not determinable.
- Consolidate the MDQ-vs-RAG decision criteria: keep the full criteria (data-ownership table) in `05_04` as canonical; replace `04_04`'s version with a one-line reference to `05_04`.

## Acceptance Criteria
`05_04` lists only currently-existing RAG tool names; the search-only invocation method is either documented or explicitly tracked as Needs Confirmation; `04_04` references `05_04` for boundary criteria instead of duplicating it.

## Testing Expectations
Not required (documentation-only). Manually verify current RAG tool names via `scripts/mcp_servers/rag_pipeline/` before finalizing.

## Documentation Impact
Both files updated; `05_04` becomes the canonical MDQ/RAG boundary reference.

## Out of Scope
Do not implement a search-only RAG tool in this issue — documentation only, reflecting current reality.

## AI Implementation Instruction
This is a confirmed factual error (tool names) — apply directly. Do not guess at the search-only invocation method; verify via source or mark as Needs Confirmation.

## Traceability
- Workflow phase: issue-creation
- Source: docs_review_mcp.md §1 (全体評価 item 4), §3 要約候補 item 3, §5 例4, §6A (RAGツール名の陳腐化)
- Generated at: 2026-08-02
