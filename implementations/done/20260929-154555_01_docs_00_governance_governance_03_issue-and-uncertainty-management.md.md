## Goal
Remove the stale NC-036 entry from Part 2 "Active Items" and update the closing
summary line (REQ-001).

## Scope
- **In-Scope**: The NC-036 entry block in Part 2 "Active Items" (confirmed at
  lines 187-202, currently the last entry in this section) and the closing
  summary line (confirmed at line 204) of this target file.
- **Out-of-Scope**: The log-message fix in
  `scripts/rag/pipeline_service.py` (covered by the sibling implementation
  procedure document for that file, seq 02 of this Plan); re-verifying ADR-010
  Decision #9 compliance itself (already confirmed fixed by the cited commits).

## Assumptions
- Both cited commits (`ba82419b`, `4ee51b8d`) already fixed the underlying
  ADR-010 contradiction NC-036 describes, and the test it cites
  (`test_json_parse_error_calls_set_fallback_reason`) no longer exists under
  that name — it was renamed to
  test_json_parse_error_does_not_call_set_fallback_reason and now asserts the
  opposite (Plan Background) — this entry documents a resolved, stale state,
  not an open question.
- The line numbers cited here (187-202, 204) reflect this file's current state
  as of this document's generation, after the sibling NC-021, NC-027, NC-028,
  NC-029, NC-033, and NC-035 entries and an unrelated Part 1 Known Issues item
  were already removed earlier — re-confirm by content match (`#### NC-036`
  heading), not solely by these line numbers, since the Plan's own original
  citation (366-381, 383) has already been superseded once (see Plan's
  Implementation Target Files revalidation note).
- NC-036 is currently the last entry in "Active Items" (no `#### NC-037`
  follows it) — its block ends directly at the summary line, not at another
  NC heading; re-confirm this is still the case before deleting, since a
  future NC entry could be appended after it by an unrelated cycle.

## Design decisions
- Remove the entry outright rather than marking it "closed" in place, per the
  governance doc's own Part 2 "Status Values" rule and per `rules/coding.md`'s
  "Obsolete and removable" Documentation notes classification (`skills/python-design`
  — follow the doc's own documented convention).

## Alternatives considered
- Mark NC-036 "Status: closed" in place instead of deleting the entry —
  rejected: contradicts the governance doc's own explicit removal-on-resolution
  rule cited above.
- Leave a note in the entry referencing the fixing commits instead of removing
  it — rejected: the governance doc's own Part 2 rule requires removal on
  resolution, not an amended closed-out record.
- Update only the summary line and leave the NC-036 entry block in place —
  rejected: would leave the inventory internally inconsistent (entry present,
  summary line silent about it).

## Implementation
### Target file
`docs/00_governance/governance_03_issue-and-uncertainty-management.md`

### Procedure
1. Locate the `#### NC-036` heading by content match (do not assume the cited
   line number without confirming via search first, since this file's line
   numbers shift whenever a sibling NC entry is added or removed) and confirm
   it is still the last entry (no `#### NC-037` follows). Remove the entire
   entry block: the heading through its final bullet (`- **Blocking**: No`)
   and the one blank line immediately following it, ending just before the
   closing summary line.
2. After the deletion, locate the closing summary line by its literal text
   ("No other active Needs Confirmation items exist outside the set listed
   here: ...") rather than by its pre-deletion line number — deleting step 1's
   block shifts subsequent line numbers in this same file. Since NC-036 is
   currently the only ID in the enumerated list, replace the entire sentence
   with one stating no active items remain (see Details below for the exact
   wording, contingent on whether any other NC entry is later added to this
   list before this cycle runs).

### Method
Direct text edit: one block deletion, one single-line text edit — no code,
schema, or config change.

### Details
Block to remove (verbatim, lines 187-202 as confirmed by direct read at this
document's generation time — re-locate by the `#### NC-036` heading if this
file has changed further since):
```
#### NC-036

- **Source File**: `scripts/rag/pipeline_service.py::call_rag_service()` / `ADR-010-rag-fallback.md`
- **Section**: Decision #9 vs. actual behavior
- **Line Number**: Decision #9 (line 69), `call_rag_service()` ValueError handling
- **Question**: Is the parse-error-triggers-fallback behavior an intentional refinement of Decision #9 or an unintended deviation?
- **Evidence**: ADR-010 Decision #9 states "解析エラーはログに記録し、空結果として扱う" (parse errors should be logged and treated as an empty result); however, `call_rag_service()` returns `None` on parse error, triggering fallback. The test `test_json_parse_error_calls_set_fallback_reason` confirms this behavior is actively defended by a passing test.
- **Impact**: An undocumented ADR deviation actively defended by a passing test — operators may assume parse errors are handled per ADR when they actually trigger fallback
- **Required Action**: Owner/architect judgment required: (1) If intentional, amend ADR-010 via ADR Change Protocol + RACI approval from `@data-eng`; (2) If unintended, fix `call_rag_service()` to treat parse errors as empty results per Decision #9. (Priority intentionally differs from neighboring NC entries: this item documents an active code/ADR contradiction with a named owner requiring architect judgment, not an unknown-rationale documentation question.)
- **Status**: open
- **Assigned To**: @data-eng
- **Last Reviewed**: 2026-09-16
- **Priority**: High
- **Related NC**: None
- **Resolution Target**: Next RAG architecture review
- **Blocking**: No

```
(the trailing blank line above is removed too, so the summary line becomes the
next non-blank line after the preceding entry's own trailing blank line).

Summary line, current text (confirmed via direct read, line 204):
> No other active Needs Confirmation items exist outside the set listed here: NC-036.

New text (NC-036 was the sole remaining ID in this list; if this file has
gained a new NC entry since this document's generation, re-derive the correct
enumerated-list wording from whatever IDs actually remain instead of applying
this exact replacement blindly):
> No other active Needs Confirmation items remain open.

Do not modify any other section of this file. Do not modify
`scripts/rag/pipeline_service.py` — it is the sibling implementation procedure
document's own scope (seq 02 of this Plan).

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

Expected outcome: all pass; NC-036 is absent from Part 2 "Active Items" and from the
closing summary line.

## Completion criteria
- The `#### NC-036` entry block is absent from Part 2 "Active Items".
- The closing summary line accurately reflects the remaining set of NC entries
  (no active items remain, unless a new entry was added to this file since
  this document's generation, in which case the line is worded accordingly).
- No other section is altered.
- All checkers listed in Validation plan pass.

## Out of scope
- The log-message fix in `scripts/rag/pipeline_service.py` — handled by the
  sibling implementation procedure document for that file (seq 02 of this
  Plan).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove the NC-036 entry block and update the summary line per Implementation > Procedure/Method/Details | Completed | 20260929-154939 | 20260929-154939 | NC-036 block (lines 187-202, was the last entry) removed; summary line replaced with 'No other active Needs Confirmation items remain open.'; stale_detector clean |
| 2 | Run the applicable documentation checker(s) per Validation plan | Completed | 20260929-154939 | 20260929-154939 | Doc checkers run — NC-036 confirmed absent, inventory now empty; structure passes; pre-existing unrelated findings recorded |

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
- **Source issue**: issues/20260927-211419_nc036_remove-stale-nc-036-adr-010-contradiction-entry.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260928-164318_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260929-154555
- **Related target files**: docs/00_governance/governance_03_issue-and-uncertainty-management.md