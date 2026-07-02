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
import hashlib
import logging
import time
from collections import OrderedDict
from dataclasses import dataclass
from typing import Any, Protocol

import httpx
import orjson

from shared import plugin_registry
from shared.json_utils import dumps as _json_dumps
from shared.mcp_config import (
    McpServerConfig,
    McpServerHealthRegistry,
    McpServerHealthState,
)
from shared.route_resolver import ToolRouteResolver
from shared.tool_cache import CacheEntry
from shared.tool_constants import DELETE_TOOLS, WRITE_TOOLS

logger = logging.getLogger(__name__)

# Plugin tool return value: (output: str, is_error: bool)
_PLUGIN_RESULT_TUPLE_LENGTH = 2


# ── Typed result DTOs ─────────────────────────────────────────────────────────


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


# ─────────────────────────────────────────────────────────────────────────────
# Transport implementations
# ─────────────────────────────────────────────────────────────────────────────


class TransportError(Exception):
    """Raised by transport layers when a transport-level failure occurs.

    Distinguishes transport failures (network down, timeout, process crash)
    from tool-level errors (MCP server responds with is_error=true).
    """


class HttpTransport:
    """Calls /v1/call_tool on a running HTTP MCP server via httpx."""

    def __init__(
        self,
        http: httpx.AsyncClient,
        base_url: str,
        server_key: str,
        cfg: McpServerConfig | None = None,
        timeout_sec: float = 60.0,
    ) -> None:
        self._http = http
        self._base_url = base_url
        self._server_key = server_key
        self._auth_token: str = cfg.auth_token if cfg is not None else ""
        self._timeout = timeout_sec
        self._session_id: str = ""

    def set_session_id(self, session_id: str) -> None:
        """Inject session ID to be forwarded as X-Session-Id header on every call."""
        self._session_id = session_id

    @staticmethod
    def _parse_http_response(resp: httpx.Response) -> ToolCallResult:
        """Parse HTTP response body and return a ToolCallResult.

        Raises ValueError if the response structure is invalid.
        """
        data = orjson.loads(resp.content)
        if not isinstance(data, dict):
            raise ValueError(
                f"MCP /v1/call_tool returned non-dict: {type(data).__name__}"
            )
        result_val = data.get("result")
        if not isinstance(result_val, str):
            raise ValueError("MCP /v1/call_tool missing 'result' str field")
        is_error_val = data.get("is_error", False)
        if not isinstance(is_error_val, bool):
            raise ValueError(
                f"MCP 'is_error' must be bool, got {type(is_error_val).__name__}"
            )
        x_request_id = resp.headers.get("x-request-id", "")
        return ToolCallResult.from_transport(
            output=result_val, is_error=is_error_val, request_id=x_request_id
        )

    _RETRYABLE_STATUS: frozenset[int] = frozenset({429, 502, 503, 504})
    _RETRY_MAX: int = 3

    async def call(self, name: str, args: dict[str, Any]) -> ToolCallResult:
        """POST to /v1/call_tool and return ToolCallResult.

        Raises TransportError on transport-level failures (network errors,
        timeouts, invalid responses).  Tool-level errors from the MCP server
        are returned as-is with is_error=True in the result.
        """
        headers: dict[str, str] = {}
        if self._auth_token:
            headers["Authorization"] = f"Bearer {self._auth_token}"
        if self._session_id:
            headers["X-Session-Id"] = self._session_id

        timeout = httpx.Timeout(self._timeout) if self._timeout > 0 else None
        last_exc: Exception | None = None
        for attempt in range(self._RETRY_MAX):
            try:
                resp = await self._http.post(
                    f"{self._base_url}/v1/call_tool",
                    json={"name": name, "args": args},
                    headers=headers,
                    timeout=timeout,
                )
                if resp.status_code in self._RETRYABLE_STATUS:
                    wait_sec = 2 ** (self._RETRY_MAX - attempt - 1)  # 4, 2, 1
                    logger.warning(
                        "HTTP %s from %s; retrying in %.0fs (attempt %d/%d)",
                        resp.status_code,
                        self._base_url,
                        wait_sec,
                        attempt + 1,
                        self._RETRY_MAX,
                    )
                    await asyncio.sleep(wait_sec)
                    continue
                resp.raise_for_status()
                result = self._parse_http_response(resp)
                return ToolCallResult(
                    output=result.output,
                    is_error=result.is_error,
                    request_id=result.request_id,
                    server_key=self._server_key,
                    error_type=result.error_type,
                )
            except httpx.TimeoutException as e:
                msg = f"[TimeoutException] tool={name} url={self._base_url}: {e}"
                logger.warning(msg)
                last_exc = TransportError(msg)
                break  # timeout = non-retryable
            except httpx.HTTPStatusError as e:
                msg = (
                    f"[HTTPStatusError] tool={name} url={self._base_url}"
                    f" status={e.response.status_code}"
                    f" response={e.response.text[:300]!r}"
                    f" — check {self._base_url}/health"
                )
                logger.warning(msg)
                last_exc = TransportError(msg)
                break
            except (httpx.RequestError, ValueError) as e:
                msg = (
                    f"[{type(e).__name__}] tool={name} url={self._base_url}: {e}"
                    f" — check {self._base_url}/health"
                )
                logger.warning(msg)
                last_exc = TransportError(msg)
                break
        else:
            msg = f"[Retry exhausted] tool={name} url={self._base_url} after {self._RETRY_MAX} attempts"
            logger.error(msg)
            raise TransportError(msg)
        raise last_exc or TransportError(f"call failed: {name}")


