## Goal
Remove the obsolete NC-033 entry from Part 2 "Active Items" and update the
closing summary line that enumerates remaining open NC items (REQ-001).

## Scope
- **In-Scope**: The NC-033 entry block in Part 2 "Active Items" (confirmed at
  lines 187-203) and the closing summary line enumerating open items (confirmed
  at line 238) of this target file.
- **Out-of-Scope**: NC-035, NC-036 entries (unrelated items, left untouched);
  fixing the stale `LanguageCode` reference in
  `docs/21_rag/rag_05_5-constraints-reference.md` (covered by the sibling
  implementation procedure document for that file); re-investigating whether
  `LanguageCode`'s prior removal was correct (already a settled, separate
  change).

## Assumptions
- `LanguageCode` and its sole former user (the now-deleted CrawlTarget class) are confirmed absent from
  current `scripts/rag/` source (`rg` zero matches) — this entry documents an
  obsolete question, not an open one, per Plan Background.
- The line numbers cited here (187-203, 238) reflect this file's current state
  as of this document's generation, after the sibling NC-021, NC-027, NC-028,
  and NC-029 entries and an unrelated Part 1 Known Issues item were already
  removed earlier — re-confirm by content match (`#### NC-033` heading), not
  solely by these line numbers, since the Plan's own original citation
  (315-330, 383) has already been superseded once (see Plan's Implementation
  Target Files revalidation note).

## Design decisions
- Remove the entry outright rather than marking it "closed" in place, per the
  governance doc's own Part 2 "Status Values" rule and per `rules/coding.md`'s
  "Obsolete and removable" Documentation notes classification (an
  already-verified-gone discrepancy is deleted, not retained as if still open)
  (`skills/python-design` — follow the doc's own documented convention).
- Unlike the sibling NC-027/NC-028/NC-029 closures, no new closure phrasing is
  added — this is a removal-of-obsolete-content task, not a "no rationale"
  resolution (Plan Design).

## Alternatives considered
- Mark NC-033 "Status: closed" in place instead of deleting the entry —
  rejected: contradicts the governance doc's own explicit removal-on-resolution
  rule, and `rules/coding.md`'s "Obsolete and removable" classification calls
  for deletion, not retention with a closed status.
- Update only the summary line and leave the NC-033 entry block in place —
  rejected: would leave the inventory internally inconsistent (entry present,
  summary line silent about it).

## Implementation
### Target file
`docs/00_governance/governance_03_issue-and-uncertainty-management.md`

### Procedure
1. Locate the `#### NC-033` heading by content match (do not assume the cited
   line number without confirming via search first, since this file's line
   numbers shift whenever a sibling NC entry is added or removed) and remove the
   entire entry block: the heading through its final bullet (`- **Blocking**:
   No`) and the one blank line immediately following it, ending just before the
   next entry's heading (`#### NC-035`).
2. After the deletion, locate the closing summary line by its literal text ("No
   other active Needs Confirmation items exist outside the set listed here: ...")
   rather than by its pre-deletion line number — deleting step 1's block shifts
   all subsequent line numbers in this same file. Remove `NC-033, ` (with its
   trailing comma and space) from the enumerated list on that line.

### Method
Direct text edit: one block deletion, one single-line text edit (remove one item
from a comma-separated enumeration) — no code, schema, or config change.

### Details
Block to remove (verbatim, lines 187-203 as confirmed by direct read at this
document's generation time — re-locate by the `#### NC-033` heading if this file
has changed further since):
```
#### NC-033

- **Source File**: `rag_02_03_ingestion_pipeline-chunksplitter.md`
- **Section**: lang Field Validation
- **Line Number**: ~194
- **Question**: Is `lang` field enforcement against `LanguageCode` values intended?
- **Evidence**: The document states: "any non-empty string accepted; the en/ja value set (LanguageCode) is convention only — not enforced at parse time (Needs confirmation: whether enforcement is intended)"
- **Impact**: If lang-field enforcement is actually intended but not implemented, downstream language-handling code could behave incorrectly without anyone flagging it as an open question
- **Required Action**: Owner confirmation or investigation of scripts/rag/ validation logic for the lang field
- **Status**: open
- **Assigned To**: Unassigned
- **Last Reviewed**: 2026-09-14
- **Priority**: Low
- **Related NC**: None
- **Resolution Target**: Next ChunkSplitter specification review
- **Blocking**: No

```
(the trailing blank line above is removed too, so `#### NC-035` becomes the next
line after the preceding entry's own trailing blank line — do not leave a double
blank line or remove the separator before `#### NC-033`).

Summary line, current text (confirmed via direct read, line 238):
> No other active Needs Confirmation items exist outside the set listed here:
> NC-033, NC-035, and NC-036.

New text:
> No other active Needs Confirmation items exist outside the set listed here:
> NC-035, and NC-036.

Do not modify any other NC entry (NC-035, NC-036) or any other section of this
file. Do not modify `docs/21_rag/rag_05_5-constraints-reference.md` — it is the
sibling implementation procedure document's own scope (seq 02 of this Plan).

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

Expected outcome: all pass; NC-033 is absent from Part 2 "Active Items" and from the
closing summary line.

## Completion criteria
- The `#### NC-033` entry block is absent from Part 2 "Active Items".
- The closing summary line's enumerated list no longer contains "NC-033".
- No other NC entry or section is altered.
- All checkers listed in Validation plan pass.

## Out of scope
- Fixing the `lang` field row in
  `docs/21_rag/rag_05_5-constraints-reference.md` — handled by the sibling
  implementation procedure document for that file (seq 02 of this Plan).
- Any change to NC-035 or NC-036 entries.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove the NC-033 entry block and update the summary line per Implementation > Procedure/Method/Details | Completed | 20260929-151927 | 20260929-151927 | NC-033 block (lines 187-203) removed; summary line updated; stale_detector clean after rewording one false-positive backtick mention (CrawlTarget) |
| 2 | Run the applicable documentation checker(s) per Validation plan | Completed | 20260929-151928 | 20260929-151928 | Doc checkers run — NC-033 confirmed absent; structure passes; pre-existing unrelated findings recorded, out of scope |

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
- **Requirement ID**: REQ-001
- **Source issue**: issues/20260927-211410_nc033_remove-obsolete-lang-field-enforcement-question.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260928-163034_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260929-151401
- **Related target files**: docs/00_governance/governance_03_issue-and-uncertainty-management.md