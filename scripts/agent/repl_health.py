"""MCP server health monitoring and startup validation for AgentREPL.

Standalone async functions taking AgentContext as first argument.
Extracted from agent/repl.py to allow targeted loading when modifying
health check or watchdog behaviour.
"""

from __future__ import annotations

import asyncio
from http import HTTPStatus
from typing import TYPE_CHECKING
from urllib.parse import urlparse

import httpx
import orjson
from mcp.git.models import GitConfig
from mcp.shell.models import ShellConfig
from mcp.sqlite.models import SqliteConfig
from shared.logger import Logger
from shared.tool_executor import StdioTransport

from agent.context import AgentContext
from agent.shared.health_models import HealthCheckResult, ServiceWarning

if TYPE_CHECKING:
    from shared.mcp_config import McpServerConfig

logger = Logger(__name__, "/opt/llm/logs/agent.log")


async def probe_mcp_health(http: httpx.AsyncClient, base_url: str) -> bool:
    """Return True if the MCP server at base_url responds to /health with 200."""
    try:
        resp = await http.get(f"{base_url}/health", timeout=5.0)
        ok: bool = (
            resp.status_code == HTTPStatus.OK
        )  # explicit type for older mypy stubs
        return ok
    except (httpx.HTTPError, OSError, TimeoutError):
        return False


async def check_service_health(ctx: AgentContext) -> HealthCheckResult:
    """Probe LLM and Embed service health at startup; return warning strings on failure.

    Failure is non-fatal: the REPL continues regardless.
    Derives the /health URL by stripping the path from each endpoint URL.
    """
    if ctx.services.http is None:
        raise RuntimeError("http service not initialized")
    checks = [
        ("llm", ctx.cfg.llm.llm_url),
        ("embed-llm", ctx.cfg.rag.embed_url),
    ]
    warnings: list[ServiceWarning] = []
    for label, url in checks:
        if not url:
            continue
        parsed = urlparse(url)
        health_url = f"{parsed.scheme}://{parsed.netloc}/health"
        try:
            resp = await ctx.services.http.get(health_url, timeout=2.0)
            if resp.status_code != HTTPStatus.OK:
                msg = f"{label} health check returned HTTP {resp.status_code}"
                logger.warning(msg)
                warnings.append(
                    ServiceWarning(label=label, url=health_url, message=msg)
                )
        except (httpx.HTTPError, OSError) as e:
            msg = f"{label} unreachable at {health_url}: {e}"
            logger.warning(msg)
            warnings.append(ServiceWarning(label=label, url=health_url, message=msg))
    return HealthCheckResult(warnings=warnings)


async def check_readiness(
    ctx: AgentContext, *, production_mode: bool = False
) -> HealthCheckResult:
    """Probe required services at startup; raise in production mode on failure.

    In production mode, any failed health check raises RuntimeError listing
    which services are unavailable.
    In development mode, behaves like check_service_health(): warnings only.
    """
    result = await check_service_health(ctx)
    if production_mode and result.has_issues:
        error_msgs = [f"{w.label}: {w.message}" for w in result.warnings]
        msg = (
            "Startup readiness check failed (required services unavailable): "
            + "; ".join(error_msgs)
        )
        logger.error(msg)
        raise RuntimeError(msg)
    return result


async def _fetch_stdio_tools(transport: object) -> set[str]:
    """Query a running stdio server for its tool list via the __list_tools__ RPC.

    Returns an empty set when the server is unreachable or returns an error.
    """
    if not isinstance(transport, StdioTransport) or not transport.is_alive():
        return set()
    try:
        result = await asyncio.wait_for(
            transport.call("__list_tools__", {}),
            timeout=5.0,
        )
        if result.is_error:
            return set()
        data = orjson.loads(result.output)
        return {str(n) for n in data.get("tools", [])}
    except (TimeoutError, orjson.JSONDecodeError, OSError) as e:
        logger.warning("__list_tools__ RPC failed: %s", e)
        return set()


