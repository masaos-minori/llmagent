"""MCP server health monitoring and startup validation for AgentREPL.

Standalone async functions taking AgentContext as first argument.
Extracted from agent/repl.py to allow targeted loading when modifying
health check or watchdog behaviour.
"""

from __future__ import annotations

import asyncio
from http import HTTPStatus
from pathlib import Path
from typing import TYPE_CHECKING
from urllib.parse import urlparse

import httpx
from shared.logger import Logger
from shared.mcp_config import StartupMode, TransportType

from agent.context import AgentContext
from agent.security_audit_config import (
    load_cicd_audit_config,
    load_git_audit_config,
    load_github_audit_config,
    load_shell_audit_config,
)
from agent.shared.health_models import (
    HealthCheckResult,
    McpHealthProbeResult,
    ServiceWarning,
)

if TYPE_CHECKING:
    from shared.mcp_config import McpServerConfig


logger = Logger(__name__, "/opt/llm/logs/agent.log")


async def _probe_mcp_health_detail(
    http: httpx.AsyncClient, base_url: str
) -> McpHealthProbeResult:
    """Probe /health and return a structured McpHealthProbeResult.

    Never raises. On network failure returns reachable=False with status_code=None.
    On JSON parse failure falls back to restart_recommended=False, operator_action_required=False.
    """
    try:
        resp = await http.get(f"{base_url}/health", timeout=5.0)
    except (httpx.HTTPError, OSError, TimeoutError):
        return McpHealthProbeResult(
            reachable=False,
            status_code=None,
            restart_recommended=False,
            operator_action_required=False,
            body={},
        )
    try:
        body: dict[str, object] = resp.json()
    except Exception:  # noqa: BLE001 — health check must not fail on body parse errors
        body = {}
    restart_recommended: bool = bool(body.get("restart_recommended", False))
    operator_action_required: bool = bool(body.get("operator_action_required", False))
    return McpHealthProbeResult(
        reachable=True,
        status_code=resp.status_code,
        restart_recommended=restart_recommended,
        operator_action_required=operator_action_required,
        body=body,
    )


async def probe_mcp_health(http: httpx.AsyncClient, base_url: str) -> bool:
    """Return True if the MCP server at base_url responds to /health with HTTP 200.

    Backward-compatible bool wrapper around _probe_mcp_health_detail().
    Callers that need structured probe results should use _probe_mcp_health_detail() directly.
    """
    result = await _probe_mcp_health_detail(http, base_url)
    return result.reachable and result.status_code == HTTPStatus.OK


async def check_service_health(ctx: AgentContext) -> HealthCheckResult:
    """Probe LLM and Embed service health at startup; return warning strings on failure.

    Failure is non-fatal: the REPL continues regardless.
    Derives the /health URL by stripping the path from each endpoint URL.
    """
    if ctx.services_required.http is None:
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
            resp = await ctx.services_required.http.get(health_url, timeout=2.0)
            if resp.status_code != HTTPStatus.OK:
                msg = f"{label} health check returned HTTP {resp.status_code}"
                logger.warning(msg)
                warnings.append(
                    ServiceWarning(label=label, url=health_url, message=msg)
                )
        except (httpx.HTTPError, OSError) as e:
            msg = f"[non-fatal] {label} unreachable at {health_url}: {e}"
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


def _validate_tools_response(
    server_key: str, body: object
) -> tuple[list[str], str | None]:
    """Validate /v1/tools response body. Returns (tool_names, error_msg).

    error_msg is None on success; a descriptive string if the response is malformed.
    """
    if not isinstance(body, dict):
        return (
            [],
            f"{server_key}: /v1/tools response is not a JSON object (got {type(body).__name__})",
        )
    tools = body.get("tools")
    if tools is None:
        return [], f"{server_key}: /v1/tools response missing 'tools' field"
    if not isinstance(tools, list):
        return (
            [],
            f"{server_key}: /v1/tools 'tools' must be a list (got {type(tools).__name__})",
        )
    names: list[str] = []
    for i, entry in enumerate(tools):
        if not isinstance(entry, dict):
            return [], f"{server_key}: /v1/tools tools[{i}] is not an object"
        name = entry.get("name")
        if not isinstance(name, str) or not name.strip():
            return [], f"{server_key}: /v1/tools tools[{i}] has invalid name {name!r}"
        names.append(name)
    return names, None


