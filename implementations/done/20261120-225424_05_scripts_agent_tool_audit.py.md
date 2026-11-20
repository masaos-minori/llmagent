## Goal

Record the logical call id in every tool-exec audit event and make the audit record mandatory (raising) for side-effecting calls while keeping read-only best-effort (`REQ-007` mandatory audit, `REQ-008` logical id in audit).

## Scope
**Release unit**: contract-chain (logical-id field, Phase 2). The mandatory-audit change (Phase 5) lands in unit auth-intent.

## Assumptions
- `ToolExecEvent`'s `idempotency_key` field name stays; its value becomes the logical call id (row 8 updates the comment).
- Side-effect classification for the mandatory rule uses `classify_operation_type` / `ALL_SIDE_EFFECTING_TOOLS` semantics already used at :212-213.

## Design decisions
- In `audit_tool_exec`, the silent skip `if ctx.services_required.audit_logger is None: return` (:198-199) and the no-id/no-source skip (:200-201) become raises for side-effecting calls; read-only calls keep returning silently.
- The `idempotency_key: str = ""` parameter (:188) is filled from the logical call id by callers; for side-effecting calls an empty value is an error, not a default.
- The `_workflow_id_or_skip` path (:202-204): side-effecting calls missing a workflow id raise under the same fail-closed rule.
- Citation fixes (verified 2026-11-20): event construction is at :207-226; the silent-skip gap spans :198-204.

## Alternatives considered
- Logging an error but still executing: rejected — REQ-007/AC-5 require the side effect itself to be rejected when the audit record cannot be written.

## Implementation
### Target file
`scripts/agent/tool_audit.py`

### Procedure
Introduce a raising variant of the skip conditions in `audit_tool_exec` (:198-204) gated on the side-effect class; keep the existing event construction (:207-226) otherwise unchanged.

### Method
Classify once inside `audit_tool_exec` via `classify_operation_type` (already invoked for the event), then branch return vs raise.

### Details
- Keep `dedup_state`/`artifact_uri` behavior untouched.
- Callers (`tool_runner` row 4, gateway audit) must treat the new exception as a denial.

### Companion test files
- `tests/agent/test_tool_audit.py`
  - Procedure: add cases — side-effecting call with `audit_logger is None` raises; read-only call with missing logger still returns silently; logical id lands in the event.
  - Validation: `uv run pytest tests/agent/test_tool_audit.py` passes.

## Compatibility considerations
`audit_approval` and the denied-event path (`_ERROR_TYPE_DENIED`) keep their current skip behavior.

## Security considerations
Mandatory audit closes the current silent-skip gap (:198-204) for side effects; audit content stays masked (`mask_args`, `args_preview`).

## Rollback considerations
N/A: revert the commit.

## Validation plan
`uv run pytest tests/agent/test_tool_audit.py tests/agent/test_audit_log_format.py` — mandatory for side effects, best-effort for read-only, logical id present.

## Completion criteria
No side-effecting call can complete without an audit event carrying the logical call id; all skip paths for side-effecting calls raise instead of silently returning.

## Out of Scope
Audit event model fields (row 8); caller-side denial handling (row 4).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 2026-11-21 | 2026-11-21 | Deviation: the mandatory gate is an explicit `_MANDATORY_AUDIT_OP_TYPES` = {WRITE, DELETE, EXECUTE, API_WRITE}; UNKNOWN (registry-less unclassified tool) stays best-effort because dispatch already rejects unregistered tools. Also: the empty-`idempotency_key` and `_workflow_id_or_skip` skip paths raise for mandatory calls; `AuditUnavailableError` docstring rewritten (was "not raised"). |
| 2 | Add or update tests per Validation plan | Completed | 2026-11-21 | 2026-11-21 | `TestMandatoryAuditForSideEffects` added (raise on missing logger/identity/logical-id/workflow-id; read-only + denied path stay silent). Existing `audit_tool_exec` pins pass `idempotency_key=_CALL_ID`; `_make_ctx` pins `runtime_tools=None`, `_read_registry()` gives explicit READ classification. Companion fix in `tests/agent/test_tool_runner.py`: `_make_ctx` audit_logger is now a MagicMock (REQ-007 fail-closed), and two `TestAttemptSideEffectFlag` gateway fixtures pin `executor.execute` return values (audit now serializes the result fields). |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-11-21 | 2026-11-21 | ruff clean; mypy scripts/ clean (445 files); lint-imports 6 kept; tests/agent + tests/shared: 5786 passed, 3 skipped. `tests/agent/test_audit_log_format.py` (row 22) landed alongside as the companion test row. |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 2026-11-21 | N/A: docs sweep owned by mcpai012 |

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
- **Requirement ID**: `REQ-007`, `REQ-008`
- **Source issue**: `issues/20261120-115840_mcpdl001_approval-grant-intent.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261120-222144_mcpdl001_approval-grant-intent.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261120-225424
- **Related target files**: `scripts/agent/tool_audit.py`, `tests/agent/test_tool_audit.py`
