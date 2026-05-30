"""
MCP server health monitoring and startup validation for AgentREPL.

Standalone async functions taking AgentContext as first argument.
Extracted from agent/repl.py to allow targeted loading when modifying
health check or watchdog behaviour.
"""

from __future__ import annotations

import asyncio
import subprocess
from typing import TYPE_CHECKING
from urllib.parse import urlparse

import httpx
import orjson
from shared.logger import Logger

from agent.context import AgentContext

if TYPE_CHECKING:
    from shared.mcp_config import McpServerConfig

logger = Logger(__name__, "/opt/llm/logs/agent.log")


async def probe_mcp_health(http: httpx.AsyncClient, base_url: str) -> bool:
    """Return True if the MCP server at base_url responds to /health with 200."""
    try:
        resp = await http.get(f"{base_url}/health", timeout=5.0)
        return int(resp.status_code) == 200
    except Exception:
        return False


async def check_service_health(ctx: AgentContext) -> None:
    """Probe LLM and Embed service health at startup; log warnings on failure.

    Failure is non-fatal: the REPL continues regardless.
    Derives the /health URL by stripping the path from each endpoint URL.
    """
    assert ctx.services.http is not None
    checks = [
        ("llm", ctx.cfg.llm_url),
        ("embed-llm", ctx.cfg.embed_url),
    ]
    for label, url in checks:
        if not url:
            continue
        parsed = urlparse(url)
        health_url = f"{parsed.scheme}://{parsed.netloc}/health"
        try:
            resp = await ctx.services.http.get(health_url, timeout=2.0)
            if resp.status_code != 200:
                msg = f"{label} health check returned HTTP {resp.status_code}"
                logger.warning(msg)
                print(f"[warn] {msg}")
        except Exception as e:
            msg = f"{label} unreachable at {health_url}: {e}"
            logger.warning(msg)
            print(f"[warn] {msg}")


async def _fetch_stdio_tools(transport: object) -> set[str]:
    """Query a running stdio server for its tool list via the __list_tools__ RPC.

    Returns an empty set when the server is unreachable or returns an error.
    """
    from shared.tool_executor import StdioTransport  # noqa: PLC0415

    if not isinstance(transport, StdioTransport) or not transport.is_alive():
        return set()
    try:
        raw, is_error = await asyncio.wait_for(
            transport.call("__list_tools__", {}), timeout=5.0
        )
        if is_error:
            return set()
        data = orjson.loads(raw)
        return {str(n) for n in data.get("tools", [])}
    except Exception as e:
        logger.warning(f"__list_tools__ RPC failed: {e}")
        return set()


async def _collect_server_tool_names(ctx: AgentContext) -> set[str]:
    """Probe all configured MCP servers and return the union of their tool names.

    HTTP servers: probed via GET /v1/tools.
    Stdio servers: probed via the __list_tools__ reserved RPC (only when running).
    """
    assert ctx.services.http is not None
    server_names: set[str] = set()
    for key, srv_cfg in ctx.cfg.mcp_servers.items():
        if srv_cfg.transport == "http":
            if not srv_cfg.url:
                continue
            try:
                resp = await ctx.services.http.get(
                    f"{srv_cfg.url}/v1/tools", timeout=5.0
                )
                if resp.status_code == 200:
                    server_names.update(t["name"] for t in resp.json().get("tools", []))
            except Exception as e:
                logger.warning(f"Cannot reach {srv_cfg.url}/v1/tools: {e}")
        elif srv_cfg.transport == "stdio":
            transport = ctx.services.stdio_procs.get(key)
            if transport is None:
                continue  # not yet started (ondemand or failed persistent)
            names = await _fetch_stdio_tools(transport)
            server_names.update(names)
    return server_names


