## Goal
- Record the dry-run/real-deletion authorization parity, the intent-audit order, and the `supported_extensions` removal in the file-write/file-delete documentation section (REQ-004, REQ-005, REQ-006, REQ-008, AC-3, AC-4, AC-6).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: the file-write and file-delete sections of `docs/22_mcp/mcp_04_02_file-write-file-delete-shell.md` — add the dry-run parity, intent-audit-before-delete with fail-closed, `applied_audit_failed`, and the removal of the `supported_extensions` control.
- Out of scope: the final consistency sweep of this document, which remains mcpai012's work (Plan Assumptions, judged compatible); the implementation (seq 03, 09, 10, 11, 12, 13).

## Assumptions
- Verified in Step 2: the postcondition and root-protection sections (lines 28-32) describe root protection without dry-run parity or audit order.
- Overlap with mcpai012 on this file is judged compatible: this document records the facts this Plan establishes; mcpai012 sweeps afterward.
- Documentation is written in English per `skills/DESIGN.md` Output language.

## Design decisions
- The delete section states the order as behavior: the allowed-root guard runs before the dry-run branch, the intent audit is written before the destructive operation and fails closed, and a completion-audit failure after an applied delete is reported as `applied_audit_failed`.
- The write section drops the `supported_extensions` statement since the control is removed by owner decision (20261126).
- Only the task-scope section mapped in `docs/00_index.md` is edited.

## Alternatives considered
- N/A: documentation row with no design decision of its own.

## Implementation
### Target file
`docs/22_mcp/mcp_04_02_file-write-file-delete-shell.md`

### Procedure
1. In the file-delete section, add the dry-run parity and the intent-audit order with fail-closed and `applied_audit_failed` behavior.
2. In the file-write section, remove or correct the `supported_extensions` statement.

### Method
- Match the existing section style (short policy statements with the enforcing function names).

### Details
- Audit-record identifiers (session, request, logical-call) are stated in the same section per REQ-005.

## Compatibility considerations
- N/A: documentation only; the facts describe behavior established by seq 09, 10.

## Security considerations
- N/A: no secrets; the policy statements document the audit-order closure.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_quality.py` (structural/formatting rules per `rules/tool-gates.md`); docs consistency checker per the same table.

## Completion criteria
- The sections record dry-run parity, audit order, and the removal; the docs checkers pass (AC-6).

## Out of Scope
- The consistency sweep reserved to mcpai012; implementation (seq 03, 09-13).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Run the docs checkers (`rules/tool-gates.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-004` (dry-run parity), `REQ-005` (audit order), `REQ-006` (`supported_extensions` removal), `REQ-008` (documentation records the facts this Plan establishes)
- **Source issue**: issues/20261119-140516_mcpai009_file-mcp-hardening.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261126-065258_mcpai009_file-mcp-hardening.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-171048
- **Related target files**: `docs/22_mcp/mcp_04_02_file-write-file-delete-shell.md`
