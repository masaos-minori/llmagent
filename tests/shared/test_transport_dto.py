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
from shared.transport_dto import (
    DynamicAvailabilityHint,
    ToolCallResult,
    ToolExecutionContext,
)


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

    def test_success_has_empty_metadata(self) -> None:
        result = ToolCallResult.from_transport(output="ok", is_error=False)

        assert not result.is_error
        assert result.error_type == ""
        assert result.execution_mode == ""
        assert result.side_effect_applied is False

    def test_from_transport_carries_result_metadata(self) -> None:
        result = ToolCallResult.from_transport(
            output="ok",
            is_error=False,
            request_id="req-2",
            execution_mode="preview",
            side_effect_applied=False,
        )

        assert result.execution_mode == "preview"
        assert result.side_effect_applied is False

    def test_from_transport_carries_applied_metadata(self) -> None:
        result = ToolCallResult.from_transport(
            output="ok",
            is_error=False,
            execution_mode="applied",
            side_effect_applied=True,
        )

        assert result.execution_mode == "applied"
        assert result.side_effect_applied is True

    def test_dedup_state_defaults_to_empty(self) -> None:
        # mcpai007 REQ-001: no dedup branch taken means "".
        result = ToolCallResult.from_transport(output="ok", is_error=False)
        assert result.dedup_state == ""

    def test_from_transport_carries_dedup_state(self) -> None:
        result = ToolCallResult.from_transport(
            output="ok",
            is_error=False,
            dedup_state="duplicate_hit",
        )
        assert result.dedup_state == "duplicate_hit"


class TestExecutionContextExecutionMode:
    """ToolExecutionContext.execution_mode contract: default, explicit value, frozen."""

    def test_defaults_to_applied(self) -> None:
        ctx = ToolExecutionContext(
            call_id="call-1",
            tool="write_file",
            args_hash="hash",
            operation="call_tool",
        )
        assert ctx.execution_mode == "applied"

    def test_accepts_preview_mode(self) -> None:
        ctx = ToolExecutionContext(
            call_id="call-1",
            tool="write_file",
            args_hash="hash",
            operation="call_tool",
            execution_mode="preview",
        )
        assert ctx.execution_mode == "preview"

    def test_stays_frozen(self) -> None:
        ctx = ToolExecutionContext(
            call_id="call-1",
            tool="write_file",
            args_hash="hash",
            operation="call_tool",
        )
        with pytest.raises(dataclasses.FrozenInstanceError):
            ctx.execution_mode = "preview"  # type: ignore[misc] — frozen dataclass field write; mypy flags the direct assignment though the runtime FrozenInstanceError guard blocks it, which this assertion verifies.
        assert (
            dataclasses.replace(ctx, execution_mode="preview").execution_mode
            == "preview"
        )


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
