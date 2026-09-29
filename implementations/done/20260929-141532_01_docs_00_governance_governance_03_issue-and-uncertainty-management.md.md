## Goal
Remove the NC-034 entry from Part 2 "Active Items" and update the closing summary
line that enumerates remaining open NC items (REQ-001).

## Scope
- **In-Scope**: The NC-034 entry block in Part 2 "Active Items" (confirmed at
  lines 221-237) and the closing summary line enumerating open items (confirmed
  at line 272) of this target file.
- **Out-of-Scope**: NC-021, NC-027, NC-028, NC-029, NC-033, NC-035, NC-036
  entries (unrelated items, left untouched); editing
  `docs/21_rag/rag_02_03_ingestion_pipeline-chunksplitter.md` or
  `config/chunk_splitter.toml` — both confirmed to need no change (Plan
  Background: the doc carries no rationale claim to reconcile, and the toml's
  existing comment already serves as the permanent closure record).

## Assumptions
- The Plan's "no rationale found, accepted as-is, close" resolution is
  owner-confirmed and authoritative for this closure (Plan Assumptions).
- Removing this entry does not affect any other NC entry's numbering or
  cross-references — NC IDs are stable identifiers, not renumbered on removal
  (consistent with the governance doc's own removal-on-resolution rule, Part 2
  "Status Values").
- The line numbers cited here (221-237, 272) reflect this file's current state
  as of this document's generation, after the sibling NC-027, NC-028, and
  NC-029 entries were already removed earlier — re-confirm by content match
  (`#### NC-034` heading), not solely by these line numbers, since the Plan's
  own original citation (332-347, 383) has already been superseded once (see
  Plan's Implementation Target Files revalidation note).

## Design decisions
- Remove the entry outright rather than marking it "closed" in place, per the
  governance doc's own Part 2 "Status Values" rule: "An item is removed from the
  Active Items list ... once it is resolved ... it is not retained here with a
  closed-out status" (`skills/python-design` — follow the doc's own documented
  convention rather than introducing a new closed-item convention).
- Unlike the sibling NC-027/NC-028/NC-029 closures, no new closure phrasing is
  drafted or added anywhere — `config/chunk_splitter.toml`'s existing inline
  comment already serves as the permanent record (Plan Design), so this
  document's only content change is the entry removal itself.

## Alternatives considered
- Mark NC-034 "Status: closed" in place instead of deleting the entry —
  rejected: contradicts the governance doc's own explicit removal-on-resolution
  rule cited above.
- Add a new "no rationale" marker sentence to
  `docs/21_rag/rag_02_03_ingestion_pipeline-chunksplitter.md` to mirror the
  sibling NC-027/NC-028/NC-029 closures — rejected: that document carries no
  existing "Needs Confirmation" marker or rationale claim to resolve (Plan
  Background/Reference Files), so adding one would be new, unrequested content
  rather than a resolution of an existing gap.
- Update only the summary line and leave the NC-034 entry block in place —
  rejected: would leave the inventory internally inconsistent (entry present,
  summary line silent about it).

## Implementation
### Target file
`docs/00_governance/governance_03_issue-and-uncertainty-management.md`

### Procedure
1. Locate the `#### NC-034` heading by content match (do not assume the cited
   line number without confirming via search first, since this file's line
   numbers shift whenever a sibling NC entry is added or removed) and remove the
   entire entry block: the heading through its final bullet (`- **Blocking**:
   No`) and the one blank line immediately following it, ending just before the
   next entry's heading (`#### NC-035`).
