#!/usr/bin/env python3
"""scripts/agent/config_builders.py

Agent config assembly entry point: load_config, resolved_config_dir, the
production-validation and assembly pipeline, and build_agent_config.

The per-section builder helpers this module delegates to live in
agent.config_section_builders.py.

Import from here:  from agent.config_builders import (
    agent_config_payload, build_agent_config, load_config, ConfigLoadError,
)
"""

from __future__ import annotations

import dataclasses
import logging
from pathlib import Path
from typing import Any

from db.config import build_db_config
from db.maintenance import DbMaintenanceConfig
from shared.config_errors import ConfigLoadError
from shared.config_loader import ConfigLoader
from shared.mcp_config import _MCP_SERVER_KEYS, _build_mcp_servers
from shared.runtime_paths import resolve_config_dir
from shared.tool_registry import get_registry

from agent.config_dataclasses import (
    AgentConfig,
    ApprovalConfig,
    DiagnosticsConfig,
    LLMConfig,
    MCPConfig,
    MemoryConfig,
    ObservabilityConfig,
    ToolConfig,
)
from agent.config_section_builders import (
    _build_approval_config,
    _build_diagnostics_config,
    _build_llm_config,
    _build_memory_config,
    _build_tool_config,
    _get_or_default,
    _get_str_or_default,
)
from agent.production_config_validator import ProductionConfigValidator
from agent.services.config_field_registry import validate_section_fields
from agent.services.exceptions import ConfigReloadValidationError
from agent.services.typed_validators import (
    _get_bool,
    _get_float,
    _get_int,
)

logger = logging.getLogger(__name__)

# AgentConfig sections rendered as flat payload keys by agent_config_payload().
_PAYLOAD_SECTIONS: tuple[str, ...] = ("llm", "tool", "memory", "approval", "obs")
# Section objects _section_payload() renders: every dataclass the renderer passes it.
_PayloadSection = (
    LLMConfig
    | ToolConfig
    | MemoryConfig
    | ApprovalConfig
    | ObservabilityConfig
    | DiagnosticsConfig
)
# AgentConfig fields that are not flat scalar keys: the section objects, the nested
# diagnostics table, and the MCP container.
_PAYLOAD_AGENT_FIELDS: frozenset[str] = frozenset(
    (
        "db",
        "maintenance",
        "llm",
        "tool",
        "memory",
        "mcp",
        "approval",
        "obs",
        "diagnostics",
        "messages",
    )
)


def _section_payload(section: _PayloadSection) -> dict[str, Any]:
    """Return one section dataclass as its ``config key -> value`` mapping."""
    return {f.name: getattr(section, f.name) for f in dataclasses.fields(section)}


def resolved_config_dir() -> Path:
    """Return the resolved agent config directory via the shared resolver.

    Replaces the stale module-level config-dir constant (which pointed at a
    nonexistent ``scripts/config``). Evaluating the resolver at call time keeps
    the env-var and compiled-adjacent branches live instead of fixed at import.
    """
    return resolve_config_dir()


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
# Assembly pipeline
# ---------------------------------------------------------------------------


def _resolve_config_source_and_registry(
    cfg_override: dict[str, Any] | None,
) -> tuple[dict[str, Any], set[str]]:
    """Resolve config source and tool registry. Returns (cfg, known_tools)."""
    cfg = cfg_override if cfg_override is not None else load_config()
    try:
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
    known_tools: set[str],
) -> None:
    """Run production config validation; exit on errors."""
    results = ProductionConfigValidator().validate(cfg, known_tools=known_tools)
    if results.errors:
        logger.error("Production config validation failed:")
        for err in results.errors:
            logger.error("  - %s", err)
        raise ConfigReloadValidationError(
            f"Production config validation failed: {results.errors}"
        )
    for warning in results.warnings:
        logger.warning(warning)


