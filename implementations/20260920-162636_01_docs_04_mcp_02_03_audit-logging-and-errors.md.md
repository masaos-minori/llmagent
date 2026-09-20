## Goal
Replace `docs/04_mcp_02_03_audit-logging-and-errors.md`'s "Error Classification Table"
(lines 65-74) with a pointer to `scripts/shared/mcp_health.py::HealthRegistry.record_failure()`,
per `REQ-001` (Plan `plans/20260920-160121_plan.md`), so
`tools/check_docs_content_policy.py` reports no finding at this table's location while
the surrounding HealthRegistry design-intent prose is preserved.

## Scope
In scope: the "### Error Classification Table" heading and table (lines 65-76,
including the explanatory paragraph immediately below the table) only. Out of scope:
the "## Audit Log Format" section (lines 18-39), the "## Common Error Formats" table
(lines 45-56), the "### HealthRegistry Updates" bullets (lines 59-63), and the
"## dispatch_tool helper" section (lines 80-94) — none of these were flagged by
`check_docs_content_policy.py` (re-confirmed 2026-09-20). Also out of scope: the
malformed front-matter `related` entry (line 13) — a pre-existing
`check_docs_structure.py` finding recorded in the Plan's Background/Reason for change,
not part of `REQ-001`.

## Assumptions
The finding at line 67 and the file's exact current content (re-verified via Read
during this document's creation) have not shifted since the Plan was frozen — no
commit has touched this file or `scripts/shared/mcp_health.py` since.

## Design decisions
Replace the table (lines 65-74) with a pointer to
`scripts/shared/mcp_health.py::HealthRegistry.record_failure()` as the canonical
source for the exact HTTP-status/retryability classification, while retaining the
explanatory paragraph at line 76 ("For all transport failures, `request_id=""`...")
unchanged immediately after it — that paragraph explains *when* `record_success()`
vs. leaving `request_id` empty applies, which is design intent about the two code
paths' distinct behavior, not a restatement of the table's per-error-type rows.

## Alternatives considered
- Remove the table with no replacement text: rejected — would also strand the
  now-orphaned explanatory paragraph at line 76, which refers back to "transport
  failures" as a category the table previously enumerated.
- Fold the six error-type rows into a bulleted list instead of a full removal:
  rejected — a bulleted list still restates the same code-derivable
  HTTP-status/retryability mapping per error kind; the underlying content, not its
  table shape, is what `REQ-001` requires removing.

## Implementation
### Target file
`docs/04_mcp_02_03_audit-logging-and-errors.md`

### Procedure
1. Read lines 57-77 to confirm current content matches the Plan's recorded evidence.
2. Replace lines 65-74 (the `### Error Classification Table` heading through the last
   table row) with the same heading followed by one sentence pointing to
   `scripts/shared/mcp_health.py::HealthRegistry.record_failure()` (and its callers in
   the transport-error-handling path) as the canonical source for the exact
   HTTP-status/retryability mapping per error kind.
3. Leave line 76 (the "For all transport failures..." paragraph) and every other line
   in this file unchanged.

### Method
Single localized `Edit`, replacing exactly the table's header-through-last-row span
(lines 65-74) with the pointer sentence from Procedure step 2. Do not touch line 76 or
any content outside this range.

### Details
Do not restate any of the six error-type rows (`HTTP 4xx`, `HTTP 5xx`, `Timeout`,
`Connection Refused`, `DNS/Network Error`, `Malformed Response`) or their
retryability/HealthRegistry-action values — all are directly readable from
`scripts/shared/mcp_health.py` and the transport-error-handling code path. Retain the
line 76 paragraph verbatim; it is the design-intent statement about `request_id`
handling and `record_success()` timing, not part of the flagged table.

## Compatibility considerations
`N/A: documentation-only change, no code, public interface, or data format is affected`.

## Security considerations
`N/A: no security-relevant content is touched — this is an error-classification
listing, not a security-boundary/fail-safe-default statement`.

## Rollback considerations
Revert via `git checkout` on this one file. The edit is independently revertable from
the other four Plan rows' files.

## Validation plan
- `uv run python tools/check_docs_content_policy.py` — confirm zero findings for
  `docs/04_mcp_02_03_audit-logging-and-errors.md` (Plan `AC-1`).
- `uv run python tools/check_docs_quality.py`, scoped to this file — confirm no new
  warning is introduced.
- `uv run python tools/check_docs_structure.py docs/04_mcp_02_03_audit-logging-and-errors.md`
  — confirm the finding count does not exceed the one pre-existing malformed-`related`
  finding already recorded in the Plan (this row's edit does not touch the front
  matter, so no change to that count is expected).
- `uv run python tools/check_docs_consistency.py --domain mcp` — confirm no new drift
  finding.

## Completion criteria
The "### Error Classification Table" heading is followed by a canonical-source pointer
sentence, not a table; the line 76 explanatory paragraph is unchanged; no other section
of this file is altered; `check_docs_content_policy.py` reports zero findings for this
file.

## Out of scope
- Every other section of this file (see Scope) — not flagged, not part of `REQ-001`.
- The pre-existing malformed front-matter `related` entry (line 13) — tracked in the
  Plan as a pre-existing, out-of-scope structural finding.
- Any other `docs/*.md` file — see the Plan's other four target-file rows, each with
  its own implementation procedure document.
- Extending `check_docs_content_policy.py`'s detection rules.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260920-170036 | 20260920-170036 |  |
| 2 | Add or update tests per Validation plan | Completed | 20260920-170036 | 20260920-170036 | N/A: documentation-only, no automated test beyond the doc checkers already listed |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260920-170036 | 20260920-170036 | Scoped to the doc checkers in Validation plan, not the full Python toolchain (no `scripts/` change) |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260920-170036 | 20260920-170036 | N/A: this document IS the documentation change |

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
- **Requirement ID**: `REQ-001` — replace the Error Classification Table with a canonical-source pointer
- **Source issue**: issues/20260920-154352_dcp010_mcp-docs-content-policy-cleanup-batch-2.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260920-160121_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260920-162636
- **Related target files**: docs/04_mcp_02_03_audit-logging-and-errors.md