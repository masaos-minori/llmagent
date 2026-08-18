## Goal

Clean up dead code in `shell/subprocess_runner.py` and `shell_service.py` — remove dead `_timeout_sec` store and fix stale docstring.

## Scope

- **In-Scope**:
  - Phase 1: Confirm `_timeout_sec` is truly dead (zero read sites) across `scripts/mcp_servers/shell/` and `tests/mcp_servers/shell/`
  - Phase 2: Remove dead `self._timeout_sec = timeout_sec` store from `SubprocessRunner.__init__`
  - Phase 3: Fix stale docstring in `shell_service.py` (change "service.py" to "shell_service.py")
- **Out-of-Scope**:
  - Changes to `kill_timed_out_process` — confirmed alive by tests
  - Any other timeout-related code in `subprocess_runner.py`
  - Changes outside `scripts/mcp_servers/shell/`

## Assumptions

- `_timeout_sec` is genuinely dead — no subclass or external caller reads the attribute
- Removing `self._timeout_sec = timeout_sec` does not break any downstream consumers
- The docstring fix is purely cosmetic with no behavioral impact

## Design decisions

- Use `rg` to confirm zero read sites before removing the dead store
- Only remove `timeout_sec` parameter from `__init__` signature if Phase 1 confirms no external callers pass it

## Alternatives considered

- Leave dead code in place — rejected because it misleads maintainers
- Keep `timeout_sec` parameter but remove only the store — acceptable if external callers still need it

## Compatibility considerations

- Removing `timeout_sec` parameter may break external callers that pass it
- Must confirm zero read sites before proceeding

## Security considerations

- N/A — dead code removal has no security impact

## Rollback considerations

- Revert the diff; no data loss or service impact

## Implementation

### Target files

- `scripts/mcp_servers/shell/subprocess_runner.py`
- `scripts/mcp_servers/shell/shell_service.py`

### Procedure

1. **Phase 1: Preparation / Verification**
   - Run `rg "_timeout_sec" scripts/mcp_servers/shell/ tests/mcp_servers/shell/` to confirm zero read sites
   - Run `rg "SubprocessRunner(" scripts/ tests/` to check if any external callers pass `timeout_sec`
   - Read `subprocess_runner.py:33` context to determine if `timeout_sec` parameter should also be removed

2. **Phase 2: Core Logic Implementation**
   - Remove `self._timeout_sec = timeout_sec` from `SubprocessRunner.__init__`
   - If `timeout_sec` is provably unused after this, also remove it from `__init__` signature
   - Fix `shell_service.py` module docstring: change "service.py" to "shell_service.py"

3. **Phase 3: Deployment & Verification**
   - Run `uv run pytest tests/mcp_servers/shell/ -v` — verify all 54+ tests pass unchanged
   - Run `uv run pytest tests/mcp_servers/cicd/test_tool_server_layer_consistency.py -v` — verify ShellService construction still works

### Method

Dead code removal — eliminate unused attribute assignment and fix stale documentation.

### Details

```python
# In scripts/mcp_servers/shell/subprocess_runner.py:

# BEFORE:
class SubprocessRunner:
    def __init__(self, timeout_sec: int | None = None):
        self._timeout_sec = timeout_sec  # DEAD CODE — never read
        
    def run(self, ...):
        # ... uses kill_timed_out_process which IS alive
        
# AFTER:
class SubprocessRunner:
    def __init__(self, timeout_sec: int | None = None):
        # timeout_sec kept if external callers still pass it; otherwise remove param too
        pass  # dead store removed
    
    def run(self, ...):
        # ... uses kill_timed_out_process which IS alive

# In scripts/mcp_servers/shell/shell_service.py:

# BEFORE (module docstring ~line 10):
"""MCP server for shell operations. See service.py for architecture."""

# AFTER:
"""MCP server for shell operations. See shell_service.py for architecture."""
```

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tests/mcp_servers/shell/` | Regression (54+ tests) | `uv run pytest tests/mcp_servers/shell/ -v` | All pass unchanged |
| `tests/mcp_servers/cicd/test_tool_server_layer_consistency.py` | Regression | `uv run pytest tests/mcp_servers/cicd/test_tool_server_layer_consistency.py -v` | Passes unchanged |

## Out of scope

- Changes to `kill_timed_out_process` — confirmed alive by tests
- Any other timeout-related code in `subprocess_runner.py`
- Changes outside `scripts/mcp_servers/shell/`

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: requires/20260817-143115_require.md
- Source plan: plans/20260817-170520_plan.md
- Source implementation procedure: N/A
- Generated at: 20260817-185553
- Related target files: scripts/mcp_servers/shell/subprocess_runner.py, scripts/mcp_servers/shell/shell_service.py
