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
from pathlib import Path
from typing import Any

from shared.config_errors import ConfigLoadError
from shared.config_loader import ConfigLoader
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
# Default constant tables (mirrored from dataclass defaults for _build_* callers)
# ---------------------------------------------------------------------------

_DEFAULT_PLAN_BLOCKED_TOOLS: list[str] = [
    "write_file",
    "create_directory",
    "delete_file",
    "delete_directory",
]
_DEFAULT_APPROVAL_RISK_RULES: dict[str, str] = {
    "write_file": "medium",
    "edit_file": "medium",
    "create_directory": "medium",
    "move_file": "medium",
    "delete_file": "high",
    "delete_directory": "high",
    "shell_run": "high",
    "github_push_files": "high",
    "github_create_or_update_file": "high",
    "github_delete_file": "high",
    "github_merge_pull_request": "high",
    "github_create_branch": "medium",
    "github_create_pull_request": "medium",
    "github_update_pull_request": "medium",
    "github_create_issue": "medium",
    "github_add_issue_comment": "medium",
}
_DEFAULT_PROTECTED_PATHS: list[str] = [
    "/opt/",
    "/etc/",
    "/boot/",
    "/usr/",
    "/bin/",
    "/sbin/",
]
_DEFAULT_SHELL_SAFE_PREFIXES: list[str] = [
    "ls",
    "cat",
    "echo",
    "git log",
    "git status",
    "git diff",
    "git show",
    "git branch",
    "pwd",
    "find",
    "grep",
]
_DEFAULT_RESOURCE_KEYS: dict[str, list[str]] = {
    "path_keys": ["path", "file_path", "directory_path", "source", "destination"],
    "branch_keys": ["branch", "base", "head"],
}
_DEFAULT_DRY_RUN_TOOLS: list[str] = [
    "write_file",
    "edit_file",
    "create_directory",
    "delete_file",
    "delete_directory",
    "move_file",
]


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------


def _get_list_or_default(
    cfg: dict[str, Any], key: str, default: list[Any]
) -> list[Any]:
    """Extract a list from cfg, falling back to *default* only when the key is absent."""
    v = _get_list(cfg, key)
    return v if v is not None else default


def _get_dict_or_default(
    cfg: dict[str, Any], key: str, default: dict[str, Any]
) -> dict[str, Any]:
    """Extract a dict from cfg, falling back to *default* only when the key is absent."""
    v = _get_dict(cfg, key)
    return v if v is not None else default


def _get_str_or_default(cfg: dict[str, Any], key: str, default: str) -> str:
    """Extract a str from cfg, falling back to *default* only when the key is absent.

    Only use this for keys whose default is `""` — for a non-empty default, an
    explicit empty-string override must not be conflated with an absent key (see
    the `_get_str(cfg, key) or default` call sites left untouched for that case).
    """
    v = _get_str(cfg, key)
    return v if v is not None else default


def _get_int_or_default(cfg: dict[str, Any], key: str, default: int) -> int:
    """Extract an int from cfg, falling back to *default* only when the key is absent."""
    v = _get_int(cfg, key)
    return v if v is not None else default


def _get_float_or_default(cfg: dict[str, Any], key: str, default: float) -> float:
    """Extract a float from cfg, falling back to *default* only when the key is absent."""
    v = _get_float(cfg, key)
    return v if v is not None else default


def _get_bool_or_default(cfg: dict[str, Any], key: str, default: bool) -> bool:
    """Extract a bool from cfg, falling back to *default* only when the key is absent."""
    v = _get_bool(cfg, key)
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