async def _collect_server_tool_names(ctx: AgentContext) -> tuple[set[str], list[str]]:
    """Probe all configured MCP servers and return (tool_names, unreachable_keys).

    HTTP servers: probed via GET /v1/tools.
    Returns a tuple of (union of tool names, list of server keys that were unreachable).

    Scenarios and expected log output:
      - One HTTP server unreachable:
          WARNING "{key} unreachable at {url}/v1/tools: ..."
          returns (names_from_remaining_servers, [key])
      - All HTTP servers unreachable:
          WARNING per server (as above)
          returns (set(), [key1, key2, ...])
      - All servers reachable:
          returns (union_of_all_tool_names, [])
    """
    if ctx.services_required.http is None:
        raise RuntimeError("http service not initialized")
    server_names: set[str] = set()
    unreachable: list[str] = []
    for key, srv_cfg in ctx.cfg.mcp.mcp_servers.items():
        if srv_cfg.transport == TransportType.HTTP:
            if not srv_cfg.url:
                continue
            try:
                resp = await ctx.services_required.http.get(
                    f"{srv_cfg.url}/v1/tools",
                    timeout=5.0,
                )
                if resp.status_code == HTTPStatus.OK:
                    try:
                        body_data: object = resp.json()
                    except ValueError as e:
                        msg = f"{key}: /v1/tools response is not valid JSON: {e}"
                        logger.warning("Malformed /v1/tools: %s", msg)
                        unreachable.append(key)
                        continue
                    names, err_msg = _validate_tools_response(key, body_data)
                    if err_msg:
                        logger.warning("Malformed /v1/tools: %s", err_msg)
                        unreachable.append(key)
                    else:
                        server_names.update(names)
                else:
                    msg = f"{key} /v1/tools returned HTTP {resp.status_code}"
                    logger.warning(msg)
                    unreachable.append(key)
            except (httpx.HTTPError, OSError) as e:
                msg = f"{key} unreachable at {srv_cfg.url}/v1/tools: {e}"
                logger.warning(msg)
                unreachable.append(key)
    return server_names, unreachable


async def _collect_server_tool_names_per_server(
    ctx: AgentContext,
) -> tuple[dict[str, list[str]], list[str]]:
    """Probe all configured HTTP MCP servers; return (per_server_names, unreachable_keys).

    Returns:
        per_server_names: {server_key: [tool_name, ...]} for reachable servers.
        unreachable_keys: list of server keys that were unreachable or returned non-200.
    """
    if ctx.services_required.http is None:
        raise RuntimeError("http service not initialized")
    per_server: dict[str, list[str]] = {}
    unreachable: list[str] = []
    for key, srv_cfg in ctx.cfg.mcp.mcp_servers.items():
        if srv_cfg.transport == TransportType.HTTP:
            if not srv_cfg.url:
                continue
            try:
                resp = await ctx.services_required.http.get(
                    f"{srv_cfg.url}/v1/tools",
                    timeout=5.0,
                )
                if resp.status_code == HTTPStatus.OK:
                    try:
                        body_data_ps: object = resp.json()
                    except ValueError as e:
                        msg = f"{key}: /v1/tools response is not valid JSON: {e}"
                        logger.warning("Malformed /v1/tools: %s", msg)
                        unreachable.append(key)
                        continue
                    names_ps, err_msg_ps = _validate_tools_response(key, body_data_ps)
                    if err_msg_ps:
                        logger.warning("Malformed /v1/tools: %s", err_msg_ps)
                        unreachable.append(key)
                    else:
                        per_server[key] = names_ps
                else:
                    msg = f"{key} /v1/tools returned HTTP {resp.status_code}"
                    logger.warning(msg)
                    unreachable.append(key)
            except (httpx.HTTPError, OSError) as e:
                msg = f"{key} unreachable at {srv_cfg.url}/v1/tools: {e}"
                logger.warning(msg)
                unreachable.append(key)
    return per_server, unreachable


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
          WARNING "Tools in tools_definitions.toml but not on any server: [...]" (if mismatch)
          returns HealthCheckResult(warnings=[...]) or HealthCheckResult()
      - All servers unreachable, strict=True:
          ERROR "Strict mode: all MCP servers unreachable — cannot validate tool definitions. Unreachable servers: [...]."
          raises RuntimeError
      - All servers unreachable, strict=False:
          INFO "All MCP servers unreachable; skipping tool definition check. Unreachable: [...]"
          returns HealthCheckResult() — no warnings
      - Tool mismatch, strict=False:
          WARNING "Tools in tools_definitions.toml but not on any server: [...]"
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
            if strict:
                msg = (
                    f"Strict mode: all MCP servers unreachable — cannot validate tool definitions. "
                    f"Unreachable servers: {sorted(set(unreachable))}."
                )
                logger.error(msg)
                raise RuntimeError(msg)
            msg = f"All MCP servers unreachable; skipping tool definition check. Unreachable: {sorted(set(unreachable))}"
            logger.info(msg)
        else:
            msg = "No tool definitions in config and no servers reachable; skipping validation"
            logger.info(msg)
        return HealthCheckResult()
    missing_in_server = cfg_names - server_names
    missing_in_cfg = server_names - cfg_names
    warnings: list[ServiceWarning] = []
    if missing_in_server:
        msg = f"Tools in tools_definitions.toml but not on any server: {sorted(missing_in_server)}"
        logger.warning(msg)
        warnings.append(ServiceWarning(label="tool_definitions", url="", message=msg))
    if missing_in_cfg:
        msg = f"Tools on servers but not in tools_definitions.toml: {sorted(missing_in_cfg)}"
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


