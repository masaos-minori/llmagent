"""scripts/agent/services/config_outcome_classification.py — Outcome classification: standalone functions that compare the reload candidate against live state and return the pending records for MCP server changes, startup-only fields, and diagnostics."""

from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from agent.config_dataclasses import AgentConfig, MCPConfig
    from agent.context import AgentContext

from shared.mcp_config import _MCP_SERVER_KEYS

from agent.services.config_field_registry import CONFIG_FIELD_REGISTRY
from agent.services.config_pending_state import PendingMcpRecord

# The declared MCP configuration input. `McpServerConfig.key` and
# `McpServerConfig.fields` are excluded: `agent_config_payload` does not render
# them, so comparing them would report a change the user never made.
_MCP_SERVER_FIELDS: tuple[str, ...] = _MCP_SERVER_KEYS

PendingReason = Literal["startup_only"]


@dataclasses.dataclass(frozen=True)
class PendingChange:
    """One startup-only configuration change `/reload` records instead of applying live.

    The record names the field and the reason, never the configured value
    (REQ-011), so the display layer prints it without re-deriving why the change
    is pending (REQ-003).

    Attributes:
        field_path: Config key path the record names: the bare config key
            (``context_char_limit``).  An MCP definition change is recorded as a
            `PendingMcpRecord` instead, because the display names the server and
            each field that differs rather than one key.
        reason: Why the change cannot be applied live.
    """

    field_path: str
    reason: PendingReason = "startup_only"


def diff_mcp_definitions(
    live_mcp: MCPConfig,
    candidate_mcp: MCPConfig,
) -> list[PendingMcpRecord]:
    """Return one record per MCP server the candidate redefines.

    REQ-008: both sides are typed ``MCPConfig`` values: the live one startup built,
    the candidate one the shared candidate build parsed from the payload.  A server
    the candidate adds or removes names the server itself; a server in both names
    each declared MCP field that differs.  Nothing is applied to the running
    lifecycle: the record is the whole result, and a restart is what applies it
    (AC-4).
    """
    records: list[PendingMcpRecord] = []
    live_servers = live_mcp.mcp_servers
    for server_key, candidate_server in candidate_mcp.mcp_servers.items():
        live_server = live_servers.get(server_key)
        if live_server is None:
            records.append(
                PendingMcpRecord(
                    server_key=server_key,
                    change="added",
                    field_paths=(f"mcp_servers/{server_key}",),
                )
            )
            continue
        changed_fields = tuple(
            f"mcp_servers/{server_key}.{field_name}"
            for field_name in _MCP_SERVER_FIELDS
            if getattr(live_server, field_name) != getattr(candidate_server, field_name)
        )
        if changed_fields:
            records.append(
                PendingMcpRecord(
                    server_key=server_key,
                    change="changed",
                    field_paths=changed_fields,
                )
            )
    for server_key in live_servers:
        if server_key not in candidate_mcp.mcp_servers:
            records.append(
                PendingMcpRecord(
                    server_key=server_key,
                    change="removed",
                    field_paths=(f"mcp_servers/{server_key}",),
                )
            )
    return records


def classify_startup_only_fields(
    ctx: AgentContext,
    candidate: AgentConfig,
) -> list[PendingChange]:
    """Return pending records for startup-only fields the candidate changes.

    Runs on the candidate before any live mutation, so the comparison sees the
    running values rather than values the reload already wrote (REQ-003). Both
    sides are typed by the same parser, so a plain equality comparison is enough
    to tell a changed value from an unchanged one.
    """
    changed: list[PendingChange] = []
    for entry in CONFIG_FIELD_REGISTRY.values():
        if entry.hot_reloadable:
            continue
        value = getattr(getattr(candidate, entry.section_path), entry.name)
        current = getattr(getattr(ctx.cfg, entry.section_path), entry.name)
        if value != current:
            changed.append(PendingChange(entry.name, "startup_only"))
    return changed


def detect_diagnostics_live_fields(
    ctx: AgentContext,
    new_cfg: dict,
) -> list[str]:
    """Return names of diagnostics.* fields that differ between new_cfg and running cfg.

    These fields take effect immediately on every DiagnosticStore save()/fetch()
    call, independent of /reload — they are config-file-driven, not startup-only,
    so they are reported from the payload rather than from a pending record.
    """
    changed: list[str] = []
    diag_new = new_cfg.get("diagnostics")
    if diag_new is None:
        return changed
    diag_running = getattr(ctx.cfg, "diagnostics", None)
    if diag_running is None:
        return changed
    for key in ("encryption_key", "retention_days", "sensitive_fields"):
        v = diag_new.get(key)
        if v is None:
            continue
        current = getattr(diag_running, key, None)
        if v != current:
            changed.append(f"diagnostics.{key}")
    return changed
