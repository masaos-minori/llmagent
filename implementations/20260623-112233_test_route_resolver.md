# Implementation: Add `TestValidateRoutingDrift` to `tests/test_route_resolver.py`

## Goal

Add tests for `validate_routing_against_config()` and `validate_all_routing()` to `tests/test_route_resolver.py`.

## Scope

- **In-Scope:** Add new test class `TestValidateRoutingDrift` at the end of `tests/test_route_resolver.py`
- **Out-of-Scope:** Changes to existing test classes

## Assumptions verified

1. `MagicMock` is NOT imported in `tests/test_route_resolver.py` — confirmed by grep (no matches). Must add `from unittest.mock import MagicMock` import.
2. `McpServerConfig` is imported from `shared.mcp_config` at line 8 — confirmed.
3. `validate_routing_against_config` and `validate_all_routing` are importable from `shared.tool_registry` — confirmed at lines 189, 237.
4. `ToolRegistry` uses `_tools: dict[str, ToolDefinition]` and `_by_server: dict[str, list[str]]` — confirmed at lines 49-51. There is NO `_routes` attribute. Tests must use `registry.register(ToolDefinition(...))` to populate the registry.
5. `ToolDefinition` is a dataclass with fields `name: str`, `server_key: str` — confirmed at lines 37-43.
6. `validate_routing_against_config` skips servers with empty `cfg.tool_names` (returns `{}`) — confirmed at line 205.
7. The test file ends at line 182.

## Implementation

**Target file:** `tests/test_route_resolver.py`

**Procedure:**
1. Add `from unittest.mock import MagicMock` to the import block at the top of the file.
2. Append the new test class after the last line (182).

**Method:** Two Edit operations.

**Details:**

**Edit 1 — add MagicMock import:**

Current (lines 5-9):
```python
import logging

import pytest
from shared.mcp_config import McpServerConfig, StartupMode
from shared.route_resolver import ToolRouteResolver
```

Replacement:
```python
import logging
from unittest.mock import MagicMock

import pytest
from shared.mcp_config import McpServerConfig, StartupMode
from shared.route_resolver import ToolRouteResolver
```

**Edit 2 — append test class at end of file:**

Append after the last line of the file:

```python


class TestValidateRoutingDrift:
    def test_no_drift_when_config_matches_registry(self) -> None:
        """validate_routing_against_config returns {} when config tool_names are in the registry."""
        from shared.tool_registry import ToolDefinition, ToolRegistry, validate_routing_against_config

        registry = ToolRegistry()
        registry.register(ToolDefinition(name="read_text_file", server_key="file_read"))
        registry.register(ToolDefinition(name="list_directory", server_key="file_read"))

        cfg = MagicMock(spec=McpServerConfig)
        cfg.tool_names = ["read_text_file", "list_directory"]
        server_configs = {"file_read": cfg}

        result = validate_routing_against_config(registry=registry, server_configs=server_configs)
        assert result == {}

    def test_drift_detected_when_config_has_unregistered_tool(self) -> None:
        """validate_routing_against_config returns mismatch when config lists a tool not in registry."""
        from shared.tool_registry import ToolDefinition, ToolRegistry, validate_routing_against_config

        registry = ToolRegistry()
        registry.register(ToolDefinition(name="read_text_file", server_key="file_read"))

        cfg = MagicMock(spec=McpServerConfig)
        cfg.tool_names = ["read_text_file", "missing_tool"]
        server_configs = {"file_read": cfg}

        result = validate_routing_against_config(registry=registry, server_configs=server_configs)
        assert "file_read" in result
        assert any("missing_tool" in msg for msg in result["file_read"])

    def test_no_drift_when_config_tool_names_empty(self) -> None:
        """validate_routing_against_config skips servers with empty tool_names."""
        from shared.tool_registry import validate_routing_against_config

        cfg = MagicMock(spec=McpServerConfig)
        cfg.tool_names = []
        server_configs = {"some_server": cfg}

        result = validate_routing_against_config(server_configs=server_configs)
        assert result == {}
```

## Key corrections from original spec

- `_routes` attribute does not exist on `ToolRegistry`. Use `registry.register(ToolDefinition(name=..., server_key=...))` instead of directly assigning `registry._routes = {...}`.
- `MagicMock` is not imported in the file — must add `from unittest.mock import MagicMock`.
- Import `ToolDefinition` alongside `ToolRegistry` in test methods that construct registry entries.

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| New tests pass | `uv run pytest tests/test_route_resolver.py::TestValidateRoutingDrift -v` | All 3 PASSED |
| Full file | `uv run pytest tests/test_route_resolver.py -v` | No regressions |
| Lint | `uv run ruff check tests/test_route_resolver.py` | 0 errors |
