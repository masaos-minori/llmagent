## Goal

Add `ToolExecEvent.idempotency_key: str` and a WorkflowEngine task-linkage field populated from `ctx.workflow.current_task_id` (see UNK-02 for the attempt-level gap); extend the dataclass schema to support the new idempotency key and task linkage.

## Scope

- Add `idempotency_key: str` field to `ToolExecEvent` in `scripts/agent/shared/models.py`
- Add a WorkflowEngine task-linkage field to `ToolExecEvent` in `scripts/agent/shared/models.py`
- No other files are modified in this row

## Assumptions

- The exact name of the task-linkage field (e.g. `task_linkage`, `engine_task_id`) is resolved at implementation time against the concrete `AgentContext` fields identified in this Plan's Problem section.
- The `idempotency_key` field should have a default value of `""` to maintain backward compatibility with existing callers that do not yet supply the key.
- The task-linkage field should also have a default value of `""` to maintain backward compatibility.
- `ctx.workflow.current_task_id` is an acceptable first-increment linkage target for REQ-002 (see UNK-02): true attempt-level linkage is deferred to a follow-up once `attempt_id` is exposed on `AgentContext`.

## Design decisions

- Adding both fields as optional (default `""`) rather than required: this allows gradual adoption — callers that do not yet supply the key get today's unguarded behavior (no regression), while callers that do supply it get the new protection.
- Using `ctx.workflow.current_task_id` as the first-increment linkage target for REQ-002: true attempt-level linkage is deferred to a follow-up once `attempt_id` is exposed on `AgentContext`.

## Alternatives considered

- Making both fields required — rejected: would break all existing callers that do not yet supply these values; opt-in defaults allow incremental rollout without breaking changes.
- Deriving the task-linkage from `attempts.attempt_id` instead of `current_task_id` — rejected: `attempt_id` is not currently exposed on `AgentContext` (confirmed via `scripts/agent/context.py`); exposing it would touch a file outside this Plan's frozen scope.

## Implementation

### Target file

`scripts/agent/shared/models.py`

### Procedure

Add `idempotency_key` and the task-linkage field to `ToolExecEvent`.

### Method

1. Re-verify, immediately before editing, that each target row's cited line/content is unchanged since this Plan's evidence-gathering (per `rules/workflow-lifecycle.md` Revalidation): `scripts/agent/shared/models.py` lines 45, 49, 53, 59.
2. Add `idempotency_key: str = ""` field to `ToolExecEvent`.
3. Add the task-linkage field to `ToolExecEvent` (name resolved at implementation time).

### Details

```python
# Lines 45-61: add the two new fields:
# Before:
@dataclass(frozen=True)
class ToolExecEvent:
    """Structured audit event for tool_exec log entries."""

    event: Literal["tool_exec"]
    task_id: str
    tool: str
    operation_type: str
    resource_scope: dict[str, str]
    mcp_request_id: str
    is_error: bool
    args_preview: dict[str, object]
    ts: float
    source: str = "agent"
    error_type: str = ""  # "transport" | "tool" | "" (empty on success)
    workflow_id: str = ""
    session_id: str = ""
    artifact_uri: str | None = None

# After:
@dataclass(frozen=True)
class ToolExecEvent:
    """Structured audit event for tool_exec log entries."""

    event: Literal["tool_exec"]
    task_id: str
    tool: str
    operation_type: str
    resource_scope: dict[str, str]
    mcp_request_id: str
    is_error: bool
    args_preview: dict[str, object]
    ts: float
    source: str = "agent"
    error_type: str = ""  # "transport" | "tool" | "" (empty on success)
    workflow_id: str = ""
    session_id: str = ""
    artifact_uri: str | None = None
    idempotency_key: str = ""  # NEW: stable, retry-invariant key for deduplication
    task_linkage: str = ""   # NEW: WorkflowEngine task-level linkage (current_task_id)
```

## Compatibility considerations

- Both new fields have default values (`""`) so existing callers that do not yet supply them continue to work without modification.
- The dataclass is frozen — adding fields must be done carefully to avoid breaking positional construction patterns.

## Security considerations

- No security impact. This is adding new fields to an audit event dataclass, not changing any security boundary.

## Rollback considerations

- Reverting this change restores the original `ToolExecEvent` schema without the new fields. If needed later, the fields should be reimplemented to match the canonical exclude-and-FATAL duplicate-ownership policy from `McpToolDiscoveryService._dedupe_and_build()`.

## Validation plan

- Unit: run `uv run pytest tests/agent/test_tool_audit.py tests/agent/test_audit_log_format.py -q` to confirm no failures introduced, including new field-population tests (AC-2, AC-4).
- Static analysis: `uv run ruff check scripts/agent/shared/models.py`, `uv run mypy scripts/agent/shared/models.py`.
- Import lint: `PYTHONPATH=scripts uv run lint-imports` to confirm no broken contracts introduced.

## Completion criteria

- `ToolExecEvent` contains the new `idempotency_key` field alongside the existing `mcp_request_id` (AC-2).
- `ToolExecEvent` contains the new task-linkage field alongside the existing `mcp_request_id` (AC-2).
- All existing tests in `tests/agent/test_tool_audit.py` and `tests/agent/test_audit_log_format.py` continue to pass without modification (AC-4).
- No new lint/type errors introduced.

## Out of scope

- Changes to `scripts/agent/tool_runner.py` — covered by separate row (REQ-001).
- Changes to `scripts/agent/tool_audit.py` — covered by separate row (REQ-002).
- Changes to `scripts/mcp_servers/dispatch.py` — covered by separate row (REQ-003).
- Changes to `scripts/mcp_servers/server.py` — covered by separate row (REQ-004).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add idempotency_key field to ToolExecEvent | Completed | 20260917-214212 | 20260917-214212 |  |
| 2 | Add task-linkage field to ToolExecEvent | Completed | 20260917-214212 | 20260917-214212 |  |
| 3 | Run the validation sequence (rules/toolchain.md) | Completed | 20260917-214212 | 20260917-214212 |  |

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
- **Related target files**: scripts/agent/shared/models.py