async def check_tool_definitions(ctx: AgentContext) -> None:
    """Compare tool_definitions in agent.toml against live tool lists from each server.

    Logs a warning on mismatch. Raises RuntimeError when tool_definitions_strict=True.
    Skips silently when all servers are unreachable (startup order tolerance).
    """
    cfg_names = {
        td["function"]["name"] for td in ctx.cfg.tool_definitions if "function" in td
    }
    server_names = await _collect_server_tool_names(ctx)
    if not server_names:
        return  # All servers unreachable; skip validation
    missing_in_server = cfg_names - server_names
    missing_in_cfg = server_names - cfg_names
    if missing_in_server:
        msg = f"Tools in agent.toml but not on any server: {sorted(missing_in_server)}"
        logger.warning(msg)
        print(f"[warn] {msg}")
    if missing_in_cfg:
        logger.warning(
            f"Tools on servers but not in agent.toml: {sorted(missing_in_cfg)}"
        )
    if (missing_in_server or missing_in_cfg) and ctx.cfg.tool_definitions_strict:
        raise RuntimeError("Strict mode: tool definition mismatch detected")


async def _watchdog_check_http(
    ctx: AgentContext,
    key: str,
    srv_cfg: McpServerConfig,
    restart_counts: dict[str, int],
    max_restarts: int,
) -> None:
    """Probe one HTTP server and restart via OpenRC when health check fails."""
    assert ctx.services.http is not None
    if not srv_cfg.url:
        return
    ok = await probe_mcp_health(ctx.services.http, srv_cfg.url)
    if ok:
        restart_counts[key] = 0
        return
    count = restart_counts.get(key, 0)
    if count >= max_restarts:
        logger.warning(
            f"Watchdog: {srv_cfg.openrc_service!r} unreachable;"
            f" restart limit reached ({max_restarts})"
        )
        return
    logger.warning(
        f"Watchdog: {srv_cfg.openrc_service!r} health check failed,"
        f" restarting (attempt {count + 1}/{max_restarts})"
    )
    if srv_cfg.openrc_service:
        try:
            subprocess.run(
                ["rc-service", srv_cfg.openrc_service, "restart"],
                timeout=30,
                check=False,
            )
            restart_counts[key] = count + 1
        except Exception as e:
            logger.error(f"Watchdog: failed to restart {srv_cfg.openrc_service!r}: {e}")


async def _watchdog_check_stdio(
    ctx: AgentContext,
    key: str,
    srv_cfg: McpServerConfig,
    restart_counts: dict[str, int],
    max_restarts: int,
) -> None:
    """Check liveness of one stdio server and restart it when dead."""
    # Ondemand servers are lifecycle-managed; skip watchdog coverage.
    if srv_cfg.startup_mode == "ondemand":
        return
    transport = ctx.services.stdio_procs.get(key)
    if transport is None:
        return
    alive = transport.is_alive()
    if alive and srv_cfg.healthcheck_mode == "ping_tool":
        # Confirm responsiveness beyond process liveness with a ping.
        names = await _fetch_stdio_tools(transport)
        alive = bool(names)
    if alive:
        restart_counts[key] = 0
        return
    count = restart_counts.get(key, 0)
    if count >= max_restarts:
        logger.warning(
            f"Watchdog: stdio server {key!r} dead;"
            f" restart limit reached ({max_restarts})"
        )
        return
    logger.warning(
        f"Watchdog: stdio server {key!r} died,"
        f" restarting (attempt {count + 1}/{max_restarts})"
    )
    try:
        await transport.start()
        restart_counts[key] = count + 1
    except Exception as e:
        logger.error(f"Watchdog: failed to restart stdio server {key!r}: {e}")


async def watchdog_loop(ctx: AgentContext) -> None:
    """Periodically probe MCP server health and restart via OpenRC on failure.

    Runs until cancelled (e.g. when the REPL exits).
    Restart attempts per server are capped at mcp_watchdog_max_restarts to
    prevent infinite restart loops.
    """
    interval = ctx.cfg.mcp_watchdog_interval
    max_restarts = ctx.cfg.mcp_watchdog_max_restarts
    restart_counts: dict[str, int] = {}
    while True:
        await asyncio.sleep(interval)
        for key, srv_cfg in ctx.cfg.mcp_servers.items():
            if srv_cfg.transport == "http":
                await _watchdog_check_http(
                    ctx, key, srv_cfg, restart_counts, max_restarts
                )
            elif srv_cfg.transport == "stdio":
                await _watchdog_check_stdio(
                    ctx, key, srv_cfg, restart_counts, max_restarts
                )
        if ctx.services.lifecycle is not None:
            await ctx.services.lifecycle.shutdown_idle()
