"""Tests for /v1/tools malformed response validation in repl_health."""

import pytest
from agent.repl_health import _validate_tools_response

# --- _validate_tools_response unit tests ---


def test_valid_response_returns_names():
    names, err = _validate_tools_response(
        "srv", {"tools": [{"name": "tool_a"}, {"name": "tool_b"}]}
    )
    assert names == ["tool_a", "tool_b"]
    assert err is None


def test_not_a_dict():
    names, err = _validate_tools_response("srv", ["not", "a", "dict"])
    assert names == []
    assert err is not None
    assert "not a JSON object" in err


def test_missing_tools_field():
    names, err = _validate_tools_response("srv", {"other": "data"})
    assert names == []
    assert err is not None
    assert "missing 'tools'" in err


def test_tools_not_a_list():
    names, err = _validate_tools_response("srv", {"tools": {"name": "tool_a"}})
    assert names == []
    assert err is not None
    assert "must be a list" in err


def test_tool_entry_not_a_dict():
    names, err = _validate_tools_response("srv", {"tools": ["not_a_dict"]})
    assert names == []
    assert err is not None
    assert "not an object" in err


def test_tool_entry_missing_name():
    names, err = _validate_tools_response("srv", {"tools": [{"other_field": "x"}]})
    assert names == []
    assert err is not None
    assert "invalid name" in err


def test_tool_entry_empty_name():
    names, err = _validate_tools_response("srv", {"tools": [{"name": ""}]})
    assert names == []
    assert err is not None
    assert "invalid name" in err


def test_server_key_in_error_message():
    _, err = _validate_tools_response("my_server", {"tools": "not_a_list"})
    assert err is not None
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
async def test_collect_server_tool_names_invalid_json():
    """Invalid JSON response -> server in unreachable list."""
    from unittest.mock import AsyncMock, MagicMock

    from agent.repl_health import _collect_server_tool_names

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
    """Missing 'tools' field -> server in unreachable list."""
    from unittest.mock import AsyncMock, MagicMock

    from agent.repl_health import _collect_server_tool_names

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
