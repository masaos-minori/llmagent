"""shared/config_validator.py — Startup validator for RAG config cross-file consistency."""

from __future__ import annotations

import dataclasses
from typing import Any


@dataclasses.dataclass
class ConfigValidationResult:
    errors: list[str]
    warnings: list[str]

    @property
    def ok(self) -> bool:
        return len(self.errors) == 0


class RagConfigValidator:
    def validate(self, cfg: dict[str, Any]) -> ConfigValidationResult:
        errors: list[str] = []
        warnings: list[str] = []

        rag = cfg.get("rag", {})

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

        return ConfigValidationResult(errors=errors, warnings=warnings)
