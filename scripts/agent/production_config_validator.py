"""scripts/agent/production_config_validator.py"""

from __future__ import annotations

import logging
from collections.abc import Mapping
from dataclasses import fields as dataclass_fields
from typing import TYPE_CHECKING

from shared.component_mandatoriness import (
    ClassificationConflictError,
    UnknownComponentError,
    check_required_agreement,
)
from shared.config_validator import ConfigValidationResult

if TYPE_CHECKING:
    from shared.component_mandatoriness import ComponentClassification
    from shared.runtime_tool_registry import RuntimeToolRegistry

logger = logging.getLogger(__name__)

# Keys where explicit false is an error in production (absent is acceptable)
_REQUIRED_NOT_FALSE_KEYS: tuple[str, ...] = ()

# Valid top-level keys derived from dataclass field introspection.
# Includes all sub-config field names + AgentConfig-level keys + build_agent_config() direct keys.
_VALID_PRODUCTION_KEYS: frozenset[str] | None = None


def _resolve_known_tools(known_tools: set[str] | None) -> set[str]:
    """Resolve the known tool name set, falling back to the tool registry.

    Raises `ValueError` if `known_tools` was not provided and the registry lookup
    fails, producing an actionable error message rather than silently skipping.
    """
    if known_tools is not None:
        return known_tools
    try:
        from shared.tool_registry import get_registry

        return set(get_registry().get_all_tool_names())
    except ValueError as exc:
        msg = (
            "Tool registry resolution failed: duplicate registration "
            "(cannot determine authoritative tool set for production validation)"
        )
        raise ValueError(msg) from exc
    except ImportError as exc:
        msg = (
            "Tool registry resolution failed: module import error "
            "(cannot determine authoritative tool set for production validation)"
        )
        raise ValueError(msg) from exc


# Agentcfg003 REQ-011: the removed per-tool maps have no compatibility reader.
# They are subtracted from the introspected valid-key set explicitly so a stale
# deployed config is rejected as an unknown key with the key named, independent
# of when the dataclass fields themselves are removed.
_REMOVED_PRODUCTION_KEYS: frozenset[str] = frozenset(
    {
        "tool_safety_tiers",
        "approval_risk_rules",
        "approval_resource_keys",
        "approval_dry_run_tools",
    }
)

# The named git write tools carry a declared-tier risk floor (see
# _check_approval_risk_floor).
_GIT_RISK_FLOOR_TOOLS: frozenset[str] = frozenset(
    ("git_checkout", "git_pull", "git_push")
)


def _check_approval_risk_floor(
    runtime_tools: RuntimeToolRegistry | None,
    known_tools: set[str] | None = None,
    errors: list[str] | None = None,
) -> list[str]:
    """Return git write tools whose declared tier resolves below the risk floor.

    Agentcfg003 REQ-004/REQ-007 (AC-04): the floor reads each registered tool's
    declared ``agent_safety_tier`` mapped through ``_TIER_TO_RISK`` — the removed
    ``approval_risk_rules``/``tool_safety_tiers`` maps no longer contribute. The
    named git write tools must declare a tier whose mapped risk is above NONE; a
    registered tool with no usable declaration (missing field or unrecognized
    tier value) is reported fail-closed. A tool absent from the runtime registry
    is not flagged: ``classify_risk()`` resolves it to HIGH (UNKNOWN fail-safe),
    exactly as before. When ``runtime_tools`` is None there is no declared source
    to read: config validation runs before /v1/tools discovery, so enforcement
    lives at the discovery schema gate, at ``classify_risk()`` decision time,
    and in the routing drift report. The MEDIUM-to-HIGH escalation via
    ``approval_protected_paths`` remains a runtime decision.
    """
    from agent.tool_policy import _TIER_TO_RISK, RiskLevel

    try:
        resolved_tools = _resolve_known_tools(known_tools)
    except ValueError as exc:
        if errors is not None:
            errors.append(str(exc))
        return []
    targets = _GIT_RISK_FLOOR_TOOLS & resolved_tools
    if runtime_tools is None:
        return []
    below_floor: list[str] = []
    for tool_name in sorted(targets):
        try:
            tool = runtime_tools.get(tool_name)
        except KeyError:
            continue
        tier = getattr(tool, "agent_safety_tier", None)
        if tier is None:
            below_floor.append(f"'{tool_name}' missing declared agent_safety_tier")
            continue
        base = _TIER_TO_RISK.get(str(tier))
        if base is None:
            below_floor.append(f"'{tool_name}' unrecognized declared tier {tier!r}")
        elif base is RiskLevel.NONE:
            below_floor.append(
                f"'{tool_name}' declared tier {tier!r} effective risk {base.value}"
            )
    return below_floor


