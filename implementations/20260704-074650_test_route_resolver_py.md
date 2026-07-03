# Implementation: Add routing isolation tests to `tests/test_route_resolver.py`

## Goal

Add `TestRoutingSourceIsolation` class with 2 tests to `tests/test_route_resolver.py`, confirming
that (1) config `tool_names` metadata does not affect `ToolRouteResolver.resolve()` behavior, and
(2) `ToolRouteResolver` does NOT fall back to `tool_constants.py` frozensets for unknown tools —
it raises `ValueError` instead.

## Scope

- In-Scope: Add `TestRoutingSourceIsolation` class with 2 test methods to the existing file
  `tests/test_route_resolver.py`.
- Out-of-Scope: No changes to `ToolRouteResolver`, `ToolRegistry`, or `tool_constants.py`.

## Assumptions

1. `tests/test_route_resolver.py` exists with an existing test class.
2. `ToolRouteResolver` is importable from `shared.route_resolver`.
3. `McpServerConfig` accepts a `tool_names` keyword argument (confirmed in require-28 analysis).
4. `ToolRouteResolver({})` with an empty dict raises `ValueError` for unknown tool names.
5. `uv run pytest` with `asyncio_mode = "auto"` is the test runner.

## Implementation

### Target file

`tests/test_route_resolver.py` (existing — add class at end)

### Procedure

1. Read the end of `tests/test_route_resolver.py` to find the correct append point.
2. Add `TestRoutingSourceIsolation` class with the 2 test methods below.
3. Run `uv run ruff check tests/test_route_resolver.py` — expect 0 errors.
4. Run `uv run pytest tests/test_route_resolver.py::TestRoutingSourceIsolation -v` — expect 2 passed.

### Method

Append to `tests/test_route_resolver.py`:

```python
class TestRoutingSourceIsolation:
    def test_config_tool_names_do_not_affect_routing(self) -> None:
        """Config tool_names is metadata only — ToolRouteResolver.resolve() ignores it."""
        from shared.mcp_config import McpServerConfig, TransportType

        cfg = McpServerConfig(
            transport=TransportType.HTTP,
            url="http://localhost",
            tool_names=["read_text_file"],  # config metadata — not a routing input
        )
        resolver = ToolRouteResolver({"file_read": cfg})
        assert resolver.resolve("read_text_file") == "file_read"

    def test_constants_not_used_directly_by_resolver(self) -> None:
        """ToolRouteResolver does not fall back to tool_constants frozensets."""
        resolver = ToolRouteResolver({})
        with pytest.raises(ValueError, match="[Uu]nknown tool"):
            resolver.resolve("nonexistent_tool_xyz")
```

### Details

- `test_config_tool_names_do_not_affect_routing` verifies that passing `tool_names=["read_text_file"]`
  to a config does NOT change routing — the tool is still resolved via `ToolRegistry`, not via the
  config list.
- `test_constants_not_used_directly_by_resolver` verifies that when no discovery map and no
  registry match exist, the resolver raises `ValueError` (not silently returns a frozenset-derived
  default).
- The imports (`ToolRouteResolver`, `pytest`) are already present at the top of
  `test_route_resolver.py`; no new imports are needed at the module level. The `McpServerConfig`
  and `TransportType` imports are done inline to avoid breaking existing test structure.

## Validation plan

```bash
# New isolation tests
uv run pytest tests/test_route_resolver.py::TestRoutingSourceIsolation -v
# Expected: 2 passed

# Full route resolver test suite
uv run pytest tests/test_route_resolver.py -q
# Expected: all pass

# Lint
uv run ruff check tests/test_route_resolver.py
# Expected: 0 errors
```