async def check_tool_definitions_startup(ctx: AgentContext) -> HealthCheckResult:
    """Startup validation: respects tool_definitions_strict config flag."""
    strict = getattr(ctx.cfg.tool, "tool_definitions_strict", False)
    return await _check_tool_definitions(ctx, strict=strict)


async def check_routing_drift_vs_live(
    ctx: AgentContext,
    *,
    strict: bool = False,
) -> HealthCheckResult:
    """Validate live /v1/tools responses against ToolRegistry at startup.

    Detects four drift conditions:
      1. Tool in live response but not in registry.
      2. Tool in registry but not in live response for that server.
      3. Tool returned by a server that does not own it in the registry.
      4. Duplicate live tool ownership (same tool from two servers) — logged as warning.

    In strict mode: any drift raises RuntimeError.
    In non-strict mode: drift is logged and returned as HealthCheckResult warnings.
    All servers unreachable: skip validation with INFO log (same as _check_tool_definitions).
    """
    from shared.route_resolver import build_discovery_map  # noqa: PLC0415
    from shared.tool_registry import get_registry  # noqa: PLC0415
    from shared.tool_routing_validation import (
        validate_routing_against_live,  # noqa: PLC0415
    )

    per_server, unreachable = await _collect_server_tool_names_per_server(ctx)
    if not per_server:
        if unreachable:
            if strict:
                msg = (
                    f"Strict mode: all MCP servers unreachable — cannot validate "
                    f"live routing drift. Unreachable servers: {sorted(set(unreachable))}."
                )
                logger.error(msg)
                raise RuntimeError(msg)
            msg = (
                f"All MCP servers unreachable; skipping live routing drift check. "
                f"Unreachable: {sorted(set(unreachable))}"
            )
            logger.info(msg)
        return HealthCheckResult()

    _route_map, duplicates = build_discovery_map(
        {k: [{"name": n} for n in names] for k, names in per_server.items()}
    )

    drift = validate_routing_against_live(live_tool_lists=per_server)

    warnings: list[ServiceWarning] = []
    for tool_name, server_keys in duplicates.items():
        registry_owner = get_registry().get_server_for_tool(tool_name)
        dup_msg = (
            f"Duplicate live tool ownership: {tool_name!r} claimed by {sorted(server_keys)}; "
            f"registry owner={registry_owner!r}"
        )
        logger.warning(dup_msg)
        warnings.append(
            ServiceWarning(label="duplicate_ownership", url="", message=dup_msg)
        )

    if duplicates and strict:
        raise RuntimeError(
            f"Strict mode: duplicate live tool ownership detected: {sorted(duplicates)}"
        )

    for server_key, messages in drift.items():
        for msg in messages:
            full_msg = f"Live routing drift [{server_key}]: {msg}"
            logger.warning(full_msg)
            warnings.append(ServiceWarning(label=server_key, url="", message=full_msg))

    if drift and strict:
        drift_str = "; ".join(f"{sk}: {msgs}" for sk, msgs in drift.items())
        unreachable_str = sorted(set(unreachable)) if unreachable else []
        msg = (
            f"Strict mode: live routing drift detected. "
            f"Drift: {drift_str}. "
            f"Unreachable servers: {unreachable_str}."
        )
        logger.error(msg)
        raise RuntimeError(msg)

    return HealthCheckResult(warnings=warnings)


