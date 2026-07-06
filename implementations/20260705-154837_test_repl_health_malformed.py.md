# Implementation: tests/test_repl_health_malformed.py — /v1/tools malformed response tests

## Goal

Test all 7 malformed cases for `/v1/tools` response validation, plus strict/non-strict behavior when malformed servers cause all-unreachable scenarios.

## Scope

**In**: Tests for `_validate_tools_response()` and `_collect_server_tool_names()` behavior with mocked HTTP.

**Out**: Source file changes.

## Assumptions

1. `_validate_tools_response()` is importable from `agent.repl_health`.
2. `_collect_server_tool_names()` is tested via integration with mocked `httpx.AsyncClient`.
3. Strict mode behavior (all unreachable → raise) is inherited from existing code and tested minimally here.

## Implementation

### Target file
`tests/test_repl_health_malformed.py`

### Procedure
Write unit tests for `_validate_tools_response()` and integration tests for the collector with mocked responses.

### Method

```python
import pytest
from agent.repl_health import _validate_tools_response


# --- _validate_tools_response unit tests ---

def test_valid_response_returns_names():
    names, err = _validate_tools_response("srv", {"tools": [{"name": "tool_a"}, {"name": "tool_b"}]})
    assert names == ["tool_a", "tool_b"]
    assert err is None


def test_not_a_dict():
    names, err = _validate_tools_response("srv", ["not", "a", "dict"])
    assert names == []
    assert "not a JSON object" in err


def test_missing_tools_field():
    names, err = _validate_tools_response("srv", {"other": "data"})
    assert names == []
    assert "missing 'tools'" in err


def test_tools_not_a_list():
    names, err = _validate_tools_response("srv", {"tools": {"name": "tool_a"}})
    assert names == []
    assert "must be a list" in err


def test_tool_entry_not_a_dict():
    names, err = _validate_tools_response("srv", {"tools": ["not_a_dict"]})
    assert names == []
    assert "not an object" in err


def test_tool_entry_missing_name():
    names, err = _validate_tools_response("srv", {"tools": [{"other_field": "x"}]})
    assert names == []
    assert "invalid name" in err


def test_tool_entry_empty_name():
    names, err = _validate_tools_response("srv", {"tools": [{"name": ""}]})
    assert names == []
    assert "invalid name" in err


def test_server_key_in_error_message():
    _, err = _validate_tools_response("my_server", {"tools": "not_a_list"})
    assert "my_server" in err


def test_valid_single_tool():
    names, err = _validate_tools_response("srv", {"tools": [{"name": "my_tool"}]})
    assert names == ["my_tool"]
    assert err is None


def test_empty_tools_list():
    names, err = _validate_tools_response("srv", {"tools": []})
    assert names == []
    assert err is None


# --- collector integration tests (mocked HTTP) ---

@pytest.mark.asyncio
async def test_collect_server_tool_names_invalid_json(respx_mock):
    """Invalid JSON response → server in unreachable list."""
    from agent.repl_health import _collect_server_tool_names
    from unittest.mock import AsyncMock, MagicMock
    import httpx

    ctx = MagicMock()
    srv = MagicMock()
    srv.transport = "http"
    srv.url = "http://srv1.test"
    ctx.cfg.mcp.mcp_servers = {"srv1": srv}

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.side_effect = ValueError("invalid json")
    mock_http = AsyncMock()
    mock_http.get.return_value = mock_response
    ctx.services_required.http = mock_http

    names, unreachable = await _collect_server_tool_names(ctx)
    assert "srv1" in unreachable
    assert len(names) == 0


@pytest.mark.asyncio
async def test_collect_server_tool_names_missing_tools_field():
    """Missing 'tools' field → server in unreachable list."""
    from agent.repl_health import _collect_server_tool_names
    from unittest.mock import AsyncMock, MagicMock

    ctx = MagicMock()
    srv = MagicMock()
    srv.transport = "http"
    srv.url = "http://srv1.test"
    ctx.cfg.mcp.mcp_servers = {"srv1": srv}

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"other": "data"}
    mock_http = AsyncMock()
    mock_http.get.return_value = mock_response
    ctx.services_required.http = mock_http

    names, unreachable = await _collect_server_tool_names(ctx)
    assert "srv1" in unreachable
```

## Validation plan

- `uv run pytest tests/test_repl_health_malformed.py -v` — all pass.
- `ruff check tests/test_repl_health_malformed.py` — 0 errors.