def _get_valid_production_keys() -> frozenset[str]:
    """Return the set of valid top-level config keys.

    Derived from dataclass field introspection on all sub-config classes
    plus AgentConfig-level keys and build_agent_config() direct keys.
    Cached in _VALID_PRODUCTION_KEYS for efficiency.
    """
    global _VALID_PRODUCTION_KEYS
    if _VALID_PRODUCTION_KEYS is not None:
        return _VALID_PRODUCTION_KEYS

    from agent.config_dataclasses import (
        ApprovalConfig,
        DiagnosticsConfig,
        LLMConfig,
        MCPConfig,
        MemoryConfig,
        MessageRoleConfig,
        ObservabilityConfig,
        RAGConfig,
        ToolConfig,
    )

    valid_keys: set[str] = set()
    for cls in [
        LLMConfig,
        RAGConfig,
        ToolConfig,
        MemoryConfig,
        MCPConfig,
        ApprovalConfig,
        ObservabilityConfig,
        DiagnosticsConfig,
        MessageRoleConfig,
    ]:
        for f in dataclass_fields(cls):
            valid_keys.add(f.name)

    # AgentConfig-level key
    valid_keys.add("agent_memory_max_startup_snippets")

    # AgentConfig-level key: Agent-side stale-pending timeout window moved here
    # from config/mcp_dedup.toml (seq 03). Registered so
    # _check_unknown_production_keys does not reject it as an unknown top-level
    # key during build_agent_config.
    valid_keys.add("pending_timeout_minutes")

    # build_agent_config() direct keys (not mapped to any sub-config)
    valid_keys.add("system_prompt_tool")

    # Nested-table section key: _build_diagnostics_config() reads cfg["diagnostics"]
    # as a whole table, so the section name itself (not its inner fields, already
    # added above via DiagnosticsConfig) is a valid top-level key.
    valid_keys.add("diagnostics")

    # Keys consumed by other subsystems (scripts/db/, scripts/rag/) that share
    # config/agent.toml but are not part of any AgentConfig sub-dataclass.
    valid_keys.update(
        {
            "rag_db_path",
            "session_db_path",
            "sqlite_archive_dir",
            "sqlite_archive_max_age_days",
            "sqlite_archive_max_files",
            "sqlite_busy_timeout_ms",
            "sqlite_corrupt_archive_max_age_days",
            "sqlite_corrupt_archive_max_files",
            "sqlite_drill_artifact_max_age_days",
            "sqlite_drill_artifact_max_files",
            "sqlite_quarantine_max_age_days",
            "sqlite_quarantine_max_files",
            "sqlite_retention_max_age_days",
            "sqlite_retention_max_sessions",
            "sqlite_timeout",
            "sqlite_vec_so",
            "sqlite_wal_checkpoint_mode",
            "workflow_db_path",
        }
    )

    _VALID_PRODUCTION_KEYS = frozenset(valid_keys - _REMOVED_PRODUCTION_KEYS)
    return _VALID_PRODUCTION_KEYS


