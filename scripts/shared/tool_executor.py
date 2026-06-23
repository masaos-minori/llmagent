#!/usr/bin/env python3
"""tool_executor.py
MCP tool execution layer.

Provides two transport implementations:
  HttpTransport  — POST /v1/call_tool over httpx (default)
  StdioTransport — line-delimited JSON-RPC over subprocess stdin/stdout

ToolExecutor routes tool calls to the appropriate server via ToolRouteResolver,
applies TTL caching on successful results, and delegates execution to the
configured transport.
"""

import asyncio
import hashlib
import logging
import os
import time
from collections import OrderedDict
from dataclasses import dataclass
from pathlib import Path
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

# Seconds to wait for a stdio server response before treating it as a timeout.
_STDIO_CALL_TIMEOUT: float = 60.0


# ── Typed result DTOs ─────────────────────────────────────────────────────────


@dataclass(frozen=True)
class ToolCallResult:
    """Typed result from a single tool call execution."""

    output: str
    is_error: bool
    request_id: str  # x-request-id from HTTP transport; "" for stdio/plugin/cache
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
    ) -> None:
        self._http = http
        self._base_url = base_url
        self._server_key = server_key
        self._auth_token: str = cfg.auth_token if cfg is not None else ""
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
        try:
            resp = await self._http.post(
                f"{self._base_url}/v1/call_tool",
                json={"name": name, "args": args},
                headers=headers,
            )
            resp.raise_for_status()
            result = self._parse_http_response(resp)
            return ToolCallResult(
                output=result.output,
                is_error=result.is_error,
                request_id=result.request_id,
                server_key=self._server_key,
                error_type=result.error_type,
            )
        except httpx.HTTPStatusError as e:
            msg = (
                f"[HTTPStatusError] tool={name} url={self._base_url}"
                f" status={e.response.status_code}"
                f" response={e.response.text[:300]!r}"
                f" — check {self._base_url}/health"
            )
            logger.warning(msg)
            raise TransportError(msg) from e
        except (httpx.RequestError, ValueError) as e:
            msg = (
                f"[{type(e).__name__}] tool={name} url={self._base_url}: {e}"
                f" — check {self._base_url}/health"
            )
            logger.warning(msg)
            raise TransportError(msg) from e


