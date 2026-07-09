# Implementation: M-3 — test_tool_executor_routing.py identity-preservation test

Source plan: `plans/20260709-100825_plan.md` (M-3, Implementation step 2).

## Goal

Prove `apply_config(cache_ttl=...)` never recreates transports, server
configs, or the route resolver — closing the gap left by the two existing
`TestToolExecutorApplyConfig` tests, which only assert `cache_ttl` itself.

## Scope

**Target**: `tests/test_tool_executor_routing.py`,
`class TestToolExecutorApplyConfig` (lines 419-442) — add one test after
`test_apply_config_none_is_no_op`.

## Assumptions

1. `_make_executor()` (lines 420-432) already constructs a `ToolExecutor`
   with one server (`"file_read"`) and an `AsyncMock` HTTP client — reused
   as-is; no fixture change needed.

## Implementation

### Target file

`tests/test_tool_executor_routing.py`

### Procedure

#### Step 1: Add the test

Insert after `test_apply_config_none_is_no_op` (line 442):

```python
    def test_apply_config_does_not_recreate_transports_or_resolver(self) -> None:
        ex = self._make_executor()
        transports_before = ex._transports
        transport_before = ex._transports["file_read"]
        server_configs_before = ex._server_configs
        resolver_before = ex._resolver

        ex.apply_config(cache_ttl=600.0)

        assert ex._cache_ttl == 600.0
        assert ex._transports is transports_before
        assert ex._transports["file_read"] is transport_before
        assert ex._server_configs is server_configs_before
        assert ex._resolver is resolver_before
```

### Method

- One additive test method; no changes to `_make_executor` or the other
  two existing tests in this class.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| New test present | `grep -n "test_apply_config_does_not_recreate_transports_or_resolver" tests/test_tool_executor_routing.py` | 1 match |
| Test run | `uv run pytest tests/test_tool_executor_routing.py -k does_not_recreate -v` | passes |
| Full file regression | `uv run pytest tests/test_tool_executor_routing.py -v` | all pass |
