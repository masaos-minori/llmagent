"""scripts/agent/services/config_pending_state.py — Pending configuration state: the restart-pending MCP and startup-only records, and the guard that refuses a reload after a degraded stage.

The reload path cannot apply an MCP server definition or a startup-only field to
the running process, so it records them here and the display commands read them on
every call (REQ-003, REQ-008, REQ-009).  The container owns one instance for the
lifetime of the process (`AppServices.pending_config`), which is what makes a
record survive from one CLI command to the next; a restart builds a new process and
a new instance, so the pending view starts empty (AC-4, AC-5).

The state stores the record of a change, never a configuration value: a record is a
field path and a change kind, so a token such as ``auth_token`` cannot reach the
display layer (REQ-011).
"""

from __future__ import annotations

import dataclasses
from collections.abc import Sequence
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from agent.context import AgentContext, AppServices
    from agent.services.config_field_registry import ConfigFieldRegistry

McpChangeKind = Literal["added", "changed", "removed"]


@dataclasses.dataclass(frozen=True)
class PendingMcpRecord:
    """One MCP server definition change `/reload` recorded instead of applying.

    Attributes:
        server_key: MCP server key the record names.
        change: Definition change kind.
        field_paths: Config paths under `mcp_servers/<server_key>` the record
            names, in the order they were first recorded.  An added or removed
            server names the server itself; a changed server names each field
            that differs.  No value is stored (REQ-011).
    """

    server_key: str
    change: McpChangeKind
    field_paths: tuple[str, ...]


class PendingConfigState:
    """Restart-pending configuration records and the degraded-reload guard.

    One instance lives on `AppServices` for the lifetime of the process, so the
    pending view is shared by every command rather than rebuilt per command
    (REQ-009).  Nothing here is persisted: a restart clears every record.
    """

    def __init__(self) -> None:
        """Start with no pending record and no degraded service."""
        self._mcp_records: dict[str, PendingMcpRecord] = {}
        self._startup_only: dict[str, None] = {}
        self._degraded: dict[str, None] = {}

    # ── MCP definition records ────────────────────────────────────────────────

    def set_mcp_records(self, records: Sequence[PendingMcpRecord]) -> None:
        """Store the MCP records one reload classified, replacing the previous set.

        Every reload classifies the complete candidate against the live config, so the
        records it returns are the complete pending MCP view, not one payload's
        fragment.  Replacing the set is what keeps the view honest: a definition the
        config file no longer redefines stops being pending, and one it still redefines
        is recorded again by the next reload (REQ-008, AC-4).
        """
        self._mcp_records = {record.server_key: record for record in records}

    def pending_mcp_records(self) -> tuple[PendingMcpRecord, ...]:
        """Return every pending MCP record, oldest server first (REQ-008)."""
        return tuple(self._mcp_records.values())

    # ── Startup-only field records ────────────────────────────────────────────

    def set_startup_only(self, fields: Sequence[ConfigFieldRegistry | str]) -> None:
        """Store the startup-only fields one reload found changed, replacing the set.

        Accepts the `ConfigFieldRegistry` entries `startup_only_for` returned, or their
        names, so the caller does not have to map them first.  The classification runs
        over the whole candidate every reload, so the set it produces is the complete
        pending view: a field the payload no longer changes stops being pending
        (REQ-003, AC-2).
        """
        self._startup_only = {}
        for field in fields:
            name = field if isinstance(field, str) else field.name
            self._startup_only.setdefault(name, None)

    def pending_startup_only(self) -> tuple[str, ...]:
        """Return every pending startup-only field path, first seen first (REQ-003)."""
        return tuple(self._startup_only)

    # ── Degraded-reload guard ─────────────────────────────────────────────────

    def record_degraded(self, services: tuple[str, ...] | list[str]) -> None:
        """Record that a reload left these services inconsistent (REQ-012)."""
        for service in services:
            self._degraded.setdefault(service, None)

    def degraded_services(self) -> tuple[str, ...]:
        """Return the services a previous reload left inconsistent."""
        return tuple(self._degraded)

    def allow_reload(self) -> bool:
        """Return whether a further reload may commit.

        False once any reload recorded a `degraded` stage: a commit on top of an
        inconsistent service would apply changes to a state its own rollback could
        not restore, so the reload is refused until a restart (REQ-012, AC-5).
        """
        return not self._degraded


def pending_state_for(ctx: AgentContext) -> PendingConfigState | None:
    """Return the pending state the context's container carries, or None.

    `factory.py` puts one `PendingConfigState` on `AppServices`, so every command in
    the process reads and writes the same records (REQ-009).  None means the caller
    has no cross-command view: the reload then guards only its own instance, and a
    display command prints no pending section.
    """
    services: AppServices | None = ctx.services
    if services is None:
        return None
    pending = services.pending_config
    return pending if isinstance(pending, PendingConfigState) else None