async def _collect_server_tool_names(ctx: AgentContext) -> tuple[set[str], list[str]]:
    """Probe all configured MCP servers and return (tool_names, unreachable_keys).

    HTTP servers: probed via GET /v1/tools.
    Stdio servers: probed via the __list_tools__ reserved RPC (only when running).
    Returns a tuple of (union of tool names, list of server keys that were unreachable).

    Scenarios and expected log output:
      - One HTTP server unreachable:
          WARNING "{key} unreachable at {url}/v1/tools: ..."
          returns (names_from_remaining_servers, [key])
      - All HTTP servers unreachable:
          WARNING per server (as above)
          returns (set(), [key1, key2, ...])
      - Stdio server not running (persistent mode):
          WARNING "{key} stdio process not running (ondemand or failed)"
          returns (set(), [key])
      - All servers reachable:
          returns (union_of_all_tool_names, [])
    """
    if ctx.services.http is None:
        raise RuntimeError("http service not initialized")
    server_names: set[str] = set()
    unreachable: list[str] = []
    for key, srv_cfg in ctx.cfg.mcp.mcp_servers.items():
        if srv_cfg.transport == "http":
            if not srv_cfg.url:
                continue
            try:
                resp = await ctx.services.http.get(
                    f"{srv_cfg.url}/v1/tools",
                    timeout=5.0,
                )
                if resp.status_code == HTTPStatus.OK:
                    server_names.update(t["name"] for t in resp.json().get("tools", []))
                else:
                    msg = f"{key} /v1/tools returned HTTP {resp.status_code}"
                    logger.warning(msg)
                    unreachable.append(key)
            except (httpx.HTTPError, OSError) as e:
                msg = f"{key} unreachable at {srv_cfg.url}/v1/tools: {e}"
                logger.warning(msg)
                unreachable.append(key)
        elif srv_cfg.transport == "stdio":
            transport = ctx.services.stdio_procs.get(key)
            if transport is None:
                msg = f"{key} stdio process not running (ondemand or failed)"
                logger.warning(msg)
                unreachable.append(key)
                continue
            names = await _fetch_stdio_tools(transport)
            if not names:
                msg = f"{key} __list_tools__ returned empty tool list"
                logger.warning(msg)
                unreachable.append(key)
            server_names.update(names)
    return server_names, unreachable


