# Fix confirmed tool-count errors in docs/04_mcp_01_system_overview.md Server Catalog

## Priority
High

## Summary
The Server Catalog table in `docs/04_mcp_01_system_overview.md` lists mdq-mcp as having 9 tools (actual, confirmed: 7) and web-search-mcp as having 1 tool (actual, confirmed: 2, after a `browser_fetch` integration that was never reflected in this table).

## Reason for Change
This is a confirmed factual error, not speculation. Anyone relying on this table for a design change or audit will find a mismatch and lose trust in the document's accuracy, and the update-history gap (the `browser_fetch` integration event was never recorded) suggests this table has no reliable update process.

## Implementation Intent
Correct both tool-count values and add a note recording the `browser_fetch` integration event, plus a source/update-history column so future changes are easier to track.

## Target Files or Areas
`docs/04_mcp_01_system_overview.md`

## Required Changes
- Correct mdq-mcp's tool count from 9 to 7.
- Correct web-search-mcp's tool count from 1 to 2.
- Add a note/column recording that web-search-mcp's count changed from 1 to 2 due to `browser_fetch` integration.

## Acceptance Criteria
Both tool counts match current implementation; the `browser_fetch` count-change event is recorded in the table or an adjacent update-history note.

## Testing Expectations
Not required (documentation-only). Manually re-verify current tool counts for mdq-mcp and web-search-mcp against `scripts/mcp_servers/mdq/` and `scripts/mcp_servers/web_search/` before finalizing.

## Documentation Impact
`docs/04_mcp_01_system_overview.md` Server Catalog table corrected.

## Out of Scope
Do not add a full update-history mechanism for the entire document in this issue — only the specific correction and its accompanying note.

## AI Implementation Instruction
Verify tool counts directly against current source (count actual tool-registering functions/decorators) before finalizing — do not merely apply the numbers stated in this review without independent re-verification, since more time may have passed since the review was written.

## Traceability
- Workflow phase: issue-creation
- Source: docs_review_mcp.md §1 (全体評価 item 2), §5 例2, §6A (mdq-mcp/web-search-mcpのツール数)
- Generated at: 2026-08-02
