"""shared/config_validator.py — Startup validator for RAG config cross-file consistency."""

from __future__ import annotations

import dataclasses
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

    def validate(self, cfg: dict[str, Any]) -> ConfigValidationResult:
        """Validate RAG configuration and return results with errors and warnings."""
        errors: list[str] = []
        warnings: list[str] = []

        rag = (
            cfg["rag"] if "rag" in cfg else cfg
        )  # Normalize: nested {"rag": {...}} (agent.toml) and flat {...} (MCP module_cfg) both supported

        # Embedding dimension consistency
        embed_dim = rag.get("embedding_dim")
        vec_dim = rag.get("vec_dim")
        if embed_dim and vec_dim and embed_dim != vec_dim:
            errors.append(f"embedding_dim={embed_dim} != vec_dim={vec_dim}")

        # use_rrf=False warning
        if not rag.get("use_rrf", True):
            warnings.append(
                "use_rrf=false degrades retrieval quality; use only for diagnostics"
            )

        # Semantic cache threshold sanity
        threshold = rag.get("semantic_cache_threshold", 0.92)
        if threshold < 0.5:
            warnings.append(f"semantic_cache_threshold={threshold} is unusually low")

        # Semantic cache max_size validation (negative values are always invalid)
        max_size = rag.get("semantic_cache_max_size", 100)
        if max_size < 0:
            errors.append(
                f"semantic_cache_max_size={max_size} is negative; must be >= 0"
            )

        return ConfigValidationResult(errors=errors, warnings=warnings)
