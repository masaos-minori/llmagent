## Goal

Derive a stable, retry-invariant idempotency key per Tool Call from `ctx.workflow.workflow_id`, `ctx.workflow.current_task_id`, `ctx.turn.current_turn_id`, and a per-call sequence discriminator (exact composition resolved at implementation time, per UNK-01); keep the existing per-HTTP-request trace ID unchanged; pass the new key into `audit_tool_exec()`.

## Scope

- Derive the stable idempotency key in `execute_one_tool_call()` in `scripts/agent/tool_runner.py`
- Pass the new key into `audit_tool_exec()` alongside the existing `result.request_id`
- No other files are modified in this row

## Assumptions

- The exact composition of the stable idempotency key (e.g. `{workflow_id}:{task_id}:{turn_id}:{sequence}` vs. an alternative) is deferred to implementation time against the actual call-site data (UNK-01)
- The existing per-HTTP-request trace ID (`result.request_id`) remains unchanged — only the new key is added as a separate field
- `ctx.workflow.workflow_id`, `ctx.workflow.current_task_id`, `ctx.turn.current_turn_id` exist on `AgentContext` (confirmed via `scripts/agent/context.py`)
- Callers of `execute_one_tool_call()`: `tool_preparation.py`, `tool_arg_validator.py`, 3 test files (confirmed via `grep`) — none require changes, only internal key derivation added

## Design decisions

- Adding a new idempotency key field rather than replacing the existing `request_id`: the two serve different purposes — `request_id` is a per-HTTP-request trace ID, while the new key is a stable, retry-invariant identifier for the logical Tool Call attempt. Both must coexist.
- Using `ctx.workflow.current_task_id` as the first-increment linkage target for REQ-002 (see UNK-02): true attempt-level linkage is deferred to a follow-up once `attempt_id` is exposed on `AgentContext`.

## Alternatives considered

- Replacing `request_id` with the idempotency key — rejected: they serve different purposes; `request_id` is needed for HTTP-layer tracing, while the idempotency key is for deduplication semantics.
- Deriving the key from `ctx.turn.current_turn_id` alone — rejected: insufficient granularity for distinguishing different Tool Calls within the same turn.

## Implementation

### Target file

`scripts/agent/tool_runner.py`

### Procedure

Derive the stable idempotency key per Tool Call and pass it to `audit_tool_exec()`.

### Method

1. Re-verify, immediately before editing, that each target row's cited line/content is unchanged since this Plan's evidence-gathering (per `rules/workflow-lifecycle.md` Revalidation): `scripts/agent/tool_runner.py` lines 90, 113-115.
2. In `execute_one_tool_call()`, derive the stable idempotency key from `ctx.workflow.workflow_id`, `ctx.workflow.current_task_id`, `ctx.turn.current_turn_id`, and a per-call sequence discriminator (composition resolved at implementation time per UNK-01).
3. Pass the new key into `audit_tool_exec()` alongside the existing `result.request_id`.

### Details

