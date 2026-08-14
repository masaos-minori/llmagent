"""scripts/agent/tool_scheduler.py

Resource-scoped dependency scheduler for tool call batches.

Single-engine, phase-based, call-id-keyed execution planner. build_execution_groups()
walks the batch of tool calls in original order and builds a sequence of phases:

  - A requires_serial=True call is an in-place barrier: it closes any phase
    accumulated so far, becomes its own single-call sequential phase (at its
    original position — never hoisted to the front of the batch), and a fresh
    phase starts for the calls that follow it.
  - Within every other phase, calls are grouped by resource_scopes overlap: a
    conflict-graph connected component (edge when either side is_write=True and
    their resource_scopes overlap; see shared.resource_scope._scopes_conflict())
    becomes its own sequential group, while every call left un-conflicted in that
    phase is pooled into one concurrent group.
  - A write call whose resource_scopes is empty is treated as occupying the
    synthetic "global:write" scope, so scope-less writes conflict with each other
    (and with anything else touching "global:write") instead of racing.
  - force_serial=True bypasses phase-building entirely: every call becomes its
    own single-call sequential phase, in original order.

build_execution_groups() returns a single ExecutionPlan (an ordered sequence of
ScheduledBatches, each holding ScheduledGroups, plus the SerializationEvents the
plan implies) instead of a metadata/return-value pair that could drift apart.

NOTE — is_side_effect() (shared/tool_executor_helpers.py) is a separate,
unrelated mechanism: it now backs only the TTL-cache-bypass check in
shared/tool_executor.py. It no longer drives any batch-level parallel/serial
decision in execute_all_tool_calls() — that decision now flows entirely
through this module's phase-building (requires_serial barriers and
resource-scope conflicts, described above) plus the force_serial input. Do not
conflate is_side_effect() with ToolSpec.requires_serial when reasoning about
tool-call concurrency.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from shared.resource_scope import _scopes_conflict
from shared.tool_spec import ToolSpec

logger = logging.getLogger(__name__)

# Synthetic scope assigned (defensively, within this module) to a write call whose
# resource_scopes is empty, so scope-less writes conflict with each other instead of
# racing. shared.resource_scope.resolve_resource_scopes() already applies this same
# fallback when building a ToolSpec from a live RuntimeTool; this constant exists here
# only so a directly-constructed ToolSpec (e.g. in tests, or any future caller that
# builds ToolSpec without going through the registry) behaves the same way.
_GLOBAL_WRITE_SCOPE = "global:write"


class MissingToolSpecError(Exception):
    """Raised when a tool call's call_id has no entry in the call_specs map

    passed to build_execution_groups(). A missing spec is a scheduling
    failure, not a condition that should silently default to an unscoped,
    non-write ToolSpec.
    """


@dataclass(frozen=True)
class SerializationEvent:
    """Record of one serialization decision made while building an ExecutionPlan."""

    trigger_tool: str
    reason: str
    tools_count: int
    resource_scopes: tuple[str, ...] = ()
    is_write: bool = False
    requires_serial: bool = False
    scheduling_decision: str = ""


@dataclass(frozen=True)
class ScheduledGroup:
    """One group of calls within a batch.

    Executed sequentially (in tuple order) when `sequential` is True, gathered
    concurrently otherwise. `reason` names why the group exists (empty for the
    plain concurrent pool).
    """

    calls: tuple[ToolSpec, ...]
    sequential: bool
    reason: str = ""


@dataclass(frozen=True)
class ScheduledBatch:
    """One or more ScheduledGroups that run concurrently with each other."""

    groups: tuple[ScheduledGroup, ...]


@dataclass(frozen=True)
class ExecutionPlan:
    """The full scheduling result for one batch of tool calls.

    `batches` run one after another, in order; the groups within a single
    batch run concurrently with each other.
    """

    batches: tuple[ScheduledBatch, ...]
    serialization_events: tuple[SerializationEvent, ...]


def _effective_scopes(spec: ToolSpec) -> tuple[str, ...]:
    """Return spec.resource_scopes, substituting the synthetic global:write scope

    for a write call whose resource_scopes is empty (see _GLOBAL_WRITE_SCOPE)."""
    if spec.is_write and not spec.resource_scopes:
        return (_GLOBAL_WRITE_SCOPE,)
    return spec.resource_scopes


def _classify_conflict_reason(
    members: list[ToolSpec], effective: dict[str, tuple[str, ...]]
) -> str:
    """Classify why *members* (a conflict-graph connected component of size > 1)

    must serialize: the global:write fallback, a read/write overlap, or a
    write/write overlap on an explicit shared scope."""
    union_scopes = {scope for m in members for scope in effective[m.call_id]}
    if union_scopes == {_GLOBAL_WRITE_SCOPE}:
        return "global_write_scope"
    if any(not m.is_write for m in members):
        return "resource_read_write_conflict"
    return "resource_write_write_conflict"


class _UnionFind:
    """Minimal union-find over call_id strings (no path compression — batches

    are small enough that this stays O(n) in practice)."""

    def __init__(self, call_ids: list[str]) -> None:
        self._parent = {call_id: call_id for call_id in call_ids}

    def find(self, call_id: str) -> str:
        while self._parent[call_id] != call_id:
            call_id = self._parent[call_id]
        return call_id

    def union(self, a: str, b: str) -> None:
        root_a, root_b = self.find(a), self.find(b)
        if root_a != root_b:
            self._parent[root_a] = root_b


def _build_phase_batch(
    specs: list[ToolSpec],
) -> tuple[ScheduledBatch, list[SerializationEvent]]:
    """Partition one phase's calls into sequential conflict groups plus one

    concurrent group pooling everything left un-conflicted. Read/read pairs
    never conflict; an edge exists only when either side is_write=True and
    their (effective) resource_scopes overlap.
    """
    effective = {spec.call_id: _effective_scopes(spec) for spec in specs}
    uf = _UnionFind([spec.call_id for spec in specs])

    for i, spec_a in enumerate(specs):
        for spec_b in specs[i + 1 :]:
            if not (spec_a.is_write or spec_b.is_write):
                continue
            if any(
                _scopes_conflict(scope_a, scope_b)
                for scope_a in effective[spec_a.call_id]
                for scope_b in effective[spec_b.call_id]
            ):
                uf.union(spec_a.call_id, spec_b.call_id)

    components: dict[str, list[ToolSpec]] = {}
    for spec in specs:
        # Iterating `specs` in original order means each component's list is
        # already in original relative order, with no extra sort needed.
        components.setdefault(uf.find(spec.call_id), []).append(spec)

    order = {spec.call_id: i for i, spec in enumerate(specs)}
    sequential_groups: list[ScheduledGroup] = []
    events: list[SerializationEvent] = []
    concurrent_members: list[ToolSpec] = []
    for members in components.values():
        if len(members) == 1:
            concurrent_members.append(members[0])
            continue
        reason = _classify_conflict_reason(members, effective)
        sequential_groups.append(
            ScheduledGroup(calls=tuple(members), sequential=True, reason=reason)
        )
        union_scopes = tuple(
            dict.fromkeys(scope for m in members for scope in effective[m.call_id])
        )
        events.append(
            SerializationEvent(
                trigger_tool=members[0].name,
                reason=reason,
                tools_count=len(members),
                resource_scopes=union_scopes,
                is_write=any(m.is_write for m in members),
                requires_serial=False,
                scheduling_decision="resource_scope",
            )
        )

    sequential_groups.sort(key=lambda g: order[g.calls[0].call_id])
    concurrent_members.sort(key=lambda spec: order[spec.call_id])

    groups: list[ScheduledGroup] = list(sequential_groups)
    if concurrent_members:
        groups.append(ScheduledGroup(calls=tuple(concurrent_members), sequential=False))
    return ScheduledBatch(groups=tuple(groups)), events


def _log_serialization_events(events: tuple[SerializationEvent, ...]) -> None:
    for evt in events:
        logger.info(
            "ROUND_SERIALIZATION: triggered by %s (%s) — %d tools serialized in this round",
            evt.trigger_tool,
            evt.reason,
            evt.tools_count,
        )


def _build_forced_serial_plan(specs_ordered: list[ToolSpec]) -> ExecutionPlan:
    """One single-call sequential phase per call, in original order.

    Mirrors the previous is_side_effect()-driven downgrade's observable
    behavior: a serialization event fires (reason "forced_serial") whenever any
    call in the batch is a write, covering the whole batch's tools_count — not
    one event per call — since forcing serial only ever "prevents concurrency"
    that a write call could otherwise have raced against.
    """
    batches = tuple(
        ScheduledBatch(
            groups=(
                ScheduledGroup(calls=(spec,), sequential=True, reason="forced_serial"),
            )
        )
        for spec in specs_ordered
    )
    events: tuple[SerializationEvent, ...] = ()
    write_specs = [spec for spec in specs_ordered if spec.is_write]
    if write_specs:
        trigger = write_specs[0]
        events = (
            SerializationEvent(
                trigger_tool=trigger.name,
                reason="forced_serial",
                tools_count=len(specs_ordered),
                resource_scopes=trigger.resource_scopes,
                is_write=True,
                requires_serial=False,
                scheduling_decision="forced_serial",
            ),
        )
    _log_serialization_events(events)
    return ExecutionPlan(batches=batches, serialization_events=events)


def build_execution_groups(
    tool_calls: list[dict],
    call_specs: dict[str, ToolSpec],  # call_id -> ToolSpec
    *,
    force_serial: bool = False,
) -> ExecutionPlan:
    """Build the single-engine DAG execution plan for *tool_calls*.

    When `force_serial` is True, phase-building/conflict-graph construction is
    skipped entirely (see _build_forced_serial_plan()). Otherwise, calls are
    walked in original order building phases, with each requires_serial=True
    call acting as an in-place barrier (see module docstring).

    Raises:
        MissingToolSpecError: if a tool call's call_id has no entry in call_specs.
    """
    specs_ordered: list[ToolSpec] = []
    for tc in tool_calls:
        call_id = tc["id"]
        spec = call_specs.get(call_id)
        if spec is None:
            raise MissingToolSpecError(
                f"No ToolSpec for call_id={call_id!r} (tool={tc['function']['name']!r})"
            )
        specs_ordered.append(spec)

    if not specs_ordered:
        return ExecutionPlan(batches=(), serialization_events=())

    if force_serial:
        return _build_forced_serial_plan(specs_ordered)

    batches: list[ScheduledBatch] = []
    events_list: list[SerializationEvent] = []
    current_phase: list[ToolSpec] = []
    for spec in specs_ordered:
        if not spec.requires_serial:
            current_phase.append(spec)
            continue
        if current_phase:
            batch, phase_events = _build_phase_batch(current_phase)
            batches.append(batch)
            events_list.extend(phase_events)
            current_phase = []
        batches.append(
            ScheduledBatch(
                groups=(
                    ScheduledGroup(
                        calls=(spec,), sequential=True, reason="requires_serial"
                    ),
                )
            )
        )
        events_list.append(
            SerializationEvent(
                trigger_tool=spec.name,
                reason="requires_serial",
                tools_count=1,
                resource_scopes=spec.resource_scopes,
                is_write=spec.is_write,
                requires_serial=True,
                scheduling_decision="serial_barrier",
            )
        )
    if current_phase:
        batch, phase_events = _build_phase_batch(current_phase)
        batches.append(batch)
        events_list.extend(phase_events)

    events = tuple(events_list)
    _log_serialization_events(events)
    return ExecutionPlan(batches=tuple(batches), serialization_events=events)
