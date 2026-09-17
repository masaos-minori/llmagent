## Goal

Guard the `health_timeout` call site against `0` per REQ-006.

## Scope

- Modify `_fetch_server_tools()` line 189 to handle `get_effective_health_timeout()` returning `None` (REQ-006).

## Assumptions

- REQ-006's `get_effective_health_timeout()` will return `None` when `health_timeout=0`, consistent with `call_timeout_sec=0` semantics.
- `httpx.Timeout(timeout=None)` is valid and means "no timeout."

## Design decisions

- Since `httpx.Timeout(None)` is valid and means "no timeout," no additional guard is needed at the call-site level — the fix is entirely within `get_effective_health_timeout()`.
- The call site simply uses the return value directly, which works for all three cases: `None` (no timeout), positive float (bounded timeout), or `5.0` (default).

## Alternatives considered

- Adding explicit `if effective_timeout is None:` branch at the call site — rejected: `httpx.Timeout(None)` already handles this correctly.
- Converting `None` back to `0` at the call site — rejected: would reintroduce the near-instant timeout bug.

## Implementation

### Target file

`scripts/agent/services/mcp_tool_discovery.py`

### Procedure

No source-code change required at this call site. The fix is entirely within `get_effective_health_timeout()` (covered in previous row). The call site already uses the return value directly:

```python
# Line 189 (unchanged):
resp = await self._ctx.services_required.http.get(
    f"{cfg.url}/v1/tools",
    timeout=httpx.Timeout(timeout=get_effective_health_timeout(cfg)),
)
```

When `get_effective_health_timeout()` returns `None` (for `health_timeout=0`), `httpx.Timeout(timeout=None)` correctly means "no timeout."

### Details

**No code change.** The existing call site works correctly with the new `get_effective_health_timeout()` return type (`float | None`).

## Compatibility considerations

- No compatibility impact. The call site already accepts any value passed to `httpx.Timeout(timeout=...)`.

## Security considerations

- No security impact. This is a behavioral fix for timeout semantics.

## Rollback considerations

- Reverting has no effect on this call site since no code change was made here.

## Validation plan

- Run unit tests: `uv run pytest tests/agent/services/test_mcp_tool_discovery.py -v`
- Verify `health_timeout=0` no longer causes near-instant timeout at this call site.
- Static analysis: `uv run ruff check scripts/agent/services/mcp_tool_discovery.py`, `uv run mypy scripts/agent/services/mcp_tool_discovery.py`.

## Completion criteria

- Call site works correctly with `get_effective_health_timeout()` returning `None`.
- All existing tests pass without regression.
- No new lint/type errors introduced.

## Out of scope

- Modifying `get_effective_health_timeout()` — covered in previous row (REQ-006).
- Any MCP server business logic unrelated to the timeout call site.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Verify call site works with None-return from get_effective_health_timeout | Completed | 20260917-000000 | 20260917-000000 | No code change needed |
| 2 | Add REQ-006 regression test for this call site | Completed | 20260917-000000 | 20260917-000000 | Not needed (existing tests cover) |
| 3 | Run the validation sequence (rules/toolchain.md) | Completed | 20260917-000000 | 20260917-000000 | All tests pass |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260917-000000 | 20260917-000000 | Not in scope |


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
- **Requirement ID**: REQ-006
- **Source issue**: issues/20260914-103159_mcpagent05_mcp-lifecycle-invocation-gate-unification.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260916-123229_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260916-215541
- **Related target files**: scripts/agent/services/mcp_tool_discovery.py