async def _check_tool_definitions(
    ctx: AgentContext, strict: bool = False
) -> HealthCheckResult:
    """Compare tool_definitions against live server tool lists.

    Distinguishes failure cases:
      - server unreachable (logged as warning, included in unreachable list)
      - /v1/tools fetch failed (HTTP non-200)
      - tool mismatch (missing_in_server or missing_in_cfg)
      - all servers unreachable -> skip validation with info log

    Scenarios and expected log output:
      - Partial unreachable (some servers respond):
          WARNING per unreachable server (from _collect_server_tool_names)
          WARNING "Tools in agent.toml but not on any server: [...]" (if mismatch)
          returns HealthCheckResult(warnings=[...]) or HealthCheckResult()
      - All servers unreachable:
          INFO "All MCP servers unreachable during strict validation: [...]; skipping tool definition check"
          returns HealthCheckResult() — no warnings, no error even in strict mode
      - Tool mismatch, strict=False:
          WARNING "Tools in agent.toml but not on any server: [...]"
          returns HealthCheckResult(warnings=[ServiceWarning(...)])
      - Tool mismatch, strict=True:
          ERROR "Strict mode: tool definition mismatch detected. Mismatches: .... Unreachable servers: ...."
          raises RuntimeError
    """
    cfg_names = {
        td["function"]["name"]
        for td in ctx.cfg.tool.tool_definitions
        if "function" in td
    }
    server_names, unreachable = await _collect_server_tool_names(ctx)
    if not server_names:
        if unreachable:
            msg = f"All MCP servers unreachable during strict validation: {sorted(set(unreachable))}; skipping tool definition check"
            logger.info(msg)
        else:
            msg = "No tool definitions in config and no servers reachable; skipping validation"
            logger.info(msg)
        return HealthCheckResult()
    missing_in_server = cfg_names - server_names
    missing_in_cfg = server_names - cfg_names
    warnings: list[ServiceWarning] = []
    if missing_in_server:
        msg = f"Tools in agent.toml but not on any server: {sorted(missing_in_server)}"
        logger.warning(msg)
        warnings.append(ServiceWarning(label="tool_definitions", url="", message=msg))
    if missing_in_cfg:
        msg = f"Tools on servers but not in agent.toml: {sorted(missing_in_cfg)}"
        logger.warning(msg)
    if (missing_in_server or missing_in_cfg) and strict:
        mismatch_parts: list[str] = []
        if missing_in_server:
            mismatch_parts.append(f"missing_in_server={sorted(missing_in_server)}")
        if missing_in_cfg:
            mismatch_parts.append(f"extra_on_servers={sorted(missing_in_cfg)}")
        mismatch_str = ", ".join(mismatch_parts) if mismatch_parts else "none"
        unreachable_str = sorted(set(unreachable)) if unreachable else []
        msg = (
            f"Strict mode: tool definition mismatch detected. "
            f"Mismatches: {mismatch_str}. "
            f"Unreachable servers: {unreachable_str}."
        )
        logger.error(msg)
        raise RuntimeError(msg)
    return HealthCheckResult(warnings=warnings)


async def check_tool_definitions_runtime(ctx: AgentContext) -> HealthCheckResult:
    """Runtime validation: no raise, warnings only."""
    return await _check_tool_definitions(ctx, strict=False)


async def _watchdog_check_http(
    ctx: AgentContext,
    key: str,
    srv_cfg: McpServerConfig,
    restart_counts: dict[str, int],
    max_restarts: int,
) -> None:
    """Probe one HTTP server and restart via lifecycle manager when health check fails.

    For startup_mode="subprocess" servers, restart is delegated to
    ctx.services.lifecycle.restart().  Other modes (externally-managed) only
    log a warning because the agent does not own those processes.
    """
    if ctx.services.http is None:
        raise RuntimeError("http service not initialized")
    if not srv_cfg.url:
        return
    ok = await probe_mcp_health(ctx.services.http, srv_cfg.url)
    if ok:
        restart_counts[key] = 0
        if ctx.services.health_registry:
            ctx.services.health_registry.record_success(key)
        return
    count = restart_counts.get(key, 0)
    if count >= max_restarts:
        logger.warning(
            "Watchdog: %r unreachable; restart limit reached (%s)",
            key,
            max_restarts,
        )
        return
    logger.warning(
        "Watchdog: %r health check failed, restarting (attempt %s/%s)",
        key,
        count + 1,
        max_restarts,
    )
    # Delegate restart to lifecycle manager
    if srv_cfg.startup_mode == "subprocess" and ctx.services.lifecycle is not None:
        try:
            await ctx.services.lifecycle.restart(key)
            restart_counts[key] = count + 1
        except (OSError, RuntimeError) as e:
            logger.error("Watchdog: failed to restart %r: %s", key, e)
    else:
        logger.warning(
            "Watchdog: %r is not a subprocess-mode server;"
            " manual intervention required",
            key,
        )
    if ctx.services.health_registry:
        ctx.services.health_registry.record_failure(key)


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
        if ctx.services.health_registry:
            ctx.services.health_registry.record_success(key)
        return
    count = restart_counts.get(key, 0)
    if count >= max_restarts:
        logger.warning(
            "Watchdog: stdio server %r dead; restart limit reached (%s)",
            key,
            max_restarts,
        )
        return
    logger.warning(
        "Watchdog: stdio server %r died, restarting (attempt %s/%s)",
        key,
        count + 1,
        max_restarts,
    )
    if ctx.services.lifecycle is not None:
        try:
            await ctx.services.lifecycle.restart_stdio(key)
            restart_counts[key] = count + 1
        except (OSError, RuntimeError) as e:
            logger.error("Watchdog: failed to restart stdio server %r: %s", key, e)
    if ctx.services.health_registry:
        ctx.services.health_registry.record_failure(key)


