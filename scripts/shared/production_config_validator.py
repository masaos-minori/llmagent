"""scripts/shared/production_config_validator.py"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shared.mcp_config import SecurityProfile


@dataclass
class ConfigValidationResult:
    """Result of configuration validation containing errors and warnings."""

    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


# Strict keys that must be true in production (defaulting to false is an error)
_REQUIRED_STRICT_KEYS = (
    "tool_definitions_strict",
    "routing_drift_strict",
)

# Keys where explicit false is an error in production (absent is acceptable)
_REQUIRED_NOT_FALSE_KEYS: tuple[str, ...] = ()


def _resolve_known_tools(known_tools: set[str] | None) -> set[str] | None:
    """Resolve the known tool name set, falling back to the tool registry.

    Returns `None` if `known_tools` was not provided and the registry lookup
    fails, signaling the caller to skip its check.
    """
    if known_tools is not None:
        return known_tools
    try:
        from shared.tool_registry import get_registry

        return set(get_registry().get_all_tool_names())
    except Exception:  # noqa: BLE001 — tool registry lookup is best-effort; skip this check rather than fail production config validation
        return None


def _check_missing_tool_safety_tiers(
    tool_safety_tiers: Mapping[str, object],
    known_tools: set[str] | None = None,
) -> list[str]:
    """Return tool names that are registered but missing from tool_safety_tiers."""
    resolved_tools = _resolve_known_tools(known_tools)
    if resolved_tools is None:
        return []
    missing = [t for t in sorted(resolved_tools) if t not in tool_safety_tiers]
    return [f"'{t}' not in tool_safety_tiers" for t in missing]


def _check_unknown_tool_safety_tiers(
    tool_safety_tiers: Mapping[str, object],
    known_tools: set[str] | None = None,
) -> list[str]:
    """Return tool_safety_tiers keys that are not registered tool names."""
    resolved_tools = _resolve_known_tools(known_tools)
    if resolved_tools is None:
        return []
    unknown = sorted(set(tool_safety_tiers) - resolved_tools)
    return [f"'{k}' not a registered tool name" for k in unknown]


def _check_approval_risk_floor(
    approval_risk_rules: Mapping[str, object],
    tool_safety_tiers: Mapping[str, object],
    known_tools: set[str] | None = None,
) -> list[str]:
    """Return tool names whose resolved effective risk is below HIGH."""
    from agent.tool_policy import _TIER_TO_RISK, RiskLevel

    GIT_WRITE_TOOLS = frozenset(("git_checkout", "git_pull", "git_push"))
    resolved_tools = _resolve_known_tools(known_tools)
    if resolved_tools is None:
        return []
    targets = GIT_WRITE_TOOLS & resolved_tools
    below_high: list[str] = []
    for tool_name in sorted(targets):
        raw_rule = approval_risk_rules.get(tool_name)
        if raw_rule is not None:
            try:
                base = RiskLevel(str(raw_rule))
            except ValueError:
                continue
        elif tool_name in tool_safety_tiers:
            tier = str(tool_safety_tiers[tool_name])
            base = _TIER_TO_RISK.get(tier, RiskLevel.MEDIUM)
        else:
            continue
        if base != RiskLevel.HIGH:
            below_high.append(f"'{tool_name}' effective risk={base}")
    return below_high


class ProductionConfigValidator:
    """Validate configuration against production security requirements.

    Checks strict mode flags, tool safety tier consistency, and other
    production-critical settings.
    """

    def validate(
        self,
        config: Mapping[str, object],
        security_profile: SecurityProfile | str = "local",
        known_tools: set[str] | None = None,
    ) -> ConfigValidationResult:
        """Validate the full configuration against security profile rules."""
        errors: list[str] = []
        warnings: list[str] = []

        is_production = security_profile == "production"

        # Strict keys: default false is an error
        for key in _REQUIRED_STRICT_KEYS:
            if not config.get(key, False):
                msg = f"{key}=false — strict mode is required in production"
                self._record(errors, warnings, msg, is_production)

        # Not-false keys: explicit false is an error (absent is acceptable)
        for key in _REQUIRED_NOT_FALSE_KEYS:
            if config.get(key) is False:
                msg = f"{key}=false — strict mode is required in production"
                self._record(errors, warnings, msg, is_production)

        # Bidirectional tool_safety_tiers validation
        raw_tiers = config.get("tool_safety_tiers")
        tool_safety_tiers: Mapping[str, object] = (
            raw_tiers if isinstance(raw_tiers, Mapping) else {}
        )
        if tool_safety_tiers:
            missing_tiers = _check_missing_tool_safety_tiers(
                tool_safety_tiers, known_tools=known_tools
            )
            if missing_tiers:
                tier_msg = "; ".join(missing_tiers)
                self._record(
                    errors, warnings, f"Missing safety tiers: {tier_msg}", is_production
                )

            unknown_tiers = _check_unknown_tool_safety_tiers(
                tool_safety_tiers, known_tools=known_tools
            )
            if unknown_tiers:
                tier_msg = "; ".join(unknown_tiers)
                self._record(
                    errors,
                    warnings,
                    f"Unknown safety tier keys: {tier_msg}",
                    is_production,
                )

        # Approval risk floor check for git write tools
        approval_risk_rules = config.get("approval_risk_rules")
        if isinstance(approval_risk_rules, Mapping):
            low_risk_tools = _check_approval_risk_floor(
                approval_risk_rules, tool_safety_tiers, known_tools=known_tools
            )
            if low_risk_tools:
                tool_list = "; ".join(low_risk_tools)
                msg = f"Effective risk below HIGH for git tools: {tool_list}"
                self._record(errors, warnings, msg, is_production)

        # allowed_tools visibility
        allowed_tools = config.get("allowed_tools")
        if isinstance(allowed_tools, (list, tuple)) and len(allowed_tools) == 0:
            msg = "allowed_tools=[] (all tools allowed; use allowlist to restrict)"
            self._record(errors, warnings, msg, is_production)

        return ConfigValidationResult(errors=errors, warnings=warnings)

    def validate_unknown_tool_safety_tiers(
        self, unknown_keys: list[str]
    ) -> ConfigValidationResult:
        """Validate that unknown tool_safety_tiers keys are rejected."""
        errors = [
            f"tool_safety_tiers contains unknown key {k!r} (not a registered tool name)"
            for k in unknown_keys
        ]
        return ConfigValidationResult(errors=errors)

    @classmethod
    def _record(
        cls,
        errors: list[str],
        warnings: list[str],
        msg: str,
        is_production: bool,
    ) -> None:
        """Format `msg` as an error or warning and append it to the matching list."""
        e, w = cls._format_error_or_warning(msg, is_production)
        errors.extend(e)
        warnings.extend(w)

    @staticmethod
    def _format_error_or_warning(
        msg: str, is_production: bool
    ) -> tuple[list[str], list[str]]:
        errors: list[str] = []
        warnings: list[str] = []
        if is_production:
            errors.append(msg)
        else:
            warnings.append(f"[local/development] {msg}")
        return errors, warnings


__all__ = ["ConfigValidationResult", "ProductionConfigValidator"]
