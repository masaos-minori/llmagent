## Goal
Replace the full JSON response example (lines 48-64) in
`docs/eventbus/03_replay_operations.md`'s JSON-format response section with a one-line
shape description and a pointer to `scripts/eventbus/replay_route.py`, per `REQ-004`
(Plan `plans/20260920-160505_plan.md`), so `tools/check_docs_content_policy.py`
reports no finding at this location while the "Field descriptions" prose remains
unchanged.

## Scope
In scope: the `### Response (HTTP 200) — JSON format (format=json)` JSON code block
(lines 48-64) only. Out of scope: the `### Request Parameters` table (lines 21-26), the
SSE-format response section (lines 28-42, including its own field descriptions and
"Connection lifecycle" note), the JSON-format "Field descriptions" list (lines 66-70),
the "### Empty-result behavior" JSON example (lines 76-83), and the
"### Invalid-parameter behavior"/"### Ordering"/"### Concurrency guarantee" sections
(lines 87-105) — none of these were flagged by `check_docs_content_policy.py`
(re-confirmed 2026-09-20).

## Assumptions
The finding at line 48 and the file's exact current content (re-verified via Read
during this document's creation) have not shifted since the Plan was frozen — no
commit has touched this file or `scripts/eventbus/replay_route.py` since.

## Design decisions
Replace the JSON example with one sentence describing the response shape (a pagination
envelope plus an `items` array) and pointing to `scripts/eventbus/replay_route.py` for
the exact schema, immediately followed by the existing, unchanged "Field descriptions"
list (lines 66-70) — mirroring the same treatment already applied to the sibling
`eventbus/01_dlq_operations.md` row of this same Plan (`REQ-003`), since both endpoints
share the same pagination-envelope response shape.

## Alternatives considered
- Also rewrite the SSE-format response section's own event-format block (lines 30-36)
  for consistency: rejected — that block is a small `id:`/`data:` two-line SSE frame
  format illustration, not a full JSON payload example, and was not flagged.
- Remove the JSON example and the "Field descriptions" list together: rejected — the
  Plan's `REQ-004` targets only the JSON example; "Field descriptions" is reader-facing
  prose, not flagged, and not code-derivable restatement.

## Implementation
### Target file
`docs/eventbus/03_replay_operations.md`

### Procedure
1. Read lines 44-71 to confirm current content matches the Plan's recorded evidence.
2. Replace the JSON code block (lines 48-64) with one sentence: the response returns a
   pagination envelope (`total`/`limit`/`offset`) plus an `items` array of event
   objects (each carrying the event's metadata, plus `dlq_at` if the event was promoted
   to the DLQ) — see `scripts/eventbus/replay_route.py` for the exact response schema.
3. Leave the "### Response (HTTP 200) — JSON format (`format=json`)" heading, the
   "Field descriptions" list (lines 66-70), and every other section unchanged.

### Method
Single localized `Edit`, replacing exactly the JSON code block (lines 48-64) with the
sentence from Procedure step 2. Do not touch the SSE-format section, the "Field
descriptions" list, or any other line.

### Details
Do not restate any of the six JSON field names/types from the removed example
(`event_id`, `topic`, `payload`, `producer`, `published_at`,
`delivery_failure_count`) — all are directly readable from
`scripts/eventbus/replay_route.py`. The "Field descriptions" list already covers
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
  `docs/eventbus/03_replay_operations.md` (Plan `AC-4`).
- `uv run python tools/check_docs_quality.py`, scoped to this file — confirm no new
  warning is introduced.
- `uv run python tools/check_docs_structure.py docs/eventbus/03_replay_operations.md`
  — confirm it passes (this file had no pre-existing `check_docs_structure.py` finding
  recorded in the Plan).

## Completion criteria
The JSON-format `### Response (HTTP 200)` example is replaced by a one-sentence shape
description and canonical-source pointer; the SSE-format section, the "Field
descriptions" list, and every other section are unchanged; `check_docs_content_policy.py`
reports zero findings for this file.

## Out of scope
- The `### Request Parameters` table, the SSE-format response section, the
  "Field descriptions" list, "### Empty-result behavior", "### Invalid-parameter
  behavior", "### Ordering", and "### Concurrency guarantee" sections (see Scope) —
  not flagged, not part of `REQ-004`.
- Any other `docs/*.md` file — see the Plan's other four target-file rows, each with
  its own implementation procedure document.
- Extending `check_docs_content_policy.py`'s detection rules.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260920-171613 | 20260920-171613 | Edit left a stray closing code-fence line; caught and fixed during Step 3e review |
| 2 | Add or update tests per Validation plan | Completed | 20260920-171613 | 20260920-171613 | N/A: documentation-only, no automated test beyond the doc checkers already listed |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260920-171613 | 20260920-171613 | Scoped to the doc checkers in Validation plan, not the full Python toolchain (no `scripts/` change) |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260920-171613 | 20260920-171613 | N/A: this document IS the documentation change |

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
- **Requirement ID**: `REQ-004` — replace the full JSON response example with the same treatment as REQ-003
- **Source issue**: issues/20260920-154603_dcp012_eventbus-docs-content-policy-cleanup-batch-2.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260920-160505_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260920-163249
- **Related target files**: docs/eventbus/03_replay_operations.md