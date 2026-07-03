#!/usr/bin/env python3
"""shared/transport_dto.py — Transport-level data classes for MCP tool execution."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ToolCallResult:
    """Typed result from a single tool call execution."""

    output: str
    is_error: bool
    request_id: str  # x-request-id from HTTP transport; "" for plugin/cache
    server_key: str  # server key that handled the call; "" for plugin tools
    error_type: str = ""  # "transport" | "tool" | "" (empty on success)

    @classmethod
    def from_transport(
        cls, output: str, is_error: bool, request_id: str = ""
    ) -> "ToolCallResult":
        """Construct a ToolCallResult with default server_key and error_type."""
        return cls(
            output=output,
            is_error=is_error,
            request_id=request_id,
            server_key="",
            error_type="tool" if is_error else "",
        )


@dataclass(frozen=True)
class TransportErrorInfo:
    """Structured error info for LLM/tool transport failures (audit logs)."""

    summary: str
    detail: str  # JSON-encoded dict for audit log
