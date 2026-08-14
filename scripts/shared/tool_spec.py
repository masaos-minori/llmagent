#!/usr/bin/env python3
"""scripts/shared/tool_spec.py

Typed metadata for one tool call in the execution DAG.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ToolSpec:
    """Execution metadata for a single approved tool call.

    Fields:
        call_id:        LLM-assigned tool call id (from tool_calls[].id)
        name:           Tool function name
        args:           Parsed argument dict
        resource_scopes: Tuple of kind-prefixed resource-scope strings for conflict
                        detection (empty tuple if none; see shared.resource_scope for
                        the string shape).
        requires_serial: True when the tool must not run concurrently with others
        is_write:       True when the tool has write/delete side effects
    """

    call_id: str
    name: str
    args: dict[str, Any] = field(default_factory=dict)
    resource_scopes: tuple[str, ...] = ()
    requires_serial: bool = False
    is_write: bool = False
