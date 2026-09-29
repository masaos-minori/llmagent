## Goal
Remove the NC-021 entry from Part 2 "Active Items" and update the closing summary
line that enumerates remaining open NC items, once REQ-001's test has landed and
passed (REQ-003).

## Scope
- **In-Scope**: The NC-021 entry block in Part 2 "Active Items" (confirmed at
  lines 187-203) and the closing summary line enumerating open items (confirmed
  at line 255) of this target file.
- **Out-of-Scope**: NC-033, NC-035, NC-036 entries (unrelated items, left
  untouched); adding the integration test itself (covered by the sibling
  implementation procedure document for `tests/db/test_db_recovery.py`, seq 01
  of this Plan — this document's own move MUST NOT proceed until that sibling's
  test has landed and passed, per the Plan's own Risk mitigation and
  Implementation steps ordering).

## Assumptions
- The Plan's ordering (test lands and passes first, entry removed second) is
  binding for this cycle: do not remove this entry before confirming (by reading
  the sibling implementation procedure document's own Execution Status, or by
  re-running the test) that the new test added there passes (Plan Risks).
- The line numbers cited here (187-203, 255) reflect this file's current state
  as of this document's generation, after the sibling NC-027, NC-028, and
  NC-029 entries and an unrelated Part 1 Known Issues item were already removed
  earlier — re-confirm by content match (`#### NC-021` heading), not solely by
  these line numbers, since the Plan's own original citation (207-223, 383) has
  already been superseded once (see Plan's Implementation Target Files
  revalidation note).

## Design decisions
- Remove the entry outright rather than marking it "closed" in place, per the
  governance doc's own Part 2 "Status Values" rule: "An item is removed from the
  Active Items list ... once it is resolved ... it is not retained here with a
  closed-out status" (`skills/python-design` — follow the doc's own documented
  convention rather than introducing a new closed-item convention).

## Alternatives considered
- Remove the entry in the same cycle as the test addition without waiting for
  test confirmation — rejected: the Plan's own Risk mitigation explicitly orders
  documentation removal after test validation passes, to avoid a premature
  closure if the test is blocked or fails.
- Update only the summary line and leave the NC-021 entry block in place —
  rejected: would leave the inventory internally inconsistent (entry present,
  summary line silent about it).

## Implementation
### Target file
`docs/00_governance/governance_03_issue-and-uncertainty-management.md`

### Procedure
0. Before making any edit, confirm the sibling implementation procedure
   document for `tests/db/test_db_recovery.py` (seq 01 of this Plan) shows its
   test-addition and validation steps `Completed` — do not proceed on this
   document if that sibling is still `Pending` or `Blocked`.
1. Locate the `#### NC-021` heading by content match (do not assume the cited
   line number without confirming via search first, since this file's line
   numbers shift whenever a sibling NC entry is added or removed) and remove the
   entire entry block: the heading through its final bullet (`- **Blocking**:
   No`) and the one blank line immediately following it, ending just before the
   next entry's heading (`#### NC-033`).