class ProductionConfigValidator:
    """Validate configuration against production security requirements.

    Checks the declared-metadata risk floor and other production-critical
    settings; removed per-tool maps are rejected as unknown keys (REQ-011).
    """

    def validate(
        self,
        config: Mapping[str, object],
        known_tools: set[str] | None = None,
        runtime_tools: RuntimeToolRegistry | None = None,
    ) -> ConfigValidationResult:
        """Validate the full configuration against production security rules.

        ``runtime_tools`` (the live RuntimeToolRegistry) supplies the declared
        tiers for the git risk floor; without it the floor defers to the
        discovery schema gate and decision-time classification (see
        ``_check_approval_risk_floor``).
        """
        errors: list[str] = []
        warnings: list[str] = []

        # Not-false keys: explicit false is an error (absent is acceptable)
        for key in _REQUIRED_NOT_FALSE_KEYS:
            if config.get(key) is False:
                msg = f"{key}=false — strict mode is required in production"
                self._record(errors, warnings, msg)

        # Declared-tier risk floor for the named git write tools. Reads the
        # registry's declared metadata, never a configuration map (REQ-004).
        below_floor = _check_approval_risk_floor(
            runtime_tools,
            known_tools=known_tools,
            errors=errors,
        )
        if below_floor:
            tool_list = "; ".join(below_floor)
            msg = f"Declared risk below floor for git tools: {tool_list}"
            self._record(errors, warnings, msg)

        # allowed_root: an empty or absent root would disable the path jail
        allowed_root = config.get("allowed_root")
        if not (isinstance(allowed_root, str) and allowed_root.strip()):
            msg = (
                "allowed_root is empty or absent (the path jail would be disabled; "
                "set an absolute directory)"
            )
            self._record(errors, warnings, msg)

        # sqlite_vec_so: processes that open rag.sqlite or session.sqlite need the
        # sqlite-vec library path; an empty or absent value breaks those processes.
        sqlite_vec_so = config.get("sqlite_vec_so")
        if not (isinstance(sqlite_vec_so, str) and sqlite_vec_so.strip()):
            msg = (
                "sqlite_vec_so is empty or absent (required for processes that open "
                "rag.sqlite or session.sqlite; set the sqlite-vec library path in "
                "agent.toml)"
            )
            self._record(errors, warnings, msg)

        # Unknown top-level key rejection
        unknown_keys = ProductionConfigValidator._check_unknown_production_keys(config)
        if unknown_keys:
            unknown_list = ", ".join(repr(k) for k in unknown_keys)
            self._record(
                errors,
                warnings,
                f"Unknown config keys: {unknown_list}",
            )

        return ConfigValidationResult(errors=errors, warnings=warnings)

    def validate_against_registry(
        self,
        registry: Mapping[str, ComponentClassification],
        mcp_required: Mapping[str, bool],
    ) -> list[str]:
        """Return mandatoriness cross-check errors for the configured MCP servers.

        Compares each configured ``required`` value against the approved
        classification in ``registry``. A ``required`` server configured as
        ``required = false`` yields exactly one conflict error; a configured
        server absent from the registry yields exactly one unknown-classification
        error. Registry entries with no configured server are logged as warnings,
        not errors (a classified-but-not-configured server cannot be used). The
        returned strings are exactly the fatal set the startup pipeline turns into
        failures: ``{conflict, unknown-configured-server}``.

        ``registry`` is passed in by the caller (loaded once); this method never
        loads the registry itself, so it stays pure and testable with synthetic
        maps.
        """
        errors: list[str] = []
        configured = set(mcp_required)
        for server_key, config_required in mcp_required.items():
            try:
                check_required_agreement(registry, server_key, config_required)
            except ClassificationConflictError:
                approved = registry[server_key].classification
                errors.append(
                    f"component mandatoriness: '{server_key}' config "
                    f"required={config_required} conflicts with registry "
                    f"classification '{approved}' "
                    f"(registry: registry/component_mandatoriness.yaml)"
                )
            except UnknownComponentError:
                errors.append(
                    f"component mandatoriness: '{server_key}' is configured but "
                    f"absent from the mandatoriness registry "
                    f"(registry: registry/component_mandatoriness.yaml)"
                )
        for component_id in sorted(set(registry) - configured):
            logger.warning(
                "component mandatoriness: '%s' is classified in the registry but "
                "has no configured server (registry: "
                "registry/component_mandatoriness.yaml)",
                component_id,
            )
        return errors

    @staticmethod
    def _check_unknown_production_keys(config: Mapping[str, object]) -> list[str]:
        """Return top-level keys not found in any sub-config dataclass field."""
        valid_keys = _get_valid_production_keys()
        unknown_keys = sorted(k for k in config if k not in valid_keys)
        return unknown_keys

    @classmethod
    def _record(
        cls,
        errors: list[str],
        warnings: list[str],
        msg: str,
    ) -> None:
        """Format `msg` as an error and append it to the matching list."""
        e, w = cls._format_error_or_warning(msg)
        errors.extend(e)
        warnings.extend(w)

    @staticmethod
    def _format_error_or_warning(msg: str) -> tuple[list[str], list[str]]:
        return [msg], []


__all__ = ["ConfigValidationResult", "ProductionConfigValidator"]
