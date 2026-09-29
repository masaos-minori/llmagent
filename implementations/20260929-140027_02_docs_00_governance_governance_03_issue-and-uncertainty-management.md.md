## Goal
Remove the NC-029 entry from Part 2 "Active Items" and update the closing summary
line that enumerates remaining open NC items (REQ-002).

## Scope
- **In-Scope**: The NC-029 entry block in Part 2 "Active Items" (confirmed at lines
  204-220) and the closing summary line enumerating open items (confirmed at line
  289) of this target file.
- **Out-of-Scope**: NC-021, NC-027, NC-028, NC-033, NC-034, NC-035, NC-036 entries
  (unrelated items, left untouched); the inline marker sentence in
  `docs/21_rag/rag_02_09_ingestion_pipeline-shared-utilities.md` (covered by the
  sibling implementation procedure document for that file).

## Assumptions
- The Plan's "no rationale found, accepted as-is" resolution is owner-confirmed
  and authoritative for this closure (Plan Assumptions).
- Removing this entry does not affect any other NC entry's numbering or
  cross-references — NC IDs are stable identifiers, not renumbered on removal
  (consistent with the governance doc's own removal-on-resolution rule, Part 2
  "Status Values").
- The line numbers cited here (204-220, 289) reflect this file's current state as
  of this document's generation, after the sibling NC-027 and NC-028 entries
  were already removed earlier — re-confirm by content match (`#### NC-029`
  heading), not solely by these line numbers, since the Plan's own original
  citation (298-313, 383) has already been superseded once (see Plan's
  Implementation Target Files revalidation note).

## Design decisions
- Remove the entry outright rather than marking it "closed" in place, per the
  governance doc's own Part 2 "Status Values" rule: "An item is removed from the
  Active Items list ... once it is resolved ... it is not retained here with a
  closed-out status" (`skills/python-design` — follow the doc's own documented
  convention rather than introducing a new closed-item convention).

## Alternatives considered
- Mark NC-029 "Status: closed" in place instead of deleting the entry — rejected:
  contradicts the governance doc's own explicit removal-on-resolution rule cited
  above.
- Correct only the entry's stale "Required Action" premise (external library)
  and leave the entry open — rejected: the Plan's own resolution is closure, not
  a partial correction; the premise finding is supporting evidence for removal,
  not an alternative outcome.
- Update only the summary line and leave the NC-029 entry block in place —
  rejected: would leave the inventory internally inconsistent (entry present,
  summary line silent about it).

## Implementation
### Target file
`docs/00_governance/governance_03_issue-and-uncertainty-management.md`

### Procedure
1. Locate the `#### NC-029` heading by content match (do not assume the cited
   line number without confirming via search first, since this file's line
   numbers shift whenever a sibling NC entry is added or removed) and remove the
   entire entry block: the heading through its final bullet (`- **Blocking**:
   No`) and the one blank line immediately following it, ending just before the
   next entry's heading (`#### NC-033`).
2. After the deletion, locate the closing summary line by its literal text ("No
   other active Needs Confirmation items exist outside the set listed here: ...")
   rather than by its pre-deletion line number — deleting step 1's block shifts
   all subsequent line numbers in this same file. Remove `NC-029, ` (with its
   trailing comma and space) from the enumerated list on that line.

### Method
Direct text edit: one block deletion, one single-line text edit (remove one item
from a comma-separated enumeration) — no code, schema, or config change.

### Details
Block to remove (verbatim, lines 204-220 as confirmed by direct read at this
document's generation time — re-locate by the `#### NC-029` heading if this file
has changed further since):
```
#### NC-029

- **Source File**: `rag_02_09_ingestion_pipeline-shared-utilities.md`
- **Section**: Constants
- **Line Number**: ~47
- **Question**: What is the rationale for `MIN_TEXT_LENGTH_FOR_DETECTION = 100` (the minimum text length required for language detection)?
- **Evidence**: The document already carries an inline marker: "the rationale for `MIN_TEXT_LENGTH_FOR_DETECTION = 100` is unconfirmed (Needs Confirmation)"; the constant is defined in `scripts/rag/utils.py` with no rationale comment
- **Impact**: Changing this threshold without knowing its rationale risks unintended effects on language-detection accuracy for short texts
- **Required Action**: Owner confirmation, or validate against the language-detection library's own empirical guidance
- **Status**: open
- **Assigned To**: Unassigned
- **Last Reviewed**: 2026-09-03
- **Priority**: Low
- **Related NC**: None
- **Resolution Target**: Next language-detection logic review
- **Blocking**: No

```
(the trailing blank line above is removed too, so `#### NC-033` becomes the next
line after the preceding entry's own trailing blank line — do not leave a double
blank line or remove the separator before `#### NC-029`).

Summary line, current text (confirmed via direct read, line 289):
> No other active Needs Confirmation items exist outside the set listed here:
> NC-021, NC-029, NC-033, NC-034, NC-035, and NC-036.

New text:
> No other active Needs Confirmation items exist outside the set listed here:
> NC-021, NC-033, NC-034, NC-035, and NC-036.

Do not modify any other NC entry (NC-021, NC-033, NC-034, NC-035, NC-036) or any
other section of this file.

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
  removed by this change — confirm the inline marker in the sibling target file is
  also updated in the same cycle, not left inconsistent)

Expected outcome: all pass; NC-029 is absent from Part 2 "Active Items" and from the
closing summary line.

## Completion criteria
- The `#### NC-029` entry block is absent from Part 2 "Active Items".
- The closing summary line's enumerated list no longer contains "NC-029".
- No other NC entry or section is altered.
- All checkers listed in Validation plan pass.

## Out of scope
- Replacing the inline marker sentence in
  `docs/21_rag/rag_02_09_ingestion_pipeline-shared-utilities.md` — handled by the
  sibling implementation procedure document for that file (seq 01 of this Plan).
- Any change to NC-021, NC-027, NC-028, NC-033, NC-034, NC-035, or NC-036 entries.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove the NC-029 entry block and update the summary line per Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Run the applicable documentation checker(s) per Validation plan | Pending | — | — | |

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
- **Requirement ID**: REQ-002
- **Source issue**: issues/20260927-211401_nc029_confirm-rationale-for-min_text_length_for_detection100.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260928-162759_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260929-140027
- **Related target files**: docs/00_governance/governance_03_issue-and-uncertainty-management.md