2. After the deletion, locate the closing summary line by its literal text ("No
   other active Needs Confirmation items exist outside the set listed here: ...")
   rather than by its pre-deletion line number — deleting step 1's block shifts
   all subsequent line numbers in this same file. Remove `NC-021, ` (with its
   trailing comma and space) from the enumerated list on that line.

### Method
Direct text edit: one block deletion, one single-line text edit (remove one item
from a comma-separated enumeration) — no code, schema, or config change.

### Details
Block to remove (verbatim, lines 187-203 as confirmed by direct read at this
document's generation time — re-locate by the `#### NC-021` heading if this file
has changed further since):
```
#### NC-021

- **Source File**: `~~db_07_db_api_and_operations-recovery-and-reference~~ (deleted).md`
- **Section**: 9.3 Integrity-result model (target design)
- **Line Number**: ~39
- **Question**: ADR-008 (Decision Details #14, merged from former ADR-011) already settles that `INVALID_FORMAT` is kept as a defined-but-currently-unreachable classification, not removed as dead code — the remaining open question is narrower: should a test be added to cover this branch (e.g. via a fixture that triggers it), or is "verified unreachable by design" sufficient?
- **Evidence**: The structured six-state `DbCondition` classification is implemented (`scripts/db/recovery.py`), but `INVALID_FORMAT` is defined and dispatched-on without any code path that produces it — the branch is currently unreachable. ADR-008 Decision Details #14 already resolves the keep-vs-remove question in favor of keeping the enum value and dispatch branch.
- **Impact**: Leaving this unconfirmed risks an untested branch silently diverging from its intended (unreachable-by-design) behavior if the classification logic changes
- **Required Action**: Owner decision on whether test coverage for the unreachable `INVALID_FORMAT` branch is required, or whether "verified unreachable by design per ADR-008 #14" is an acceptable resolution
- **Status**: open
- **Assigned To**: Unassigned
- **Last Reviewed**: 2026-09-27
- **Priority**: Medium
- **Related NC**: None
- **Resolution Target**: Confirm whether the unreachable `INVALID_FORMAT` branch needs dedicated test coverage, given ADR-008 #14 already settles that it should be kept rather than removed.
- **Blocking**: No

```
(the trailing blank line above is removed too, so `#### NC-033` becomes the next
line after the preceding entry's own trailing blank line — do not leave a double
blank line or remove the separator before `#### NC-021`).

Summary line, current text (confirmed via direct read, line 255):
> No other active Needs Confirmation items exist outside the set listed here:
> NC-021, NC-033, NC-035, and NC-036.

New text:
> No other active Needs Confirmation items exist outside the set listed here:
> NC-033, NC-035, and NC-036.

Do not modify any other NC entry (NC-033, NC-035, NC-036) or any other section
of this file.

## Compatibility considerations
N/A: documentation-only inventory change, no public contract, API, schema, or
runtime behavior affected.

## Security considerations
N/A: no code, credentials, or data-handling change.

## Rollback considerations
Revert via `git revert`/`git checkout` of this file if needed; no data migration or
schema state to unwind. Re-adding a removed NC entry manually (rather than via
revert) is not recommended, since it would require re-confirming line numbers and
neighboring entries by direct read.

## Validation plan
Run the applicable documentation checker(s) per `routing.md` Tools → "When to run
which tool":
- `uv run python tools/check_docs_quality.py` (docs file edited)
- `uv run python tools/check_docs_structure.py docs/00_governance/governance_03_issue-and-uncertainty-management.md` (docs file edited)
- `uv run python tools/check_docs_content_policy.py` (docs file edited)
- `uv run python tools/check_needs_confirmation_inventory.py` (an NC marker/entry is
  removed by this change)

Expected outcome: all pass; NC-021 is absent from Part 2 "Active Items" and from the
closing summary line.

## Completion criteria
- Step 0's precondition (sibling test-addition document Completed) is satisfied
  before this document's own move to `implementations/done/`.
- The `#### NC-021` entry block is absent from Part 2 "Active Items".
- The closing summary line's enumerated list no longer contains "NC-021".
- No other NC entry or section is altered.
- All checkers listed in Validation plan pass.

## Out of scope
- Adding the new integration test itself — handled by the sibling
  implementation procedure document for `tests/db/test_db_recovery.py` (seq 01
  of this Plan).
- Any change to NC-033, NC-035, or NC-036 entries.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove the NC-021 entry block and update the summary line per Implementation > Procedure/Method/Details, gated on the sibling test document's completion | Completed | 20260929-151118 | 20260929-151118 | Step 0 precondition confirmed: sibling test-addition document Completed. NC-021 block (lines 187-203) removed; summary line updated; stale_detector clean |
| 2 | Run the applicable documentation checker(s) per Validation plan | Completed | 20260929-151119 | 20260929-151119 | Doc checkers run — NC-021 confirmed absent; structure check passes; pre-existing unrelated findings recorded, out of scope |

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
- **Requirement ID**: REQ-003
- **Source issue**: issues/20260927-211353_nc021_add-missing-integration-test-for-unreachable-invalid_format-branch.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260928-152012_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260929-143826
- **Related target files**: docs/00_governance/governance_03_issue-and-uncertainty-management.md