#!/usr/bin/env python3
"""scripts/agent/mcp_call_recovery.py — Agent recovery service for a lost tool-call response.

Reads the owning MCP server's control API for one stale tool-call row, maps the ledger
state through the shared mapping table (mcpdl004 REQ-005), and reports what it found.
It never executes a tool handler and never calls the tool transport: recovery of a
completed side effect must not repeat it. Writes stay with the caller, which owns the
guarded UPDATE in `agent.workflow.tool_call_state_ops`.
"""

from __future__ import annotations

import logging
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from shared.http_transport import ControlClient
from shared.mcp_call_state_contract import (
    AGENT_RECOVERY_STATES,
    CONTROL_ERROR_CODES,
    RESULT_CLASSES,
    agent_state_for,
)
from shared.mcp_config import McpServerConfig

if TYPE_CHECKING:
    from agent.workflow.tool_call_state_ops import ToolCallState

logger = logging.getLogger(__name__)

# The ledger states the shared mapping table covers. A payload naming anything else is
# not trusted, so it is discarded rather than mapped.
_LEDGER_STATES = frozenset({"pending", "completed", "failed", "interrupted"})

_DEFAULT_TIMEOUT_SEC = 3.0
_MAX_LOOKUPS = 8
# Fixed refusal labels for problems the control contract has no code for. The call id is
# logged as a prefix so a full opaque id never appears in a log line.
_UNKNOWN_SERVER = "unknown_server"
_UNCONFIGURED = "control_unconfigured"
_LOOKUP_BOUND = "lookup_bound"
_BAD_PAYLOAD = "bad_payload"


@dataclass(frozen=True)
class RecoveryResolution:
    """Validated answer for one stale call.

    Every field is a closed-vocabulary value or an opaque identifier. A reconcile answer
    carries no result facts, so `result_class` and `external_ref` are empty there.
    """

    agent_state: str
    result_class: str
    external_ref: str
    error_code: str


def _validated_resolution(payload: Mapping[str, Any]) -> RecoveryResolution | None:
    """Accept a control payload only when every field it uses is in the contract.

    Returns None for anything the contract does not define: an unknown key, an
    out-of-vocabulary value, a payload that disagrees with the shared mapping table, or
    a wrong field type. The payload itself is never logged.
    """
    state = payload.get("agent_state")
    ledger_status = payload.get("ledger_status")
    lease_live = payload.get("lease_live")
    code = payload.get("error_code")
    result_class = payload.get("result_class")
    external_ref = payload.get("external_ref")
    if not isinstance(state, str) or state not in AGENT_RECOVERY_STATES:
        return None
    if not isinstance(ledger_status, str) or ledger_status not in _LEDGER_STATES:
        return None
    if not isinstance(lease_live, bool):
        return None
    if (
        not isinstance(code, str)
        or code not in CONTROL_ERROR_CODES
        or code == "unknown_key"
    ):
        return None
    if result_class is not None and (
        not isinstance(result_class, str) or result_class not in RESULT_CLASSES
    ):
        return None
    if external_ref is not None and not isinstance(external_ref, str):
        return None
    try:
        mapped = agent_state_for(ledger_status, lease_live)
    except ValueError:
        # An unknown ledger state is out of the mapping table's domain: the shared
        # table raises rather than guessing, and a guessed state is not evidence.
        return None
    if mapped != state:
        return None
    return RecoveryResolution(
        agent_state=state,
        result_class=result_class or "",
        external_ref=external_ref or "",
        error_code=code,
    )


