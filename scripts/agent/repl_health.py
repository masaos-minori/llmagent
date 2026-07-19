"""MCP server health monitoring and startup validation for AgentREPL.

Standalone async functions taking AgentContext as first argument.
Extracted from agent/repl.py to allow targeted loading when modifying
health check behaviour.
"""

from __future__ import annotations

from http import HTTPStatus
from pathlib import Path
from urllib.parse import urlparse

import httpx
from shared.logger import Logger
from shared.mcp_config import TransportType
from shared.production_config_validator import ProductionConfigValidator

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
    except Exception as exc:  # noqa: BLE001 — health check must not fail on body parse errors
        return McpHealthProbeResult(
            reachable=True,
            status_code=resp.status_code,
            restart_recommended=False,
            operator_action_required=False,
            body={},
            parse_failed=True,
            parse_error=f"{exc} (raw={resp.text[:200]!r})",
        )
    restart_recommended: bool = bool(body.get("restart_recommended", False))
    operator_action_required: bool = bool(body.get("operator_action_required", False))
    return McpHealthProbeResult(
        reachable=True,
        status_code=resp.status_code,
        restart_recommended=restart_recommended,
        operator_action_required=operator_action_required,
        body=body,
    )


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


def check_workflow_definition(workflows_dir: Path | None = None) -> None:
    """Raise RuntimeError if the workflow definition file is missing."""
    from agent.workflow.workflow_loader import (  # noqa: PLC0415 — lazy to avoid circular import
        WORKFLOWS_DIR,
    )

    target_dir = workflows_dir if workflows_dir is not None else WORKFLOWS_DIR
    workflow_file = target_dir / "default.json"
    if not workflow_file.exists():
        raise RuntimeError(
            f"Workflow definition file not found: {workflow_file}. Deploy config/workflows/default.json to fix this."
        )


REQUIRED_WORKFLOW_TABLES: dict[str, list[str]] = {
    "tasks": ["task_id", "session_id", "workflow_id", "status", "created_at"],
    "attempts": ["attempt_id", "task_id", "stage_id", "status"],
    "processed_events": ["event_id", "task_id"],
    "artifacts": ["artifact_id", "task_id"],
    "approvals": ["approval_id", "task_id", "status"],
    "workflow_schema_version": ["version", "applied_at"],
}


def check_workflow_schema(db_path: str | None = None) -> None:
    """Raise RuntimeError if the workflow DB is missing required tables or columns."""
    from db.helper import SQLiteHelper  # noqa: PLC0415
    from db.schema_sql import WORKFLOW_SCHEMA_VERSION  # noqa: PLC0415

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
                    f"Workflow schema missing table {table!r}. Run create_workflow_schema() to initialize."
                )
            existing = {
                row[1] for row in db.fetchall(f"PRAGMA table_info({table})", ())
            }
            for col in required_cols:
                if col not in existing:
                    raise RuntimeError(
                        f"Workflow schema missing column {table}.{col}. Reinitialize the workflow database."
                    )

        rows = db.fetchall(
            "SELECT version FROM workflow_schema_version ORDER BY applied_at DESC LIMIT 1",
            (),
        )
        actual_version = rows[0][0] if rows else None
        if actual_version != WORKFLOW_SCHEMA_VERSION:
            raise RuntimeError(
                f"Workflow schema version mismatch: expected {WORKFLOW_SCHEMA_VERSION!r}, "
                f"found {actual_version!r}. Run create_workflow_schema() to migrate."
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
    warnings: list[str] = check_tool_safety_tiers(tool_safety_tiers=tool_safety_tiers)
    return warnings


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
        if (
            not srv_cfg.auth_token
            and srv_cfg.transport == TransportType.HTTP
            and srv_cfg.url
        ):
            msg = f"{key}: no auth_token configured (auth disabled)"
            violations.append(msg)

    if production_mode and violations:
        servers_str = "; ".join(violations)
        raise RuntimeError(
            f"Production mode requires auth_token on all HTTP MCP servers. Violations: {servers_str}"
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

    # Check production config strict flags and safety tiers
    tool_cfg = getattr(ctx.cfg, "tool", None)
    approval_cfg = getattr(ctx.cfg, "approval", None)
    tool_safety_tiers = (
        getattr(approval_cfg, "tool_safety_tiers", {}) if approval_cfg else {}
    )
    allowed_tools = getattr(tool_cfg, "allowed_tools", None) if tool_cfg else None

    known_tools: set[str] | None = None
    if tool_safety_tiers:
        try:
            from shared.tool_registry import get_registry

            known_tools = set(get_registry().get_all_tool_names())
        except Exception:
            known_tools = None

    github_cfg = None
    try:
        github_cfg = load_github_audit_config()
    except RuntimeError as exc:
        msg = str(exc)
        if production_mode:
            logger.error(msg)
            raise
        logger.warning(msg)
        warnings.append(msg)

    result = ProductionConfigValidator().validate(
        {
            "tool_definitions_strict": getattr(
                tool_cfg, "tool_definitions_strict", False
            ),
            "routing_drift_strict": getattr(tool_cfg, "routing_drift_strict", False),
            "tool_safety_tiers": tool_safety_tiers,
            "allowed_tools": allowed_tools,
        },
        security_profile="production" if production_mode else "local",
        known_tools=known_tools,
    )
    if result.errors:
        for msg in result.errors:
            if production_mode:
                raise RuntimeError(msg)
            logger.warning("Security: %s", msg)
            warnings.append(f"Security: {msg}")
    for warning in result.warnings:
        logger.warning("Security: %s", warning)
        warnings.append(warning)

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
    if github_cfg is not None and not github_cfg.allowed_repos and not lockdown:
        fail_closed_empty.append("github.allowed_repos")
        msg = (
            "DENY-ALL detected: github.allowed_repos is empty. "
            "github-mcp will reject ALL repo access requests. "
            "Verify this is intentional or add allowed repos to github_mcp_server.toml."
        )
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