def check_workflow_definition(workflows_dir: Path | None = None) -> None:
    """Raise RuntimeError if the workflow definition file is missing."""
    from agent.workflow.workflow_loader import (  # noqa: PLC0415 — lazy to avoid circular import
        WORKFLOWS_DIR,
    )

    target_dir = workflows_dir if workflows_dir is not None else WORKFLOWS_DIR
    workflow_file = target_dir / "default.json"
    if not workflow_file.exists():
        raise RuntimeError(
            f"Workflow definition file not found: {workflow_file}. "
            "Deploy config/workflows/default.json to fix this."
        )


REQUIRED_WORKFLOW_TABLES: dict[str, list[str]] = {
    "tasks": ["task_id", "session_id", "workflow_id", "status", "created_at"],
    "attempts": ["attempt_id", "task_id", "stage_id", "status"],
    "processed_events": ["event_id", "task_id"],
    "artifacts": ["artifact_id", "task_id"],
    "approvals": ["approval_id", "task_id", "status"],
}


def check_workflow_schema(db_path: str | None = None) -> None:
    """Raise RuntimeError if the workflow DB is missing required tables or columns."""
    from db.helper import SQLiteHelper  # noqa: PLC0415

    db = SQLiteHelper(target="workflow", db_path=db_path)
    db.open(write_mode=False, row_factory=False)
    try:
        tables = {
            row[0]
            for row in db.fetchall(
                "SELECT name FROM sqlite_master WHERE type='table'", ()
            )
        }
        for table, required_cols in REQUIRED_WORKFLOW_TABLES.items():
            if table not in tables:
                raise RuntimeError(
                    f"Workflow schema missing table {table!r}. "
                    "Run create_workflow_schema() to initialize."
                )
            existing = {
                row[1] for row in db.fetchall(f"PRAGMA table_info({table})", ())
            }
            for col in required_cols:
                if col not in existing:
                    raise RuntimeError(
                        f"Workflow schema missing column {table}.{col}. "
                        "Reinitialize the workflow database."
                    )
    finally:
        db.close()


def check_routing_drift(ctx: AgentContext, *, strict: bool = False) -> list[str]:
    """Check config tool_names against ToolRegistry at startup. Returns warning messages.

    When strict=True, raises RuntimeError if any drift is detected.
    """
    from shared.tool_routing_validation import (
        validate_routing_against_config,  # noqa: PLC0415
    )

    try:
        server_configs = ctx.cfg.mcp.mcp_servers
        drift = validate_routing_against_config(server_configs=server_configs)
        warnings: list[str] = []
        for server_key, messages in drift.items():
            for msg in messages:
                full_msg = f"Routing drift [{server_key}]: {msg}"
                logger.warning(full_msg)
                warnings.append(full_msg)
        if drift and strict:
            drift_str = "; ".join(f"{sk}: {msgs}" for sk, msgs in drift.items())
            msg = f"Strict mode: routing drift detected. Drift: {drift_str}."
            logger.error(msg)
            raise RuntimeError(msg)
        return warnings
    except RuntimeError:
        raise
    except Exception as exc:  # noqa: BLE001
        logger.warning("Routing drift check failed: %s", exc)
        return []


def check_routing_safety_tiers(ctx: AgentContext) -> list[str]:
    """Check that all registered tools have a declared safety tier. Returns warning messages."""
    from shared.tool_routing_validation import check_tool_safety_tiers  # noqa: PLC0415

    tool_safety_tiers = getattr(ctx.cfg.approval, "tool_safety_tiers", {})
    return check_tool_safety_tiers(tool_safety_tiers=tool_safety_tiers)


