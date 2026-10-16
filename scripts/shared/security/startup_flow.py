#!/usr/bin/env python3
"""scripts/shared/security/startup_flow.py — the one startup-validation ordering every MCP server runs."""

from __future__ import annotations

import hashlib
import logging
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from enum import StrEnum

from shared.security.posture_contract import (
    CHECK_ID_AUTH_TOKEN,
    CHECK_ID_OWN_CONFIG_ONLY,
    CHECK_ID_PUBLISHED_TOOLS,
    SECURITY_CONTRACT_VERSION,
    SecurityPosture,
    compute_config_fingerprint,
)
from shared.security.result_dto import (
    DEFAULT_POLICY_VERSION,
    REASON_AUTH_TOKEN_MISSING,
    REASON_CONFIG_INVALID,
    REASON_CONFIG_MISSING,
    REASON_DEPENDENCY_UNREACHABLE,
    REASON_OK,
    SecurityCheckResult,
    SecurityCheckStatus,
)

FLOW_VERSION = "1"

# The key a server's normalized config view must carry so the flow can prove the view came from
# ConfigLoader.restrict_to(own_config_file).
OWN_CONFIG_FILE_VIEW_KEY = "own_config_file"
_REJECTED_VIEW_MARKER = "config_view_rejected"

logger = logging.getLogger(__name__)


class StartupStage(StrEnum):
    """The REQ-003 stages, in the order every MCP server must run them."""

    CONFIG_LOAD = "config_load"
    SCHEMA_VALIDATION = "schema_validation"
    COMMON_SECURITY_VALIDATION = "common_security_validation"
    SERVER_SECURITY_VALIDATION = "server_security_validation"
    DEPENDENCY_VALIDATION = "dependency_validation"
    TOOL_CAPABILITY_VALIDATION = "tool_capability_validation"
    RUNTIME_STATE_INSTALLATION = "runtime_state_installation"
    HTTP_BIND = "http_bind"
    READY = "ready"


# CONFIG_LOAD is performed by the caller (scripts/mcp_servers/server.py) and is asserted here
# through check_own_config_only(). RUNTIME_STATE_INSTALLATION, HTTP_BIND and READY belong to the
# caller and may only be reached when the returned posture has ready=True.
EXECUTED_STAGES: tuple[StartupStage, ...] = (
    StartupStage.SCHEMA_VALIDATION,
    StartupStage.COMMON_SECURITY_VALIDATION,
    StartupStage.SERVER_SECURITY_VALIDATION,
    StartupStage.DEPENDENCY_VALIDATION,
    StartupStage.TOOL_CAPABILITY_VALIDATION,
)

# For each stage the flow may be given a callable for: the check-id namespace a raised stage
# reports under, and the reason code it maps to (REQ-004).
_STAGE_FAILURE_SHAPE: Mapping[StartupStage, tuple[str, str]] = {
    StartupStage.SCHEMA_VALIDATION: ("schema", REASON_CONFIG_INVALID),
    StartupStage.COMMON_SECURITY_VALIDATION: ("common", REASON_CONFIG_INVALID),
    StartupStage.SERVER_SECURITY_VALIDATION: ("server", REASON_CONFIG_INVALID),
    StartupStage.DEPENDENCY_VALIDATION: ("dependency", REASON_DEPENDENCY_UNREACHABLE),
    StartupStage.TOOL_CAPABILITY_VALIDATION: ("tool", REASON_CONFIG_INVALID),
}

StageCallable = Callable[[], Iterable[SecurityCheckResult]]


@dataclass(frozen=True)
class StageOutcome:
    """What one stage produced: its checks in order, and whether the stage is fatal."""

    stage: StartupStage
    checks: tuple[SecurityCheckResult, ...]
    fatal: bool


def _ok(check_id: str, message: str) -> SecurityCheckResult:
    return SecurityCheckResult(
        check_id=check_id,
        status=SecurityCheckStatus.OK,
        reason_code=REASON_OK,
        message=message,
    )


def _failed(check_id: str, reason_code: str, message: str) -> SecurityCheckResult:
    return SecurityCheckResult(
        check_id=check_id,
        status=SecurityCheckStatus.FAILED,
        reason_code=reason_code,
        message=message,
    )


def check_own_config_only(
    server_key: str,
    own_config_file: str,
    config_view: Mapping[str, object],
) -> SecurityCheckResult:
    """Confirm the config view the server hands the flow came from its own config file only."""
    expected = f"{server_key}_mcp_server.toml"
    view_name = config_view.get(OWN_CONFIG_FILE_VIEW_KEY)
    if own_config_file == expected and view_name == own_config_file:
        try:
            compute_config_fingerprint(config_view)
        except ValueError:
            reason = REASON_CONFIG_INVALID
            message = (
                f"{server_key} config view carries a value no fingerprint may hash"
            )
            return _failed(CHECK_ID_OWN_CONFIG_ONLY, reason, message)
        return _ok(
            CHECK_ID_OWN_CONFIG_ONLY,
            f"{server_key} config view is restricted to {expected}",
        )
    reason = REASON_CONFIG_MISSING if not own_config_file else REASON_CONFIG_INVALID
    message = f"{server_key} config view is not restricted to {expected}"
    return _failed(CHECK_ID_OWN_CONFIG_ONLY, reason, message)


