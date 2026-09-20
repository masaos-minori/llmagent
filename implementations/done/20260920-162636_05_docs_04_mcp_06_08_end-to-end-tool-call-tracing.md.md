## Goal
Replace `docs/04_mcp_06_08_end-to-end-tool-call-tracing.md`'s `error_type`
meaning/example-cause table (lines 37-41) with a pointer to
`scripts/agent/tool_audit.py`'s audit-event emitter, per `REQ-005` (Plan
`plans/20260920-160121_plan.md`), so `tools/check_docs_content_policy.py` reports no
finding at this table's location while the "Regarding cross-layer correlation" prose
above it is preserved.

## Scope
In scope: the `error_type` table (lines 37-41) only. Out of scope: the numbered tracing
steps (lines 12-27), the "Regarding cross-layer correlation" prose (line 33), the
example audit log line and filter commands (lines 43-55), "## Per-Server Error
Counters" (lines 57-68), "## Detecting Repeated Failures" (lines 70-78), and "##
Serialization of Side Effects" (lines 82-104) — none of these were flagged by
`check_docs_content_policy.py` (re-confirmed 2026-09-20).

## Assumptions
The finding at line 37 and the file's exact current content (re-verified via Read
during this document's creation) have not shifted since the Plan was frozen — no
commit has touched this file or `scripts/agent/tool_audit.py` since.

## Design decisions
Replace the table with a pointer to `scripts/agent/tool_audit.py` (confirmed to define
the `error_type` field and its assignment at lines 167 and 196) as the canonical source
for the exact `error_type` values and when each is set, immediately following the
unchanged line 33 "Regarding cross-layer correlation" sentence and the unchanged line
35 lead-in sentence.

## Alternatives considered
- Remove the table and the line 35 lead-in sentence together: rejected — the lead-in
  sentence ("The agent-side audit event includes an `error_type` field:") is a
  transition, not a restatement of the table's values; removing it would leave the
  pointer sentence dangling with no context.
- Keep the table with only the `Example Cause` column removed: rejected — the
  remaining `| error_type | Meaning |` shape still restates code-derivable
  meaning-per-value data and would likely still match the same detection pattern.

## Implementation
### Target file
`docs/04_mcp_06_08_end-to-end-tool-call-tracing.md`

### Procedure
1. Read lines 31-42 to confirm current content matches the Plan's recorded evidence.
2. Replace lines 37-41 (the table header through the `_(empty)_` row) with one sentence
   pointing to `scripts/agent/tool_audit.py` as the canonical source for the exact
   `error_type` values (`transport`, `tool`, empty) and when each is set.
3. Leave line 33 (the "Regarding cross-layer correlation" prose), line 35 (the lead-in
   sentence), and every other section of this file unchanged.

### Method
Single localized `Edit`, replacing exactly the table (lines 37-41) with the pointer
sentence from Procedure step 2. Do not touch line 33, line 35, or any content outside
this range.

### Details
Do not restate the three `error_type` values' meanings or example causes (`transport` /
network failure or crash; `tool` / validation failure or DB constraint violation;
empty / success) — all are directly readable from `scripts/agent/tool_audit.py`'s
`error_type` assignment logic. Retain line 33's correlation-strategy explanation
verbatim — it is unrelated design intent about which log is authoritative for
cross-layer correlation, not part of the flagged table.

## Compatibility considerations
`N/A: documentation-only change, no code, public interface, or data format is affected`.

## Security considerations
`N/A: no security-relevant content is touched`.

## Rollback considerations
Revert via `git checkout` on this one file. The edit is independently revertable from
the other four Plan rows' files.

## Validation plan
- `uv run python tools/check_docs_content_policy.py` — confirm zero findings for
  `docs/04_mcp_06_08_end-to-end-tool-call-tracing.md` (Plan `AC-5`).
- `uv run python tools/check_docs_quality.py`, scoped to this file — confirm no new
  warning is introduced.
- `uv run python tools/check_docs_structure.py docs/04_mcp_06_08_end-to-end-tool-call-tracing.md`
  — confirm it passes (this file had no pre-existing `check_docs_structure.py` finding
  recorded in the Plan).
- `uv run python tools/check_docs_consistency.py --domain mcp` — confirm no new drift
  finding.

## Completion criteria
The `error_type` table is replaced by a canonical-source pointer to
`scripts/agent/tool_audit.py`; the "Regarding cross-layer correlation" prose and the
lead-in sentence are unchanged; `check_docs_content_policy.py` reports zero findings
for this file.

## Out of scope
- Every other section of this file (see Scope) — not flagged, not part of `REQ-005`.
- Any other `docs/*.md` file — this is the last of the Plan's five target-file rows.
- Extending `check_docs_content_policy.py`'s detection rules.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260920-170525 | 20260920-170525 |  |
| 2 | Add or update tests per Validation plan | Completed | 20260920-170525 | 20260920-170525 | N/A: documentation-only, no automated test beyond the doc checkers already listed |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260920-170525 | 20260920-170525 | Scoped to the doc checkers in Validation plan, not the full Python toolchain (no `scripts/` change) |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260920-170525 | 20260920-170525 | N/A: this document IS the documentation change |

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
- **Requirement ID**: `REQ-005` — replace the `error_type` table with a canonical-source pointer
- **Source issue**: issues/20260920-154352_dcp010_mcp-docs-content-policy-cleanup-batch-2.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260920-160121_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260920-162636
- **Related target files**: docs/04_mcp_06_08_end-to-end-tool-call-tracing.md