async def _watchdog_check_http(
    ctx: AgentContext,
    key: str,
    srv_cfg: McpServerConfig,
    restart_counts: dict[str, int],
    max_restarts: int,
) -> None:
    """Probe one HTTP server and restart via lifecycle manager when health check fails.

    Decision logic (in order):
    - probe.reachable=True and status_code=200 → fully healthy; reset count, record success.
    - probe.reachable=True and restart_recommended=False → degraded but not restartable;
      reset count, log warning if operator_action_required=True.
    - probe.reachable=False or restart_recommended=True → attempt restart if under limit.

    For startup_mode="subprocess" servers, restart is delegated to
    ctx.services_required.lifecycle.restart().  Other modes (externally-managed) only
    log a warning because the agent does not own those processes.
    """
    if ctx.services_required.http is None:
        raise RuntimeError("http service not initialized")
    if not srv_cfg.url:
        return
    probe = await _probe_mcp_health_detail(ctx.services_required.http, srv_cfg.url)

    if probe.reachable and probe.status_code == HTTPStatus.OK:
        # Fully healthy
        restart_counts[key] = 0
        if ctx.services_required.health_registry:
            ctx.services_required.health_registry.record_success(key)
        return

    if probe.reachable and not probe.restart_recommended:
        # Reachable but degraded; restart will not help
        restart_counts[key] = 0
        if probe.operator_action_required:
            logger.warning(
                "Watchdog: %r requires operator action: %s",
                key,
                probe.body,
            )
        if ctx.services_required.health_registry is not None:
            body: dict = probe.body or {}
            reason_raw = body.get("reason") or body.get("message")
            reason = str(reason_raw) if reason_raw is not None else None
            ctx.services_required.health_registry.record_degraded(key, reason=reason)
        return

    # Either unreachable (probe.reachable=False) or restart_recommended=True
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
    if (
        srv_cfg.startup_mode == StartupMode.SUBPROCESS
        and ctx.services_required.lifecycle is not None
    ):
        try:
            await ctx.services_required.lifecycle.restart(key)
            restart_counts[key] = count + 1
        except (OSError, RuntimeError) as e:
            logger.error("Watchdog: failed to restart %r: %s", key, e)
    else:
        logger.warning(
            "Watchdog: %r is not a subprocess-mode server;"
            " manual intervention required",
            key,
        )
    if ctx.services_required.health_registry:
        ctx.services_required.health_registry.record_failure(key)


async def watchdog_loop(ctx: AgentContext) -> None:
    """Periodically probe MCP server health and restart via lifecycle manager on failure.

    Runs until cancelled (e.g. when the REPL exits).
    Restart attempts per server are capped at mcp_watchdog_max_restarts to
    prevent infinite restart loops.
    """
    interval = ctx.cfg.mcp.mcp_watchdog_interval
    max_restarts = ctx.cfg.mcp.mcp_watchdog_max_restarts
    restart_counts: dict[str, int] = {}
    if interval <= 0:
        logger.warning(
            "Watchdog: disabled (interval=%.0f) — failed servers will not be auto-restarted",
            interval,
        )
        return
    logger.info(
        "Watchdog: enabled (interval=%.0fs, max_restarts=%d)",
        interval,
        max_restarts,
    )
    while True:
        await asyncio.sleep(interval)
        for key, srv_cfg in ctx.cfg.mcp.mcp_servers.items():
            if srv_cfg.transport == TransportType.HTTP:
                await _watchdog_check_http(
                    ctx,
                    key,
                    srv_cfg,
                    restart_counts,
                    max_restarts,
                )
        if ctx.services_required.lifecycle is not None:
            await ctx.services_required.lifecycle.shutdown_idle()


