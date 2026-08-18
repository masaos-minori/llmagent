"""scripts/shared/production_config_validator.py"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shared.mcp_config import SecurityProfile


from mutmut.mutation.trampoline import wrap_in_trampoline as _mutmut_mutated, MutantDict


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
mutants_x__resolve_known_tools__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x__resolve_known_tools__mutmut)
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


def x__resolve_known_tools__mutmut_orig(known_tools: set[str] | None) -> set[str] | None:
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


def x__resolve_known_tools__mutmut_1(known_tools: set[str] | None) -> set[str] | None:
    """Resolve the known tool name set, falling back to the tool registry.

    Returns `None` if `known_tools` was not provided and the registry lookup
    fails, signaling the caller to skip its check.
    """
    if known_tools is None:
        return known_tools
    try:
        from shared.tool_registry import get_registry

        return set(get_registry().get_all_tool_names())
    except Exception:  # noqa: BLE001 — tool registry lookup is best-effort; skip this check rather than fail production config validation
        return None


def x__resolve_known_tools__mutmut_2(known_tools: set[str] | None) -> set[str] | None:
    """Resolve the known tool name set, falling back to the tool registry.

    Returns `None` if `known_tools` was not provided and the registry lookup
    fails, signaling the caller to skip its check.
    """
    if known_tools is not None:
        return known_tools
    try:
        from shared.tool_registry import get_registry

        return set(None)
    except Exception:  # noqa: BLE001 — tool registry lookup is best-effort; skip this check rather than fail production config validation
        return None

mutants_x__resolve_known_tools__mutmut['_mutmut_orig'] = x__resolve_known_tools__mutmut_orig # type: ignore # mutmut generated
mutants_x__resolve_known_tools__mutmut['x__resolve_known_tools__mutmut_1'] = x__resolve_known_tools__mutmut_1 # type: ignore # mutmut generated
mutants_x__resolve_known_tools__mutmut['x__resolve_known_tools__mutmut_2'] = x__resolve_known_tools__mutmut_2 # type: ignore # mutmut generated
mutants_x__check_missing_tool_safety_tiers__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x__check_missing_tool_safety_tiers__mutmut)
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


def x__check_missing_tool_safety_tiers__mutmut_orig(
    tool_safety_tiers: Mapping[str, object],
    known_tools: set[str] | None = None,
) -> list[str]:
    """Return tool names that are registered but missing from tool_safety_tiers."""
    resolved_tools = _resolve_known_tools(known_tools)
    if resolved_tools is None:
        return []
    missing = [t for t in sorted(resolved_tools) if t not in tool_safety_tiers]
    return [f"'{t}' not in tool_safety_tiers" for t in missing]


def x__check_missing_tool_safety_tiers__mutmut_1(
    tool_safety_tiers: Mapping[str, object],
    known_tools: set[str] | None = None,
) -> list[str]:
    """Return tool names that are registered but missing from tool_safety_tiers."""
    resolved_tools = None
    if resolved_tools is None:
        return []
    missing = [t for t in sorted(resolved_tools) if t not in tool_safety_tiers]
    return [f"'{t}' not in tool_safety_tiers" for t in missing]


def x__check_missing_tool_safety_tiers__mutmut_2(
    tool_safety_tiers: Mapping[str, object],
    known_tools: set[str] | None = None,
) -> list[str]:
    """Return tool names that are registered but missing from tool_safety_tiers."""
    resolved_tools = _resolve_known_tools(None)
    if resolved_tools is None:
        return []
    missing = [t for t in sorted(resolved_tools) if t not in tool_safety_tiers]
    return [f"'{t}' not in tool_safety_tiers" for t in missing]


def x__check_missing_tool_safety_tiers__mutmut_3(
    tool_safety_tiers: Mapping[str, object],
    known_tools: set[str] | None = None,
) -> list[str]:
    """Return tool names that are registered but missing from tool_safety_tiers."""
    resolved_tools = _resolve_known_tools(known_tools)
    if resolved_tools is not None:
        return []
    missing = [t for t in sorted(resolved_tools) if t not in tool_safety_tiers]
    return [f"'{t}' not in tool_safety_tiers" for t in missing]


def x__check_missing_tool_safety_tiers__mutmut_4(
    tool_safety_tiers: Mapping[str, object],
    known_tools: set[str] | None = None,
) -> list[str]:
    """Return tool names that are registered but missing from tool_safety_tiers."""
    resolved_tools = _resolve_known_tools(known_tools)
    if resolved_tools is None:
        return []
    missing = None
    return [f"'{t}' not in tool_safety_tiers" for t in missing]


def x__check_missing_tool_safety_tiers__mutmut_5(
    tool_safety_tiers: Mapping[str, object],
    known_tools: set[str] | None = None,
) -> list[str]:
    """Return tool names that are registered but missing from tool_safety_tiers."""
    resolved_tools = _resolve_known_tools(known_tools)
    if resolved_tools is None:
        return []
    missing = [t for t in sorted(None) if t not in tool_safety_tiers]
    return [f"'{t}' not in tool_safety_tiers" for t in missing]


def x__check_missing_tool_safety_tiers__mutmut_6(
    tool_safety_tiers: Mapping[str, object],
    known_tools: set[str] | None = None,
) -> list[str]:
    """Return tool names that are registered but missing from tool_safety_tiers."""
    resolved_tools = _resolve_known_tools(known_tools)
    if resolved_tools is None:
        return []
    missing = [t for t in sorted(resolved_tools) if t in tool_safety_tiers]
    return [f"'{t}' not in tool_safety_tiers" for t in missing]

mutants_x__check_missing_tool_safety_tiers__mutmut['_mutmut_orig'] = x__check_missing_tool_safety_tiers__mutmut_orig # type: ignore # mutmut generated
mutants_x__check_missing_tool_safety_tiers__mutmut['x__check_missing_tool_safety_tiers__mutmut_1'] = x__check_missing_tool_safety_tiers__mutmut_1 # type: ignore # mutmut generated
mutants_x__check_missing_tool_safety_tiers__mutmut['x__check_missing_tool_safety_tiers__mutmut_2'] = x__check_missing_tool_safety_tiers__mutmut_2 # type: ignore # mutmut generated
mutants_x__check_missing_tool_safety_tiers__mutmut['x__check_missing_tool_safety_tiers__mutmut_3'] = x__check_missing_tool_safety_tiers__mutmut_3 # type: ignore # mutmut generated
mutants_x__check_missing_tool_safety_tiers__mutmut['x__check_missing_tool_safety_tiers__mutmut_4'] = x__check_missing_tool_safety_tiers__mutmut_4 # type: ignore # mutmut generated
mutants_x__check_missing_tool_safety_tiers__mutmut['x__check_missing_tool_safety_tiers__mutmut_5'] = x__check_missing_tool_safety_tiers__mutmut_5 # type: ignore # mutmut generated
mutants_x__check_missing_tool_safety_tiers__mutmut['x__check_missing_tool_safety_tiers__mutmut_6'] = x__check_missing_tool_safety_tiers__mutmut_6 # type: ignore # mutmut generated
mutants_x__check_unknown_tool_safety_tiers__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x__check_unknown_tool_safety_tiers__mutmut)
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


def x__check_unknown_tool_safety_tiers__mutmut_orig(
    tool_safety_tiers: Mapping[str, object],
    known_tools: set[str] | None = None,
) -> list[str]:
    """Return tool_safety_tiers keys that are not registered tool names."""
    resolved_tools = _resolve_known_tools(known_tools)
    if resolved_tools is None:
        return []
    unknown = sorted(set(tool_safety_tiers) - resolved_tools)
    return [f"'{k}' not a registered tool name" for k in unknown]


def x__check_unknown_tool_safety_tiers__mutmut_1(
    tool_safety_tiers: Mapping[str, object],
    known_tools: set[str] | None = None,
) -> list[str]:
    """Return tool_safety_tiers keys that are not registered tool names."""
    resolved_tools = None
    if resolved_tools is None:
        return []
    unknown = sorted(set(tool_safety_tiers) - resolved_tools)
    return [f"'{k}' not a registered tool name" for k in unknown]


def x__check_unknown_tool_safety_tiers__mutmut_2(
    tool_safety_tiers: Mapping[str, object],
    known_tools: set[str] | None = None,
) -> list[str]:
    """Return tool_safety_tiers keys that are not registered tool names."""
    resolved_tools = _resolve_known_tools(None)
    if resolved_tools is None:
        return []
    unknown = sorted(set(tool_safety_tiers) - resolved_tools)
    return [f"'{k}' not a registered tool name" for k in unknown]


def x__check_unknown_tool_safety_tiers__mutmut_3(
    tool_safety_tiers: Mapping[str, object],
    known_tools: set[str] | None = None,
) -> list[str]:
    """Return tool_safety_tiers keys that are not registered tool names."""
    resolved_tools = _resolve_known_tools(known_tools)
    if resolved_tools is not None:
        return []
    unknown = sorted(set(tool_safety_tiers) - resolved_tools)
    return [f"'{k}' not a registered tool name" for k in unknown]


def x__check_unknown_tool_safety_tiers__mutmut_4(
    tool_safety_tiers: Mapping[str, object],
    known_tools: set[str] | None = None,
) -> list[str]:
    """Return tool_safety_tiers keys that are not registered tool names."""
    resolved_tools = _resolve_known_tools(known_tools)
    if resolved_tools is None:
        return []
    unknown = None
    return [f"'{k}' not a registered tool name" for k in unknown]


def x__check_unknown_tool_safety_tiers__mutmut_5(
    tool_safety_tiers: Mapping[str, object],
    known_tools: set[str] | None = None,
) -> list[str]:
    """Return tool_safety_tiers keys that are not registered tool names."""
    resolved_tools = _resolve_known_tools(known_tools)
    if resolved_tools is None:
        return []
    unknown = sorted(None)
    return [f"'{k}' not a registered tool name" for k in unknown]


def x__check_unknown_tool_safety_tiers__mutmut_6(
    tool_safety_tiers: Mapping[str, object],
    known_tools: set[str] | None = None,
) -> list[str]:
    """Return tool_safety_tiers keys that are not registered tool names."""
    resolved_tools = _resolve_known_tools(known_tools)
    if resolved_tools is None:
        return []
    unknown = sorted(set(tool_safety_tiers) + resolved_tools)
    return [f"'{k}' not a registered tool name" for k in unknown]


def x__check_unknown_tool_safety_tiers__mutmut_7(
    tool_safety_tiers: Mapping[str, object],
    known_tools: set[str] | None = None,
) -> list[str]:
    """Return tool_safety_tiers keys that are not registered tool names."""
    resolved_tools = _resolve_known_tools(known_tools)
    if resolved_tools is None:
        return []
    unknown = sorted(set(None) - resolved_tools)
    return [f"'{k}' not a registered tool name" for k in unknown]

mutants_x__check_unknown_tool_safety_tiers__mutmut['_mutmut_orig'] = x__check_unknown_tool_safety_tiers__mutmut_orig # type: ignore # mutmut generated
mutants_x__check_unknown_tool_safety_tiers__mutmut['x__check_unknown_tool_safety_tiers__mutmut_1'] = x__check_unknown_tool_safety_tiers__mutmut_1 # type: ignore # mutmut generated
mutants_x__check_unknown_tool_safety_tiers__mutmut['x__check_unknown_tool_safety_tiers__mutmut_2'] = x__check_unknown_tool_safety_tiers__mutmut_2 # type: ignore # mutmut generated
mutants_x__check_unknown_tool_safety_tiers__mutmut['x__check_unknown_tool_safety_tiers__mutmut_3'] = x__check_unknown_tool_safety_tiers__mutmut_3 # type: ignore # mutmut generated
mutants_x__check_unknown_tool_safety_tiers__mutmut['x__check_unknown_tool_safety_tiers__mutmut_4'] = x__check_unknown_tool_safety_tiers__mutmut_4 # type: ignore # mutmut generated
mutants_x__check_unknown_tool_safety_tiers__mutmut['x__check_unknown_tool_safety_tiers__mutmut_5'] = x__check_unknown_tool_safety_tiers__mutmut_5 # type: ignore # mutmut generated
mutants_x__check_unknown_tool_safety_tiers__mutmut['x__check_unknown_tool_safety_tiers__mutmut_6'] = x__check_unknown_tool_safety_tiers__mutmut_6 # type: ignore # mutmut generated
mutants_x__check_unknown_tool_safety_tiers__mutmut['x__check_unknown_tool_safety_tiers__mutmut_7'] = x__check_unknown_tool_safety_tiers__mutmut_7 # type: ignore # mutmut generated
mutants_xǁProductionConfigValidatorǁvalidate__mutmut: MutantDict = {}  # type: ignore
mutants_xǁProductionConfigValidatorǁvalidate_unknown_tool_safety_tiers__mutmut: MutantDict = {}  # type: ignore
mutants_xǁProductionConfigValidatorǁ_record__mutmut: MutantDict = {}  # type: ignore
mutants_xǁProductionConfigValidatorǁ_format_error_or_warning__mutmut: MutantDict = {}  # type: ignore


class ProductionConfigValidator:
    """Validate configuration against production security requirements.

    Checks strict mode flags, tool safety tier consistency, and other
    production-critical settings.
    """

    @_mutmut_mutated(mutants_xǁProductionConfigValidatorǁvalidate__mutmut)
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

        # allowed_tools visibility
        allowed_tools = config.get("allowed_tools")
        if isinstance(allowed_tools, (list, tuple)) and len(allowed_tools) == 0:
            msg = "allowed_tools=[] (all tools allowed; use allowlist to restrict)"
            self._record(errors, warnings, msg, is_production)

        return ConfigValidationResult(errors=errors, warnings=warnings)

    def xǁProductionConfigValidatorǁvalidate__mutmut_orig(
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

        # allowed_tools visibility
        allowed_tools = config.get("allowed_tools")
        if isinstance(allowed_tools, (list, tuple)) and len(allowed_tools) == 0:
            msg = "allowed_tools=[] (all tools allowed; use allowlist to restrict)"
            self._record(errors, warnings, msg, is_production)

        return ConfigValidationResult(errors=errors, warnings=warnings)

    def xǁProductionConfigValidatorǁvalidate__mutmut_1(
        self,
        config: Mapping[str, object],
        security_profile: SecurityProfile | str = "XXlocalXX",
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

        # allowed_tools visibility
        allowed_tools = config.get("allowed_tools")
        if isinstance(allowed_tools, (list, tuple)) and len(allowed_tools) == 0:
            msg = "allowed_tools=[] (all tools allowed; use allowlist to restrict)"
            self._record(errors, warnings, msg, is_production)

        return ConfigValidationResult(errors=errors, warnings=warnings)

    def xǁProductionConfigValidatorǁvalidate__mutmut_2(
        self,
        config: Mapping[str, object],
        security_profile: SecurityProfile | str = "LOCAL",
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

        # allowed_tools visibility
        allowed_tools = config.get("allowed_tools")
        if isinstance(allowed_tools, (list, tuple)) and len(allowed_tools) == 0:
            msg = "allowed_tools=[] (all tools allowed; use allowlist to restrict)"
            self._record(errors, warnings, msg, is_production)

        return ConfigValidationResult(errors=errors, warnings=warnings)

    def xǁProductionConfigValidatorǁvalidate__mutmut_3(
        self,
        config: Mapping[str, object],
        security_profile: SecurityProfile | str = "local",
        known_tools: set[str] | None = None,
    ) -> ConfigValidationResult:
        """Validate the full configuration against security profile rules."""
        errors: list[str] = None
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

        # allowed_tools visibility
        allowed_tools = config.get("allowed_tools")
        if isinstance(allowed_tools, (list, tuple)) and len(allowed_tools) == 0:
            msg = "allowed_tools=[] (all tools allowed; use allowlist to restrict)"
            self._record(errors, warnings, msg, is_production)

        return ConfigValidationResult(errors=errors, warnings=warnings)

    def xǁProductionConfigValidatorǁvalidate__mutmut_4(
        self,
        config: Mapping[str, object],
        security_profile: SecurityProfile | str = "local",
        known_tools: set[str] | None = None,
    ) -> ConfigValidationResult:
        """Validate the full configuration against security profile rules."""
        errors: list[str] = []
        warnings: list[str] = None

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

        # allowed_tools visibility
        allowed_tools = config.get("allowed_tools")
        if isinstance(allowed_tools, (list, tuple)) and len(allowed_tools) == 0:
            msg = "allowed_tools=[] (all tools allowed; use allowlist to restrict)"
            self._record(errors, warnings, msg, is_production)

        return ConfigValidationResult(errors=errors, warnings=warnings)

    def xǁProductionConfigValidatorǁvalidate__mutmut_5(
        self,
        config: Mapping[str, object],
        security_profile: SecurityProfile | str = "local",
        known_tools: set[str] | None = None,
    ) -> ConfigValidationResult:
        """Validate the full configuration against security profile rules."""
        errors: list[str] = []
        warnings: list[str] = []

        is_production = None

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

        # allowed_tools visibility
        allowed_tools = config.get("allowed_tools")
        if isinstance(allowed_tools, (list, tuple)) and len(allowed_tools) == 0:
            msg = "allowed_tools=[] (all tools allowed; use allowlist to restrict)"
            self._record(errors, warnings, msg, is_production)

        return ConfigValidationResult(errors=errors, warnings=warnings)

    def xǁProductionConfigValidatorǁvalidate__mutmut_6(
        self,
        config: Mapping[str, object],
        security_profile: SecurityProfile | str = "local",
        known_tools: set[str] | None = None,
    ) -> ConfigValidationResult:
        """Validate the full configuration against security profile rules."""
        errors: list[str] = []
        warnings: list[str] = []

        is_production = security_profile != "production"

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

        # allowed_tools visibility
        allowed_tools = config.get("allowed_tools")
        if isinstance(allowed_tools, (list, tuple)) and len(allowed_tools) == 0:
            msg = "allowed_tools=[] (all tools allowed; use allowlist to restrict)"
            self._record(errors, warnings, msg, is_production)

        return ConfigValidationResult(errors=errors, warnings=warnings)

    def xǁProductionConfigValidatorǁvalidate__mutmut_7(
        self,
        config: Mapping[str, object],
        security_profile: SecurityProfile | str = "local",
        known_tools: set[str] | None = None,
    ) -> ConfigValidationResult:
        """Validate the full configuration against security profile rules."""
        errors: list[str] = []
        warnings: list[str] = []

        is_production = security_profile == "XXproductionXX"

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

        # allowed_tools visibility
        allowed_tools = config.get("allowed_tools")
        if isinstance(allowed_tools, (list, tuple)) and len(allowed_tools) == 0:
            msg = "allowed_tools=[] (all tools allowed; use allowlist to restrict)"
            self._record(errors, warnings, msg, is_production)

        return ConfigValidationResult(errors=errors, warnings=warnings)

    def xǁProductionConfigValidatorǁvalidate__mutmut_8(
        self,
        config: Mapping[str, object],
        security_profile: SecurityProfile | str = "local",
        known_tools: set[str] | None = None,
    ) -> ConfigValidationResult:
        """Validate the full configuration against security profile rules."""
        errors: list[str] = []
        warnings: list[str] = []

        is_production = security_profile == "PRODUCTION"

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

        # allowed_tools visibility
        allowed_tools = config.get("allowed_tools")
        if isinstance(allowed_tools, (list, tuple)) and len(allowed_tools) == 0:
            msg = "allowed_tools=[] (all tools allowed; use allowlist to restrict)"
            self._record(errors, warnings, msg, is_production)

        return ConfigValidationResult(errors=errors, warnings=warnings)

    def xǁProductionConfigValidatorǁvalidate__mutmut_9(
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
            if config.get(key, False):
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

        # allowed_tools visibility
        allowed_tools = config.get("allowed_tools")
        if isinstance(allowed_tools, (list, tuple)) and len(allowed_tools) == 0:
            msg = "allowed_tools=[] (all tools allowed; use allowlist to restrict)"
            self._record(errors, warnings, msg, is_production)

        return ConfigValidationResult(errors=errors, warnings=warnings)

    def xǁProductionConfigValidatorǁvalidate__mutmut_10(
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
            if not config.get(None, False):
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

        # allowed_tools visibility
        allowed_tools = config.get("allowed_tools")
        if isinstance(allowed_tools, (list, tuple)) and len(allowed_tools) == 0:
            msg = "allowed_tools=[] (all tools allowed; use allowlist to restrict)"
            self._record(errors, warnings, msg, is_production)

        return ConfigValidationResult(errors=errors, warnings=warnings)

    def xǁProductionConfigValidatorǁvalidate__mutmut_11(
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
            if not config.get(key, None):
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

        # allowed_tools visibility
        allowed_tools = config.get("allowed_tools")
        if isinstance(allowed_tools, (list, tuple)) and len(allowed_tools) == 0:
            msg = "allowed_tools=[] (all tools allowed; use allowlist to restrict)"
            self._record(errors, warnings, msg, is_production)

        return ConfigValidationResult(errors=errors, warnings=warnings)

    def xǁProductionConfigValidatorǁvalidate__mutmut_12(
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
            if not config.get(False):
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

        # allowed_tools visibility
        allowed_tools = config.get("allowed_tools")
        if isinstance(allowed_tools, (list, tuple)) and len(allowed_tools) == 0:
            msg = "allowed_tools=[] (all tools allowed; use allowlist to restrict)"
            self._record(errors, warnings, msg, is_production)

        return ConfigValidationResult(errors=errors, warnings=warnings)

    def xǁProductionConfigValidatorǁvalidate__mutmut_13(
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
            if not config.get(key, ):
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

        # allowed_tools visibility
        allowed_tools = config.get("allowed_tools")
        if isinstance(allowed_tools, (list, tuple)) and len(allowed_tools) == 0:
            msg = "allowed_tools=[] (all tools allowed; use allowlist to restrict)"
            self._record(errors, warnings, msg, is_production)

        return ConfigValidationResult(errors=errors, warnings=warnings)

    def xǁProductionConfigValidatorǁvalidate__mutmut_14(
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
            if not config.get(key, True):
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

        # allowed_tools visibility
        allowed_tools = config.get("allowed_tools")
        if isinstance(allowed_tools, (list, tuple)) and len(allowed_tools) == 0:
            msg = "allowed_tools=[] (all tools allowed; use allowlist to restrict)"
            self._record(errors, warnings, msg, is_production)

        return ConfigValidationResult(errors=errors, warnings=warnings)

    def xǁProductionConfigValidatorǁvalidate__mutmut_15(
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
                msg = None
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

        # allowed_tools visibility
        allowed_tools = config.get("allowed_tools")
        if isinstance(allowed_tools, (list, tuple)) and len(allowed_tools) == 0:
            msg = "allowed_tools=[] (all tools allowed; use allowlist to restrict)"
            self._record(errors, warnings, msg, is_production)

        return ConfigValidationResult(errors=errors, warnings=warnings)

    def xǁProductionConfigValidatorǁvalidate__mutmut_16(
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
                self._record(None, warnings, msg, is_production)

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

        # allowed_tools visibility
        allowed_tools = config.get("allowed_tools")
        if isinstance(allowed_tools, (list, tuple)) and len(allowed_tools) == 0:
            msg = "allowed_tools=[] (all tools allowed; use allowlist to restrict)"
            self._record(errors, warnings, msg, is_production)

        return ConfigValidationResult(errors=errors, warnings=warnings)

    def xǁProductionConfigValidatorǁvalidate__mutmut_17(
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
                self._record(errors, None, msg, is_production)

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

        # allowed_tools visibility
        allowed_tools = config.get("allowed_tools")
        if isinstance(allowed_tools, (list, tuple)) and len(allowed_tools) == 0:
            msg = "allowed_tools=[] (all tools allowed; use allowlist to restrict)"
            self._record(errors, warnings, msg, is_production)

        return ConfigValidationResult(errors=errors, warnings=warnings)

    def xǁProductionConfigValidatorǁvalidate__mutmut_18(
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
                self._record(errors, warnings, None, is_production)

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

        # allowed_tools visibility
        allowed_tools = config.get("allowed_tools")
        if isinstance(allowed_tools, (list, tuple)) and len(allowed_tools) == 0:
            msg = "allowed_tools=[] (all tools allowed; use allowlist to restrict)"
            self._record(errors, warnings, msg, is_production)

        return ConfigValidationResult(errors=errors, warnings=warnings)

    def xǁProductionConfigValidatorǁvalidate__mutmut_19(
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
                self._record(errors, warnings, msg, None)

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

        # allowed_tools visibility
        allowed_tools = config.get("allowed_tools")
        if isinstance(allowed_tools, (list, tuple)) and len(allowed_tools) == 0:
            msg = "allowed_tools=[] (all tools allowed; use allowlist to restrict)"
            self._record(errors, warnings, msg, is_production)

        return ConfigValidationResult(errors=errors, warnings=warnings)

    def xǁProductionConfigValidatorǁvalidate__mutmut_20(
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
                self._record(warnings, msg, is_production)

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

        # allowed_tools visibility
        allowed_tools = config.get("allowed_tools")
        if isinstance(allowed_tools, (list, tuple)) and len(allowed_tools) == 0:
            msg = "allowed_tools=[] (all tools allowed; use allowlist to restrict)"
            self._record(errors, warnings, msg, is_production)

        return ConfigValidationResult(errors=errors, warnings=warnings)

    def xǁProductionConfigValidatorǁvalidate__mutmut_21(
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
                self._record(errors, msg, is_production)

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

        # allowed_tools visibility
        allowed_tools = config.get("allowed_tools")
        if isinstance(allowed_tools, (list, tuple)) and len(allowed_tools) == 0:
            msg = "allowed_tools=[] (all tools allowed; use allowlist to restrict)"
            self._record(errors, warnings, msg, is_production)

        return ConfigValidationResult(errors=errors, warnings=warnings)

    def xǁProductionConfigValidatorǁvalidate__mutmut_22(
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
                self._record(errors, warnings, is_production)

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

        # allowed_tools visibility
        allowed_tools = config.get("allowed_tools")
        if isinstance(allowed_tools, (list, tuple)) and len(allowed_tools) == 0:
            msg = "allowed_tools=[] (all tools allowed; use allowlist to restrict)"
            self._record(errors, warnings, msg, is_production)

        return ConfigValidationResult(errors=errors, warnings=warnings)

    def xǁProductionConfigValidatorǁvalidate__mutmut_23(
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
                self._record(errors, warnings, msg, )

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

        # allowed_tools visibility
        allowed_tools = config.get("allowed_tools")
        if isinstance(allowed_tools, (list, tuple)) and len(allowed_tools) == 0:
            msg = "allowed_tools=[] (all tools allowed; use allowlist to restrict)"
            self._record(errors, warnings, msg, is_production)

        return ConfigValidationResult(errors=errors, warnings=warnings)

    def xǁProductionConfigValidatorǁvalidate__mutmut_24(
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
            if config.get(None) is False:
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

        # allowed_tools visibility
        allowed_tools = config.get("allowed_tools")
        if isinstance(allowed_tools, (list, tuple)) and len(allowed_tools) == 0:
            msg = "allowed_tools=[] (all tools allowed; use allowlist to restrict)"
            self._record(errors, warnings, msg, is_production)

        return ConfigValidationResult(errors=errors, warnings=warnings)

    def xǁProductionConfigValidatorǁvalidate__mutmut_25(
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
            if config.get(key) is not False:
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

        # allowed_tools visibility
        allowed_tools = config.get("allowed_tools")
        if isinstance(allowed_tools, (list, tuple)) and len(allowed_tools) == 0:
            msg = "allowed_tools=[] (all tools allowed; use allowlist to restrict)"
            self._record(errors, warnings, msg, is_production)

        return ConfigValidationResult(errors=errors, warnings=warnings)

    def xǁProductionConfigValidatorǁvalidate__mutmut_26(
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
            if config.get(key) is True:
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

        # allowed_tools visibility
        allowed_tools = config.get("allowed_tools")
        if isinstance(allowed_tools, (list, tuple)) and len(allowed_tools) == 0:
            msg = "allowed_tools=[] (all tools allowed; use allowlist to restrict)"
            self._record(errors, warnings, msg, is_production)

        return ConfigValidationResult(errors=errors, warnings=warnings)

    def xǁProductionConfigValidatorǁvalidate__mutmut_27(
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
                msg = None
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

        # allowed_tools visibility
        allowed_tools = config.get("allowed_tools")
        if isinstance(allowed_tools, (list, tuple)) and len(allowed_tools) == 0:
            msg = "allowed_tools=[] (all tools allowed; use allowlist to restrict)"
            self._record(errors, warnings, msg, is_production)

        return ConfigValidationResult(errors=errors, warnings=warnings)

    def xǁProductionConfigValidatorǁvalidate__mutmut_28(
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
                self._record(None, warnings, msg, is_production)

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

        # allowed_tools visibility
        allowed_tools = config.get("allowed_tools")
        if isinstance(allowed_tools, (list, tuple)) and len(allowed_tools) == 0:
            msg = "allowed_tools=[] (all tools allowed; use allowlist to restrict)"
            self._record(errors, warnings, msg, is_production)

        return ConfigValidationResult(errors=errors, warnings=warnings)

    def xǁProductionConfigValidatorǁvalidate__mutmut_29(
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
                self._record(errors, None, msg, is_production)

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

        # allowed_tools visibility
        allowed_tools = config.get("allowed_tools")
        if isinstance(allowed_tools, (list, tuple)) and len(allowed_tools) == 0:
            msg = "allowed_tools=[] (all tools allowed; use allowlist to restrict)"
            self._record(errors, warnings, msg, is_production)

        return ConfigValidationResult(errors=errors, warnings=warnings)

    def xǁProductionConfigValidatorǁvalidate__mutmut_30(
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
                self._record(errors, warnings, None, is_production)

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

        # allowed_tools visibility
        allowed_tools = config.get("allowed_tools")
        if isinstance(allowed_tools, (list, tuple)) and len(allowed_tools) == 0:
            msg = "allowed_tools=[] (all tools allowed; use allowlist to restrict)"
            self._record(errors, warnings, msg, is_production)

        return ConfigValidationResult(errors=errors, warnings=warnings)

    def xǁProductionConfigValidatorǁvalidate__mutmut_31(
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
                self._record(errors, warnings, msg, None)

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

        # allowed_tools visibility
        allowed_tools = config.get("allowed_tools")
        if isinstance(allowed_tools, (list, tuple)) and len(allowed_tools) == 0:
            msg = "allowed_tools=[] (all tools allowed; use allowlist to restrict)"
            self._record(errors, warnings, msg, is_production)

        return ConfigValidationResult(errors=errors, warnings=warnings)

    def xǁProductionConfigValidatorǁvalidate__mutmut_32(
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
                self._record(warnings, msg, is_production)

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

        # allowed_tools visibility
        allowed_tools = config.get("allowed_tools")
        if isinstance(allowed_tools, (list, tuple)) and len(allowed_tools) == 0:
            msg = "allowed_tools=[] (all tools allowed; use allowlist to restrict)"
            self._record(errors, warnings, msg, is_production)

        return ConfigValidationResult(errors=errors, warnings=warnings)

    def xǁProductionConfigValidatorǁvalidate__mutmut_33(
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
                self._record(errors, msg, is_production)

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

        # allowed_tools visibility
        allowed_tools = config.get("allowed_tools")
        if isinstance(allowed_tools, (list, tuple)) and len(allowed_tools) == 0:
            msg = "allowed_tools=[] (all tools allowed; use allowlist to restrict)"
            self._record(errors, warnings, msg, is_production)

        return ConfigValidationResult(errors=errors, warnings=warnings)

    def xǁProductionConfigValidatorǁvalidate__mutmut_34(
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
                self._record(errors, warnings, is_production)

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

        # allowed_tools visibility
        allowed_tools = config.get("allowed_tools")
        if isinstance(allowed_tools, (list, tuple)) and len(allowed_tools) == 0:
            msg = "allowed_tools=[] (all tools allowed; use allowlist to restrict)"
            self._record(errors, warnings, msg, is_production)

        return ConfigValidationResult(errors=errors, warnings=warnings)

    def xǁProductionConfigValidatorǁvalidate__mutmut_35(
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
                self._record(errors, warnings, msg, )

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

        # allowed_tools visibility
        allowed_tools = config.get("allowed_tools")
        if isinstance(allowed_tools, (list, tuple)) and len(allowed_tools) == 0:
            msg = "allowed_tools=[] (all tools allowed; use allowlist to restrict)"
            self._record(errors, warnings, msg, is_production)

        return ConfigValidationResult(errors=errors, warnings=warnings)

    def xǁProductionConfigValidatorǁvalidate__mutmut_36(
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
        raw_tiers = None
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

        # allowed_tools visibility
        allowed_tools = config.get("allowed_tools")
        if isinstance(allowed_tools, (list, tuple)) and len(allowed_tools) == 0:
            msg = "allowed_tools=[] (all tools allowed; use allowlist to restrict)"
            self._record(errors, warnings, msg, is_production)

        return ConfigValidationResult(errors=errors, warnings=warnings)

    def xǁProductionConfigValidatorǁvalidate__mutmut_37(
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
        raw_tiers = config.get(None)
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

        # allowed_tools visibility
        allowed_tools = config.get("allowed_tools")
        if isinstance(allowed_tools, (list, tuple)) and len(allowed_tools) == 0:
            msg = "allowed_tools=[] (all tools allowed; use allowlist to restrict)"
            self._record(errors, warnings, msg, is_production)

        return ConfigValidationResult(errors=errors, warnings=warnings)

    def xǁProductionConfigValidatorǁvalidate__mutmut_38(
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
        raw_tiers = config.get("XXtool_safety_tiersXX")
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

        # allowed_tools visibility
        allowed_tools = config.get("allowed_tools")
        if isinstance(allowed_tools, (list, tuple)) and len(allowed_tools) == 0:
            msg = "allowed_tools=[] (all tools allowed; use allowlist to restrict)"
            self._record(errors, warnings, msg, is_production)

        return ConfigValidationResult(errors=errors, warnings=warnings)

    def xǁProductionConfigValidatorǁvalidate__mutmut_39(
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
        raw_tiers = config.get("TOOL_SAFETY_TIERS")
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

        # allowed_tools visibility
        allowed_tools = config.get("allowed_tools")
        if isinstance(allowed_tools, (list, tuple)) and len(allowed_tools) == 0:
            msg = "allowed_tools=[] (all tools allowed; use allowlist to restrict)"
            self._record(errors, warnings, msg, is_production)

        return ConfigValidationResult(errors=errors, warnings=warnings)

    def xǁProductionConfigValidatorǁvalidate__mutmut_40(
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
        tool_safety_tiers: Mapping[str, object] = None
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

        # allowed_tools visibility
        allowed_tools = config.get("allowed_tools")
        if isinstance(allowed_tools, (list, tuple)) and len(allowed_tools) == 0:
            msg = "allowed_tools=[] (all tools allowed; use allowlist to restrict)"
            self._record(errors, warnings, msg, is_production)

        return ConfigValidationResult(errors=errors, warnings=warnings)

    def xǁProductionConfigValidatorǁvalidate__mutmut_41(
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
            missing_tiers = None
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

        # allowed_tools visibility
        allowed_tools = config.get("allowed_tools")
        if isinstance(allowed_tools, (list, tuple)) and len(allowed_tools) == 0:
            msg = "allowed_tools=[] (all tools allowed; use allowlist to restrict)"
            self._record(errors, warnings, msg, is_production)

        return ConfigValidationResult(errors=errors, warnings=warnings)

    def xǁProductionConfigValidatorǁvalidate__mutmut_42(
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
                None, known_tools=known_tools
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

        # allowed_tools visibility
        allowed_tools = config.get("allowed_tools")
        if isinstance(allowed_tools, (list, tuple)) and len(allowed_tools) == 0:
            msg = "allowed_tools=[] (all tools allowed; use allowlist to restrict)"
            self._record(errors, warnings, msg, is_production)

        return ConfigValidationResult(errors=errors, warnings=warnings)

    def xǁProductionConfigValidatorǁvalidate__mutmut_43(
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
                tool_safety_tiers, known_tools=None
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

        # allowed_tools visibility
        allowed_tools = config.get("allowed_tools")
        if isinstance(allowed_tools, (list, tuple)) and len(allowed_tools) == 0:
            msg = "allowed_tools=[] (all tools allowed; use allowlist to restrict)"
            self._record(errors, warnings, msg, is_production)

        return ConfigValidationResult(errors=errors, warnings=warnings)

    def xǁProductionConfigValidatorǁvalidate__mutmut_44(
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
                known_tools=known_tools
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

        # allowed_tools visibility
        allowed_tools = config.get("allowed_tools")
        if isinstance(allowed_tools, (list, tuple)) and len(allowed_tools) == 0:
            msg = "allowed_tools=[] (all tools allowed; use allowlist to restrict)"
            self._record(errors, warnings, msg, is_production)

        return ConfigValidationResult(errors=errors, warnings=warnings)

    def xǁProductionConfigValidatorǁvalidate__mutmut_45(
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
                tool_safety_tiers, )
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

        # allowed_tools visibility
        allowed_tools = config.get("allowed_tools")
        if isinstance(allowed_tools, (list, tuple)) and len(allowed_tools) == 0:
            msg = "allowed_tools=[] (all tools allowed; use allowlist to restrict)"
            self._record(errors, warnings, msg, is_production)

        return ConfigValidationResult(errors=errors, warnings=warnings)

    def xǁProductionConfigValidatorǁvalidate__mutmut_46(
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
                tier_msg = None
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

        # allowed_tools visibility
        allowed_tools = config.get("allowed_tools")
        if isinstance(allowed_tools, (list, tuple)) and len(allowed_tools) == 0:
            msg = "allowed_tools=[] (all tools allowed; use allowlist to restrict)"
            self._record(errors, warnings, msg, is_production)

        return ConfigValidationResult(errors=errors, warnings=warnings)

    def xǁProductionConfigValidatorǁvalidate__mutmut_47(
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
                tier_msg = "; ".join(None)
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

        # allowed_tools visibility
        allowed_tools = config.get("allowed_tools")
        if isinstance(allowed_tools, (list, tuple)) and len(allowed_tools) == 0:
            msg = "allowed_tools=[] (all tools allowed; use allowlist to restrict)"
            self._record(errors, warnings, msg, is_production)

        return ConfigValidationResult(errors=errors, warnings=warnings)

    def xǁProductionConfigValidatorǁvalidate__mutmut_48(
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
                tier_msg = "XX; XX".join(missing_tiers)
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

        # allowed_tools visibility
        allowed_tools = config.get("allowed_tools")
        if isinstance(allowed_tools, (list, tuple)) and len(allowed_tools) == 0:
            msg = "allowed_tools=[] (all tools allowed; use allowlist to restrict)"
            self._record(errors, warnings, msg, is_production)

        return ConfigValidationResult(errors=errors, warnings=warnings)

    def xǁProductionConfigValidatorǁvalidate__mutmut_49(
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
                    None, warnings, f"Missing safety tiers: {tier_msg}", is_production
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

        # allowed_tools visibility
        allowed_tools = config.get("allowed_tools")
        if isinstance(allowed_tools, (list, tuple)) and len(allowed_tools) == 0:
            msg = "allowed_tools=[] (all tools allowed; use allowlist to restrict)"
            self._record(errors, warnings, msg, is_production)

        return ConfigValidationResult(errors=errors, warnings=warnings)

    def xǁProductionConfigValidatorǁvalidate__mutmut_50(
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
                    errors, None, f"Missing safety tiers: {tier_msg}", is_production
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

        # allowed_tools visibility
        allowed_tools = config.get("allowed_tools")
        if isinstance(allowed_tools, (list, tuple)) and len(allowed_tools) == 0:
            msg = "allowed_tools=[] (all tools allowed; use allowlist to restrict)"
            self._record(errors, warnings, msg, is_production)

        return ConfigValidationResult(errors=errors, warnings=warnings)

    def xǁProductionConfigValidatorǁvalidate__mutmut_51(
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
                    errors, warnings, None, is_production
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

        # allowed_tools visibility
        allowed_tools = config.get("allowed_tools")
        if isinstance(allowed_tools, (list, tuple)) and len(allowed_tools) == 0:
            msg = "allowed_tools=[] (all tools allowed; use allowlist to restrict)"
            self._record(errors, warnings, msg, is_production)

        return ConfigValidationResult(errors=errors, warnings=warnings)

    def xǁProductionConfigValidatorǁvalidate__mutmut_52(
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
                    errors, warnings, f"Missing safety tiers: {tier_msg}", None
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

        # allowed_tools visibility
        allowed_tools = config.get("allowed_tools")
        if isinstance(allowed_tools, (list, tuple)) and len(allowed_tools) == 0:
            msg = "allowed_tools=[] (all tools allowed; use allowlist to restrict)"
            self._record(errors, warnings, msg, is_production)

        return ConfigValidationResult(errors=errors, warnings=warnings)

    def xǁProductionConfigValidatorǁvalidate__mutmut_53(
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
                    warnings, f"Missing safety tiers: {tier_msg}", is_production
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

        # allowed_tools visibility
        allowed_tools = config.get("allowed_tools")
        if isinstance(allowed_tools, (list, tuple)) and len(allowed_tools) == 0:
            msg = "allowed_tools=[] (all tools allowed; use allowlist to restrict)"
            self._record(errors, warnings, msg, is_production)

        return ConfigValidationResult(errors=errors, warnings=warnings)

    def xǁProductionConfigValidatorǁvalidate__mutmut_54(
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
                    errors, f"Missing safety tiers: {tier_msg}", is_production
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

        # allowed_tools visibility
        allowed_tools = config.get("allowed_tools")
        if isinstance(allowed_tools, (list, tuple)) and len(allowed_tools) == 0:
            msg = "allowed_tools=[] (all tools allowed; use allowlist to restrict)"
            self._record(errors, warnings, msg, is_production)

        return ConfigValidationResult(errors=errors, warnings=warnings)

    def xǁProductionConfigValidatorǁvalidate__mutmut_55(
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
                    errors, warnings, is_production
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

        # allowed_tools visibility
        allowed_tools = config.get("allowed_tools")
        if isinstance(allowed_tools, (list, tuple)) and len(allowed_tools) == 0:
            msg = "allowed_tools=[] (all tools allowed; use allowlist to restrict)"
            self._record(errors, warnings, msg, is_production)

        return ConfigValidationResult(errors=errors, warnings=warnings)

    def xǁProductionConfigValidatorǁvalidate__mutmut_56(
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
                    errors, warnings, f"Missing safety tiers: {tier_msg}", )

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

        # allowed_tools visibility
        allowed_tools = config.get("allowed_tools")
        if isinstance(allowed_tools, (list, tuple)) and len(allowed_tools) == 0:
            msg = "allowed_tools=[] (all tools allowed; use allowlist to restrict)"
            self._record(errors, warnings, msg, is_production)

        return ConfigValidationResult(errors=errors, warnings=warnings)

    def xǁProductionConfigValidatorǁvalidate__mutmut_57(
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

            unknown_tiers = None
            if unknown_tiers:
                tier_msg = "; ".join(unknown_tiers)
                self._record(
                    errors,
                    warnings,
                    f"Unknown safety tier keys: {tier_msg}",
                    is_production,
                )

        # allowed_tools visibility
        allowed_tools = config.get("allowed_tools")
        if isinstance(allowed_tools, (list, tuple)) and len(allowed_tools) == 0:
            msg = "allowed_tools=[] (all tools allowed; use allowlist to restrict)"
            self._record(errors, warnings, msg, is_production)

        return ConfigValidationResult(errors=errors, warnings=warnings)

    def xǁProductionConfigValidatorǁvalidate__mutmut_58(
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
                None, known_tools=known_tools
            )
            if unknown_tiers:
                tier_msg = "; ".join(unknown_tiers)
                self._record(
                    errors,
                    warnings,
                    f"Unknown safety tier keys: {tier_msg}",
                    is_production,
                )

        # allowed_tools visibility
        allowed_tools = config.get("allowed_tools")
        if isinstance(allowed_tools, (list, tuple)) and len(allowed_tools) == 0:
            msg = "allowed_tools=[] (all tools allowed; use allowlist to restrict)"
            self._record(errors, warnings, msg, is_production)

        return ConfigValidationResult(errors=errors, warnings=warnings)

    def xǁProductionConfigValidatorǁvalidate__mutmut_59(
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
                tool_safety_tiers, known_tools=None
            )
            if unknown_tiers:
                tier_msg = "; ".join(unknown_tiers)
                self._record(
                    errors,
                    warnings,
                    f"Unknown safety tier keys: {tier_msg}",
                    is_production,
                )

        # allowed_tools visibility
        allowed_tools = config.get("allowed_tools")
        if isinstance(allowed_tools, (list, tuple)) and len(allowed_tools) == 0:
            msg = "allowed_tools=[] (all tools allowed; use allowlist to restrict)"
            self._record(errors, warnings, msg, is_production)

        return ConfigValidationResult(errors=errors, warnings=warnings)

    def xǁProductionConfigValidatorǁvalidate__mutmut_60(
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
                known_tools=known_tools
            )
            if unknown_tiers:
                tier_msg = "; ".join(unknown_tiers)
                self._record(
                    errors,
                    warnings,
                    f"Unknown safety tier keys: {tier_msg}",
                    is_production,
                )

        # allowed_tools visibility
        allowed_tools = config.get("allowed_tools")
        if isinstance(allowed_tools, (list, tuple)) and len(allowed_tools) == 0:
            msg = "allowed_tools=[] (all tools allowed; use allowlist to restrict)"
            self._record(errors, warnings, msg, is_production)

        return ConfigValidationResult(errors=errors, warnings=warnings)

    def xǁProductionConfigValidatorǁvalidate__mutmut_61(
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
                tool_safety_tiers, )
            if unknown_tiers:
                tier_msg = "; ".join(unknown_tiers)
                self._record(
                    errors,
                    warnings,
                    f"Unknown safety tier keys: {tier_msg}",
                    is_production,
                )

        # allowed_tools visibility
        allowed_tools = config.get("allowed_tools")
        if isinstance(allowed_tools, (list, tuple)) and len(allowed_tools) == 0:
            msg = "allowed_tools=[] (all tools allowed; use allowlist to restrict)"
            self._record(errors, warnings, msg, is_production)

        return ConfigValidationResult(errors=errors, warnings=warnings)

    def xǁProductionConfigValidatorǁvalidate__mutmut_62(
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
                tier_msg = None
                self._record(
                    errors,
                    warnings,
                    f"Unknown safety tier keys: {tier_msg}",
                    is_production,
                )

        # allowed_tools visibility
        allowed_tools = config.get("allowed_tools")
        if isinstance(allowed_tools, (list, tuple)) and len(allowed_tools) == 0:
            msg = "allowed_tools=[] (all tools allowed; use allowlist to restrict)"
            self._record(errors, warnings, msg, is_production)

        return ConfigValidationResult(errors=errors, warnings=warnings)

    def xǁProductionConfigValidatorǁvalidate__mutmut_63(
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
                tier_msg = "; ".join(None)
                self._record(
                    errors,
                    warnings,
                    f"Unknown safety tier keys: {tier_msg}",
                    is_production,
                )

        # allowed_tools visibility
        allowed_tools = config.get("allowed_tools")
        if isinstance(allowed_tools, (list, tuple)) and len(allowed_tools) == 0:
            msg = "allowed_tools=[] (all tools allowed; use allowlist to restrict)"
            self._record(errors, warnings, msg, is_production)

        return ConfigValidationResult(errors=errors, warnings=warnings)

    def xǁProductionConfigValidatorǁvalidate__mutmut_64(
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
                tier_msg = "XX; XX".join(unknown_tiers)
                self._record(
                    errors,
                    warnings,
                    f"Unknown safety tier keys: {tier_msg}",
                    is_production,
                )

        # allowed_tools visibility
        allowed_tools = config.get("allowed_tools")
        if isinstance(allowed_tools, (list, tuple)) and len(allowed_tools) == 0:
            msg = "allowed_tools=[] (all tools allowed; use allowlist to restrict)"
            self._record(errors, warnings, msg, is_production)

        return ConfigValidationResult(errors=errors, warnings=warnings)

    def xǁProductionConfigValidatorǁvalidate__mutmut_65(
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
                    None,
                    warnings,
                    f"Unknown safety tier keys: {tier_msg}",
                    is_production,
                )

        # allowed_tools visibility
        allowed_tools = config.get("allowed_tools")
        if isinstance(allowed_tools, (list, tuple)) and len(allowed_tools) == 0:
            msg = "allowed_tools=[] (all tools allowed; use allowlist to restrict)"
            self._record(errors, warnings, msg, is_production)

        return ConfigValidationResult(errors=errors, warnings=warnings)

    def xǁProductionConfigValidatorǁvalidate__mutmut_66(
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
                    None,
                    f"Unknown safety tier keys: {tier_msg}",
                    is_production,
                )

        # allowed_tools visibility
        allowed_tools = config.get("allowed_tools")
        if isinstance(allowed_tools, (list, tuple)) and len(allowed_tools) == 0:
            msg = "allowed_tools=[] (all tools allowed; use allowlist to restrict)"
            self._record(errors, warnings, msg, is_production)

        return ConfigValidationResult(errors=errors, warnings=warnings)

    def xǁProductionConfigValidatorǁvalidate__mutmut_67(
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
                    None,
                    is_production,
                )

        # allowed_tools visibility
        allowed_tools = config.get("allowed_tools")
        if isinstance(allowed_tools, (list, tuple)) and len(allowed_tools) == 0:
            msg = "allowed_tools=[] (all tools allowed; use allowlist to restrict)"
            self._record(errors, warnings, msg, is_production)

        return ConfigValidationResult(errors=errors, warnings=warnings)

    def xǁProductionConfigValidatorǁvalidate__mutmut_68(
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
                    None,
                )

        # allowed_tools visibility
        allowed_tools = config.get("allowed_tools")
        if isinstance(allowed_tools, (list, tuple)) and len(allowed_tools) == 0:
            msg = "allowed_tools=[] (all tools allowed; use allowlist to restrict)"
            self._record(errors, warnings, msg, is_production)

        return ConfigValidationResult(errors=errors, warnings=warnings)

    def xǁProductionConfigValidatorǁvalidate__mutmut_69(
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
                    warnings,
                    f"Unknown safety tier keys: {tier_msg}",
                    is_production,
                )

        # allowed_tools visibility
        allowed_tools = config.get("allowed_tools")
        if isinstance(allowed_tools, (list, tuple)) and len(allowed_tools) == 0:
            msg = "allowed_tools=[] (all tools allowed; use allowlist to restrict)"
            self._record(errors, warnings, msg, is_production)

        return ConfigValidationResult(errors=errors, warnings=warnings)

    def xǁProductionConfigValidatorǁvalidate__mutmut_70(
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
                    f"Unknown safety tier keys: {tier_msg}",
                    is_production,
                )

        # allowed_tools visibility
        allowed_tools = config.get("allowed_tools")
        if isinstance(allowed_tools, (list, tuple)) and len(allowed_tools) == 0:
            msg = "allowed_tools=[] (all tools allowed; use allowlist to restrict)"
            self._record(errors, warnings, msg, is_production)

        return ConfigValidationResult(errors=errors, warnings=warnings)

    def xǁProductionConfigValidatorǁvalidate__mutmut_71(
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
                    is_production,
                )

        # allowed_tools visibility
        allowed_tools = config.get("allowed_tools")
        if isinstance(allowed_tools, (list, tuple)) and len(allowed_tools) == 0:
            msg = "allowed_tools=[] (all tools allowed; use allowlist to restrict)"
            self._record(errors, warnings, msg, is_production)

        return ConfigValidationResult(errors=errors, warnings=warnings)

    def xǁProductionConfigValidatorǁvalidate__mutmut_72(
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
                    )

        # allowed_tools visibility
        allowed_tools = config.get("allowed_tools")
        if isinstance(allowed_tools, (list, tuple)) and len(allowed_tools) == 0:
            msg = "allowed_tools=[] (all tools allowed; use allowlist to restrict)"
            self._record(errors, warnings, msg, is_production)

        return ConfigValidationResult(errors=errors, warnings=warnings)

    def xǁProductionConfigValidatorǁvalidate__mutmut_73(
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

        # allowed_tools visibility
        allowed_tools = None
        if isinstance(allowed_tools, (list, tuple)) and len(allowed_tools) == 0:
            msg = "allowed_tools=[] (all tools allowed; use allowlist to restrict)"
            self._record(errors, warnings, msg, is_production)

        return ConfigValidationResult(errors=errors, warnings=warnings)

    def xǁProductionConfigValidatorǁvalidate__mutmut_74(
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

        # allowed_tools visibility
        allowed_tools = config.get(None)
        if isinstance(allowed_tools, (list, tuple)) and len(allowed_tools) == 0:
            msg = "allowed_tools=[] (all tools allowed; use allowlist to restrict)"
            self._record(errors, warnings, msg, is_production)

        return ConfigValidationResult(errors=errors, warnings=warnings)

    def xǁProductionConfigValidatorǁvalidate__mutmut_75(
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

        # allowed_tools visibility
        allowed_tools = config.get("XXallowed_toolsXX")
        if isinstance(allowed_tools, (list, tuple)) and len(allowed_tools) == 0:
            msg = "allowed_tools=[] (all tools allowed; use allowlist to restrict)"
            self._record(errors, warnings, msg, is_production)

        return ConfigValidationResult(errors=errors, warnings=warnings)

    def xǁProductionConfigValidatorǁvalidate__mutmut_76(
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

        # allowed_tools visibility
        allowed_tools = config.get("ALLOWED_TOOLS")
        if isinstance(allowed_tools, (list, tuple)) and len(allowed_tools) == 0:
            msg = "allowed_tools=[] (all tools allowed; use allowlist to restrict)"
            self._record(errors, warnings, msg, is_production)

        return ConfigValidationResult(errors=errors, warnings=warnings)

    def xǁProductionConfigValidatorǁvalidate__mutmut_77(
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

        # allowed_tools visibility
        allowed_tools = config.get("allowed_tools")
        if isinstance(allowed_tools, (list, tuple)) or len(allowed_tools) == 0:
            msg = "allowed_tools=[] (all tools allowed; use allowlist to restrict)"
            self._record(errors, warnings, msg, is_production)

        return ConfigValidationResult(errors=errors, warnings=warnings)

    def xǁProductionConfigValidatorǁvalidate__mutmut_78(
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

        # allowed_tools visibility
        allowed_tools = config.get("allowed_tools")
        if isinstance(allowed_tools, (list, tuple)) and len(allowed_tools) != 0:
            msg = "allowed_tools=[] (all tools allowed; use allowlist to restrict)"
            self._record(errors, warnings, msg, is_production)

        return ConfigValidationResult(errors=errors, warnings=warnings)

    def xǁProductionConfigValidatorǁvalidate__mutmut_79(
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

        # allowed_tools visibility
        allowed_tools = config.get("allowed_tools")
        if isinstance(allowed_tools, (list, tuple)) and len(allowed_tools) == 1:
            msg = "allowed_tools=[] (all tools allowed; use allowlist to restrict)"
            self._record(errors, warnings, msg, is_production)

        return ConfigValidationResult(errors=errors, warnings=warnings)

    def xǁProductionConfigValidatorǁvalidate__mutmut_80(
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

        # allowed_tools visibility
        allowed_tools = config.get("allowed_tools")
        if isinstance(allowed_tools, (list, tuple)) and len(allowed_tools) == 0:
            msg = None
            self._record(errors, warnings, msg, is_production)

        return ConfigValidationResult(errors=errors, warnings=warnings)

    def xǁProductionConfigValidatorǁvalidate__mutmut_81(
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

        # allowed_tools visibility
        allowed_tools = config.get("allowed_tools")
        if isinstance(allowed_tools, (list, tuple)) and len(allowed_tools) == 0:
            msg = "XXallowed_tools=[] (all tools allowed; use allowlist to restrict)XX"
            self._record(errors, warnings, msg, is_production)

        return ConfigValidationResult(errors=errors, warnings=warnings)

    def xǁProductionConfigValidatorǁvalidate__mutmut_82(
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

        # allowed_tools visibility
        allowed_tools = config.get("allowed_tools")
        if isinstance(allowed_tools, (list, tuple)) and len(allowed_tools) == 0:
            msg = "ALLOWED_TOOLS=[] (ALL TOOLS ALLOWED; USE ALLOWLIST TO RESTRICT)"
            self._record(errors, warnings, msg, is_production)

        return ConfigValidationResult(errors=errors, warnings=warnings)

    def xǁProductionConfigValidatorǁvalidate__mutmut_83(
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

        # allowed_tools visibility
        allowed_tools = config.get("allowed_tools")
        if isinstance(allowed_tools, (list, tuple)) and len(allowed_tools) == 0:
            msg = "allowed_tools=[] (all tools allowed; use allowlist to restrict)"
            self._record(None, warnings, msg, is_production)

        return ConfigValidationResult(errors=errors, warnings=warnings)

    def xǁProductionConfigValidatorǁvalidate__mutmut_84(
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

        # allowed_tools visibility
        allowed_tools = config.get("allowed_tools")
        if isinstance(allowed_tools, (list, tuple)) and len(allowed_tools) == 0:
            msg = "allowed_tools=[] (all tools allowed; use allowlist to restrict)"
            self._record(errors, None, msg, is_production)

        return ConfigValidationResult(errors=errors, warnings=warnings)

    def xǁProductionConfigValidatorǁvalidate__mutmut_85(
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

        # allowed_tools visibility
        allowed_tools = config.get("allowed_tools")
        if isinstance(allowed_tools, (list, tuple)) and len(allowed_tools) == 0:
            msg = "allowed_tools=[] (all tools allowed; use allowlist to restrict)"
            self._record(errors, warnings, None, is_production)

        return ConfigValidationResult(errors=errors, warnings=warnings)

    def xǁProductionConfigValidatorǁvalidate__mutmut_86(
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

        # allowed_tools visibility
        allowed_tools = config.get("allowed_tools")
        if isinstance(allowed_tools, (list, tuple)) and len(allowed_tools) == 0:
            msg = "allowed_tools=[] (all tools allowed; use allowlist to restrict)"
            self._record(errors, warnings, msg, None)

        return ConfigValidationResult(errors=errors, warnings=warnings)

    def xǁProductionConfigValidatorǁvalidate__mutmut_87(
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

        # allowed_tools visibility
        allowed_tools = config.get("allowed_tools")
        if isinstance(allowed_tools, (list, tuple)) and len(allowed_tools) == 0:
            msg = "allowed_tools=[] (all tools allowed; use allowlist to restrict)"
            self._record(warnings, msg, is_production)

        return ConfigValidationResult(errors=errors, warnings=warnings)

    def xǁProductionConfigValidatorǁvalidate__mutmut_88(
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

        # allowed_tools visibility
        allowed_tools = config.get("allowed_tools")
        if isinstance(allowed_tools, (list, tuple)) and len(allowed_tools) == 0:
            msg = "allowed_tools=[] (all tools allowed; use allowlist to restrict)"
            self._record(errors, msg, is_production)

        return ConfigValidationResult(errors=errors, warnings=warnings)

    def xǁProductionConfigValidatorǁvalidate__mutmut_89(
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

        # allowed_tools visibility
        allowed_tools = config.get("allowed_tools")
        if isinstance(allowed_tools, (list, tuple)) and len(allowed_tools) == 0:
            msg = "allowed_tools=[] (all tools allowed; use allowlist to restrict)"
            self._record(errors, warnings, is_production)

        return ConfigValidationResult(errors=errors, warnings=warnings)

    def xǁProductionConfigValidatorǁvalidate__mutmut_90(
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

        # allowed_tools visibility
        allowed_tools = config.get("allowed_tools")
        if isinstance(allowed_tools, (list, tuple)) and len(allowed_tools) == 0:
            msg = "allowed_tools=[] (all tools allowed; use allowlist to restrict)"
            self._record(errors, warnings, msg, )

        return ConfigValidationResult(errors=errors, warnings=warnings)

    def xǁProductionConfigValidatorǁvalidate__mutmut_91(
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

        # allowed_tools visibility
        allowed_tools = config.get("allowed_tools")
        if isinstance(allowed_tools, (list, tuple)) and len(allowed_tools) == 0:
            msg = "allowed_tools=[] (all tools allowed; use allowlist to restrict)"
            self._record(errors, warnings, msg, is_production)

        return ConfigValidationResult(errors=None, warnings=warnings)

    def xǁProductionConfigValidatorǁvalidate__mutmut_92(
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

        # allowed_tools visibility
        allowed_tools = config.get("allowed_tools")
        if isinstance(allowed_tools, (list, tuple)) and len(allowed_tools) == 0:
            msg = "allowed_tools=[] (all tools allowed; use allowlist to restrict)"
            self._record(errors, warnings, msg, is_production)

        return ConfigValidationResult(errors=errors, warnings=None)

    def xǁProductionConfigValidatorǁvalidate__mutmut_93(
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

        # allowed_tools visibility
        allowed_tools = config.get("allowed_tools")
        if isinstance(allowed_tools, (list, tuple)) and len(allowed_tools) == 0:
            msg = "allowed_tools=[] (all tools allowed; use allowlist to restrict)"
            self._record(errors, warnings, msg, is_production)

        return ConfigValidationResult(warnings=warnings)

    def xǁProductionConfigValidatorǁvalidate__mutmut_94(
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

        # allowed_tools visibility
        allowed_tools = config.get("allowed_tools")
        if isinstance(allowed_tools, (list, tuple)) and len(allowed_tools) == 0:
            msg = "allowed_tools=[] (all tools allowed; use allowlist to restrict)"
            self._record(errors, warnings, msg, is_production)

        return ConfigValidationResult(errors=errors, )

    @_mutmut_mutated(mutants_xǁProductionConfigValidatorǁvalidate_unknown_tool_safety_tiers__mutmut)
    def validate_unknown_tool_safety_tiers(
        self, unknown_keys: list[str]
    ) -> ConfigValidationResult:
        """Validate that unknown tool_safety_tiers keys are rejected."""
        errors = [
            f"tool_safety_tiers contains unknown key {k!r} (not a registered tool name)"
            for k in unknown_keys
        ]
        return ConfigValidationResult(errors=errors)

    def xǁProductionConfigValidatorǁvalidate_unknown_tool_safety_tiers__mutmut_orig(
        self, unknown_keys: list[str]
    ) -> ConfigValidationResult:
        """Validate that unknown tool_safety_tiers keys are rejected."""
        errors = [
            f"tool_safety_tiers contains unknown key {k!r} (not a registered tool name)"
            for k in unknown_keys
        ]
        return ConfigValidationResult(errors=errors)

    def xǁProductionConfigValidatorǁvalidate_unknown_tool_safety_tiers__mutmut_1(
        self, unknown_keys: list[str]
    ) -> ConfigValidationResult:
        """Validate that unknown tool_safety_tiers keys are rejected."""
        errors = None
        return ConfigValidationResult(errors=errors)

    def xǁProductionConfigValidatorǁvalidate_unknown_tool_safety_tiers__mutmut_2(
        self, unknown_keys: list[str]
    ) -> ConfigValidationResult:
        """Validate that unknown tool_safety_tiers keys are rejected."""
        errors = [
            f"tool_safety_tiers contains unknown key {k!r} (not a registered tool name)"
            for k in unknown_keys
        ]
        return ConfigValidationResult(errors=None)

    @classmethod
    @_mutmut_mutated(mutants_xǁProductionConfigValidatorǁ_record__mutmut, is_classmethod = True)
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

    @classmethod
    def xǁProductionConfigValidatorǁ_record__mutmut_orig(
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

    @classmethod
    def xǁProductionConfigValidatorǁ_record__mutmut_1(
        cls,
        errors: list[str],
        warnings: list[str],
        msg: str,
        is_production: bool,
    ) -> None:
        """Format `msg` as an error or warning and append it to the matching list."""
        e, w = None
        errors.extend(e)
        warnings.extend(w)

    @classmethod
    def xǁProductionConfigValidatorǁ_record__mutmut_2(
        cls,
        errors: list[str],
        warnings: list[str],
        msg: str,
        is_production: bool,
    ) -> None:
        """Format `msg` as an error or warning and append it to the matching list."""
        e, w = cls._format_error_or_warning(None, is_production)
        errors.extend(e)
        warnings.extend(w)

    @classmethod
    def xǁProductionConfigValidatorǁ_record__mutmut_3(
        cls,
        errors: list[str],
        warnings: list[str],
        msg: str,
        is_production: bool,
    ) -> None:
        """Format `msg` as an error or warning and append it to the matching list."""
        e, w = cls._format_error_or_warning(msg, None)
        errors.extend(e)
        warnings.extend(w)

    @classmethod
    def xǁProductionConfigValidatorǁ_record__mutmut_4(
        cls,
        errors: list[str],
        warnings: list[str],
        msg: str,
        is_production: bool,
    ) -> None:
        """Format `msg` as an error or warning and append it to the matching list."""
        e, w = cls._format_error_or_warning(is_production)
        errors.extend(e)
        warnings.extend(w)

    @classmethod
    def xǁProductionConfigValidatorǁ_record__mutmut_5(
        cls,
        errors: list[str],
        warnings: list[str],
        msg: str,
        is_production: bool,
    ) -> None:
        """Format `msg` as an error or warning and append it to the matching list."""
        e, w = cls._format_error_or_warning(msg, )
        errors.extend(e)
        warnings.extend(w)

    @classmethod
    def xǁProductionConfigValidatorǁ_record__mutmut_6(
        cls,
        errors: list[str],
        warnings: list[str],
        msg: str,
        is_production: bool,
    ) -> None:
        """Format `msg` as an error or warning and append it to the matching list."""
        e, w = cls._format_error_or_warning(msg, is_production)
        errors.extend(None)
        warnings.extend(w)

    @classmethod
    def xǁProductionConfigValidatorǁ_record__mutmut_7(
        cls,
        errors: list[str],
        warnings: list[str],
        msg: str,
        is_production: bool,
    ) -> None:
        """Format `msg` as an error or warning and append it to the matching list."""
        e, w = cls._format_error_or_warning(msg, is_production)
        errors.extend(e)
        warnings.extend(None)

    @staticmethod
    @_mutmut_mutated(mutants_xǁProductionConfigValidatorǁ_format_error_or_warning__mutmut)
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

    @staticmethod
    def xǁProductionConfigValidatorǁ_format_error_or_warning__mutmut_orig(
        msg: str, is_production: bool
    ) -> tuple[list[str], list[str]]:
        errors: list[str] = []
        warnings: list[str] = []
        if is_production:
            errors.append(msg)
        else:
            warnings.append(f"[local/development] {msg}")
        return errors, warnings

    @staticmethod
    def xǁProductionConfigValidatorǁ_format_error_or_warning__mutmut_1(
        msg: str, is_production: bool
    ) -> tuple[list[str], list[str]]:
        errors: list[str] = None
        warnings: list[str] = []
        if is_production:
            errors.append(msg)
        else:
            warnings.append(f"[local/development] {msg}")
        return errors, warnings

    @staticmethod
    def xǁProductionConfigValidatorǁ_format_error_or_warning__mutmut_2(
        msg: str, is_production: bool
    ) -> tuple[list[str], list[str]]:
        errors: list[str] = []
        warnings: list[str] = None
        if is_production:
            errors.append(msg)
        else:
            warnings.append(f"[local/development] {msg}")
        return errors, warnings

    @staticmethod
    def xǁProductionConfigValidatorǁ_format_error_or_warning__mutmut_3(
        msg: str, is_production: bool
    ) -> tuple[list[str], list[str]]:
        errors: list[str] = []
        warnings: list[str] = []
        if is_production:
            errors.append(None)
        else:
            warnings.append(f"[local/development] {msg}")
        return errors, warnings

    @staticmethod
    def xǁProductionConfigValidatorǁ_format_error_or_warning__mutmut_4(
        msg: str, is_production: bool
    ) -> tuple[list[str], list[str]]:
        errors: list[str] = []
        warnings: list[str] = []
        if is_production:
            errors.append(msg)
        else:
            warnings.append(None)
        return errors, warnings

mutants_xǁProductionConfigValidatorǁvalidate__mutmut['_mutmut_orig'] = ProductionConfigValidator.xǁProductionConfigValidatorǁvalidate__mutmut_orig # type: ignore # mutmut generated
mutants_xǁProductionConfigValidatorǁvalidate__mutmut['xǁProductionConfigValidatorǁvalidate__mutmut_1'] = ProductionConfigValidator.xǁProductionConfigValidatorǁvalidate__mutmut_1 # type: ignore # mutmut generated
mutants_xǁProductionConfigValidatorǁvalidate__mutmut['xǁProductionConfigValidatorǁvalidate__mutmut_2'] = ProductionConfigValidator.xǁProductionConfigValidatorǁvalidate__mutmut_2 # type: ignore # mutmut generated
mutants_xǁProductionConfigValidatorǁvalidate__mutmut['xǁProductionConfigValidatorǁvalidate__mutmut_3'] = ProductionConfigValidator.xǁProductionConfigValidatorǁvalidate__mutmut_3 # type: ignore # mutmut generated
mutants_xǁProductionConfigValidatorǁvalidate__mutmut['xǁProductionConfigValidatorǁvalidate__mutmut_4'] = ProductionConfigValidator.xǁProductionConfigValidatorǁvalidate__mutmut_4 # type: ignore # mutmut generated
mutants_xǁProductionConfigValidatorǁvalidate__mutmut['xǁProductionConfigValidatorǁvalidate__mutmut_5'] = ProductionConfigValidator.xǁProductionConfigValidatorǁvalidate__mutmut_5 # type: ignore # mutmut generated
mutants_xǁProductionConfigValidatorǁvalidate__mutmut['xǁProductionConfigValidatorǁvalidate__mutmut_6'] = ProductionConfigValidator.xǁProductionConfigValidatorǁvalidate__mutmut_6 # type: ignore # mutmut generated
mutants_xǁProductionConfigValidatorǁvalidate__mutmut['xǁProductionConfigValidatorǁvalidate__mutmut_7'] = ProductionConfigValidator.xǁProductionConfigValidatorǁvalidate__mutmut_7 # type: ignore # mutmut generated
mutants_xǁProductionConfigValidatorǁvalidate__mutmut['xǁProductionConfigValidatorǁvalidate__mutmut_8'] = ProductionConfigValidator.xǁProductionConfigValidatorǁvalidate__mutmut_8 # type: ignore # mutmut generated
mutants_xǁProductionConfigValidatorǁvalidate__mutmut['xǁProductionConfigValidatorǁvalidate__mutmut_9'] = ProductionConfigValidator.xǁProductionConfigValidatorǁvalidate__mutmut_9 # type: ignore # mutmut generated
mutants_xǁProductionConfigValidatorǁvalidate__mutmut['xǁProductionConfigValidatorǁvalidate__mutmut_10'] = ProductionConfigValidator.xǁProductionConfigValidatorǁvalidate__mutmut_10 # type: ignore # mutmut generated
mutants_xǁProductionConfigValidatorǁvalidate__mutmut['xǁProductionConfigValidatorǁvalidate__mutmut_11'] = ProductionConfigValidator.xǁProductionConfigValidatorǁvalidate__mutmut_11 # type: ignore # mutmut generated
mutants_xǁProductionConfigValidatorǁvalidate__mutmut['xǁProductionConfigValidatorǁvalidate__mutmut_12'] = ProductionConfigValidator.xǁProductionConfigValidatorǁvalidate__mutmut_12 # type: ignore # mutmut generated
mutants_xǁProductionConfigValidatorǁvalidate__mutmut['xǁProductionConfigValidatorǁvalidate__mutmut_13'] = ProductionConfigValidator.xǁProductionConfigValidatorǁvalidate__mutmut_13 # type: ignore # mutmut generated
mutants_xǁProductionConfigValidatorǁvalidate__mutmut['xǁProductionConfigValidatorǁvalidate__mutmut_14'] = ProductionConfigValidator.xǁProductionConfigValidatorǁvalidate__mutmut_14 # type: ignore # mutmut generated
mutants_xǁProductionConfigValidatorǁvalidate__mutmut['xǁProductionConfigValidatorǁvalidate__mutmut_15'] = ProductionConfigValidator.xǁProductionConfigValidatorǁvalidate__mutmut_15 # type: ignore # mutmut generated
mutants_xǁProductionConfigValidatorǁvalidate__mutmut['xǁProductionConfigValidatorǁvalidate__mutmut_16'] = ProductionConfigValidator.xǁProductionConfigValidatorǁvalidate__mutmut_16 # type: ignore # mutmut generated
mutants_xǁProductionConfigValidatorǁvalidate__mutmut['xǁProductionConfigValidatorǁvalidate__mutmut_17'] = ProductionConfigValidator.xǁProductionConfigValidatorǁvalidate__mutmut_17 # type: ignore # mutmut generated
mutants_xǁProductionConfigValidatorǁvalidate__mutmut['xǁProductionConfigValidatorǁvalidate__mutmut_18'] = ProductionConfigValidator.xǁProductionConfigValidatorǁvalidate__mutmut_18 # type: ignore # mutmut generated
mutants_xǁProductionConfigValidatorǁvalidate__mutmut['xǁProductionConfigValidatorǁvalidate__mutmut_19'] = ProductionConfigValidator.xǁProductionConfigValidatorǁvalidate__mutmut_19 # type: ignore # mutmut generated
mutants_xǁProductionConfigValidatorǁvalidate__mutmut['xǁProductionConfigValidatorǁvalidate__mutmut_20'] = ProductionConfigValidator.xǁProductionConfigValidatorǁvalidate__mutmut_20 # type: ignore # mutmut generated
mutants_xǁProductionConfigValidatorǁvalidate__mutmut['xǁProductionConfigValidatorǁvalidate__mutmut_21'] = ProductionConfigValidator.xǁProductionConfigValidatorǁvalidate__mutmut_21 # type: ignore # mutmut generated
mutants_xǁProductionConfigValidatorǁvalidate__mutmut['xǁProductionConfigValidatorǁvalidate__mutmut_22'] = ProductionConfigValidator.xǁProductionConfigValidatorǁvalidate__mutmut_22 # type: ignore # mutmut generated
mutants_xǁProductionConfigValidatorǁvalidate__mutmut['xǁProductionConfigValidatorǁvalidate__mutmut_23'] = ProductionConfigValidator.xǁProductionConfigValidatorǁvalidate__mutmut_23 # type: ignore # mutmut generated
mutants_xǁProductionConfigValidatorǁvalidate__mutmut['xǁProductionConfigValidatorǁvalidate__mutmut_24'] = ProductionConfigValidator.xǁProductionConfigValidatorǁvalidate__mutmut_24 # type: ignore # mutmut generated
mutants_xǁProductionConfigValidatorǁvalidate__mutmut['xǁProductionConfigValidatorǁvalidate__mutmut_25'] = ProductionConfigValidator.xǁProductionConfigValidatorǁvalidate__mutmut_25 # type: ignore # mutmut generated
mutants_xǁProductionConfigValidatorǁvalidate__mutmut['xǁProductionConfigValidatorǁvalidate__mutmut_26'] = ProductionConfigValidator.xǁProductionConfigValidatorǁvalidate__mutmut_26 # type: ignore # mutmut generated
mutants_xǁProductionConfigValidatorǁvalidate__mutmut['xǁProductionConfigValidatorǁvalidate__mutmut_27'] = ProductionConfigValidator.xǁProductionConfigValidatorǁvalidate__mutmut_27 # type: ignore # mutmut generated
mutants_xǁProductionConfigValidatorǁvalidate__mutmut['xǁProductionConfigValidatorǁvalidate__mutmut_28'] = ProductionConfigValidator.xǁProductionConfigValidatorǁvalidate__mutmut_28 # type: ignore # mutmut generated
mutants_xǁProductionConfigValidatorǁvalidate__mutmut['xǁProductionConfigValidatorǁvalidate__mutmut_29'] = ProductionConfigValidator.xǁProductionConfigValidatorǁvalidate__mutmut_29 # type: ignore # mutmut generated
mutants_xǁProductionConfigValidatorǁvalidate__mutmut['xǁProductionConfigValidatorǁvalidate__mutmut_30'] = ProductionConfigValidator.xǁProductionConfigValidatorǁvalidate__mutmut_30 # type: ignore # mutmut generated
mutants_xǁProductionConfigValidatorǁvalidate__mutmut['xǁProductionConfigValidatorǁvalidate__mutmut_31'] = ProductionConfigValidator.xǁProductionConfigValidatorǁvalidate__mutmut_31 # type: ignore # mutmut generated
mutants_xǁProductionConfigValidatorǁvalidate__mutmut['xǁProductionConfigValidatorǁvalidate__mutmut_32'] = ProductionConfigValidator.xǁProductionConfigValidatorǁvalidate__mutmut_32 # type: ignore # mutmut generated
mutants_xǁProductionConfigValidatorǁvalidate__mutmut['xǁProductionConfigValidatorǁvalidate__mutmut_33'] = ProductionConfigValidator.xǁProductionConfigValidatorǁvalidate__mutmut_33 # type: ignore # mutmut generated
mutants_xǁProductionConfigValidatorǁvalidate__mutmut['xǁProductionConfigValidatorǁvalidate__mutmut_34'] = ProductionConfigValidator.xǁProductionConfigValidatorǁvalidate__mutmut_34 # type: ignore # mutmut generated
mutants_xǁProductionConfigValidatorǁvalidate__mutmut['xǁProductionConfigValidatorǁvalidate__mutmut_35'] = ProductionConfigValidator.xǁProductionConfigValidatorǁvalidate__mutmut_35 # type: ignore # mutmut generated
mutants_xǁProductionConfigValidatorǁvalidate__mutmut['xǁProductionConfigValidatorǁvalidate__mutmut_36'] = ProductionConfigValidator.xǁProductionConfigValidatorǁvalidate__mutmut_36 # type: ignore # mutmut generated
mutants_xǁProductionConfigValidatorǁvalidate__mutmut['xǁProductionConfigValidatorǁvalidate__mutmut_37'] = ProductionConfigValidator.xǁProductionConfigValidatorǁvalidate__mutmut_37 # type: ignore # mutmut generated
mutants_xǁProductionConfigValidatorǁvalidate__mutmut['xǁProductionConfigValidatorǁvalidate__mutmut_38'] = ProductionConfigValidator.xǁProductionConfigValidatorǁvalidate__mutmut_38 # type: ignore # mutmut generated
mutants_xǁProductionConfigValidatorǁvalidate__mutmut['xǁProductionConfigValidatorǁvalidate__mutmut_39'] = ProductionConfigValidator.xǁProductionConfigValidatorǁvalidate__mutmut_39 # type: ignore # mutmut generated
mutants_xǁProductionConfigValidatorǁvalidate__mutmut['xǁProductionConfigValidatorǁvalidate__mutmut_40'] = ProductionConfigValidator.xǁProductionConfigValidatorǁvalidate__mutmut_40 # type: ignore # mutmut generated
mutants_xǁProductionConfigValidatorǁvalidate__mutmut['xǁProductionConfigValidatorǁvalidate__mutmut_41'] = ProductionConfigValidator.xǁProductionConfigValidatorǁvalidate__mutmut_41 # type: ignore # mutmut generated
mutants_xǁProductionConfigValidatorǁvalidate__mutmut['xǁProductionConfigValidatorǁvalidate__mutmut_42'] = ProductionConfigValidator.xǁProductionConfigValidatorǁvalidate__mutmut_42 # type: ignore # mutmut generated
mutants_xǁProductionConfigValidatorǁvalidate__mutmut['xǁProductionConfigValidatorǁvalidate__mutmut_43'] = ProductionConfigValidator.xǁProductionConfigValidatorǁvalidate__mutmut_43 # type: ignore # mutmut generated
mutants_xǁProductionConfigValidatorǁvalidate__mutmut['xǁProductionConfigValidatorǁvalidate__mutmut_44'] = ProductionConfigValidator.xǁProductionConfigValidatorǁvalidate__mutmut_44 # type: ignore # mutmut generated
mutants_xǁProductionConfigValidatorǁvalidate__mutmut['xǁProductionConfigValidatorǁvalidate__mutmut_45'] = ProductionConfigValidator.xǁProductionConfigValidatorǁvalidate__mutmut_45 # type: ignore # mutmut generated
mutants_xǁProductionConfigValidatorǁvalidate__mutmut['xǁProductionConfigValidatorǁvalidate__mutmut_46'] = ProductionConfigValidator.xǁProductionConfigValidatorǁvalidate__mutmut_46 # type: ignore # mutmut generated
mutants_xǁProductionConfigValidatorǁvalidate__mutmut['xǁProductionConfigValidatorǁvalidate__mutmut_47'] = ProductionConfigValidator.xǁProductionConfigValidatorǁvalidate__mutmut_47 # type: ignore # mutmut generated
mutants_xǁProductionConfigValidatorǁvalidate__mutmut['xǁProductionConfigValidatorǁvalidate__mutmut_48'] = ProductionConfigValidator.xǁProductionConfigValidatorǁvalidate__mutmut_48 # type: ignore # mutmut generated
mutants_xǁProductionConfigValidatorǁvalidate__mutmut['xǁProductionConfigValidatorǁvalidate__mutmut_49'] = ProductionConfigValidator.xǁProductionConfigValidatorǁvalidate__mutmut_49 # type: ignore # mutmut generated
mutants_xǁProductionConfigValidatorǁvalidate__mutmut['xǁProductionConfigValidatorǁvalidate__mutmut_50'] = ProductionConfigValidator.xǁProductionConfigValidatorǁvalidate__mutmut_50 # type: ignore # mutmut generated
mutants_xǁProductionConfigValidatorǁvalidate__mutmut['xǁProductionConfigValidatorǁvalidate__mutmut_51'] = ProductionConfigValidator.xǁProductionConfigValidatorǁvalidate__mutmut_51 # type: ignore # mutmut generated
mutants_xǁProductionConfigValidatorǁvalidate__mutmut['xǁProductionConfigValidatorǁvalidate__mutmut_52'] = ProductionConfigValidator.xǁProductionConfigValidatorǁvalidate__mutmut_52 # type: ignore # mutmut generated
mutants_xǁProductionConfigValidatorǁvalidate__mutmut['xǁProductionConfigValidatorǁvalidate__mutmut_53'] = ProductionConfigValidator.xǁProductionConfigValidatorǁvalidate__mutmut_53 # type: ignore # mutmut generated
mutants_xǁProductionConfigValidatorǁvalidate__mutmut['xǁProductionConfigValidatorǁvalidate__mutmut_54'] = ProductionConfigValidator.xǁProductionConfigValidatorǁvalidate__mutmut_54 # type: ignore # mutmut generated
mutants_xǁProductionConfigValidatorǁvalidate__mutmut['xǁProductionConfigValidatorǁvalidate__mutmut_55'] = ProductionConfigValidator.xǁProductionConfigValidatorǁvalidate__mutmut_55 # type: ignore # mutmut generated
mutants_xǁProductionConfigValidatorǁvalidate__mutmut['xǁProductionConfigValidatorǁvalidate__mutmut_56'] = ProductionConfigValidator.xǁProductionConfigValidatorǁvalidate__mutmut_56 # type: ignore # mutmut generated
mutants_xǁProductionConfigValidatorǁvalidate__mutmut['xǁProductionConfigValidatorǁvalidate__mutmut_57'] = ProductionConfigValidator.xǁProductionConfigValidatorǁvalidate__mutmut_57 # type: ignore # mutmut generated
mutants_xǁProductionConfigValidatorǁvalidate__mutmut['xǁProductionConfigValidatorǁvalidate__mutmut_58'] = ProductionConfigValidator.xǁProductionConfigValidatorǁvalidate__mutmut_58 # type: ignore # mutmut generated
mutants_xǁProductionConfigValidatorǁvalidate__mutmut['xǁProductionConfigValidatorǁvalidate__mutmut_59'] = ProductionConfigValidator.xǁProductionConfigValidatorǁvalidate__mutmut_59 # type: ignore # mutmut generated
mutants_xǁProductionConfigValidatorǁvalidate__mutmut['xǁProductionConfigValidatorǁvalidate__mutmut_60'] = ProductionConfigValidator.xǁProductionConfigValidatorǁvalidate__mutmut_60 # type: ignore # mutmut generated
mutants_xǁProductionConfigValidatorǁvalidate__mutmut['xǁProductionConfigValidatorǁvalidate__mutmut_61'] = ProductionConfigValidator.xǁProductionConfigValidatorǁvalidate__mutmut_61 # type: ignore # mutmut generated
mutants_xǁProductionConfigValidatorǁvalidate__mutmut['xǁProductionConfigValidatorǁvalidate__mutmut_62'] = ProductionConfigValidator.xǁProductionConfigValidatorǁvalidate__mutmut_62 # type: ignore # mutmut generated
mutants_xǁProductionConfigValidatorǁvalidate__mutmut['xǁProductionConfigValidatorǁvalidate__mutmut_63'] = ProductionConfigValidator.xǁProductionConfigValidatorǁvalidate__mutmut_63 # type: ignore # mutmut generated
mutants_xǁProductionConfigValidatorǁvalidate__mutmut['xǁProductionConfigValidatorǁvalidate__mutmut_64'] = ProductionConfigValidator.xǁProductionConfigValidatorǁvalidate__mutmut_64 # type: ignore # mutmut generated
mutants_xǁProductionConfigValidatorǁvalidate__mutmut['xǁProductionConfigValidatorǁvalidate__mutmut_65'] = ProductionConfigValidator.xǁProductionConfigValidatorǁvalidate__mutmut_65 # type: ignore # mutmut generated
mutants_xǁProductionConfigValidatorǁvalidate__mutmut['xǁProductionConfigValidatorǁvalidate__mutmut_66'] = ProductionConfigValidator.xǁProductionConfigValidatorǁvalidate__mutmut_66 # type: ignore # mutmut generated
mutants_xǁProductionConfigValidatorǁvalidate__mutmut['xǁProductionConfigValidatorǁvalidate__mutmut_67'] = ProductionConfigValidator.xǁProductionConfigValidatorǁvalidate__mutmut_67 # type: ignore # mutmut generated
mutants_xǁProductionConfigValidatorǁvalidate__mutmut['xǁProductionConfigValidatorǁvalidate__mutmut_68'] = ProductionConfigValidator.xǁProductionConfigValidatorǁvalidate__mutmut_68 # type: ignore # mutmut generated
mutants_xǁProductionConfigValidatorǁvalidate__mutmut['xǁProductionConfigValidatorǁvalidate__mutmut_69'] = ProductionConfigValidator.xǁProductionConfigValidatorǁvalidate__mutmut_69 # type: ignore # mutmut generated
mutants_xǁProductionConfigValidatorǁvalidate__mutmut['xǁProductionConfigValidatorǁvalidate__mutmut_70'] = ProductionConfigValidator.xǁProductionConfigValidatorǁvalidate__mutmut_70 # type: ignore # mutmut generated
mutants_xǁProductionConfigValidatorǁvalidate__mutmut['xǁProductionConfigValidatorǁvalidate__mutmut_71'] = ProductionConfigValidator.xǁProductionConfigValidatorǁvalidate__mutmut_71 # type: ignore # mutmut generated
mutants_xǁProductionConfigValidatorǁvalidate__mutmut['xǁProductionConfigValidatorǁvalidate__mutmut_72'] = ProductionConfigValidator.xǁProductionConfigValidatorǁvalidate__mutmut_72 # type: ignore # mutmut generated
mutants_xǁProductionConfigValidatorǁvalidate__mutmut['xǁProductionConfigValidatorǁvalidate__mutmut_73'] = ProductionConfigValidator.xǁProductionConfigValidatorǁvalidate__mutmut_73 # type: ignore # mutmut generated
mutants_xǁProductionConfigValidatorǁvalidate__mutmut['xǁProductionConfigValidatorǁvalidate__mutmut_74'] = ProductionConfigValidator.xǁProductionConfigValidatorǁvalidate__mutmut_74 # type: ignore # mutmut generated
mutants_xǁProductionConfigValidatorǁvalidate__mutmut['xǁProductionConfigValidatorǁvalidate__mutmut_75'] = ProductionConfigValidator.xǁProductionConfigValidatorǁvalidate__mutmut_75 # type: ignore # mutmut generated
mutants_xǁProductionConfigValidatorǁvalidate__mutmut['xǁProductionConfigValidatorǁvalidate__mutmut_76'] = ProductionConfigValidator.xǁProductionConfigValidatorǁvalidate__mutmut_76 # type: ignore # mutmut generated
mutants_xǁProductionConfigValidatorǁvalidate__mutmut['xǁProductionConfigValidatorǁvalidate__mutmut_77'] = ProductionConfigValidator.xǁProductionConfigValidatorǁvalidate__mutmut_77 # type: ignore # mutmut generated
mutants_xǁProductionConfigValidatorǁvalidate__mutmut['xǁProductionConfigValidatorǁvalidate__mutmut_78'] = ProductionConfigValidator.xǁProductionConfigValidatorǁvalidate__mutmut_78 # type: ignore # mutmut generated
mutants_xǁProductionConfigValidatorǁvalidate__mutmut['xǁProductionConfigValidatorǁvalidate__mutmut_79'] = ProductionConfigValidator.xǁProductionConfigValidatorǁvalidate__mutmut_79 # type: ignore # mutmut generated
mutants_xǁProductionConfigValidatorǁvalidate__mutmut['xǁProductionConfigValidatorǁvalidate__mutmut_80'] = ProductionConfigValidator.xǁProductionConfigValidatorǁvalidate__mutmut_80 # type: ignore # mutmut generated
mutants_xǁProductionConfigValidatorǁvalidate__mutmut['xǁProductionConfigValidatorǁvalidate__mutmut_81'] = ProductionConfigValidator.xǁProductionConfigValidatorǁvalidate__mutmut_81 # type: ignore # mutmut generated
mutants_xǁProductionConfigValidatorǁvalidate__mutmut['xǁProductionConfigValidatorǁvalidate__mutmut_82'] = ProductionConfigValidator.xǁProductionConfigValidatorǁvalidate__mutmut_82 # type: ignore # mutmut generated
mutants_xǁProductionConfigValidatorǁvalidate__mutmut['xǁProductionConfigValidatorǁvalidate__mutmut_83'] = ProductionConfigValidator.xǁProductionConfigValidatorǁvalidate__mutmut_83 # type: ignore # mutmut generated
mutants_xǁProductionConfigValidatorǁvalidate__mutmut['xǁProductionConfigValidatorǁvalidate__mutmut_84'] = ProductionConfigValidator.xǁProductionConfigValidatorǁvalidate__mutmut_84 # type: ignore # mutmut generated
mutants_xǁProductionConfigValidatorǁvalidate__mutmut['xǁProductionConfigValidatorǁvalidate__mutmut_85'] = ProductionConfigValidator.xǁProductionConfigValidatorǁvalidate__mutmut_85 # type: ignore # mutmut generated
mutants_xǁProductionConfigValidatorǁvalidate__mutmut['xǁProductionConfigValidatorǁvalidate__mutmut_86'] = ProductionConfigValidator.xǁProductionConfigValidatorǁvalidate__mutmut_86 # type: ignore # mutmut generated
mutants_xǁProductionConfigValidatorǁvalidate__mutmut['xǁProductionConfigValidatorǁvalidate__mutmut_87'] = ProductionConfigValidator.xǁProductionConfigValidatorǁvalidate__mutmut_87 # type: ignore # mutmut generated
mutants_xǁProductionConfigValidatorǁvalidate__mutmut['xǁProductionConfigValidatorǁvalidate__mutmut_88'] = ProductionConfigValidator.xǁProductionConfigValidatorǁvalidate__mutmut_88 # type: ignore # mutmut generated
mutants_xǁProductionConfigValidatorǁvalidate__mutmut['xǁProductionConfigValidatorǁvalidate__mutmut_89'] = ProductionConfigValidator.xǁProductionConfigValidatorǁvalidate__mutmut_89 # type: ignore # mutmut generated
mutants_xǁProductionConfigValidatorǁvalidate__mutmut['xǁProductionConfigValidatorǁvalidate__mutmut_90'] = ProductionConfigValidator.xǁProductionConfigValidatorǁvalidate__mutmut_90 # type: ignore # mutmut generated
mutants_xǁProductionConfigValidatorǁvalidate__mutmut['xǁProductionConfigValidatorǁvalidate__mutmut_91'] = ProductionConfigValidator.xǁProductionConfigValidatorǁvalidate__mutmut_91 # type: ignore # mutmut generated
mutants_xǁProductionConfigValidatorǁvalidate__mutmut['xǁProductionConfigValidatorǁvalidate__mutmut_92'] = ProductionConfigValidator.xǁProductionConfigValidatorǁvalidate__mutmut_92 # type: ignore # mutmut generated
mutants_xǁProductionConfigValidatorǁvalidate__mutmut['xǁProductionConfigValidatorǁvalidate__mutmut_93'] = ProductionConfigValidator.xǁProductionConfigValidatorǁvalidate__mutmut_93 # type: ignore # mutmut generated
mutants_xǁProductionConfigValidatorǁvalidate__mutmut['xǁProductionConfigValidatorǁvalidate__mutmut_94'] = ProductionConfigValidator.xǁProductionConfigValidatorǁvalidate__mutmut_94 # type: ignore # mutmut generated

mutants_xǁProductionConfigValidatorǁvalidate_unknown_tool_safety_tiers__mutmut['_mutmut_orig'] = ProductionConfigValidator.xǁProductionConfigValidatorǁvalidate_unknown_tool_safety_tiers__mutmut_orig # type: ignore # mutmut generated
mutants_xǁProductionConfigValidatorǁvalidate_unknown_tool_safety_tiers__mutmut['xǁProductionConfigValidatorǁvalidate_unknown_tool_safety_tiers__mutmut_1'] = ProductionConfigValidator.xǁProductionConfigValidatorǁvalidate_unknown_tool_safety_tiers__mutmut_1 # type: ignore # mutmut generated
mutants_xǁProductionConfigValidatorǁvalidate_unknown_tool_safety_tiers__mutmut['xǁProductionConfigValidatorǁvalidate_unknown_tool_safety_tiers__mutmut_2'] = ProductionConfigValidator.xǁProductionConfigValidatorǁvalidate_unknown_tool_safety_tiers__mutmut_2 # type: ignore # mutmut generated

mutants_xǁProductionConfigValidatorǁ_record__mutmut['_mutmut_orig'] = ProductionConfigValidator.xǁProductionConfigValidatorǁ_record__mutmut_orig # type: ignore # mutmut generated
mutants_xǁProductionConfigValidatorǁ_record__mutmut['xǁProductionConfigValidatorǁ_record__mutmut_1'] = ProductionConfigValidator.xǁProductionConfigValidatorǁ_record__mutmut_1 # type: ignore # mutmut generated
mutants_xǁProductionConfigValidatorǁ_record__mutmut['xǁProductionConfigValidatorǁ_record__mutmut_2'] = ProductionConfigValidator.xǁProductionConfigValidatorǁ_record__mutmut_2 # type: ignore # mutmut generated
mutants_xǁProductionConfigValidatorǁ_record__mutmut['xǁProductionConfigValidatorǁ_record__mutmut_3'] = ProductionConfigValidator.xǁProductionConfigValidatorǁ_record__mutmut_3 # type: ignore # mutmut generated
mutants_xǁProductionConfigValidatorǁ_record__mutmut['xǁProductionConfigValidatorǁ_record__mutmut_4'] = ProductionConfigValidator.xǁProductionConfigValidatorǁ_record__mutmut_4 # type: ignore # mutmut generated
mutants_xǁProductionConfigValidatorǁ_record__mutmut['xǁProductionConfigValidatorǁ_record__mutmut_5'] = ProductionConfigValidator.xǁProductionConfigValidatorǁ_record__mutmut_5 # type: ignore # mutmut generated
mutants_xǁProductionConfigValidatorǁ_record__mutmut['xǁProductionConfigValidatorǁ_record__mutmut_6'] = ProductionConfigValidator.xǁProductionConfigValidatorǁ_record__mutmut_6 # type: ignore # mutmut generated
mutants_xǁProductionConfigValidatorǁ_record__mutmut['xǁProductionConfigValidatorǁ_record__mutmut_7'] = ProductionConfigValidator.xǁProductionConfigValidatorǁ_record__mutmut_7 # type: ignore # mutmut generated

mutants_xǁProductionConfigValidatorǁ_format_error_or_warning__mutmut['_mutmut_orig'] = ProductionConfigValidator.xǁProductionConfigValidatorǁ_format_error_or_warning__mutmut_orig # type: ignore # mutmut generated
mutants_xǁProductionConfigValidatorǁ_format_error_or_warning__mutmut['xǁProductionConfigValidatorǁ_format_error_or_warning__mutmut_1'] = ProductionConfigValidator.xǁProductionConfigValidatorǁ_format_error_or_warning__mutmut_1 # type: ignore # mutmut generated
mutants_xǁProductionConfigValidatorǁ_format_error_or_warning__mutmut['xǁProductionConfigValidatorǁ_format_error_or_warning__mutmut_2'] = ProductionConfigValidator.xǁProductionConfigValidatorǁ_format_error_or_warning__mutmut_2 # type: ignore # mutmut generated
mutants_xǁProductionConfigValidatorǁ_format_error_or_warning__mutmut['xǁProductionConfigValidatorǁ_format_error_or_warning__mutmut_3'] = ProductionConfigValidator.xǁProductionConfigValidatorǁ_format_error_or_warning__mutmut_3 # type: ignore # mutmut generated
mutants_xǁProductionConfigValidatorǁ_format_error_or_warning__mutmut['xǁProductionConfigValidatorǁ_format_error_or_warning__mutmut_4'] = ProductionConfigValidator.xǁProductionConfigValidatorǁ_format_error_or_warning__mutmut_4 # type: ignore # mutmut generated


__all__ = ["ConfigValidationResult", "ProductionConfigValidator"]
