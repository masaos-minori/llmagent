#!/usr/bin/env python3
"""scripts/agent/config_builders.py

Agent config assembly entry point: load_config, resolved_config_dir, the
production-validation and assembly pipeline, and build_agent_config.

The per-section builder helpers this module delegates to live in
agent.config_section_builders.py.

Import from here:  from agent.config_builders import (
    build_agent_config, load_config, ConfigLoadError,
)
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from shared.config_errors import ConfigLoadError
from shared.config_loader import ConfigLoader
from shared.mcp_config import (
    SecurityProfile,
    _build_mcp_servers,
)
from shared.runtime_paths import resolve_config_dir
from shared.tool_registry import get_registry

from agent.config_dataclasses import (
    AgentConfig,
    MCPConfig,
    ObservabilityConfig,
)
from agent.config_section_builders import (
    _build_approval_config,
    _build_diagnostics_config,
    _build_llm_config,
    _build_memory_config,
    _build_rag_config,
    _build_tool_config,
    _get_or_default,
    _get_str_or_default,
)
from agent.production_config_validator import ProductionConfigValidator
from agent.services.exceptions import ConfigReloadValidationError
from agent.services.typed_validators import (
    _get_bool,
    _get_int,
)

logger = logging.getLogger(__name__)


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
            logger.error("  - %s", err)
        raise ConfigReloadValidationError(
            f"Production config validation failed: {results.errors}"
        )
    for warning in results.warnings:
        logger.warning(warning)


def _assemble_agent_config(
    cfg: dict[str, Any],
    system_prompt_tool: str,
    security_profile_val: SecurityProfile,
) -> AgentConfig:
    """Assemble AgentConfig by delegating to builder functions."""
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
        ),
        approval=_build_approval_config(cfg),
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
