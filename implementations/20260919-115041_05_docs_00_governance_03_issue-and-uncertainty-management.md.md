## Goal
Remove the `NC-032` entry from
`docs/00_governance_03_issue-and-uncertainty-management.md`'s active inventory,
now that `additionalProperties` has been explicitly decided (`REQ-006`).

## Scope
In scope: removing the `NC-032` entry only. Out of scope: any other Needs
Confirmation entry in this file.

## Assumptions
- `NC-032` entry unchanged since the Plan was written — re-confirmed at
  `docs/00_governance_03_issue-and-uncertainty-management.md:722-748` (the full
  entry spans through its `Priority` field at line 748, one line further than
  the Plan's own `722-744` citation — a minor citation-range correction, not a
  content discrepancy).
- Depends on seq 01 (`schemas/doc_front_matter.json`) actually landing the
  `additionalProperties` decision first — this row should not remove `NC-032`
  until that decision is actually reflected in the schema file, not merely
  planned.

## Design decisions
Remove the entire `#### NC-032` entry block (heading through its last field),
per this document's own stated removal policy for resolved Needs Confirmation
items — do not leave a placeholder or a "resolved" annotation in place; the
project's convention (confirmed by the absence of any "resolved" example
elsewhere in this file, and the `routing.md` tool-table's own instruction for
`check_needs_confirmation_inventory.py`: "remove the inline marker from the
source doc once an entry is marked resolved") is full removal, not
strikethrough or archival within the same file.

## Alternatives considered
Marking `NC-032`'s `Status` field as `resolved` in place (rather than deleting
the entry) was considered, but rejected — `routing.md`'s own tool-usage guidance
for `check_needs_confirmation_inventory.py` explicitly instructs removing the
inline marker once resolved, which this project already treats as the standard
resolution mechanism.

## Implementation
### Target file
docs/00_governance_03_issue-and-uncertainty-management.md

### Procedure
1. Delete the entire `#### NC-032` section (heading + all its fields, the full
   range confirmed in Assumptions above) from the Needs Confirmation inventory.
2. Run `uv run python tools/check_needs_confirmation_inventory.py` after the
   removal (per `routing.md`'s "When to run which tool" — required whenever an
   NC marker is added, resolved, or removed) to confirm the inventory is
   internally consistent after the removal.

### Method
Direct text edit (`Edit` tool) — delete one contiguous block; then a tool run
for verification.

### Details
- Confirm no other section of this file references `NC-032` by ID before
  deleting (a dangling cross-reference elsewhere would need its own fix, which
  would be an additional-target-file discovery if found in a different file) —
  `rg -n "NC-032" docs/` should show only this one entry before the edit.

## Compatibility considerations
Removes exactly one self-contained entry — no other NC entry's numbering or
content is affected (NC entries are identified by their own fixed ID, not
positional order).

## Security considerations
N/A: documentation-only.

## Rollback considerations
`git checkout -- docs/00_governance_03_issue-and-uncertainty-management.md`
reverts this row independently. Note: reverting this row alone (while seq 01's
schema decision has landed) would leave `NC-032` incorrectly listed as still
"open" for an already-decided question — pair this row's rollback with
reconsidering seq 01's decision if either is reverted.

## Validation plan
- `rg -n "NC-032" docs/` — confirm zero remaining references after the edit.
- `uv run python tools/check_needs_confirmation_inventory.py` — confirm no new
  findings (e.g. a dangling registration elsewhere expecting `NC-032` to still
  exist).
- `uv run python tools/check_docs_quality.py` / `check_docs_structure.py` — no
  new findings.

## Completion criteria
- `NC-032` no longer appears anywhere in
  `docs/00_governance_03_issue-and-uncertainty-management.md`'s active
  inventory.
- `tools/check_needs_confirmation_inventory.py` reports no new findings.

## Out of scope
Any other Needs Confirmation entry in this file.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Depends on seq 01's additionalProperties decision actually landing first |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: documentation-only |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | `tools/check_needs_confirmation_inventory.py` + `tools/check_docs_quality.py`/`check_docs_structure.py` |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: this document's own Target file IS the documentation being updated |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-006 (remove NC-032 from the active inventory)
- **Source issue**: issues/done/20260918-130249_docsmeta01_add-class-front-matter-field.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260919-105328_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260919-115041
- **Related target files**: docs/00_governance_03_issue-and-uncertainty-management.md
