## Goal

Add an optional `idempotency_key: str | None = None` parameter to `dispatch_tool()`; when provided and `name` is classified side-effecting via a helper built on `shared/tool_constants.py`'s write/dangerous tool-name sets, check an in-process cache keyed by `idempotency_key` before invoking the handler; on a cache hit, short-circuit and return the cached `DispatchResult`; on a cache miss, invoke normally and cache the result.

## Scope

- Add the opt-in, side-effecting-tool duplicate-check to `dispatch_tool()` in `scripts/mcp_servers/dispatch.py`
- No other files are modified in this row

## Assumptions

- An in-process (per-server-process), non-persistent cache is sufficient for `dispatch_tool()`'s duplicate-check (REQ-003): each specialized MCP server runs as its own long-lived process (confirmed: each `*_server.py` binds its own `http_port` via `MCPServer.run_http()`), so retries of the same logical Tool Call reach the same process. A process restart between retries loses the cache — accepted for this increment.
- The exact rejection/short-circuit response shape for a detected duplicate (return prior cached result verbatim vs. a distinct "duplicate detected" error kind) is resolved during implementation (UNK-03); either choice satisfies AC-3 as written.
- The side-effecting classification uses `shared/tool_constants.py`'s write/dangerous tool-name sets (already importable from `mcp_servers` per the layer contract, with existing precedent in `git_server.py`/`git_service.py`).
- The signature change uses a backward-compatible default (`idempotency_key=None`), so none of the 10 callers require changes for this Plan.

## Design decisions

- Adding an in-process cache rather than a persistent one: this keeps the first increment simple and focused; a DB-backed cache can be added later if operational data shows crash-induced duplicate side effects.
- Using `shared/tool_constants.py` for side-effecting classification rather than duplicating `scripts/agent/tool_policy.py`'s `classify_operation_type`/`RiskLevel` logic: avoids both a layer-contract violation (`.importlinter`'s `mcp_servers-no-agent` contract) and a second, divergent source of truth.
- Opt-in behavior (fail-open when no `idempotency_key` is supplied) rather than fail-closed: until the follow-up wiring plan lands, no MCP server actually exercises the new protection end-to-end; making it fail-closed would break existing callers that do not yet supply the key.

## Alternatives considered

- Making the duplicate-check mandatory (fail-closed) — rejected: would break all existing callers that do not yet supply the idempotency key; opt-in defaults allow incremental rollout without breaking changes.
- Deriving the side-effecting classification from `scripts/agent/tool_policy.py` — rejected: `.importlinter`'s `mcp_servers-no-agent` contract forbids `dispatch.py` from importing `agent.*` types.

## Implementation

### Target file

`scripts/mcp_servers/dispatch.py`

### Procedure

Add the opt-in, side-effecting-tool duplicate-check to `dispatch_tool()`.

### Method

1. Re-verify, immediately before editing, that each target row's cited line/content is unchanged since this Plan's evidence-gathering (per `rules/workflow-lifecycle.md` Revalidation): `scripts/mcp_servers/dispatch.py` line 40, no existing `duplicate`/`idempot` reference (`grep` confirmed).
2. Import `shared.tool_constants` for side-effecting classification.
3. Add an in-process cache keyed by `idempotency_key`.
4. Add `idempotency_key: str | None = None` parameter to `dispatch_tool()`.
5. When `idempotency_key` is provided and `name` is classified side-effecting, check the cache before invoking the handler.
6. On a cache hit, short-circuit and return the cached `DispatchResult`.
7. On a cache miss, invoke normally and cache the result.

### Details

