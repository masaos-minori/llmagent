## Goal
Replace the "Needs Confirmation" marker for `MIN_HEADING_LINES_FOR_MARKDOWN` with an
explicit "no rationale found, accepted as heuristic" statement (REQ-001).

## Scope
- **In-Scope**: The single marker sentence on line 40 of this target file.
- **Out-of-Scope**: `MIN_HEADING_LINES_FOR_MARKDOWN`'s value in
  `scripts/rag/ingestion/chunk_splitter.py` (read-only reference, not modified);
  removing the NC-027 entry from the governance inventory (covered by the sibling
  implementation procedure document for
  `docs/00_governance/governance_03_issue-and-uncertainty-management.md`); NC-028,
  NC-029, NC-034 (unrelated items).

## Assumptions
- The Plan's "no rationale found, accepted as heuristic" resolution is
  owner-confirmed and authoritative for this closure (Plan Assumptions).
- No document other than this file and the governance inventory references
  `MIN_HEADING_LINES_FOR_MARKDOWN` or NC-027 (confirmed via Plan's Implementation
  Target Files evidence; not independently re-searched here).

## Design decisions
- Reuse NC-034's already-established "no recorded rationale ... accepted as
  heuristic" phrasing pattern (`config/chunk_splitter.toml` lines 5-7) rather than
  inventing new wording, keeping resolution style consistent across sibling
  "no rationale" NC closures (per `skills/python-design` — minimal, consistency-first
  choice; no architecture impact since this is a single prose sentence).

## Alternatives considered
- Leave the marker as "unconfirmed (Needs Confirmation)" and only remove the
  governance inventory entry — rejected: would leave the two files inconsistent
  (inventory closed, inline doc still showing an open question), violating the
  Plan's own Risk mitigation (both files must be updated together).
- Word the resolution differently from NC-034's precedent — rejected: the Plan's
  Design section explicitly calls for consistent phrasing across sibling closures.

## Implementation
### Target file
`docs/21_rag/rag_02_03_ingestion_pipeline-chunksplitter.md`

### Procedure
1. Open `docs/21_rag/rag_02_03_ingestion_pipeline-chunksplitter.md` and locate line 40
   (confirmed unchanged at this line by direct read during this document's
   generation).
2. Replace the trailing marker clause of that line with an explicit "no rationale,
   accepted as heuristic" statement.

### Method
Direct text replacement (single line, prose only) — no code, config, or schema
change; no build or migration step.

### Details
Current line 40 (confirmed via direct read):
> This module defines the following constants. See source code for details. Note
> that the rationale for `MIN_HEADING_LINES_FOR_MARKDOWN = 2` is unconfirmed (Needs
> Confirmation).

Replace it with (mirrors NC-034's precedent phrasing in
`config/chunk_splitter.toml` lines 5-7, per the Plan's Implementation intent):
> This module defines the following constants. See source code for details.
> `MIN_HEADING_LINES_FOR_MARKDOWN = 2` has no recorded historical rationale — traced
> through git history to the repository's initial commit with no explanatory commit
> message, ADR, or code comment found — and is accepted as an established heuristic,
> to be re-validated empirically if it becomes a concern.

Do not modify `scripts/rag/ingestion/chunk_splitter.py` — the constant's value is
out of scope (Plan Scope, Out-of-Scope).

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
- `uv run python tools/check_docs_structure.py docs/21_rag/rag_02_03_ingestion_pipeline-chunksplitter.md` (docs file edited)
- `uv run python tools/check_docs_content_policy.py` (docs file edited)
- `uv run python tools/check_needs_confirmation_inventory.py` (a Needs Confirmation
  marker is resolved by this change)

Expected outcome: all pass; the marker is no longer flagged as an open Needs
Confirmation item.

## Completion criteria
- Line 40 no longer contains "(Needs Confirmation)" or "unconfirmed".
- Line 40 states the constant has no recorded historical rationale and is accepted
  as an established heuristic.
- All checkers listed in Validation plan pass.

## Out of scope
- Removing the NC-027 entry from
  `docs/00_governance/governance_03_issue-and-uncertainty-management.md` — handled
  by the sibling implementation procedure document for that file (seq 02 of this
  Plan).
- Any change to `MIN_HEADING_LINES_FOR_MARKDOWN`'s value or other constants in
  `scripts/rag/ingestion/chunk_splitter.py`.
- NC-028, NC-029, NC-034 (separate issues, out of this Plan's scope).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Replace the marker sentence in the target file per Implementation > Procedure/Method/Details | Completed | 20260929-103929 | 20260929-103929 | Line 40 marker replaced; stale_detector clean; doc checkers run — 2 pre-existing unrelated self-reference findings in check_docs_structure.py confirmed pre-existing via git stash, not caused by this change; no new NC-inventory warning for this file |
| 2 | Run the applicable documentation checker(s) per Validation plan | Completed | 20260929-103939 | 20260929-103939 | check_docs_quality.py / check_docs_structure.py / check_docs_content_policy.py / check_needs_confirmation_inventory.py all run; no new finding attributable to this file |

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
- **Source issue**: issues/20260927-211354_nc027_confirm-rationale-for-min_heading_lines_for_markdown2.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260928-152710_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260929-103253
- **Related target files**: docs/21_rag/rag_02_03_ingestion_pipeline-chunksplitter.md