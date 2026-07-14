"""agent/services/config_validators.py

Validation functions extracted from config_dataclasses.py __post_init__ methods.

Each function validates a single field or cross-field invariant on its
corresponding dataclass instance.  The dataclass module imports these at
runtime so the original API surface stays unchanged.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agent.config_dataclasses import (
        ApprovalConfig,
        LLMConfig,
        MemoryConfig,
        RAGConfig,
        ToolConfig,
    )

# Re-exported constant so validators can reference it without circular import
LLM_TEMPERATURE_MAX = 2.0


def validate_llm_context_char_limit(cfg: LLMConfig) -> None:
    if cfg.context_char_limit < 0:
        raise ValueError(
            f"context_char_limit must be >= 0, got {cfg.context_char_limit}"
        )


def validate_llm_budget_warn_ratio(cfg: LLMConfig) -> None:
    if not 0.0 < cfg.budget_warn_ratio <= 1.0:
        raise ValueError(
            f"budget_warn_ratio must be in (0.0, 1.0], got {cfg.budget_warn_ratio}",
        )


def validate_llm_max_retries(cfg: LLMConfig) -> None:
    if cfg.llm_max_retries < 0:
        raise ValueError(f"llm_max_retries must be >= 0, got {cfg.llm_max_retries}")


def validate_llm_retry_base_delay(cfg: LLMConfig) -> None:
    if cfg.llm_retry_base_delay <= 0:
        raise ValueError(
            f"llm_retry_base_delay must be > 0, got {cfg.llm_retry_base_delay}"
        )


def validate_llm_temperature(cfg: LLMConfig) -> None:
    if not 0.0 <= cfg.llm_temperature <= LLM_TEMPERATURE_MAX:
        raise ValueError(
            f"llm_temperature must be in [0.0, {LLM_TEMPERATURE_MAX}], got {cfg.llm_temperature}"
        )


def validate_llm_max_tokens(cfg: LLMConfig) -> None:
    if cfg.llm_max_tokens < 1:
        raise ValueError(f"llm_max_tokens must be >= 1, got {cfg.llm_max_tokens}")


def validate_llm_sse_heartbeat_timeout(cfg: LLMConfig) -> None:
    if cfg.sse_heartbeat_timeout < 0:
        raise ValueError(
            f"sse_heartbeat_timeout must be >= 0, got {cfg.sse_heartbeat_timeout}"
        )


def validate_llm_sse_malformed_retry(cfg: LLMConfig) -> None:
    if cfg.sse_malformed_retry < 0:
        raise ValueError(
            f"sse_malformed_retry must be >= 0, got {cfg.sse_malformed_retry}"
        )


def validate_llm_sse_reconnect_max(cfg: LLMConfig) -> None:
    if cfg.sse_reconnect_max < 0:
        raise ValueError(f"sse_reconnect_max must be >= 0, got {cfg.sse_reconnect_max}")


def validate_rag_refiner_max_tokens(cfg: RAGConfig) -> None:
    if cfg.refiner_max_tokens < 1:
        raise ValueError(
            f"refiner_max_tokens must be >= 1, got {cfg.refiner_max_tokens}"
        )


def validate_rag_refiner_timeout(cfg: RAGConfig) -> None:
    if cfg.refiner_timeout <= 0:
        raise ValueError(f"refiner_timeout must be > 0, got {cfg.refiner_timeout}")


def validate_rag_refiner_max_chars_per_chunk(cfg: RAGConfig) -> None:
    if cfg.refiner_max_chars_per_chunk < 1:
        raise ValueError(
            f"refiner_max_chars_per_chunk must be >= 1,"
            f" got {cfg.refiner_max_chars_per_chunk}"
        )


def validate_tool_plugin_tool_override(cfg: ToolConfig) -> None:
    if not isinstance(cfg.plugin_tool_override, bool):
        raise ValueError(
            f"plugin_tool_override must be bool, "
            f"got {type(cfg.plugin_tool_override).__name__}"
        )


def validate_tool_plugin_strict(cfg: ToolConfig) -> None:
    if not isinstance(cfg.plugin_strict, bool):
        raise ValueError(
            f"plugin_strict must be bool, got {type(cfg.plugin_strict).__name__}"
        )


def validate_tool_dedup_max_repeats(cfg: ToolConfig) -> None:
    if cfg.tool_dedup_max_repeats < 1:
        raise ValueError(
            f"tool_dedup_max_repeats must be >= 1, got {cfg.tool_dedup_max_repeats}"
        )


def validate_tool_cycle_detect_window(cfg: ToolConfig) -> None:
    if cfg.tool_cycle_detect_window < 0:
        raise ValueError(
            f"tool_cycle_detect_window must be >= 0, got {cfg.tool_cycle_detect_window}"
        )


def validate_tool_error_max_consecutive(cfg: ToolConfig) -> None:
    if cfg.tool_error_max_consecutive < 0:
        raise ValueError(
            "tool_error_max_consecutive must be >= 0,"
            f" got {cfg.tool_error_max_consecutive}"
        )


def validate_tool_cache_max_size(cfg: ToolConfig) -> None:
    if cfg.tool_cache_max_size < 0:
        raise ValueError(
            f"tool_cache_max_size must be >= 0, got {cfg.tool_cache_max_size}"
        )


def validate_tool_error_retry_max(cfg: ToolConfig) -> None:
    if cfg.tool_error_retry_max < 0:
        raise ValueError(
            f"tool_error_retry_max must be >= 0, got {cfg.tool_error_retry_max}"
        )


def validate_memory_fts_limit(cfg: MemoryConfig) -> None:
    if cfg.memory_fts_limit < 1:
        raise ValueError(f"memory_fts_limit must be >= 1, got {cfg.memory_fts_limit}")


def validate_memory_rrf_k(cfg: MemoryConfig) -> None:
    if cfg.memory_rrf_k < 1:
        raise ValueError(f"memory_rrf_k must be >= 1, got {cfg.memory_rrf_k}")


def validate_memory_recency_days(cfg: MemoryConfig) -> None:
    if cfg.memory_recency_days <= 0:
        raise ValueError(
            f"memory_recency_days must be > 0, got {cfg.memory_recency_days}"
        )


def validate_approval_risk_rules(cfg: ApprovalConfig) -> None:
    _valid_risk = {"none", "medium", "high"}
    bad = {k: v for k, v in cfg.approval_risk_rules.items() if v not in _valid_risk}
    if bad:
        raise ValueError(
            f"approval_risk_rules: invalid levels {bad};"
            " must be 'none', 'medium', or 'high'"
        )


def validate_tool_safety_tiers(cfg: ApprovalConfig) -> None:
    _valid_tiers = {"READ_ONLY", "WRITE_SAFE", "WRITE_DANGEROUS", "ADMIN"}
    bad_tiers = {
        k: v for k, v in cfg.tool_safety_tiers.items() if v not in _valid_tiers
    }
    if bad_tiers:
        raise ValueError(
            f"tool_safety_tiers: invalid tier values {bad_tiers};"
            " must be READ_ONLY, WRITE_SAFE, WRITE_DANGEROUS, or ADMIN"
        )
