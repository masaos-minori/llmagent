#!/usr/bin/env python3
"""shared/tool_spec.py
Typed metadata for one tool call in the execution DAG.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ToolSpec:
    """Execution metadata for a single approved tool call.

    Fields:
        call_id:        LLM-assigned tool call id (from tool_calls[].id)
        name:           Tool function name
        args:           Parsed argument dict
        resource_scope: Resource path/branch string for conflict detection ("" if none)
        requires_serial: True when the tool must not run concurrently with others
        is_write:       True when the tool has write/delete side effects
    """

    call_id: str
    name: str
    args: dict[str, object] = field(default_factory=dict)
    resource_scope: str = ""
    requires_serial: bool = False
    is_write: bool = False
