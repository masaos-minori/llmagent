#!/usr/bin/env python3
"""
tool_executor.py
MCP tool execution layer.

Provides two transport implementations:
  HttpTransport  — POST /v1/call_tool over httpx (default)
  StdioTransport — line-delimited JSON-RPC over subprocess stdin/stdout

ToolExecutor routes tool calls to the appropriate server via _route(),
applies TTL caching on successful results, and delegates execution to the
configured transport.
"""

import asyncio
import hashlib
import logging
import time
from collections import OrderedDict

import httpx
import orjson

import shared.plugin_registry as plugin_registry
from shared.mcp_config import McpServerConfig

logger = logging.getLogger(__name__)

# Seconds to wait for a stdio server response before treating it as a timeout.
_STDIO_CALL_TIMEOUT: float = 60.0


# ─────────────────────────────────────────────────────────────────────────────
# Transport implementations
# ─────────────────────────────────────────────────────────────────────────────


class HttpTransport:
    """Calls /v1/call_tool on a running HTTP MCP server via httpx."""

    def __init__(self, http: httpx.AsyncClient, base_url: str, server_key: str) -> None:
        self._http = http
        self._base_url = base_url
        self._server_key = server_key

    async def call(self, name: str, args: dict) -> tuple[str, bool]:
        """POST to /v1/call_tool and return (result, is_error)."""
        try:
            resp = await self._http.post(
                f"{self._base_url}/v1/call_tool",
                json={"name": name, "args": args},
            )
            resp.raise_for_status()
            data = resp.json()
            return data["result"], data["is_error"]
        except httpx.HTTPStatusError as e:
            msg = (
                f"[HTTPStatusError] tool={name} url={self._base_url}"
                f" status={e.response.status_code}"
                f" response={e.response.text[:300]!r}"
                f" — check {self._base_url}/health"
            )
            logger.warning(msg)
            return msg, True
        except httpx.RequestError as e:
            msg = (
                f"[{type(e).__name__}] tool={name} url={self._base_url}: {e}"
                f" — check {self._base_url}/health"
            )
            logger.warning(msg)
            return msg, True
        except Exception as e:
            msg = f"[{type(e).__name__}] tool={name} url={self._base_url}: {e}"
            logger.error(msg)
            return msg, True


class StdioTransport:
    """Calls an MCP server launched as a subprocess via stdin/stdout JSON-RPC.

    Request  line: {"id": <int>, "name": <str>, "args": {...}}
    Response line: {"id": <int>, "result": <str>, "is_error": <bool>}

    A per-instance asyncio.Lock serialises concurrent tool calls so that
    request/response pairs are never interleaved on a single pipe.
    """

    def __init__(self, cmd: list[str], server_key: str) -> None:
        self._cmd = cmd
        self._server_key = server_key
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
        self._proc = await asyncio.create_subprocess_exec(
            *self._cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=None,  # inherit parent stderr so server logs reach the terminal
        )
        logger.info(
            f"stdio MCP server started: key={self._server_key!r}"
            f" pid={self._proc.pid} cmd={self._cmd}"
        )

    def is_alive(self) -> bool:
        """Return True when the subprocess is running (returncode is None)."""
        return self._proc is not None and self._proc.returncode is None

    async def call(self, name: str, args: dict) -> tuple[str, bool]:
        """Send one JSON-RPC request and return (result, is_error).

        Acquires the per-instance lock so concurrent callers are serialised.
        """
        if not self.is_alive():
            return f"stdio server not running (key={self._server_key!r})", True

        lock = self._get_lock()
        async with lock:
            self._req_id += 1
            req_id = self._req_id
            payload = (
                orjson.dumps({"id": req_id, "name": name, "args": args}).decode() + "\n"
            )

            assert self._proc and self._proc.stdin and self._proc.stdout
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
                return msg, True
            except Exception as e:
                msg = f"stdio transport error (key={self._server_key!r}): {e}"
                logger.error(msg)
                return msg, True

            if not resp_bytes:
                return (
                    f"stdio server closed connection (key={self._server_key!r})",
                    True,
                )
            try:
                resp = orjson.loads(resp_bytes)
                return str(resp["result"]), bool(resp["is_error"])
            except (orjson.JSONDecodeError, KeyError) as e:
                msg = (
                    f"stdio server invalid response (key={self._server_key!r}): {e}"
                    f" raw={resp_bytes[:200]!r}"
                )
                logger.error(msg)
                return msg, True

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
                f"stdio server {self._server_key!r} did not exit gracefully; terminating"
            )
            self._proc.terminate()
            try:
                await asyncio.wait_for(self._proc.wait(), timeout=3.0)
            except TimeoutError:
                self._proc.kill()
        except Exception as e:
            logger.warning(f"stdio server {self._server_key!r} stop error: {e}")
            self._proc.kill()
        logger.info(f"stdio MCP server stopped: key={self._server_key!r}")


