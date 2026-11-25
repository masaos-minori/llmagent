"""scripts/agent/services/config_validators.py

Validation functions extracted from config_dataclasses.py __post_init__ methods.

Each function validates a single field or cross-field invariant on its
corresponding dataclass instance.  The dataclass module imports these at
runtime so the original API surface stays unchanged.

Every validator composes the declared type rule from shared.config_field_types
before its range rule (REQ-001), so the reload path rejects a wrong-typed value
with the same message the startup builders produce.  A type-rule error names the
field path and the rule and never includes the configured value, which can carry
a path or a token (REQ-011); the range rules keep their numeric wording because
the values they echo are numbers, not secrets.

The field path is the config key name, the same string ``typed_validators``
passes to the primitives, because registry field names are unique across sections
and identical text on both paths is what AC-1 pins.
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any

from cryptography.fernet import Fernet
from shared.config_field_types import (
    strict_bool,
    strict_float,
    strict_int,
    strict_str,
    strict_str_list,
)

if TYPE_CHECKING:
    from agent.config_dataclasses import (
        ApprovalConfig,
        DiagnosticsConfig,
        LLMConfig,
        MemoryConfig,
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
    """Validate that context_char_limit is a non-negative int."""
    _require_non_negative(
        "context_char_limit",
        strict_int(cfg.context_char_limit, "context_char_limit"),
    )


def validate_llm_budget_warn_ratio(cfg: LLMConfig) -> None:
    """Validate that budget_warn_ratio is in (0.0, 1.0]."""
    ratio = strict_float(cfg.budget_warn_ratio, "budget_warn_ratio")
    if not 0.0 < ratio <= 1.0:
        raise ValueError("budget_warn_ratio must be in (0.0, 1.0]")


def validate_llm_retry_base_delay(cfg: LLMConfig) -> None:
    """Validate that llm_retry_base_delay is positive."""
    _require_positive(
        "llm_retry_base_delay",
        strict_float(cfg.llm_retry_base_delay, "llm_retry_base_delay"),
    )


def validate_llm_temperature(cfg: LLMConfig) -> None:
    """Validate that llm_temperature is in [0.0, LLM_TEMPERATURE_MAX]."""
    temperature = strict_float(cfg.llm_temperature, "llm_temperature")
    if not 0.0 <= temperature <= LLM_TEMPERATURE_MAX:
        raise ValueError(
            f"llm_temperature must be in [0.0, {LLM_TEMPERATURE_MAX}], got {temperature}"
        )


def validate_llm_max_tokens(cfg: LLMConfig) -> None:
    """Validate that llm_max_tokens is at least 1."""
    _require_at_least(
        "llm_max_tokens", strict_int(cfg.llm_max_tokens, "llm_max_tokens"), 1
    )


def validate_llm_sse_heartbeat_timeout(cfg: LLMConfig) -> None:
    """Validate that sse_heartbeat_timeout is non-negative."""
    _require_non_negative(
        "sse_heartbeat_timeout",
        strict_float(cfg.sse_heartbeat_timeout, "sse_heartbeat_timeout"),
    )


def validate_llm_sse_malformed_retry(cfg: LLMConfig) -> None:
    """Validate that sse_malformed_retry is a non-negative int."""
    _require_non_negative(
        "sse_malformed_retry",
        strict_int(cfg.sse_malformed_retry, "sse_malformed_retry"),
    )


def validate_llm_sse_reconnect_max(cfg: LLMConfig) -> None:
    """Validate that sse_reconnect_max is a non-negative int."""
    _require_non_negative(
        "sse_reconnect_max", strict_int(cfg.sse_reconnect_max, "sse_reconnect_max")
    )


_AGENT_REFINER_KEYS = (
    "use_refiner",
    "refiner_max_tokens",
    "refiner_timeout",
    "refiner_max_chars_per_chunk",
)


def check_agent_refiner_keys(raw_cfg: Mapping[str, Any]) -> list[str]:
    """Return an error when config/agent.toml still carries refiner keys.

    The refiner runs inside the rag-pipeline MCP server and is configured only in
    config/rag_pipeline_mcp_server.toml (ADR-002); an Agent-side value would be
    silently ignored.
    """
    found = [k for k in _AGENT_REFINER_KEYS if k in raw_cfg]
    if not found:
        return []
    return [
        f"config/agent.toml: {', '.join(found)} is not an Agent setting; "
        "the refiner is configured in config/rag_pipeline_mcp_server.toml"
    ]


def validate_tool_dedup_max_repeats(cfg: ToolConfig) -> None:
    """Validate that tool_dedup_max_repeats is at least 1."""
    _require_at_least(
        "tool_dedup_max_repeats",
        strict_int(cfg.tool_dedup_max_repeats, "tool_dedup_max_repeats"),
        1,
    )


def validate_tool_cycle_detect_window(cfg: ToolConfig) -> None:
    """Validate that tool_cycle_detect_window is a non-negative int."""
    _require_non_negative(
        "tool_cycle_detect_window",
        strict_int(cfg.tool_cycle_detect_window, "tool_cycle_detect_window"),
    )


def validate_tool_error_max_consecutive(cfg: ToolConfig) -> None:
    """Validate that tool_error_max_consecutive is a non-negative int."""
    _require_non_negative(
        "tool_error_max_consecutive",
        strict_int(cfg.tool_error_max_consecutive, "tool_error_max_consecutive"),
    )


def validate_tool_error_retry_max(cfg: ToolConfig) -> None:
    """Validate that tool_error_retry_max is a non-negative int."""
    _require_non_negative(
        "tool_error_retry_max",
        strict_int(cfg.tool_error_retry_max, "tool_error_retry_max"),
    )


def validate_progress_stagnation_window(cfg: ToolConfig) -> None:
    """Validate that progress_stagnation_window is a non-negative int."""
    _require_non_negative(
        "progress_stagnation_window",
        strict_int(cfg.progress_stagnation_window, "progress_stagnation_window"),
    )


def validate_allowed_tools(cfg: ToolConfig) -> None:
    """Validate that allowed_tools is a list of strings (an empty list is valid)."""
    strict_str_list(cfg.allowed_tools, "allowed_tools", allow_empty=True)


def validate_tool_policy_mode(cfg: ToolConfig) -> None:
    """Validate that tool_policy_mode is one of the allowed enum values."""
    strict_str(cfg.tool_policy_mode, "tool_policy_mode")
    if cfg.tool_policy_mode not in {"discovered", "explicit_allowlist"}:
        raise ValueError(
            "tool_policy_mode must be 'discovered' or 'explicit_allowlist'"
        )


def validate_disabled_tools(cfg: ToolConfig) -> None:
    """Validate that disabled_tools is a list of registered tool names."""
    tools = strict_str_list(cfg.disabled_tools, "disabled_tools", allow_empty=True)
    try:
        from shared.tool_registry import get_registry

        known = set(get_registry().get_all_tool_names())
    except ImportError as exc:
        msg = (
            "Tool registry resolution failed: cannot determine authoritative "
            "tool set for disabled_tools validation"
        )
        raise ValueError(msg) from exc
    unknown = [t for t in tools if t not in known]
    if unknown:
        raise ValueError(
            f"disabled_tools references unregistered tool names: {unknown!r}"
        )


def validate_memory_fts_limit(cfg: MemoryConfig) -> None:
    """Validate that memory_fts_limit is at least 1."""
    _require_at_least(
        "memory_fts_limit",
        strict_int(cfg.memory_fts_limit, "memory_fts_limit"),
        1,
    )


def validate_memory_rrf_k(cfg: MemoryConfig) -> None:
    """Validate that memory_rrf_k is at least 1."""
    _require_at_least("memory_rrf_k", strict_int(cfg.memory_rrf_k, "memory_rrf_k"), 1)


def validate_memory_recency_days(cfg: MemoryConfig) -> None:
    """Validate that memory_recency_days is positive."""
    _require_positive(
        "memory_recency_days",
        strict_float(cfg.memory_recency_days, "memory_recency_days"),
    )


def validate_memory_max_inject_semantic(cfg: MemoryConfig) -> None:
    """Validate that memory_max_inject_semantic is a non-negative int."""
    _require_non_negative(
        "memory_max_inject_semantic",
        strict_int(cfg.memory_max_inject_semantic, "memory_max_inject_semantic"),
    )


def validate_memory_max_inject_episodic(cfg: MemoryConfig) -> None:
    """Validate that memory_max_inject_episodic is a non-negative int."""
    _require_non_negative(
        "memory_max_inject_episodic",
        strict_int(cfg.memory_max_inject_episodic, "memory_max_inject_episodic"),
    )


def validate_memory_embed_timeout_sec(cfg: MemoryConfig) -> None:
    """Validate that memory_embed_timeout_sec is positive."""
    _require_positive(
        "memory_embed_timeout_sec",
        strict_float(cfg.memory_embed_timeout_sec, "memory_embed_timeout_sec"),
    )


def validate_memory_retention_days(cfg: MemoryConfig) -> None:
    """Validate that memory_retention_days is at least 1."""
    _require_at_least(
        "memory_retention_days",
        strict_int(cfg.memory_retention_days, "memory_retention_days"),
        1,
    )


def validate_memory_max_pinned(cfg: MemoryConfig) -> None:
    """Validate that memory_max_pinned is at least 1."""
    _require_at_least(
        "memory_max_pinned",
        strict_int(cfg.memory_max_pinned, "memory_max_pinned"),
        1,
    )


def validate_diagnostics_encryption_key(cfg: DiagnosticsConfig) -> None:
    """Validate encryption_key is a valid Fernet key when configured (empty = disabled)."""
    key = strict_str(cfg.encryption_key, "encryption_key", allow_empty=True)
    if not key:
        return
    try:
        Fernet(key.encode("utf-8"))
    except (ValueError, TypeError) as exc:
        raise ValueError(f"encryption_key is not a valid Fernet key: {exc}") from exc


def validate_diagnostics_retention_days(cfg: DiagnosticsConfig) -> None:
    """Validate retention_days is an int (<= 0 disables purge).

    The rule is the shared int rule (bool rejected); the wording is kept because
    ``tests/agent/test_config_dataclasses.py`` pins it and the field is not a
    registry entry, so the parity contract does not reach it.
    """
    if isinstance(cfg.retention_days, bool) or not isinstance(cfg.retention_days, int):
        raise ValueError(
            f"retention_days must be an int, got {type(cfg.retention_days).__name__}"
        )


def validate_diagnostics_sensitive_fields(cfg: DiagnosticsConfig) -> None:
    """Validate sensitive_fields is a frozenset of strings."""
    fields = cfg.sensitive_fields
    if not isinstance(fields, frozenset) or not all(
        isinstance(field, str) for field in fields
    ):
        raise ValueError("sensitive_fields must be a frozenset of strings")


def validate_allowed_root(cfg: ApprovalConfig) -> None:
    """Validate that allowed_root is a non-empty absolute path.

    An empty value would disable the path jail.
    """
    root = strict_str(cfg.allowed_root, "allowed_root", allow_empty=True)
    if not root.strip():
        raise ValueError(
            "allowed_root must not be empty; an empty value disables the path jail"
        )
    if not os.path.isabs(root):
        raise ValueError("allowed_root must be an absolute path")


def validate_llm_http_timeout(cfg: LLMConfig) -> None:
    """Validate that http_timeout is positive."""
    _require_positive("http_timeout", strict_float(cfg.http_timeout, "http_timeout"))


def validate_llm_context_token_limit(cfg: LLMConfig) -> None:
    """Validate that context_token_limit is a non-negative int."""
    _require_non_negative(
        "context_token_limit",
        strict_int(cfg.context_token_limit, "context_token_limit"),
    )


def validate_tool_max_tool_turns(cfg: ToolConfig) -> None:
    """Validate that max_tool_turns is positive."""
    _require_positive(
        "max_tool_turns", strict_int(cfg.max_tool_turns, "max_tool_turns")
    )


def validate_tool_result_max_llm_chars(cfg: ToolConfig) -> None:
    """Validate that tool_result_max_llm_chars is positive."""
    _require_positive(
        "tool_result_max_llm_chars",
        strict_int(cfg.tool_result_max_llm_chars, "tool_result_max_llm_chars"),
    )


# Validators for the registry entries that had none (REQ-010). They are named
# after the field they validate, matching the existing convention.


def validate_llm_url(cfg: LLMConfig) -> None:
    """Validate that llm_url is a string (an empty value means no LLM endpoint)."""
    strict_str(cfg.llm_url, "llm_url", allow_empty=True)


def validate_context_compress_turns(cfg: LLMConfig) -> None:
    """Validate that context_compress_turns is an int.

    No range rule is added: the strictness this Plan publishes for this field is
    the type rule, not a new range.
    """
    strict_int(cfg.context_compress_turns, "context_compress_turns")


def validate_llm_stream_retry_on_heartbeat_timeout(cfg: LLMConfig) -> None:
    """Validate that llm_stream_retry_on_heartbeat_timeout is a bool."""
    strict_bool(
        cfg.llm_stream_retry_on_heartbeat_timeout,
        "llm_stream_retry_on_heartbeat_timeout",
    )


def validate_llm_stream_retry_on_malformed_chunk(cfg: LLMConfig) -> None:
    """Validate that llm_stream_retry_on_malformed_chunk is a bool."""
    strict_bool(
        cfg.llm_stream_retry_on_malformed_chunk,
        "llm_stream_retry_on_malformed_chunk",
    )


def validate_serial_tool_calls(cfg: ToolConfig) -> None:
    """Validate that serial_tool_calls is a bool."""
    strict_bool(cfg.serial_tool_calls, "serial_tool_calls")


def validate_plan_blocked_tools(cfg: ToolConfig) -> None:
    """Validate that plan_blocked_tools is a list of strings (an empty list is valid)."""
    strict_str_list(cfg.plan_blocked_tools, "plan_blocked_tools", allow_empty=True)


def validate_approval_protected_paths(cfg: ApprovalConfig) -> None:
    """Validate that approval_protected_paths is a list of strings (an empty list is valid)."""
    strict_str_list(
        cfg.approval_protected_paths,
        "approval_protected_paths",
        allow_empty=True,
    )


def validate_approval_high_risk_branches(cfg: ApprovalConfig) -> None:
    """Validate that approval_high_risk_branches is a list of strings (an empty list is valid)."""
    strict_str_list(
        cfg.approval_high_risk_branches,
        "approval_high_risk_branches",
        allow_empty=True,
    )


def validate_approval_shell_safe_prefixes(cfg: ApprovalConfig) -> None:
    """Validate that approval_shell_safe_prefixes is a list of strings.

    ``allow_empty`` applies at both levels: the tool policy skips an empty or
    whitespace-only prefix instead of failing startup, which
    ``tests/agent/test_tool_policy.py`` pins.
    """
    strict_str_list(
        cfg.approval_shell_safe_prefixes,
        "approval_shell_safe_prefixes",
        allow_empty=True,
    )


def validate_approval_github_allowed_repos(cfg: ApprovalConfig) -> None:
    """Validate that approval_github_allowed_repos is a list of strings (an empty list is valid)."""
    strict_str_list(
        cfg.approval_github_allowed_repos,
        "approval_github_allowed_repos",
        allow_empty=True,
    )


def validate_gitops_push_blocked(cfg: ApprovalConfig) -> None:
    """Validate that gitops_push_blocked is a bool."""
    strict_bool(cfg.gitops_push_blocked, "gitops_push_blocked")


def validate_approval_medium_preview_fallback(cfg: ApprovalConfig) -> None:
    """Validate that approval_medium_preview_fallback is a bool."""
    strict_bool(
        cfg.approval_medium_preview_fallback,
        "approval_medium_preview_fallback",
    )


def validate_memory_local_only(cfg: MemoryConfig) -> None:
    """Validate that memory_local_only is a bool."""
    strict_bool(cfg.memory_local_only, "memory_local_only")


def validate_use_memory_layer(cfg: MemoryConfig) -> None:
    """Validate that use_memory_layer is a bool."""
    strict_bool(cfg.use_memory_layer, "use_memory_layer")


def validate_memory_embed_enabled(cfg: MemoryConfig) -> None:
    """Validate that memory_embed_enabled is a bool."""
    strict_bool(cfg.memory_embed_enabled, "memory_embed_enabled")


def validate_memory_embed_url(cfg: MemoryConfig) -> None:
    """Validate that memory_embed_url is a string.

    An empty value is a type-level pass: the cross-field rule that requires a
    non-empty endpoint when embedding is enabled lives in
    ``MemoryConfig.__post_init__``.
    """
    strict_str(cfg.memory_embed_url, "memory_embed_url", allow_empty=True)
