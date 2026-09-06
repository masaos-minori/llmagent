"""scripts/shared/config_validator.py — Startup validator for RAG config cross-file consistency."""

from __future__ import annotations

import dataclasses
from collections.abc import Mapping
from typing import Any


@dataclasses.dataclass
class ConfigValidationResult:
    """Result of RAG configuration validation containing errors and warnings."""

    errors: list[str]
    warnings: list[str]

    @property
    def ok(self) -> bool:
        """Return True when there are no validation errors."""
        return len(self.errors) == 0


class RagConfigValidator:
    """Validate RAG configuration for cross-file consistency."""

    def validate(self, cfg: Mapping[str, Any]) -> ConfigValidationResult:
        """Validate RAG configuration and return results with errors and warnings."""
        rag = self._extract_rag_section(cfg)
        errors: list[str] = []
        warnings: list[str] = []

        use_rrf_warning = self._check_use_rrf(rag)
        if use_rrf_warning is not None:
            warnings.append(use_rrf_warning)

        unknown_keys = self._check_unknown_rag_keys(rag)
        for key in unknown_keys:
            errors.append(f"unknown RAG config key: {key}")

        return ConfigValidationResult(errors=errors, warnings=warnings)

    @staticmethod
    def _extract_rag_section(cfg: Mapping[str, Any]) -> Mapping[str, Any]:
        """Normalize nested {"rag": {...}} (agent.toml) and flat {...} (MCP module_cfg) shapes."""
        return cfg["rag"] if "rag" in cfg else cfg

    @staticmethod
    def _check_use_rrf(rag: Mapping[str, Any]) -> str | None:
        """Return a warning message when use_rrf is disabled."""
        if not rag.get("use_rrf", True):
            return "use_rrf=false degrades retrieval quality; use only for diagnostics"
        return None

    @staticmethod
    def _check_unknown_rag_keys(rag: Mapping[str, Any]) -> list[str]:
        """Return a list of unknown RAG config keys that were removed from RagConfigImpl."""
        REMOVED_KEYS = frozenset(("semantic_cache_max_size", "semantic_cache_threshold", "use_semantic_cache"))
        return [k for k in rag if k in REMOVED_KEYS]