def _assemble_agent_config(cfg: dict[str, Any]) -> AgentConfig:
    """Assemble AgentConfig by delegating to builder functions.

    Every section the field registry covers is validated through the registry after
    it is built, so the startup path applies exactly the rules the reload candidate
    applies (REQ-001, REQ-010).
    """
    otel_enabled = _get_or_default(cfg, "otel_enabled", _get_bool, False)
    structured_log = _get_or_default(cfg, "structured_log", _get_bool, False)
    llm = _build_llm_config(cfg)
    tool = _build_tool_config(cfg)
    memory = _build_memory_config(cfg)
    approval = _build_approval_config(cfg)
    for section_path, section in (
        ("llm", llm),
        ("tool", tool),
        ("memory", memory),
        ("approval", approval),
    ):
        validate_section_fields(section_path, section)
    return AgentConfig(
        llm=llm,
        tool=tool,
        memory=memory,
        mcp=MCPConfig(mcp_servers=_build_mcp_servers(cfg)),
        approval=approval,
        obs=ObservabilityConfig(
            otel_enabled=otel_enabled,
            otel_endpoint=_get_str_or_default(cfg, "otel_endpoint"),
            otel_service_name=_get_str_or_default(
                cfg, "otel_service_name", "llm-agent"
            ),
            audit_log_file=_get_str_or_default(
                cfg, "audit_log_file", "/opt/llm/logs/audit.log"
            ),
            structured_log=structured_log,
        ),
        diagnostics=_build_diagnostics_config(cfg),
        db=build_db_config(cfg),
        maintenance=DbMaintenanceConfig.from_mapping(cfg),
        agent_memory_max_startup_snippets=_get_or_default(
            cfg, "agent_memory_max_startup_snippets", _get_int, 10
        ),
        pending_timeout_minutes=_get_or_default(
            cfg, "pending_timeout_minutes", _get_int, 10
        ),
        approval_grant_ttl_seconds=_get_or_default(
            cfg, "approval_grant_ttl_seconds", _get_float, 300.0
        ),
        shutdown_deadline_seconds=_get_or_default(
            cfg, "shutdown_deadline_seconds", _get_float, 45.0
        ),
        shutdown_settle_seconds=_get_or_default(
            cfg, "shutdown_settle_seconds", _get_float, 10.0
        ),
        shutdown_termination_confirm_seconds=_get_or_default(
            cfg, "shutdown_termination_confirm_seconds", _get_float, 2.0
        ),
        shutdown_force_exit_on_second_sigint=_get_or_default(
            cfg, "shutdown_force_exit_on_second_sigint", _get_bool, False
        ),
    )


def build_agent_config(cfg_override: dict[str, Any] | None = None) -> AgentConfig:
    """Construct AgentConfig from a config dict.

    If cfg_override is provided it is used directly (for /reload and tests).
    Otherwise configuration is loaded from files via load_config().

    This is also the candidate-build entry the reload path calls with
    ``cfg_override`` set (REQ-002): the candidate is a typed ``AgentConfig`` built by
    the same production validation and section assembly startup uses, and building it
    mutates no live state — the payload dict is read, never written.
    """
    cfg, known_tools = _resolve_config_source_and_registry(cfg_override)
    _run_production_validation(cfg, known_tools)
    return _assemble_agent_config(cfg)


def agent_config_payload(cfg: AgentConfig) -> dict[str, Any]:
    """Render a typed AgentConfig back into the flat payload shape the builders read.

    This is the inverse of `build_agent_config` for the keys the builders read, and
    the reload candidate phase uses it to apply a payload on top of the live
    configuration (REQ-002): `build_agent_config` always sees a complete
    configuration, so a payload that names one field changes only that field, and a
    value the payload does not name keeps the value startup already validated.

    `messages` is not rendered: no section builder reads its key, so the candidate
    takes the same default the live configuration has. `McpServerConfig.key` and
    `McpServerConfig.fields` are not rendered either: only the declared
    `_MCP_SERVER_KEYS` are configuration input.
    """
    payload: dict[str, Any] = {
        f.name: getattr(cfg.db, f.name) for f in dataclasses.fields(cfg.db)
    }
    payload.update(
        {
            f"sqlite_{f.name}": getattr(cfg.maintenance, f.name)
            for f in dataclasses.fields(cfg.maintenance)
        }
    )
    for section_path in _PAYLOAD_SECTIONS:
        payload.update(_section_payload(getattr(cfg, section_path)))
    payload["diagnostics"] = _section_payload(cfg.diagnostics)
    payload["mcp_servers"] = {
        server_key: {name: getattr(server, name) for name in _MCP_SERVER_KEYS}
        for server_key, server in cfg.mcp.mcp_servers.items()
    }
    payload.update(
        {
            f.name: getattr(cfg, f.name)
            for f in dataclasses.fields(cfg)
            if f.name not in _PAYLOAD_AGENT_FIELDS
        }
    )
    return payload
