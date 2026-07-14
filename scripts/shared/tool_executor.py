#!/usr/bin/env python3
"""tool_executor.py

MCP tool execution layer.

Provides HttpTransport implementation for POST /v1/call_tool over httpx.

ToolExecutor routes tool calls to the appropriate server via ToolRouteResolver,
applies TTL caching on successful results, and delegates execution to the
configured transport.
"""

import asyncio
import logging
import time
from collections import OrderedDict
from typing import Any, cast

import httpx
from shared.http_transport import TransportError
from shared.json_utils import dumps as _json_dumps
from shared.mcp_config import (
    McpServerConfig,
    StartupMode,
)
from shared.plugin_tool_invoker import PluginToolInvoker
from shared.route_resolver import ToolRouteResolver
from shared.tool_cache import CacheEntry
from shared.tool_lifecycle import LifecycleProtocol
from shared.tool_transport_invoker import ToolTransportInvoker
from shared.transport_dto import ToolCallResult

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# ToolExecutor
# ─────────────────────────────────────────────────────────────────────────────


class ToolExecutor(ToolTransportInvoker):
    """Routes tool calls to the appropriate MCP server transport with TTL caching; only successful results are cached."""

    def __init__(
        self,
        http: httpx.AsyncClient,
        cache_ttl: float,
        server_configs: dict[str, McpServerConfig],
        cache_max_size: int = 0,
        concurrency_limits: dict[str, int] | None = None,
        lifecycle: LifecycleProtocol | None = None,
        discovery_map: dict[str, str] | None = None,
    ) -> None:
        super().__init__(http, server_configs, concurrency_limits, lifecycle)
        self._cache_ttl = cache_ttl
        self._cache_max_size = cache_max_size
        self._server_configs = server_configs
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.stat_cache_hits: int = 0
        self._inflight: dict[str, asyncio.Future[ToolCallResult]] = {}

        self._resolver = ToolRouteResolver(
            server_configs, discovery_map=discovery_map or {}
        )
        self._plugin_invoker = PluginToolInvoker()

    def apply_config(self, *, cache_ttl: float | None = None) -> None:
        """Update hot-reloadable configuration fields without recreating the instance."""
        if cache_ttl is not None:
            self._cache_ttl = cache_ttl

    def _check_startup_mode(self, server_key: str) -> ToolCallResult | None:
        """Return an error result if the server is disabled (startup_mode=none); None otherwise."""
        cfg = self._server_configs.get(server_key)
        if cfg is not None and cfg.startup_mode == StartupMode.NONE:
            msg = (
                f"MCP server {server_key!r} is disabled (startup_mode=none) "
                "and cannot be used"
            )
            logger.warning(msg)
            return self._error_result(server_key, msg, error_type="tool")
        return None

    async def _raw_execute(
        self,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallResult:
        """Execute tool via the appropriate transport; applies per-server-key Semaphore when configured."""
        server_key = self._resolver.resolve(tool_name)

        # Startup mode gate (startup_mode=none is disabled by design)
        if err := self._check_startup_mode(server_key):
            return err

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
        """Share inflight future among concurrent callers to prevent stampede.

        If _raw_execute() raises, the exception is propagated to every concurrent
        waiter via inflight.set_exception() -- not just the caller that triggered
        execution -- so no waiter hangs indefinitely on a failed shared future.
        """
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
        except Exception as exc:  # noqa: BLE001 -- must release all inflight waiters regardless of exception type
            if not inflight.done():
                inflight.set_exception(exc)
            raise
        else:
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
        return cast(dict[str, dict[str, int]], super().get_error_counters())
