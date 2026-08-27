"""scripts/agent/services/config_validators.py

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


def _require_non_negative(name: str, value: float) -> None:
    """Require value >= 0."""
    if value < 0:
        raise ValueError(f"{name} must be >= 0, got {value}")


def _require_at_least(name: str, value: float, minimum: float) -> None:
    """Require value >= minimum."""
    if value < minimum:
        raise ValueError(f"{name} must be >= {minimum}, got {value}")


def _require_positive(name: str, value: float) -> None:
    """Require value > 0."""
    if value <= 0:
        raise ValueError(f"{name} must be > 0, got {value}")


def validate_llm_context_char_limit(cfg: LLMConfig) -> None:
    """Validate that context_char_limit is non-negative."""
    _require_non_negative("context_char_limit", cfg.context_char_limit)


def validate_llm_budget_warn_ratio(cfg: LLMConfig) -> None:
    """Validate that budget_warn_ratio is in (0.0, 1.0]."""
    if not 0.0 < cfg.budget_warn_ratio <= 1.0:
        raise ValueError(
            f"budget_warn_ratio must be in (0.0, 1.0], got {cfg.budget_warn_ratio}",
        )


def validate_llm_max_retries(cfg: LLMConfig) -> None:
    """Validate that llm_max_retries is non-negative."""
    _require_non_negative("llm_max_retries", cfg.llm_max_retries)


def validate_llm_retry_base_delay(cfg: LLMConfig) -> None:
    """Validate that llm_retry_base_delay is positive."""
    _require_positive("llm_retry_base_delay", cfg.llm_retry_base_delay)


def validate_llm_temperature(cfg: LLMConfig) -> None:
    """Validate that llm_temperature is in [0.0, LLM_TEMPERATURE_MAX]."""
    if not 0.0 <= cfg.llm_temperature <= LLM_TEMPERATURE_MAX:
        raise ValueError(
            f"llm_temperature must be in [0.0, {LLM_TEMPERATURE_MAX}], got {cfg.llm_temperature}"
        )


def validate_llm_max_tokens(cfg: LLMConfig) -> None:
    """Validate that llm_max_tokens is at least 1."""
    _require_at_least("llm_max_tokens", cfg.llm_max_tokens, 1)


def validate_llm_sse_heartbeat_timeout(cfg: LLMConfig) -> None:
    """Validate that sse_heartbeat_timeout is non-negative."""
    _require_non_negative("sse_heartbeat_timeout", cfg.sse_heartbeat_timeout)


def validate_llm_sse_malformed_retry(cfg: LLMConfig) -> None:
    """Validate that sse_malformed_retry is non-negative."""
    _require_non_negative("sse_malformed_retry", cfg.sse_malformed_retry)


def validate_llm_sse_reconnect_max(cfg: LLMConfig) -> None:
    """Validate that sse_reconnect_max is non-negative."""
    _require_non_negative("sse_reconnect_max", cfg.sse_reconnect_max)


def validate_rag_refiner_max_tokens(cfg: RAGConfig) -> None:
    """Validate that refiner_max_tokens is at least 1."""
    _require_at_least("refiner_max_tokens", cfg.refiner_max_tokens, 1)


def validate_rag_refiner_timeout(cfg: RAGConfig) -> None:
    """Validate that refiner_timeout is positive."""
    _require_positive("refiner_timeout", cfg.refiner_timeout)


def validate_rag_refiner_max_chars_per_chunk(cfg: RAGConfig) -> None:
    """Validate that refiner_max_chars_per_chunk is at least 1."""
    _require_at_least("refiner_max_chars_per_chunk", cfg.refiner_max_chars_per_chunk, 1)


def validate_tool_dedup_max_repeats(cfg: ToolConfig) -> None:
    """Validate that tool_dedup_max_repeats is at least 1."""
    _require_at_least("tool_dedup_max_repeats", cfg.tool_dedup_max_repeats, 1)


def validate_tool_cycle_detect_window(cfg: ToolConfig) -> None:
    """Validate that tool_cycle_detect_window is non-negative."""
    _require_non_negative("tool_cycle_detect_window", cfg.tool_cycle_detect_window)


def validate_tool_error_max_consecutive(cfg: ToolConfig) -> None:
    """Validate that tool_error_max_consecutive is non-negative."""
    _require_non_negative("tool_error_max_consecutive", cfg.tool_error_max_consecutive)


def validate_tool_error_retry_max(cfg: ToolConfig) -> None:
    """Validate that tool_error_retry_max is non-negative."""
    _require_non_negative("tool_error_retry_max", cfg.tool_error_retry_max)


def validate_progress_stagnation_window(cfg: ToolConfig) -> None:
    """Validate that progress_stagnation_window is non-negative."""
    _require_non_negative("progress_stagnation_window", cfg.progress_stagnation_window)


def validate_memory_fts_limit(cfg: MemoryConfig) -> None:
    """Validate that memory_fts_limit is at least 1."""
    _require_at_least("memory_fts_limit", cfg.memory_fts_limit, 1)


def validate_memory_rrf_k(cfg: MemoryConfig) -> None:
    """Validate that memory_rrf_k is at least 1."""
    _require_at_least("memory_rrf_k", cfg.memory_rrf_k, 1)


def validate_memory_recency_days(cfg: MemoryConfig) -> None:
    """Validate that memory_recency_days is positive."""
    _require_positive("memory_recency_days", cfg.memory_recency_days)


def validate_memory_max_inject_semantic(cfg: MemoryConfig) -> None:
    """Validate that memory_max_inject_semantic is non-negative."""
    _require_non_negative("memory_max_inject_semantic", cfg.memory_max_inject_semantic)


def validate_memory_max_inject_episodic(cfg: MemoryConfig) -> None:
    """Validate that memory_max_inject_episodic is non-negative."""
    _require_non_negative("memory_max_inject_episodic", cfg.memory_max_inject_episodic)


def validate_memory_embed_timeout_sec(cfg: MemoryConfig) -> None:
    """Validate that memory_embed_timeout_sec is positive."""
    _require_positive("memory_embed_timeout_sec", cfg.memory_embed_timeout_sec)


def validate_memory_retention_days(cfg: MemoryConfig) -> None:
    """Validate that memory_retention_days is at least 1."""
    _require_at_least("memory_retention_days", cfg.memory_retention_days, 1)


def validate_approval_risk_rules(cfg: ApprovalConfig) -> None:
    """Validate that all approval_risk_rules values are valid."""
    _valid_risk = {"none", "medium", "high"}
    bad = {k: v for k, v in cfg.approval_risk_rules.items() if v not in _valid_risk}
    if bad:
        raise ValueError(
            f"approval_risk_rules: invalid levels {bad}; must be 'none', 'medium', or 'high'"
        )


def validate_tool_safety_tiers(cfg: ApprovalConfig) -> None:
    """Validate that all tool_safety_tiers values are valid."""
    _valid_tiers = {"READ_ONLY", "WRITE_SAFE", "WRITE_DANGEROUS", "ADMIN"}
    bad_tiers = {
        k: v for k, v in cfg.tool_safety_tiers.items() if v not in _valid_tiers
    }
    if bad_tiers:
        raise ValueError(
            f"tool_safety_tiers: invalid tier values {bad_tiers};"
            " must be READ_ONLY, WRITE_SAFE, WRITE_DANGEROUS, or ADMIN"
        )


def validate_llm_http_timeout(cfg: LLMConfig) -> None:
    """Validate that http_timeout is positive."""
    _require_positive("http_timeout", cfg.http_timeout)


def validate_llm_context_token_limit(cfg: LLMConfig) -> None:
    """Validate that context_token_limit is non-negative."""
    _require_non_negative("context_token_limit", cfg.context_token_limit)


def validate_tool_max_tool_turns(cfg: ToolConfig) -> None:
    """Validate that max_tool_turns is positive."""
    _require_positive("max_tool_turns", cfg.max_tool_turns)


def validate_tool_result_max_llm_chars(cfg: ToolConfig) -> None:
    """Validate that tool_result_max_llm_chars is positive."""
    _require_positive("tool_result_max_llm_chars", cfg.tool_result_max_llm_chars)
