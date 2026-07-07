#!/usr/bin/env python3
"""tool_executor.py
MCP tool execution layer.

Provides HttpTransport implementation for POST /v1/call_tool over httpx.

ToolExecutor routes tool calls to the appropriate server via ToolRouteResolver,
applies TTL caching on successful results, and delegates execution to the
configured transport.
"""

import asyncio
import contextlib
import logging
import time
from collections import OrderedDict
from typing import Any, Protocol

import httpx

from shared.http_transport import HttpTransport, TransportError
from shared.json_utils import dumps as _json_dumps
from shared.mcp_config import (
    McpServerConfig,
    McpServerHealthRegistry,
    McpServerHealthState,
)
from shared.plugin_tool_invoker import PluginToolInvoker
from shared.route_resolver import ToolRouteResolver
from shared.tool_cache import CacheEntry
from shared.tool_executor_helpers import (  # noqa: F401 — re-export for backward compat
    format_transport_error,
    is_side_effect,
    tool_hash_key,
)
from shared.transport_dto import (
    ToolCallResult,  # noqa: F401 — re-export for backward compat
    TransportErrorInfo,  # noqa: F401 — re-export for backward compat
)

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Lifecycle protocol — implemented by agent/lifecycle.py; defined here so that
# shared/ does not need to import from agent/.
# ─────────────────────────────────────────────────────────────────────────────


class LifecycleProtocol(Protocol):
    """Protocol for MCP server lifecycle managers injected into ToolExecutor."""

    async def ensure_ready(self, server_key: str) -> None:
        """Ensure the MCP server identified by server_key is ready to accept calls."""
        ...


# ─────────────────────────────────────────────────────────────────────────────
# ToolExecutor
# ─────────────────────────────────────────────────────────────────────────────


