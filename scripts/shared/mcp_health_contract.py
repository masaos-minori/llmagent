#!/usr/bin/env python3
"""scripts/shared/mcp_health_contract.py — Shared MCP `/health` body contract.

One definition of the health body shape for both sides of the contract: the MCP
servers produce it and the Agent parses it. `shared` is the only layer both may
import (import-linter contract "mcp_servers must not import from agent"), so this
module stays a pure data/vocabulary leaf: no I/O, no logging, no imports from
`agent` or `mcp_servers`.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Literal

from shared.mcp_health import (
    HEALTH_REASON_HALF_OPEN_TRIAL_IN_PROGRESS,
    HEALTH_REASON_SERVER_UNAVAILABLE,
)
from shared.security.result_dto import REASON_CONFIG_MISSING

# Version 1 is the current contract. A body with no capability block parses as a
# legacy report, reported as version 0.
HEALTH_SCHEMA_VERSION = 1
LEGACY_HEALTH_SCHEMA_VERSION = 0

# Closed degraded reason-code vocabulary, documented in
# docs/22_mcp/mcp_06_10_health-reasons-and-error-kinds.md. `config_missing` is the
# canonical constant owned by shared.security.result_dto; the two availability-hint
# codes are the canonical constants owned by shared.mcp_health. Referencing the
# constants here makes a mistyped name fail at import, not at comparison.
HEALTH_REASON_CONFIG_MISSING = REASON_CONFIG_MISSING
HEALTH_DEGRADED_REASON_CODES: frozenset[str] = frozenset(
    {
        HEALTH_REASON_CONFIG_MISSING,
        HEALTH_REASON_SERVER_UNAVAILABLE,
        HEALTH_REASON_HALF_OPEN_TRIAL_IN_PROGRESS,
    }
)

# Closed capability-state vocabulary.
CapabilityStateName = Literal["ok", "degraded", "unavailable"]
CAPABILITY_STATE_OK: CapabilityStateName = "ok"
CAPABILITY_STATE_DEGRADED: CapabilityStateName = "degraded"
CAPABILITY_STATE_UNAVAILABLE: CapabilityStateName = "unavailable"

# The lookup keeps the Literal values resolvable from a parsed string without a cast.
CAPABILITY_STATE_BY_NAME: dict[str, CapabilityStateName] = {
    CAPABILITY_STATE_OK: CAPABILITY_STATE_OK,
    CAPABILITY_STATE_DEGRADED: CAPABILITY_STATE_DEGRADED,
    CAPABILITY_STATE_UNAVAILABLE: CAPABILITY_STATE_UNAVAILABLE,
}

CAPABILITY_STATES: frozenset[str] = frozenset(CAPABILITY_STATE_BY_NAME)


@dataclass(frozen=True)
class CapabilityState:
    """One capability's reported state plus its optional reason code."""

    state: CapabilityStateName
    reason_code: str | None = None


@dataclass(frozen=True)
class HealthReport:
    """Parsed `/health` body. `capabilities` is read-only (the parser returns a proxy)."""

    health_schema_version: int
    liveness: bool
    ready: bool
    degraded_reasons: tuple[str, ...]
    capabilities: Mapping[str, CapabilityState]

    @property
    def is_legacy(self) -> bool:
        """True when the body carries no capability block (D-6 legacy rule)."""
        return not self.capabilities


def parse_health_body(body: Mapping[str, object]) -> HealthReport:
    """Parse a raw `/health` body into a `HealthReport`.

    Strict typing with no truthy coercion: a present field of the wrong type, a
    reason code outside the closed vocabulary, or an unknown capability state raises
    `ValueError` naming the field. An absent field is not a wrong type: it parses as
    its default, which is what makes a legacy body (only `liveness`/`ready`) parseable.

    Args:
        body: The decoded JSON body of a `/health` response.

    Returns:
        The parsed report; `capabilities` is empty for a legacy body.

    Raises:
        ValueError: A field, a reason code, or a capability state is not as the contract defines it.
    """
    if not isinstance(body, Mapping):
        raise ValueError("body: expected an object")

    return HealthReport(
        health_schema_version=_int_field(
            body, "health_schema_version", LEGACY_HEALTH_SCHEMA_VERSION
        ),
        liveness=_bool_field(body, "liveness", False),
        ready=_bool_field(body, "ready", False),
        degraded_reasons=_reason_codes(body.get("degraded_reasons")),
        capabilities=_capability_states(body.get("capabilities")),
    )


def _bool_field(body: Mapping[str, object], name: str, default: bool) -> bool:
    """Read one boolean field; a JSON null is treated as absent."""
    value = body.get(name)
    if value is None:
        return default
    if not isinstance(value, bool):
        raise ValueError(f"{name}: expected a boolean")
    return value


def _int_field(body: Mapping[str, object], name: str, default: int) -> int:
    """Read one integer field; a boolean is not an integer here."""
    value = body.get(name)
    if value is None:
        return default
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{name}: expected an integer")
    return value


def _reason_codes(value: object) -> tuple[str, ...]:
    """Read the `degraded_reasons` list against the closed vocabulary."""
    if value is None:
        return ()
    if not isinstance(value, list):
        raise ValueError("degraded_reasons: expected a list of reason codes")
    codes: list[str] = []
    for entry in value:
        if not isinstance(entry, str):
            raise ValueError("degraded_reasons: expected a list of reason codes")
        if entry not in HEALTH_DEGRADED_REASON_CODES:
            raise ValueError(
                f"degraded_reasons: {entry!r} is outside the closed vocabulary"
            )
        codes.append(entry)
    return tuple(codes)


def _capability_states(value: object) -> Mapping[str, CapabilityState]:
    """Read the `capabilities` object: capability name to state, plus optional reason code."""
    if value is None:
        return MappingProxyType({})
    if not isinstance(value, Mapping):
        raise ValueError(
            "capabilities: expected an object of capability names to states"
        )
    states: dict[str, CapabilityState] = {}
    for name, entry in value.items():
        if not isinstance(name, str):
            raise ValueError("capabilities: capability name must be a string")
        if isinstance(entry, str):
            state_name = entry
            reason_code: str | None = None
        elif isinstance(entry, Mapping):
            raw_state = entry.get("state")
            raw_reason = entry.get("reason_code")
            if not isinstance(raw_state, str):
                raise ValueError(f"capabilities.{name}: state must be a string")
            if raw_reason is not None and not isinstance(raw_reason, str):
                raise ValueError(f"capabilities.{name}: reason_code must be a string")
            state_name = raw_state
            reason_code = raw_reason
            if (
                reason_code is not None
                and reason_code not in HEALTH_DEGRADED_REASON_CODES
            ):
                raise ValueError(
                    f"capabilities.{name}: reason_code {reason_code!r} is outside the closed vocabulary"
                )
        else:
            raise ValueError(f"capabilities.{name}: expected a capability state")
        state = CAPABILITY_STATE_BY_NAME.get(state_name)
        if state is None:
            raise ValueError(
                f"capabilities.{name}: {state_name!r} is not a known capability state"
            )
        states[name] = CapabilityState(state=state, reason_code=reason_code)
    return MappingProxyType(states)
