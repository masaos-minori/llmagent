"""agent/tool_scheduler.py

Resource-scoped dependency scheduler for tool call batches.

Groups tool calls so that:
  - requires_serial=True tools run as a global serial barrier
  - tools with the same non-empty resource_scope and is_write=True are serialized
  - write tools without resource_scope go into a write-first group
  - all remaining tools run in parallel in the final group

NOTE — two distinct, intentionally-separate serialization mechanisms exist in
this codebase:
  1. ToolSpec.requires_serial (this module): a per-tool flag consumed by
     build_execution_groups() to force a single tool into its own serial
     barrier group within a batch's group scheduling.
  2. is_side_effect() (shared/tool_executor_helpers.py): a batch-level
     downgrade. When any tool call in a batch has a side effect,
     execute_all_tool_calls() falls back to serial execution for the whole
     batch instead of running calls concurrently.
They are not unified today, and whether they should be is an open follow-up
design question — not resolved as part of this change. Do not conflate them
when reasoning about tool-call concurrency.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from shared.tool_spec import ToolSpec

logger = logging.getLogger(__name__)


@dataclass
class _SerializationEvent:
    """Record of a serialization decision made during group building."""

    trigger_tool: str
    reason: str
    tools_count: int
    resource_scope: str = ""
    is_write: bool = False
    requires_serial: bool = False
    scheduling_decision: str = ""


@dataclass
class ScheduledBatch:
    """One concurrent execution unit: groups run concurrently; within each group,

    execution is sequential when serialize_flags[i] is True, gathered when False."""

    groups: list[list[dict]]
    serialize_flags: list[bool]  # parallel to groups


@dataclass
class _GroupMetadata:
    """Metadata about execution group construction including serialization events."""

    total_tools: int
    total_groups: int
    serialization_events: list[_SerializationEvent] = field(default_factory=list)
    # Each element is a batch of groups that can run concurrently.
    # Groups within a batch run concurrently; batches run sequentially.
    concurrent_groups: list[ScheduledBatch] = field(default_factory=list)


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
    # All resource-scope groups + parallel group share one concurrent batch;
    # serialize_flags=True for same-scope write groups, False for reads.
    cgr: list[ScheduledBatch] = []
    for tc in serial_barrier:
        cgr.append(ScheduledBatch(groups=[[tc]], serialize_flags=[False]))
    if write_first:
        cgr.append(ScheduledBatch(groups=[write_first], serialize_flags=[False]))

    has_concurrent = bool(resource_groups) or bool(parallel)
    if has_concurrent:
        batch_groups: list[list[dict]] = []
        batch_flags: list[bool] = []
        for scope_tcs in resource_groups.values():
            batch_groups.append(scope_tcs)
            batch_flags.append(True)  # same-scope writes run sequentially within group
        if parallel:
            batch_groups.append(parallel)
            batch_flags.append(False)  # reads gathered concurrently
        cgr.append(ScheduledBatch(groups=batch_groups, serialize_flags=batch_flags))

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
                requires_serial=True,
                is_write=True,
                scheduling_decision="serial_barrier",
            )
        )

    for scope, scope_tcs in resource_groups.items():
        trigger = scope_tcs[0]["function"]["name"]
        metadata.serialization_events.append(
            _SerializationEvent(
                trigger_tool=trigger,
                reason="resource_scope_conflict",
                tools_count=len(scope_tcs),
                resource_scope=scope,
                is_write=True,
                scheduling_decision="resource_scope",
            )
        )

    if write_first:
        trigger = write_first[0]["function"]["name"]
        metadata.serialization_events.append(
            _SerializationEvent(
                trigger_tool=trigger,
                reason="is_write_overlap",
                tools_count=len(write_first),
                is_write=True,
                scheduling_decision="write_first",
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
