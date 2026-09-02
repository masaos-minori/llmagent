"""scripts/agent/services/security_audit.py

Security-defaults auditing functions.

Extracted from scripts/agent/repl_health.py to allow targeted loading
when modifying health check behaviour.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar, Optional

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

T = TypeVar("T")

logger = Logger(__name__, "/opt/llm/logs/agent.log")


def _load_audit_config_or_warn[T](
    loader: Callable[[], T],
    production_mode: bool,
    warnings: list[str],
) -> T | None:
    """Call *loader*; on RuntimeError, raise in production mode or append a warning.

    Returns the loaded config, or None when the load failed (non-production mode).
    """
    try:
        return loader()
    except RuntimeError as exc:
        msg = str(exc)
        if production_mode:
            logger.error(msg)
            raise
        logger.warning(msg)
        warnings.append(msg)
        return None


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

    # Check shell sandbox and command_allowlist.
    # If configuration is missing or cannot be loaded, skip shell-related security checks.
    shell_cfg = _load_audit_config_or_warn(
        load_shell_audit_config, production_mode, warnings
    )

    if shell_cfg is not None:
        import shutil as _shutil

        if shell_cfg.sandbox_backend == "none":
            msg = "shell_sandbox_backend=none is not permitted"
            raise RuntimeError(f"{msg} regardless of environment")
        elif shell_cfg.sandbox_backend != "firejail":
            msg = (
                f"shell_sandbox_backend={shell_cfg.sandbox_backend!r}; "
                "production default is 'firejail'. "
                "Update config/shell_mcp_server.toml."
            )
            logger.warning("Security: %s", msg)
            warnings.append(f"Security: {msg}")
        # NOTE: Unlike other checks in this function, a configured-but-missing
        # sandbox backend means shell commands would run completely unsandboxed,
        # which is unacceptable in any environment (local or production).
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
        except Exception:  # noqa: BLE001 — tool registry lookup is best-effort; fall back to unrestricted set rather than abort startup
            known_tools = None

    github_cfg = _load_audit_config_or_warn(
        load_github_audit_config, production_mode, warnings
    )

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
    git_cfg = _load_audit_config_or_warn(
        load_git_audit_config, production_mode, warnings
    )

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
    cicd_cfg = _load_audit_config_or_warn(
        load_cicd_audit_config, production_mode, warnings
    )

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
