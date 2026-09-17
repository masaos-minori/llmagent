## Goal

Populate both new fields (`idempotency_key` and the task-linkage field) in `audit_tool_exec()` alongside the existing `mcp_request_id`.

## Scope

- Populate the new `ToolExecEvent` fields in `audit_tool_exec()` in `scripts/agent/tool_audit.py`
- No other files are modified in this row

## Assumptions

- The caller (`execute_one_tool_call()`) passes the new idempotency key as a parameter to `audit_tool_exec()` (covered by REQ-001).
- The task-linkage value comes from `ctx.workflow.current_task_id` (see UNK-02 for the attempt-level gap).
- Both fields have default values (`""`) so callers that do not yet supply them get today's unguarded behavior (no regression).

## Design decisions

- Adding the new fields to `audit_tool_exec()`'s signature rather than deriving them internally: this keeps the function's responsibility focused on audit logging and lets the caller control the key derivation logic.
- Using `ctx.workflow.current_task_id` as the first-increment linkage target for REQ-002: true attempt-level linkage is deferred to a follow-up once `attempt_id` is exposed on `AgentContext`.

## Alternatives considered

- Deriving the task-linkage internally in `audit_tool_exec()` — rejected: would duplicate the key derivation logic from `execute_one_tool_call()`; better to keep it centralized in the caller.

## Implementation

### Target file

`scripts/agent/tool_audit.py`

### Procedure

Populate the new `ToolExecEvent` fields in `audit_tool_exec()`.

### Method

1. Re-verify, immediately before editing, that each target row's cited line/content is unchanged since this Plan's evidence-gathering (per `rules/workflow-lifecycle.md` Revalidation): `scripts/agent/tool_audit.py` lines 161, 181-198.
2. Add `idempotency_key: str = ""` parameter to `audit_tool_exec()`.
3. Add the task-linkage parameter to `audit_tool_exec()` (name resolved at implementation time).
4. Pass both new fields into `ToolExecEvent(...)` construction.

### Details

```python
# Lines 161-198: add the two new parameters and pass them to ToolExecEvent:
# Before:
def audit_tool_exec(
    ctx: AgentContext,
    tool_name: str,
    args: dict,
    is_error: bool,
    mcp_request_id: str,
    error_type: str = "",
    artifact_uri: str | None = None,
    source: str = "",
) -> None:
    """Write a tool_exec event with mcp_request_id to the audit log."""
    if ctx.services_required.audit_logger is None:
        return
    if not mcp_request_id and not source:
        return
    assert ctx.workflow.workflow_id, (
        "workflow_id required: audit_tool_exec called outside workflow context"
    )
    masked = mask_args(args, ctx.cfg.tool.masked_fields)
    resource_scope = _extract_resource_scope(ctx, masked)
    evt = ToolExecEvent(
        event="tool_exec",
        task_id=ctx.turn.current_turn_id or "",
        tool=tool_name,
        operation_type=classify_operation_type(
            tool_name, ctx.services_required.runtime_tools
        ),
        resource_scope=resource_scope,
        mcp_request_id=mcp_request_id,
        is_error=is_error,
        args_preview=masked,
        ts=time.time(),
        source=source if source else "agent",
        error_type=error_type,
        workflow_id=ctx.workflow.workflow_id,
        session_id=str(ctx.session.session_id) if ctx.session.session_id else "",
        artifact_uri=artifact_uri,
    )
    ctx.services_required.audit_logger.info(_json_dumps(dataclasses.asdict(evt)))

# After:
def audit_tool_exec(
    ctx: AgentContext,
    tool_name: str,
    args: dict,
    is_error: bool,
    mcp_request_id: str,
    error_type: str = "",
    artifact_uri: str | None = None,
    source: str = "",
    idempotency_key: str = "",  # NEW: stable, retry-invariant key for deduplication
    task_linkage: str = "",     # NEW: WorkflowEngine task-level linkage (current_task_id)
) -> None:
    """Write a tool_exec event with mcp_request_id to the audit log."""
    if ctx.services_required.audit_logger is None:
        return
    if not mcp_request_id and not source:
        return
    assert ctx.workflow.workflow_id, (
        "workflow_id required: audit_tool_exec called outside workflow context"
    )
    masked = mask_args(args, ctx.cfg.tool.masked_fields)
    resource_scope = _extract_resource_scope(ctx, masked)
    evt = ToolExecEvent(
        event="tool_exec",
        task_id=ctx.turn.current_turn_id or "",
        tool=tool_name,
        operation_type=classify_operation_type(
            tool_name, ctx.services_required.runtime_tools
        ),
        resource_scope=resource_scope,
        mcp_request_id=mcp_request_id,
        is_error=is_error,
        args_preview=masked,
        ts=time.time(),
        source=source if source else "agent",
        error_type=error_type,
        workflow_id=ctx.workflow.workflow_id,
        session_id=str(ctx.session.session_id) if ctx.session.session_id else "",
        artifact_uri=artifact_uri,
        idempotency_key=idempotency_key,   # NEW: pass the derived key
        task_linkage=task_linkage,          # NEW: pass the task linkage
    )
    ctx.services_required.audit_logger.info(_json_dumps(dataclasses.asdict(evt)))
```

