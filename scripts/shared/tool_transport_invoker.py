#!/usr/bin/env python3
"""shared/tool_transport_invoker.py — MCP transport invocation layer."""

from __future__ import annotations

import asyncio
import contextlib
import logging
from typing import Any

import httpx

from shared.http_transport import HttpTransport, TransportError
from shared.mcp_config import (
    McpServerConfig,
    McpServerHealthRegistry,
    McpServerHealthState,
)
from shared.tool_lifecycle import LifecycleProtocol
from shared.transport_dto import ToolCallResult

logger = logging.getLogger(__name__)


class ToolTransportInvoker:
    """Handles transport-level MCP invocation: health, lifecycle, semaphore, call, and recording."""

    def __init__(
        self,
        http: httpx.AsyncClient,
        server_configs: dict[str, McpServerConfig],
        concurrency_limits: dict[str, int] | None = None,
        lifecycle: LifecycleProtocol | None = None,
    ) -> None:
        """Initialize with HTTP client, server configs, and optional concurrency limits."""
        self._lifecycle = lifecycle
        self._health_registry: McpServerHealthRegistry | None = None
        self.stat_tool_errors: dict[str, int] = {}
        self.stat_transport_errors: dict[str, int] = {}
        self._concurrency_limits: dict[str, int] = dict(concurrency_limits or {})
        self._semaphores: dict[str, asyncio.Semaphore] | None = None

        known_keys = set(server_configs.keys())
        unknown_keys = set(self._concurrency_limits) - known_keys
        if unknown_keys:
            logger.warning(
                "tool_concurrency_limits: unknown server key(s) %r;"
                " Semaphore will not be applied for these server keys.",
                sorted(unknown_keys),
            )

        self._transports: dict[str, HttpTransport] = {}
        for key, cfg in server_configs.items():
            timeout_sec = (
                cfg.call_timeout_sec
                if hasattr(cfg, "call_timeout_sec") and cfg.call_timeout_sec
                else 60.0
            )
            self._transports[key] = HttpTransport(
                http, cfg.url, key, cfg, timeout_sec=timeout_sec
            )

    def set_lifecycle(self, lifecycle: LifecycleProtocol | None) -> None:
        """Attach a lifecycle protocol for pre-call readiness checks."""
        self._lifecycle = lifecycle

    def set_health_registry(self, registry: McpServerHealthRegistry | None) -> None:
        """Attach a health registry for post-call success/failure tracking."""
        self._health_registry = registry

    def set_session_id(self, session_id: str) -> None:
        """Propagate the current session ID to all transports."""
        for transport in self._transports.values():
            if isinstance(transport, HttpTransport):
                transport.set_session_id(session_id)

    def get_error_counters(self) -> dict[str, dict[str, int]]:
        """Return per-server transport and tool error counts."""
        all_keys = set(self.stat_transport_errors) | set(self.stat_tool_errors)
        return {
            k: {
                "transport": self.stat_transport_errors.get(k, 0),
                "tool": self.stat_tool_errors.get(k, 0),
            }
            for k in all_keys
        }

    def _ensure_semaphores(self) -> None:
        """Lazily create concurrency semaphores from configuration limits."""
        if self._semaphores is None and self._concurrency_limits:
            self._semaphores = {
                key: asyncio.Semaphore(n)
                for key, n in self._concurrency_limits.items()
                if n > 0
            }

    @staticmethod
    def _maybe_semaphore(
        sem: asyncio.Semaphore | None,
    ) -> contextlib.AbstractAsyncContextManager[None]:
        """Return the semaphore as an async context manager, or nullcontext if None."""
        if sem is not None:
            return sem
        return contextlib.nullcontext()

    def _transport_missing_msg(self, server_key: str) -> str:
        """Build an error message for a missing transport by server key."""
        return f"No transport configured for server {server_key!r}"

    def _error_result(
        self,
        server_key: str,
        output: str,
        error_type: str = "tool",
    ) -> ToolCallResult:
        """Construct a ToolCallResult indicating a tool-level error."""
        return ToolCallResult(
            output=output,
            is_error=True,
            request_id="",
            server_key=server_key,
            source="mcp",
            error_type=error_type,
        )

    def _check_health(self, server_key: str) -> ToolCallResult | None:
        """Check MCP server health before dispatching; returns error result if unavailable."""
        if self._health_registry is None:
            return None
        state = self._health_registry.get_state(server_key)
        if state == McpServerHealthState.HALF_OPEN:
            logger.info("Health: %r is HALF_OPEN — allowing trial dispatch", server_key)
            return None
        if self._health_registry.is_unavailable(server_key):
            msg = f"MCP server {server_key!r} is currently unavailable (health check failed)"
            logger.warning(msg)
            return self._error_result(server_key, msg, error_type="tool")
        return None

    def _record_success(self, server_key: str, result: ToolCallResult) -> None:
        """Record a successful call for health tracking; increment tool error counter on tool errors."""
        if self._health_registry is not None:
            self._health_registry.record_success(server_key)
        if result.is_error and result.error_type == "tool":
            self.stat_tool_errors[server_key] = (
                self.stat_tool_errors.get(server_key, 0) + 1
            )

    def _record_transport_error(
        self, server_key: str, e: TransportError
    ) -> ToolCallResult:
        """Record a transport-layer error and update health state accordingly."""
        self.stat_transport_errors[server_key] = (
            self.stat_transport_errors.get(server_key, 0) + 1
        )
        if self._health_registry is not None:
            state = self._health_registry.record_failure(server_key)
            logger.warning(
                "transport failure for %r: %s (state=%s)", server_key, e, state.value
            )
        return ToolCallResult(
            output=str(e),
            is_error=True,
            request_id="",
            server_key=server_key,
            source="mcp",
            error_type="transport",
        )

    async def _execute_with_semaphore(
        self,
        transport: HttpTransport,
        tool_name: str,
        args: dict[str, Any],
        sem: asyncio.Semaphore | None,
    ) -> ToolCallResult:
        """Execute a transport call under optional concurrency semaphore."""
        async with self._maybe_semaphore(sem):
            return await transport.call(tool_name, args)

    async def invoke(
        self,
        server_key: str,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Invoke tool via transport; applies health check, lifecycle, semaphore, and recording."""
        if err := self._check_health(server_key):
            return err

        if self._lifecycle is not None:
            await self._lifecycle.ensure_ready(server_key)

        transport = self._transports.get(server_key)
        if transport is None:
            msg = self._transport_missing_msg(server_key)
            logger.error(msg)
            return self._error_result(server_key, msg, error_type="tool")

        self._ensure_semaphores()
        sem = (self._semaphores or {}).get(server_key)

        try:
            result = await self._execute_with_semaphore(transport, tool_name, args, sem)
            self._record_success(server_key, result)
            return result
        except TransportError as e:
            return self._record_transport_error(server_key, e)