2. After the deletion, locate the closing summary line by its literal text ("No
   other active Needs Confirmation items exist outside the set listed here: ...")
   rather than by its pre-deletion line number — deleting step 1's block shifts
   all subsequent line numbers in this same file. Remove `NC-034, ` (with its
   trailing comma and space) from the enumerated list on that line.

### Method
Direct text edit: one block deletion, one single-line text edit (remove one item
from a comma-separated enumeration) — no code, schema, or config change.

### Details
Block to remove (verbatim, lines 221-237 as confirmed by direct read at this
document's generation time — re-locate by the `#### NC-034` heading if this file
has changed further since):
```
#### NC-034

- **Source File**: `chunk_splitter.py` / `config/chunk_splitter.toml`
- **Section**: min_chunk / max_chunk / chunk_overlap constants
- **Line Number**: ~70-71, 168-169, 185-186
- **Question**: Why is the minimum chunk size 40 characters, maximum chunk size 500 characters, and overlap 50 characters? What is the historical reason for these specific values?
- **Evidence**: No rationale comment in `chunk_splitter.py` or `config/chunk_splitter.toml`; no ADR or governance entry found. `_min_chunk` (line 70), `_max_chunk` (line 71), and `_chunk_overlap` (line 74) enforce the constraint boundaries documented in `docs/rag_05_1-configuration-reference.md` line 39, but no explanation exists for why 40/500/50 were chosen over any other values.
- **Impact**: Operators cannot understand why sub-40-char chunks are discarded as noise, why sections exceeding 500 chars are split further, or why overlap is set to 50 characters
- **Required Action**: Owner confirmation of the historical reason for these specific values; if resolved, update the chunksplitter documentation accordingly
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
blank line or remove the separator before `#### NC-034`).

Summary line, current text (confirmed via direct read, line 272):
> No other active Needs Confirmation items exist outside the set listed here:
> NC-021, NC-033, NC-034, NC-035, and NC-036.

New text:
> No other active Needs Confirmation items exist outside the set listed here:
> NC-021, NC-033, NC-035, and NC-036.

Do not modify any other NC entry (NC-021, NC-033, NC-035, NC-036) or any other
section of this file. Do not modify `config/chunk_splitter.toml` or
`docs/21_rag/rag_02_03_ingestion_pipeline-chunksplitter.md` — both are out of
scope (Plan Scope, Out-of-Scope).

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

Expected outcome: all pass; NC-034 is absent from Part 2 "Active Items" and from the
closing summary line.

## Completion criteria
- The `#### NC-034` entry block is absent from Part 2 "Active Items".
- The closing summary line's enumerated list no longer contains "NC-034".
- No other NC entry or section is altered.
- `config/chunk_splitter.toml` and
  `docs/21_rag/rag_02_03_ingestion_pipeline-chunksplitter.md` remain unchanged.
- All checkers listed in Validation plan pass.

## Out of scope
- Any edit to `docs/21_rag/rag_02_03_ingestion_pipeline-chunksplitter.md` or
  `config/chunk_splitter.toml` (Plan Background: confirmed to need no change).
- Any change to `min_chunk`/`max_chunk`/`chunk_overlap`'s values or actual
  performance-tuning validation.
- NC-021, NC-027, NC-028, NC-029, NC-033, NC-035, NC-036 (separate items, out of
  this Plan's scope).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove the NC-034 entry block and update the summary line per Implementation > Procedure/Method/Details | Completed | 20260929-141759 | 20260929-141759 | NC-034 block (lines 221-237) removed; summary line updated (NC-034 dropped from enumerated list); stale_detector clean; config/chunk_splitter.toml and rag_02_03_ingestion_pipeline-chunksplitter.md confirmed unchanged (out of scope) |
| 2 | Run the applicable documentation checker(s) per Validation plan | Completed | 20260929-141759 | 20260929-141759 | Doc checkers run — NC-034 confirmed absent from inventory output; structure check passes; pre-existing unrelated findings recorded (content-policy line 229 crawler item; quality-similarity warnings) — out of this Plan's scope |

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
- **Source issue**: issues/20260927-211412_nc034_confirm-rationale-for-chunk-size-bounds.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260928-163544_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260929-141532
- **Related target files**: docs/00_governance/governance_03_issue-and-uncertainty-management.md