def audit_security_defaults(
    ctx: AgentContext, production_mode: bool = False
) -> list[str]:
    """Audit security-related configuration defaults and return warning strings.

    In production mode (production_mode=True), HTTP servers without auth_token
    raise RuntimeError instead of returning a warning.

    Checks for risky settings such as:
      - auth_token disabled (empty) on servers that support it
      - shell sandbox disabled (none backend)
      - cicd workflow_allowlist empty (fail-closed: deny-all)
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
        if not srv_cfg.auth_token and srv_cfg.transport == TransportType.HTTP and srv_cfg.url:
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

    # Check shell sandbox and command_allowlist
    try:
        shell_cfg = load_shell_audit_config()
    except RuntimeError as exc:
        msg = str(exc)
        if production_mode:
            logger.error(msg)
            raise
        logger.warning(msg)
        warnings.append(msg)
        shell_cfg = None

    if shell_cfg is not None:
        import shutil as _shutil

        if shell_cfg.sandbox_backend == "none":
            msg = "shell_sandbox_backend=none is not permitted in production mode"
            if production_mode:
                raise RuntimeError(f"Production mode requires shell sandbox. {msg}")
            logger.warning("Security: %s", msg)
            warnings.append(f"Security: {msg}")
        elif shell_cfg.sandbox_backend != "firejail":
            msg = (
                f"shell_sandbox_backend={shell_cfg.sandbox_backend!r}; "
                "production default is 'firejail'. "
                "Update config/shell_mcp_server.toml."
            )
            logger.warning("Security: %s", msg)
            warnings.append(f"Security: {msg}")
        if shell_cfg.sandbox_backend == "firejail" and not _shutil.which("firejail"):
            msg = (
                "shell_sandbox_backend=firejail but firejail binary not found in PATH. "
                "Install firejail or change shell_sandbox_backend in shell_mcp_server.toml."
            )
            raise RuntimeError(msg)
        if not shell_cfg.command_allowlist and not lockdown:
            fail_closed_empty.append("shell.command_allowlist")
            msg = (
                "DENY-ALL detected: shell.command_allowlist is empty. "
                "shell-mcp will reject ALL shell commands. "
                "Verify this is intentional or add allowed commands to shell_mcp_server.toml."
            )
            logger.warning(msg)
            warnings.append(msg)

    # Check git allowed_repo_paths
    try:
        git_cfg = load_git_audit_config()
    except RuntimeError as exc:
        msg = str(exc)
        if production_mode:
            logger.error(msg)
            raise
        logger.warning(msg)
        warnings.append(msg)
        git_cfg = None

    if git_cfg is not None and not git_cfg.allowed_repo_paths and not lockdown:
        fail_closed_empty.append("git.allowed_repo_paths")
        msg = (
            "DENY-ALL detected: git.allowed_repo_paths is empty. "
            "git-mcp will reject ALL repository operations. "
            "Verify this is intentional or add allowed paths to git_mcp_server.toml."
        )
        logger.warning(msg)
        warnings.append(msg)

    # Check github allowed_repos (fail-closed — empty = deny all repo access)
    try:
        github_cfg = load_github_audit_config()
    except RuntimeError as exc:
        msg = str(exc)
        if production_mode:
            logger.error(msg)
            raise
        logger.warning(msg)
        warnings.append(msg)
        github_cfg = None

    if github_cfg is not None and not github_cfg.allowed_repos and not lockdown:
        fail_closed_empty.append("github.allowed_repos")
        msg = (
            "DENY-ALL detected: github.allowed_repos is empty. "
            "github-mcp will reject ALL repo access requests. "
            "Verify this is intentional or add allowed repos to github_mcp_server.toml."
        )
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

    # Check cicd workflow_allowlist (fail-closed — empty = deny all workflow triggers)
    try:
        cicd_cfg = load_cicd_audit_config()
    except RuntimeError as exc:
        msg = str(exc)
        if production_mode:
            logger.error(msg)
            raise
        logger.warning(msg)
        warnings.append(msg)
        cicd_cfg = None

    if cicd_cfg is not None and not cicd_cfg.workflow_allowlist and not lockdown:
        fail_closed_empty.append("cicd.workflow_allowlist")
        msg = (
            "DENY-ALL detected: cicd.workflow_allowlist is empty. "
            "cicd-mcp will reject ALL workflow trigger requests. "
            "Verify this is intentional or add allowed workflows to cicd_mcp_server.toml."
        )
        logger.warning(msg)
        warnings.append(msg)

    # Surface GitHub write settings (warning only — not a production-mode hard error)
    try:
        gh_write_cfg = load_github_audit_config()
    except RuntimeError as exc:
        logger.debug("Security audit: skipped GitHub write settings check: %s", exc)
        gh_write_cfg = None

    if gh_write_cfg is not None:
        if gh_write_cfg.allow_force_push:
            msg = "github.allow_force_push=true (force push and rebase merge permitted)"
            logger.warning("Security: %s", msg)
            warnings.append(f"Security: {msg}")
        if not gh_write_cfg.require_pr_review:
            msg = "github.require_pr_review=false (PR merge without review permitted)"
            logger.warning("Security: %s", msg)
            warnings.append(f"Security: {msg}")

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
