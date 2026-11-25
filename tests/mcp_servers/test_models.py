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

    def test_metadata_defaults(self) -> None:
        resp = CallToolResponse(result="ok", is_error=False)
        assert resp.execution_mode == ""
        assert resp.side_effect_applied is False

    def test_metadata_round_trip(self) -> None:
        resp = CallToolResponse(
            result="ok",
            is_error=False,
            dedup_state="replayed",
            execution_mode="preview",
            side_effect_applied=False,
        )
        assert resp.execution_mode == "preview"
        assert resp.side_effect_applied is False

        applied = CallToolResponse(
            result="ok",
            is_error=False,
            execution_mode="applied",
            side_effect_applied=True,
        )
        assert applied.execution_mode == "applied"
        assert applied.side_effect_applied is True

    def test_serialized_key_set(self) -> None:
        resp = CallToolResponse(result="ok", is_error=False)
        assert set(resp.model_dump()) == {
            "result",
            "is_error",
            "dedup_state",
            "execution_mode",
            "side_effect_applied",
        }
