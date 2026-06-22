"""agent/tool_scheduler.py
Resource-scoped dependency scheduler for tool call batches.

Groups tool calls so that:
  - requires_serial=True tools run as a global serial barrier
  - tools with the same non-empty resource_scope and is_write=True are serialized
  - write tools without resource_scope go into a write-first group
  - all remaining tools run in parallel in the final group
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from shared.tool_spec import ToolSpec

logger = logging.getLogger(__name__)


@dataclass
class _SerializationEvent:
    trigger_tool: str
    reason: str
    tools_count: int


@dataclass
class _GroupMetadata:
    total_tools: int
    total_groups: int
    serialization_events: list[_SerializationEvent] = field(default_factory=list)
    # Each element is a batch of groups that can run concurrently.
    # Groups within a batch are safe to gather(); batches run sequentially.
    concurrent_groups: list[list[list[dict]]] = field(default_factory=list)


def build_execution_groups(
    tool_calls: list[dict],
    tool_meta: dict[str, ToolSpec],  # tool_name -> ToolSpec
) -> tuple[list[list[dict]], _GroupMetadata]:
    """Return (groups, metadata) where groups is an ordered list of execution groups
    and metadata contains serialization event information.

    Rules:
    1. requires_serial=True tools form their own single-element group (acts as barrier)
    2. Tools with the same resource_scope and is_write=True share a serial group
    3. Write tools without resource_scope go into a write-first group
    4. All remaining (read) tools go into a parallel group at the end
    """
    serial_barrier: list[dict] = []
    resource_groups: dict[str, list[dict]] = {}  # scope -> [tool_calls]
    write_first: list[dict] = []
    parallel: list[dict] = []

    for tc in tool_calls:
        name = tc["function"]["name"]
        meta = tool_meta.get(name)
        if meta is not None and meta.requires_serial:
            serial_barrier.append(tc)
            continue
        scope = meta.resource_scope if meta is not None else ""
        is_write = meta.is_write if meta is not None else False
        if scope and is_write:
            resource_groups.setdefault(scope, []).append(tc)
        elif is_write:
            write_first.append(tc)
        else:
            parallel.append(tc)

    groups: list[list[dict]] = []
    for tc in serial_barrier:
        groups.append([tc])  # one-element group = serial barrier
    for scope_tcs in resource_groups.values():
        groups.append(scope_tcs)  # serialized within resource scope
    if write_first:
        groups.append(write_first)  # write-first group
    if parallel:
        groups.append(parallel)

    # Build concurrent_groups: which batches of groups can run in parallel.
    # serial_barrier tools each get their own sequential batch.
    # write_first gets its own sequential batch (no scope — conservative).
    # All resource-scope groups + parallel group share one concurrent batch.
    concurrent_batch: list[list[dict]] = []
    for scope_tcs in resource_groups.values():
        concurrent_batch.append(scope_tcs)
    if parallel:
        concurrent_batch.append(parallel)

    cgr: list[list[list[dict]]] = []
    for tc in serial_barrier:
        cgr.append([[tc]])
    if write_first:
        cgr.append([write_first])
    if concurrent_batch:
        cgr.append(concurrent_batch)

    metadata = _GroupMetadata(
        total_tools=len(tool_calls),
        total_groups=len(groups),
        concurrent_groups=cgr,
    )

    for tc in serial_barrier:
        name = tc["function"]["name"]
        metadata.serialization_events.append(
            _SerializationEvent(
                trigger_tool=name,
                reason="requires_serial",
                tools_count=1,
            )
        )

    for scope, scope_tcs in resource_groups.items():
        trigger = scope_tcs[0]["function"]["name"]
        metadata.serialization_events.append(
            _SerializationEvent(
                trigger_tool=trigger,
                reason="resource_scope_conflict",
                tools_count=len(scope_tcs),
            )
        )

    if write_first:
        trigger = write_first[0]["function"]["name"]
        metadata.serialization_events.append(
            _SerializationEvent(
                trigger_tool=trigger,
                reason="is_write_overlap",
                tools_count=len(write_first),
            )
        )

    for evt in metadata.serialization_events:
        logger.info(
            "ROUND_SERIALIZATION: triggered by %s (%s) — %d tools serialized in this round",
            evt.trigger_tool,
            evt.reason,
            evt.tools_count,
        )

    return groups, metadata