class McpCallRecoveryService:
    """One control read per stale row, through the typed control client.

    Clients are built lazily per server key from `McpServerConfig.url` and
    `control_auth_token`, so constructing this service performs no I/O. Any control
    problem — an unknown server, an empty control token, a failed request, a payload the
    contract does not define — resolves to None, which leaves the caller's row at its
    existing `outcome_unknown`. Only fixed labels and a call-id prefix are logged.
    """

    def __init__(
        self,
        server_configs: Mapping[str, McpServerConfig],
        server_for_tool: Callable[[str], str | None],
        client_factory: Callable[..., ControlClient] = ControlClient,
        timeout_sec: float = _DEFAULT_TIMEOUT_SEC,
        max_lookups: int = _MAX_LOOKUPS,
    ) -> None:
        """Initialize with the configured servers and the tool-to-server lookup.

        Args:
            server_configs: `McpServerConfig` map keyed by server key.
            server_for_tool: Returns the server key owning a tool name, or None. Callers
                pass a lazy lookup because a tool registry may not be populated yet here.
            client_factory: Control client constructor, `(base_url, token, timeout_sec)`.
            timeout_sec: Per-request control timeout.
            max_lookups: Maximum control requests this instance will make.

        Raises:
            ValueError: if `timeout_sec` or `max_lookups` is not positive.
        """
        if timeout_sec <= 0:
            raise ValueError("McpCallRecoveryService requires a positive timeout_sec")
        if max_lookups <= 0:
            raise ValueError("McpCallRecoveryService requires a positive max_lookups")
        self._configs = server_configs
        self._server_for_tool = server_for_tool
        self._client_factory = client_factory
        self._timeout_sec = timeout_sec
        self._max_lookups = max_lookups
        self._clients: dict[str, ControlClient] = {}
        self._lookups_used = 0

    def resolve_state(self, row: ToolCallState) -> str | None:
        """Mapped Agent state for one stale row, or None when nothing was established.

        `in_progress` is reported as the mapping table defines it; storing it is the
        caller's decision, since it is not a `tool_call_state` state.
        """
        resolution = self.resolve(row)
        return resolution.agent_state if resolution is not None else None

    def resolve(self, row: ToolCallState) -> RecoveryResolution | None:
        """Read the call state for one row from the server that owns its tool."""
        return self._read(row, request="state")

    def reconcile(self, row: ToolCallState) -> RecoveryResolution | None:
        """Ask the owning server to reconcile one row (operator-triggered path).

        The resolver path never calls this: reconciliation is a decision an operator or a
        registered reconciler makes, not something recovery does on its own.
        """
        return self._read(row, request="reconcile")

    def _read(self, row: ToolCallState, request: str) -> RecoveryResolution | None:
        """One control request for one row, with the lookup bound applied first."""
        server_key = self._server_for_tool(row.tool)
        if server_key is None:
            self._refuse(row, server_key, _UNKNOWN_SERVER)
            return None
        cfg = self._configs.get(server_key)
        if cfg is None or not cfg.control_auth_token:
            self._refuse(row, server_key, _UNCONFIGURED)
            return None
        if self._lookups_used >= self._max_lookups:
            self._refuse(row, server_key, _LOOKUP_BOUND)
            return None
        client = self._client_for(cfg)
        self._lookups_used += 1
        result = (
            client.get_call_state(row.idempotency_key)
            if request == "state"
            else client.request_reconcile(row.idempotency_key)
        )
        if not result.ok:
            self._refuse(row, server_key, result.error)
            return None
        payload = result.payload
        if payload is None:
            self._refuse(row, server_key, _BAD_PAYLOAD)
            return None
        resolution = _validated_resolution(payload)
        if resolution is None:
            self._refuse(row, server_key, _BAD_PAYLOAD)
            return None
        return resolution

    def _client_for(self, cfg: McpServerConfig) -> ControlClient:
        """Build and keep one control client per server key."""
        client = self._clients.get(cfg.key)
        if client is None:
            client = self._client_factory(
                cfg.url, cfg.control_auth_token, self._timeout_sec
            )
            self._clients[cfg.key] = client
        return client

    @staticmethod
    def _refuse(row: ToolCallState, server_key: str | None, label: str) -> None:
        """Log the fixed label, the server key, and a call-id prefix only."""
        logger.warning(
            "event=call_state_recovery label=%s server=%s call=%s",
            label,
            server_key or "",
            row.idempotency_key[:8],
        )


__all__ = [
    "McpCallRecoveryService",
    "RecoveryResolution",
]
