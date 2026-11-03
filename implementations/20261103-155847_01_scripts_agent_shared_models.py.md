## Goal

Correct the `ToolExecEvent.idempotency_key` field comment in `scripts/agent/shared/models.py` so it states that the value is the workflow-scoped logical-call identity (`workflow_id:task_id:turn_id:call_id`) recorded for the audit log and is distinct from the transport `X-Idempotency-Key` used for server-side deduplication (`REQ-001`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- **A1**: The audit key's composition (`workflow_id:task_id:turn_id:call_id`) is intentionally kept separate from the transport key per `toolstate001` REQ-009; this document describes that decision and does not reopen it.
- **A2**: No consumer reads `ToolExecEvent.idempotency_key` back (`context.py`'s recorder consumes a different key for `tool_call_state`), so correcting the comment cannot regress behavior.

## Design decisions
- **DD-1 — What the comment states.** The comment names the logical-call identity plus its distinctness from the transport `X-Idempotency-Key`, matching the two-key model in `toolstate001` (REQ-003/D3, REQ-009). This fully resolves the mislabel rather than leaving a bare "not a dedup key" statement.

## Alternatives considered
- Minimal fix: remove only the wrong "for deduplication" phrase and leave the comment generic. Rejected: it would still not tell a reader what the value actually is or that it differs from the transport key.

## Implementation
### Target file
`scripts/agent/shared/models.py`

### Procedure
Edit the `idempotency_key` field comment on the `ToolExecEvent` dataclass (currently `scripts/agent/shared/models.py:61`) from a dedup label to a description of the audit-side logical-call identity.

### Method
Replace the trailing comment on the field definition:
```python
idempotency_key: str = ""  # stable, retry-invariant key for deduplication
```
with:
```python
idempotency_key: str = ""  # workflow-scoped logical-call identity (workflow_id:task_id:turn_id:call_id) recorded for the audit log; distinct from the transport X-Idempotency-Key used for server-side deduplication
```
Change only the comment text after `= ""`. Do not touch the field type, default, or any other line.

### Details
- The value written here comes from `tool_runner.py::_idempotency_key` (`:133-141`) → `audit_tool_exec(..., idempotency_key=...)` (`:273-284`); it is never consumed for deduplication. The transport `X-Idempotency-Key` (derived in `http_transport.py::derive_idempotency_key` `:62`, emitted `:193-203`) is the dedup key and is what this comment now distinguishes itself from.
- Keep the comment on the same line as the field definition; do not split it into a multi-line block.

## Compatibility considerations
Comment-only change; no runtime, API, or serialization impact.

## Security considerations
N/A: the change rewording a field comment; it does not alter how the key is derived, stored, or compared.

## Rollback considerations
N/A: revert the comment edit.

## Validation plan
- Comment review: confirm the field comment at `scripts/agent/shared/models.py:61` now states the logical-call identity and its distinction from the transport `X-Idempotency-Key`.
- Existing audit tests stay green: `uv run pytest tests/agent/test_tool_runner.py`.

## Completion criteria
- The `idempotency_key` field comment no longer labels the value as a dedup key.
- The comment states the value is the workflow-scoped logical-call identity (`workflow_id:task_id:turn_id:call_id`) recorded for the audit log and distinct from the transport `X-Idempotency-Key`.
- The field definition itself (type, default) is unchanged and existing audit tests pass.

## Out of Scope
- Changing which key the audit event records (stays `workflow_id:task_id:turn_id:call_id` per `toolstate001` REQ-009).
- Any change to the transport `X-Idempotency-Key` derivation/emission or the `tool_call_state` key.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Correct the `ToolExecEvent.idempotency_key` field comment in `scripts/agent/shared/models.py` | Completed | 20261103 | 20261103 | comment-only; no behavior change |
| 2 | Add or update tests per Validation plan | Completed | 20261103 | 20261103 | N/A: comment-only, no new tests |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261103 | 20261103 | ruff/mypy clean; existing audit tests pass unchanged |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261103 | 20261103 | N/A |

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
- **Requirement ID**: `REQ-001` — correct the `ToolExecEvent.idempotency_key` field comment to state the audit-side logical-call identity and its distinction from the transport `X-Idempotency-Key`
- **Source issue**: `issues/20261101-073823_idemaudit001_audit-idempotency-key-mismatch.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261101-165600_idemaudit001_audit-idempotency-key-mismatch.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261103-155847
- **Related target files**: `scripts/agent/shared/models.py`
