"""scripts/rag/config_resolution.py — Provides configuration resolution with priority ordering:
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
    "use_search": False,
    "use_refiner": False,
    "refiner_max_tokens": 512,
    "refiner_max_chars_per_chunk": 800,
    "refiner_timeout": 30.0,
    "llm_url": "",
    "embed_url": "",
    "rag_db_path": "",
    "sqlite_vec_so": "/opt/llm/sqlite-vec/vec0.so",
    "sqlite_timeout": 5,
    "sqlite_busy_timeout_ms": 5000,
    "embed_retry": 3,
    "embed_workers": 4,
    "mqe_prompt_template": "Expand query: {query}",
    "mqe_n_queries": 3,
    "rerank_prompt_template": "Rerank results for: {query}",
}


def _load_raw_cfg(
    cfg: RagConfig,
    module_cfg: dict | None,
    config_loader: Callable[[], dict[str, Any]] | None,
) -> dict[str, Any]:
    """Layer the raw config source into a new dict and return it.

    For a dict or object ``cfg`` the passed ``module_cfg`` values are the base and
    the caller's ``cfg`` values win; for ``None`` cfg delegates to
    `_load_from_loader`. Never mutates the caller's dict, its ``__dict__``,
    ``module_cfg``, or the loader's returned dict.
    """
    module = module_cfg or {}
    if isinstance(cfg, dict):
        return {**module, **cfg}
    if cfg is not None and hasattr(cfg, "__dict__"):
        return {**module, **vars(cfg)}
    return _load_from_loader(config_loader, module)


def _load_from_loader(
    config_loader: Callable[[], dict[str, Any]] | None,
    module: dict[str, Any],
) -> dict[str, Any]:
    """Load raw config via ``config_loader``, falling back to ``module``.

    Defaults to the config loader when none is passed; on a loader error yields an
    empty dict, and an empty result falls back to a copy of ``module``.
    """
    if config_loader is None:
        config_loader = lambda: ConfigLoader().load_all()  # noqa: E731 — closure capture requires lambda; cannot use def inside try block
    try:
        raw = config_loader()
    except (FileNotFoundError, ValueError):
        raw = {}
    if not raw:
        raw = dict(module)
    return raw


def _apply_defaults(raw: dict[str, Any]) -> dict[str, Any]:
    """Fill missing keys from defaults and keep only known fields.

    Returns a new dict keyed by ``_ALL_FIELDS``: each field is ``raw[k]`` when the
    caller supplied it, otherwise the built-in default. Unknown keys are dropped.
    """
    return {k: raw[k] if k in raw else _DEFAULTS_FOR_ALL[k] for k in _ALL_FIELDS}


def _require_search_fields(filtered_cfg: dict[str, Any]) -> None:
    """Raise when ``use_search=True`` and a required field is empty or ``None``.

    Checks ``rag_db_path``, ``llm_url``, ``embed_url`` in that order and names all
    empty fields together.
    """
    if not filtered_cfg.get("use_search", False):
        return
    empty_fields: list[str] = []
    for field_name in ("rag_db_path", "llm_url", "embed_url"):
        value = filtered_cfg.get(field_name)
        if value == "" or value is None:
            empty_fields.append(field_name)
    if empty_fields:
        raise ValueError(
            f"RAG config requires non-empty {', '.join(empty_fields)} "
            f"when use_search=True"
        )


def resolve_rag_config(
    cfg: RagConfig,
    *,
    module_cfg: dict | None = None,
    config_loader: Callable[[], dict[str, Any]] | None = None,
) -> RagConfigImpl:
    """Resolve RAG configuration from multiple sources with priority ordering.

    Priority order:
      1. cfg if already a RagConfigImpl (returned directly)
      2. cfg as dict (layered over module_cfg, then defaults)
      3. cfg as object with __dict__ (layered over module_cfg, then defaults)
      4. module_cfg passed explicitly (used for keys the caller omits)
      5. config_loader() callable (defaults to ConfigLoader().load_all())

    For a dict or object cfg the caller's values take precedence over module_cfg,
    which takes precedence over the built-in defaults; resolution writes into a new
    mapping and never mutates the caller's input. For a None cfg the config loader
    runs first and module_cfg is only a fallback.

    When config_loader raises FileNotFoundError or ValueError, returns empty dict
    as fallback (same behavior as the removed _ModuleConfig.get()).

    Returns a validated RagConfigImpl populated with defaults for any missing fields.

    Raises:
        ValueError: If ``use_search=True`` and any of ``rag_db_path``, ``llm_url``,
            ``embed_url`` is empty or ``None``.
    """
    if isinstance(cfg, RagConfigImpl):
        return cfg

    raw_cfg = _load_raw_cfg(cfg, module_cfg, config_loader)
    filtered_cfg = _apply_defaults(raw_cfg)
    validator = RagConfigValidator()
    # Validate the raw layered dict: _apply_defaults drops unknown keys, so a removed
    # key would never reach the validator after filtering.
    validation_result = validator.validate(raw_cfg)
    for warning in validation_result.warnings:
        logger.warning("rag config warning: %s", warning)
    for error in validation_result.errors:
        logger.error("rag config error: %s", error)
    if not validation_result.ok:
        raise ValueError(f"RAG config validation failed: {validation_result.errors}")
    _require_search_fields(filtered_cfg)
    return RagConfigImpl(**filtered_cfg)