# Tools with side effects: writes, deletes, or shell execution.
# Used to auto-downgrade parallel execution to serial in execute_all_tool_calls().
_SIDE_EFFECT_TOOLS: frozenset[str] = (
    WRITE_TOOLS | DELETE_TOOLS | frozenset({"shell_run"})
)

# ─────────────────────────────────────────────────────────────────────────────
# Lifecycle protocol — implemented by agent/lifecycle.py; defined here so that
# shared/ does not need to import from agent/.
# ─────────────────────────────────────────────────────────────────────────────


class LifecycleProtocol(Protocol):
    """Protocol for MCP server lifecycle managers injected into ToolExecutor."""

    async def ensure_ready(self, server_key: str) -> None:
        """Ensure the MCP server identified by server_key is ready to accept calls."""
        ...


def is_side_effect(tool_name: str) -> bool:
    """Return True when the tool modifies state (write, delete, shell)."""
    return tool_name in _SIDE_EFFECT_TOOLS


def format_transport_error(
    *,
    source: str,
    phase: str,
    kind: str,
    url: str,
    status_code: int | None,
    retryable: bool,
    partial: bool,
) -> TransportErrorInfo:
    """Return TransportErrorInfo for LLM/tool transport failures; summary is one-line user-facing; detail is JSON for audit logs."""
    detail = _json_dumps(
        {
            "source": source,
            "phase": phase,
            "kind": kind,
            "status_code": status_code,
            "url": url,
            "retryable": retryable,
            "partial": partial,
        },
    )
    summary = f"[{source.upper()} {kind}] {phase} failure (retryable={retryable})"
    return TransportErrorInfo(summary=summary, detail=detail)


def tool_hash_key(name: str, args: dict[str, Any]) -> str:
    """Return a stable MD5 hash for a (tool name, args) pair; used for failed-call tracking (NOT for cache keys). Cache keys use plain string concatenation: f'{name}:{json_dumps(args)}'."""
    return hashlib.md5(  # nosec B324 — non-security hash for dedup key identity
        f"{name}:{_json_dumps(args)}".encode(),
        usedforsecurity=False,
    ).hexdigest()


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
            await self._lifecycle.ensure_ready(server_key)

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
        plugin_fn = plugin_registry.get_tool(tool_name)
        if plugin_fn is not None:
            try:
                result_raw = await plugin_fn(args)
            except Exception as e:  # noqa: BLE001 — plugin errors must not propagate
                msg = f"[plugin error] {tool_name}: {e}"
                logger.error(msg)
                return ToolCallResult(
                    output=msg,
                    is_error=True,
                    request_id="",
                    server_key="",
                    error_type="tool",
                )
            if (
                not isinstance(result_raw, tuple)
                or len(result_raw) < _PLUGIN_RESULT_TUPLE_LENGTH
            ):
                raise ValueError(
                    f"Plugin tool {tool_name!r} must return tuple[str, bool],"
                    f" got {type(result_raw).__name__}"
                )
            output, is_error = result_raw[0], result_raw[1]
            if not isinstance(output, str):
                raise TypeError(
                    f"Plugin {tool_name!r}: output must be str,"
                    f" got {type(output).__name__}"
                )
            if not isinstance(is_error, bool):
                raise TypeError(f"Plugin {tool_name!r}: is_error must be bool")
            return ToolCallResult(
                output=output,
                is_error=is_error,
                request_id="",
                server_key="",
                error_type="tool" if is_error else "",
            )
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
