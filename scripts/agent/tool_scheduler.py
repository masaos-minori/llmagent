"""agent/tool_scheduler.py
Resource-scoped dependency scheduler for tool call batches.

Groups tool calls so that:
  - requires_serial=True tools run as a global serial barrier
  - tools with the same non-empty resource_scope and is_write=True are serialized
  - all other tools run in parallel within their group
"""

from __future__ import annotations

from typing import TypeVar

T = TypeVar("T")


def build_execution_groups(
    tool_calls: list[dict],
    tool_meta: dict[
        str, dict
    ],  # tool_name -> {resource_scope, requires_serial, is_write}
) -> list[list[dict]]:
    """Return an ordered list of groups; each group runs concurrently within itself,
    groups are executed sequentially.

    Rules:
    1. requires_serial=True tools form their own single-element group (acts as barrier)
    2. Tools with the same resource_scope and is_write=True share a serial group
    3. All other tools go into a parallel group at the end
    """
    serial_barrier: list[dict] = []
    resource_groups: dict[str, list[dict]] = {}  # scope -> [tool_calls]
    parallel: list[dict] = []

    for tc in tool_calls:
        name = tc["function"]["name"]
        meta = tool_meta.get(name, {})
        if meta.get("requires_serial"):
            serial_barrier.append(tc)
            continue
        scope = meta.get("resource_scope", "")
        is_write = meta.get("is_write", False)
        if scope and is_write:
            resource_groups.setdefault(scope, []).append(tc)
        else:
            parallel.append(tc)

    groups: list[list[dict]] = []
    for tc in serial_barrier:
        groups.append([tc])  # one-element group = serial barrier
    for scope_tcs in resource_groups.values():
        groups.append(scope_tcs)  # serialized within resource scope
    if parallel:
        groups.append(parallel)
    return groups
