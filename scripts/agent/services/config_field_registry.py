"""Configuration field registry — shared schema definition for config reload."""

from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import Any

from agent.services.config_validators import (
    validate_llm_context_char_limit,
    validate_llm_context_token_limit,
    validate_llm_http_timeout,
    validate_llm_max_retries,
    validate_llm_max_tokens,
    validate_llm_retry_base_delay,
    validate_llm_sse_heartbeat_timeout,
    validate_llm_sse_malformed_retry,
    validate_llm_sse_reconnect_max,
    validate_llm_temperature,
    validate_rag_refiner_max_chars_per_chunk,
    validate_rag_refiner_max_tokens,
    validate_rag_refiner_timeout,
    validate_tool_max_tool_turns,
    validate_tool_result_max_llm_chars,
)


@dataclasses.dataclass(frozen=True)
class ConfigFieldRegistry:
    """A single entry in CONFIG_FIELD_REGISTRY."""

    name: str
    section_path: str
    hot_reloadable: bool
    validator_fn: Callable[[Any], None] | None = None


_CONFIG_ENTRIES: list[ConfigFieldRegistry] = [
    # LLM section
    ConfigFieldRegistry("http_timeout", "llm", True, validate_llm_http_timeout),
    ConfigFieldRegistry(
        "context_token_limit", "llm", False, validate_llm_context_token_limit
    ),
    ConfigFieldRegistry(
        "context_char_limit", "llm", False, validate_llm_context_char_limit
    ),
    ConfigFieldRegistry("context_compress_turns", "llm", False),
    ConfigFieldRegistry("llm_temperature", "llm", True, validate_llm_temperature),
    ConfigFieldRegistry("llm_max_tokens", "llm", True, validate_llm_max_tokens),
    ConfigFieldRegistry("llm_url", "llm", True),
    ConfigFieldRegistry("llm_max_retries", "llm", True, validate_llm_max_retries),
    ConfigFieldRegistry(
        "llm_retry_base_delay", "llm", True, validate_llm_retry_base_delay
    ),
    ConfigFieldRegistry(
        "sse_heartbeat_timeout", "llm", True, validate_llm_sse_heartbeat_timeout
    ),
    ConfigFieldRegistry(
        "sse_malformed_retry", "llm", True, validate_llm_sse_malformed_retry
    ),
    ConfigFieldRegistry(
        "sse_reconnect_max", "llm", True, validate_llm_sse_reconnect_max
    ),
    ConfigFieldRegistry("llm_stream_retry_on_heartbeat_timeout", "llm", True),
    ConfigFieldRegistry("llm_stream_retry_on_malformed_chunk", "llm", True),
    # RAG section
    ConfigFieldRegistry("embed_url", "rag", True),
    ConfigFieldRegistry("web_search_url", "rag", True),
    ConfigFieldRegistry("use_refiner", "rag", True),
    ConfigFieldRegistry(
        "refiner_max_tokens", "rag", True, validate_rag_refiner_max_tokens
    ),
    ConfigFieldRegistry("refiner_timeout", "rag", True, validate_rag_refiner_timeout),
    ConfigFieldRegistry(
        "refiner_max_chars_per_chunk",
        "rag",
        True,
        validate_rag_refiner_max_chars_per_chunk,
    ),
    # Tool section
    ConfigFieldRegistry("max_tool_turns", "tool", True, validate_tool_max_tool_turns),
    ConfigFieldRegistry(
        "tool_result_max_llm_chars",
        "tool",
        True,
        validate_tool_result_max_llm_chars,
    ),
    ConfigFieldRegistry("serial_tool_calls", "tool", True),
    ConfigFieldRegistry("tool_definitions_strict", "tool", True),
    ConfigFieldRegistry("plan_blocked_tools", "tool", True),
    ConfigFieldRegistry("system_prompt_tool", "tool", True),
    ConfigFieldRegistry("system_prompts", "tool", True),
    ConfigFieldRegistry("tool_definitions", "tool", True),
    ConfigFieldRegistry("allowed_tools", "tool", True),
    ConfigFieldRegistry("routing_drift_strict", "tool", False),
    # Approval section
    ConfigFieldRegistry("approval_risk_rules", "approval", True),
    ConfigFieldRegistry("approval_protected_paths", "approval", True),
    ConfigFieldRegistry("approval_high_risk_branches", "approval", True),
    ConfigFieldRegistry("approval_shell_safe_prefixes", "approval", True),
    ConfigFieldRegistry("approval_resource_keys", "approval", True),
    ConfigFieldRegistry("approval_dry_run_tools", "approval", True),
    ConfigFieldRegistry("tool_safety_tiers", "approval", True),
    ConfigFieldRegistry("allowed_root", "approval", True),
    ConfigFieldRegistry("approval_github_allowed_repos", "approval", True),
    ConfigFieldRegistry("gitops_push_blocked", "approval", False),
    # Memory section
    ConfigFieldRegistry("memory_retention_days", "memory", True),
    ConfigFieldRegistry("memory_local_only", "memory", True),
    ConfigFieldRegistry("use_memory_layer", "memory", False),
    ConfigFieldRegistry("memory_embed_enabled", "memory", False),
    # MCP section
    ConfigFieldRegistry("security_profile", "mcp", True),
    ConfigFieldRegistry("security_lockdown_enabled", "mcp", True),
]

CONFIG_FIELD_REGISTRY: dict[str, ConfigFieldRegistry] = {
    entry.name: entry for entry in _CONFIG_ENTRIES
}


def registry_for(section_path: str) -> list[ConfigFieldRegistry]:
    """Return all ConfigFieldRegistry entries matching the given section path."""
    return [entry for entry in _CONFIG_ENTRIES if entry.section_path == section_path]
