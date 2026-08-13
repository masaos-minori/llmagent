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

        embed_dim_error = self._check_embedding_dim(rag)
        if embed_dim_error is not None:
            errors.append(embed_dim_error)

        use_rrf_warning = self._check_use_rrf(rag)
        if use_rrf_warning is not None:
            warnings.append(use_rrf_warning)

        threshold_warning = self._check_semantic_cache_threshold(rag)
        if threshold_warning is not None:
            warnings.append(threshold_warning)

        max_size_error = self._check_semantic_cache_max_size(rag)
        if max_size_error is not None:
            errors.append(max_size_error)

        return ConfigValidationResult(errors=errors, warnings=warnings)

    @staticmethod
    def _extract_rag_section(cfg: Mapping[str, Any]) -> Mapping[str, Any]:
        """Normalize nested {"rag": {...}} (agent.toml) and flat {...} (MCP module_cfg) shapes."""
        return cfg["rag"] if "rag" in cfg else cfg

    @staticmethod
    def _check_embedding_dim(rag: Mapping[str, Any]) -> str | None:
        """Return an error message when embedding_dim and vec_dim disagree."""
        embed_dim = rag.get("embedding_dim")
        vec_dim = rag.get("vec_dim")
        if embed_dim and vec_dim and embed_dim != vec_dim:
            return f"embedding_dim={embed_dim} != vec_dim={vec_dim}"
        return None

    @staticmethod
    def _check_use_rrf(rag: Mapping[str, Any]) -> str | None:
        """Return a warning message when use_rrf is disabled."""
        if not rag.get("use_rrf", True):
            return "use_rrf=false degrades retrieval quality; use only for diagnostics"
        return None

    @staticmethod
    def _check_semantic_cache_threshold(rag: Mapping[str, Any]) -> str | None:
        """Return a warning message when semantic_cache_threshold is unusually low."""
        threshold = rag.get("semantic_cache_threshold", 0.92)
        if threshold < 0.5:
            return f"semantic_cache_threshold={threshold} is unusually low"
        return None

    @staticmethod
    def _check_semantic_cache_max_size(rag: Mapping[str, Any]) -> str | None:
        """Return an error message when semantic_cache_max_size is negative."""
        max_size = rag.get("semantic_cache_max_size", 100)
        if max_size < 0:
            return f"semantic_cache_max_size={max_size} is negative; must be >= 0"
        return None
