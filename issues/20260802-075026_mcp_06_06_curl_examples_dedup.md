# Remove repeated curl command example notes in docs/04_mcp_06_06

## Priority
Low

## Summary
`docs/04_mcp_06_06`'s per-server curl command / JSON response examples repeat the same explanatory note across all 5 examples verbatim.

## Reason for Change
The repeated note is a maintenance burden that increases with every server added, and carries no additional design information beyond the first instance.

## Implementation Intent
State the common note once, then list each server's endpoint-specific detail in a compact table rather than 5 near-identical full examples.

## Target Files or Areas
`docs/04_mcp_06_06`

## Required Changes
- Consolidate the repeated explanatory note into a single statement at the top of the section.
- Replace the 5 full curl+JSON examples with a table listing each server's specific endpoint name/path, keeping one full worked example if a concrete illustration is still useful.

## Acceptance Criteria
The common explanatory note appears once; server-specific endpoint detail is presented as a compact table rather than 5 repeated full examples.

## Testing Expectations
Not required (documentation-only).

## Documentation Impact
`docs/04_mcp_06_06` shortened; no endpoint information lost.

## Out of Scope
Do not change actual server endpoints in this issue — documentation only.

## AI Implementation Instruction
Verify each server's endpoint name/path against actual source before compiling the summary table, in case any have drifted since this review was written.

## Traceability
- Workflow phase: issue-creation
- Source: docs_review_mcp.md §1 (コード説明に寄りすぎている領域), §2 削除候補 item 5
- Generated at: 2026-08-02
