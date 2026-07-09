from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from shared.mcp_config import SecurityProfile


@dataclass
class ConfigValidationResult:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


# Strict keys that must be true in production (defaulting to false is an error)
_REQUIRED_STRICT_KEYS = (
    "plugin_strict",
    "tool_definitions_strict",
    "routing_drift_strict",
)

# Keys where explicit false is an error in production (absent is acceptable)
_REQUIRED_NOT_FALSE_KEYS = ("use_tool_dag",)


def _check_missing_tool_safety_tiers(
    tool_safety_tiers: Any,
    known_tools: set[str] | None = None,
) -> list[str]:
    """Return tool names that are registered but missing from tool_safety_tiers."""
    if known_tools is None:
        try:
            from shared.tool_registry import get_registry

            known_tools = set(get_registry().get_all_tool_names())
        except Exception:
            return []
    missing = [t for t in sorted(known_tools) if t not in tool_safety_tiers]
    return [f"'{t}' not in tool_safety_tiers" for t in missing]


def _check_unknown_tool_safety_tiers(
    tool_safety_tiers: Any,
    known_tools: set[str] | None = None,
) -> list[str]:
    """Return tool_safety_tiers keys that are not registered tool names."""
    if known_tools is None:
        try:
            from shared.tool_registry import get_registry

            known_tools = set(get_registry().get_all_tool_names())
        except Exception:
            return []
    unknown = sorted(set(tool_safety_tiers) - known_tools)
    return [f"'{k}' not a registered tool name" for k in unknown]


class ProductionConfigValidator:
    def validate(
        self,
        config: Any,
        security_profile: SecurityProfile | str = "local",
        known_tools: set[str] | None = None,
        allowed_repos_mode: str | None = None,
    ) -> ConfigValidationResult:
        errors: list[str] = []
        warnings: list[str] = []

        is_production = security_profile == "production"

        # Strict keys: default false is an error
        for key in _REQUIRED_STRICT_KEYS:
            if not config.get(key, False):
                msg = f"{key}=false — strict mode is required in production"
                if is_production:
                    errors.append(msg)
                else:
                    warnings.append(f"[local/development] {msg}")

        # Not-false keys: explicit false is an error (absent is acceptable)
        for key in _REQUIRED_NOT_FALSE_KEYS:
            if config.get(key) is False:
                msg = f"{key}=false — strict mode is required in production"
                if is_production:
                    errors.append(msg)
                else:
                    warnings.append(f"[local/development] {msg}")

        # Bidirectional tool_safety_tiers validation
        tool_safety_tiers = config.get("tool_safety_tiers") or {}
        if tool_safety_tiers:
            missing_tiers = _check_missing_tool_safety_tiers(
                tool_safety_tiers, known_tools=known_tools
            )
            if missing_tiers:
                tier_msg = "; ".join(missing_tiers)
                if is_production:
                    errors.append(f"Missing safety tiers: {tier_msg}")
                else:
                    warnings.append(
                        f"[local/development] Missing safety tiers: {tier_msg}"
                    )

            unknown_tiers = _check_unknown_tool_safety_tiers(
                tool_safety_tiers, known_tools=known_tools
            )
            if unknown_tiers:
                tier_msg = "; ".join(unknown_tiers)
                if is_production:
                    errors.append(f"Unknown safety tier keys: {tier_msg}")
                else:
                    warnings.append(
                        f"[local/development] Unknown safety tier keys: {tier_msg}"
                    )

        # GitHub allowed_repos_mode check
        if allowed_repos_mode == "fail_open":
            msg = (
                "github.allowed_repos_mode='fail_open' is not permitted in production mode. "
                "Set allowed_repos_mode='fail_closed' in github_mcp_server.toml."
            )
            if is_production:
                errors.append(msg)
            else:
                warnings.append(f"[local/development] {msg}")

        # allowed_tools visibility
        allowed_tools = config.get("allowed_tools")
        if isinstance(allowed_tools, (list, tuple)) and len(allowed_tools) == 0:
            msg = "allowed_tools=[] (all tools allowed; use allowlist to restrict)"
            if is_production:
                errors.append(msg)
            else:
                warnings.append(f"[local/development] {msg}")

        return ConfigValidationResult(errors=errors, warnings=warnings)

    def validate_github_fail_open(
        self, allowed_repos_mode: str, security_profile: SecurityProfile | str = "local"
    ) -> ConfigValidationResult:
        errors: list[str] = []
        warnings: list[str] = []

        is_production = security_profile == "production"

        if allowed_repos_mode == "fail_open":
            msg = (
                "github.allowed_repos_mode='fail_open' is not permitted in production mode. "
                "Set allowed_repos_mode='fail_closed' in github_mcp_server.toml."
            )
            if is_production:
                errors.append(msg)
            else:
                warnings.append(f"[local/development] {msg}")

        return ConfigValidationResult(errors=errors, warnings=warnings)

    def validate_unknown_tool_safety_tiers(
        self, unknown_keys: list[str]
    ) -> ConfigValidationResult:
        errors = [
            f"tool_safety_tiers contains unknown key {k!r} (not a registered tool name)"
            for k in unknown_keys
        ]
        return ConfigValidationResult(errors=errors)


__all__ = ["ConfigValidationResult", "ProductionConfigValidator"]
