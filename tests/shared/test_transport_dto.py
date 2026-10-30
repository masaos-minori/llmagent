"""tests/shared/test_transport_dto.py
Unit tests for ToolCallResult.from_transport error_type classification.
"""

from __future__ import annotations

import dataclasses

import pytest
from shared.mcp_health import (
    HEALTH_REASON_HALF_OPEN_TRIAL_IN_PROGRESS,
    HEALTH_REASON_SERVER_UNAVAILABLE,
    McpServerHealthState,
)
from shared.transport_dto import DynamicAvailabilityHint, ToolCallResult


class TestFromTransport:
    def test_server_reported_error_is_tool_error(self) -> None:
        # The server responded (is_error=True in the body): a tool error, not a
        # transport failure — see docs/22_mcp tool-vs-transport error table.
        result = ToolCallResult.from_transport(
            output="file not found", is_error=True, request_id="req-1"
        )

        assert result.is_error
        assert result.error_type == "tool"
        assert result.request_id == "req-1"
        assert result.source == "mcp"

    def test_success_has_empty_error_type(self) -> None:
        result = ToolCallResult.from_transport(output="ok", is_error=False)

        assert not result.is_error
        assert result.error_type == ""


class TestAvailabilityHint:
    """DynamicAvailabilityHint / ToolCallResult.availability_hint contract.

    Default None everywhere (legacy shape lock), explicit construction
    round-trip, frozen semantics, and the closed reason-literal shape.
    """

    def test_from_transport_leaves_hint_none(self) -> None:
        result = ToolCallResult.from_transport(output="ok", is_error=False)
        assert result.availability_hint is None

    def test_legacy_keyword_construction_leaves_hint_none(self) -> None:
        result = ToolCallResult(
            output="err",
            is_error=True,
            request_id="",
            server_key="mdq",
            source="mcp",
            error_type="tool",
        )
        assert result.availability_hint is None
        assert result.server_key == "mdq"

    def test_hint_round_trips_when_constructed_explicitly(self) -> None:
        hint = DynamicAvailabilityHint(
            reason=HEALTH_REASON_SERVER_UNAVAILABLE,
            circuit_state=McpServerHealthState.UNAVAILABLE,
            retry_after_seconds=12,
        )
        result = ToolCallResult(
            output="err",
            is_error=True,
            request_id="",
            server_key="mdq",
            source="mcp",
            error_type="tool",
            availability_hint=hint,
        )
        assert result.availability_hint == hint
        assert result.availability_hint.reason == "server_unavailable"
        assert result.availability_hint.retry_after_seconds == 12

    def test_half_open_reason_and_none_retry_after_accepted(self) -> None:
        hint = DynamicAvailabilityHint(
            reason=HEALTH_REASON_HALF_OPEN_TRIAL_IN_PROGRESS,
            circuit_state=McpServerHealthState.HALF_OPEN,
            retry_after_seconds=None,
        )
        assert hint.reason == "half_open_trial_in_progress"
        assert hint.retry_after_seconds is None

    def test_frozen_semantics(self) -> None:
        result = ToolCallResult(
            output="ok", is_error=False, request_id="", server_key="mdq"
        )
        with pytest.raises(dataclasses.FrozenInstanceError):
            result.availability_hint = None  # type: ignore[misc] — frozen dataclass field write; mypy flags the direct assignment though the runtime FrozenInstanceError guard blocks it, which this assertion verifies.
        replaced = dataclasses.replace(
            result,
            availability_hint=DynamicAvailabilityHint(
                reason=HEALTH_REASON_SERVER_UNAVAILABLE,
                circuit_state=McpServerHealthState.UNAVAILABLE,
                retry_after_seconds=0,
            ),
        )
        assert replaced.availability_hint is not None
        assert replaced.availability_hint.retry_after_seconds == 0