class StdioTransport:
    """Calls an MCP server subprocess via stdin/stdout JSON-RPC; per-instance Lock serializes concurrent calls to prevent request/response interleaving."""

    def __init__(
        self,
        cmd: list[str],
        server_key: str,
        working_dir: str = "",
        env: dict[str, str] | None = None,
    ) -> None:
        self._cmd = cmd
        self._server_key = server_key
        self._working_dir = working_dir
        self._env_overrides: dict[str, str] = env or {}
        self._proc: asyncio.subprocess.Process | None = None
        self._lock: asyncio.Lock | None = None  # created after the event loop starts
        self._req_id: int = 0

    def _get_lock(self) -> asyncio.Lock:
        # Lazily create the Lock after the event loop is running.
        if self._lock is None:
            self._lock = asyncio.Lock()
        return self._lock

    async def start(self) -> None:
        """Spawn the subprocess. No-op if it is already alive."""
        if self.is_alive():
            return
        cwd: str | None = None
        if self._working_dir:
            if not Path(self._working_dir).is_dir():
                raise ValueError(
                    f"StdioTransport: working_dir {self._working_dir!r} does not exist",
                )
            cwd = self._working_dir
        merged_env: dict[str, str] | None = None
        if self._env_overrides:
            merged_env = {**os.environ, **self._env_overrides}
        self._proc = await asyncio.create_subprocess_exec(
            *self._cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=None,  # inherit parent stderr so server logs reach the terminal
            cwd=cwd,
            env=merged_env,
        )
        logger.info(
            "stdio MCP server started: key=%r pid=%s cmd=%s",
            self._server_key,
            self._proc.pid,
            self._cmd,
        )

    def is_alive(self) -> bool:
        """Return True when the subprocess is running (returncode is None)."""
        return self._proc is not None and self._proc.returncode is None

    @staticmethod
    def _parse_stdio_response(resp_bytes: bytes) -> ToolCallResult:
        """Parse a JSON-RPC response line and return ToolCallResult.

        Raises (orjson.JSONDecodeError, KeyError) if the response is invalid.
        """
        resp = orjson.loads(resp_bytes)
        is_error = bool(resp["is_error"])
        return ToolCallResult.from_transport(
            output=str(resp["result"]), is_error=is_error
        )

    async def call(self, name: str, args: dict[str, Any]) -> ToolCallResult:
        """Send one JSON-RPC request and return ToolCallResult; acquires per-instance lock so concurrent callers are serialized.

        Raises TransportError on transport-level failures (process crash,
        timeout, broken pipe, invalid response).  Tool-level errors from the
        MCP server are returned as-is with is_error=True in the result.
        """
        if not self.is_alive():
            msg = f"stdio server not running (key={self._server_key!r})"
            raise TransportError(msg)

        lock = self._get_lock()
        async with lock:
            self._req_id += 1
            req_id = self._req_id
            payload = _json_dumps({"id": req_id, "name": name, "args": args}) + "\n"

            if not (self._proc and self._proc.stdin and self._proc.stdout):
                # Unreachable after is_alive() guard above; defensive check for type narrowing
                msg = f"stdio server process invalid (key={self._server_key!r})"
                raise TransportError(msg)
            try:
                self._proc.stdin.write(payload.encode())
                await self._proc.stdin.drain()
                resp_bytes = await asyncio.wait_for(
                    self._proc.stdout.readline(),
                    timeout=_STDIO_CALL_TIMEOUT,
                )
            except TimeoutError:
                msg = f"stdio server timeout (key={self._server_key!r} tool={name})"
                logger.warning(msg)
                raise TransportError(msg) from None
            except (OSError, BrokenPipeError) as e:
                msg = f"stdio transport error (key={self._server_key!r}): {e}"
                logger.error(msg)
                raise TransportError(msg) from e

            if not resp_bytes:
                msg = f"stdio server closed connection (key={self._server_key!r})"
                raise TransportError(msg)
            try:
                result = self._parse_stdio_response(resp_bytes)
                return ToolCallResult(
                    output=result.output,
                    is_error=result.is_error,
                    request_id=result.request_id,
                    server_key=self._server_key,
                    error_type=result.error_type,
                )
            except (orjson.JSONDecodeError, KeyError) as e:
                msg = (
                    f"stdio server invalid response (key={self._server_key!r}): {e}"
                    f" raw={resp_bytes[:200]!r}"
                )
                logger.error(msg)
                raise TransportError(msg) from e

    async def stop(self) -> None:
        """Gracefully shut down the subprocess (close stdin → wait → kill)."""
        if self._proc is None or not self.is_alive():
            return
        try:
            if self._proc.stdin:
                self._proc.stdin.close()
            await asyncio.wait_for(self._proc.wait(), timeout=5.0)
        except TimeoutError:
            logger.warning(
                "stdio server %r did not exit gracefully; terminating",
                self._server_key,
            )
            self._proc.terminate()
            try:
                await asyncio.wait_for(self._proc.wait(), timeout=3.0)
            except TimeoutError:
                self._proc.kill()
        except (OSError, BrokenPipeError) as e:
            logger.warning("stdio server %r stop error: %s", self._server_key, e)
            self._proc.kill()
        logger.info("stdio MCP server stopped: key=%r", self._server_key)


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
    """Routes tool calls to the appropriate MCP server transport with TTL caching; only successful results are cached; StdioTransport must be injected via set_transport()."""

    def __init__(
        self,
        http: httpx.AsyncClient,
        cache_ttl: float,
        server_configs: dict[str, McpServerConfig],
        cache_max_size: int = 0,
        concurrency_limits: dict[str, int] | None = None,
        lifecycle: LifecycleProtocol | None = None,
        repeated_tool_error_threshold: int = 3,
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

        # Initialise transports: HTTP servers get their transport immediately;
        # stdio servers get None until set_transport() is called after process spawn.
        self._transports: dict[str, HttpTransport | StdioTransport | None] = {}
        for key, cfg in server_configs.items():
            if cfg.transport == "http":
                self._transports[key] = HttpTransport(http, cfg.url, key, cfg)
            else:
                self._transports[key] = None  # filled by set_transport()

        self._resolver = ToolRouteResolver(server_configs)

    def set_transport(self, server_key: str, transport: StdioTransport) -> None:
        """Register a started StdioTransport for the given server key."""
        self._transports[server_key] = transport
        logger.info("StdioTransport registered for server key %r", server_key)

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
        cfg = self._server_configs.get(server_key)
        if cfg and cfg.transport == "stdio":
            return (
                f"stdio server {server_key!r} not started"
                " (call _start_stdio_servers first)"
            )
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
        transport: HttpTransport | StdioTransport,
        tool_name: str,
        args: dict[str, Any],
        sem: asyncio.Semaphore | None,
    ) -> ToolCallResult:
        """Execute via transport, optionally under a semaphore."""
        if sem is not None:
            async with sem:
                return await transport.call(tool_name, args)
        return await transport.call(tool_name, args)

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
        cached = self._cache.get(cache_key)
        if cached is not None:
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
        result = await self._raw_execute(tool_name, args)
        if not result.is_error:
            self._cache[cache_key] = CacheEntry(
                output=result.output, is_error=result.is_error, cached_at=time.time()
            )
            if self._cache_max_size > 0 and len(self._cache) > self._cache_max_size:
                evicted_key, _ = self._cache.popitem(last=False)
                logger.debug("Tool cache LRU evict: %r", evicted_key)
        return result

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
