## Goal
Replace the full JSON response example (lines 27-44) in
`docs/eventbus/01_dlq_operations.md` with a one-line shape description and a pointer to
`scripts/eventbus/dlq_route.py`, per `REQ-003` (Plan `plans/20260920-160505_plan.md`),
so `tools/check_docs_content_policy.py` reports no finding at this location while the
`limit`/`offset` request-parameter table and the "Field descriptions" prose remain
unchanged.

## Scope
In scope: the `### Response (HTTP 200)` JSON code block (lines 27-44) only. Out of
scope: the `### Request Parameters` table (lines 20-23), the "Field descriptions" list
(lines 46-50), the "### Empty-result behavior" JSON example (lines 56-63), the
"### Invalid-parameter behavior" and "### Ordering" sections (lines 65-74) — none of
these were flagged by `check_docs_content_policy.py` (re-confirmed 2026-09-20).

## Assumptions
The finding at line 27 and the file's exact current content (re-verified via Read
during this document's creation) have not shifted since the Plan was frozen — no
commit has touched this file or `scripts/eventbus/dlq_route.py` since.

## Design decisions
Replace the JSON example with one sentence describing the response shape (a pagination
envelope plus an `items` array) and pointing to `scripts/eventbus/dlq_route.py` for the
exact schema, immediately followed by the existing, unchanged "Field descriptions"
list — which already explains `total`/`limit`/`offset`/`items` in prose and is not
itself code-derivable restatement (it explains what each field *means* for a reader,
which a bare JSON example does not).

## Alternatives considered
- Remove the JSON example and the "Field descriptions" list together: rejected — the
  Plan's `REQ-003` targets only the JSON example (line 27); "Field descriptions" is
  reader-facing prose, not flagged, and provides value the schema pointer alone does
  not (a one-line meaning for each field).
- Also remove or rewrite the "### Empty-result behavior" JSON example (lines 56-63)
  for consistency: rejected as exceeding this row's frozen scope — not flagged, not
  named by `REQ-003`.

## Implementation
### Target file
`docs/eventbus/01_dlq_operations.md`

### Procedure
1. Read lines 25-51 to confirm current content matches the Plan's recorded evidence.
2. Replace the JSON code block (lines 27-44) with one sentence: the response returns a
   pagination envelope (`total`/`limit`/`offset`) plus an `items` array of DLQ event
   objects (each carrying the event's metadata plus `dlq_at`) — see
   `scripts/eventbus/dlq_route.py` for the exact response schema.
3. Leave the "### Response (HTTP 200)" heading, the "Field descriptions" list (lines
   46-50), and every other section unchanged.

### Method
Single localized `Edit`, replacing exactly the JSON code block (lines 27-44) with the
sentence from Procedure step 2. Do not touch the "Field descriptions" list or any other
line.

### Details
Do not restate any of the seven JSON field names/types from the removed example
(`event_id`, `topic`, `payload`, `producer`, `published_at`,
`delivery_failure_count`, `dlq_at`) — all are directly readable from
`scripts/eventbus/dlq_route.py`. The "Field descriptions" list already covers
`total`/`limit`/`offset`/`items` at a higher level and stays as-is.

## Compatibility considerations
`N/A: documentation-only change, no code, public interface, or data format is affected`.

## Security considerations
`N/A: no security-relevant content is touched`.

## Rollback considerations
Revert via `git checkout` on this one file. The edit is independently revertable from
the other four Plan rows' files.

## Validation plan
- `uv run python tools/check_docs_content_policy.py` — confirm zero findings for
  `docs/eventbus/01_dlq_operations.md` (Plan `AC-3`).
- `uv run python tools/check_docs_quality.py`, scoped to this file — confirm no new
  warning is introduced.
- `uv run python tools/check_docs_structure.py docs/eventbus/01_dlq_operations.md` —
  confirm it passes (this file had no pre-existing `check_docs_structure.py` finding
  recorded in the Plan).

## Completion criteria
The `### Response (HTTP 200)` JSON example is replaced by a one-sentence shape
description and canonical-source pointer; the `### Request Parameters` table and
"Field descriptions" list are unchanged; `check_docs_content_policy.py` reports zero
findings for this file.

## Out of scope
- The `### Request Parameters` table, "Field descriptions" list, "### Empty-result
  behavior", "### Invalid-parameter behavior", and "### Ordering" sections (see Scope)
  — not flagged, not part of `REQ-003`.
- Any other `docs/*.md` file — see the Plan's other four target-file rows, each with
  its own implementation procedure document.
- Extending `check_docs_content_policy.py`'s detection rules.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260920-171508 | 20260920-171508 |  |
| 2 | Add or update tests per Validation plan | Completed | 20260920-171508 | 20260920-171508 | N/A: documentation-only, no automated test beyond the doc checkers already listed |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260920-171508 | 20260920-171508 | Scoped to the doc checkers in Validation plan, not the full Python toolchain (no `scripts/` change) |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260920-171508 | 20260920-171508 | N/A: this document IS the documentation change |

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
- **Requirement ID**: `REQ-003` — replace the full JSON response example with a shape description and pointer
- **Source issue**: issues/20260920-154603_dcp012_eventbus-docs-content-policy-cleanup-batch-2.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260920-160505_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260920-163249
- **Related target files**: docs/eventbus/01_dlq_operations.md