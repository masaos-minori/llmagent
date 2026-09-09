"""scripts/rag/config_resolution.py

Extracted from scripts/rag/pipeline.py — resolve_rag_config().

Provides configuration resolution with priority ordering:
  CLI args > env vars > YAML config > defaults.
"""

import logging
from collections.abc import Callable
from typing import Any

from shared.config_loader import ConfigLoader
from shared.config_validator import RagConfigValidator
from shared.types import RagConfig

from rag.models_config import RagConfigImpl

logger = logging.getLogger(__name__)

# All fields that must be present in the resolved config.
_ALL_FIELDS = frozenset(
    {
        "use_mqe",
        "top_k_search",
        "use_rerank",
        "rag_top_k",
        "max_chunks_per_doc",
        "top_k_rerank",
        "rag_min_score",
        "use_rrf",
        "rrf_k",
        "use_search",
        "rag_service_url",
        "rag_auth_token",
        "use_refiner",
        "refiner_max_tokens",
        "refiner_max_chars_per_chunk",
        "refiner_timeout",
        "llm_url",
        "embed_url",
        "rag_db_path",
        "sqlite_vec_so",
        "sqlite_timeout",
        "sqlite_busy_timeout_ms",
        "embed_retry",
        "embed_workers",
        "rag_pipeline_service_url",
        "mqe_prompt_template",
        "mqe_n_queries",
        "rerank_prompt_template",
    }
)

_DEFAULTS_FOR_ALL = {
    "use_mqe": False,
    "top_k_search": 5,
    "use_rerank": False,
    "rag_top_k": 3,
    "max_chunks_per_doc": 5,
    "top_k_rerank": 10,
    "rag_min_score": 0.0,
    "use_rrf": True,
    "rrf_k": 60,
    "use_search": True,
    "rag_service_url": None,
    "rag_auth_token": None,
    "use_refiner": False,
    "refiner_max_tokens": 512,
    "refiner_max_chars_per_chunk": 800,
    "refiner_timeout": 30.0,
    "llm_url": "",
    "embed_url": "",
    "rag_db_path": ":memory:",
    "sqlite_vec_so": "/opt/llm/sqlite-vec/vec0.so",
    "sqlite_timeout": 5,
    "sqlite_busy_timeout_ms": 5000,
    "embed_retry": 3,
    "embed_workers": 4,
    "rag_pipeline_service_url": None,
    "mqe_prompt_template": "Expand query: {query}",
    "mqe_n_queries": 3,
    "rerank_prompt_template": "Rerank results for: {query}",
}


def resolve_rag_config(
    cfg: RagConfig,
    *,
    module_cfg: dict | None = None,
    config_loader: Callable[[], dict[str, Any]] | None = None,
) -> RagConfigImpl:
    """Resolve RAG configuration from multiple sources with priority ordering.

    Priority order:
      1. cfg if already a RagConfigImpl (returned directly)
      2. cfg as dict (used as-is)
      3. cfg as object with __dict__ (converted to dict)
      4. module_cfg passed explicitly
      5. config_loader() callable (defaults to ConfigLoader().load_all())

    When config_loader raises FileNotFoundError or ValueError, returns empty dict
    as fallback (same behavior as the removed _ModuleConfig.get()).

    Returns a validated RagConfigImpl populated with defaults for any missing fields.
    """
    if isinstance(cfg, RagConfigImpl):
        return cfg

    _raw_cfg: dict[str, Any] = {}
    if isinstance(cfg, dict):
        _raw_cfg = cfg
    elif cfg is not None and hasattr(cfg, "__dict__"):
        _raw_cfg = cfg.__dict__
    else:
        if config_loader is None:
            try:
                config_loader = lambda: ConfigLoader().load_all()  # noqa: E731 — closure capture requires lambda; cannot use def inside try block
            except (FileNotFoundError, ValueError):
                _raw_cfg = {}
        if not _raw_cfg and config_loader is not None:
            try:
                _raw_cfg = config_loader()
            except (FileNotFoundError, ValueError):
                _raw_cfg = {}
                config_loader = None
        if not _raw_cfg:
            _raw_cfg = module_cfg if module_cfg is not None else {}

    for k in _ALL_FIELDS:
        if k not in _raw_cfg:
            _raw_cfg[k] = _DEFAULTS_FOR_ALL[k]
    # Only pass known fields to RagConfigImpl; ignore extras from config loader
    filtered_cfg = {k: v for k, v in _raw_cfg.items() if k in _ALL_FIELDS}
    validator = RagConfigValidator()
    validation_result = validator.validate(filtered_cfg)
    for warning in validation_result.warnings:
        logger.warning("rag config warning: %s", warning)
    for error in validation_result.errors:
        logger.error("rag config error: %s", error)
    if not validation_result.ok:
        raise ValueError(f"RAG config validation failed: {validation_result.errors}")
    return RagConfigImpl(**filtered_cfg)