async def watchdog_loop(ctx: AgentContext) -> None:
    """Periodically probe MCP server health and restart via lifecycle manager on failure.

    Runs until cancelled (e.g. when the REPL exits).
    Restart attempts per server are capped at mcp_watchdog_max_restarts to
    prevent infinite restart loops.
    """
    interval = ctx.cfg.mcp.mcp_watchdog_interval
    max_restarts = ctx.cfg.mcp.mcp_watchdog_max_restarts
    restart_counts: dict[str, int] = {}
    if interval > 0:
        logger.info(
            "Watchdog: enabled (interval=%.0fs, max_restarts=%d)",
            interval,
            max_restarts,
        )
    else:
        logger.warning(
            "Watchdog: disabled (interval=%.0f) — failed servers will not be auto-restarted",
            interval,
        )
    while True:
        await asyncio.sleep(interval)
        for key, srv_cfg in ctx.cfg.mcp.mcp_servers.items():
            if srv_cfg.transport == "http":
                await _watchdog_check_http(
                    ctx,
                    key,
                    srv_cfg,
                    restart_counts,
                    max_restarts,
                )
            elif srv_cfg.transport == "stdio":
                await _watchdog_check_stdio(
                    ctx,
                    key,
                    srv_cfg,
                    restart_counts,
                    max_restarts,
                )
        if ctx.services.lifecycle is not None:
            await ctx.services.lifecycle.shutdown_idle()