def check_auth_token_present(
    server_key: str, auth_token: str | None
) -> SecurityCheckResult:
    """Mirror the Agent-side mcp_auth rule on the server side (Plan UNK-06: WARNING, not FAILED)."""
    if auth_token:
        return _ok(CHECK_ID_AUTH_TOKEN, f"{server_key} auth_token is configured")
    message = f"{server_key} auth_token is empty"
    return SecurityCheckResult(
        check_id=CHECK_ID_AUTH_TOKEN,
        status=SecurityCheckStatus.WARNING,
        reason_code=REASON_AUTH_TOKEN_MISSING,
        message=message,
    )


def check_published_tools_declared(
    server_key: str,
    declared_tools: Iterable[str],
) -> SecurityCheckResult:
    """Confirm the server declares a usable tool set; a declared-but-disabled tool is not a violation."""
    names = tuple(declared_tools)
    if not names or not all(isinstance(name, str) and name for name in names):
        message = f"{server_key} declares no usable tool names"
        return _failed(CHECK_ID_PUBLISHED_TOOLS, REASON_CONFIG_INVALID, message)
    return _ok(
        CHECK_ID_PUBLISHED_TOOLS, f"{server_key} declares {len(names)} tool name(s)"
    )


def _run_stage(
    stage: StartupStage, stage_callable: StageCallable
) -> list[SecurityCheckResult]:
    """Run one server-supplied stage, turning a raise into a FAILED check (REQ-004)."""
    namespace, reason = _STAGE_FAILURE_SHAPE[stage]
    try:
        return list(stage_callable())
    except Exception as exc:  # noqa: BLE001 — a stage that raises must yield a posture, not a crash
        message = f"{stage.value} stage raised {type(exc).__name__}"
        return [_failed(f"{namespace}.stage_error", reason, message)]


def run_startup_validation(
    server_key: str,
    *,
    own_config_file: str,
    config_view: Mapping[str, object],
    auth_token: str | None = None,
    declared_tools: Iterable[str] = (),
    schema_checks: StageCallable | None = None,
    server_checks: StageCallable | None = None,
    dependency_checks: StageCallable | None = None,
    tool_capability_checks: StageCallable | None = None,
    policy_version: str = DEFAULT_POLICY_VERSION,
) -> SecurityPosture:
    """Run the REQ-003 stages in order and return the posture; never raises, never binds HTTP.

    The caller binds only when the returned posture has validated=True and ready=True. The flow
    stops at the first stage that yields a FAILED check, so a partially validated server can
    never reach RUNTIME_STATE_INSTALLATION.
    """
    stage_callables: Mapping[StartupStage, StageCallable | None] = {
        StartupStage.SCHEMA_VALIDATION: schema_checks,
        StartupStage.SERVER_SECURITY_VALIDATION: server_checks,
        StartupStage.DEPENDENCY_VALIDATION: dependency_checks,
        StartupStage.TOOL_CAPABILITY_VALIDATION: tool_capability_checks,
    }
    checks: list[SecurityCheckResult] = []
    for stage in EXECUTED_STAGES:
        if stage is StartupStage.COMMON_SECURITY_VALIDATION:
            stage_checks = [
                check_own_config_only(server_key, own_config_file, config_view),
                check_auth_token_present(server_key, auth_token),
                check_published_tools_declared(server_key, declared_tools),
            ]
        else:
            stage_callable = stage_callables[stage]
            if stage_callable is None:
                continue
            stage_checks = _run_stage(stage, stage_callable)
        outcome = StageOutcome(
            stage=stage,
            checks=tuple(stage_checks),
            fatal=any(
                check.status is SecurityCheckStatus.FAILED for check in stage_checks
            ),
        )
        checks.extend(outcome.checks)
        if outcome.fatal:
            _log_fatal_stage(outcome.stage, outcome.checks)
            break

    validated = not any(check.status is SecurityCheckStatus.FAILED for check in checks)
    return SecurityPosture(
        contract_version=SECURITY_CONTRACT_VERSION,
        server_key=server_key,
        policy_version=policy_version,
        validated=validated,
        ready=validated,
        fingerprint=_posture_fingerprint(server_key, config_view),
        checks=tuple(checks),
    )


def _log_fatal_stage(
    stage: StartupStage, checks: Iterable[SecurityCheckResult]
) -> None:
    """Record which checks failed, by id and reason code only (REQ-004)."""
    failed = ", ".join(
        f"{check.check_id}:{check.reason_code}"
        for check in checks
        if check.status is SecurityCheckStatus.FAILED
    )
    logger.warning(
        "security startup flow v%s: stage %s failed (%s)",
        FLOW_VERSION,
        stage.value,
        failed,
    )


def _posture_fingerprint(server_key: str, config_view: Mapping[str, object]) -> str:
    """Hash the server's own view, or a fixed marker when the view is not hashable."""
    try:
        return compute_config_fingerprint(config_view)
    except ValueError:
        digest_source = f"{server_key}:{_REJECTED_VIEW_MARKER}"
        return hashlib.sha256(digest_source.encode("utf-8")).hexdigest()
