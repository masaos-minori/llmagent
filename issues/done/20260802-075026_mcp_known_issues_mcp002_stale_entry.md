# Update stale MCP-002 Known Issues entry in docs/04_mcp_90

## Priority
Medium

## Summary
`docs/04_mcp_90_inconsistencies_and_known_issues.md`'s MCP-002 entry states enabled/disabled_reason tracking is "unimplemented in most servers," but confirmed source inspection shows it is now implemented in git/file-read/file-write/file-delete (4 servers) — only web-search-mcp remains unimplemented.

## Reason for Change
Leaving a resolved-in-large-part issue marked as broadly unresolved risks readers spending effort re-investigating or re-implementing something already done, and undermines trust in the Known Issues document as a source of current status.

## Implementation Intent
Update the MCP-002 entry's status and description to reflect the actual current state (only web-search-mcp unimplemented), and fill in the First Found field per the document's own template if currently blank.

## Target Files or Areas
`docs/04_mcp_90_inconsistencies_and_known_issues.md`

## Required Changes
- Change MCP-002's description from "unimplemented in most servers" to "implemented in git-mcp/file-read-mcp/file-write-mcp/file-delete-mcp; only web-search-mcp remains unimplemented."
- Fill in the "First Found" field (or equivalent lifecycle metadata per `docs/00_governance_04`'s template) if currently blank.
- Consider whether the entry's overall status (open/investigating/fixed/deferred) should change given the near-complete implementation.

## Acceptance Criteria
MCP-002's description accurately reflects current implementation state; lifecycle metadata fields are filled per the standard Known Issues template.

## Testing Expectations
Not required (documentation-only). Manually re-verify enabled/disabled_reason implementation status for all 5 relevant servers before finalizing.

## Documentation Impact
`docs/04_mcp_90_inconsistencies_and_known_issues.md` MCP-002 entry updated.

## Out of Scope
Do not implement enabled/disabled_reason tracking for web-search-mcp in this issue — documentation only, reflecting current reality.

## AI Implementation Instruction
Re-verify the current implementation status for all 5 servers directly via source before updating — do not merely apply this review's stated finding without independent re-confirmation, since more time may have passed.

## Traceability
- Workflow phase: issue-creation
- Source: docs_review_mcp.md §1 (全体評価 item 13), §6A (MCP-002エントリの陳腐化)
- Generated at: 2026-08-02
