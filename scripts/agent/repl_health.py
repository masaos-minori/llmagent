"""
MCP server health monitoring and startup validation for AgentREPL.

Standalone async functions taking AgentContext as first argument.
Extracted from agent_repl.py to allow targeted loading when modifying
health check or watchdog behaviour.
"""

import asyncio
import subprocess
from urllib.parse import urlparse

import httpx
from shared.logger import Logger

from agent.context import AgentContext

logger = Logger(__name__, "/opt/llm/logs/agent.log")


async def probe_mcp_health(http: httpx.AsyncClient, base_url: str) -> bool:
    """Return True if the MCP server at base_url responds to /health with 200."""
    try:
        resp = await http.get(f"{base_url}/health", timeout=5.0)
        return bool(resp.status_code == 200)
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


async def check_tool_definitions(ctx: AgentContext) -> None:
    """Compare tool_definitions in agent.toml against /v1/tools from each server.

    Logs a warning on mismatch. Raises RuntimeError when
    tool_definitions_strict=True.
    Skips silently when all servers are unreachable (startup order tolerance).
    """
    assert ctx.services.http is not None
    cfg_names = {
        td["function"]["name"] for td in ctx.cfg.tool_definitions if "function" in td
    }
    server_names: set[str] = set()
    for key, srv_cfg in ctx.cfg.mcp_servers.items():
        # stdio servers do not expose an HTTP /v1/tools endpoint; skip them.
        if srv_cfg.transport != "http" or not srv_cfg.url:
            continue
        try:
            resp = await ctx.services.http.get(f"{srv_cfg.url}/v1/tools", timeout=5.0)
            if resp.status_code == 200:
                server_names.update(t["name"] for t in resp.json().get("tools", []))
        except Exception as e:
            logger.warning(f"Cannot reach {srv_cfg.url}/v1/tools: {e}")
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
        assert ctx.services.http is not None
        for key, srv_cfg in ctx.cfg.mcp_servers.items():
            if srv_cfg.transport == "http":
                if not srv_cfg.url:
                    continue
                ok = await probe_mcp_health(ctx.services.http, srv_cfg.url)
                if ok:
                    restart_counts[key] = 0
                    continue
                count = restart_counts.get(key, 0)
                if count >= max_restarts:
                    logger.warning(
                        f"Watchdog: {srv_cfg.openrc_service!r} unreachable;"
                        f" restart limit reached ({max_restarts})"
                    )
                    continue
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
                        logger.error(
                            f"Watchdog: failed to restart"
                            f" {srv_cfg.openrc_service!r}: {e}"
                        )
            elif srv_cfg.transport == "stdio":
                transport = ctx.services.stdio_procs.get(key)
                if transport is None:
                    continue
                if transport.is_alive():
                    restart_counts[key] = 0
                    continue
                count = restart_counts.get(key, 0)
                if count >= max_restarts:
                    logger.warning(
                        f"Watchdog: stdio server {key!r} dead;"
                        f" restart limit reached ({max_restarts})"
                    )
                    continue
                logger.warning(
                    f"Watchdog: stdio server {key!r} died,"
                    f" restarting (attempt {count + 1}/{max_restarts})"
                )
                try:
                    await transport.start()
                    restart_counts[key] = count + 1
                except Exception as e:
                    logger.error(
                        f"Watchdog: failed to restart stdio server {key!r}: {e}"
                    )
