## Goal

Re-point the audit event identity fields to the logical call id and define the `ApprovalGrant` model (`REQ-006` grant model, `REQ-008` audit identity).

## Scope
**Release unit**: contract-chain (event field semantics, Phase 2). The `ApprovalGrant` dataclass (Phase 4) lands in unit auth-intent.

## Assumptions
- The persisted column/field name `idempotency_key` is kept on `ToolExecEvent`; only its value semantics change to the opaque logical call id (no audit-log schema rename in this Plan).

## Design decisions
- Replace the `idempotency_key` comment block on `ToolExecEvent` (:48-50, currently "nothing deduplicates on this value" with the composite-key description) with the opaque uuid7 logical-call-id contract.
- Add `idempotency_key: str = ""` to `ToolApprovalEvent` (:13-26) so approval and execution events carry the same logical call id (AC-2).
- Define `ApprovalGrant` (new) as a frozen dataclass in this module: `tool`, `args_hash`, `mode`, `issued_at` (new), `expires_at` (new); single-use is enforced by the gateway consumer (row 3), not by the model.

## Alternatives considered
- Renaming the event field to `call_id`: rejected — the audit-log format tests and any log consumers pin `idempotency_key`; a rename widens the diff without benefit (row 22 pins the format).

## Implementation
### Target file
`scripts/agent/shared/models.py`

### Procedure
Update `ToolExecEvent`'s comment (:45-50), add the field to `ToolApprovalEvent`, and append the `ApprovalGrant` (new) dataclass.

### Method
Field/comment additions only; existing constructors gain defaults, so all call sites keep compiling.

### Details
- `args_hash` is hex sha256 of canonical-JSON args; computed by `tool_approval` (row 2).
- Types stay stdlib-only (`dataclasses`, `typing`) to keep this module import-light.

## Compatibility considerations
Old audit lines keep their stored values; only new events carry the uuid7 id. Row 22 updates the format pins.

## Security considerations
The grant model carries no secrets; the args hash is a commitment, not the args themselves.

## Rollback considerations
N/A: revert the commit.

## Validation plan
`uv run pytest tests/agent/test_audit_log_format.py && uv run mypy scripts/` — field contract intact, model importable.

## Completion criteria
Approval and exec audit events carry the same logical call id field; `ApprovalGrant` is importable from `agent.shared.models` with the fields rows 2-3 rely on.

## Out of Scope
Grant issuance (row 2); grant verification (row 3).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | Docs sweep owned by mcpai012 |

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
- **Requirement ID**: `REQ-006`, `REQ-008`
- **Source issue**: `issues/20261120-115840_mcpdl001_approval-grant-intent.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261120-222144_mcpdl001_approval-grant-intent.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261120-225424
- **Related target files**: `scripts/agent/shared/models.py`
