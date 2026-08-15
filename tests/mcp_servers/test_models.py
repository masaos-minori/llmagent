"""tests/mcp_servers/test_models.py

Characterization tests for mcp_servers/models.py's shared Pydantic models
(CallToolRequest, CallToolResponse). Locks the name-validation and
strip-normalization behavior that no other test module exercises directly.
"""

from __future__ import annotations

import pytest
from mcp_servers.models import CallToolRequest, CallToolResponse
from pydantic import ValidationError


class TestCallToolRequestNameValidation:
    def test_blank_name_raises(self) -> None:
        with pytest.raises(ValidationError, match="Tool name must not be blank"):
            CallToolRequest(name="", args={})

    def test_whitespace_only_name_raises(self) -> None:
        with pytest.raises(ValidationError, match="Tool name must not be blank"):
            CallToolRequest(name="   ", args={})

    def test_name_is_stripped(self) -> None:
        req = CallToolRequest(name="  read_file  ", args={})
        assert req.name == "read_file"

    def test_args_defaults_to_empty_dict(self) -> None:
        req = CallToolRequest(name="read_file")
        assert req.args == {}


class TestCallToolResponse:
    def test_round_trip(self) -> None:
        resp = CallToolResponse(result="ok", is_error=False)
        assert resp.result == "ok"
        assert resp.is_error is False
