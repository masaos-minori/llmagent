#!/usr/bin/env python3
"""agent/config_builders.py

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

_SENTINEL = object()


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
    llm_url = _get_str(cfg, "llm_url") or ""
    _ht = _get_float(cfg, "http_timeout")
    http_timeout = _ht if _ht is not None else 30.0
    _mr = _get_int(cfg, "llm_max_retries")
    llm_max_retries = _mr if _mr is not None else 3
    _rbd = _get_float(cfg, "llm_retry_base_delay")
    llm_retry_base_delay = _rbd if _rbd is not None else 1.0
    _lt = _get_float(cfg, "llm_temperature")
    llm_temperature = _lt if _lt is not None else 0.2
    _mt = _get_int(cfg, "llm_max_tokens")
    llm_max_tokens = _mt if _mt is not None else 1024
    _tlt = _get_float(cfg, "title_llm_temperature")
    title_llm_temperature = _tlt if _tlt is not None else 0.1
    _tlmt = _get_int(cfg, "title_llm_max_tokens")
    title_llm_max_tokens = _tlmt if _tlmt is not None else 20
    _sht = _get_float(cfg, "sse_heartbeat_timeout")
    sse_heartbeat_timeout = _sht if _sht is not None else 30.0
    _smr = _get_int(cfg, "sse_malformed_retry")
    sse_malformed_retry = _smr if _smr is not None else 2
    _sr = _get_int(cfg, "sse_reconnect_max")
    sse_reconnect_max = _sr if _sr is not None else 1
    _v = _get_bool(cfg, "llm_stream_retry_on_heartbeat_timeout")
    llm_stream_retry_on_heartbeat_timeout = _v if _v is not None else True
    _v = _get_bool(cfg, "llm_stream_retry_on_malformed_chunk")
    llm_stream_retry_on_malformed_chunk = _v if _v is not None else False
    tokenize_url = _get_str(cfg, "tokenize_url") or ""
    _ctl = _get_int(cfg, "context_token_limit")
    context_token_limit = _ctl if _ctl is not None else 0
    _ccl = _get_int(cfg, "context_char_limit")
    context_char_limit = _ccl if _ccl is not None else 8000
    _cct = _get_int(cfg, "context_compress_turns")
    context_compress_turns = _cct if _cct is not None else 4
    _hpt = _get_int(cfg, "history_protect_turns")
    history_protect_turns = _hpt if _hpt is not None else 2
    _bwr = _get_float(cfg, "budget_warn_ratio")
    budget_warn_ratio = _bwr if _bwr is not None else 0.8
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
    embed_url = _get_str(cfg, "embed_url") or ""
    _v = _get_bool(cfg, "use_semantic_cache")
    use_semantic_cache = _v if _v is not None else False
    _sct = _get_float(cfg, "semantic_cache_threshold")
    semantic_cache_threshold = _sct if _sct is not None else 0.92
    _scms = _get_int(cfg, "semantic_cache_max_size")
    semantic_cache_max_size = _scms if _scms is not None else 100
    _v = _get_bool(cfg, "use_refiner")
    use_refiner = _v if _v is not None else False
    _rmt = _get_int(cfg, "refiner_max_tokens")
    refiner_max_tokens = _rmt if _rmt is not None else 512
    _rt = _get_float(cfg, "refiner_timeout")
    refiner_timeout = _rt if _rt is not None else 30.0
    _rmcpc = _get_int(cfg, "refiner_max_chars_per_chunk")
    refiner_max_chars_per_chunk = _rmcpc if _rmcpc is not None else 300
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
    _tct = _get_float(cfg, "tool_cache_ttl")
    tool_cache_ttl = _tct if _tct is not None else 300
    _tcms = _get_int(cfg, "tool_cache_max_size")
    tool_cache_max_size = _tcms if _tcms is not None else 200
    _v = _get_bool(cfg, "serial_tool_calls")
    serial_tool_calls = _v if _v is not None else False
    _v = _get_bool(cfg, "tool_definitions_strict")
    tool_definitions_strict = _v if _v is not None else False
    _v = _get_bool(cfg, "routing_drift_strict")
    routing_drift_strict = _v if _v is not None else False
    _tdmr = _get_int(cfg, "tool_dedup_max_repeats")
    tool_dedup_max_repeats = _tdmr if _tdmr is not None else 3
    _tcdw = _get_int(cfg, "tool_cycle_detect_window")
    tool_cycle_detect_window = _tcdw if _tcdw is not None else 2
    _temc = _get_int(cfg, "tool_error_max_consecutive")
    tool_error_max_consecutive = _temc if _temc is not None else 3
    _ter = _get_int(cfg, "tool_error_retry_max")
    tool_error_retry_max = _ter if _ter is not None else 1
    tool_concurrency_limits = _get_dict_or_default(cfg, "tool_concurrency_limits", {})
    masked_fields = _get_list_or_default(cfg, "masked_fields", ["file_content"])
    _pb = _get_list(cfg, "plan_blocked_tools")
    plan_blocked_tools = _pb if _pb is not None else list(_DEFAULT_PLAN_BLOCKED_TOOLS)
    _mtt = _get_int(cfg, "max_tool_turns")
    max_tool_turns = _mtt if _mtt is not None else 5
    _trmlc = _get_int(cfg, "tool_result_max_llm_chars")
    tool_result_max_llm_chars = _trmlc if _trmlc is not None else 8000
    _trtmc = _get_int(cfg, "tool_results_turn_max_chars")
    tool_results_turn_max_chars = _trtmc if _trtmc is not None else 50000
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
    _v = _get_bool(cfg, "use_memory_layer")
    use_memory_layer = _v if _v is not None else True
    memory_jsonl_dir = _get_str(cfg, "memory_jsonl_dir") or "/opt/llm/memory"
    _mem_semantic = _get_int(cfg, "memory_max_inject_semantic")
    memory_max_inject_semantic = _mem_semantic if _mem_semantic is not None else 5
    if memory_max_inject_semantic < 0:
        raise ConfigReloadValidationError(
            f"memory_max_inject_semantic must be >= 0, got {memory_max_inject_semantic}"
        )
    _mem_episodic = _get_int(cfg, "memory_max_inject_episodic")
    memory_max_inject_episodic = _mem_episodic if _mem_episodic is not None else 3
    if memory_max_inject_episodic < 0:
        raise ConfigReloadValidationError(
            f"memory_max_inject_episodic must be >= 0, got {memory_max_inject_episodic}"
        )
    _mmi = _get_float(cfg, "memory_min_importance")
    memory_min_importance = _mmi if _mmi is not None else 0.3
    _v = _get_bool(cfg, "memory_embed_enabled")
    memory_embed_enabled = _v if _v is not None else True
    _mem_dim = _get_int(cfg, "memory_embed_dim")
    memory_embed_dim = _mem_dim if _mem_dim is not None else 384
    if memory_embed_dim < 1:
        raise ConfigReloadValidationError(
            f"memory_embed_dim must be >= 1, got {memory_embed_dim}"
        )
    _mdt = _get_float(cfg, "memory_dedup_threshold")
    memory_dedup_threshold = _mdt if _mdt is not None else 0.3
    _mmc = _get_int(cfg, "memory_max_content_chars")
    memory_max_content_chars = _mmc if _mmc is not None else 500
    _mem_timeout = _get_float(cfg, "memory_embed_timeout_sec")
    memory_embed_timeout_sec = _mem_timeout if _mem_timeout is not None else 5.0
    if memory_embed_timeout_sec <= 0:
        raise ConfigReloadValidationError(
            f"memory_embed_timeout_sec must be > 0, got {memory_embed_timeout_sec}"
        )
    _mem_retention = _get_int(cfg, "memory_retention_days")
    memory_retention_days = _mem_retention if _mem_retention is not None else 90
    if memory_retention_days < 1:
        raise ConfigReloadValidationError(
            f"memory_retention_days must be >= 1, got {memory_retention_days}"
        )
    _mfl = _get_int(cfg, "memory_fts_limit")
    memory_fts_limit = _mfl if _mfl is not None else 50
    _mrrk = _get_int(cfg, "memory_rrf_k")
    memory_rrf_k = _mrrk if _mrrk is not None else 60
    _mrd = _get_float(cfg, "memory_recency_days")
    memory_recency_days = _mrd if _mrd is not None else 7.0
    _v = _get_bool(cfg, "memory_local_only")
    memory_local_only = _v if _v is not None else False
    return MemoryConfig(
        use_memory_layer=use_memory_layer,
        memory_jsonl_dir=memory_jsonl_dir,
        memory_max_inject_semantic=memory_max_inject_semantic,
        memory_max_inject_episodic=memory_max_inject_episodic,
        memory_min_importance=memory_min_importance,
        memory_embed_enabled=memory_embed_enabled,
        memory_embed_dim=memory_embed_dim,
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
    _tier_values = _get_dict(cfg, "tool_safety_tiers")
    ALLOWED_TIERS = {"READ_ONLY", "WRITE_SAFE", "WRITE_DANGEROUS", "ADMIN"}
    if _tier_values is not None:
        for key, val in _tier_values.items():
            if isinstance(val, str) and val not in ALLOWED_TIERS:
                raise ConfigReloadValidationError(
                    f"tool_safety_tiers[{key!r}] must be one of "
                    f"{ALLOWED_TIERS}, got {val!r}"
                )
    tool_safety_tiers = _tier_values if _tier_values is not None else {}
    allowed_root = _get_str(cfg, "allowed_root") or ""
    approval_github_allowed_repos = _get_list_or_default(
        cfg, "approval_github_allowed_repos", []
    )
    _v = _get_bool(cfg, "gitops_push_blocked")
    gitops_push_blocked = _v if _v is not None else False
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

    _logger = logging.getLogger(__name__)
    if results.errors:
        _logger.error("Production config validation failed:")
        for err in results.errors:
            _logger.error(f"  - {err}")
        sys.exit(1)

    for warning in results.warnings:
        _logger.warning(warning)

    _v = _get_bool(cfg, "security_lockdown_enabled")
    security_lockdown_enabled = _v if _v is not None else False
    _v = _get_bool(cfg, "otel_enabled")
    otel_enabled = _v if _v is not None else False
    _v = _get_bool(cfg, "structured_log")
    structured_log = _v if _v is not None else False

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
            otel_endpoint=_get_str(cfg, "otel_endpoint") or "",
            otel_service_name=_get_str(cfg, "otel_service_name") or "llm-agent",
            audit_log_file=_get_str(cfg, "audit_log_file") or "/opt/llm/logs/audit.log",
            structured_log=structured_log,
        ),
    )
