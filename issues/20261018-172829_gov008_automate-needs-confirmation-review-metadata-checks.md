# Automate Needs Confirmation review-metadata consistency checks

## Priority
Medium

## Summary
`check_needs_confirmation_inventory.py` (governance rule GV-008) currently validates only the `Assigned To` and `Resolution Target` fields of Needs Confirmation items. Extend it to also validate `Last Reviewed`, `Priority`, and Status/Blocking consistency, then mark GV-008 fully automated (status `Existing`).

## Background
`docs/00_governance/governance_04_documentation-checks.md` maps rule GV-008 ("Needs Confirmation assignment, review metadata, priority, and resolution target — `Assigned To`, `Last Reviewed`, `Priority`, and Status/Blocking consistency") to the enforcement tool `check_needs_confirmation_inventory.py`. The matrix records its status as `Partial` because the tool checks only two of the four field-groups (`Assigned To`, `Resolution Target`); the other two (`Last Reviewed`, `Priority`, and Status/Blocking consistency) are manual review.

## Problem
The three unchecked field-groups can drift without detection: a Needs Confirmation item may carry a stale or missing `Last Reviewed`, an invalid or status-inconsistent `Priority`, or a `Blocked` status that does not reference its blocking item. Such drift is invisible until a manual review runs.

## Reason for Change
Manual review is not enforced at the PR or periodic gate, so metadata drift goes unnoticed. The governance matrix already flags this as a `Partial` control; automating the remaining checks closes the documented gap without changing any Needs Confirmation data semantics.

## Implementation Intent
Extend `check_needs_confirmation_inventory.py` with three additional checks while preserving the existing `Assigned To` / `Resolution Target` checks and the tool's CLI and exit-status contract:
- `Last Reviewed`: present and within the recency policy defined in `governance_03`.
- `Priority`: one of the allowed values and consistent with the item's Status.
- Status/Blocking consistency: a `Blocked` item references its blocking item; a non-blocked item has no dangling blocking reference.

## Target Files or Areas
`tools/check_needs_confirmation_inventory.py`; `docs/00_governance/governance_04_documentation-checks.md` (GV-008 row `Partial` → `Existing`); `docs/00_governance/governance_03_issue-and-uncertainty-management.md` (read-only, for the authoritative `Priority` enum and `Last Reviewed` recency policy).

## Required Changes
- Add a `Last Reviewed` presence/recency check.
- Add a `Priority` validity-and-status-consistency check.
- Add a Status/Blocking consistency check.
- Keep the existing `Assigned To` and `Resolution Target` checks unchanged.
- Update the GV-008 matrix row to `Existing` and clear its Follow-up note.

## Constraints
- Do not change the Needs Confirmation data schema, the issue template field semantics, or the tool's exit-code contract (exit 1 on violation).
- Must remain backward compatible with existing `issues/done/` items.
- Field policies (`Priority` enum, `Last Reviewed` recency) come from `governance_03`; do not invent values.

## Acceptance Criteria
- The tool reports violations for stale/missing `Last Reviewed`, invalid `Priority`, and inconsistent Status/Blocking.
- Existing `Assigned To` / `Resolution Target` checks still pass on the compliant corpus.
- Running the tool on the full `issues/` corpus reports zero false positives.
- GV-008 matrix row is marked `Existing`.

## Testing Expectations
Unit tests for each new check with compliant and violating fixtures; a regression test asserting the existing checks are unchanged; run the tool on the full `issues/` corpus.

## Documentation Impact
`governance_04_documentation-checks.md`: GV-008 row status `Partial` → `Existing`, Follow-up column cleared.

## Out of Scope
Changing the Needs Confirmation field definitions or the issue template. Adding checks for other GV rows.

## Dependencies
Authoritative `Priority` enum and `Last Reviewed` recency policy in `governance_03_issue-and-uncertainty-management.md`.

## Unresolved Questions
Exact `Last Reviewed` recency threshold (e.g., 90 days) and the full allowed `Priority` set — confirm from `governance_03` before implementing.

## AI Implementation Instruction
Read `governance_03` for the authoritative `Priority` enum and `Last Reviewed` recency policy before coding; do not invent values. Preserve the tool's CLI and exit-code contract. Add unit tests with both compliant and violating fixtures. Do not modify the issue template or the Needs Confirmation schema.

## Traceability
- Workflow phase: issue-creator
- Source issue: N/A: this document is the issue
- Source requirement: N/A: no standalone requirement document is generated
- Source plan: N/A: not filed from a Plan
- Source implementation procedure: N/A: not filed from an implementation procedure
- Generated at: 2026-10-18
- Related target files: `tools/check_needs_confirmation_inventory.py`, `docs/00_governance/governance_04_documentation-checks.md`
