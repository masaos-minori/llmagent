# Deduplicate docs/01_overview-arch-03-features.md implemented-feature summary table against files-03-scripts

## Priority
Medium

## Summary
`docs/01_overview-arch-03-features.md` (~lines 28-42) contains an implemented-feature summary table whose content overlaps with the file-listing tables in `docs/01_overview-files-03-scripts-part*.md`, requiring double maintenance whenever a filename changes.

## Reason for Change
Per the Canonical Source Rule, file-level correspondence should have one authoritative home; maintaining the same file-to-feature mapping in two places doubles the update burden and risks the two silently diverging.

## Implementation Intent
Make `files-03-scripts` the canonical source for file-level correspondence; reduce this table to feature-name ↔ directory-name mapping only (no filenames).

## Target Files or Areas
`docs/01_overview-arch-03-features.md`

## Required Changes
- Reduce the implemented-feature summary table (~lines 28-42) to map feature name → directory name only (e.g. "Memory feature → `agent/memory/`").
- Remove filename-level detail from this table; add a pointer to the relevant `docs/01_overview-files-03-scripts-part*.md` file for file-level correspondence.

## Acceptance Criteria
The table no longer lists individual filenames; each row points to the appropriate `files-03-scripts-part*.md` file for detail.

## Testing Expectations
Not required (documentation-only).

## Documentation Impact
`docs/01_overview-arch-03-features.md` table simplified; `docs/01_overview-files-03-scripts-part*.md` files become the sole file-level reference (consistent with the separate stale-content fixes already tracked for those files).

## Out of Scope
Do not edit the `files-03-scripts-part*.md` files in this issue (tracked separately).

## AI Implementation Instruction
Verify each feature's correct target directory before rewriting the table row — do not assume the existing (potentially stale) directory mapping is still correct.

## Traceability
- Workflow phase: issue-creation
- Source: docs_review_overview_architecture.md §1 (コード説明に寄りすぎている領域), §3 要約候補 item 3
- Generated at: 2026-08-02
