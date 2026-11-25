#!/usr/bin/env python3
"""scripts/shared/transport_dto.py — Transport-level data classes for MCP tool execution."""

from dataclasses import dataclass
from typing import Literal

from shared.execution_mode import ExecutionMode
from shared.mcp_health import McpServerHealthState


@dataclass(frozen=True)
class DynamicAvailabilityHint:
    """Advisory dynamic-availability signal on a structured tool result.

    Advisory only: the hint never gates, reroutes, or retries a call, and
    never changes LLM tool visibility or static availability. ``reason`` is
    a closed literal set so server-supplied free text can never enter it.
    """

    reason: Literal["server_unavailable", "half_open_trial_in_progress"]
    circuit_state: McpServerHealthState
    retry_after_seconds: (
        int | None
    )  # seconds, never negative; None when no timing applies


@dataclass(frozen=True)
class ToolExecutionContext:
    """Immutable logical-call identity carried from preparation to the wire.

    Plain-data only: ``shared`` is an import-linter leaf, so no agent types
    may appear here. The wider identity ids (session/workflow/task/turn) ride
    on the audit event side (``ToolExecEvent``/``execution_snapshot_json``);
    ``server_key`` and the approval reference are not knowable at preparation
    time and are deliberately absent. ``execution_mode`` is the shared mode
    vocabulary from ``shared.execution_mode`` and defaults to ``applied``, so
    an existing caller that does not resolve a mode still means a real
    execution.
    """

    call_id: str  # uuid7 logical call id, generated once at preparation
    tool: str  # tool name as dispatched
    args_hash: str  # hex sha256 over canonical-JSON args; grant comparison key
    operation: str  # RPC operation name (e.g. "call_tool")
    execution_mode: ExecutionMode = "applied"  # shared mode vocabulary


@dataclass(frozen=True)
class ToolCallResult:
    """Typed result from a single tool call execution.

    ``error_type`` may also be ``"routing"``: it marks a failure before any
    transport call (see ``ToolExecutor.execute``).
    """

    output: str  # tool result text, or error message when is_error=True
    is_error: bool  # True if the call failed (transport or tool error)
    request_id: str  # x-request-id from HTTP transport; "" for cache hits
    server_key: str  # server key that handled the call
    source: str = ""  # "mcp" for MCP tools, "" for error paths
    error_type: str = ""  # "transport" | "tool" | "routing" | "" (empty on success)
    availability_hint: DynamicAvailabilityHint | None = (
        None  # advisory dynamic health signal; None means no signal
    )
    context: ToolExecutionContext | None = (
        None  # identity this call executed with; None on pre-dispatch routing errors
    )
    dispatch_stage: Literal["", "sent", "response"] = (
        ""  # how far the call got: "" nothing sent, "sent" no response,
        # "response" HTTP response received; the intent-state writer uses this
        # to keep a post-send failure at a dispatch-stage state (never replayed)
    )
    execution_mode: str = (
        ""  # server-reported execution mode; "" when the server did not report one
    )
    side_effect_applied: bool = (
        False  # True when the server ran the handler and the tool is side-effecting
    )

    @classmethod
    def from_transport(
        cls,
        output: str,
        is_error: bool,
        request_id: str = "",
        execution_mode: str = "",
        side_effect_applied: bool = False,
    ) -> "ToolCallResult":
        """Build a ToolCallResult from a successful transport response.

        This method handles HTTP 200 responses carrying is_error: true
        (i.e., tool-level errors). Transport failures are produced by the
        invoker via _error_result(..., error_type="transport"), not here.
        The result metadata is carried through unchanged; absent means the
        server reported nothing.
        """
        return cls(
            output=output,
            is_error=is_error,
            request_id=request_id,
            server_key="",
            source="mcp",
            error_type="tool" if is_error else "",
            execution_mode=execution_mode,
            side_effect_applied=side_effect_applied,
        )


@dataclass(frozen=True)
class TransportErrorInfo:
    """Structured error info for LLM/tool transport failures (audit logs)."""

    summary: str
    detail: str  # JSON-encoded dict for audit log
