## Goal
Replace the "Needs Confirmation" marker for `_MAX_FTS_TOKENS` with an explicit
"no rationale found, defer to a future performance tuning pass" statement
(REQ-001).

## Scope
- **In-Scope**: The single marker sentence on line 93 of this target file.
- **Out-of-Scope**: `_MAX_FTS_TOKENS`'s value in `scripts/rag/repository.py`
  (read-only reference, not modified); removing the NC-028 entry from the
  governance inventory (covered by the sibling implementation procedure document
  for `docs/00_governance/governance_03_issue-and-uncertainty-management.md`);
  NC-027, NC-029, NC-034 (unrelated items).

## Assumptions
- The Plan's "no rationale found, defer to a future performance tuning pass"
  resolution is owner-confirmed and authoritative for this closure (Plan
  Assumptions).
- No document other than this file and the governance inventory references
  `_MAX_FTS_TOKENS` or NC-028 (confirmed via Plan's Implementation Target Files
  evidence; not independently re-searched here).

## Design decisions
- Mirror the Issue's own suggested phrasing and the sibling NC-027 closure's
  resolution style (`plans/done/20260928-152710_plan.md`) rather than inventing
  new wording, keeping resolution style consistent across sibling "no rationale"
  NC closures (per `skills/python-design` — minimal, consistency-first choice; no
  architecture impact since this is a single prose sentence).

## Alternatives considered
- Leave the marker as an open "Needs Confirmation" question and only remove the
  governance inventory entry — rejected: would leave the two files inconsistent
  (inventory closed, inline doc still showing an open question), violating the
  Plan's own Risk mitigation (both files must be updated together).
- Word the resolution differently from the sibling NC-027 closure's precedent —
  rejected: the Plan's Design section explicitly calls for consistent phrasing
  across sibling closures.

## Implementation
### Target file
`docs/21_rag/rag_02_08_ingestion_pipeline-shared.md`

### Procedure
1. Open `docs/21_rag/rag_02_08_ingestion_pipeline-shared.md` and locate line 93
   (confirmed unchanged at this line by direct read during this document's
   generation).
2. Replace the marker sentence with an explicit "no rationale, defer to a future
   performance tuning pass" statement.

### Method
Direct text replacement (single line, prose only) — no code, config, or schema
change; no build or migration step.

### Details
Current line 93 (confirmed via direct read):
> **[Needs Confirmation]:** There is currently no documented rationale within the
> project for this specific value (20) based on measurement or load testing. As
> it appears to be a heuristic setting, it should be re-validated during
> performance tuning.

Replace it with (mirrors the Issue's own suggested wording and the sibling
NC-027 closure's precedent phrasing, per the Plan's Implementation intent):
> There is no recorded historical rationale or measurement/load-testing data for
> this value (20); it is accepted as a heuristic, with re-validation deferred to
> a future RAG query performance tuning pass.

Do not modify `scripts/rag/repository.py` — the constant's value is out of scope
(Plan Scope, Out-of-Scope).

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
- `uv run python tools/check_docs_structure.py docs/21_rag/rag_02_08_ingestion_pipeline-shared.md` (docs file edited)
- `uv run python tools/check_docs_content_policy.py` (docs file edited)
- `uv run python tools/check_needs_confirmation_inventory.py` (a Needs Confirmation
  marker is resolved by this change)

Expected outcome: all pass; the marker is no longer flagged as an open Needs
Confirmation item.

## Completion criteria
- Line 93 no longer contains "[Needs Confirmation]".
- Line 93 states the constant has no recorded rationale/measurement data and
  defers re-validation to a future performance tuning pass.
- All checkers listed in Validation plan pass.

## Out of scope
- Removing the NC-028 entry from
  `docs/00_governance/governance_03_issue-and-uncertainty-management.md` —
  handled by the sibling implementation procedure document for that file (seq 02
  of this Plan).
- Any change to `_MAX_FTS_TOKENS`'s value or other constants in
  `scripts/rag/repository.py`.
- NC-027, NC-029, NC-034 (separate issues, out of this Plan's scope).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Replace the marker sentence in the target file per Implementation > Procedure/Method/Details | Completed | 20260929-134929 | 20260929-134929 | Marker sentence replaced; stale_detector clean |
| 2 | Run the applicable documentation checker(s) per Validation plan | Completed | 20260929-134930 | 20260929-134930 | check_docs_quality.py / check_docs_structure.py / check_docs_content_policy.py / check_needs_confirmation_inventory.py all run; no finding for this file |

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
- **Source issue**: issues/20260927-211355_nc028_confirm-rationale-for-fts5-query-token-limit-of-20.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260928-154502_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260929-132245
- **Related target files**: docs/21_rag/rag_02_08_ingestion_pipeline-shared.md