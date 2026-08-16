# Implementation Procedure: Make MCP Server Health Timeout Configurable Per-Server

## Goal

Replace the global `MCPSERVER_HEALTH_TIMEOUT` constant with per-server configurable `health_timeout` on `McpServerConfig`, falling back to 5.0 seconds when not specified. Update both `mcp_tool_discovery.py` and `mcp_status.py` to use the per-server timeout via a helper function.

## Scope

- Add `health_timeout: float | None = None` field to `McpServerConfig` in `scripts/shared/mcp_config.py`
- Add `get_effective_health_timeout(cfg: McpServerConfig) -> float` helper in `scripts/shared/mcp_config.py`
- Update `scripts/agent/services/mcp_tool_discovery.py` to use per-server timeout
- Update `scripts/agent/services/mcp_status.py` to use per-server timeout
- Keep `MCPSERVER_HEALTH_TIMEOUT` in `scripts/agent/http_lifecycle.py` as documented default reference
- Add unit test for `get_effective_health_timeout()`

## Assumptions

1. The default value of 5.0 seconds is acceptable; no operator requests a different default
2. `McpServerConfig` is only used by HTTP-transport servers (verified: TransportType.HTTP is the only transport type defined)
3. No other code path reads `MCPSERVER_HEALTH_TIMEOUT` besides the two identified consumers
4. The `_build_single_server()` function in `mcp_config.py` will need updating to pass `health_timeout` from TOML config
5. `MCPSERVER_HEALTH_TIMEOUT` in `http_lifecycle.py` is only consumed by `mcp_tool_discovery.py` and `mcp_status.py` (verified: grep confirms exactly 5 references across the repo)

## Unknowns

