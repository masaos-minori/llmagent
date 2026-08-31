# tools/check_needs_confirmation_inventory.py references a nonexistent file and cannot run

## Priority
High

## Summary
`tools/check_needs_confirmation_inventory.py` hardcodes the pre-consolidation filename
`docs/00_governance_07_needs-confirmation-inventory.md`, which does not exist. Running the
tool fails immediately with `ERROR: 00_governance_07_needs-confirmation-inventory.md not
found under docs/.`, so the Needs Confirmation inventory consistency check documented in
`routing.md` and `docs/00_governance_04_documentation-checks.md` is not actually running.

## Background
Per `docs/00_governance_01_documentation-policy.md`'s (now-removed) Migration History
record, the governance documentation set was consolidated from 11 area-specific documents
into the current 4-document set. The Needs Confirmation Inventory, formerly its own
document (`00_governance_07_needs-confirmation-inventory.md`), was folded into Part 2 of
`docs/00_governance_03_issue-and-uncertainty-management.md`. This issue was discovered
during validation of an unrelated governance-policy update (Current-Specification-Only
Policy), while running the repository's documented documentation-check commands.

## Problem
`tools/check_needs_confirmation_inventory.py` defines `INVENTORY_DOC_NAME =
"00_governance_07_needs-confirmation-inventory.md"` (Evidence: Explicit in code) and looks
up that exact path under `docs/`. That file was never re-created after the consolidation, so
every invocation of the tool exits immediately with a not-found error before performing any
of its checks (verifying that "Needs confirmation" mentions across `docs/*.md` are
registered in the centralized inventory, and that resolved NC items do not leave stale
markers in source documents). `routing.md`'s Tools table lists this script as the check to
run "A 'Needs confirmation' marker was added, resolved, or removed anywhere under `docs/`" —
that gate has been silently non-functional since the consolidation.

## Reason for Change
An automated consistency check that always fails before it can check anything provides no
actual verification value and gives a false sense that NC-marker consistency is being
enforced. Any documentation change involving Needs Confirmation markers currently gets no
automated cross-check at all.

## Implementation Intent
Update the tool to read the Needs Confirmation inventory from its current location
(`docs/00_governance_03_issue-and-uncertainty-management.md`, "Part 2: Needs Confirmation
Inventory" section) instead of the removed standalone file. Since that file also contains
Part 1 (Known Issues) and other sections, the tool's parsing logic may need to scope itself
to the Part 2 section boundaries rather than assuming the entire file is the inventory. Keep
the tool's existing check semantics (stale resolved-marker detection, field-count
consistency) unchanged — only the source-location resolution needs to change.

## Target Files or Areas
- `tools/check_needs_confirmation_inventory.py` — primary target
- `docs/00_governance_03_issue-and-uncertainty-management.md` — read-only reference; the tool must parse this file's Part 2 section correctly

## Required Changes
- Update `INVENTORY_DOC_NAME` (or equivalent path resolution) to point at
  `docs/00_governance_03_issue-and-uncertainty-management.md`.
- If the tool parses the file as a flat NC-entry list, add logic to scope parsing to the
  "Part 2: Needs Confirmation Inventory" section (specifically its "Active Items"
  subsection) so Part 1's Known Issue entries are not misinterpreted as NC entries.
- Verify the tool's stale-resolved-marker check and any other existing logic still functions
  correctly against the current file's structure and the current NC status vocabulary (open,
  investigating, deferred — see `docs/00_governance_03_issue-and-uncertainty-management.md`).

## Constraints
- Do not change the tool's check semantics (what counts as a violation) — only fix the
  source-file resolution.
- Do not modify `docs/00_governance_03_issue-and-uncertainty-management.md` itself as part of
  this fix; the document's current structure is the target the tool must parse correctly.
- Do not reintroduce a standalone Needs Confirmation Inventory document — the consolidation
  into the 4-document governance set is current, intended structure.

## Acceptance Criteria
- `uv run python tools/check_needs_confirmation_inventory.py` runs to completion against the
  current `docs/` tree without a not-found error.
- The tool correctly identifies the three currently active NC entries (NC-019, NC-020,
  NC-021) in `docs/00_governance_03_issue-and-uncertainty-management.md`.
- The tool's existing checks (stale resolved-marker detection, "Needs confirmation" mentions
  registered in the inventory) produce correct results against a deliberately introduced test
  case (e.g., an unregistered "Needs confirmation" mention added temporarily during testing,
  then removed).

## Testing Expectations
- Manually verify the tool runs cleanly against the current repository state.
- Add or confirm a test exercising the corrected path resolution, if `tools/` scripts have
  existing test coverage patterns to follow (Evidence: Needs confirmation — check whether
  `tools/` scripts are covered by `tests/tools/`).
- Re-run `routing.md`'s documented check after this fix whenever a future change adds,
  resolves, or removes a "Needs confirmation" marker, to confirm the gate is now functional.

## Documentation Impact
None expected — this is a tool bug fix, not a policy or structure change. If the fix reveals
that `routing.md`'s tool description needs adjustment (e.g., to describe the section-scoped
parsing), update it in the same change.

## Out of Scope
- Changing the Needs Confirmation Inventory's structure, fields, or status values.
- Migrating the inventory back to a standalone document.
- Fixing other unrelated tool/documentation mismatches (tracked separately).

## Dependencies
N/A: none

## Unresolved Questions
- Whether `tests/tools/` has existing coverage for this script that should be extended, or
  whether this script has no current test coverage — needs confirmation before finalizing the
  Testing Expectations.

## AI Implementation Instruction
- Do not change what the tool considers a violation — only fix where it reads the inventory
  from.
- Read `docs/00_governance_03_issue-and-uncertainty-management.md`'s actual current structure
  before writing the parsing fix; do not assume the old standalone-document format still
  applies.
- Verify the fix by actually running the tool against the current repository, not just by
  code review.
- Do not touch other tools or governance documents as part of this fix.
