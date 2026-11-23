"""scripts/shared/mcp_call_state_contract.py — Call-state contract vocabularies.

The one shared, closed-vocabulary module read by the dedup ledger, the MCP
control API, and the Agent recovery service (issue mcpdl004). Consumers are
wired by the consumer rows; this module performs no I/O and holds no
registration state. Importing only the standard library and shared.config_utils
keeps the `.importlinter` contract `shared-is-leaf`.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Protocol

from shared.config_utils import resolve_env_ref

RESULT_CLASSES = frozenset(
    {
        "complete",
        "secure_reference",
        "redacted_preview",
        "replay_unavailable",
    }
)
RECONCILE_OUTCOMES = frozenset(
    {
        "evidence_found",
        "no_evidence",
        "ambiguous",
        "unverifiable",
    }
)
CONTROL_ERROR_CODES = frozenset(
    {
        "none",
        "unknown_key",
        "lease_live",
        "attempts_exhausted",
        "not_reconcilable",
        "reconciler_failed",
        "handler_failed",
        "store_unavailable",
    }
)
AGENT_RECOVERY_STATES = frozenset(
    {
        "completed",
        "in_progress",
        "outcome_unknown",
        "reconciliation_required",
        "failed",
    }
)


def agent_state_for(ledger_status: str, lease_live: bool) -> str:
    """Single authoritative ledger-state -> Agent-state mapping (REQ-005).

    `in_progress` is a recovery outcome only: it is not a member of
    `agent.workflow.models.TOOL_CALL_STATES`, so callers must not store it.
    Raises ValueError on an unknown ledger status (totality is tested).
    """
    if ledger_status == "pending":
        if lease_live:
            return "in_progress"
        return "reconciliation_required"
    if ledger_status == "completed":
        return "completed"
    if ledger_status == "failed":
        return "failed"
    if ledger_status == "interrupted":
        return "reconciliation_required"
    raise ValueError(f"agent_state_for: unknown ledger status {ledger_status!r}")


@dataclass(frozen=True)
class ReconcileEvidence:
    """Non-sensitive reconciliation evidence recorded by a Reconciler.

    `digest` must be a non-sensitive digest (hex hash or fixed label); no raw
    arguments, credentials, signed URLs, raw exceptions, or internal paths.
    """

    outcome: str
    digest: str
    external_ref: str | None = None

    def __post_init__(self) -> None:
        if self.outcome not in RECONCILE_OUTCOMES:
            raise ValueError(
                f"ReconcileEvidence: outcome {self.outcome!r} is not in "
                "RECONCILE_OUTCOMES"
            )


class Reconciler(Protocol):
    """Per-tool reconciler contract (REQ-004).

    No default implementation is registered here; per-tool implementations are
    registered at the control-API registry seam.
    """

    def reconcile(
        self, tool_name: str, call_key: str, snapshot: Mapping[str, str]
    ) -> ReconcileEvidence:
        """Return evidence for a call whose response was lost; never re-execute."""
        ...


def resolve_control_token(raw: str) -> str:
    """Tolerant `${ENV:...}` control-token resolution (REQ-002).

    Returns "" unless `raw` is a non-empty string; maps the ValueError raised by
    `resolve_env_ref` for an unset variable to "" (control closed). It never
    logs the value; callers log the server name only.
    """
    if not isinstance(raw, str) or not raw:
        return ""
    try:
        return resolve_env_ref(raw)
    except ValueError:
        return ""


__all__ = [
    "AGENT_RECOVERY_STATES",
    "CONTROL_ERROR_CODES",
    "RECONCILE_OUTCOMES",
    "RESULT_CLASSES",
    "ReconcileEvidence",
    "Reconciler",
    "agent_state_for",
    "resolve_control_token",
]
