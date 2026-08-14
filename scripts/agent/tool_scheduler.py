"""scripts/agent/tool_scheduler.py

Resource-scoped dependency scheduler for tool call batches.

Groups tool calls so that:
  - requires_serial=True tools run as a global serial barrier
  - write-relevant calls whose resource_scopes overlap (conflict-graph connected
    components; see shared.resource_scope._scopes_conflict()) are serialized together
  - write tools without resource_scopes go into a write-first group
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

from shared.resource_scope import _scopes_conflict
from shared.tool_spec import ToolSpec

logger = logging.getLogger(__name__)


class MissingToolSpecError(Exception):
    """Raised when a tool call's call_id has no entry in the tool_meta map

    passed to build_execution_groups(). A missing spec is a scheduling
    failure, not a condition that should silently default to an unscoped,
    non-write ToolSpec.
    """


@dataclass
class _SerializationEvent:
    """Record of a serialization decision made during group building."""

    trigger_tool: str
    reason: str
    tools_count: int
    resource_scopes: tuple[str, ...] = ()
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


def _connected_component(start_id: str, edges: dict[str, set[str]]) -> set[str]:
    """Return the set of call ids reachable from start_id via edges (BFS)."""
    visited = {start_id}
    queue = [start_id]
    while queue:
        current = queue.pop()
        for neighbor in edges[current]:
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)
    return visited


def _build_resource_groups(
    candidates: list[dict],
    specs: dict[str, ToolSpec],
) -> tuple[list[list[dict]], list[dict]]:
    """Build conflict-graph connected components over write-relevant *candidates*.

    Returns (resource_groups, isolated_reads) where resource_groups is an ordered
    list of call-lists (each a connected component containing at least one
    is_write=True call), and isolated_reads is the list of single-node,
    non-write components (folded into the caller's parallel bucket instead of
    becoming a serialized group of one).
    """
    edges: dict[str, set[str]] = {tc["id"]: set() for tc in candidates}
    for i, tc_a in enumerate(candidates):
        call_id_a = tc_a["id"]
        meta_a = specs[call_id_a]
        for tc_b in candidates[i + 1 :]:
            call_id_b = tc_b["id"]
            meta_b = specs[call_id_b]
            if not (meta_a.is_write or meta_b.is_write):
                continue
            if any(
                _scopes_conflict(scope_a, scope_b)
                for scope_a in meta_a.resource_scopes
                for scope_b in meta_b.resource_scopes
            ):
                edges[call_id_a].add(call_id_b)
                edges[call_id_b].add(call_id_a)

    resource_groups: list[list[dict]] = []
    isolated_reads: list[dict] = []
    visited: set[str] = set()
    for tc in candidates:
        call_id = tc["id"]
        if call_id in visited:
            continue
        component_ids = _connected_component(call_id, edges)
        visited |= component_ids
        # Preserve `candidates`' original ordering within the component rather than
        # BFS visitation order, so group contents stay deterministic and match the
        # order calls appeared in the batch.
        component = [c for c in candidates if c["id"] in component_ids]
        if len(component) == 1 and not specs[call_id].is_write:
            isolated_reads.append(component[0])
        else:
            resource_groups.append(component)
    return resource_groups, isolated_reads


def build_execution_groups(
    tool_calls: list[dict],
    tool_meta: dict[str, ToolSpec],  # call_id -> ToolSpec
) -> tuple[list[list[dict]], _GroupMetadata]:
    """Return (groups, metadata) where groups is an ordered list of execution groups

    and metadata contains serialization event information.

    Rules:
    1. requires_serial=True tools form their own single-element group (acts as barrier)
    2. Write-relevant tools whose resource_scopes overlap (conflict-graph connected
       components) share a serial group
    3. Write tools without resource_scopes go into a write-first group
    4. All remaining (read) tools go into a parallel group at the end

    Raises:
        MissingToolSpecError: if a tool call's call_id has no entry in tool_meta.
    """
    serial_barrier: list[dict] = []
    write_first: list[dict] = []
    parallel: list[dict] = []
    candidates: list[dict] = []  # calls with at least one non-empty resource_scope
    specs: dict[str, ToolSpec] = {}

    for tc in tool_calls:
        call_id = tc["id"]
        meta = tool_meta.get(call_id)
        if meta is None:
            raise MissingToolSpecError(
                f"No ToolSpec for call_id={call_id!r} (tool={tc['function']['name']!r})"
            )
        specs[call_id] = meta
        if meta.requires_serial:
            serial_barrier.append(tc)
            continue
        if meta.resource_scopes:
            candidates.append(tc)
        elif meta.is_write:
            write_first.append(tc)
        else:
            parallel.append(tc)

    resource_groups, isolated_reads = _build_resource_groups(candidates, specs)
    parallel.extend(isolated_reads)

    groups: list[list[dict]] = []
    for tc in serial_barrier:
        groups.append([tc])  # one-element group = serial barrier
    for group in resource_groups:
        groups.append(group)  # serialized within the connected component
    if write_first:
        groups.append(write_first)  # write-first group
    if parallel:
        groups.append(parallel)

    # Build concurrent_groups: which batches of groups can run in parallel.
    # serial_barrier tools each get their own sequential batch.
    # write_first gets its own sequential batch (no scope — conservative).
    # All resource-scope groups + parallel group share one concurrent batch;
    # serialize_flags=True for resource-scope conflict groups, False for reads.
    cgr: list[ScheduledBatch] = []
    for tc in serial_barrier:
        cgr.append(ScheduledBatch(groups=[[tc]], serialize_flags=[False]))
    if write_first:
        cgr.append(ScheduledBatch(groups=[write_first], serialize_flags=[False]))

    has_concurrent = bool(resource_groups) or bool(parallel)
    if has_concurrent:
        batch_groups: list[list[dict]] = []
        batch_flags: list[bool] = []
        for group in resource_groups:
            batch_groups.append(group)
            batch_flags.append(True)  # conflicting writes run sequentially within group
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

    for group in resource_groups:
        trigger = group[0]["function"]["name"]
        union_scopes = tuple(
            dict.fromkeys(
                scope for tc in group for scope in specs[tc["id"]].resource_scopes
            )
        )
        is_write_in_group = any(specs[tc["id"]].is_write for tc in group)
        metadata.serialization_events.append(
            _SerializationEvent(
                trigger_tool=trigger,
                reason="resource_scope_conflict",
                tools_count=len(group),
                resource_scopes=union_scopes,
                is_write=is_write_in_group,
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
