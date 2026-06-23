## Goal

Add four new test methods to `TestMcpServerHealthRegistry` in `tests/test_tool_executor_routing.py` covering the HALF_OPEN state transitions: cooldown expiry, successful trial probe, failed trial probe, and pre-cooldown blocking.

## Scope

**In-Scope:**
- `tests/test_tool_executor_routing.py` — append four test methods to `class TestMcpServerHealthRegistry` (after line 643)

**Out-of-Scope:**
- No changes to `TestToolExecutorHealthGate` or any other test class
- No production code changes

## Assumptions

1. `McpServerHealthState` is already imported in the test file (used by existing tests).
2. `time.monotonic` must be patched via `unittest.mock.patch("shared.mcp_config.time.monotonic", ...)` to simulate cooldown expiry without real sleeps.
3. A registry with `half_open_cooldown_sec=30.0` (default): to simulate "cooldown elapsed", mock `time.monotonic()` to return `current + 31.0` after the server entered UNAVAILABLE.
4. The `_unavailable_since` dict is populated when `record_failure()` transitions to `UNAVAILABLE`. Its value comes from `time.monotonic()` at that moment.
5. The test for "before cooldown" needs `time.monotonic()` to return a value less than `_unavailable_since + cooldown_sec`.

## Implementation

### Target file
`tests/test_tool_executor_routing.py`

### Procedure

1. Locate the end of `TestMcpServerHealthRegistry` (after `test_health_registry_transitions_from_validation_plan`, line ~643).
2. Append four new test methods.

### Method

Single `Edit` — append methods after `test_health_registry_transitions_from_validation_plan`.

### Details

All four tests use `unittest.mock.patch` to control `time.monotonic`.

#### test_half_open_after_cooldown

```python
def test_half_open_after_cooldown(self) -> None:
    """After cooldown elapses, is_unavailable() transitions to HALF_OPEN and returns False."""
    from unittest.mock import patch

    r = McpServerHealthRegistry(failure_threshold=1, half_open_cooldown_sec=30.0)
    with patch("shared.mcp_config.time.monotonic", return_value=0.0):
        r.record_failure("srv")  # → UNAVAILABLE at t=0
        assert r.is_unavailable("srv")  # cooldown not elapsed

    # Simulate 31 seconds later
    with patch("shared.mcp_config.time.monotonic", return_value=31.0):
        assert not r.is_unavailable("srv")  # cooldown elapsed → HALF_OPEN
    assert r.get_state("srv") == McpServerHealthState.HALF_OPEN
```

#### test_half_open_success_recovers

```python
def test_half_open_success_recovers(self) -> None:
    """record_success() from HALF_OPEN state transitions to HEALTHY."""
    from unittest.mock import patch

    r = McpServerHealthRegistry(failure_threshold=1, half_open_cooldown_sec=30.0)
    with patch("shared.mcp_config.time.monotonic", return_value=0.0):
        r.record_failure("srv")

    with patch("shared.mcp_config.time.monotonic", return_value=31.0):
        r.is_unavailable("srv")  # trigger UNAVAILABLE → HALF_OPEN transition

    r.record_success("srv")
    assert r.get_state("srv") == McpServerHealthState.HEALTHY
    assert not r.is_unavailable("srv")
```

#### test_half_open_failure_resets

```python
def test_half_open_failure_resets(self) -> None:
    """record_failure() from HALF_OPEN resets to UNAVAILABLE with fresh cooldown."""
    from unittest.mock import patch

    r = McpServerHealthRegistry(failure_threshold=1, half_open_cooldown_sec=30.0)
    with patch("shared.mcp_config.time.monotonic", return_value=0.0):
        r.record_failure("srv")

    with patch("shared.mcp_config.time.monotonic", return_value=31.0):
        r.is_unavailable("srv")  # → HALF_OPEN
        assert r.get_state("srv") == McpServerHealthState.HALF_OPEN
        # Trial probe fails — cooldown timestamp resets to t=31
        state = r.record_failure("srv")

    assert state == McpServerHealthState.UNAVAILABLE
    assert r.get_state("srv") == McpServerHealthState.UNAVAILABLE
    # At t=35, only 4s have elapsed since reset at t=31 — still blocked
    with patch("shared.mcp_config.time.monotonic", return_value=35.0):
        assert r.is_unavailable("srv")
```

#### test_unavailable_before_cooldown_blocks

```python
def test_unavailable_before_cooldown_blocks(self) -> None:
    """is_unavailable() returns True while cooldown has not elapsed."""
    from unittest.mock import patch

    r = McpServerHealthRegistry(failure_threshold=1, half_open_cooldown_sec=30.0)
    with patch("shared.mcp_config.time.monotonic", return_value=0.0):
        r.record_failure("srv")

    with patch("shared.mcp_config.time.monotonic", return_value=29.0):
        assert r.is_unavailable("srv")  # 29s < 30s cooldown → still blocked
    assert r.get_state("srv") == McpServerHealthState.UNAVAILABLE
```

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| New HALF_OPEN tests | `uv run pytest tests/test_tool_executor_routing.py::TestMcpServerHealthRegistry -v -k half_open or cooldown` | 4 tests PASSED |
| Full health registry class | `uv run pytest tests/test_tool_executor_routing.py::TestMcpServerHealthRegistry -v` | All PASSED (7 existing + 4 new) |
| Full routing tests | `uv run pytest tests/test_tool_executor_routing.py -v` | No new failures |
| Lint | `uv run ruff check tests/test_tool_executor_routing.py` | 0 errors |
