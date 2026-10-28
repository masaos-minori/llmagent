"""tests/agent/services/_discovery_gates.py

Shared test helper: build green PostureGate rows for McpToolDiscoveryService tests.
A green gate mirrors what agent.services.mcp_health's row-18 classifier produces for a
server that is reachable, posture-accepted, ready, and validated.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import replace

from agent.services.mcp_health import PostureGate, classify_server_failure
from shared.security.result_dto import REASON_OK


def green_gate(server_key: str) -> PostureGate:
    """Build one green gate with the failure class the row-18 classifier would attach."""
    gate = PostureGate(
        server_key=server_key,
        required=True,
        reachable=True,
        posture_accepted=True,
        ready=True,
        validated=True,
        reason_code=REASON_OK,
    )
    return replace(gate, failure_class=classify_server_failure(gate))


def gates_for(*server_keys: str) -> dict[str, PostureGate]:
    """Green gate per named server key."""
    return {key: green_gate(key) for key in server_keys}


def gates_from(servers: Mapping[str, object]) -> dict[str, PostureGate]:
    """Green gate per key of a servers mapping (the dicts _make_ctx consumes)."""
    return {key: green_gate(key) for key in servers}
