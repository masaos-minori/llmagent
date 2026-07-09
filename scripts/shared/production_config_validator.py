from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ConfigValidationResult:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


_REQUIRED_STRICT_KEYS = (
    "plugin_strict",
    "tool_definitions_strict",
    "routing_drift_strict",
    "use_tool_dag",
)


class ProductionConfigValidator:
    def validate(self, config: dict[str, Any]) -> ConfigValidationResult:
        errors: list[str] = []
        for key in _REQUIRED_STRICT_KEYS:
            if not config.get(key, False):
                errors.append(f"{key}=false — strict mode is required in production")
        return ConfigValidationResult(errors=errors)

    def validate_unknown_tool_safety_tiers(
        self, unknown_keys: list[str]
    ) -> ConfigValidationResult:
        errors = [
            f"tool_safety_tiers contains unknown key {k!r} (not a registered tool name)"
            for k in unknown_keys
        ]
        return ConfigValidationResult(errors=errors, warnings=[])


__all__ = ["ConfigValidationResult", "ProductionConfigValidator"]