def _build_llm_config(cfg: dict[str, Any]) -> LLMConfig:
    """Build LLMConfig from a raw config dict."""
    llm_url = _get_str_or_default(cfg, "llm_url", "")
    http_timeout = _get_float_or_default(cfg, "http_timeout", 30.0)
    llm_max_retries = _get_int_or_default(cfg, "llm_max_retries", 3)
    llm_retry_base_delay = _get_float_or_default(cfg, "llm_retry_base_delay", 1.0)
    llm_temperature = _get_float_or_default(cfg, "llm_temperature", 0.2)
    llm_max_tokens = _get_int_or_default(cfg, "llm_max_tokens", 1024)
    title_llm_temperature = _get_float_or_default(cfg, "title_llm_temperature", 0.1)
    title_llm_max_tokens = _get_int_or_default(cfg, "title_llm_max_tokens", 20)
    sse_heartbeat_timeout = _get_float_or_default(cfg, "sse_heartbeat_timeout", 30.0)
    sse_malformed_retry = _get_int_or_default(cfg, "sse_malformed_retry", 2)
    sse_reconnect_max = _get_int_or_default(cfg, "sse_reconnect_max", 1)
    llm_stream_retry_on_heartbeat_timeout = _get_bool_or_default(
        cfg, "llm_stream_retry_on_heartbeat_timeout", True
    )
    llm_stream_retry_on_malformed_chunk = _get_bool_or_default(
        cfg, "llm_stream_retry_on_malformed_chunk", False
    )
    tokenize_url = _get_str_or_default(cfg, "tokenize_url", "")
    context_token_limit = _get_int_or_default(cfg, "context_token_limit", 0)
    context_char_limit = _get_int_or_default(cfg, "context_char_limit", 8000)
    context_compress_turns = _get_int_or_default(cfg, "context_compress_turns", 4)
    history_protect_turns = _get_int_or_default(cfg, "history_protect_turns", 2)
    budget_warn_ratio = _get_float_or_default(cfg, "budget_warn_ratio", 0.8)
    return LLMConfig(
        llm_url=llm_url,
        http_timeout=http_timeout,
        llm_max_retries=llm_max_retries,
        llm_retry_base_delay=llm_retry_base_delay,
        llm_temperature=llm_temperature,
        llm_max_tokens=llm_max_tokens,
        title_llm_temperature=title_llm_temperature,
        title_llm_max_tokens=title_llm_max_tokens,
        sse_heartbeat_timeout=sse_heartbeat_timeout,
        sse_malformed_retry=sse_malformed_retry,
        sse_reconnect_max=sse_reconnect_max,
        llm_stream_retry_on_heartbeat_timeout=llm_stream_retry_on_heartbeat_timeout,
        llm_stream_retry_on_malformed_chunk=llm_stream_retry_on_malformed_chunk,
        tokenize_url=tokenize_url,
        context_token_limit=context_token_limit,
        context_char_limit=context_char_limit,
        context_compress_turns=context_compress_turns,
        history_protect_turns=history_protect_turns,
        budget_warn_ratio=budget_warn_ratio,
    )


def _build_rag_config(cfg: dict[str, Any]) -> RAGConfig:
    """Build RAGConfig from a raw config dict."""
    embed_url = _get_str_or_default(cfg, "embed_url", "")
    use_semantic_cache = _get_bool_or_default(cfg, "use_semantic_cache", False)
    semantic_cache_threshold = _get_float_or_default(
        cfg, "semantic_cache_threshold", 0.92
    )
    semantic_cache_max_size = _get_int_or_default(cfg, "semantic_cache_max_size", 100)
    use_refiner = _get_bool_or_default(cfg, "use_refiner", False)
    refiner_max_tokens = _get_int_or_default(cfg, "refiner_max_tokens", 512)
    refiner_timeout = _get_float_or_default(cfg, "refiner_timeout", 30.0)
    refiner_max_chars_per_chunk = _get_int_or_default(
        cfg, "refiner_max_chars_per_chunk", 300
    )
    return RAGConfig(
        embed_url=embed_url,
        use_semantic_cache=use_semantic_cache,
        semantic_cache_threshold=semantic_cache_threshold,
        semantic_cache_max_size=semantic_cache_max_size,
        use_refiner=use_refiner,
        refiner_max_tokens=refiner_max_tokens,
        refiner_timeout=refiner_timeout,
        refiner_max_chars_per_chunk=refiner_max_chars_per_chunk,
    )