def audit_security_defaults(
    ctx: AgentContext, production_mode: bool = False
) -> list[str]:
    """Audit security-related configuration defaults and return warning strings.

    In production mode (production_mode=True), HTTP servers without auth_token
    raise RuntimeError instead of returning a warning.

    Checks for risky settings such as:
      - auth_token disabled (empty) on servers that support it
      - shell sandbox disabled (none backend)
      - GitHub workflow allowlist empty (fail-open)
      - Allowed tools empty (allow all)
    Returns a list of warning messages; empty list means no issues.
    """
    warnings: list[str] = []

    profile_label = "PRODUCTION" if production_mode else "LOCAL"
    auth_required = "yes" if production_mode else "no"
    logger.info(
        "Security profile: %s — auth required for HTTP servers: %s",
        profile_label,
        auth_required,
    )

    # Check auth_token settings
    violations: list[str] = []
    for key, srv_cfg in ctx.cfg.mcp.mcp_servers.items():
        if not srv_cfg.auth_token and srv_cfg.transport == "http" and srv_cfg.url:
            msg = f"{key}: no auth_token configured (auth disabled)"
            violations.append(msg)

    if production_mode and violations:
        servers_str = "; ".join(violations)
        raise RuntimeError(
            f"Production mode requires auth_token on all HTTP MCP servers. "
            f"Violations: {servers_str}"
        )

    for v in violations:
        logger.warning("Security: %s", v)
        warnings.append(f"Security: {v}")

    fail_closed_empty: list[str] = []  # deny access when empty (safe default)
    fail_open_empty: list[str] = []  # allow all access when empty (risky default)

    lockdown = getattr(ctx.cfg.mcp, "security_lockdown_enabled", False)
    if lockdown:
        logger.info(
            "Security: security_lockdown_enabled=True — deny-all warnings suppressed"
            " (intentional lockdown acknowledged)"
        )
    else:
        # Check shell sandbox and command_allowlist
        try:
            shell_cfg = ShellConfig.load()
            if shell_cfg.shell_sandbox_backend == "none":
                msg = "Security: shell_sandbox_backend=none (no sandbox for shell commands)"
                logger.warning(msg)
                warnings.append(msg)
            if not shell_cfg.command_allowlist:
                fail_closed_empty.append("shell.command_allowlist")
                msg = (
                    "DENY-ALL detected: shell.command_allowlist is empty. "
                    "shell-mcp will reject ALL shell commands. "
                    "Verify this is intentional or add allowed commands to shell_mcp_server.toml."
                )
                logger.warning(msg)
                warnings.append(msg)
        except Exception:
            pass

        # Check sqlite db_allowlist
        try:
            sqlite_cfg = SqliteConfig.load()
            if not sqlite_cfg.db_allowlist:
                fail_closed_empty.append("sqlite.db_allowlist")
                msg = (
                    "DENY-ALL detected: sqlite.db_allowlist is empty. "
                    "sqlite-mcp will reject ALL DB queries. "
                    "Verify this is intentional or add allowed DB paths to sqlite_mcp_server.toml."
                )
                logger.warning(msg)
                warnings.append(msg)
        except Exception:
            pass

        # Check git allowed_repo_paths
        try:
            git_cfg = GitConfig.load()
            if not git_cfg.allowed_repo_paths:
                fail_closed_empty.append("git.allowed_repo_paths")
                msg = (
                    "DENY-ALL detected: git.allowed_repo_paths is empty. "
                    "git-mcp will reject ALL repository operations. "
                    "Verify this is intentional or add allowed paths to git_mcp_server.toml."
                )
                logger.warning(msg)
                warnings.append(msg)
        except Exception:
            pass

        # Check github allowed_repos (fail-closed — empty = deny all repo access)
        try:
            from mcp.github.models_config import (
                GitHubConfig,  # noqa: PLC0415 — lazy import; github-mcp optional
            )

            github_mcp_cfg = GitHubConfig.load()
            if not github_mcp_cfg.allowed_repos:
                fail_closed_empty.append("github.allowed_repos")
                msg = (
                    "DENY-ALL detected: github.allowed_repos is empty. "
                    "github-mcp will reject ALL repo access requests. "
                    "Verify this is intentional or add allowed repos to github_mcp_server.toml."
                )
                logger.warning(msg)
                warnings.append(msg)
        except Exception:
            pass

    # Check GitHub workflow allowlist (fail-open — no github config on AgentConfig)
    github_cfg = getattr(ctx.cfg, "github", None)
    if github_cfg is not None:
        allowed_workflows = getattr(github_cfg, "allowed_workflows", None)
        if isinstance(allowed_workflows, (list, tuple)) and len(allowed_workflows) == 0:
            fail_open_empty.append("github.allowed_workflows")
            msg = "Security: github.allowed_workflows is empty (fail-open: all workflows allowed)"
            logger.warning(msg)
            warnings.append(msg)

    # Check allowed_tools (fail-open: empty = allow all tools)
    tool_cfg = getattr(ctx.cfg, "tool", None)
    if tool_cfg is not None:
        allowed_tools = getattr(tool_cfg, "allowed_tools", None)
        if isinstance(allowed_tools, (list, tuple)) and len(allowed_tools) == 0:
            fail_open_empty.append("tool.allowed_tools")
            msg = "Security: tool.allowed_tools is empty (all tools allowed; use allowlist to restrict)"
            logger.warning(msg)
            warnings.append(msg)

    # Security posture summary
    if fail_closed_empty or fail_open_empty:
        fc_str = ", ".join(fail_closed_empty) if fail_closed_empty else "none"
        fo_str = ", ".join(fail_open_empty) if fail_open_empty else "none"
        summary = (
            f"Security posture summary — "
            f"fail-closed (deny when empty): {fc_str}; "
            f"fail-open (allow when empty): {fo_str}"
        )
        logger.warning(summary)
        warnings.append(summary)

    return warnings