```python
# Lines 90-115: add idempotency key derivation and pass to audit_tool_exec():
# Before:
async def execute_one_tool_call(
    ctx: AgentContext,
    pc: PreparedToolCall,
    turn: int,
) -> tuple[str, str, dict, str, bool, str]:
    """Execute and truncate one already-prepared tool call.

    Returns (tc_id, name, args, full_text, is_error, llm_text).
    Raises ToolExecutorUnavailableError when ctx.services_required.tools is None.
    Argument parsing and validation already happened in the preparation phase
    (agent.tool_preparation.prepare_tool_calls) before this function is ever called.
    """
    if ctx.services_required.tools is None:
        raise ToolExecutorUnavailableError(
            "Tool executor is not available (ctx.services_required.tools is None)"
        )
    name = pc.name
    args = pc.args

    if ctx.services_required.gateway is not None:
        result = await ctx.services_required.gateway.execute(ctx, name, args)
    else:
        result = await ctx.services_required.tools.execute(name, args)
    text, is_error, x_request_id = result.output, result.is_error, result.request_id
    audit_tool_exec(

# After:
async def execute_one_tool_call(
    ctx: AgentContext,
    pc: PreparedToolCall,
    turn: int,
) -> tuple[str, str, dict, str, bool, str]:
    """Execute and truncate one already-prepared tool call.

    Returns (tc_id, name, args, full_text, is_error, llm_text).
    Raises ToolExecutorUnavailableError when ctx.services_required.tools is None.
    Argument parsing and validation already happened in the preparation phase
    (agent.tool_preparation.prepare_tool_calls) before this function is ever called.
    """
    if ctx.services_required.tools is None:
        raise ToolExecutorUnavailableError(
            "Tool executor is not available (ctx.services_required.tools is None)"
        )
    name = pc.name
    args = pc.args

    # Derive a stable, retry-invariant idempotency key for this Tool Call.
    # Composition: {workflow_id}:{task_id}:{turn_id}:{sequence}
    # (exact format resolved at implementation time per UNK-01)
    workflow_id = ctx.workflow.workflow_id or ""
    task_id = ctx.workflow.current_task_id or ""
    turn_id = ctx.turn.current_turn_id or ""
    # Sequence discriminator: use the prepared call index within the current group
    # (resolved at implementation time — see UNK-01 for alternatives)
    seq_discriminator = getattr(pc, "_seq", "") or ""
    idempotency_key = f"{workflow_id}:{task_id}:{turn_id}:{seq_discriminator}"

    if ctx.services_required.gateway is not None:
        result = await ctx.services_required.gateway.execute(ctx, name, args)
    else:
        result = await ctx.services_required.tools.execute(name, args)
    text, is_error, x_request_id = result.output, result.is_error, result.request_id
    audit_tool_exec(
        ...
        idempotency_key=idempotency_key,  # NEW: pass the derived key
        ...
```

## Compatibility considerations

- Callers of `execute_one_tool_call()`: `tool_preparation.py`, `tool_arg_validator.py`, 3 test files (confirmed via `grep`) — none require changes, only internal key derivation added.
- The existing per-HTTP-request trace ID (`result.request_id`) remains unchanged — backward compatible.

## Security considerations

- No security impact. This is adding a new idempotency key field, not changing any security boundary.

## Rollback considerations

- Reverting this change restores the original behavior without the idempotency key. If needed later, the key should be reimplemented to match the canonical exclude-and-FATAL duplicate-ownership policy from `McpToolDiscoveryService._dedupe_and_build()`.

## Validation plan

- Unit: run `uv run pytest tests/agent/test_tool_runner.py -q` to confirm no failures introduced, including new key-derivation tests (AC-1, AC-4).
- Static analysis: `uv run ruff check scripts/agent/tool_runner.py`, `uv run mypy scripts/agent/tool_runner.py`.
- Import lint: `PYTHONPATH=scripts uv run lint-imports` to confirm no broken contracts introduced.

## Completion criteria

- A Tool Call retried within the same logical attempt (same `workflow_id`/`current_task_id`/`current_turn_id`/sequence) produces the same idempotency key across the retry (AC-1).
- A different Tool Call (different sequence, turn, task, or workflow) produces a different key (AC-1).
- The new idempotency key is passed into `audit_tool_exec()` alongside the existing `result.request_id`.
- All existing tests in `tests/agent/test_tool_runner.py` continue to pass without modification (AC-4).
- No new lint/type errors introduced.

## Out of scope

- Changes to `scripts/agent/shared/models.py` — covered by separate row (REQ-002).
- Changes to `scripts/agent/tool_audit.py` — covered by separate row (REQ-002).
- Changes to `scripts/mcp_servers/dispatch.py` — covered by separate row (REQ-003).
- Changes to `scripts/mcp_servers/server.py` — covered by separate row (REQ-004).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Derive stable idempotency key in execute_one_tool_call() | Pending | — | — | |
| 2 | Pass idempotency key into audit_tool_exec() | Pending | — | — | |
| 3 | Run the validation sequence (rules/toolchain.md) | Pending | — | — | |

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
- **Requirement ID**: REQ-001
- **Source issue**: issues/20260914-123621_arch02_tool-call-execution-id-idempotency-guard-missing.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260916-135754_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260916-232730
- **Related target files**: scripts/agent/tool_runner.py
