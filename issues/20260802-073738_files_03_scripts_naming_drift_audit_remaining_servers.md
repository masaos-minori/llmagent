# Audit remaining, not-yet-reviewed MCP server subdirectories for the same filename-prefix documentation drift

## Priority
Medium

## Summary
The naming-drift pattern confirmed in web_search, github, shell, rag_pipeline, cicd, mdq, and git MCP server documentation (generic filenames documented vs. service-prefixed actual files) has not been checked against other `scripts/mcp_servers/` subdirectories not covered by this review (e.g. `file/`).

## Reason for Change
Given the pattern was confirmed in 7 of the reviewed subdirectories, it is plausible the same drift exists elsewhere in `docs/01_overview-files-03-scripts-part*.md` files not yet cross-checked, and should be verified rather than assumed absent.

## Implementation Intent
Systematically diff each remaining documented MCP server subdirectory's file listing against `scripts/mcp_servers/<name>/`'s actual contents, and file follow-up fixes for any additional drift found.

## Target Files or Areas
`docs/01_overview-files-03-scripts-part*.md` (any subdirectory not covered by the web_search/github/shell/rag_pipeline/cicd/mdq/git fixes), cross-referenced against `scripts/mcp_servers/*/`

## Required Changes
- Enumerate all subdirectories under `scripts/mcp_servers/`.
- For each one not already covered by the naming-drift fix issues, diff its actual file list against what is documented.
- File a follow-up issue (or extend an existing one) for each additional drift found.

## Acceptance Criteria
Every subdirectory under `scripts/mcp_servers/` has been checked against its corresponding documentation; any newly found drift is tracked.

## Testing Expectations
Not required (documentation-only); the investigation itself is a manual `ls`/`diff` comparison, not a test run.

## Documentation Impact
No direct edits in this issue — output is a list of confirmed-accurate or confirmed-drifted subdirectories, feeding follow-up fix issues.

## Out of Scope
Do not fix any drift found during this audit directly in this issue — file it as a separate, scoped fix issue instead.

## AI Implementation Instruction
This is an investigation task, not an edit task. Report findings per subdirectory (accurate / drifted, with specifics) rather than silently fixing anything found.

## Traceability
- Workflow phase: issue-creation
- Source: docs_review_overview_architecture.md §6A (files-03-scripts-part4/part5 — 他のmcp_servers配下の横断確認)
- Generated at: 2026-08-02
