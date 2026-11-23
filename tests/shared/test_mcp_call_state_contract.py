"""Tests for shared.mcp_call_state_contract (mcpdl004, REQ-004/REQ-005).

Pins the closed vocabularies, the totality of the ledger-state mapping, the
reconciler Protocol shape, and tolerant control-token resolution.
"""

from __future__ import annotations

from typing import get_protocol_members

import pytest
from agent.workflow.models import TOOL_CALL_STATES
from shared.mcp_call_state_contract import (
    AGENT_RECOVERY_STATES,
    CONTROL_ERROR_CODES,
    RECONCILE_OUTCOMES,
    RESULT_CLASSES,
    ReconcileEvidence,
    Reconciler,
    agent_state_for,
    resolve_control_token,
)


def test_closed_vocabularies_are_exact():
    assert RESULT_CLASSES == frozenset(
        {"complete", "secure_reference", "redacted_preview", "replay_unavailable"}
    )
    assert RECONCILE_OUTCOMES == frozenset(
        {"evidence_found", "no_evidence", "ambiguous", "unverifiable"}
    )
    assert CONTROL_ERROR_CODES == frozenset(
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
    assert AGENT_RECOVERY_STATES == frozenset(
        {
            "completed",
            "in_progress",
            "outcome_unknown",
            "reconciliation_required",
            "failed",
        }
    )


_EXPECTED_MAPPING = {
    ("pending", True): "in_progress",
    ("pending", False): "reconciliation_required",
    ("completed", False): "completed",
    ("completed", True): "completed",
    ("failed", False): "failed",
    ("failed", True): "failed",
    ("interrupted", False): "reconciliation_required",
    ("interrupted", True): "reconciliation_required",
}


@pytest.mark.parametrize(
    ("ledger_status", "lease_live", "expected"),
    [(s, live, exp) for (s, live), exp in sorted(_EXPECTED_MAPPING.items())],
)
def test_mapping_totality(ledger_status: str, lease_live: bool, expected: str):
    state = agent_state_for(ledger_status, lease_live)
    assert state == expected
    assert state in AGENT_RECOVERY_STATES
    # in_progress is a recovery outcome only, never a stored Agent state.
    if state != "in_progress":
        assert state in TOOL_CALL_STATES


def test_mapping_rejects_unknown_status():
    with pytest.raises(ValueError, match="unknown ledger status"):
        agent_state_for("unknown", False)


def test_reconcile_evidence_rejects_unknown_outcome():
    with pytest.raises(ValueError, match="not in RECONCILE_OUTCOMES"):
        ReconcileEvidence(outcome="found", digest="abc123")
    evidence = ReconcileEvidence(outcome="ambiguous", digest="deadbeef")
    assert evidence.external_ref is None
    assert evidence.digest == "deadbeef"


class _StubReconciler:
    """Structural implementation of the Reconciler Protocol (no registration)."""

    def reconcile(self, tool_name: str, call_key: str, snapshot):
        return ReconcileEvidence(outcome="no_evidence", digest="stub")


def test_reconciler_protocol_shape():
    assert get_protocol_members(Reconciler) == {"reconcile"}
    stub = _StubReconciler()
    evidence = stub.reconcile("git", "call-key-1", {})
    assert isinstance(evidence, ReconcileEvidence)
    assert evidence.outcome in RECONCILE_OUTCOMES


def test_resolve_control_token(monkeypatch):
    monkeypatch.setenv("MCP_SHELL_CONTROL_TOKEN", "dummy-token")
    assert resolve_control_token("${ENV:MCP_SHELL_CONTROL_TOKEN}") == "dummy-token"
    monkeypatch.delenv("MCP_UNSET_CONTROL_TOKEN", raising=False)
    assert resolve_control_token("${ENV:MCP_UNSET_CONTROL_TOKEN}") == ""
    assert resolve_control_token("") == ""
    assert resolve_control_token(None) == ""