## Compatibility considerations

- Both new parameters have default values (`""`) so existing callers continue to work without modification.
- The `ToolExecEvent` dataclass must be updated first (separate row) before this row can be implemented.

## Security considerations

- No security impact. This is adding new fields to an audit event, not changing any security boundary.

## Rollback considerations

- Reverting this change restores the original `audit_tool_exec()` signature and `ToolExecEvent` construction without the new fields. If needed later, the fields should be reimplemented to match the canonical exclude-and-FATAL duplicate-ownership policy from `McpToolDiscoveryService._dedupe_and_build()`.

## Validation plan

- Unit: run `uv run pytest tests/agent/test_tool_audit.py tests/agent/test_audit_log_format.py -q` to confirm no failures introduced, including new field-population tests (AC-2, AC-4).
- Static analysis: `uv run ruff check scripts/agent/tool_audit.py`, `uv run mypy scripts/agent/tool_audit.py`.
- Import lint: `PYTHONPATH=scripts uv run lint-imports` to confirm no broken contracts introduced.

## Completion criteria

- `audit_tool_exec()` accepts the new `idempotency_key` parameter (default `""`).
- `audit_tool_exec()` accepts the new task-linkage parameter (default `""`).
- Both new fields are passed into `ToolExecEvent(...)` construction alongside the existing `mcp_request_id` (AC-2).
- All existing tests in `tests/agent/test_tool_audit.py` and `tests/agent/test_audit_log_format.py` continue to pass without modification (AC-4).
- No new lint/type errors introduced.

## Out of scope

- Changes to `scripts/agent/tool_runner.py` — covered by separate row (REQ-001).
- Changes to `scripts/agent/shared/models.py` — covered by separate row (REQ-002).
- Changes to `scripts/mcp_servers/dispatch.py` — covered by separate row (REQ-003).
- Changes to `scripts/mcp_servers/server.py` — covered by separate row (REQ-004).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add idempotency_key parameter to audit_tool_exec() | Completed | 20260917-214310 | 20260917-214310 |  |
| 2 | Add task-linkage parameter to audit_tool_exec() | Completed | 20260917-214310 | 20260917-214310 |  |
| 3 | Pass both new fields into ToolExecEvent(...) | Completed | 20260917-214310 | 20260917-214310 |  |
| 4 | Run the validation sequence (rules/toolchain.md) | Completed | 20260917-214310 | 20260917-214310 |  |

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
- **Requirement ID**: REQ-002
- **Source issue**: issues/20260914-123621_arch02_tool-call-execution-id-idempotency-guard-missing.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260916-135754_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260916-232730
- **Related target files**: scripts/agent/tool_audit.py