def _build_tool_config(cfg: dict[str, Any], system_prompt_tool: str) -> ToolConfig:
    """Build ToolConfig from a raw config dict and system prompt template."""
    tool_cache_ttl = _get_float_or_default(cfg, "tool_cache_ttl", 300)
    tool_cache_max_size = _get_int_or_default(cfg, "tool_cache_max_size", 200)
    serial_tool_calls = _get_bool_or_default(cfg, "serial_tool_calls", False)
    tool_definitions_strict = _get_bool_or_default(
        cfg, "tool_definitions_strict", False
    )
    routing_drift_strict = _get_bool_or_default(cfg, "routing_drift_strict", False)
    tool_dedup_max_repeats = _get_int_or_default(cfg, "tool_dedup_max_repeats", 3)
    tool_cycle_detect_window = _get_int_or_default(cfg, "tool_cycle_detect_window", 2)
    tool_error_max_consecutive = _get_int_or_default(
        cfg, "tool_error_max_consecutive", 3
    )
    tool_error_retry_max = _get_int_or_default(cfg, "tool_error_retry_max", 1)
    tool_concurrency_limits = _get_dict_or_default(cfg, "tool_concurrency_limits", {})
    masked_fields = _get_list_or_default(cfg, "masked_fields", ["file_content"])
    plan_blocked_tools = _get_list_or_default(
        cfg, "plan_blocked_tools", list(_DEFAULT_PLAN_BLOCKED_TOOLS)
    )
    max_tool_turns = _get_int_or_default(cfg, "max_tool_turns", 5)
    tool_result_max_llm_chars = _get_int_or_default(
        cfg, "tool_result_max_llm_chars", 8000
    )
    tool_results_turn_max_chars = _get_int_or_default(
        cfg, "tool_results_turn_max_chars", 50000
    )
    tool_definitions = _get_list_or_default(cfg, "tool_definitions", [])
    system_prompts = _get_dict_or_default(
        cfg, "system_prompts", {"default": system_prompt_tool}
    )
    allowed_tools = _get_list_or_default(cfg, "allowed_tools", [])
    return ToolConfig(
        tool_cache_ttl=tool_cache_ttl,
        tool_cache_max_size=tool_cache_max_size,
        serial_tool_calls=serial_tool_calls,
        tool_definitions_strict=tool_definitions_strict,
        routing_drift_strict=routing_drift_strict,
        tool_dedup_max_repeats=tool_dedup_max_repeats,
        tool_cycle_detect_window=tool_cycle_detect_window,
        tool_error_max_consecutive=tool_error_max_consecutive,
        tool_error_retry_max=tool_error_retry_max,
        tool_concurrency_limits=tool_concurrency_limits,
        masked_fields=masked_fields,
        plan_blocked_tools=plan_blocked_tools,
        max_tool_turns=max_tool_turns,
        tool_result_max_llm_chars=tool_result_max_llm_chars,
        tool_results_turn_max_chars=tool_results_turn_max_chars,
        tool_definitions=tool_definitions,
        system_prompts=system_prompts,
        system_prompt_tool=system_prompt_tool,
        allowed_tools=allowed_tools,
    )


def _build_memory_config(cfg: dict[str, Any]) -> MemoryConfig:
    """Build MemoryConfig from a raw config dict."""
    use_memory_layer = _get_bool_or_default(cfg, "use_memory_layer", True)
    # Non-empty default: an explicit "" override intentionally falls back too
    # (see _get_str_or_default docstring) — do not convert to that helper.
    memory_jsonl_dir = _get_str(cfg, "memory_jsonl_dir") or "/opt/llm/memory"
    memory_max_inject_semantic = _get_int_or_default(
        cfg, "memory_max_inject_semantic", 5
    )
    if memory_max_inject_semantic < 0:
        raise ConfigReloadValidationError(
            f"memory_max_inject_semantic must be >= 0, got {memory_max_inject_semantic}"
        )
    memory_max_inject_episodic = _get_int_or_default(
        cfg, "memory_max_inject_episodic", 3
    )
    if memory_max_inject_episodic < 0:
        raise ConfigReloadValidationError(
            f"memory_max_inject_episodic must be >= 0, got {memory_max_inject_episodic}"
        )
    memory_min_importance = _get_float_or_default(cfg, "memory_min_importance", 0.3)
    memory_embed_enabled = _get_bool_or_default(cfg, "memory_embed_enabled", True)
    memory_dedup_threshold = _get_float_or_default(cfg, "memory_dedup_threshold", 0.3)
    memory_max_content_chars = _get_int_or_default(cfg, "memory_max_content_chars", 500)
    memory_embed_timeout_sec = _get_float_or_default(
        cfg, "memory_embed_timeout_sec", 5.0
    )
    if memory_embed_timeout_sec <= 0:
        raise ConfigReloadValidationError(
            f"memory_embed_timeout_sec must be > 0, got {memory_embed_timeout_sec}"
        )
    memory_retention_days = _get_int_or_default(cfg, "memory_retention_days", 90)
    if memory_retention_days < 1:
        raise ConfigReloadValidationError(
            f"memory_retention_days must be >= 1, got {memory_retention_days}"
        )
    memory_fts_limit = _get_int_or_default(cfg, "memory_fts_limit", 50)
    memory_rrf_k = _get_int_or_default(cfg, "memory_rrf_k", 60)
    memory_recency_days = _get_float_or_default(cfg, "memory_recency_days", 7.0)
    memory_local_only = _get_bool_or_default(cfg, "memory_local_only", False)
    return MemoryConfig(
        use_memory_layer=use_memory_layer,
        memory_jsonl_dir=memory_jsonl_dir,
        memory_max_inject_semantic=memory_max_inject_semantic,
        memory_max_inject_episodic=memory_max_inject_episodic,
        memory_min_importance=memory_min_importance,
        memory_embed_enabled=memory_embed_enabled,
        memory_dedup_threshold=memory_dedup_threshold,
        memory_max_content_chars=memory_max_content_chars,
        memory_embed_timeout_sec=memory_embed_timeout_sec,
        memory_retention_days=memory_retention_days,
        memory_fts_limit=memory_fts_limit,
        memory_rrf_k=memory_rrf_k,
        memory_recency_days=memory_recency_days,
        memory_local_only=memory_local_only,
    )


