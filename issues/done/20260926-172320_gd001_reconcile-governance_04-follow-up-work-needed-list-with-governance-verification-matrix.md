# Reconcile governance_04 Follow-up Work Needed list with Governance Verification Matrix

## Priority
High

## Summary
The "Follow-up Work Needed" list in `docs/00_governance/governance_04_documentation-checks.md` still lists GV-007 and GV-009 as pending implementation, while their rows in the same document's Governance Verification Matrix show `Status=Existing` and `Follow-up=None`. Reconcile the derived list with the authoritative matrix so the two never disagree.

## Background
The Governance Verification Matrix is the authoritative record of each rule's tooling status and follow-up state. The "Follow-up Work Needed" section directly below it is a derived summary that, per its own header, lists only rules marked "Missing" or "Partial" in the matrix. GV-009 (Needs Confirmation owner/deadline validation, implemented in `check_needs_confirmation_inventory.py`) was recently moved to `Status=Existing` / `Follow-up=None` in the matrix; the derived list was not updated. GV-007 (Duplicate Related Link prohibition, enforced by `check_docs_structure.py`) has long carried `Status=Existing` / `Follow-up=None` in the matrix while remaining in the derived list.

## Problem
Two rules are presented as open follow-up work in the derived list even though the authoritative matrix records them as complete:

- GV-007 — list item "Implement Duplicate Related Link prohibition check" versus matrix row `Status=Existing`, `Follow-up=None`.
- GV-009 — list item "Implement Needs Confirmation owner and deadline validation" versus matrix row `Status=Existing`, `Follow-up=None`.

Neither rule matches the header's stated inclusion criterion ("Missing" or "Partial"), so both entries violate the list's own contract.

## Reason for Change
A derived list that disagrees with its authoritative source misleads reviewers into treating completed rules as still-pending, which risks duplicate effort and erodes trust in the matrix as the single source of truth for rule state.

## Implementation Intent
Trim the "Follow-up Work Needed" list so that every listed rule genuinely has `Status=Missing` or `Status=Partial` in the matrix, and every such rule appears in the list. For GV-007 and GV-009, delete their entries (their matrix rows read `Follow-up=None`). Do not edit any matrix cell — the matrix is authoritative and is what the list is reconciled against. After deletion, renumber the ordered list so it stays contiguous.

## Target Files or Areas
- `docs/00_governance/governance_04_documentation-checks.md` — "Follow-up Work Needed" section only

## Required Changes
- Remove the GV-007 entry ("Implement Duplicate Related Link prohibition check"); matrix row `Status=Existing`, `Follow-up=None`.
- Remove the GV-009 entry ("Implement Needs Confirmation owner and deadline validation"); matrix row `Status=Existing`, `Follow-up=None`.
- Renumber the remaining ordered list so numbering is contiguous with no gaps.
- Scan the whole list for any other item whose matrix row is `Status=Existing` with `Follow-up=None`; such items also violate the header and must be removed or explicitly justified.

## Constraints
- Do not modify any Governance Verification Matrix cell or any section other than "Follow-up Work Needed".
- Keep the header sentence and the list's prose style verbatim apart from renumbering.
- Do not add new rules or change any rule's documented scope.

## Acceptance Criteria
- No entry in "Follow-up Work Needed" names a rule whose matrix row reads `Status=Existing` / `Follow-up=None`.
- Every rule with `Status=Missing` or `Status=Partial` in the matrix appears exactly once in the list.
- The ordered list numbering is contiguous with no gaps or duplicates.

## Testing Expectations
Not required (documentation-only). Optionally run `uv run python tools/check_docs_structure.py docs/00_governance/*.md` to confirm no new structural findings.

## Documentation Impact
This issue is itself the documentation update. No downstream artifact consumes the list beyond human review.

## Out of Scope
- Any change to the Governance Verification Matrix itself.
- Changing GV-007 or GV-009 tooling, scope, or status.
- Editing any other governance document.

## Dependencies
- N/A: none

## Unresolved Questions
- Were there additional non-"Missing"/"Partial" rules already listed under "Follow-up Work Needed" that were not caught during triage? Inspect the full list before finalizing.

## AI Implementation Instruction
Edit only the "Follow-up Work Needed" section of `docs/00_governance/governance_04_documentation-checks.md`. Delete the GV-007 and GV-009 bullets, renumber the list contiguously, and do not touch the matrix or any other section. If you find another listed rule whose matrix row is `Status=Existing` / `Follow-up=None`, remove it too and report it in your completion notes; otherwise leave every other entry untouched.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260926-172320
- **Related target files**: docs/00_governance/governance_04_documentation-checks.md
