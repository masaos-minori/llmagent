# Implementation: MCP Server Health State Registry (healthy/degraded/unavailable)

## Goal

Add a `McpServerHealthRegistry` that tracks per-server health states (`healthy`, `degraded`, `unavailable`) and gates `ToolExecutor.execute()` from dispatching to `unavailable` servers.

## Scope

**In:**
- `McpServerHealthState` enum in `scripts/shared/mcp_config.py`
- `McpServerHealthRegistry` class to track states + failure counts
- `ToolExecutor.set_health_registry(registry)` injection point
- `ToolExecutor.execute()` to return error immediately for `unavailable` servers
- `watchdog_loop()` in `repl_health.py` to update health states
- `/mcp` status display updated to show health state

**Out:**
- Auto-restart on failure (Watchdog already handles this)
- Health state persistence across REPL sessions

## Assumptions

- `scripts/shared/tool_executor.py`: `ToolExecutor._raw_execute()` resolves `server_key` via `_resolver.resolve()`; can check health before calling transport
- `scripts/agent/repl_health.py`: `watchdog_loop()` already tracks `restart_counts`; can update registry here
- `scripts/agent/services/mcp_status.py`: `McpServerStatus.status` is a string; currently "OK" / "FAIL" / "RUNNING" etc.
- `scripts/agent/context.py`: `AppServices` can hold a `health_registry` reference

## Implementation

### 1. `scripts/shared/mcp_config.py` — add `McpServerHealthState`

```python
from enum import Enum

class McpServerHealthState(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"    # failing but not yet unavailable
    UNAVAILABLE = "unavailable"
```

### 2. `scripts/shared/tool_executor.py` — `McpServerHealthRegistry` + gate

Add inline (small enough to keep in `tool_executor.py`):

```python
class McpServerHealthRegistry:
    """Tracks per-server health states for ToolExecutor dispatch gating."""

    def __init__(self, failure_threshold: int = 3) -> None:
        self._states: dict[str, McpServerHealthState] = {}
        self._failure_counts: dict[str, int] = {}
        self._failure_threshold = failure_threshold

    def record_failure(self, server_key: str) -> McpServerHealthState:
        count = self._failure_counts.get(server_key, 0) + 1
        self._failure_counts[server_key] = count
        if count >= self._failure_threshold:
            self._states[server_key] = McpServerHealthState.UNAVAILABLE
        else:
            self._states[server_key] = McpServerHealthState.DEGRADED
        return self._states[server_key]

    def record_success(self, server_key: str) -> None:
        self._states[server_key] = McpServerHealthState.HEALTHY
        self._failure_counts[server_key] = 0

    def get_state(self, server_key: str) -> McpServerHealthState:
        return self._states.get(server_key, McpServerHealthState.HEALTHY)

    def is_unavailable(self, server_key: str) -> bool:
        return self.get_state(server_key) == McpServerHealthState.UNAVAILABLE
```

In `ToolExecutor._raw_execute()`, check health before dispatch:

```python
async def _raw_execute(self, tool_name: str, args: dict[str, Any]) -> tuple[str, bool, str]:
    server_key = self._resolver.resolve(tool_name)
    if self._health_registry is not None and self._health_registry.is_unavailable(server_key):
        msg = f"MCP server {server_key!r} is currently unavailable (health check failed)"
        logger.warning(msg)
        return msg, True, ""
    # ... existing lifecycle + transport dispatch ...
```

Add `set_health_registry()` method:

```python
def set_health_registry(self, registry: McpServerHealthRegistry | None) -> None:
    self._health_registry = registry
```

### 3. `scripts/agent/repl_health.py` — update watchdog to record health

In `_watchdog_check_http()` and `_watchdog_check_stdio()`, after health check:

```python
registry = ctx.services.health_registry
if ok:
    if registry:
        registry.record_success(key)
else:
    if registry:
        registry.record_failure(key)
```

### 4. `scripts/agent/services/mcp_status.py` — show health state in `/mcp`

Update `McpServerStatus.status` to include health state:

```python
from shared.mcp_config import McpServerHealthState

# In probe_all():
health_state = (
    ctx.services.health_registry.get_state(key)
    if ctx.services.health_registry
    else McpServerHealthState.HEALTHY
)
health_label = health_state.value.upper()  # "HEALTHY" | "DEGRADED" | "UNAVAILABLE"
# Combine with existing status (OK/FAIL/RUNNING): "OK/HEALTHY", "FAIL/DEGRADED" etc.
```

## Validation plan

```bash
uv run ruff check scripts/shared/tool_executor.py scripts/agent/repl_health.py
uv run mypy scripts/
uv run pytest tests/test_tool_executor_routing.py tests/test_cmd_mcp.py -v
```

Add to tests:
```python
def test_unavailable_server_returns_error_without_transport_call():
    registry = McpServerHealthRegistry(failure_threshold=1)
    registry.record_failure("file_read")
    executor = make_executor_with_registry(registry)
    result, is_error, _ = asyncio.run(executor._raw_execute("read_text_file", {}))
    assert is_error
    assert "unavailable" in result

def test_health_registry_transitions():
    r = McpServerHealthRegistry(failure_threshold=3)
    assert r.get_state("srv") == McpServerHealthState.HEALTHY
    r.record_failure("srv"); assert r.get_state("srv") == McpServerHealthState.DEGRADED
    r.record_failure("srv"); r.record_failure("srv")
    assert r.get_state("srv") == McpServerHealthState.UNAVAILABLE
    r.record_success("srv"); assert r.get_state("srv") == McpServerHealthState.HEALTHY
```