def _build_approval_config(cfg: dict[str, Any]) -> ApprovalConfig:
    """Build ApprovalConfig from a raw config dict."""
    approval_risk_rules = _get_dict_or_default(
        cfg, "approval_risk_rules", _DEFAULT_APPROVAL_RISK_RULES
    )
    approval_protected_paths = _get_list_or_default(
        cfg, "approval_protected_paths", list(_DEFAULT_PROTECTED_PATHS)
    )
    approval_high_risk_branches = _get_list_or_default(
        cfg, "approval_high_risk_branches", ["main", "master"]
    )
    approval_shell_safe_prefixes = _get_list_or_default(
        cfg, "approval_shell_safe_prefixes", list(_DEFAULT_SHELL_SAFE_PREFIXES)
    )
    approval_resource_keys = _get_dict_or_default(
        cfg, "approval_resource_keys", _DEFAULT_RESOURCE_KEYS
    )
    approval_dry_run_tools = _validate_dry_run_tools(
        _get_list_or_default(cfg, "approval_dry_run_tools", _DEFAULT_DRY_RUN_TOOLS),
    )
    tool_safety_tiers = _get_dict_or_default(cfg, "tool_safety_tiers", {})
    ALLOWED_TIERS = {"READ_ONLY", "WRITE_SAFE", "WRITE_DANGEROUS", "ADMIN"}
    for key, val in tool_safety_tiers.items():
        if isinstance(val, str) and val not in ALLOWED_TIERS:
            raise ConfigReloadValidationError(
                f"tool_safety_tiers[{key!r}] must be one of "
                f"{ALLOWED_TIERS}, got {val!r}"
            )
    allowed_root = _get_str_or_default(cfg, "allowed_root", "")
    approval_github_allowed_repos = _get_list_or_default(
        cfg, "approval_github_allowed_repos", []
    )
    gitops_push_blocked = _get_bool_or_default(cfg, "gitops_push_blocked", False)
    return ApprovalConfig(
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
    encryption_key = _get_str_or_default(diagnostics_raw, "encryption_key", "")
    retention_days = _get_int_or_default(diagnostics_raw, "retention_days", 30)
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


def build_agent_config(cfg_override: dict[str, Any] | None = None) -> AgentConfig:
    """Construct AgentConfig from a config dict.

    If cfg_override is provided it is used directly (for /reload and tests).
    Otherwise configuration is loaded from files via load_config().
    """
    cfg = cfg_override if cfg_override is not None else load_config()
    system_prompt_tool = cfg.get("system_prompt_tool", "")
    security_profile_val = SecurityProfile(cfg.get("security_profile", "local"))
    # Production config validation (before REPL becomes available)
    results = ProductionConfigValidator().validate(
        cfg,
        security_profile=security_profile_val,
    )

    if results.errors:
        logger.error("Production config validation failed:")
        for err in results.errors:
            logger.error(f"  - {err}")
        sys.exit(1)

    for warning in results.warnings:
        logger.warning(warning)

    security_lockdown_enabled = _get_bool_or_default(
        cfg, "security_lockdown_enabled", False
    )
    otel_enabled = _get_bool_or_default(cfg, "otel_enabled", False)
    structured_log = _get_bool_or_default(cfg, "structured_log", False)

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
    )
