#!/usr/bin/env python3
"""scripts/agent/config_section_builders.py — Default-resolution helpers and per-section config builders.

Owns the key-reading half of agent config construction: `_or_default`,
`_get_or_default`, `_get_str_or_default`, `_validate_dry_run_tools`,
`_build_model`, and the `_build_*_config` functions for the llm, rag, tool,
memory, approval and diagnostics sections. `agent.config_builders` delegates to
them; the assembly entry point (`build_agent_config`, `load_config`,
`resolved_config_dir`) stays there.

Import from here:  from agent.config_section_builders import (
    _build_llm_config, _build_rag_config, _build_tool_config,
    _build_memory_config, _build_approval_config, _build_diagnostics_config,
)
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

from shared.config_validator import RagConfigValidator

from agent.config_dataclasses import (
    ApprovalConfig,
    DiagnosticsConfig,
    LLMConfig,
    MemoryConfig,
    RAGConfig,
    ToolConfig,
)
from agent.constants import (
    _DEFAULT_APPROVAL_RISK_RULES,
    _DEFAULT_DRY_RUN_TOOLS,
    _DEFAULT_PLAN_BLOCKED_TOOLS,
    _DEFAULT_PROTECTED_PATHS,
    _DEFAULT_RESOURCE_KEYS,
    _DEFAULT_SHELL_SAFE_PREFIXES,
)
from agent.services.config_validators import check_agent_refiner_keys
from agent.services.exceptions import ConfigReloadValidationError
from agent.services.typed_validators import (
    _get_bool,
    _get_dict,
    _get_float,
    _get_int,
    _get_list,
    _get_str,
)

logger = logging.getLogger(__name__)


def _or_default[T](value: T | None, default: T) -> T:
    """Return *default* when a config value supplies nothing.

    Nothing means an absent key (the typed getters report None) or an explicit
    empty string: every builder treats the two the same way.
    """
    if value is None or value == "":
        return default
    return value


def _get_or_default(
    cfg: dict[str, Any],
    key: str,
    getter: Callable[[dict[str, Any], str], Any],
    default: Any,
) -> Any:
    """Extract a value from cfg using *getter*, falling back to *default* when unset.

    Unset means the key is absent or the value is an empty string; see `_or_default`.
    """
    return _or_default(getter(cfg, key), default)


def _get_str_or_default(cfg: dict[str, Any], key: str, default: str = "") -> str:
    """Extract a str from cfg, falling back to *default* when the key is unset.

    Unset means absent or an explicit empty string, the same rule the
    `_get_str(cfg, key) or default` call sites used before they were folded here.
    """
    return _or_default(_get_str(cfg, key), default)


def _validate_dry_run_tools(tools: list[str]) -> list[str]:
    """Validate dry-run tools against known capabilities; warn on unsupported
    entries."""
    supported = set(_DEFAULT_DRY_RUN_TOOLS)
    filtered: list[str] = []
    for tool in tools:
        if tool not in supported:
            logger.warning("Dry-run tool '%s' is not supported; ignoring", tool)
        else:
            filtered.append(tool)
    return filtered


# ---------------------------------------------------------------------------
# Builder functions
# ---------------------------------------------------------------------------


def _build_model[T](model: type[T], **fields: Any) -> T:
    """Construct a config model, reporting a rejected value as ConfigReloadValidationError.

    Every builder reports a rejected value the same way. A pydantic ValidationError
    arrives as a plain ValueError, which the config-reload path cannot tell apart from
    any other ValueError; wrapping it names the failure the way the typed getters do.
    """
    try:
        return model(**fields)
    except ValueError as e:
        raise ConfigReloadValidationError(str(e)) from e


def _build_llm_config(cfg: dict[str, Any]) -> LLMConfig:
    """Build LLMConfig from a raw config dict."""
    return _build_model(
        LLMConfig,
        llm_url=_get_str_or_default(cfg, "llm_url"),
        http_timeout=_get_or_default(cfg, "http_timeout", _get_float, 30.0),
        llm_retry_base_delay=_get_or_default(
            cfg, "llm_retry_base_delay", _get_float, 1.0
        ),
        sse_heartbeat_timeout=_get_or_default(
            cfg, "sse_heartbeat_timeout", _get_float, 30.0
        ),
        sse_malformed_retry=_get_or_default(cfg, "sse_malformed_retry", _get_int, 2),
        sse_reconnect_max=_get_or_default(cfg, "sse_reconnect_max", _get_int, 1),
        llm_stream_retry_on_heartbeat_timeout=_get_or_default(
            cfg, "llm_stream_retry_on_heartbeat_timeout", _get_bool, True
        ),
        llm_stream_retry_on_malformed_chunk=_get_or_default(
            cfg, "llm_stream_retry_on_malformed_chunk", _get_bool, False
        ),
        llm_temperature=_get_or_default(cfg, "llm_temperature", _get_float, 0.2),
        llm_max_tokens=_get_or_default(cfg, "llm_max_tokens", _get_int, 1024),
        title_llm_temperature=_get_or_default(
            cfg, "title_llm_temperature", _get_float, 0.1
        ),
        title_llm_max_tokens=_get_or_default(cfg, "title_llm_max_tokens", _get_int, 20),
        llm_compress_temperature=_get_or_default(
            cfg, "llm_compress_temperature", _get_float, 0.3
        ),
        llm_compress_max_tokens=_get_or_default(
            cfg, "llm_compress_max_tokens", _get_int, 300
        ),
        tokenize_url=_get_str_or_default(cfg, "tokenize_url"),
        context_token_limit=_get_or_default(cfg, "context_token_limit", _get_int, 0),
        context_char_limit=_get_or_default(cfg, "context_char_limit", _get_int, 8000),
        context_compress_turns=_get_or_default(
            cfg, "context_compress_turns", _get_int, 4
        ),
        history_protect_turns=_get_or_default(
            cfg, "history_protect_turns", _get_int, 2
        ),
        budget_warn_ratio=_get_or_default(cfg, "budget_warn_ratio", _get_float, 0.8),
    )


def _build_rag_config(cfg: dict[str, Any]) -> RAGConfig:
    """Build RAGConfig from a raw config dict."""
    validator = RagConfigValidator()
    validation_result = validator.validate(cfg)
    for warning in validation_result.warnings:
        logger.warning("rag config warning: %s", warning)
    for error in validation_result.errors:
        logger.error("rag config error: %s", error)
    # Both rag-side sources are collected before raising, so one report names every
    # rejected key instead of only the first source that failed.
    errors = [*validation_result.errors, *check_agent_refiner_keys(cfg)]
    if errors:
        raise ConfigReloadValidationError(f"RAG config validation failed: {errors}")
    return _build_model(RAGConfig, embed_url=_get_str_or_default(cfg, "embed_url"))


def _build_tool_config(cfg: dict[str, Any], system_prompt_tool: str) -> ToolConfig:
    """Build ToolConfig from a raw config dict and system prompt template."""
    return _build_model(
        ToolConfig,
        serial_tool_calls=_get_or_default(cfg, "serial_tool_calls", _get_bool, False),
        tool_definitions_strict=_get_or_default(
            cfg, "tool_definitions_strict", _get_bool, False
        ),
        routing_drift_strict=_get_or_default(
            cfg, "routing_drift_strict", _get_bool, False
        ),
        tool_dedup_max_repeats=_get_or_default(
            cfg, "tool_dedup_max_repeats", _get_int, 3
        ),
        tool_cycle_detect_window=_get_or_default(
            cfg, "tool_cycle_detect_window", _get_int, 2
        ),
        tool_error_max_consecutive=_get_or_default(
            cfg, "tool_error_max_consecutive", _get_int, 3
        ),
        tool_error_retry_max=_get_or_default(cfg, "tool_error_retry_max", _get_int, 1),
        tool_concurrency_limits=_get_or_default(
            cfg, "tool_concurrency_limits", _get_dict, {}
        ),
        masked_fields=_get_or_default(
            cfg, "masked_fields", _get_list, ["content", "old_text", "new_text"]
        ),
        plan_blocked_tools=_get_or_default(
            cfg, "plan_blocked_tools", _get_list, list(_DEFAULT_PLAN_BLOCKED_TOOLS)
        ),
        max_tool_turns=_get_or_default(cfg, "max_tool_turns", _get_int, 5),
        tool_result_max_llm_chars=_get_or_default(
            cfg, "tool_result_max_llm_chars", _get_int, 8000
        ),
        tool_results_turn_max_chars=_get_or_default(
            cfg, "tool_results_turn_max_chars", _get_int, 50000
        ),
        tool_definitions=_get_or_default(cfg, "tool_definitions", _get_list, []),
        system_prompts=_get_or_default(
            cfg, "system_prompts", _get_dict, {"default": system_prompt_tool}
        ),
        system_prompt_tool=system_prompt_tool,
        allowed_tools=_get_or_default(cfg, "allowed_tools", _get_list, []),
    )


def _build_memory_config(cfg: dict[str, Any]) -> MemoryConfig:
    """Build MemoryConfig from a raw config dict."""
    use_memory_layer = _get_or_default(cfg, "use_memory_layer", _get_bool, True)
    memory_jsonl_dir = _get_str_or_default(cfg, "memory_jsonl_dir", "/opt/llm/memory")
    memory_max_inject_semantic = _get_or_default(
        cfg, "memory_max_inject_semantic", _get_int, 5
    )
    memory_max_inject_episodic = _get_or_default(
        cfg, "memory_max_inject_episodic", _get_int, 3
    )
    memory_min_importance = _get_or_default(
        cfg, "memory_min_importance", _get_float, 0.3
    )
    memory_max_content_chars = _get_or_default(
        cfg, "memory_max_content_chars", _get_int, 500
    )
    memory_embed_enabled = _get_or_default(cfg, "memory_embed_enabled", _get_bool, True)
    memory_dedup_threshold = _get_or_default(
        cfg, "memory_dedup_threshold", _get_float, 0.3
    )
    memory_embed_timeout_sec = _get_or_default(
        cfg, "memory_embed_timeout_sec", _get_float, 5.0
    )
    memory_retention_days = _get_or_default(cfg, "memory_retention_days", _get_int, 90)
    memory_max_pinned = _get_or_default(cfg, "memory_max_pinned", _get_int, 10)
    memory_fts_limit = _get_or_default(cfg, "memory_fts_limit", _get_int, 50)
    memory_rrf_k = _get_or_default(cfg, "memory_rrf_k", _get_int, 60)
    memory_recency_days = _get_or_default(cfg, "memory_recency_days", _get_float, 7.0)
    memory_local_only = _get_or_default(cfg, "memory_local_only", _get_bool, False)
    return _build_model(
        MemoryConfig,
        use_memory_layer=use_memory_layer,
        memory_jsonl_dir=memory_jsonl_dir,
        memory_max_inject_semantic=memory_max_inject_semantic,
        memory_max_inject_episodic=memory_max_inject_episodic,
        memory_min_importance=memory_min_importance,
        memory_max_content_chars=memory_max_content_chars,
        memory_embed_enabled=memory_embed_enabled,
        memory_dedup_threshold=memory_dedup_threshold,
        memory_embed_timeout_sec=memory_embed_timeout_sec,
        memory_retention_days=memory_retention_days,
        memory_max_pinned=memory_max_pinned,
        memory_fts_limit=memory_fts_limit,
        memory_rrf_k=memory_rrf_k,
        memory_recency_days=memory_recency_days,
        memory_local_only=memory_local_only,
    )


def _build_approval_config(cfg: dict[str, Any]) -> ApprovalConfig:
    """Build ApprovalConfig from a raw config dict."""
    approval_risk_rules = _get_or_default(
        cfg, "approval_risk_rules", _get_dict, _DEFAULT_APPROVAL_RISK_RULES
    )
    approval_protected_paths = _get_or_default(
        cfg, "approval_protected_paths", _get_list, list(_DEFAULT_PROTECTED_PATHS)
    )
    approval_high_risk_branches = _get_or_default(
        cfg, "approval_high_risk_branches", _get_list, ["main", "master"]
    )
    approval_shell_safe_prefixes = _get_or_default(
        cfg,
        "approval_shell_safe_prefixes",
        _get_list,
        list(_DEFAULT_SHELL_SAFE_PREFIXES),
    )
    approval_resource_keys = _get_or_default(
        cfg, "approval_resource_keys", _get_dict, _DEFAULT_RESOURCE_KEYS
    )
    approval_dry_run_tools = _validate_dry_run_tools(
        _get_or_default(
            cfg, "approval_dry_run_tools", _get_list, _DEFAULT_DRY_RUN_TOOLS
        ),
    )
    tool_safety_tiers = _get_or_default(cfg, "tool_safety_tiers", _get_dict, {})
    allowed_root = _get_str_or_default(cfg, "allowed_root")
    approval_github_allowed_repos = _get_or_default(
        cfg, "approval_github_allowed_repos", _get_list, []
    )
    gitops_push_blocked = _get_or_default(cfg, "gitops_push_blocked", _get_bool, False)
    return _build_model(
        ApprovalConfig,
        approval_risk_rules=approval_risk_rules,
        approval_protected_paths=approval_protected_paths,
        approval_high_risk_branches=approval_high_risk_branches,
        approval_shell_safe_prefixes=approval_shell_safe_prefixes,
        approval_resource_keys=approval_resource_keys,
        approval_dry_run_tools=approval_dry_run_tools,
        tool_safety_tiers=tool_safety_tiers,
        allowed_root=allowed_root,
        approval_github_allowed_repos=approval_github_allowed_repos,
        gitops_push_blocked=gitops_push_blocked,
    )


def _build_diagnostics_config(cfg: dict[str, Any]) -> DiagnosticsConfig:
    """Build DiagnosticsConfig from a raw config dict's [diagnostics] table."""
    diagnostics_raw = _get_dict(cfg, "diagnostics") or {}
    encryption_key = _get_str_or_default(diagnostics_raw, "encryption_key")
    retention_days = _get_or_default(diagnostics_raw, "retention_days", _get_int, 30)
    raw_sf = diagnostics_raw.get("sensitive_fields", [])
    # A non-list value means "no sensitive fields"; it is not a validation error.
    sensitive_fields = frozenset(raw_sf) if isinstance(raw_sf, list) else frozenset()
    return _build_model(
        DiagnosticsConfig,
        encryption_key=encryption_key,
        retention_days=retention_days,
        sensitive_fields=sensitive_fields,
    )