1. No existing TOML configs set `health_timeout` (verified across all config/*.toml files). Safe to add as new field.
2. Does `call_timeout_sec` (default 60.0) overlap semantically with health timeout? They serve different purposes — `call_timeout_sec` is for tool execution calls, while health timeout is for `/v1/tools` and `/health` probes.
3. Should negative or zero values for `health_timeout` be rejected? Need to decide validation policy.

## Design decisions

- Add `health_timeout: float | None = None` field to `McpServerConfig` dataclass
- Create `get_effective_health_timeout(cfg: McpServerConfig) -> float` helper that returns cfg.health_timeout if set, else 5.0
- Keep `MCPSERVER_HEALTH_TIMEOUT` in `http_lifecycle.py` as documented default reference (not removed)
- Validate non-positive values in the helper function (raise ValueError for <= 0)

## Alternatives considered

1. **Remove `MCPSERVER_HEALTH_TIMEOUT` entirely**: Would simplify but lose the documented default reference. Keeping it provides visibility into the original design decision.
2. **Use a sentinel value instead of None**: Would avoid `| None` typing but adds complexity. None is more idiomatic Python.
3. **Add validation in the dataclass field itself**: Would catch invalid values earlier but adds boilerplate. Validation in the helper is sufficient.

## Compatibility considerations

- Adding optional field to `McpServerConfig` is backward-compatible — existing code without the field defaults to None → 5.0
- Existing TOML configs don't set `health_timeout`, so no migration needed
- Test fixtures that construct `McpServerConfig` directly may need updating if they rely on positional arguments
- If any code catches `ValueError` from the helper, it could conflict with other ValueError uses

## Security considerations

N/A — no security implications. Only changes configuration handling.

## Rollback considerations

- Revert `McpServerConfig` dataclass field addition
- Remove `get_effective_health_timeout` helper
- Restore direct imports of `MCPSERVER_HEALTH_TIMEOUT` in both consumers
- No database or config changes to revert

## Validation plan

- Unit test for `get_effective_health_timeout()` with various config values including None
- Verify backward compatibility: existing TOML configs without `health_timeout` still default to 5.0
- Run full test suite to ensure no regressions in normal operation
- Manual verification that no other code depends on `MCPSERVER_HEALTH_TIMEOUT` being imported from `http_lifecycle`

## Out of scope

- Changes to any other timeout-related constants in the codebase
- Changes to `call_timeout_sec` semantics
- Changes to how timeouts are propagated through the MCP server lifecycle
- Changes to TOML schema documentation (separate concern)

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: requires/20260815-162130_require.md
- Source plan: plans/20260815-180719_plan.md
- Source implementation procedure: N/A
- Generated at: 20260816-082042
- Related target files: scripts/shared/mcp_config.py, scripts/agent/services/mcp_tool_discovery.py, scripts/agent/services/mcp_status.py, scripts/agent/http_lifecycle.py

---

## Implementation

### Target file: `scripts/shared/mcp_config.py`

#### Procedure

1. Read `scripts/shared/mcp_config.py` to confirm current field list and identify insertion point
2. Add `health_timeout: float | None = None` field after `call_timeout_sec` in `McpServerConfig` dataclass
3. Add `get_effective_health_timeout(cfg: McpServerConfig) -> float` helper function below the class definition
4. Update `_build_single_server()` to read `health_timeout` from TOML config dict
5. Search for all `McpServerConfig` instantiations in test fixtures to ensure they remain compatible
6. Add unit test for `get_effective_health_timeout()` covering: None → 5.0, explicit value, zero value, negative value

#### Method

Modify the dataclass and add a module-level helper function.

#### Details

Current `McpServerConfig` dataclass fields (need to verify exact order):
```python
@dataclass
class McpServerConfig:
    # ... existing fields ...
    call_timeout_sec: float = 60.0
```

New fields added after `call_timeout_sec`:
```python
@dataclass
class McpServerConfig:
    # ... existing fields ...
    call_timeout_sec: float = 60.0
    health_timeout: float | None = None
```

New helper function (added below the dataclass):
```python
def get_effective_health_timeout(cfg: McpServerConfig) -> float:
    """Return the effective health timeout for a given server config.

    Returns the configured ``health_timeout`` if set, otherwise falls back
    to the global default of 5.0 seconds.

    Raises:
        ValueError: If ``health_timeout`` is set to a non-positive value.
    """
    if cfg.health_timeout is None:
        return 5.0
    if cfg.health_timeout <= 0:
        raise ValueError(f"health_timeout must be positive, got {cfg.health_timeout}")
    return cfg.health_timeout
```

Update `_build_single_server()` to read `health_timeout` from TOML config dict:
```python
# In _build_single_server():
# Before:
#     health_timeout = 5.0  # hardcoded default
# After:
#     health_timeout = config.get("health_timeout")  # may be None
```

Note: The `_build_single_server()` function needs to handle the case where `health_timeout` is not present in the TOML config (defaults to None → 5.0 fallback).

---

### Target file: `scripts/agent/services/mcp_tool_discovery.py`

#### Procedure

1. Read `scripts/agent/services/mcp_tool_discovery.py` to confirm current import and usage
2. Replace `from agent.http_lifecycle import MCPSERVER_HEALTH_TIMEOUT` with `from shared.mcp_config import get_effective_health_timeout`
3. Replace `MCPSERVER_HEALTH_TIMEOUT` usage at line 163 with `get_effective_health_timeout(cfg)`
4. Verify no other callers depend on `MCPSERVER_HEALTH_TIMEOUT` being imported here

#### Method

Change import statement and replace constant usage with helper function call.

#### Details

Current code (line 52):
```python
from agent.http_lifecycle import MCPSERVER_HEALTH_TIMEOUT
```

New code:
```python
from shared.mcp_config import get_effective_health_timeout
```

Current code (line 163):
```python
timeout=httpx.Timeout(timeout=MCPSERVER_HEALTH_TIMEOUT),
```

New code:
```python
timeout=httpx.Timeout(timeout=get_effective_health_timeout(cfg)),
```

Note: `cfg` must be available in the calling context. If not, the caller needs to pass it.

---

### Target file: `scripts/agent/services/mcp_status.py`

#### Procedure

1. Read `scripts/agent/services/mcp_status.py` to confirm current import and usage
2. Replace `from agent.http_lifecycle import MCPSERVER_HEALTH_TIMEOUT` with `from shared.mcp_config import get_effective_health_timeout`
3. Replace `MCPSERVER_HEALTH_TIMEOUT` usage at line 69 with `get_effective_health_timeout(cfg)`
4. Verify no other callers depend on `MCPSERVER_HEALTH_TIMEOUT` being imported here

#### Method

Same pattern as mcp_tool_discovery.py — change import and replace constant usage.

#### Details

Current code (line 18):
```python
from agent.http_lifecycle import MCPSERVER_HEALTH_TIMEOUT
```

New code:
```python
from shared.mcp_config import get_effective_health_timeout
```

Current code (line 69):
```python
timeout=httpx.Timeout(timeout=MCPSERVER_HEALTH_TIMEOUT)
```

New code:
```python
timeout=httpx.Timeout(timeout=get_effective_health_timeout(cfg))
```

Note: Same constraint about `cfg` availability applies.

---

### Target file: `scripts/agent/http_lifecycle.py`

#### Procedure

No changes required. `MCPSERVER_HEALTH_TIMEOUT` remains as a documented default reference.

#### Method

None — keep the constant as-is.

#### Details

Current code (line 32):
```python
MCPSERVER_HEALTH_TIMEOUT: float = 5.0
```

No changes — this constant serves as the documented default value that `get_effective_health_timeout()` falls back to. It should remain visible for operators who want to understand the default behavior.
