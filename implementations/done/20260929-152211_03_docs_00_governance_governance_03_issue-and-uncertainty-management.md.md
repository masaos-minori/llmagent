## Goal
Remove the NC-035 entry from Part 2 "Active Items" and update the closing
summary line, once both the code fix and its regression test have landed and
passed (REQ-003).

## Scope
- **In-Scope**: The NC-035 entry block in Part 2 "Active Items" (confirmed at
  lines 187-203) and the closing summary line enumerating open items (confirmed
  at line 221) of this target file.
- **Out-of-Scope**: NC-021, NC-027, NC-028, NC-029, NC-033, NC-036 entries
  (unrelated items, left untouched); the code fix in
  `scripts/rag/ingestion/crawler.py` or the regression test in
  `tests/rag/ingestion/test_crawler_integration.py` — this document's own move
  MUST NOT proceed until both sibling documents (seq 01, seq 02 of this Plan)
  show `Completed`.

## Assumptions
- The Plan's ordering (fix and test land and pass first, entry removed second)
  is binding for this cycle: do not remove this entry before confirming (by
  reading both sibling implementation procedure documents' own Execution
  Status) that both are `Completed` (Plan Risks).
- The line numbers cited here (187-203, 221) reflect this file's current state
  as of this document's generation, after the sibling NC-021, NC-027, NC-028,
  NC-029, and NC-033 entries and an unrelated Part 1 Known Issues item were
  already removed earlier — re-confirm by content match (`#### NC-035`
  heading), not solely by these line numbers, since the Plan's own original
  citation (349-364, 383) has already been superseded once (see Plan's
  Implementation Target Files revalidation note).
- Per the Plan's Background, the user confirmed no historical rationale exists
  for the `max_depth=3`/`max_pages=200` operational limits themselves — this
  entry is removed entirely (not merely trimmed), since both its code-bug and
  rationale-question components are resolved in the same cycle.

## Design decisions
- Remove the entry outright rather than marking it "closed" in place, per the
  governance doc's own Part 2 "Status Values" rule (`skills/python-design` —
  follow the doc's own documented convention rather than introducing a new
  closed-item convention).

## Alternatives considered
- Remove the entry in the same cycle as the code fix without waiting for test
  confirmation — rejected: the Plan's own Risk mitigation explicitly orders
  documentation removal after the fix and test are both confirmed complete, to
  avoid a premature closure if either is blocked.
- Trim the entry to only the still-open rationale question instead of removing
  it entirely — rejected: the Plan's Background explicitly records the user's
  "no rationale, accepted as-is" resolution for the operational-value question
  in the same cycle as the bug fix, so both components are resolved and the
  entry is removed entirely (Plan Background).
- Update only the summary line and leave the NC-035 entry block in place —
  rejected: would leave the inventory internally inconsistent (entry present,
  summary line silent about it).

## Implementation
### Target file
`docs/00_governance/governance_03_issue-and-uncertainty-management.md`

### Procedure
0. Before making any edit, confirm both sibling implementation procedure
   documents (seq 01 for `scripts/rag/ingestion/crawler.py`, seq 02 for
   `tests/rag/ingestion/test_crawler_integration.py`) show `Completed` — do
   not proceed on this document if either sibling is still `Pending` or
   `Blocked`.
1. Locate the `#### NC-035` heading by content match (do not assume the cited
   line number without confirming via search first, since this file's line
   numbers shift whenever a sibling NC entry is added or removed) and remove
   the entire entry block: the heading through its final bullet (`-
   **Blocking**: No`) and the one blank line immediately following it, ending
   just before the next entry's heading (`#### NC-036`).
