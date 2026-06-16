#!/usr/bin/env python3
"""agent/config_builders.py

Constants, builder functions, ConfigLoadError, load_config, and build_agent_config.

Import from here:  from agent.config_builders import (
    build_agent_config, load_config, ConfigLoadError,
)
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from shared.config_loader import ConfigLoader
from shared.mcp_config import (
    _build_mcp_servers,  # noqa: F401 — re-exported via agent.config
)

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

_CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"


# ---------------------------------------------------------------------------
# Exception + loader
# ---------------------------------------------------------------------------


class ConfigLoadError(RuntimeError):
    """Raised when configuration files cannot be loaded."""


def load_config() -> dict[str, Any]:
    """Load configuration from files.  No module-level cache — always fresh."""
    try:
        return ConfigLoader().load_all()
    except (OSError, ValueError, TypeError) as e:
        raise ConfigLoadError(f"Config load failed: {e}") from e


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
    "delete_file",
    "delete_directory",
    "move_file",
]


# ---------------------------------------------------------------------------
# Builder functions
# ---------------------------------------------------------------------------


def _build_llm_config(cfg: dict[str, Any]) -> LLMConfig:
    return LLMConfig(
        llm_url=cfg.get("llm_url", ""),
        http_timeout=float(cfg.get("http_timeout", 30.0)),
        llm_max_retries=int(cfg.get("llm_max_retries", 3)),
        llm_retry_base_delay=float(cfg.get("llm_retry_base_delay", 1.0)),
        llm_temperature=float(cfg.get("llm_temperature", 0.2)),
        llm_max_tokens=int(cfg.get("llm_max_tokens", 1024)),
        title_llm_temperature=float(cfg.get("title_llm_temperature", 0.1)),
        title_llm_max_tokens=int(cfg.get("title_llm_max_tokens", 20)),
        sse_heartbeat_timeout=float(cfg.get("sse_heartbeat_timeout", 30.0)),
        sse_malformed_retry=int(cfg.get("sse_malformed_retry", 2)),
        sse_reconnect_max=int(cfg.get("sse_reconnect_max", 1)),
        llm_stream_retry_on_heartbeat_timeout=bool(
            cfg.get("llm_stream_retry_on_heartbeat_timeout", True),
        ),
        llm_stream_retry_on_malformed_chunk=bool(
            cfg.get("llm_stream_retry_on_malformed_chunk", False),
        ),
        tokenize_url=cfg.get("tokenize_url", ""),
        context_token_limit=int(cfg.get("context_token_limit", 0)),
        context_char_limit=int(cfg.get("context_char_limit", 8000)),
        context_compress_turns=int(cfg.get("context_compress_turns", 4)),
        history_protect_turns=int(cfg.get("history_protect_turns", 2)),
        budget_warn_ratio=float(cfg.get("budget_warn_ratio", 0.8)),
    )


def _build_rag_config(cfg: dict[str, Any]) -> RAGConfig:
    return RAGConfig(
        top_k_search=int(cfg.get("top_k_search", 20)),
        top_k_rerank=int(cfg.get("top_k_rerank", 15)),
        max_chunks_per_doc=int(cfg.get("max_chunks_per_doc", 2)),
        web_search_url=cfg.get("web_search_url", ""),
        web_search_max_results=int(cfg.get("web_search_max_results", 5)),
        embed_url=cfg.get("embed_url", "http://127.0.0.1:8003/embedding"),
        use_semantic_cache=bool(cfg.get("use_semantic_cache", False)),
        semantic_cache_threshold=float(cfg.get("semantic_cache_threshold", 0.92)),
        semantic_cache_max_size=int(cfg.get("semantic_cache_max_size", 100)),
        use_refiner=bool(cfg.get("use_refiner", False)),
        refiner_max_tokens=int(cfg.get("refiner_max_tokens", 512)),
        refiner_timeout=float(cfg.get("refiner_timeout", 30.0)),
        refiner_max_chars_per_chunk=int(cfg.get("refiner_max_chars_per_chunk", 300)),
    )


def _build_tool_config(cfg: dict[str, Any], system_prompt_tool: str) -> ToolConfig:
    return ToolConfig(
        tool_cache_ttl=float(cfg.get("tool_cache_ttl", 300)),
        tool_cache_max_size=int(cfg.get("tool_cache_max_size", 200)),
        serial_tool_calls=bool(cfg.get("serial_tool_calls", False)),
        auto_inject_notes=bool(cfg.get("auto_inject_notes", True)),
        use_tool_summarize=bool(cfg.get("use_tool_summarize", False)),
        tool_summarize_threshold=int(cfg.get("tool_summarize_threshold", 3000)),
        tool_definitions_strict=bool(cfg.get("tool_definitions_strict", False)),
        tool_dedup_max_repeats=int(cfg.get("tool_dedup_max_repeats", 3)),
        tool_cycle_detect_window=int(cfg.get("tool_cycle_detect_window", 2)),
        tool_error_max_consecutive=int(cfg.get("tool_error_max_consecutive", 3)),
        tool_error_retry_max=int(cfg.get("tool_error_retry_max", 1)),
        tool_concurrency_limits=dict(cfg.get("tool_concurrency_limits", {})),
        masked_fields=list(cfg.get("masked_fields", ["file_content"])),
        plan_blocked_tools=list(
            cfg.get("plan_blocked_tools", _DEFAULT_PLAN_BLOCKED_TOOLS),
        ),
        max_tool_turns=int(cfg.get("max_tool_turns", 5)),
        tool_result_max_llm_chars=int(cfg.get("tool_result_max_llm_chars", 8000)),
        tool_results_turn_max_chars=int(cfg.get("tool_results_turn_max_chars", 50000)),
        use_tool_dag=bool(cfg.get("use_tool_dag", False)),
        tool_definitions=list(cfg.get("tool_definitions", [])),
        system_prompts=dict(
            cfg.get("system_prompts", {"default": system_prompt_tool}),
        ),
        system_prompt_tool=system_prompt_tool,
        allowed_tools=list(cfg.get("allowed_tools", [])),
        plugin_tool_override=bool(cfg.get("plugin_tool_override", False)),
    )


def _build_memory_config(cfg: dict[str, Any]) -> MemoryConfig:
    return MemoryConfig(
        use_memory_layer=bool(cfg.get("use_memory_layer", False)),
        memory_jsonl_dir=cfg.get("memory_jsonl_dir", "/opt/llm/memory"),
        memory_max_inject_semantic=int(cfg.get("memory_max_inject_semantic", 5)),
        memory_max_inject_episodic=int(cfg.get("memory_max_inject_episodic", 3)),
        memory_min_importance=float(cfg.get("memory_min_importance", 0.3)),
        memory_embed_enabled=bool(cfg.get("memory_embed_enabled", False)),
        memory_embed_dim=int(cfg.get("memory_embed_dim", 384)),
        memory_dedup_threshold=float(cfg.get("memory_dedup_threshold", 0.3)),
        memory_max_content_chars=int(cfg.get("memory_max_content_chars", 500)),
        memory_embed_timeout_sec=float(cfg.get("memory_embed_timeout_sec", 5.0)),
        memory_retention_days=int(cfg.get("memory_retention_days", 90)),
        memory_fts_limit=int(cfg.get("memory_fts_limit", 50)),
        memory_rrf_k=int(cfg.get("memory_rrf_k", 60)),
        memory_recency_days=float(cfg.get("memory_recency_days", 7.0)),
    )


def _build_approval_config(cfg: dict[str, Any]) -> ApprovalConfig:
    return ApprovalConfig(
        approval_risk_rules=dict(
            cfg.get("approval_risk_rules", _DEFAULT_APPROVAL_RISK_RULES),
        ),
        approval_protected_paths=list(
            cfg.get("approval_protected_paths", _DEFAULT_PROTECTED_PATHS),
        ),
        approval_high_risk_branches=list(
            cfg.get("approval_high_risk_branches", ["main", "master"]),
        ),
        approval_shell_safe_prefixes=list(
            cfg.get("approval_shell_safe_prefixes", _DEFAULT_SHELL_SAFE_PREFIXES),
        ),
        approval_resource_keys=dict(
            cfg.get("approval_resource_keys", _DEFAULT_RESOURCE_KEYS),
        ),
        approval_dry_run_tools=list(
            cfg.get("approval_dry_run_tools", _DEFAULT_DRY_RUN_TOOLS),
        ),
        tool_safety_tiers=dict(cfg.get("tool_safety_tiers", {})),
        allowed_root=cfg.get("allowed_root", ""),
        approval_github_allowed_repos=list(
            cfg.get("approval_github_allowed_repos", []),
        ),
        gitops_push_blocked=bool(cfg.get("gitops_push_blocked", False)),
        gitops_force_push_blocked=bool(cfg.get("gitops_force_push_blocked", True)),
        gitops_protected_branches=list(
            cfg.get("gitops_protected_branches", ["main", "master"])
        ),
    )


def build_agent_config(cfg_override: dict[str, Any] | None = None) -> AgentConfig:
    """Construct AgentConfig from a config dict.

    If cfg_override is provided it is used directly (for /reload and tests).
    Otherwise configuration is loaded from files via load_config().
    """
    cfg = cfg_override if cfg_override is not None else load_config()
    system_prompt_tool = cfg.get("system_prompt_tool", "")
    return AgentConfig(
        llm=_build_llm_config(cfg),
        rag=_build_rag_config(cfg),
        tool=_build_tool_config(cfg, system_prompt_tool),
        memory=_build_memory_config(cfg),
        mcp=MCPConfig(
            mcp_servers=_build_mcp_servers(cfg),
            mcp_watchdog_interval=float(cfg.get("mcp_watchdog_interval", 0.0)),
            mcp_watchdog_max_restarts=int(cfg.get("mcp_watchdog_max_restarts", 3)),
            github_url=cfg.get("github_server_url", "http://127.0.0.1:8006"),
        ),
        approval=_build_approval_config(cfg),
        obs=ObservabilityConfig(
            otel_enabled=bool(cfg.get("otel_enabled", False)),
            otel_endpoint=cfg.get("otel_endpoint", ""),
            otel_service_name=cfg.get("otel_service_name", "llm-agent"),
            audit_log_file=cfg.get("audit_log_file", "/opt/llm/logs/audit.log"),
            structured_log=bool(cfg.get("structured_log", False)),
        ),
    )