# ─────────────────────────────────────────────────────────────────────────────
# Tool routing sets (module-level constants shared by ToolExecutor._route)
# ─────────────────────────────────────────────────────────────────────────────

_READ_TOOLS: frozenset[str] = frozenset(
    {
        "list_directory",
        "list_directory_with_sizes",
        "directory_tree",
        "read_text_file",
        "read_media_file",
        "read_multiple_files",
        "search_files",
        "grep_files",
        "get_file_info",
    }
)
_WRITE_TOOLS: frozenset[str] = frozenset(
    {
        "write_file",
        "edit_file",
        "create_directory",
        "move_file",
    }
)
_DELETE_TOOLS: frozenset[str] = frozenset(
    {
        "delete_file",
        "delete_directory",
    }
)

# Tools with side effects: writes, deletes, or shell execution.
# Used to auto-downgrade parallel execution to serial in execute_all_tool_calls().
_SIDE_EFFECT_TOOLS: frozenset[str] = (
    _WRITE_TOOLS | _DELETE_TOOLS | frozenset({"shell_run"})
)

# Valid server keys returned by _route(); used to validate tool_concurrency_limits keys.
_KNOWN_SERVER_KEYS: frozenset[str] = frozenset(
    {"file_read", "file_write", "file_delete", "shell", "web_search", "github"}
)


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
) -> dict[str, str]:
    """Return {"summary": str, "detail": str} for LLM/tool transport failures.

    summary: one-line user-facing description.
    detail:  JSON string for audit logs and ToolResult storage.
    """
    detail = orjson.dumps(
        {
            "source": source,
            "phase": phase,
            "kind": kind,
            "status_code": status_code,
            "url": url,
            "retryable": retryable,
            "partial": partial,
        }
    ).decode()
    summary = f"[{source.upper()} {kind}] {phase} failure (retryable={retryable})"
    return {"summary": summary, "detail": detail}


def tool_call_key(name: str, args: dict) -> str:
    """Return a stable hash key for a (tool name, args) pair.

    Normalises dict key order via sort_keys so that LLM-generated argument
    objects with varying key order produce the same key.
    Both orchestrator.py (lookup) and agent_repl_tool_exec.py (insert)
    must use this function to guarantee key identity.
    """
    return hashlib.md5(  # nosec B324 — non-security hash for dedup key identity
        f"{name}:{orjson.dumps(args, option=orjson.OPT_SORT_KEYS).decode()}".encode(),
        usedforsecurity=False,
    ).hexdigest()


# ─────────────────────────────────────────────────────────────────────────────
# ToolExecutor
# ─────────────────────────────────────────────────────────────────────────────


