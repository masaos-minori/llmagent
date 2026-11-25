"""scripts/agent/services/config_field_registry.py — Configuration field registry: shared schema definition for config reload."""

from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING

from shared.config_field_types import (
    RULE_BOOL,
    RULE_FLOAT,
    RULE_INT,
    RULE_STR,
    RULE_STR_LIST,
    FieldRule,
)

from agent.services.config_validators import (
    validate_allowed_root,
    validate_allowed_tools,
    validate_approval_github_allowed_repos,
    validate_approval_high_risk_branches,
    validate_approval_medium_preview_fallback,
    validate_approval_protected_paths,
    validate_approval_shell_safe_prefixes,
    validate_context_compress_turns,
    validate_disabled_tools,
    validate_gitops_push_blocked,
    validate_llm_context_char_limit,
    validate_llm_context_token_limit,
    validate_llm_http_timeout,
    validate_llm_max_tokens,
    validate_llm_retry_base_delay,
    validate_llm_sse_heartbeat_timeout,
    validate_llm_sse_malformed_retry,
    validate_llm_sse_reconnect_max,
    validate_llm_stream_retry_on_heartbeat_timeout,
    validate_llm_stream_retry_on_malformed_chunk,
    validate_llm_temperature,
    validate_llm_url,
    validate_memory_embed_enabled,
    validate_memory_embed_url,
    validate_memory_local_only,
    validate_memory_max_pinned,
    validate_memory_retention_days,
    validate_plan_blocked_tools,
    validate_serial_tool_calls,
    validate_tool_max_tool_turns,
    validate_tool_policy_mode,
    validate_tool_result_max_llm_chars,
    validate_use_memory_layer,
)
from agent.services.exceptions import ConfigReloadValidationError

if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import Any


@dataclasses.dataclass(frozen=True)
class ConfigFieldRegistry:
    """A single entry in CONFIG_FIELD_REGISTRY.

    Attributes:
        name: Field name as it appears in the configuration file.
        section_path: Section the field belongs to (llm, tool, approval, memory).
        hot_reloadable: False means the value is read once at startup and a change
            stays pending until restart (REQ-003).
        validator_fn: Validator the reload candidate runs, always the one that
            composes ``field_type`` (REQ-001, REQ-010).
        field_type: Declared type rule from shared.config_field_types, so the
            registry and the validator reference the same rule object.
        allow_empty: Emptiness rule for the field, matching the flag the validator
            passes to the primitive. Pinned per entry by
            ``tests/agent/services/test_config_reload_parity.py``.
    """

    name: str
    section_path: str
    hot_reloadable: bool
    validator_fn: Callable[[Any], None] | None = None
    field_type: FieldRule | None = None
    allow_empty: bool = False


