# Implementation Procedure: scripts/shared/config_validator.py + scripts/rag/pipeline.py

## Goal

起動時に RAG 設定の cross-file 整合性を検証する `RagConfigValidator` を実装する。

## Scope

**In:**
- 新規 `scripts/shared/config_validator.py` — `RagConfigValidator`, `ConfigValidationResult`
- `scripts/rag/pipeline.py` — `__init__` でバリデーター呼び出し
- 新規 `tests/test_config_validator.py`

**Out:** config ファイルレイアウトの再設計

## Implementation

### scripts/shared/config_validator.py

```python
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
            warnings.append(
                f"semantic_cache_threshold={threshold} is unusually low"
            )

        return ConfigValidationResult(errors=errors, warnings=warnings)
```

### pipeline.py — __init__ でバリデーター呼び出し

```python
from shared.config_validator import RagConfigValidator

# In RagPipeline.__init__:
validator = RagConfigValidator()
result = validator.validate(cfg_dict)
for warning in result.warnings:
    logger.warning("rag config warning: %s", warning)
for error in result.errors:
    logger.error("rag config error: %s", error)
if not result.ok:
    raise ValueError(f"RAG config validation failed: {result.errors}")
```

## Validation plan

| Check | Command | Expected |
|---|---|---|
| ファイル存在 | `ls scripts/shared/config_validator.py` | found |
| Tests | `uv run pytest tests/test_config_validator.py -x -q` | all pass |
| Lint | `uv run ruff check scripts/shared/config_validator.py` | 0 errors |