class ToolExecutor:
    """Routes tool calls to the appropriate MCP server transport with TTL caching.

    Tool results are cached by (name, args) key for cache_ttl seconds to
    avoid redundant calls for repeated identical invocations.
    Only successful (non-error) results are cached.

    Transport selection:
      HttpTransport  is created immediately for each http-transport server.
      StdioTransport must be started async and injected via set_transport()
      before its server's tools can be called.
    """

    def __init__(
        self,
        http: httpx.AsyncClient,
        cache_ttl: float,
        server_configs: "dict[str, McpServerConfig]",
        cache_max_size: int = 0,
        concurrency_limits: "dict[str, int] | None" = None,
    ) -> None:
        self._http = http
        self._cache_ttl = cache_ttl
        self._cache_max_size = cache_max_size
        self._server_configs = server_configs
        self._cache: OrderedDict[str, tuple[str, bool, float]] = OrderedDict()
        self.stat_cache_hits: int = 0

        # concurrency_limits: server_key -> max concurrent calls.
        # Semaphores are created lazily inside _raw_execute() to avoid event loop issues.
        self._concurrency_limits: dict[str, int] = dict(concurrency_limits or {})
        self._semaphores: dict[str, asyncio.Semaphore] | None = None

        # Validate concurrency_limits keys at construction time to catch config errors early.
        unknown_keys = set(self._concurrency_limits) - _KNOWN_SERVER_KEYS
        if unknown_keys:
            logger.warning(
                f"tool_concurrency_limits: unknown server key(s) {sorted(unknown_keys)!r};"
                " Semaphore will not be applied for these tools."
            )

        # Initialise transports: HTTP servers get their transport immediately;
        # stdio servers get None until set_transport() is called after process spawn.
        self._transports: dict[str, HttpTransport | StdioTransport | None] = {}
        for key, cfg in server_configs.items():
            if cfg.transport == "http":
                self._transports[key] = HttpTransport(http, cfg.url, key)
            else:
                self._transports[key] = None  # filled by set_transport()

    def set_transport(self, server_key: str, transport: StdioTransport) -> None:
        """Register a started StdioTransport for the given server key."""
        self._transports[server_key] = transport
        logger.info(f"StdioTransport registered for server key {server_key!r}")

    def _route(self, tool_name: str) -> str:
        """Return the server key for the given tool name.

        Routing rules (checked in order):
          _READ_TOOLS   → file_read
          _WRITE_TOOLS  → file_write
          _DELETE_TOOLS → file_delete
          shell_run     → shell
          search_web    → web_search
          github_*      → github      (prefix match)
        """
        if tool_name in _READ_TOOLS:
            return "file_read"
        if tool_name in _WRITE_TOOLS:
            return "file_write"
        if tool_name in _DELETE_TOOLS:
            return "file_delete"
        if tool_name == "shell_run":
            return "shell"
        if tool_name == "search_web":
            return "web_search"
        if tool_name.startswith("github_"):
            return "github"
        raise ValueError(f"Unknown tool: {tool_name}")

    async def _raw_execute(self, tool_name: str, args: dict) -> tuple[str, bool]:
        """Execute tool via the appropriate transport; return (result, is_error).

        Applies per-server-key Semaphore concurrency limit when configured.
        Semaphores are created lazily on first call to avoid event loop issues.
        """
        server_key = self._route(tool_name)
        transport = self._transports.get(server_key)
        if transport is None:
            cfg = self._server_configs.get(server_key)
            if cfg and cfg.transport == "stdio":
                msg = (
                    f"stdio server {server_key!r} not started"
                    " (call _start_stdio_servers first)"
                )
            else:
                msg = f"No transport configured for server {server_key!r}"
            logger.error(msg)
            return msg, True

        # Lazy Semaphore initialisation: safe because asyncio is single-threaded
        # and the if-branch completes before the first await.
        if self._semaphores is None and self._concurrency_limits:
            self._semaphores = {
                key: asyncio.Semaphore(n)
                for key, n in self._concurrency_limits.items()
                if n > 0
            }

        sem = (self._semaphores or {}).get(server_key)
        if sem is not None:
            async with sem:
                return await transport.call(tool_name, args)
        return await transport.call(tool_name, args)

    async def execute(self, tool_name: str, args: dict) -> tuple[str, bool]:
        """Execute a tool, returning a cached result when available within cache_ttl.

        Plugin tools (registered via @register_tool) are called directly and
        bypass both the cache and MCP routing.
        """
        plugin_fn = plugin_registry.get_tool(tool_name)
        if plugin_fn is not None:
            try:
                result_raw = await plugin_fn(args)
                result_str, result_err = str(result_raw[0]), bool(result_raw[1])
                return result_str, result_err
            except Exception as e:
                logger.error(f"Plugin tool {tool_name!r} raised: {e}")
                return f"[plugin error] {tool_name}: {e}", True

        cache_key = (
            f"{tool_name}:{orjson.dumps(args, option=orjson.OPT_SORT_KEYS).decode()}"
        )
        cached = self._cache.get(cache_key)
        if cached is not None:
            result, is_error, ts = cached
            age = time.time() - ts
            if age < self._cache_ttl:
                self._cache.move_to_end(cache_key)  # LRU: mark as recently used
                self.stat_cache_hits += 1
                logger.info(f"Tool cache hit: {tool_name} (age={age:.0f}s)")
                return result, is_error
            del self._cache[cache_key]
        result, is_error = await self._raw_execute(tool_name, args)
        if not is_error:
            self._cache[cache_key] = (result, is_error, time.time())
            if self._cache_max_size > 0 and len(self._cache) > self._cache_max_size:
                evicted_key, _ = self._cache.popitem(last=False)
                logger.debug(f"Tool cache LRU evict: {evicted_key!r}")
        return result, is_error

    def clear_cache(self) -> None:
        """Evict all cached tool results."""
        self._cache.clear()
