# Remove firejail installation instructions from docs/04_mcp_06_16

## Priority
Low

## Summary
`docs/04_mcp_06_16` contains OS-package installation commands for firejail — operational runbook-level content, not design documentation.

## Reason for Change
Installation commands are out of scope for a design document and belong in an operations runbook if one exists; keeping them here mixes design intent with setup procedure.

## Implementation Intent
Remove the installation instructions from this design document. If an operational setup runbook already exists, move the content there; otherwise, simply remove it (design docs should not become the de facto runbook).

## Target Files or Areas
`docs/04_mcp_06_16`

## Required Changes
- Check whether an operations/setup runbook already exists for MCP server prerequisites.
- If one exists, move the firejail installation instructions there and leave a pointer in `06_16`.
- If none exists, remove the installation instructions entirely, keeping only the fail-open/closed check-item content that this review confirms is important and code-verified.

## Acceptance Criteria
`06_16` no longer contains OS package installation commands as inline design-document content; the important fail-open/closed check items remain.

## Testing Expectations
Not required (documentation-only).

## Documentation Impact
`06_16` shortened; installation content either relocated or removed.

## Out of Scope
Do not create a new operations runbook in this issue if one does not exist — only remove the content (or relocate if a target already exists).

## AI Implementation Instruction
Search for an existing ops/runbook document before deciding whether to relocate or simply delete the installation content.

## Traceability
- Workflow phase: issue-creation
- Source: docs_review_mcp.md §1 (コード説明に寄りすぎている領域), §2 削除候補 item 6
- Generated at: 2026-08-02