2. After the deletion, locate the closing summary line by its literal text
   ("No other active Needs Confirmation items exist outside the set listed
   here: ...") rather than by its pre-deletion line number — deleting step 1's
   block shifts all subsequent line numbers in this same file. Remove
   `NC-035 and ` (matching this file's current two-item list phrasing) from
   the enumerated list on that line.

### Method
Direct text edit: one block deletion, one single-line text edit (remove one
item from the enumerated list) — no code, schema, or config change.

### Details
Block to remove (verbatim, lines 187-203 as confirmed by direct read at this
document's generation time — re-locate by the `#### NC-035` heading if this
file has changed further since):
```
#### NC-035

- **Source File**: `crawler.py` / `config/crawler.toml`
- **Section**: max_depth / max_pages operational limits
- **Line Number**: ~61, 66
- **Question**: Why is the crawl depth limited to 3 hops from the start URL, and why is the maximum pages per site limited to 200? What is the historical reason for these specific operational values? Additionally, why does the code's own fallback default for `max_pages` (500) differ from the deployed `config/crawler.toml` value (200)?
- **Evidence**: No rationale comment in `crawler.py` or `config/crawler.toml`; no ADR or governance entry found. `_max_depth` (line 61) and `_max_pages` (line 66) read from `config/crawler.toml` and stop BFS traversal at the limit, but no explanation exists for why 3 and 200 were chosen over any other values. Additionally, `scripts/rag/ingestion/crawler.py:66` falls back to `cfg.get("max_pages", 500)` if the key is absent, while the deployed `config/crawler.toml:23` sets `max_pages = 200` — a code-default-vs-deployed-config mismatch. `config/crawler.toml:22` already carries an inline comment acknowledging this same discrepancy lacks measured justification.
- **Impact**: Operators cannot understand why crawlers stop after 3 hops or 200 pages per site; new developers may not realize these are operational limits rather than technical constraints. The 500-vs-200 mismatch also means removing or misconfiguring the TOML key would silently change deployed behavior to the code's higher default without anyone noticing.
- **Required Action**: Owner confirmation of the historical reason for these specific operational values, and confirmation of which `max_pages` value (500 or 200) is the intended operational limit; if resolved, update the crawler documentation and reconcile the code default with the deployed config accordingly
- **Status**: open
- **Assigned To**: Unassigned
- **Last Reviewed**: 2026-09-27
- **Priority**: Low
- **Related NC**: None
- **Resolution Target**: Next crawler operations review
- **Blocking**: No

```
(the trailing blank line above is removed too, so `#### NC-036` becomes the
next line after the preceding entry's own trailing blank line — do not leave a
double blank line or remove the separator before `#### NC-035`).

Summary line, current text (confirmed via direct read, line 221):
> No other active Needs Confirmation items exist outside the set listed here:
> NC-035 and NC-036.

New text:
> No other active Needs Confirmation items exist outside the set listed here:
> NC-036.

Do not modify the NC-036 entry or any other section of this file. Do not
modify `scripts/rag/ingestion/crawler.py` or
`tests/rag/ingestion/test_crawler_integration.py` — both are the sibling
implementation procedure documents' own scope (seq 01, seq 02 of this Plan).

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

Expected outcome: all pass; NC-035 is absent from Part 2 "Active Items" and from the
closing summary line.

## Completion criteria
- Step 0's precondition (both sibling documents `Completed`) is satisfied
  before this document's own move to `implementations/done/`.
- The `#### NC-035` entry block is absent from Part 2 "Active Items".
- The closing summary line's enumerated list no longer contains "NC-035".
- No other NC entry or section is altered.
- All checkers listed in Validation plan pass.

## Out of scope
- The code fix in `scripts/rag/ingestion/crawler.py` — handled by the sibling
  implementation procedure document for that file (seq 01 of this Plan).
- The regression test in
  `tests/rag/ingestion/test_crawler_integration.py` — handled by the sibling
  implementation procedure document for that file (seq 02 of this Plan).
- Any change to the NC-036 entry.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove the NC-035 entry block and update the summary line per Implementation > Procedure/Method/Details, gated on both sibling documents' completion | Completed | 20260929-154305 | 20260929-154305 | Step 0 precondition confirmed: both sibling documents (crawler.py fix, regression test) Completed. NC-035 block (lines 187-203) removed; summary line updated; stale_detector clean |
| 2 | Run the applicable documentation checker(s) per Validation plan | Completed | 20260929-154305 | 20260929-154305 | Doc checkers run — NC-035 confirmed absent; structure passes; content-policy finding for this file resolved as a side effect (was citing the now-removed NC-035 entry text); pre-existing unrelated findings recorded |

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
- **Source issue**: issues/20260927-211418_nc035_fix-crawler-max_pages-default-mismatch-and-confirm-limit-rationale.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260928-164033_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260929-152211
- **Related target files**: docs/00_governance/governance_03_issue-and-uncertainty-management.md