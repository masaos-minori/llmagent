# Remove resolved Known Issue entries from active Part 1 inventory

## Priority
High

## Summary
Remove RAG-006 and REQ-003 from Part 1 (Known Issues) of `docs/00_governance_03_issue-and-uncertainty-management.md`. Both entries carry `Status: resolved` but remain in the Active Items section, violating the Current-Specification-Only Policy.

## Background
The Known Issues consolidation on 2026-09-03 moved area-specific inconsistency files into `docs/00_governance_03_issue-and-uncertainty-management.md` Part 1. Since then, RAG-006 was resolved (retention policy documented via `plans/20260924-080000_plan.md`) and REQ-003 was resolved (coverage mapping completed via `plans/20260924-070936_plan.md`). Both entries record `Resolved At` dates and `Resolution Evidence` paths.

## Problem
Part 1's lifecycle rule (line 29-30) states: "An item is removed from this active inventory once it is resolved or no longer applies to the current system; it is not retained here with a closed-out status." Despite this, RAG-006 and REQ-003 remain listed under "### Active Items" with `Status: resolved`. This creates false positives for automated tools and human reviewers scanning the active inventory.

## Reason for Change
The Current-Specification-Only Policy requires the active documentation set to contain only items applicable to the current system. Retaining resolved entries violates this principle and undermines trust in the active inventory as a source of truth.

## Implementation Intent
Edit `docs/00_governance_03_issue-and-uncertainty-management.md` Part 1 Active Items section. Locate the `#### RAG-006` heading and the `#### REQ-003` heading. Delete the entire entry block for each (from the heading through to the next `####` heading or end of section). Preserve all other entries, their ordering, and the surrounding text including the Consolidation Note and the two preserved non-Known-Issue notes.

## Target Files or Areas
- `docs/00_governance_03_issue-and-uncertainty-management.md` (Part 1 Active Items)

## Required Changes
- Delete the `#### RAG-006` entry block entirely (lines ~108-130)
- Delete the `#### REQ-003` entry block entirely (lines ~447-467)
- Verify no trailing blank-line artifacts remain between remaining entries
- Verify the Active Items ordering convention (by ID-prefix groups) is preserved after deletion

## Constraints
- Do not modify any entries other than RAG-006 and REQ-003
- Do not alter Part 2 (Needs Confirmation), Part 3 (Canonical Source Conflict), or Part 4 (Configuration Drift) sections
- Preserve the Consolidation Note (lines 68-101) and the two preserved historical notes exactly as-is
- Preserve the paragraph between EVENTBUS-007 and CI-008 (ADR-010 Decision #9 note) which is not a resolved entry

## Acceptance Criteria
- [ ] No `#### RAG-006` heading remains in the Active Items section
- [ ] No `#### REQ-003` heading remains in the Active Items section
- [ ] All other Active Items entries (DESIGN-2, EVENTBUS-005 through EVENTBUS-007, CI-008 through CI-018) remain intact and unchanged
- [ ] The Active Items ordering convention (RAG-* → DESIGN-* → EVENTBUS-* → SHARED-* → CI-*) is preserved
- [ ] No other file modified

## Testing Expectations
Manual review of the edited file against the pre-edit version. Run `uv run python tools/check_docs_structure.py docs/00_governance_03_issue-and-uncertainty-management.md` to verify structural integrity (front matter, headings, link reachability).

## Documentation Impact
This is a governance document cleanup. No new documentation is created. The change aligns the document with its own stated Current-Specification-Only Policy.

## Out of Scope
- Modifying any Needs Confirmation (Part 2) entries
- Modifying Part 3 (Canonical Source Conflict) or Part 4 (Configuration Drift) templates
- Adding automated checks for resolved-item detection (future enhancement opportunity)
- Modifying area-specific documentation files

## Dependencies
- None

## Unresolved Questions
N/A: none

## AI Implementation Instruction
Edit only `docs/00_governance_03_issue-and-uncertainty-management.md`. Delete the complete entry blocks starting at `#### RAG-006` and `#### REQ-003` headings respectively, up to (but not including) the next `####` heading. Do not touch any other content. After editing, run `uv run python tools/check_docs_structure.py docs/00_governance_03_issue-and-uncertainty-management.md` to confirm no structural issues.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260925-120032
- **Related target files**: docs/00_governance_03_issue-and-uncertainty-management.md