_CONFIG_ENTRIES: list[ConfigFieldRegistry] = [
    # LLM section
    ConfigFieldRegistry(
        "http_timeout", "llm", True, validate_llm_http_timeout, RULE_FLOAT
    ),
    ConfigFieldRegistry(
        "context_token_limit",
        "llm",
        False,
        validate_llm_context_token_limit,
        RULE_INT,
    ),
    ConfigFieldRegistry(
        "context_char_limit",
        "llm",
        False,
        validate_llm_context_char_limit,
        RULE_INT,
    ),
    ConfigFieldRegistry(
        "context_compress_turns",
        "llm",
        False,
        validate_context_compress_turns,
        RULE_INT,
    ),
    ConfigFieldRegistry(
        "llm_temperature", "llm", True, validate_llm_temperature, RULE_FLOAT
    ),
    ConfigFieldRegistry(
        "llm_max_tokens", "llm", True, validate_llm_max_tokens, RULE_INT
    ),
    ConfigFieldRegistry(
        "llm_url", "llm", True, validate_llm_url, RULE_STR, allow_empty=True
    ),
    ConfigFieldRegistry(
        "llm_retry_base_delay", "llm", True, validate_llm_retry_base_delay, RULE_FLOAT
    ),
    ConfigFieldRegistry(
        "sse_heartbeat_timeout",
        "llm",
        True,
        validate_llm_sse_heartbeat_timeout,
        RULE_FLOAT,
    ),
    ConfigFieldRegistry(
        "sse_malformed_retry", "llm", True, validate_llm_sse_malformed_retry, RULE_INT
    ),
    ConfigFieldRegistry(
        "sse_reconnect_max", "llm", True, validate_llm_sse_reconnect_max, RULE_INT
    ),
    ConfigFieldRegistry(
        "llm_stream_retry_on_heartbeat_timeout",
        "llm",
        True,
        validate_llm_stream_retry_on_heartbeat_timeout,
        RULE_BOOL,
    ),
    ConfigFieldRegistry(
        "llm_stream_retry_on_malformed_chunk",
        "llm",
        True,
        validate_llm_stream_retry_on_malformed_chunk,
        RULE_BOOL,
    ),
    # Tool section
    ConfigFieldRegistry(
        "max_tool_turns", "tool", True, validate_tool_max_tool_turns, RULE_INT
    ),
    ConfigFieldRegistry(
        "tool_result_max_llm_chars",
        "tool",
        True,
        validate_tool_result_max_llm_chars,
        RULE_INT,
    ),
    ConfigFieldRegistry(
        "serial_tool_calls", "tool", True, validate_serial_tool_calls, RULE_BOOL
    ),
    ConfigFieldRegistry(
        "plan_blocked_tools",
        "tool",
        True,
        validate_plan_blocked_tools,
        RULE_STR_LIST,
        allow_empty=True,
    ),
    ConfigFieldRegistry(
        "allowed_tools",
        "tool",
        True,
        validate_allowed_tools,
        RULE_STR_LIST,
        allow_empty=True,
    ),
    ConfigFieldRegistry(
        "tool_policy_mode", "tool", True, validate_tool_policy_mode, RULE_STR
    ),
    ConfigFieldRegistry(
        "disabled_tools",
        "tool",
        True,
        validate_disabled_tools,
        RULE_STR_LIST,
        allow_empty=True,
    ),
    # Approval section
    ConfigFieldRegistry(
        "approval_protected_paths",
        "approval",
        True,
        validate_approval_protected_paths,
        RULE_STR_LIST,
        allow_empty=True,
    ),
    ConfigFieldRegistry(
        "approval_high_risk_branches",
        "approval",
        True,
        validate_approval_high_risk_branches,
        RULE_STR_LIST,
        allow_empty=True,
    ),
    ConfigFieldRegistry(
        "approval_shell_safe_prefixes",
        "approval",
        True,
        validate_approval_shell_safe_prefixes,
        RULE_STR_LIST,
        allow_empty=True,
    ),
    ConfigFieldRegistry(
        "allowed_root", "approval", True, validate_allowed_root, RULE_STR
    ),
    ConfigFieldRegistry(
        "approval_github_allowed_repos",
        "approval",
        True,
        validate_approval_github_allowed_repos,
        RULE_STR_LIST,
        allow_empty=True,
    ),
    ConfigFieldRegistry(
        "gitops_push_blocked",
        "approval",
        False,
        validate_gitops_push_blocked,
        RULE_BOOL,
    ),
    ConfigFieldRegistry(
        "approval_medium_preview_fallback",
        "approval",
        False,
        validate_approval_medium_preview_fallback,
        RULE_BOOL,
    ),
    # Memory section
    ConfigFieldRegistry(
        "memory_retention_days",
        "memory",
        True,
        validate_memory_retention_days,
        RULE_INT,
    ),
    ConfigFieldRegistry(
        "memory_max_pinned", "memory", True, validate_memory_max_pinned, RULE_INT
    ),
    ConfigFieldRegistry(
        "memory_local_only", "memory", True, validate_memory_local_only, RULE_BOOL
    ),
    ConfigFieldRegistry(
        "use_memory_layer", "memory", False, validate_use_memory_layer, RULE_BOOL
    ),
    ConfigFieldRegistry(
        "memory_embed_enabled",
        "memory",
        False,
        validate_memory_embed_enabled,
        RULE_BOOL,
    ),
    ConfigFieldRegistry(
        "memory_embed_url",
        "memory",
        True,
        validate_memory_embed_url,
        RULE_STR,
        allow_empty=True,
    ),
]

CONFIG_FIELD_REGISTRY: dict[str, ConfigFieldRegistry] = {
    entry.name: entry for entry in _CONFIG_ENTRIES
}


def registry_for(section_path: str) -> list[ConfigFieldRegistry]:
    """Return the hot-reloadable ConfigFieldRegistry entries for the given section path.

    Startup-only entries are excluded: they must not enter a reload candidate
    (REQ-003). Use startup_only_for() for the complementary set.
    """
    return [
        entry
        for entry in _CONFIG_ENTRIES
        if entry.section_path == section_path and entry.hot_reloadable
    ]


def startup_only_for(section_path: str) -> list[ConfigFieldRegistry]:
    """Return the ConfigFieldRegistry entries the given section reads only at startup."""
    return [
        entry
        for entry in _CONFIG_ENTRIES
        if entry.section_path == section_path and not entry.hot_reloadable
    ]


def validate_section_fields(section_path: str, section: Any) -> None:
    """Run every registered validator for one section against a built section.

    The startup assembly calls this for each validated section, so the startup path
    and the reload candidate apply the same semantic rules from the same registry
    entries, and a field the registry does not list is validated by neither (REQ-001,
    REQ-010). A rejected value raises the same key-naming error the reload path
    raises, without echoing the value.
    """
    for entry in _CONFIG_ENTRIES:
        if entry.section_path != section_path or entry.validator_fn is None:
            continue
        try:
            entry.validator_fn(section)
        except ValueError as exc:
            raise ConfigReloadValidationError(str(exc)) from exc
