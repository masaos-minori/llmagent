#!/usr/bin/env python3
"""scripts/shared/config_undo.py — Undo vocabulary for reversible live-config changes.

A live configuration change is reversible when the value it replaced is captured
before the mutation.  `ServiceSnapshot` is what a live service returns from its
`snapshot*()` call; `UndoToken` is what a mutation returns so the reload
transaction can replay it in reverse order.

The module lives in the leaf layer because `.importlinter` contract
`shared-is-leaf` forbids `shared` importing `agent`, and both
`shared/llm_hot_config.py` and `shared/runtime_tool_registry.py` return these
types (REQ-006).

No configuration value appears in either record's reporting text: a token names
the service and the field paths it reverses (REQ-011).
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ServiceSnapshot:
    """Config-derived state captured from one live service before a mutation.

    Attributes:
        service: Service identifier the snapshot belongs to, used by the rollback
            report when a restore fails.
        values: Captured attribute values, keyed by the attribute name the owning
            service's restore method reads.  The values are the live objects, not
            copies, so a restore reattaches what was captured.
    """

    service: str
    values: dict[str, Any]


@dataclass(frozen=True)
class UndoToken:
    """One reversible step, captured at the point of mutation.

    Attributes:
        service: Live service or section the token reverses.
        field_paths: Config field paths the step changed, which is what the
            rollback report prints.
        restore: Callable that puts the service or section back to its captured
            state.  It must be safe to call once and must not raise on a value
            the service already accepted.
    """

    service: str
    field_paths: tuple[str, ...]
    restore: Callable[[], None]


__all__ = ["ServiceSnapshot", "UndoToken"]
