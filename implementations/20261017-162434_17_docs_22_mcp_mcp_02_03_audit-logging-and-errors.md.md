## Goal

Document the `requested_target` field and the approval-correlation join path in
`docs/22_mcp/mcp_02_03_audit-logging-and-errors.md`, and correct the two places that state file-write-mcp
writes no audit log and file-delete-mcp writes only its dedicated log (REQ-003, REQ-010, AC-003, AC-010).

## Scope

- Add a `requested_target` row to the field table.
- Update the server list in the opening paragraph and the Note below the table.
- Add a short correlation subsection that states how an audit record joins to the agent-side approval
  record.
- Update the `outcome` row so `"rejected"` is no longer described as git-mcp only.

## Assumptions

- The field semantics are exactly the ones Plan row 1 implements: `NotRequired[str]`, emitted only when
  the caller supplies a non-empty value, and redacted by the caller.
- The correlation join is the pair `session_id` plus `request_id`, which the agent-side `tool_exec`
  record also carries; no new correlation key is introduced.

## Design decisions

- Keep `canonical_target`'s row wording and mirror it for `requested_target`, so the pair reads as
  requested form and resolved form of the same resource rather than as two unrelated optional fields.
- State the file servers' target convention in the existing `target` row rather than adding a new row,
  because the truncation convention is already documented there.

## Alternatives considered

- Document the correlation in `docs/22_mcp/mcp_06_05_reading-audit-logs.md` instead: rejected — the Plan's
  frozen target row names this file, and the field table that AC-003 requires lives here.

## Implementation

### Target file

`docs/22_mcp/mcp_02_03_audit-logging-and-errors.md`

### Procedure

1. Insert a `requested_target` row immediately above the `canonical_target` row in the field table.
2. Rewrite the opening paragraph's server list so file-write-mcp and file-delete-mcp are listed as
   servers that write the shared audit log.
3. Rewrite the Note so it no longer states that file-write-mcp writes no audit log, and so file-delete-mcp
   is described as writing both.
4. Extend the `outcome` row so `"rejected"` names the file servers as well as git-mcp.
5. Add a `### Approval correlation` subsection after the Note.

### Method

Replace sentences in place; keep the table shape, the existing field names, and the document's existing
terminology.

### Details

- The field table is `docs/22_mcp/mcp_02_03_audit-logging-and-errors.md:29-40`; `canonical_target` is at
  `docs/22_mcp/mcp_02_03_audit-logging-and-errors.md:38`.
- New row shape: `requested_target` | Caller-supplied resource path as received, before resolution;
  emitted by git-mcp and, for rejected calls, by file-write-mcp and file-delete-mcp | No | Omitted.
- The opening paragraph is `docs/22_mcp/mcp_02_03_audit-logging-and-errors.md:22` and the Note is
  `docs/22_mcp/mcp_02_03_audit-logging-and-errors.md:42`.
- Correlation subsection: state that `session_id` and `request_id` are the join keys to the agent-side
  `tool_exec` record, that a rejected call is joined the same way as an accepted one, and that the
  dedicated plain-text logs carry no correlation fields, so correlation runs through the shared and
  agent-side JSON-lines logs.

## Compatibility considerations

- `docs/22_mcp/mcp_06_05_reading-audit-logs.md` describes how to read these logs; its server list must be
  checked for the same stale claim, and it is not a Plan target file, so report any stale claim there
  rather than editing it in this row.
- The example record line in the code block stays as a minimal record, because optional keys are omitted
  when not supplied.

## Security considerations

- The document states that the field carries the caller-supplied form and that redaction is the caller's
  responsibility, so no reader concludes that the value is normalized or safe to display.

## Rollback considerations

N/A: revert the commit. A rollback leaves the audit documentation describing a field that is not emitted.

## Validation plan

- `uv run python tools/check_docs_quality.py`
- `uv run python tools/check_known_deviation_sync.py`
- `uv run python tools/check_workitem_structure.py --file implementations/20261017-162434_17_docs_22_mcp_mcp_02_03_audit-logging-and-errors.md.md`

## Completion criteria

- The field table contains a `requested_target` row with its presence and omission rules (AC-003).
- No sentence in this file still states that file-write-mcp writes no audit log or that file-delete-mcp
  writes only a dedicated log (AC-001, AC-009).
- A stated join path from an MCP audit record to the agent-side approval record exists (AC-010).
- The docs checkers report no findings for this file.

## Out of scope

- Changing any audit code.
- Editing `docs/22_mcp/mcp_06_05_reading-audit-logs.md`, which is not a Plan target file.
- Documenting the swapped request-context binding in the five servers that bind it in the wrong order.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the `requested_target` field row | Pending | — | — | REQ-003 |
| 2 | Update the server list, the Note, and the outcome row | Pending | — | — | REQ-001, REQ-002 |
| 3 | Add the approval-correlation subsection | Pending | — | — | REQ-010 |
| 4 | Run the docs checkers | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

## Work Items Created

- None.

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-003, REQ-010
- **Source issue**: `issues/20261017-115004_mcp006_implement-missing-guard-layers-for-high-risk-tool-categories.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261017-160222_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261017-162434
- **Related target files**: `docs/22_mcp/mcp_02_03_audit-logging-and-errors.md`
