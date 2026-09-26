# Investigate NC ID gaps and dangling Related refs in governance_03 inventory

## Priority
Medium

## Summary
Two data-quality problems exist in `docs/00_governance/governance_03_issue-and-uncertainty-management.md`: (1) the Part 2 (Needs Confirmation) closing statement asserts a contiguous range "NC-021 through NC-039" while the active list skips five IDs, and (2) three Part 1 Known Issues cite Related items (CI-001, CI-003, CI-005, CI-007) that no longer have active entries. Both need investigation to determine whether they indicate stale summaries, removed items, or genuine completeness gaps.

## Background
The document's removal-placeholder policy states that once an item is removed its references must be updated or removed to avoid dangling citations. Part 2 ends with a prose summary of the active Needs Confirmation set. Part 1 Known Issues carry a `Related` field cross-referencing other known-issue entries.

## Problem
- Part 2 closing statement (near end of the Needs Confirmation section) reads "No other active items beyond NC-021 through NC-039," implying every ID from 021 to 039 is active. The active list omits NC-022, NC-026, NC-030, NC-032, and NC-038 — five gaps. The statement therefore describes a range that does not match the contents.
- Part 1 Known Issues reference absent items in their `Related` fields:
  - CI-009 cites CI-001.
  - CI-010 cites CI-003.
  - CI-014 cites CI-005 and CI-007.
  None of CI-001, CI-003, CI-005, CI-007 has an active entry, so these are dangling references under the removal-placeholder policy.

## Reason for Change
A closing summary that implies a contiguous range misrepresents which items are actually open, and dangling cross-references point readers at entries that no longer exist. Both undermine the inventory's reliability as the source of truth for open items.

## Implementation Intent
First investigate the root cause before editing:
- For the NC gaps: determine whether NC-022/026/030/032/038 were legitimately resolved or removed (making the summary stale) or are genuinely missing open items (a completeness gap). Check git history and any resolution records for those IDs.
- For the dangling Related refs: confirm CI-001/003/005/007 are intentionally gone (resolved/removed) rather than accidentally deleted.
Then apply the minimal correction consistent with the finding: fix the closing statement to describe the active set without asserting a false contiguous range, and update or clear the dangling Related fields. Do not fabricate resolutions or invent new items.

## Target Files or Areas
- `docs/00_governance/governance_03_issue-and-uncertainty-management.md` — Part 1 `Related` fields and Part 2 closing statement only

## Required Changes
- Determine and record the status of each of NC-022, NC-026, NC-030, NC-032, NC-038 (resolved/removed vs still-open).
- Rewrite the Part 2 closing statement so it accurately reflects the active Needs Confirmation IDs without claiming a contiguous 021–039 range.
- Update the `Related` fields of CI-009, CI-010, and CI-014 to drop the now-absent CI-001/003/005/007 references, replacing them with currently-active related items where a genuine relationship exists, or removing the field if none remains.

## Constraints
- Do not invent new Needs Confirmation items or assert resolutions that cannot be evidenced.
- Do not change any item's substantive content beyond the `Related` fields and the Part 2 closing statement.
- Preserve the ID-group ordering convention of both parts.

## Acceptance Criteria
- The Part 2 closing statement matches the actual active NC-ID set and does not assert a contiguous range that contains gaps.
- Every `Related` field reference in Part 1 points to an item present in the current inventory; no dangling CI-001/003/005/007 references remain.

## Testing Expectations
Not required (documentation-only). Optionally run `uv run python tools/check_docs_structure.py docs/00_governance/*.md` to confirm no new structural findings.

## Documentation Impact
This issue is itself the documentation update. No downstream artifact consumes these sections beyond human review.

## Out of Scope
- Adding or removing Needs Confirmation items based on this issue's own judgment (only correct the summary/references per the investigated facts).
- Changing the lifecycle/status vocabulary.
- Editing any part other than Part 1 `Related` fields and Part 2's closing statement.
- Editing any other governance document.

## Dependencies
- Companion to the Part 1 inventory-hygiene issue (gd002); both touch governance_03 but address different sections and can proceed independently.

## Unresolved Questions
- Are the five NC gaps expected (resolved/removed elsewhere) or a genuine completeness problem requiring new items? This is the central question the issue resolves before any edit.
- Were CI-001/003/005/007 removed deliberately, making the Related refs removable, or should they be restored?

## AI Implementation Instruction
Read Part 1 and Part 2 of `docs/00_governance/governance_03_issue-and-uncertainty-management.md`. Investigate the status of NC-022/026/030/032/038 and of CI-001/003/005/007 (git history, resolution records, or absence thereof). Then correct only the Part 2 closing statement and the `Related` fields of CI-009/010/014 to match reality; do not add or remove items, and do not touch other sections. Report the root-cause findings for the unresolved questions in your completion notes.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260926-174250
- **Related target files**: docs/00_governance/governance_03_issue-and-uncertainty-management.md
