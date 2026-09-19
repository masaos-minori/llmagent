#!/usr/bin/env python3
"""scripts/agent/config_builders.py

Constants, builder functions, ConfigLoadError, load_config, and build_agent_config.

Import from here:  from agent.config_builders import (
    build_agent_config, load_config, ConfigLoadError,
)
"""

from __future__ import annotations

import logging
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

from shared.config_errors import ConfigLoadError
from shared.config_loader import ConfigLoader
from shared.config_validator import RagConfigValidator
from shared.mcp_config import (
    SecurityProfile,  # noqa: F401 — used by build_agent_config
    _build_mcp_servers,  # noqa: F401 — used by config_reload.py (lazy import)
)
from shared.production_config_validator import ProductionConfigValidator

from agent.config_dataclasses import (
    AgentConfig,
    ApprovalConfig,
    DiagnosticsConfig,
    LLMConfig,
    MCPConfig,
    MemoryConfig,
    ObservabilityConfig,
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

_CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"


# ---------------------------------------------------------------------------
# Exception + loader
# ---------------------------------------------------------------------------


def load_config() -> dict[str, Any]:
    """Load configuration from files.  No module-level cache — always fresh."""
    try:
        config: dict[str, Any] = ConfigLoader().load_all()
        return config
    except (OSError, ValueError, TypeError) as e:
        raise ConfigLoadError(f"Config load failed: {e}", cause=e) from e


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------


def _get_or_default(
    cfg: dict[str, Any],
    key: str,
    getter: Callable[[dict[str, Any], str], Any],
    default: Any,
) -> Any:
    """Extract a value from cfg using *getter*, falling back to *default* when absent.

    Only use this for keys whose default is non-empty (non-zero for numbers,
    non-empty string for strings). For empty-string defaults, use
    ``_get_str_or_default`` instead to preserve None vs "" semantics.
    """
    v = getter(cfg, key)
    return v if v is not None else default


def _get_str_or_default(cfg: dict[str, Any], key: str, default: str) -> str:
    """Extract a str from cfg, falling back to *default* only when the key is absent.

    Only use this for keys whose default is `""` — for a non-empty default, an
    explicit empty-string override must not be conflated with an absent key (see
    the `_get_str(cfg, key) or default` call sites left untouched for that case).
    """
    v = _get_str(cfg, key)
    return v if v is not None else default


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


def _extract_llm_transport_fields(cfg: dict[str, Any]) -> dict[str, Any]:
    """Extract LLM transport-related fields."""
    return {
        "llm_url": _get_str_or_default(cfg, "llm_url", ""),
        "http_timeout": _get_or_default(cfg, "http_timeout", _get_float, 30.0),
        "llm_max_retries": _get_or_default(cfg, "llm_max_retries", _get_int, 3),
        "llm_retry_base_delay": _get_or_default(
            cfg, "llm_retry_base_delay", _get_float, 1.0
        ),
        "sse_heartbeat_timeout": _get_or_default(
            cfg, "sse_heartbeat_timeout", _get_float, 30.0
        ),
        "sse_malformed_retry": _get_or_default(cfg, "sse_malformed_retry", _get_int, 2),
        "sse_reconnect_max": _get_or_default(cfg, "sse_reconnect_max", _get_int, 1),
        "llm_stream_retry_on_heartbeat_timeout": _get_or_default(
            cfg, "llm_stream_retry_on_heartbeat_timeout", _get_bool, True
        ),
        "llm_stream_retry_on_malformed_chunk": _get_or_default(
            cfg, "llm_stream_retry_on_malformed_chunk", _get_bool, False
        ),
    }


def _extract_llm_temperature_fields(cfg: dict[str, Any]) -> dict[str, Any]:
    """Extract LLM temperature-related fields."""
    return {
        "llm_temperature": _get_or_default(cfg, "llm_temperature", _get_float, 0.2),
        "llm_max_tokens": _get_or_default(cfg, "llm_max_tokens", _get_int, 1024),
        "title_llm_temperature": _get_or_default(
            cfg, "title_llm_temperature", _get_float, 0.1
        ),
        "title_llm_max_tokens": _get_or_default(
            cfg, "title_llm_max_tokens", _get_int, 20
        ),
        "llm_compress_temperature": _get_or_default(
            cfg, "llm_compress_temperature", _get_float, 0.3
        ),
        "llm_compress_max_tokens": _get_or_default(
            cfg, "llm_compress_max_tokens", _get_int, 300
        ),
    }


def _extract_llm_context_fields(cfg: dict[str, Any]) -> dict[str, Any]:
    """Extract LLM context-related fields."""
    return {
        "tokenize_url": _get_str_or_default(cfg, "tokenize_url", ""),
        "context_token_limit": _get_or_default(cfg, "context_token_limit", _get_int, 0),
        "context_char_limit": _get_or_default(
            cfg, "context_char_limit", _get_int, 8000
        ),
        "context_compress_turns": _get_or_default(
            cfg, "context_compress_turns", _get_int, 4
        ),
        "history_protect_turns": _get_or_default(
            cfg, "history_protect_turns", _get_int, 2
        ),
        "budget_warn_ratio": _get_or_default(cfg, "budget_warn_ratio", _get_float, 0.8),
    }


def _build_llm_config(cfg: dict[str, Any]) -> LLMConfig:
    """Build LLMConfig from a raw config dict."""
    transport = _extract_llm_transport_fields(cfg)
    temperature = _extract_llm_temperature_fields(cfg)
    context = _extract_llm_context_fields(cfg)
    all_fields = {**transport, **temperature, **context}
    return LLMConfig(**all_fields)


def _build_rag_config(cfg: dict[str, Any]) -> RAGConfig:
    """Build RAGConfig from a raw config dict."""
    validator = RagConfigValidator()
    validation_result = validator.validate(cfg)
    for warning in validation_result.warnings:
        logger.warning("rag config warning: %s", warning)
    for error in validation_result.errors:
        logger.error("rag config error: %s", error)
    if not validation_result.ok:
        raise ValueError(f"RAG config validation failed: {validation_result.errors}")
    embed_url = _get_str_or_default(cfg, "embed_url", "")
    use_refiner = _get_or_default(cfg, "use_refiner", _get_bool, False)
    refiner_max_tokens = _get_or_default(cfg, "refiner_max_tokens", _get_int, 512)
    refiner_timeout = _get_or_default(cfg, "refiner_timeout", _get_float, 30.0)
    refiner_max_chars_per_chunk = _get_or_default(
        cfg, "refiner_max_chars_per_chunk", _get_int, 300
    )
    return RAGConfig(
        embed_url=embed_url,
        use_refiner=use_refiner,
        refiner_max_tokens=refiner_max_tokens,
        refiner_timeout=refiner_timeout,
        refiner_max_chars_per_chunk=refiner_max_chars_per_chunk,
    )


def _extract_tool_execution_fields(cfg: dict[str, Any]) -> dict[str, Any]:
    """Extract tool execution-related fields."""
    return {
        "serial_tool_calls": _get_or_default(
            cfg, "serial_tool_calls", _get_bool, False
        ),
        "tool_definitions_strict": _get_or_default(
            cfg, "tool_definitions_strict", _get_bool, False
        ),
        "routing_drift_strict": _get_or_default(
            cfg, "routing_drift_strict", _get_bool, False
        ),
        "tool_dedup_max_repeats": _get_or_default(
            cfg, "tool_dedup_max_repeats", _get_int, 3
        ),
        "tool_cycle_detect_window": _get_or_default(
            cfg, "tool_cycle_detect_window", _get_int, 2
        ),
        "tool_error_max_consecutive": _get_or_default(
            cfg, "tool_error_max_consecutive", _get_int, 3
        ),
        "tool_error_retry_max": _get_or_default(
            cfg, "tool_error_retry_max", _get_int, 1
        ),
    }


def _extract_tool_limits_fields(cfg: dict[str, Any]) -> dict[str, Any]:
    """Extract tool limits-related fields."""
    return {
        "tool_concurrency_limits": _get_or_default(
            cfg, "tool_concurrency_limits", _get_dict, {}
        ),
        "masked_fields": _get_or_default(
            cfg, "masked_fields", _get_list, ["file_content"]
        ),
        "plan_blocked_tools": _get_or_default(
            cfg, "plan_blocked_tools", _get_list, list(_DEFAULT_PLAN_BLOCKED_TOOLS)
        ),
        "max_tool_turns": _get_or_default(cfg, "max_tool_turns", _get_int, 5),
        "tool_result_max_llm_chars": _get_or_default(
            cfg, "tool_result_max_llm_chars", _get_int, 8000
        ),
        "tool_results_turn_max_chars": _get_or_default(
            cfg, "tool_results_turn_max_chars", _get_int, 50000
        ),
    }


def _extract_tool_schema_fields(
    cfg: dict[str, Any], system_prompt_tool: str
) -> dict[str, Any]:
    """Extract tool schema-related fields."""
    return {
        "tool_definitions": _get_or_default(cfg, "tool_definitions", _get_list, []),
        "system_prompts": _get_or_default(
            cfg, "system_prompts", _get_dict, {"default": system_prompt_tool}
        ),
        "system_prompt_tool": system_prompt_tool,
        "allowed_tools": _get_or_default(cfg, "allowed_tools", _get_list, []),
    }


def _build_tool_config(cfg: dict[str, Any], system_prompt_tool: str) -> ToolConfig:
    """Build ToolConfig from a raw config dict and system prompt template."""
    execution = _extract_tool_execution_fields(cfg)
    limits = _extract_tool_limits_fields(cfg)
    schema = _extract_tool_schema_fields(cfg, system_prompt_tool)
    all_fields = {**execution, **limits, **schema}
    return ToolConfig(**all_fields)


def _extract_memory_core_fields(cfg: dict[str, Any]) -> dict[str, Any]:
    """Extract memory core fields."""
    use_memory_layer = _get_or_default(cfg, "use_memory_layer", _get_bool, True)
    # Non-empty default: an explicit "" override intentionally falls back too
    # (see _get_str_or_default docstring) — do not convert to that helper.
    memory_jsonl_dir = _get_str(cfg, "memory_jsonl_dir") or "/opt/llm/memory"
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
    return {
        "use_memory_layer": use_memory_layer,
        "memory_jsonl_dir": memory_jsonl_dir,
        "memory_max_inject_semantic": memory_max_inject_semantic,
        "memory_max_inject_episodic": memory_max_inject_episodic,
        "memory_min_importance": memory_min_importance,
        "memory_max_content_chars": memory_max_content_chars,
    }


def _extract_memory_embedding_fields(cfg: dict[str, Any]) -> dict[str, Any]:
    """Extract memory embedding fields."""
    memory_embed_enabled = _get_or_default(cfg, "memory_embed_enabled", _get_bool, True)
    memory_dedup_threshold = _get_or_default(
        cfg, "memory_dedup_threshold", _get_float, 0.3
    )
    memory_embed_timeout_sec = _get_or_default(
        cfg, "memory_embed_timeout_sec", _get_float, 5.0
    )
    return {
        "memory_embed_enabled": memory_embed_enabled,
        "memory_dedup_threshold": memory_dedup_threshold,
        "memory_embed_timeout_sec": memory_embed_timeout_sec,
    }


def _extract_memory_search_fields(cfg: dict[str, Any]) -> dict[str, Any]:
    """Extract memory search fields."""
    memory_retention_days = _get_or_default(cfg, "memory_retention_days", _get_int, 90)
    memory_fts_limit = _get_or_default(cfg, "memory_fts_limit", _get_int, 50)
    memory_rrf_k = _get_or_default(cfg, "memory_rrf_k", _get_int, 60)
    memory_recency_days = _get_or_default(cfg, "memory_recency_days", _get_float, 7.0)
    memory_local_only = _get_or_default(cfg, "memory_local_only", _get_bool, False)
    return {
        "memory_retention_days": memory_retention_days,
        "memory_fts_limit": memory_fts_limit,
        "memory_rrf_k": memory_rrf_k,
        "memory_recency_days": memory_recency_days,
        "memory_local_only": memory_local_only,
    }


def _build_memory_config(cfg: dict[str, Any]) -> MemoryConfig:
    """Build MemoryConfig from a raw config dict."""
    core = _extract_memory_core_fields(cfg)
    embedding = _extract_memory_embedding_fields(cfg)
    search = _extract_memory_search_fields(cfg)
    all_fields = {**core, **embedding, **search}
    try:
        return MemoryConfig(**all_fields)
    except ValueError as e:
        # Convert ValueError from MemoryConfig.__post_init__ validators
        # to ConfigReloadValidationError for reload path error handling
        raise ConfigReloadValidationError(str(e)) from e


def _extract_approval_risk_fields(cfg: dict[str, Any]) -> dict[str, Any]:
    """Extract approval risk-related fields."""
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
    return {
        "approval_risk_rules": approval_risk_rules,
        "approval_protected_paths": approval_protected_paths,
        "approval_high_risk_branches": approval_high_risk_branches,
        "approval_shell_safe_prefixes": approval_shell_safe_prefixes,
        "approval_resource_keys": approval_resource_keys,
    }


def _extract_approval_tool_fields(cfg: dict[str, Any]) -> dict[str, Any]:
    """Extract approval tool-related fields."""
    approval_dry_run_tools = _validate_dry_run_tools(
        _get_or_default(
            cfg, "approval_dry_run_tools", _get_list, _DEFAULT_DRY_RUN_TOOLS
        ),
    )
    tool_safety_tiers = _get_or_default(cfg, "tool_safety_tiers", _get_dict, {})
    ALLOWED_TIERS = {"READ_ONLY", "WRITE_SAFE", "WRITE_DANGEROUS", "ADMIN"}
    for key, val in tool_safety_tiers.items():
        if isinstance(val, str) and val not in ALLOWED_TIERS:
            raise ConfigReloadValidationError(
                f"tool_safety_tiers[{key!r}] must be one of "
                f"{ALLOWED_TIERS}, got {val!r}"
            )
    return {
        "approval_dry_run_tools": approval_dry_run_tools,
        "tool_safety_tiers": tool_safety_tiers,
    }


def _extract_approval_github_fields(cfg: dict[str, Any]) -> dict[str, Any]:
    """Extract approval GitHub-related fields."""
    allowed_root = _get_str_or_default(cfg, "allowed_root", "")
    approval_github_allowed_repos = _get_or_default(
        cfg, "approval_github_allowed_repos", _get_list, []
    )
    gitops_push_blocked = _get_or_default(cfg, "gitops_push_blocked", _get_bool, False)
    return {
        "allowed_root": allowed_root,
        "approval_github_allowed_repos": approval_github_allowed_repos,
        "gitops_push_blocked": gitops_push_blocked,
    }


def _build_approval_config(cfg: dict[str, Any]) -> ApprovalConfig:
    """Build ApprovalConfig from a raw config dict."""
    risk = _extract_approval_risk_fields(cfg)
    tool = _extract_approval_tool_fields(cfg)
    github = _extract_approval_github_fields(cfg)
    all_fields = {**risk, **tool, **github}
    return ApprovalConfig(**all_fields)


def _build_diagnostics_config(cfg: dict[str, Any]) -> DiagnosticsConfig:
    """Build DiagnosticsConfig from a raw config dict's [diagnostics] table."""
    diagnostics_raw = _get_dict(cfg, "diagnostics") or {}
    encryption_key = _get_str_or_default(diagnostics_raw, "encryption_key", "")
    retention_days = _get_or_default(diagnostics_raw, "retention_days", _get_int, 30)
    raw_sf = diagnostics_raw.get("sensitive_fields", [])
    if isinstance(raw_sf, list):
        sf = frozenset(raw_sf)
    else:
        sf = frozenset()
    return DiagnosticsConfig(
        encryption_key=encryption_key,
        retention_days=retention_days,
        sensitive_fields=sf,
    )


def _resolve_config_source_and_registry(
    cfg_override: dict[str, Any] | None,
) -> tuple[dict[str, Any], set[str]]:
    """Resolve config source and tool registry. Returns (cfg, known_tools)."""
    cfg = cfg_override if cfg_override is not None else load_config()
    try:
        from shared.tool_registry import get_registry

        known_tools = set(get_registry().get_all_tool_names())
    except ValueError as exc:
        raise ConfigReloadValidationError(
            f"Tool registry resolution failed during config build: {exc}"
        ) from exc
    except ImportError as exc:
        raise ConfigReloadValidationError(
            f"Tool registry module unavailable during config build: {exc}"
        ) from exc
    return cfg, known_tools


def _run_production_validation(
    cfg: dict[str, Any],
    security_profile_val: SecurityProfile,
    known_tools: set[str],
) -> None:
    """Run production config validation; exit on errors."""
    results = ProductionConfigValidator().validate(
        cfg, security_profile=security_profile_val, known_tools=known_tools
    )
    if results.errors:
        logger.error("Production config validation failed:")
        for err in results.errors:
            logger.error(f"  - {err}")
        sys.exit(1)
    for warning in results.warnings:
        logger.warning(warning)


def _assemble_agent_config(
    cfg: dict[str, Any],
    system_prompt_tool: str,
    security_profile_val: SecurityProfile,
) -> AgentConfig:
    """Assemble AgentConfig by delegating to builder functions."""
    security_lockdown_enabled = _get_or_default(
        cfg, "security_lockdown_enabled", _get_bool, False
    )
    otel_enabled = _get_or_default(cfg, "otel_enabled", _get_bool, False)
    structured_log = _get_or_default(cfg, "structured_log", _get_bool, False)
    return AgentConfig(
        llm=_build_llm_config(cfg),
        rag=_build_rag_config(cfg),
        tool=_build_tool_config(cfg, system_prompt_tool),
        memory=_build_memory_config(cfg),
        mcp=MCPConfig(
            mcp_servers=_build_mcp_servers(cfg),
            security_profile=security_profile_val,
            security_lockdown_enabled=security_lockdown_enabled,
        ),
        approval=_build_approval_config(cfg),
        obs=ObservabilityConfig(
            otel_enabled=otel_enabled,
            otel_endpoint=_get_str_or_default(cfg, "otel_endpoint", ""),
            otel_service_name=_get_str(cfg, "otel_service_name") or "llm-agent",
            audit_log_file=_get_str(cfg, "audit_log_file") or "/opt/llm/logs/audit.log",
            structured_log=structured_log,
        ),
        diagnostics=_build_diagnostics_config(cfg),
        agent_memory_max_startup_snippets=_get_or_default(
            cfg, "agent_memory_max_startup_snippets", _get_int, 10
        ),
    )


def build_agent_config(cfg_override: dict[str, Any] | None = None) -> AgentConfig:
    """Construct AgentConfig from a config dict.

    If cfg_override is provided it is used directly (for /reload and tests).
    Otherwise configuration is loaded from files via load_config().
    """
    cfg, known_tools = _resolve_config_source_and_registry(cfg_override)
    system_prompt_tool = cfg.get("system_prompt_tool", "")
    security_profile_val = SecurityProfile(cfg.get("security_profile", "production"))
    _run_production_validation(cfg, security_profile_val, known_tools)
    return _assemble_agent_config(cfg, system_prompt_tool, security_profile_val)
