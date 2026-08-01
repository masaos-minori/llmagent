# Remove docs/00_index.md body sections that duplicate its own frontmatter

## Priority
Low

## Summary
`docs/00_index.md`'s body contains a "Related Documents" list (~lines 151-159) that exactly duplicates the frontmatter `related` field (~lines 10-17), and a "Keywords" list (~lines 161-168) that exactly duplicates the frontmatter `tags` field (~lines 4-9).

## Reason for Change
Maintaining the same information in both frontmatter and body creates a dual-maintenance burden and risk of the two silently diverging over time.

## Implementation Intent
Keep frontmatter as the single source of truth for these two lists; remove the redundant body sections.

## Target Files or Areas
`docs/00_index.md`

## Required Changes
- Confirm the body "Related Documents" list matches frontmatter `related` exactly, and remove the body section.
- Confirm the body "Keywords" list matches frontmatter `tags` exactly, and remove the body section.

## Acceptance Criteria
`docs/00_index.md` no longer contains a body-level Related Documents or Keywords section; frontmatter `related`/`tags` remain the sole record of this information.

## Testing Expectations
Not required (documentation-only).

## Documentation Impact
`docs/00_index.md` body shortened; no information lost (frontmatter retains it).

## Out of Scope
Do not change frontmatter field values or format in this issue.

## AI Implementation Instruction
Diff the body list against frontmatter before deleting; if they differ in any entry, stop and report the discrepancy instead of deleting silently.

## Traceability
- Workflow phase: issue-creation
- Source: docs_review_governance.md §1 (重複している情報の傾向 item 4), §2 削除候補 items 4-5
- Generated at: 2026-08-02
