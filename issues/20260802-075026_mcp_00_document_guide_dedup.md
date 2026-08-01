# Remove File Index / Related Documents duplication in docs/04_mcp_00_document-guide.md

## Priority
Low

## Summary
`docs/04_mcp_00_document-guide.md` lists the same file inventory in both a "File Index" section and a "Related Documents" section.

## Reason for Change
Self-duplication within the entry-point document itself creates the same update-drift risk seen elsewhere in this domain (e.g. port numbers, procedure duplication) — any file addition/removal must be applied twice to stay accurate.

## Implementation Intent
Make "File Index" the canonical, complete file listing; restrict "Related Documents" to only files explicitly referenced/discussed in this guide's own body text, avoiding the full-inventory duplication.

## Target Files or Areas
`docs/04_mcp_00_document-guide.md`

## Required Changes
- Keep "File Index" as the complete, canonical file listing.
- Reduce "Related Documents" to only the subset of files actually mentioned/linked within this guide's prose, removing the redundant full-inventory duplication.

## Acceptance Criteria
"File Index" remains the complete listing; "Related Documents" no longer duplicates the full inventory, containing only in-text-referenced files.

## Testing Expectations
Not required (documentation-only).

## Documentation Impact
`docs/04_mcp_00_document-guide.md` self-duplication removed.

## Out of Scope
Do not change the actual set of 45 `docs/04_mcp_*.md` files in this issue — documentation only.

## AI Implementation Instruction
Confirm which files are actually referenced in the guide's prose before trimming "Related Documents" — do not remove entries that are genuinely linked elsewhere in the body.

## Traceability
- Workflow phase: issue-creation
- Source: docs_review_mcp.md §2 削除候補 item 7 (00_document-guide.md)
- Generated at: 2026-08-02