class ToolExecutor:
    """Routes tool calls to the appropriate MCP server transport with TTL caching; only successful results are cached."""

    def __init__(
        self,
        http: httpx.AsyncClient,
        cache_ttl: float,
        server_configs: dict[str, McpServerConfig],
        cache_max_size: int = 0,
        concurrency_limits: dict[str, int] | None = None,
        lifecycle: LifecycleProtocol | None = None,
        repeated_tool_error_threshold: int = 3,
        discovery_map: dict[str, str] | None = None,
    ) -> None:
        self._http = http
        self._cache_ttl = cache_ttl
        self._cache_max_size = cache_max_size
        self._server_configs = server_configs
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.stat_cache_hits: int = 0
        self.stat_tool_errors: dict[str, int] = {}
        self.stat_transport_errors: dict[str, int] = {}
        self._tool_error_threshold = repeated_tool_error_threshold
        self._lifecycle: LifecycleProtocol | None = lifecycle
        self._health_registry: McpServerHealthRegistry | None = None
        self._inflight: dict[str, asyncio.Future[ToolCallResult]] = {}

        # concurrency_limits: server_key -> max concurrent calls.
        # Semaphores are created lazily inside _raw_execute() to avoid event loop issues.
        self._concurrency_limits: dict[str, int] = dict(concurrency_limits or {})
        self._semaphores: dict[str, asyncio.Semaphore] | None = None

        # Validate concurrency_limits keys against configured server keys.
        known_keys = set(server_configs.keys())
        unknown_keys = set(self._concurrency_limits) - known_keys
        if unknown_keys:
            logger.warning(
                "tool_concurrency_limits: unknown server key(s) %r;"
                " Semaphore will not be applied for these tools.",
                sorted(unknown_keys),
            )

        # Initialise transports: HTTP servers get their transport immediately.
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

        self._resolver = ToolRouteResolver(
            server_configs, discovery_map=discovery_map or {}
        )
        self._plugin_invoker = PluginToolInvoker()

    def apply_config(self, *, cache_ttl: float | None = None) -> None:
        """Update hot-reloadable configuration fields without recreating the instance."""
        if cache_ttl is not None:
            self._cache_ttl = cache_ttl

    def set_lifecycle(self, lifecycle: LifecycleProtocol | None) -> None:
        """Inject or replace the lifecycle manager after construction."""
        self._lifecycle = lifecycle

    def set_health_registry(self, registry: McpServerHealthRegistry | None) -> None:
        """Inject or replace the health registry after construction."""
        self._health_registry = registry

    def set_session_id(self, session_id: str) -> None:
        """Propagate session ID to all HttpTransport instances for audit logging."""
        for transport in self._transports.values():
            if isinstance(transport, HttpTransport):
                transport.set_session_id(session_id)

    def _ensure_semaphores(self) -> None:
        """Initialise per-server Semaphores lazily on first use.

        Safe because asyncio is single-threaded and this branch completes
        before the first await in _raw_execute.
        """
        if self._semaphores is None and self._concurrency_limits:
            self._semaphores = {
                key: asyncio.Semaphore(n)
                for key, n in self._concurrency_limits.items()
                if n > 0
            }

    def _transport_missing_msg(self, server_key: str) -> str:
        """Return the appropriate error message when a transport is not registered."""
        return f"No transport configured for server {server_key!r}"

    def _error_result(
        self,
        server_key: str,
        output: str,
        error_type: str = "tool",
    ) -> ToolCallResult:
        """Return a ToolCallResult with is_error=True."""
        return ToolCallResult(
            output=output,
            is_error=True,
            request_id="",
            server_key=server_key,
            error_type=error_type,
        )

    def _success_result(self, result: ToolCallResult) -> ToolCallResult:
        """Return the transport result unchanged."""
        return result

    def _record_success(self, server_key: str, result: ToolCallResult) -> None:
        """Record a successful transport call; tool-level errors are still success."""
        if self._health_registry is not None:
            self._health_registry.record_success(server_key)
        if result.is_error and result.error_type == "tool":
            self.stat_tool_errors[server_key] = (
                self.stat_tool_errors.get(server_key, 0) + 1
            )

    def _record_transport_error(
        self, server_key: str, e: TransportError
    ) -> ToolCallResult:
        """Record a transport-level failure and return an error result."""
        self.stat_transport_errors[server_key] = (
            self.stat_transport_errors.get(server_key, 0) + 1
        )
        if self._health_registry is not None:
            state = self._health_registry.record_failure(server_key)
            logger.warning(
                "transport failure for %r: %s (state=%s)",
                server_key,
                e,
                state.value,
            )
        return ToolCallResult(
            output=str(e),
            is_error=True,
            request_id="",
            server_key=server_key,
            error_type="transport",
        )

    def _check_health(self, server_key: str) -> ToolCallResult | None:
        """Return an error result if the server is unavailable; None if healthy."""
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

    async def _execute_with_semaphore(
        self,
        transport: HttpTransport,
        tool_name: str,
        args: dict[str, Any],
        sem: asyncio.Semaphore | None,
    ) -> ToolCallResult:
        """Execute via transport under a semaphore (if configured)."""
        async with self._maybe_semaphore(sem):
            return await transport.call(tool_name, args)

    @staticmethod
    def _maybe_semaphore(
        sem: asyncio.Semaphore | None,
    ) -> contextlib.AbstractAsyncContextManager[None]:
        """Return an async context manager that acquires the semaphore if present."""
        if sem is not None:
            return sem
        return contextlib.nullcontext()

    async def _raw_execute(
        self,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Execute tool via the appropriate transport; applies per-server-key Semaphore when configured."""
        server_key = self._resolver.resolve(tool_name)

        # Health check
        if err := self._check_health(server_key):
            return err

        # Lifecycle ensure_ready
        if self._lifecycle is not None:
            try:
                await self._lifecycle.ensure_ready(server_key)
            except (OSError, RuntimeError) as e:
                msg = f"Lifecycle ensure_ready failed for {server_key!r}: {e}"
                logger.error(msg)
                if self._health_registry is not None:
                    self._health_registry.record_failure(server_key)
                return self._error_result(server_key, msg, error_type="transport")

        # Transport resolution
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

    async def _execute_with_cache(
        self,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Execute a tool: return cached result on hit; execute and store on miss."""
        cache_key = f"{tool_name}:{_json_dumps(args)}"
        if (cached := self._cache.get(cache_key)) is not None:
            age = time.time() - cached.cached_at
            if age < self._cache_ttl:
                self._cache.move_to_end(cache_key)  # LRU: mark as recently used
                self.stat_cache_hits += 1
                logger.info("Tool cache hit: %s (age=%.0fs)", tool_name, age)
                return ToolCallResult(
                    output=cached.output,
                    is_error=cached.is_error,
                    request_id="",
                    server_key="",
                    error_type="tool" if cached.is_error else "",
                )
            del self._cache[cache_key]
        result = await self._execute_with_stampede_protection(
            cache_key, tool_name, args
        )
        if not result.is_error:
            self._store_and_evict(cache_key, result)
        return result

    async def _execute_with_stampede_protection(
        self,
        cache_key: str,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Share inflight future among concurrent callers to prevent stampede."""
        inflight = self._inflight.get(cache_key)
        if inflight is not None and not inflight.done():
            return await inflight
        if inflight is not None and inflight.done():
            return inflight.result()
        loop = asyncio.get_running_loop()
        inflight = loop.create_future()
        self._inflight[cache_key] = inflight
        try:
            result = await self._raw_execute(tool_name, args)
            if not inflight.done():
                inflight.set_result(result)
            return result
        finally:
            self._inflight.pop(cache_key, None)

    def _store_and_evict(self, cache_key: str, result: ToolCallResult) -> None:
        """Store a non-error result in the cache and evict LRU entry if needed."""
        self._cache[cache_key] = CacheEntry(
            output=result.output, is_error=result.is_error, cached_at=time.time()
        )
        if self._cache_max_size > 0 and len(self._cache) > self._cache_max_size:
            evicted_key, _ = self._cache.popitem(last=False)
            logger.debug("Tool cache LRU evict: %r", evicted_key)

    async def execute(
        self,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Execute a tool. Plugin tools bypass cache and MCP routing; others use cache."""
        plugin_result = await self._plugin_invoker.try_execute(tool_name, args)
        if plugin_result is not None:
            return plugin_result
        return await self._execute_with_cache(tool_name, args)

    def clear_cache(self) -> None:
        """Evict all cached tool results."""
        self._cache.clear()

    def get_error_counters(self) -> dict[str, dict[str, int]]:
        """Return per-server error counters: {server_key: {"transport": N, "tool": N}}."""
        all_keys = set(self.stat_transport_errors) | set(self.stat_tool_errors)
        return {
            k: {
                "transport": self.stat_transport_errors.get(k, 0),
                "tool": self.stat_tool_errors.get(k, 0),
            }
            for k in all_keys
        }