```python
# Lines 40-70: add the duplicate-check capability:
# Before:
async def dispatch_tool(
    table: Mapping[str, Callable[[ToolArgs], Awaitable[str]]],
    name: str,
    args: ToolArgs,
) -> DispatchResult:
    """Route a tool call through a dispatch table.

    Returns a DispatchResult with output text and is_error flag.
    Raises for non-ValueError handler exceptions (caller is responsible for transport-level handling).
    ValueError from handlers is converted to an error result (user-input/validation errors).
    Unknown tool and empty name return error results without raising.
    """
    if not isinstance(name, str) or not name.strip():
        logger.warning("dispatch_tool called with empty tool name")
        return DispatchResult(
            output="Tool name must be a non-empty string", is_error=True
        )

    handler = table.get(name)
    if handler is None:
        logger.warning("Unknown tool requested: %s", name)
        return DispatchResult(output=f"Unknown tool: {name}", is_error=True)

    try:
        result = await handler(args)
        return DispatchResult(output=result, is_error=False)
    except ValueError as e:
        # Validation / user-input errors: return as tool error, not server fault
        logger.warning("Tool '%s' validation error: %s", name, e)
        return DispatchResult(output=f"Validation error: {e}", is_error=True)
    # All other exceptions (RuntimeError, IOError, HTTPException, etc.) propagate to caller.

# After:
# NEW import:
from scripts.shared import tool_constants  # side-effecting classification

# In-process cache for deduplication (keyed by idempotency_key):
_duplicate_cache: dict[str, DispatchResult] = {}

def _is_side_effecting(tool_name: str) -> bool:
    """Check if a tool name belongs to the write/dangerous/exec sets."""
    all_write_tools = set()
    for s in (tool_constants.WRITE_TOOLS, tool_constants.DELETE_TOOLS,
              tool_constants.GIT_WRITE_TOOLS, tool_constants.RAG_WRITE_TOOLS,
              tool_constants.CICD_WRITE_TOOLS, tool_constants.GITHUB_WRITE_TOOLS,
              tool_constants.GITHUB_DANGEROUS_TOOLS, tool_constants.SHELL_TOOLS):
        all_write_tools.update(s)
    return tool_name in all_write_tools

async def dispatch_tool(
    table: Mapping[str, Callable[[ToolArgs], Awaitable[str]]],
    name: str,
    args: ToolArgs,
    idempotency_key: str | None = None,  # NEW: stable, retry-invariant key
) -> DispatchResult:
    """Route a tool call through a dispatch table.

    Returns a DispatchResult with output text and is_error flag.
    Raises for non-ValueError handler exceptions (caller is responsible for transport-level handling).
    ValueError from handlers is converted to an error result (user-input/validation errors).
    Unknown tool and empty name return error results without raising.
    If idempotency_key is provided and name is side-effecting, checks for duplicates.
    """
    if not isinstance(name, str) or not name.strip():
        logger.warning("dispatch_tool called with empty tool name")
        return DispatchResult(
            output="Tool name must be a non-empty string", is_error=True
        )

    handler = table.get(name)
    if handler is None:
        logger.warning("Unknown tool requested: %s", name)
        return DispatchResult(output=f"Unknown tool: {name}", is_error=True)

    # NEW: duplicate-check for side-effecting tools
    if idempotency_key is not None and _is_side_effecting(name):
        cached = _duplicate_cache.get(idempotency_key)
        if cached is not None:
            logger.info("Duplicate tool call detected: %s (key=%s)", name, idempotency_key)
            return cached

    try:
        result = await handler(args)
        dispatched_result = DispatchResult(output=result, is_error=False)
        # NEW: cache the result for deduplication
        if idempotency_key is not None and _is_side_effecting(name):
            _duplicate_cache[idempotency_key] = dispatched_result
        return dispatched_result
    except ValueError as e:
        # Validation / user-input errors: return as tool error, not server fault
        logger.warning("Tool '%s' validation error: %s", name, e)
        error_result = DispatchResult(output=f"Validation error: {e}", is_error=True)
        # NEW: cache the error result for deduplication
        if idempotency_key is not None and _is_side_effecting(name):
            _duplicate_cache[idempotency_key] = error_result
        return error_result
    # All other exceptions (RuntimeError, IOError, HTTPException, etc.) propagate to caller.
```

## Compatibility considerations

- The signature change uses a backward-compatible default (`idempotency_key=None`), so none of the 10 callers require changes for this Plan.
- The in-process cache is per-server-process; a process restart between retries loses the cache — accepted for this increment (no Acceptance Criterion requires crash-durability).

## Security considerations

- No security impact. This is adding a deduplication mechanism, not changing any security boundary.

## Rollback considerations

- Reverting this change restores the original `dispatch_tool()` behavior without the duplicate-check. If needed later, the fields should be reimplemented to match the canonical exclude-and-FATAL duplicate-ownership policy from `McpToolDiscoveryService._dedupe_and_build()`.

## Validation plan

- Unit: run `uv run pytest tests/mcp_servers/test_mcp_dispatch.py -q` to confirm no failures introduced, including new duplicate-check tests (AC-3, AC-5).
- Static analysis: `uv run ruff check scripts/mcp_servers/dispatch.py`, `uv run mypy scripts/mcp_servers/dispatch.py`.
- Import lint: `PYTHONPATH=scripts uv run lint-imports` to confirm no broken contracts introduced.

## Completion criteria

- `dispatch_tool()` accepts the optional `idempotency_key` parameter (default `None`) (AC-3).
- When `idempotency_key` is provided and `name` is classified side-effecting, the duplicate-check returns the cached `DispatchResult` on the second call without re-invoking the handler (AC-3).
- When invoked with a tool name not in a side-effecting set, or with no key, behaves exactly as before (no regression) (AC-3).
- All existing tests in `tests/mcp_servers/test_mcp_dispatch.py` continue to pass without modification (AC-5).
- No new lint/type errors introduced.

## Out of scope

- Changes to `scripts/agent/tool_runner.py` — covered by separate row (REQ-001).
- Changes to `scripts/agent/shared/models.py` — covered by separate row (REQ-002).
- Changes to `scripts/agent/tool_audit.py` — covered by separate row (REQ-002).
- Changes to `scripts/mcp_servers/server.py` — covered by separate row (REQ-004).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add idempotency_key parameter to dispatch_tool() | Pending | — | — | |
| 2 | Add side-effecting classification helper | Pending | — | — | |
| 3 | Add in-process cache for deduplication | Pending | — | — | |
| 4 | Implement duplicate-check logic | Pending | — | — | |
| 5 | Cache result/error after invocation | Pending | — | — | |
| 6 | Run the validation sequence (rules/toolchain.md) | Pending | — | — | |

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
- **Requirement ID**: REQ-003
- **Source issue**: issues/20260914-123621_arch02_tool-call-execution-id-idempotency-guard-missing.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260916-135754_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260916-232730
- **Related target files**: scripts/mcp_servers/dispatch.py
