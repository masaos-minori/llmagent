## Goal
Replace the "Needs Confirmation" marker for `MIN_TEXT_LENGTH_FOR_DETECTION` with an
explicit "no rationale found, accepted as-is" statement (REQ-001).

## Scope
- **In-Scope**: The single marker sentence on line 47 of this target file.
- **Out-of-Scope**: `MIN_TEXT_LENGTH_FOR_DETECTION`'s value in
  `scripts/rag/utils.py` (read-only reference, not modified); `detect_lang()`'s
  CJK-ratio detection logic in `scripts/rag/ingestion/crawler_utils.py`
  (read-only reference, not modified); removing the NC-029 entry from the
  governance inventory (covered by the sibling implementation procedure document
  for `docs/00_governance/governance_03_issue-and-uncertainty-management.md`);
  NC-027, NC-028, NC-034 (unrelated items).

## Assumptions
- The Plan's "no rationale found, accepted as-is" resolution is owner-confirmed
  and authoritative for this closure (Plan Assumptions).
- No document other than this file and the governance inventory references
  `MIN_TEXT_LENGTH_FOR_DETECTION` or NC-029 (confirmed via Plan's Implementation
  Target Files/Reference Files evidence; not independently re-searched here).

## Design decisions
- Mirror the resolution style already used for the sibling NC-027
  (`plans/done/20260928-152710_plan.md`) and NC-028
  (`plans/done/20260928-154502_plan.md`) closures rather than inventing new
  wording, keeping phrasing consistent across sibling "no rationale" NC closures
  (per `skills/python-design` — minimal, consistency-first choice; no
  architecture impact since this is a single prose sentence).

## Alternatives considered
- Leave the marker as "unconfirmed (Needs Confirmation)" and only remove the
  governance inventory entry — rejected: would leave the two files inconsistent
  (inventory closed, inline doc still showing an open question), violating the
  Plan's own Risk mitigation (both files must be updated together).
- Word the resolution differently from the sibling NC-027/NC-028 precedent —
  rejected: the Plan's Design section explicitly calls for consistent phrasing
  across sibling closures.

## Implementation
### Target file
`docs/21_rag/rag_02_09_ingestion_pipeline-shared-utilities.md`

### Procedure
1. Open `docs/21_rag/rag_02_09_ingestion_pipeline-shared-utilities.md` and locate
   line 47 (confirmed unchanged at this line by direct read during this
   document's generation).
2. Replace the trailing marker clause of that line with an explicit "no
   rationale, accepted as-is" statement.

### Method
Direct text replacement (single line, prose only) — no code, config, or schema
change; no build or migration step.

### Details
Current line 47 (confirmed via direct read):
> This module defines the following constants. Please refer to the source code
> for details. Specifically, the rationale for
> `MIN_TEXT_LENGTH_FOR_DETECTION = 100` is unconfirmed (Needs Confirmation).

Replace it with (mirrors the sibling NC-027/NC-028 closures' precedent phrasing,
per the Plan's Implementation intent):
> This module defines the following constants. Please refer to the source code
> for details. `MIN_TEXT_LENGTH_FOR_DETECTION = 100` has no recorded historical
> rationale and is accepted as a heuristic value as-is.

Do not modify `scripts/rag/utils.py` or
`scripts/rag/ingestion/crawler_utils.py`'s `detect_lang()` — both are out of
scope (Plan Scope, Out-of-Scope).

## Compatibility considerations
N/A: documentation-only prose change, no public contract, API, schema, or runtime
behavior affected.

## Security considerations
N/A: no code, credentials, or data-handling change.

## Rollback considerations
Single-line prose revert via `git revert`/`git checkout` of this file if needed; no
data migration or schema state to unwind.

## Validation plan
Run the applicable documentation checker(s) per `routing.md` Tools → "When to run
which tool":
- `uv run python tools/check_docs_quality.py` (docs file edited)
- `uv run python tools/check_docs_structure.py docs/21_rag/rag_02_09_ingestion_pipeline-shared-utilities.md` (docs file edited)
- `uv run python tools/check_docs_content_policy.py` (docs file edited)
- `uv run python tools/check_needs_confirmation_inventory.py` (a Needs Confirmation
  marker is resolved by this change)

Expected outcome: all pass; the marker is no longer flagged as an open Needs
Confirmation item.

## Completion criteria
- Line 47 no longer contains "(Needs Confirmation)" or "unconfirmed".
- Line 47 states the constant has no recorded historical rationale and is
  accepted as a heuristic value as-is.
- All checkers listed in Validation plan pass.

## Out of scope
- Removing the NC-029 entry from
  `docs/00_governance/governance_03_issue-and-uncertainty-management.md` —
  handled by the sibling implementation procedure document for that file (seq 02
  of this Plan).
- Any change to `MIN_TEXT_LENGTH_FOR_DETECTION`'s value or `detect_lang()`'s
  logic.
- NC-027, NC-028, NC-034 (separate issues, out of this Plan's scope).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Replace the marker sentence in the target file per Implementation > Procedure/Method/Details | Completed | 20260929-140504 | 20260929-140504 | Marker sentence replaced; stale_detector clean |
| 2 | Run the applicable documentation checker(s) per Validation plan | Completed | 20260929-140504 | 20260929-140504 | check_docs_quality.py / check_docs_structure.py / check_docs_content_policy.py / check_needs_confirmation_inventory.py all run; no finding for this file |

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
- **Source issue**: issues/20260927-211401_nc029_confirm-rationale-for-min_text_length_for_detection100.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260928-162759_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260929-140027
- **Related target files**: docs/21_rag/rag_02_09_ingestion_pipeline-shared-utilities.md