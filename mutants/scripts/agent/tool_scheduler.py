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


from mutmut.mutation.trampoline import wrap_in_trampoline as _mutmut_mutated, MutantDict


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
mutants_x__effective_scopes__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x__effective_scopes__mutmut)
def _effective_scopes(spec: ToolSpec) -> tuple[str, ...]:
    """Return spec.resource_scopes, substituting the synthetic global:write scope

    for a write call whose resource_scopes is empty (see _GLOBAL_WRITE_SCOPE)."""
    if spec.is_write and not spec.resource_scopes:
        return (_GLOBAL_WRITE_SCOPE,)
    return spec.resource_scopes


def x__effective_scopes__mutmut_orig(spec: ToolSpec) -> tuple[str, ...]:
    """Return spec.resource_scopes, substituting the synthetic global:write scope

    for a write call whose resource_scopes is empty (see _GLOBAL_WRITE_SCOPE)."""
    if spec.is_write and not spec.resource_scopes:
        return (_GLOBAL_WRITE_SCOPE,)
    return spec.resource_scopes


def x__effective_scopes__mutmut_1(spec: ToolSpec) -> tuple[str, ...]:
    """Return spec.resource_scopes, substituting the synthetic global:write scope

    for a write call whose resource_scopes is empty (see _GLOBAL_WRITE_SCOPE)."""
    if spec.is_write or not spec.resource_scopes:
        return (_GLOBAL_WRITE_SCOPE,)
    return spec.resource_scopes


def x__effective_scopes__mutmut_2(spec: ToolSpec) -> tuple[str, ...]:
    """Return spec.resource_scopes, substituting the synthetic global:write scope

    for a write call whose resource_scopes is empty (see _GLOBAL_WRITE_SCOPE)."""
    if spec.is_write and spec.resource_scopes:
        return (_GLOBAL_WRITE_SCOPE,)
    return spec.resource_scopes

mutants_x__effective_scopes__mutmut['_mutmut_orig'] = x__effective_scopes__mutmut_orig # type: ignore # mutmut generated
mutants_x__effective_scopes__mutmut['x__effective_scopes__mutmut_1'] = x__effective_scopes__mutmut_1 # type: ignore # mutmut generated
mutants_x__effective_scopes__mutmut['x__effective_scopes__mutmut_2'] = x__effective_scopes__mutmut_2 # type: ignore # mutmut generated
mutants_x__classify_conflict_reason__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x__classify_conflict_reason__mutmut)
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


def x__classify_conflict_reason__mutmut_orig(
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


def x__classify_conflict_reason__mutmut_1(
    members: list[ToolSpec], effective: dict[str, tuple[str, ...]]
) -> str:
    """Classify why *members* (a conflict-graph connected component of size > 1)

    must serialize: the global:write fallback, a read/write overlap, or a
    write/write overlap on an explicit shared scope."""
    union_scopes = None
    if union_scopes == {_GLOBAL_WRITE_SCOPE}:
        return "global_write_scope"
    if any(not m.is_write for m in members):
        return "resource_read_write_conflict"
    return "resource_write_write_conflict"


def x__classify_conflict_reason__mutmut_2(
    members: list[ToolSpec], effective: dict[str, tuple[str, ...]]
) -> str:
    """Classify why *members* (a conflict-graph connected component of size > 1)

    must serialize: the global:write fallback, a read/write overlap, or a
    write/write overlap on an explicit shared scope."""
    union_scopes = {scope for m in members for scope in effective[m.call_id]}
    if union_scopes != {_GLOBAL_WRITE_SCOPE}:
        return "global_write_scope"
    if any(not m.is_write for m in members):
        return "resource_read_write_conflict"
    return "resource_write_write_conflict"


def x__classify_conflict_reason__mutmut_3(
    members: list[ToolSpec], effective: dict[str, tuple[str, ...]]
) -> str:
    """Classify why *members* (a conflict-graph connected component of size > 1)

    must serialize: the global:write fallback, a read/write overlap, or a
    write/write overlap on an explicit shared scope."""
    union_scopes = {scope for m in members for scope in effective[m.call_id]}
    if union_scopes == {_GLOBAL_WRITE_SCOPE}:
        return "XXglobal_write_scopeXX"
    if any(not m.is_write for m in members):
        return "resource_read_write_conflict"
    return "resource_write_write_conflict"


def x__classify_conflict_reason__mutmut_4(
    members: list[ToolSpec], effective: dict[str, tuple[str, ...]]
) -> str:
    """Classify why *members* (a conflict-graph connected component of size > 1)

    must serialize: the global:write fallback, a read/write overlap, or a
    write/write overlap on an explicit shared scope."""
    union_scopes = {scope for m in members for scope in effective[m.call_id]}
    if union_scopes == {_GLOBAL_WRITE_SCOPE}:
        return "GLOBAL_WRITE_SCOPE"
    if any(not m.is_write for m in members):
        return "resource_read_write_conflict"
    return "resource_write_write_conflict"


def x__classify_conflict_reason__mutmut_5(
    members: list[ToolSpec], effective: dict[str, tuple[str, ...]]
) -> str:
    """Classify why *members* (a conflict-graph connected component of size > 1)

    must serialize: the global:write fallback, a read/write overlap, or a
    write/write overlap on an explicit shared scope."""
    union_scopes = {scope for m in members for scope in effective[m.call_id]}
    if union_scopes == {_GLOBAL_WRITE_SCOPE}:
        return "global_write_scope"
    if any(None):
        return "resource_read_write_conflict"
    return "resource_write_write_conflict"


def x__classify_conflict_reason__mutmut_6(
    members: list[ToolSpec], effective: dict[str, tuple[str, ...]]
) -> str:
    """Classify why *members* (a conflict-graph connected component of size > 1)

    must serialize: the global:write fallback, a read/write overlap, or a
    write/write overlap on an explicit shared scope."""
    union_scopes = {scope for m in members for scope in effective[m.call_id]}
    if union_scopes == {_GLOBAL_WRITE_SCOPE}:
        return "global_write_scope"
    if any(m.is_write for m in members):
        return "resource_read_write_conflict"
    return "resource_write_write_conflict"


def x__classify_conflict_reason__mutmut_7(
    members: list[ToolSpec], effective: dict[str, tuple[str, ...]]
) -> str:
    """Classify why *members* (a conflict-graph connected component of size > 1)

    must serialize: the global:write fallback, a read/write overlap, or a
    write/write overlap on an explicit shared scope."""
    union_scopes = {scope for m in members for scope in effective[m.call_id]}
    if union_scopes == {_GLOBAL_WRITE_SCOPE}:
        return "global_write_scope"
    if any(not m.is_write for m in members):
        return "XXresource_read_write_conflictXX"
    return "resource_write_write_conflict"


def x__classify_conflict_reason__mutmut_8(
    members: list[ToolSpec], effective: dict[str, tuple[str, ...]]
) -> str:
    """Classify why *members* (a conflict-graph connected component of size > 1)

    must serialize: the global:write fallback, a read/write overlap, or a
    write/write overlap on an explicit shared scope."""
    union_scopes = {scope for m in members for scope in effective[m.call_id]}
    if union_scopes == {_GLOBAL_WRITE_SCOPE}:
        return "global_write_scope"
    if any(not m.is_write for m in members):
        return "RESOURCE_READ_WRITE_CONFLICT"
    return "resource_write_write_conflict"


def x__classify_conflict_reason__mutmut_9(
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
    return "XXresource_write_write_conflictXX"


def x__classify_conflict_reason__mutmut_10(
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
    return "RESOURCE_WRITE_WRITE_CONFLICT"

mutants_x__classify_conflict_reason__mutmut['_mutmut_orig'] = x__classify_conflict_reason__mutmut_orig # type: ignore # mutmut generated
mutants_x__classify_conflict_reason__mutmut['x__classify_conflict_reason__mutmut_1'] = x__classify_conflict_reason__mutmut_1 # type: ignore # mutmut generated
mutants_x__classify_conflict_reason__mutmut['x__classify_conflict_reason__mutmut_2'] = x__classify_conflict_reason__mutmut_2 # type: ignore # mutmut generated
mutants_x__classify_conflict_reason__mutmut['x__classify_conflict_reason__mutmut_3'] = x__classify_conflict_reason__mutmut_3 # type: ignore # mutmut generated
mutants_x__classify_conflict_reason__mutmut['x__classify_conflict_reason__mutmut_4'] = x__classify_conflict_reason__mutmut_4 # type: ignore # mutmut generated
mutants_x__classify_conflict_reason__mutmut['x__classify_conflict_reason__mutmut_5'] = x__classify_conflict_reason__mutmut_5 # type: ignore # mutmut generated
mutants_x__classify_conflict_reason__mutmut['x__classify_conflict_reason__mutmut_6'] = x__classify_conflict_reason__mutmut_6 # type: ignore # mutmut generated
mutants_x__classify_conflict_reason__mutmut['x__classify_conflict_reason__mutmut_7'] = x__classify_conflict_reason__mutmut_7 # type: ignore # mutmut generated
mutants_x__classify_conflict_reason__mutmut['x__classify_conflict_reason__mutmut_8'] = x__classify_conflict_reason__mutmut_8 # type: ignore # mutmut generated
mutants_x__classify_conflict_reason__mutmut['x__classify_conflict_reason__mutmut_9'] = x__classify_conflict_reason__mutmut_9 # type: ignore # mutmut generated
mutants_x__classify_conflict_reason__mutmut['x__classify_conflict_reason__mutmut_10'] = x__classify_conflict_reason__mutmut_10 # type: ignore # mutmut generated
mutants_xǁ_UnionFindǁ__init____mutmut: MutantDict = {}  # type: ignore
mutants_xǁ_UnionFindǁfind__mutmut: MutantDict = {}  # type: ignore
mutants_xǁ_UnionFindǁunion__mutmut: MutantDict = {}  # type: ignore


class _UnionFind:
    """Minimal union-find over call_id strings (no path compression — batches

    are small enough that this stays O(n) in practice)."""

    @_mutmut_mutated(mutants_xǁ_UnionFindǁ__init____mutmut)
    def __init__(self, call_ids: list[str]) -> None:
        self._parent = {call_id: call_id for call_id in call_ids}

    def xǁ_UnionFindǁ__init____mutmut_orig(self, call_ids: list[str]) -> None:
        self._parent = {call_id: call_id for call_id in call_ids}

    def xǁ_UnionFindǁ__init____mutmut_1(self, call_ids: list[str]) -> None:
        self._parent = None

    @_mutmut_mutated(mutants_xǁ_UnionFindǁfind__mutmut)
    def find(self, call_id: str) -> str:
        while self._parent[call_id] != call_id:
            call_id = self._parent[call_id]
        return call_id

    def xǁ_UnionFindǁfind__mutmut_orig(self, call_id: str) -> str:
        while self._parent[call_id] != call_id:
            call_id = self._parent[call_id]
        return call_id

    def xǁ_UnionFindǁfind__mutmut_1(self, call_id: str) -> str:
        while self._parent[call_id] == call_id:
            call_id = self._parent[call_id]
        return call_id

    def xǁ_UnionFindǁfind__mutmut_2(self, call_id: str) -> str:
        while self._parent[call_id] != call_id:
            call_id = None
        return call_id

    @_mutmut_mutated(mutants_xǁ_UnionFindǁunion__mutmut)
    def union(self, a: str, b: str) -> None:
        root_a, root_b = self.find(a), self.find(b)
        if root_a != root_b:
            self._parent[root_a] = root_b

    def xǁ_UnionFindǁunion__mutmut_orig(self, a: str, b: str) -> None:
        root_a, root_b = self.find(a), self.find(b)
        if root_a != root_b:
            self._parent[root_a] = root_b

    def xǁ_UnionFindǁunion__mutmut_1(self, a: str, b: str) -> None:
        root_a, root_b = None
        if root_a != root_b:
            self._parent[root_a] = root_b

    def xǁ_UnionFindǁunion__mutmut_2(self, a: str, b: str) -> None:
        root_a, root_b = self.find(None), self.find(b)
        if root_a != root_b:
            self._parent[root_a] = root_b

    def xǁ_UnionFindǁunion__mutmut_3(self, a: str, b: str) -> None:
        root_a, root_b = self.rfind(a), self.find(b)
        if root_a != root_b:
            self._parent[root_a] = root_b

    def xǁ_UnionFindǁunion__mutmut_4(self, a: str, b: str) -> None:
        root_a, root_b = self.find(a), self.find(None)
        if root_a != root_b:
            self._parent[root_a] = root_b

    def xǁ_UnionFindǁunion__mutmut_5(self, a: str, b: str) -> None:
        root_a, root_b = self.find(a), self.rfind(b)
        if root_a != root_b:
            self._parent[root_a] = root_b

    def xǁ_UnionFindǁunion__mutmut_6(self, a: str, b: str) -> None:
        root_a, root_b = self.find(a), self.find(b)
        if root_a == root_b:
            self._parent[root_a] = root_b

    def xǁ_UnionFindǁunion__mutmut_7(self, a: str, b: str) -> None:
        root_a, root_b = self.find(a), self.find(b)
        if root_a != root_b:
            self._parent[root_a] = None

mutants_xǁ_UnionFindǁ__init____mutmut['_mutmut_orig'] = _UnionFind.xǁ_UnionFindǁ__init____mutmut_orig # type: ignore # mutmut generated
mutants_xǁ_UnionFindǁ__init____mutmut['xǁ_UnionFindǁ__init____mutmut_1'] = _UnionFind.xǁ_UnionFindǁ__init____mutmut_1 # type: ignore # mutmut generated

mutants_xǁ_UnionFindǁfind__mutmut['_mutmut_orig'] = _UnionFind.xǁ_UnionFindǁfind__mutmut_orig # type: ignore # mutmut generated
mutants_xǁ_UnionFindǁfind__mutmut['xǁ_UnionFindǁfind__mutmut_1'] = _UnionFind.xǁ_UnionFindǁfind__mutmut_1 # type: ignore # mutmut generated
mutants_xǁ_UnionFindǁfind__mutmut['xǁ_UnionFindǁfind__mutmut_2'] = _UnionFind.xǁ_UnionFindǁfind__mutmut_2 # type: ignore # mutmut generated

mutants_xǁ_UnionFindǁunion__mutmut['_mutmut_orig'] = _UnionFind.xǁ_UnionFindǁunion__mutmut_orig # type: ignore # mutmut generated
mutants_xǁ_UnionFindǁunion__mutmut['xǁ_UnionFindǁunion__mutmut_1'] = _UnionFind.xǁ_UnionFindǁunion__mutmut_1 # type: ignore # mutmut generated
mutants_xǁ_UnionFindǁunion__mutmut['xǁ_UnionFindǁunion__mutmut_2'] = _UnionFind.xǁ_UnionFindǁunion__mutmut_2 # type: ignore # mutmut generated
mutants_xǁ_UnionFindǁunion__mutmut['xǁ_UnionFindǁunion__mutmut_3'] = _UnionFind.xǁ_UnionFindǁunion__mutmut_3 # type: ignore # mutmut generated
mutants_xǁ_UnionFindǁunion__mutmut['xǁ_UnionFindǁunion__mutmut_4'] = _UnionFind.xǁ_UnionFindǁunion__mutmut_4 # type: ignore # mutmut generated
mutants_xǁ_UnionFindǁunion__mutmut['xǁ_UnionFindǁunion__mutmut_5'] = _UnionFind.xǁ_UnionFindǁunion__mutmut_5 # type: ignore # mutmut generated
mutants_xǁ_UnionFindǁunion__mutmut['xǁ_UnionFindǁunion__mutmut_6'] = _UnionFind.xǁ_UnionFindǁunion__mutmut_6 # type: ignore # mutmut generated
mutants_xǁ_UnionFindǁunion__mutmut['xǁ_UnionFindǁunion__mutmut_7'] = _UnionFind.xǁ_UnionFindǁunion__mutmut_7 # type: ignore # mutmut generated
mutants_x__build_phase_batch__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x__build_phase_batch__mutmut)
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


def x__build_phase_batch__mutmut_orig(
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


def x__build_phase_batch__mutmut_1(
    specs: list[ToolSpec],
) -> tuple[ScheduledBatch, list[SerializationEvent]]:
    """Partition one phase's calls into sequential conflict groups plus one

    concurrent group pooling everything left un-conflicted. Read/read pairs
    never conflict; an edge exists only when either side is_write=True and
    their (effective) resource_scopes overlap.
    """
    effective = None
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


def x__build_phase_batch__mutmut_2(
    specs: list[ToolSpec],
) -> tuple[ScheduledBatch, list[SerializationEvent]]:
    """Partition one phase's calls into sequential conflict groups plus one

    concurrent group pooling everything left un-conflicted. Read/read pairs
    never conflict; an edge exists only when either side is_write=True and
    their (effective) resource_scopes overlap.
    """
    effective = {spec.call_id: _effective_scopes(None) for spec in specs}
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


def x__build_phase_batch__mutmut_3(
    specs: list[ToolSpec],
) -> tuple[ScheduledBatch, list[SerializationEvent]]:
    """Partition one phase's calls into sequential conflict groups plus one

    concurrent group pooling everything left un-conflicted. Read/read pairs
    never conflict; an edge exists only when either side is_write=True and
    their (effective) resource_scopes overlap.
    """
    effective = {spec.call_id: _effective_scopes(spec) for spec in specs}
    uf = None

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


def x__build_phase_batch__mutmut_4(
    specs: list[ToolSpec],
) -> tuple[ScheduledBatch, list[SerializationEvent]]:
    """Partition one phase's calls into sequential conflict groups plus one

    concurrent group pooling everything left un-conflicted. Read/read pairs
    never conflict; an edge exists only when either side is_write=True and
    their (effective) resource_scopes overlap.
    """
    effective = {spec.call_id: _effective_scopes(spec) for spec in specs}
    uf = _UnionFind(None)

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


def x__build_phase_batch__mutmut_5(
    specs: list[ToolSpec],
) -> tuple[ScheduledBatch, list[SerializationEvent]]:
    """Partition one phase's calls into sequential conflict groups plus one

    concurrent group pooling everything left un-conflicted. Read/read pairs
    never conflict; an edge exists only when either side is_write=True and
    their (effective) resource_scopes overlap.
    """
    effective = {spec.call_id: _effective_scopes(spec) for spec in specs}
    uf = _UnionFind([spec.call_id for spec in specs])

    for i, spec_a in enumerate(None):
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


def x__build_phase_batch__mutmut_6(
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
        for spec_b in specs[i - 1 :]:
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


def x__build_phase_batch__mutmut_7(
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
        for spec_b in specs[i + 2 :]:
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


def x__build_phase_batch__mutmut_8(
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
            if (spec_a.is_write or spec_b.is_write):
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


def x__build_phase_batch__mutmut_9(
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
            if not (spec_a.is_write and spec_b.is_write):
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


def x__build_phase_batch__mutmut_10(
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
                break
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


def x__build_phase_batch__mutmut_11(
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
                None
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


def x__build_phase_batch__mutmut_12(
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
                _scopes_conflict(None, scope_b)
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


def x__build_phase_batch__mutmut_13(
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
                _scopes_conflict(scope_a, None)
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


def x__build_phase_batch__mutmut_14(
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
                _scopes_conflict(scope_b)
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


def x__build_phase_batch__mutmut_15(
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
                _scopes_conflict(scope_a, )
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


def x__build_phase_batch__mutmut_16(
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
                uf.union(None, spec_b.call_id)

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


def x__build_phase_batch__mutmut_17(
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
                uf.union(spec_a.call_id, None)

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


def x__build_phase_batch__mutmut_18(
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
                uf.union(spec_b.call_id)

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


def x__build_phase_batch__mutmut_19(
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
                uf.union(spec_a.call_id, )

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


def x__build_phase_batch__mutmut_20(
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

    components: dict[str, list[ToolSpec]] = None
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


def x__build_phase_batch__mutmut_21(
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
        components.setdefault(uf.find(spec.call_id), []).append(None)

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


def x__build_phase_batch__mutmut_22(
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
        components.setdefault(None, []).append(spec)

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


def x__build_phase_batch__mutmut_23(
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
        components.setdefault(uf.find(spec.call_id), None).append(spec)

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


def x__build_phase_batch__mutmut_24(
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
        components.setdefault([]).append(spec)

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


def x__build_phase_batch__mutmut_25(
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
        components.setdefault(uf.find(spec.call_id), ).append(spec)

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


def x__build_phase_batch__mutmut_26(
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
        components.setdefault(uf.find(None), []).append(spec)

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


def x__build_phase_batch__mutmut_27(
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
        components.setdefault(uf.rfind(spec.call_id), []).append(spec)

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


def x__build_phase_batch__mutmut_28(
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

    order = None
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


def x__build_phase_batch__mutmut_29(
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

    order = {spec.call_id: i for i, spec in enumerate(None)}
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


def x__build_phase_batch__mutmut_30(
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
    sequential_groups: list[ScheduledGroup] = None
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


def x__build_phase_batch__mutmut_31(
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
    events: list[SerializationEvent] = None
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


def x__build_phase_batch__mutmut_32(
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
    concurrent_members: list[ToolSpec] = None
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


def x__build_phase_batch__mutmut_33(
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
        if len(members) != 1:
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


def x__build_phase_batch__mutmut_34(
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
        if len(members) == 2:
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


def x__build_phase_batch__mutmut_35(
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
            concurrent_members.append(None)
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


def x__build_phase_batch__mutmut_36(
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
            concurrent_members.append(members[1])
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


def x__build_phase_batch__mutmut_37(
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
            break
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


def x__build_phase_batch__mutmut_38(
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
        reason = None
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


def x__build_phase_batch__mutmut_39(
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
        reason = _classify_conflict_reason(None, effective)
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


def x__build_phase_batch__mutmut_40(
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
        reason = _classify_conflict_reason(members, None)
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


def x__build_phase_batch__mutmut_41(
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
        reason = _classify_conflict_reason(effective)
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


def x__build_phase_batch__mutmut_42(
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
        reason = _classify_conflict_reason(members, )
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


def x__build_phase_batch__mutmut_43(
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
            None
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


def x__build_phase_batch__mutmut_44(
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
            ScheduledGroup(calls=None, sequential=True, reason=reason)
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


def x__build_phase_batch__mutmut_45(
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
            ScheduledGroup(calls=tuple(members), sequential=None, reason=reason)
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


def x__build_phase_batch__mutmut_46(
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
            ScheduledGroup(calls=tuple(members), sequential=True, reason=None)
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


def x__build_phase_batch__mutmut_47(
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
            ScheduledGroup(sequential=True, reason=reason)
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


def x__build_phase_batch__mutmut_48(
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
            ScheduledGroup(calls=tuple(members), reason=reason)
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


def x__build_phase_batch__mutmut_49(
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
            ScheduledGroup(calls=tuple(members), sequential=True, )
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


def x__build_phase_batch__mutmut_50(
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
            ScheduledGroup(calls=tuple(None), sequential=True, reason=reason)
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


def x__build_phase_batch__mutmut_51(
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
            ScheduledGroup(calls=tuple(members), sequential=False, reason=reason)
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


def x__build_phase_batch__mutmut_52(
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
        union_scopes = None
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


def x__build_phase_batch__mutmut_53(
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
            None
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


def x__build_phase_batch__mutmut_54(
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
            dict.fromkeys(None)
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


def x__build_phase_batch__mutmut_55(
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
            None
        )

    sequential_groups.sort(key=lambda g: order[g.calls[0].call_id])
    concurrent_members.sort(key=lambda spec: order[spec.call_id])

    groups: list[ScheduledGroup] = list(sequential_groups)
    if concurrent_members:
        groups.append(ScheduledGroup(calls=tuple(concurrent_members), sequential=False))
    return ScheduledBatch(groups=tuple(groups)), events


def x__build_phase_batch__mutmut_56(
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
                trigger_tool=None,
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


def x__build_phase_batch__mutmut_57(
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
                reason=None,
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


def x__build_phase_batch__mutmut_58(
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
                tools_count=None,
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


def x__build_phase_batch__mutmut_59(
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
                resource_scopes=None,
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


def x__build_phase_batch__mutmut_60(
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
                is_write=None,
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


def x__build_phase_batch__mutmut_61(
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
                requires_serial=None,
                scheduling_decision="resource_scope",
            )
        )

    sequential_groups.sort(key=lambda g: order[g.calls[0].call_id])
    concurrent_members.sort(key=lambda spec: order[spec.call_id])

    groups: list[ScheduledGroup] = list(sequential_groups)
    if concurrent_members:
        groups.append(ScheduledGroup(calls=tuple(concurrent_members), sequential=False))
    return ScheduledBatch(groups=tuple(groups)), events


def x__build_phase_batch__mutmut_62(
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
                scheduling_decision=None,
            )
        )

    sequential_groups.sort(key=lambda g: order[g.calls[0].call_id])
    concurrent_members.sort(key=lambda spec: order[spec.call_id])

    groups: list[ScheduledGroup] = list(sequential_groups)
    if concurrent_members:
        groups.append(ScheduledGroup(calls=tuple(concurrent_members), sequential=False))
    return ScheduledBatch(groups=tuple(groups)), events


def x__build_phase_batch__mutmut_63(
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


def x__build_phase_batch__mutmut_64(
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


def x__build_phase_batch__mutmut_65(
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


def x__build_phase_batch__mutmut_66(
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


def x__build_phase_batch__mutmut_67(
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


def x__build_phase_batch__mutmut_68(
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
                scheduling_decision="resource_scope",
            )
        )

    sequential_groups.sort(key=lambda g: order[g.calls[0].call_id])
    concurrent_members.sort(key=lambda spec: order[spec.call_id])

    groups: list[ScheduledGroup] = list(sequential_groups)
    if concurrent_members:
        groups.append(ScheduledGroup(calls=tuple(concurrent_members), sequential=False))
    return ScheduledBatch(groups=tuple(groups)), events


def x__build_phase_batch__mutmut_69(
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
                )
        )

    sequential_groups.sort(key=lambda g: order[g.calls[0].call_id])
    concurrent_members.sort(key=lambda spec: order[spec.call_id])

    groups: list[ScheduledGroup] = list(sequential_groups)
    if concurrent_members:
        groups.append(ScheduledGroup(calls=tuple(concurrent_members), sequential=False))
    return ScheduledBatch(groups=tuple(groups)), events


def x__build_phase_batch__mutmut_70(
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
                trigger_tool=members[1].name,
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


def x__build_phase_batch__mutmut_71(
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
                is_write=any(None),
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


def x__build_phase_batch__mutmut_72(
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
                requires_serial=True,
                scheduling_decision="resource_scope",
            )
        )

    sequential_groups.sort(key=lambda g: order[g.calls[0].call_id])
    concurrent_members.sort(key=lambda spec: order[spec.call_id])

    groups: list[ScheduledGroup] = list(sequential_groups)
    if concurrent_members:
        groups.append(ScheduledGroup(calls=tuple(concurrent_members), sequential=False))
    return ScheduledBatch(groups=tuple(groups)), events


def x__build_phase_batch__mutmut_73(
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
                scheduling_decision="XXresource_scopeXX",
            )
        )

    sequential_groups.sort(key=lambda g: order[g.calls[0].call_id])
    concurrent_members.sort(key=lambda spec: order[spec.call_id])

    groups: list[ScheduledGroup] = list(sequential_groups)
    if concurrent_members:
        groups.append(ScheduledGroup(calls=tuple(concurrent_members), sequential=False))
    return ScheduledBatch(groups=tuple(groups)), events


def x__build_phase_batch__mutmut_74(
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
                scheduling_decision="RESOURCE_SCOPE",
            )
        )

    sequential_groups.sort(key=lambda g: order[g.calls[0].call_id])
    concurrent_members.sort(key=lambda spec: order[spec.call_id])

    groups: list[ScheduledGroup] = list(sequential_groups)
    if concurrent_members:
        groups.append(ScheduledGroup(calls=tuple(concurrent_members), sequential=False))
    return ScheduledBatch(groups=tuple(groups)), events


def x__build_phase_batch__mutmut_75(
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

    sequential_groups.sort(key=None)
    concurrent_members.sort(key=lambda spec: order[spec.call_id])

    groups: list[ScheduledGroup] = list(sequential_groups)
    if concurrent_members:
        groups.append(ScheduledGroup(calls=tuple(concurrent_members), sequential=False))
    return ScheduledBatch(groups=tuple(groups)), events


def x__build_phase_batch__mutmut_76(
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

    sequential_groups.sort(key=lambda g: None)
    concurrent_members.sort(key=lambda spec: order[spec.call_id])

    groups: list[ScheduledGroup] = list(sequential_groups)
    if concurrent_members:
        groups.append(ScheduledGroup(calls=tuple(concurrent_members), sequential=False))
    return ScheduledBatch(groups=tuple(groups)), events


def x__build_phase_batch__mutmut_77(
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

    sequential_groups.sort(key=lambda g: order[g.calls[1].call_id])
    concurrent_members.sort(key=lambda spec: order[spec.call_id])

    groups: list[ScheduledGroup] = list(sequential_groups)
    if concurrent_members:
        groups.append(ScheduledGroup(calls=tuple(concurrent_members), sequential=False))
    return ScheduledBatch(groups=tuple(groups)), events


def x__build_phase_batch__mutmut_78(
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
    concurrent_members.sort(key=None)

    groups: list[ScheduledGroup] = list(sequential_groups)
    if concurrent_members:
        groups.append(ScheduledGroup(calls=tuple(concurrent_members), sequential=False))
    return ScheduledBatch(groups=tuple(groups)), events


def x__build_phase_batch__mutmut_79(
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
    concurrent_members.sort(key=lambda spec: None)

    groups: list[ScheduledGroup] = list(sequential_groups)
    if concurrent_members:
        groups.append(ScheduledGroup(calls=tuple(concurrent_members), sequential=False))
    return ScheduledBatch(groups=tuple(groups)), events


def x__build_phase_batch__mutmut_80(
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

    groups: list[ScheduledGroup] = None
    if concurrent_members:
        groups.append(ScheduledGroup(calls=tuple(concurrent_members), sequential=False))
    return ScheduledBatch(groups=tuple(groups)), events


def x__build_phase_batch__mutmut_81(
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

    groups: list[ScheduledGroup] = list(None)
    if concurrent_members:
        groups.append(ScheduledGroup(calls=tuple(concurrent_members), sequential=False))
    return ScheduledBatch(groups=tuple(groups)), events


def x__build_phase_batch__mutmut_82(
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
        groups.append(None)
    return ScheduledBatch(groups=tuple(groups)), events


def x__build_phase_batch__mutmut_83(
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
        groups.append(ScheduledGroup(calls=None, sequential=False))
    return ScheduledBatch(groups=tuple(groups)), events


def x__build_phase_batch__mutmut_84(
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
        groups.append(ScheduledGroup(calls=tuple(concurrent_members), sequential=None))
    return ScheduledBatch(groups=tuple(groups)), events


def x__build_phase_batch__mutmut_85(
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
        groups.append(ScheduledGroup(sequential=False))
    return ScheduledBatch(groups=tuple(groups)), events


def x__build_phase_batch__mutmut_86(
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
        groups.append(ScheduledGroup(calls=tuple(concurrent_members), ))
    return ScheduledBatch(groups=tuple(groups)), events


def x__build_phase_batch__mutmut_87(
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
        groups.append(ScheduledGroup(calls=tuple(None), sequential=False))
    return ScheduledBatch(groups=tuple(groups)), events


def x__build_phase_batch__mutmut_88(
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
        groups.append(ScheduledGroup(calls=tuple(concurrent_members), sequential=True))
    return ScheduledBatch(groups=tuple(groups)), events


def x__build_phase_batch__mutmut_89(
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
    return ScheduledBatch(groups=None), events


def x__build_phase_batch__mutmut_90(
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
    return ScheduledBatch(groups=tuple(None)), events

mutants_x__build_phase_batch__mutmut['_mutmut_orig'] = x__build_phase_batch__mutmut_orig # type: ignore # mutmut generated
mutants_x__build_phase_batch__mutmut['x__build_phase_batch__mutmut_1'] = x__build_phase_batch__mutmut_1 # type: ignore # mutmut generated
mutants_x__build_phase_batch__mutmut['x__build_phase_batch__mutmut_2'] = x__build_phase_batch__mutmut_2 # type: ignore # mutmut generated
mutants_x__build_phase_batch__mutmut['x__build_phase_batch__mutmut_3'] = x__build_phase_batch__mutmut_3 # type: ignore # mutmut generated
mutants_x__build_phase_batch__mutmut['x__build_phase_batch__mutmut_4'] = x__build_phase_batch__mutmut_4 # type: ignore # mutmut generated
mutants_x__build_phase_batch__mutmut['x__build_phase_batch__mutmut_5'] = x__build_phase_batch__mutmut_5 # type: ignore # mutmut generated
mutants_x__build_phase_batch__mutmut['x__build_phase_batch__mutmut_6'] = x__build_phase_batch__mutmut_6 # type: ignore # mutmut generated
mutants_x__build_phase_batch__mutmut['x__build_phase_batch__mutmut_7'] = x__build_phase_batch__mutmut_7 # type: ignore # mutmut generated
mutants_x__build_phase_batch__mutmut['x__build_phase_batch__mutmut_8'] = x__build_phase_batch__mutmut_8 # type: ignore # mutmut generated
mutants_x__build_phase_batch__mutmut['x__build_phase_batch__mutmut_9'] = x__build_phase_batch__mutmut_9 # type: ignore # mutmut generated
mutants_x__build_phase_batch__mutmut['x__build_phase_batch__mutmut_10'] = x__build_phase_batch__mutmut_10 # type: ignore # mutmut generated
mutants_x__build_phase_batch__mutmut['x__build_phase_batch__mutmut_11'] = x__build_phase_batch__mutmut_11 # type: ignore # mutmut generated
mutants_x__build_phase_batch__mutmut['x__build_phase_batch__mutmut_12'] = x__build_phase_batch__mutmut_12 # type: ignore # mutmut generated
mutants_x__build_phase_batch__mutmut['x__build_phase_batch__mutmut_13'] = x__build_phase_batch__mutmut_13 # type: ignore # mutmut generated
mutants_x__build_phase_batch__mutmut['x__build_phase_batch__mutmut_14'] = x__build_phase_batch__mutmut_14 # type: ignore # mutmut generated
mutants_x__build_phase_batch__mutmut['x__build_phase_batch__mutmut_15'] = x__build_phase_batch__mutmut_15 # type: ignore # mutmut generated
mutants_x__build_phase_batch__mutmut['x__build_phase_batch__mutmut_16'] = x__build_phase_batch__mutmut_16 # type: ignore # mutmut generated
mutants_x__build_phase_batch__mutmut['x__build_phase_batch__mutmut_17'] = x__build_phase_batch__mutmut_17 # type: ignore # mutmut generated
mutants_x__build_phase_batch__mutmut['x__build_phase_batch__mutmut_18'] = x__build_phase_batch__mutmut_18 # type: ignore # mutmut generated
mutants_x__build_phase_batch__mutmut['x__build_phase_batch__mutmut_19'] = x__build_phase_batch__mutmut_19 # type: ignore # mutmut generated
mutants_x__build_phase_batch__mutmut['x__build_phase_batch__mutmut_20'] = x__build_phase_batch__mutmut_20 # type: ignore # mutmut generated
mutants_x__build_phase_batch__mutmut['x__build_phase_batch__mutmut_21'] = x__build_phase_batch__mutmut_21 # type: ignore # mutmut generated
mutants_x__build_phase_batch__mutmut['x__build_phase_batch__mutmut_22'] = x__build_phase_batch__mutmut_22 # type: ignore # mutmut generated
mutants_x__build_phase_batch__mutmut['x__build_phase_batch__mutmut_23'] = x__build_phase_batch__mutmut_23 # type: ignore # mutmut generated
mutants_x__build_phase_batch__mutmut['x__build_phase_batch__mutmut_24'] = x__build_phase_batch__mutmut_24 # type: ignore # mutmut generated
mutants_x__build_phase_batch__mutmut['x__build_phase_batch__mutmut_25'] = x__build_phase_batch__mutmut_25 # type: ignore # mutmut generated
mutants_x__build_phase_batch__mutmut['x__build_phase_batch__mutmut_26'] = x__build_phase_batch__mutmut_26 # type: ignore # mutmut generated
mutants_x__build_phase_batch__mutmut['x__build_phase_batch__mutmut_27'] = x__build_phase_batch__mutmut_27 # type: ignore # mutmut generated
mutants_x__build_phase_batch__mutmut['x__build_phase_batch__mutmut_28'] = x__build_phase_batch__mutmut_28 # type: ignore # mutmut generated
mutants_x__build_phase_batch__mutmut['x__build_phase_batch__mutmut_29'] = x__build_phase_batch__mutmut_29 # type: ignore # mutmut generated
mutants_x__build_phase_batch__mutmut['x__build_phase_batch__mutmut_30'] = x__build_phase_batch__mutmut_30 # type: ignore # mutmut generated
mutants_x__build_phase_batch__mutmut['x__build_phase_batch__mutmut_31'] = x__build_phase_batch__mutmut_31 # type: ignore # mutmut generated
mutants_x__build_phase_batch__mutmut['x__build_phase_batch__mutmut_32'] = x__build_phase_batch__mutmut_32 # type: ignore # mutmut generated
mutants_x__build_phase_batch__mutmut['x__build_phase_batch__mutmut_33'] = x__build_phase_batch__mutmut_33 # type: ignore # mutmut generated
mutants_x__build_phase_batch__mutmut['x__build_phase_batch__mutmut_34'] = x__build_phase_batch__mutmut_34 # type: ignore # mutmut generated
mutants_x__build_phase_batch__mutmut['x__build_phase_batch__mutmut_35'] = x__build_phase_batch__mutmut_35 # type: ignore # mutmut generated
mutants_x__build_phase_batch__mutmut['x__build_phase_batch__mutmut_36'] = x__build_phase_batch__mutmut_36 # type: ignore # mutmut generated
mutants_x__build_phase_batch__mutmut['x__build_phase_batch__mutmut_37'] = x__build_phase_batch__mutmut_37 # type: ignore # mutmut generated
mutants_x__build_phase_batch__mutmut['x__build_phase_batch__mutmut_38'] = x__build_phase_batch__mutmut_38 # type: ignore # mutmut generated
mutants_x__build_phase_batch__mutmut['x__build_phase_batch__mutmut_39'] = x__build_phase_batch__mutmut_39 # type: ignore # mutmut generated
mutants_x__build_phase_batch__mutmut['x__build_phase_batch__mutmut_40'] = x__build_phase_batch__mutmut_40 # type: ignore # mutmut generated
mutants_x__build_phase_batch__mutmut['x__build_phase_batch__mutmut_41'] = x__build_phase_batch__mutmut_41 # type: ignore # mutmut generated
mutants_x__build_phase_batch__mutmut['x__build_phase_batch__mutmut_42'] = x__build_phase_batch__mutmut_42 # type: ignore # mutmut generated
mutants_x__build_phase_batch__mutmut['x__build_phase_batch__mutmut_43'] = x__build_phase_batch__mutmut_43 # type: ignore # mutmut generated
mutants_x__build_phase_batch__mutmut['x__build_phase_batch__mutmut_44'] = x__build_phase_batch__mutmut_44 # type: ignore # mutmut generated
mutants_x__build_phase_batch__mutmut['x__build_phase_batch__mutmut_45'] = x__build_phase_batch__mutmut_45 # type: ignore # mutmut generated
mutants_x__build_phase_batch__mutmut['x__build_phase_batch__mutmut_46'] = x__build_phase_batch__mutmut_46 # type: ignore # mutmut generated
mutants_x__build_phase_batch__mutmut['x__build_phase_batch__mutmut_47'] = x__build_phase_batch__mutmut_47 # type: ignore # mutmut generated
mutants_x__build_phase_batch__mutmut['x__build_phase_batch__mutmut_48'] = x__build_phase_batch__mutmut_48 # type: ignore # mutmut generated
mutants_x__build_phase_batch__mutmut['x__build_phase_batch__mutmut_49'] = x__build_phase_batch__mutmut_49 # type: ignore # mutmut generated
mutants_x__build_phase_batch__mutmut['x__build_phase_batch__mutmut_50'] = x__build_phase_batch__mutmut_50 # type: ignore # mutmut generated
mutants_x__build_phase_batch__mutmut['x__build_phase_batch__mutmut_51'] = x__build_phase_batch__mutmut_51 # type: ignore # mutmut generated
mutants_x__build_phase_batch__mutmut['x__build_phase_batch__mutmut_52'] = x__build_phase_batch__mutmut_52 # type: ignore # mutmut generated
mutants_x__build_phase_batch__mutmut['x__build_phase_batch__mutmut_53'] = x__build_phase_batch__mutmut_53 # type: ignore # mutmut generated
mutants_x__build_phase_batch__mutmut['x__build_phase_batch__mutmut_54'] = x__build_phase_batch__mutmut_54 # type: ignore # mutmut generated
mutants_x__build_phase_batch__mutmut['x__build_phase_batch__mutmut_55'] = x__build_phase_batch__mutmut_55 # type: ignore # mutmut generated
mutants_x__build_phase_batch__mutmut['x__build_phase_batch__mutmut_56'] = x__build_phase_batch__mutmut_56 # type: ignore # mutmut generated
mutants_x__build_phase_batch__mutmut['x__build_phase_batch__mutmut_57'] = x__build_phase_batch__mutmut_57 # type: ignore # mutmut generated
mutants_x__build_phase_batch__mutmut['x__build_phase_batch__mutmut_58'] = x__build_phase_batch__mutmut_58 # type: ignore # mutmut generated
mutants_x__build_phase_batch__mutmut['x__build_phase_batch__mutmut_59'] = x__build_phase_batch__mutmut_59 # type: ignore # mutmut generated
mutants_x__build_phase_batch__mutmut['x__build_phase_batch__mutmut_60'] = x__build_phase_batch__mutmut_60 # type: ignore # mutmut generated
mutants_x__build_phase_batch__mutmut['x__build_phase_batch__mutmut_61'] = x__build_phase_batch__mutmut_61 # type: ignore # mutmut generated
mutants_x__build_phase_batch__mutmut['x__build_phase_batch__mutmut_62'] = x__build_phase_batch__mutmut_62 # type: ignore # mutmut generated
mutants_x__build_phase_batch__mutmut['x__build_phase_batch__mutmut_63'] = x__build_phase_batch__mutmut_63 # type: ignore # mutmut generated
mutants_x__build_phase_batch__mutmut['x__build_phase_batch__mutmut_64'] = x__build_phase_batch__mutmut_64 # type: ignore # mutmut generated
mutants_x__build_phase_batch__mutmut['x__build_phase_batch__mutmut_65'] = x__build_phase_batch__mutmut_65 # type: ignore # mutmut generated
mutants_x__build_phase_batch__mutmut['x__build_phase_batch__mutmut_66'] = x__build_phase_batch__mutmut_66 # type: ignore # mutmut generated
mutants_x__build_phase_batch__mutmut['x__build_phase_batch__mutmut_67'] = x__build_phase_batch__mutmut_67 # type: ignore # mutmut generated
mutants_x__build_phase_batch__mutmut['x__build_phase_batch__mutmut_68'] = x__build_phase_batch__mutmut_68 # type: ignore # mutmut generated
mutants_x__build_phase_batch__mutmut['x__build_phase_batch__mutmut_69'] = x__build_phase_batch__mutmut_69 # type: ignore # mutmut generated
mutants_x__build_phase_batch__mutmut['x__build_phase_batch__mutmut_70'] = x__build_phase_batch__mutmut_70 # type: ignore # mutmut generated
mutants_x__build_phase_batch__mutmut['x__build_phase_batch__mutmut_71'] = x__build_phase_batch__mutmut_71 # type: ignore # mutmut generated
mutants_x__build_phase_batch__mutmut['x__build_phase_batch__mutmut_72'] = x__build_phase_batch__mutmut_72 # type: ignore # mutmut generated
mutants_x__build_phase_batch__mutmut['x__build_phase_batch__mutmut_73'] = x__build_phase_batch__mutmut_73 # type: ignore # mutmut generated
mutants_x__build_phase_batch__mutmut['x__build_phase_batch__mutmut_74'] = x__build_phase_batch__mutmut_74 # type: ignore # mutmut generated
mutants_x__build_phase_batch__mutmut['x__build_phase_batch__mutmut_75'] = x__build_phase_batch__mutmut_75 # type: ignore # mutmut generated
mutants_x__build_phase_batch__mutmut['x__build_phase_batch__mutmut_76'] = x__build_phase_batch__mutmut_76 # type: ignore # mutmut generated
mutants_x__build_phase_batch__mutmut['x__build_phase_batch__mutmut_77'] = x__build_phase_batch__mutmut_77 # type: ignore # mutmut generated
mutants_x__build_phase_batch__mutmut['x__build_phase_batch__mutmut_78'] = x__build_phase_batch__mutmut_78 # type: ignore # mutmut generated
mutants_x__build_phase_batch__mutmut['x__build_phase_batch__mutmut_79'] = x__build_phase_batch__mutmut_79 # type: ignore # mutmut generated
mutants_x__build_phase_batch__mutmut['x__build_phase_batch__mutmut_80'] = x__build_phase_batch__mutmut_80 # type: ignore # mutmut generated
mutants_x__build_phase_batch__mutmut['x__build_phase_batch__mutmut_81'] = x__build_phase_batch__mutmut_81 # type: ignore # mutmut generated
mutants_x__build_phase_batch__mutmut['x__build_phase_batch__mutmut_82'] = x__build_phase_batch__mutmut_82 # type: ignore # mutmut generated
mutants_x__build_phase_batch__mutmut['x__build_phase_batch__mutmut_83'] = x__build_phase_batch__mutmut_83 # type: ignore # mutmut generated
mutants_x__build_phase_batch__mutmut['x__build_phase_batch__mutmut_84'] = x__build_phase_batch__mutmut_84 # type: ignore # mutmut generated
mutants_x__build_phase_batch__mutmut['x__build_phase_batch__mutmut_85'] = x__build_phase_batch__mutmut_85 # type: ignore # mutmut generated
mutants_x__build_phase_batch__mutmut['x__build_phase_batch__mutmut_86'] = x__build_phase_batch__mutmut_86 # type: ignore # mutmut generated
mutants_x__build_phase_batch__mutmut['x__build_phase_batch__mutmut_87'] = x__build_phase_batch__mutmut_87 # type: ignore # mutmut generated
mutants_x__build_phase_batch__mutmut['x__build_phase_batch__mutmut_88'] = x__build_phase_batch__mutmut_88 # type: ignore # mutmut generated
mutants_x__build_phase_batch__mutmut['x__build_phase_batch__mutmut_89'] = x__build_phase_batch__mutmut_89 # type: ignore # mutmut generated
mutants_x__build_phase_batch__mutmut['x__build_phase_batch__mutmut_90'] = x__build_phase_batch__mutmut_90 # type: ignore # mutmut generated
mutants_x__log_serialization_events__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x__log_serialization_events__mutmut)
def _log_serialization_events(events: tuple[SerializationEvent, ...]) -> None:
    for evt in events:
        logger.info(
            "ROUND_SERIALIZATION: triggered by %s (%s) — %d tools serialized in this round",
            evt.trigger_tool,
            evt.reason,
            evt.tools_count,
        )


def x__log_serialization_events__mutmut_orig(events: tuple[SerializationEvent, ...]) -> None:
    for evt in events:
        logger.info(
            "ROUND_SERIALIZATION: triggered by %s (%s) — %d tools serialized in this round",
            evt.trigger_tool,
            evt.reason,
            evt.tools_count,
        )


def x__log_serialization_events__mutmut_1(events: tuple[SerializationEvent, ...]) -> None:
    for evt in events:
        logger.info(
            None,
            evt.trigger_tool,
            evt.reason,
            evt.tools_count,
        )


def x__log_serialization_events__mutmut_2(events: tuple[SerializationEvent, ...]) -> None:
    for evt in events:
        logger.info(
            "ROUND_SERIALIZATION: triggered by %s (%s) — %d tools serialized in this round",
            None,
            evt.reason,
            evt.tools_count,
        )


def x__log_serialization_events__mutmut_3(events: tuple[SerializationEvent, ...]) -> None:
    for evt in events:
        logger.info(
            "ROUND_SERIALIZATION: triggered by %s (%s) — %d tools serialized in this round",
            evt.trigger_tool,
            None,
            evt.tools_count,
        )


def x__log_serialization_events__mutmut_4(events: tuple[SerializationEvent, ...]) -> None:
    for evt in events:
        logger.info(
            "ROUND_SERIALIZATION: triggered by %s (%s) — %d tools serialized in this round",
            evt.trigger_tool,
            evt.reason,
            None,
        )


def x__log_serialization_events__mutmut_5(events: tuple[SerializationEvent, ...]) -> None:
    for evt in events:
        logger.info(
            evt.trigger_tool,
            evt.reason,
            evt.tools_count,
        )


def x__log_serialization_events__mutmut_6(events: tuple[SerializationEvent, ...]) -> None:
    for evt in events:
        logger.info(
            "ROUND_SERIALIZATION: triggered by %s (%s) — %d tools serialized in this round",
            evt.reason,
            evt.tools_count,
        )


def x__log_serialization_events__mutmut_7(events: tuple[SerializationEvent, ...]) -> None:
    for evt in events:
        logger.info(
            "ROUND_SERIALIZATION: triggered by %s (%s) — %d tools serialized in this round",
            evt.trigger_tool,
            evt.tools_count,
        )


def x__log_serialization_events__mutmut_8(events: tuple[SerializationEvent, ...]) -> None:
    for evt in events:
        logger.info(
            "ROUND_SERIALIZATION: triggered by %s (%s) — %d tools serialized in this round",
            evt.trigger_tool,
            evt.reason,
            )


def x__log_serialization_events__mutmut_9(events: tuple[SerializationEvent, ...]) -> None:
    for evt in events:
        logger.info(
            "XXROUND_SERIALIZATION: triggered by %s (%s) — %d tools serialized in this roundXX",
            evt.trigger_tool,
            evt.reason,
            evt.tools_count,
        )


def x__log_serialization_events__mutmut_10(events: tuple[SerializationEvent, ...]) -> None:
    for evt in events:
        logger.info(
            "round_serialization: triggered by %s (%s) — %d tools serialized in this round",
            evt.trigger_tool,
            evt.reason,
            evt.tools_count,
        )


def x__log_serialization_events__mutmut_11(events: tuple[SerializationEvent, ...]) -> None:
    for evt in events:
        logger.info(
            "ROUND_SERIALIZATION: TRIGGERED BY %S (%S) — %D TOOLS SERIALIZED IN THIS ROUND",
            evt.trigger_tool,
            evt.reason,
            evt.tools_count,
        )

mutants_x__log_serialization_events__mutmut['_mutmut_orig'] = x__log_serialization_events__mutmut_orig # type: ignore # mutmut generated
mutants_x__log_serialization_events__mutmut['x__log_serialization_events__mutmut_1'] = x__log_serialization_events__mutmut_1 # type: ignore # mutmut generated
mutants_x__log_serialization_events__mutmut['x__log_serialization_events__mutmut_2'] = x__log_serialization_events__mutmut_2 # type: ignore # mutmut generated
mutants_x__log_serialization_events__mutmut['x__log_serialization_events__mutmut_3'] = x__log_serialization_events__mutmut_3 # type: ignore # mutmut generated
mutants_x__log_serialization_events__mutmut['x__log_serialization_events__mutmut_4'] = x__log_serialization_events__mutmut_4 # type: ignore # mutmut generated
mutants_x__log_serialization_events__mutmut['x__log_serialization_events__mutmut_5'] = x__log_serialization_events__mutmut_5 # type: ignore # mutmut generated
mutants_x__log_serialization_events__mutmut['x__log_serialization_events__mutmut_6'] = x__log_serialization_events__mutmut_6 # type: ignore # mutmut generated
mutants_x__log_serialization_events__mutmut['x__log_serialization_events__mutmut_7'] = x__log_serialization_events__mutmut_7 # type: ignore # mutmut generated
mutants_x__log_serialization_events__mutmut['x__log_serialization_events__mutmut_8'] = x__log_serialization_events__mutmut_8 # type: ignore # mutmut generated
mutants_x__log_serialization_events__mutmut['x__log_serialization_events__mutmut_9'] = x__log_serialization_events__mutmut_9 # type: ignore # mutmut generated
mutants_x__log_serialization_events__mutmut['x__log_serialization_events__mutmut_10'] = x__log_serialization_events__mutmut_10 # type: ignore # mutmut generated
mutants_x__log_serialization_events__mutmut['x__log_serialization_events__mutmut_11'] = x__log_serialization_events__mutmut_11 # type: ignore # mutmut generated
mutants_x__build_forced_serial_plan__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x__build_forced_serial_plan__mutmut)
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


def x__build_forced_serial_plan__mutmut_orig(specs_ordered: list[ToolSpec]) -> ExecutionPlan:
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


def x__build_forced_serial_plan__mutmut_1(specs_ordered: list[ToolSpec]) -> ExecutionPlan:
    """One single-call sequential phase per call, in original order.

    Mirrors the previous is_side_effect()-driven downgrade's observable
    behavior: a serialization event fires (reason "forced_serial") whenever any
    call in the batch is a write, covering the whole batch's tools_count — not
    one event per call — since forcing serial only ever "prevents concurrency"
    that a write call could otherwise have raced against.
    """
    batches = None
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


def x__build_forced_serial_plan__mutmut_2(specs_ordered: list[ToolSpec]) -> ExecutionPlan:
    """One single-call sequential phase per call, in original order.

    Mirrors the previous is_side_effect()-driven downgrade's observable
    behavior: a serialization event fires (reason "forced_serial") whenever any
    call in the batch is a write, covering the whole batch's tools_count — not
    one event per call — since forcing serial only ever "prevents concurrency"
    that a write call could otherwise have raced against.
    """
    batches = tuple(
        None
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


def x__build_forced_serial_plan__mutmut_3(specs_ordered: list[ToolSpec]) -> ExecutionPlan:
    """One single-call sequential phase per call, in original order.

    Mirrors the previous is_side_effect()-driven downgrade's observable
    behavior: a serialization event fires (reason "forced_serial") whenever any
    call in the batch is a write, covering the whole batch's tools_count — not
    one event per call — since forcing serial only ever "prevents concurrency"
    that a write call could otherwise have raced against.
    """
    batches = tuple(
        ScheduledBatch(
            groups=None
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


def x__build_forced_serial_plan__mutmut_4(specs_ordered: list[ToolSpec]) -> ExecutionPlan:
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
                ScheduledGroup(calls=None, sequential=True, reason="forced_serial"),
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


def x__build_forced_serial_plan__mutmut_5(specs_ordered: list[ToolSpec]) -> ExecutionPlan:
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
                ScheduledGroup(calls=(spec,), sequential=None, reason="forced_serial"),
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


def x__build_forced_serial_plan__mutmut_6(specs_ordered: list[ToolSpec]) -> ExecutionPlan:
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
                ScheduledGroup(calls=(spec,), sequential=True, reason=None),
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


def x__build_forced_serial_plan__mutmut_7(specs_ordered: list[ToolSpec]) -> ExecutionPlan:
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
                ScheduledGroup(sequential=True, reason="forced_serial"),
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


def x__build_forced_serial_plan__mutmut_8(specs_ordered: list[ToolSpec]) -> ExecutionPlan:
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
                ScheduledGroup(calls=(spec,), reason="forced_serial"),
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


def x__build_forced_serial_plan__mutmut_9(specs_ordered: list[ToolSpec]) -> ExecutionPlan:
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
                ScheduledGroup(calls=(spec,), sequential=True, ),
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


def x__build_forced_serial_plan__mutmut_10(specs_ordered: list[ToolSpec]) -> ExecutionPlan:
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
                ScheduledGroup(calls=(spec,), sequential=False, reason="forced_serial"),
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


def x__build_forced_serial_plan__mutmut_11(specs_ordered: list[ToolSpec]) -> ExecutionPlan:
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
                ScheduledGroup(calls=(spec,), sequential=True, reason="XXforced_serialXX"),
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


def x__build_forced_serial_plan__mutmut_12(specs_ordered: list[ToolSpec]) -> ExecutionPlan:
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
                ScheduledGroup(calls=(spec,), sequential=True, reason="FORCED_SERIAL"),
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


def x__build_forced_serial_plan__mutmut_13(specs_ordered: list[ToolSpec]) -> ExecutionPlan:
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
    events: tuple[SerializationEvent, ...] = None
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


def x__build_forced_serial_plan__mutmut_14(specs_ordered: list[ToolSpec]) -> ExecutionPlan:
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
    write_specs = None
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


def x__build_forced_serial_plan__mutmut_15(specs_ordered: list[ToolSpec]) -> ExecutionPlan:
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
        trigger = None
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


def x__build_forced_serial_plan__mutmut_16(specs_ordered: list[ToolSpec]) -> ExecutionPlan:
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
        trigger = write_specs[1]
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


def x__build_forced_serial_plan__mutmut_17(specs_ordered: list[ToolSpec]) -> ExecutionPlan:
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
        events = None
    _log_serialization_events(events)
    return ExecutionPlan(batches=batches, serialization_events=events)


def x__build_forced_serial_plan__mutmut_18(specs_ordered: list[ToolSpec]) -> ExecutionPlan:
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
                trigger_tool=None,
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


def x__build_forced_serial_plan__mutmut_19(specs_ordered: list[ToolSpec]) -> ExecutionPlan:
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
                reason=None,
                tools_count=len(specs_ordered),
                resource_scopes=trigger.resource_scopes,
                is_write=True,
                requires_serial=False,
                scheduling_decision="forced_serial",
            ),
        )
    _log_serialization_events(events)
    return ExecutionPlan(batches=batches, serialization_events=events)


def x__build_forced_serial_plan__mutmut_20(specs_ordered: list[ToolSpec]) -> ExecutionPlan:
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
                tools_count=None,
                resource_scopes=trigger.resource_scopes,
                is_write=True,
                requires_serial=False,
                scheduling_decision="forced_serial",
            ),
        )
    _log_serialization_events(events)
    return ExecutionPlan(batches=batches, serialization_events=events)


def x__build_forced_serial_plan__mutmut_21(specs_ordered: list[ToolSpec]) -> ExecutionPlan:
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
                resource_scopes=None,
                is_write=True,
                requires_serial=False,
                scheduling_decision="forced_serial",
            ),
        )
    _log_serialization_events(events)
    return ExecutionPlan(batches=batches, serialization_events=events)


def x__build_forced_serial_plan__mutmut_22(specs_ordered: list[ToolSpec]) -> ExecutionPlan:
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
                is_write=None,
                requires_serial=False,
                scheduling_decision="forced_serial",
            ),
        )
    _log_serialization_events(events)
    return ExecutionPlan(batches=batches, serialization_events=events)


def x__build_forced_serial_plan__mutmut_23(specs_ordered: list[ToolSpec]) -> ExecutionPlan:
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
                requires_serial=None,
                scheduling_decision="forced_serial",
            ),
        )
    _log_serialization_events(events)
    return ExecutionPlan(batches=batches, serialization_events=events)


def x__build_forced_serial_plan__mutmut_24(specs_ordered: list[ToolSpec]) -> ExecutionPlan:
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
                scheduling_decision=None,
            ),
        )
    _log_serialization_events(events)
    return ExecutionPlan(batches=batches, serialization_events=events)


def x__build_forced_serial_plan__mutmut_25(specs_ordered: list[ToolSpec]) -> ExecutionPlan:
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


def x__build_forced_serial_plan__mutmut_26(specs_ordered: list[ToolSpec]) -> ExecutionPlan:
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
                tools_count=len(specs_ordered),
                resource_scopes=trigger.resource_scopes,
                is_write=True,
                requires_serial=False,
                scheduling_decision="forced_serial",
            ),
        )
    _log_serialization_events(events)
    return ExecutionPlan(batches=batches, serialization_events=events)


def x__build_forced_serial_plan__mutmut_27(specs_ordered: list[ToolSpec]) -> ExecutionPlan:
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
                resource_scopes=trigger.resource_scopes,
                is_write=True,
                requires_serial=False,
                scheduling_decision="forced_serial",
            ),
        )
    _log_serialization_events(events)
    return ExecutionPlan(batches=batches, serialization_events=events)


def x__build_forced_serial_plan__mutmut_28(specs_ordered: list[ToolSpec]) -> ExecutionPlan:
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
                is_write=True,
                requires_serial=False,
                scheduling_decision="forced_serial",
            ),
        )
    _log_serialization_events(events)
    return ExecutionPlan(batches=batches, serialization_events=events)


def x__build_forced_serial_plan__mutmut_29(specs_ordered: list[ToolSpec]) -> ExecutionPlan:
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
                requires_serial=False,
                scheduling_decision="forced_serial",
            ),
        )
    _log_serialization_events(events)
    return ExecutionPlan(batches=batches, serialization_events=events)


def x__build_forced_serial_plan__mutmut_30(specs_ordered: list[ToolSpec]) -> ExecutionPlan:
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
                scheduling_decision="forced_serial",
            ),
        )
    _log_serialization_events(events)
    return ExecutionPlan(batches=batches, serialization_events=events)


def x__build_forced_serial_plan__mutmut_31(specs_ordered: list[ToolSpec]) -> ExecutionPlan:
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
                ),
        )
    _log_serialization_events(events)
    return ExecutionPlan(batches=batches, serialization_events=events)


def x__build_forced_serial_plan__mutmut_32(specs_ordered: list[ToolSpec]) -> ExecutionPlan:
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
                reason="XXforced_serialXX",
                tools_count=len(specs_ordered),
                resource_scopes=trigger.resource_scopes,
                is_write=True,
                requires_serial=False,
                scheduling_decision="forced_serial",
            ),
        )
    _log_serialization_events(events)
    return ExecutionPlan(batches=batches, serialization_events=events)


def x__build_forced_serial_plan__mutmut_33(specs_ordered: list[ToolSpec]) -> ExecutionPlan:
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
                reason="FORCED_SERIAL",
                tools_count=len(specs_ordered),
                resource_scopes=trigger.resource_scopes,
                is_write=True,
                requires_serial=False,
                scheduling_decision="forced_serial",
            ),
        )
    _log_serialization_events(events)
    return ExecutionPlan(batches=batches, serialization_events=events)


def x__build_forced_serial_plan__mutmut_34(specs_ordered: list[ToolSpec]) -> ExecutionPlan:
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
                is_write=False,
                requires_serial=False,
                scheduling_decision="forced_serial",
            ),
        )
    _log_serialization_events(events)
    return ExecutionPlan(batches=batches, serialization_events=events)


def x__build_forced_serial_plan__mutmut_35(specs_ordered: list[ToolSpec]) -> ExecutionPlan:
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
                requires_serial=True,
                scheduling_decision="forced_serial",
            ),
        )
    _log_serialization_events(events)
    return ExecutionPlan(batches=batches, serialization_events=events)


def x__build_forced_serial_plan__mutmut_36(specs_ordered: list[ToolSpec]) -> ExecutionPlan:
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
                scheduling_decision="XXforced_serialXX",
            ),
        )
    _log_serialization_events(events)
    return ExecutionPlan(batches=batches, serialization_events=events)


def x__build_forced_serial_plan__mutmut_37(specs_ordered: list[ToolSpec]) -> ExecutionPlan:
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
                scheduling_decision="FORCED_SERIAL",
            ),
        )
    _log_serialization_events(events)
    return ExecutionPlan(batches=batches, serialization_events=events)


def x__build_forced_serial_plan__mutmut_38(specs_ordered: list[ToolSpec]) -> ExecutionPlan:
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
    _log_serialization_events(None)
    return ExecutionPlan(batches=batches, serialization_events=events)


def x__build_forced_serial_plan__mutmut_39(specs_ordered: list[ToolSpec]) -> ExecutionPlan:
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
    return ExecutionPlan(batches=None, serialization_events=events)


def x__build_forced_serial_plan__mutmut_40(specs_ordered: list[ToolSpec]) -> ExecutionPlan:
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
    return ExecutionPlan(batches=batches, serialization_events=None)


def x__build_forced_serial_plan__mutmut_41(specs_ordered: list[ToolSpec]) -> ExecutionPlan:
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
    return ExecutionPlan(serialization_events=events)


def x__build_forced_serial_plan__mutmut_42(specs_ordered: list[ToolSpec]) -> ExecutionPlan:
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
    return ExecutionPlan(batches=batches, )

mutants_x__build_forced_serial_plan__mutmut['_mutmut_orig'] = x__build_forced_serial_plan__mutmut_orig # type: ignore # mutmut generated
mutants_x__build_forced_serial_plan__mutmut['x__build_forced_serial_plan__mutmut_1'] = x__build_forced_serial_plan__mutmut_1 # type: ignore # mutmut generated
mutants_x__build_forced_serial_plan__mutmut['x__build_forced_serial_plan__mutmut_2'] = x__build_forced_serial_plan__mutmut_2 # type: ignore # mutmut generated
mutants_x__build_forced_serial_plan__mutmut['x__build_forced_serial_plan__mutmut_3'] = x__build_forced_serial_plan__mutmut_3 # type: ignore # mutmut generated
mutants_x__build_forced_serial_plan__mutmut['x__build_forced_serial_plan__mutmut_4'] = x__build_forced_serial_plan__mutmut_4 # type: ignore # mutmut generated
mutants_x__build_forced_serial_plan__mutmut['x__build_forced_serial_plan__mutmut_5'] = x__build_forced_serial_plan__mutmut_5 # type: ignore # mutmut generated
mutants_x__build_forced_serial_plan__mutmut['x__build_forced_serial_plan__mutmut_6'] = x__build_forced_serial_plan__mutmut_6 # type: ignore # mutmut generated
mutants_x__build_forced_serial_plan__mutmut['x__build_forced_serial_plan__mutmut_7'] = x__build_forced_serial_plan__mutmut_7 # type: ignore # mutmut generated
mutants_x__build_forced_serial_plan__mutmut['x__build_forced_serial_plan__mutmut_8'] = x__build_forced_serial_plan__mutmut_8 # type: ignore # mutmut generated
mutants_x__build_forced_serial_plan__mutmut['x__build_forced_serial_plan__mutmut_9'] = x__build_forced_serial_plan__mutmut_9 # type: ignore # mutmut generated
mutants_x__build_forced_serial_plan__mutmut['x__build_forced_serial_plan__mutmut_10'] = x__build_forced_serial_plan__mutmut_10 # type: ignore # mutmut generated
mutants_x__build_forced_serial_plan__mutmut['x__build_forced_serial_plan__mutmut_11'] = x__build_forced_serial_plan__mutmut_11 # type: ignore # mutmut generated
mutants_x__build_forced_serial_plan__mutmut['x__build_forced_serial_plan__mutmut_12'] = x__build_forced_serial_plan__mutmut_12 # type: ignore # mutmut generated
mutants_x__build_forced_serial_plan__mutmut['x__build_forced_serial_plan__mutmut_13'] = x__build_forced_serial_plan__mutmut_13 # type: ignore # mutmut generated
mutants_x__build_forced_serial_plan__mutmut['x__build_forced_serial_plan__mutmut_14'] = x__build_forced_serial_plan__mutmut_14 # type: ignore # mutmut generated
mutants_x__build_forced_serial_plan__mutmut['x__build_forced_serial_plan__mutmut_15'] = x__build_forced_serial_plan__mutmut_15 # type: ignore # mutmut generated
mutants_x__build_forced_serial_plan__mutmut['x__build_forced_serial_plan__mutmut_16'] = x__build_forced_serial_plan__mutmut_16 # type: ignore # mutmut generated
mutants_x__build_forced_serial_plan__mutmut['x__build_forced_serial_plan__mutmut_17'] = x__build_forced_serial_plan__mutmut_17 # type: ignore # mutmut generated
mutants_x__build_forced_serial_plan__mutmut['x__build_forced_serial_plan__mutmut_18'] = x__build_forced_serial_plan__mutmut_18 # type: ignore # mutmut generated
mutants_x__build_forced_serial_plan__mutmut['x__build_forced_serial_plan__mutmut_19'] = x__build_forced_serial_plan__mutmut_19 # type: ignore # mutmut generated
mutants_x__build_forced_serial_plan__mutmut['x__build_forced_serial_plan__mutmut_20'] = x__build_forced_serial_plan__mutmut_20 # type: ignore # mutmut generated
mutants_x__build_forced_serial_plan__mutmut['x__build_forced_serial_plan__mutmut_21'] = x__build_forced_serial_plan__mutmut_21 # type: ignore # mutmut generated
mutants_x__build_forced_serial_plan__mutmut['x__build_forced_serial_plan__mutmut_22'] = x__build_forced_serial_plan__mutmut_22 # type: ignore # mutmut generated
mutants_x__build_forced_serial_plan__mutmut['x__build_forced_serial_plan__mutmut_23'] = x__build_forced_serial_plan__mutmut_23 # type: ignore # mutmut generated
mutants_x__build_forced_serial_plan__mutmut['x__build_forced_serial_plan__mutmut_24'] = x__build_forced_serial_plan__mutmut_24 # type: ignore # mutmut generated
mutants_x__build_forced_serial_plan__mutmut['x__build_forced_serial_plan__mutmut_25'] = x__build_forced_serial_plan__mutmut_25 # type: ignore # mutmut generated
mutants_x__build_forced_serial_plan__mutmut['x__build_forced_serial_plan__mutmut_26'] = x__build_forced_serial_plan__mutmut_26 # type: ignore # mutmut generated
mutants_x__build_forced_serial_plan__mutmut['x__build_forced_serial_plan__mutmut_27'] = x__build_forced_serial_plan__mutmut_27 # type: ignore # mutmut generated
mutants_x__build_forced_serial_plan__mutmut['x__build_forced_serial_plan__mutmut_28'] = x__build_forced_serial_plan__mutmut_28 # type: ignore # mutmut generated
mutants_x__build_forced_serial_plan__mutmut['x__build_forced_serial_plan__mutmut_29'] = x__build_forced_serial_plan__mutmut_29 # type: ignore # mutmut generated
mutants_x__build_forced_serial_plan__mutmut['x__build_forced_serial_plan__mutmut_30'] = x__build_forced_serial_plan__mutmut_30 # type: ignore # mutmut generated
mutants_x__build_forced_serial_plan__mutmut['x__build_forced_serial_plan__mutmut_31'] = x__build_forced_serial_plan__mutmut_31 # type: ignore # mutmut generated
mutants_x__build_forced_serial_plan__mutmut['x__build_forced_serial_plan__mutmut_32'] = x__build_forced_serial_plan__mutmut_32 # type: ignore # mutmut generated
mutants_x__build_forced_serial_plan__mutmut['x__build_forced_serial_plan__mutmut_33'] = x__build_forced_serial_plan__mutmut_33 # type: ignore # mutmut generated
mutants_x__build_forced_serial_plan__mutmut['x__build_forced_serial_plan__mutmut_34'] = x__build_forced_serial_plan__mutmut_34 # type: ignore # mutmut generated
mutants_x__build_forced_serial_plan__mutmut['x__build_forced_serial_plan__mutmut_35'] = x__build_forced_serial_plan__mutmut_35 # type: ignore # mutmut generated
mutants_x__build_forced_serial_plan__mutmut['x__build_forced_serial_plan__mutmut_36'] = x__build_forced_serial_plan__mutmut_36 # type: ignore # mutmut generated
mutants_x__build_forced_serial_plan__mutmut['x__build_forced_serial_plan__mutmut_37'] = x__build_forced_serial_plan__mutmut_37 # type: ignore # mutmut generated
mutants_x__build_forced_serial_plan__mutmut['x__build_forced_serial_plan__mutmut_38'] = x__build_forced_serial_plan__mutmut_38 # type: ignore # mutmut generated
mutants_x__build_forced_serial_plan__mutmut['x__build_forced_serial_plan__mutmut_39'] = x__build_forced_serial_plan__mutmut_39 # type: ignore # mutmut generated
mutants_x__build_forced_serial_plan__mutmut['x__build_forced_serial_plan__mutmut_40'] = x__build_forced_serial_plan__mutmut_40 # type: ignore # mutmut generated
mutants_x__build_forced_serial_plan__mutmut['x__build_forced_serial_plan__mutmut_41'] = x__build_forced_serial_plan__mutmut_41 # type: ignore # mutmut generated
mutants_x__build_forced_serial_plan__mutmut['x__build_forced_serial_plan__mutmut_42'] = x__build_forced_serial_plan__mutmut_42 # type: ignore # mutmut generated
mutants_x_build_execution_groups__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x_build_execution_groups__mutmut)
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


def x_build_execution_groups__mutmut_orig(
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


def x_build_execution_groups__mutmut_1(
    tool_calls: list[dict],
    call_specs: dict[str, ToolSpec],  # call_id -> ToolSpec
    *,
    force_serial: bool = True,
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


def x_build_execution_groups__mutmut_2(
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
    specs_ordered: list[ToolSpec] = None
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


def x_build_execution_groups__mutmut_3(
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
        call_id = None
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


def x_build_execution_groups__mutmut_4(
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
        call_id = tc["XXidXX"]
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


def x_build_execution_groups__mutmut_5(
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
        call_id = tc["ID"]
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


def x_build_execution_groups__mutmut_6(
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
        spec = None
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


def x_build_execution_groups__mutmut_7(
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
        spec = call_specs.get(None)
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


def x_build_execution_groups__mutmut_8(
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
        if spec is not None:
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


def x_build_execution_groups__mutmut_9(
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
                None
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


def x_build_execution_groups__mutmut_10(
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
                f"No ToolSpec for call_id={call_id!r} (tool={tc['XXfunctionXX']['name']!r})"
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


def x_build_execution_groups__mutmut_11(
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
                f"No ToolSpec for call_id={call_id!r} (tool={tc['FUNCTION']['name']!r})"
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


def x_build_execution_groups__mutmut_12(
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
                f"No ToolSpec for call_id={call_id!r} (tool={tc['function']['XXnameXX']!r})"
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


def x_build_execution_groups__mutmut_13(
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
                f"No ToolSpec for call_id={call_id!r} (tool={tc['function']['NAME']!r})"
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


def x_build_execution_groups__mutmut_14(
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
        specs_ordered.append(None)

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


def x_build_execution_groups__mutmut_15(
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

    if specs_ordered:
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


def x_build_execution_groups__mutmut_16(
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
        return ExecutionPlan(batches=None, serialization_events=())

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


def x_build_execution_groups__mutmut_17(
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
        return ExecutionPlan(batches=(), serialization_events=None)

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


def x_build_execution_groups__mutmut_18(
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
        return ExecutionPlan(serialization_events=())

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


def x_build_execution_groups__mutmut_19(
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
        return ExecutionPlan(batches=(), )

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


def x_build_execution_groups__mutmut_20(
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
        return _build_forced_serial_plan(None)

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


def x_build_execution_groups__mutmut_21(
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

    batches: list[ScheduledBatch] = None
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


def x_build_execution_groups__mutmut_22(
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
    events_list: list[SerializationEvent] = None
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


def x_build_execution_groups__mutmut_23(
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
    current_phase: list[ToolSpec] = None
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


def x_build_execution_groups__mutmut_24(
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
        if spec.requires_serial:
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


def x_build_execution_groups__mutmut_25(
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
            current_phase.append(None)
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


def x_build_execution_groups__mutmut_26(
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
            break
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


def x_build_execution_groups__mutmut_27(
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
            batch, phase_events = None
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


def x_build_execution_groups__mutmut_28(
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
            batch, phase_events = _build_phase_batch(None)
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


def x_build_execution_groups__mutmut_29(
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
            batches.append(None)
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


def x_build_execution_groups__mutmut_30(
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
            events_list.extend(None)
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


def x_build_execution_groups__mutmut_31(
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
            current_phase = None
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


def x_build_execution_groups__mutmut_32(
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
            None
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


def x_build_execution_groups__mutmut_33(
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
                groups=None
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


def x_build_execution_groups__mutmut_34(
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
                        calls=None, sequential=True, reason="requires_serial"
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


def x_build_execution_groups__mutmut_35(
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
                        calls=(spec,), sequential=None, reason="requires_serial"
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


def x_build_execution_groups__mutmut_36(
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
                        calls=(spec,), sequential=True, reason=None
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


def x_build_execution_groups__mutmut_37(
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
                        sequential=True, reason="requires_serial"
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


def x_build_execution_groups__mutmut_38(
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
                        calls=(spec,), reason="requires_serial"
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


def x_build_execution_groups__mutmut_39(
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
                        calls=(spec,), sequential=True, ),
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


def x_build_execution_groups__mutmut_40(
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
                        calls=(spec,), sequential=False, reason="requires_serial"
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


def x_build_execution_groups__mutmut_41(
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
                        calls=(spec,), sequential=True, reason="XXrequires_serialXX"
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


def x_build_execution_groups__mutmut_42(
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
                        calls=(spec,), sequential=True, reason="REQUIRES_SERIAL"
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


def x_build_execution_groups__mutmut_43(
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
            None
        )
    if current_phase:
        batch, phase_events = _build_phase_batch(current_phase)
        batches.append(batch)
        events_list.extend(phase_events)

    events = tuple(events_list)
    _log_serialization_events(events)
    return ExecutionPlan(batches=tuple(batches), serialization_events=events)


def x_build_execution_groups__mutmut_44(
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
                trigger_tool=None,
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


def x_build_execution_groups__mutmut_45(
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
                reason=None,
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


def x_build_execution_groups__mutmut_46(
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
                tools_count=None,
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


def x_build_execution_groups__mutmut_47(
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
                resource_scopes=None,
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


def x_build_execution_groups__mutmut_48(
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
                is_write=None,
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


def x_build_execution_groups__mutmut_49(
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
                requires_serial=None,
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


def x_build_execution_groups__mutmut_50(
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
                scheduling_decision=None,
            )
        )
    if current_phase:
        batch, phase_events = _build_phase_batch(current_phase)
        batches.append(batch)
        events_list.extend(phase_events)

    events = tuple(events_list)
    _log_serialization_events(events)
    return ExecutionPlan(batches=tuple(batches), serialization_events=events)


def x_build_execution_groups__mutmut_51(
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


def x_build_execution_groups__mutmut_52(
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


def x_build_execution_groups__mutmut_53(
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


def x_build_execution_groups__mutmut_54(
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


def x_build_execution_groups__mutmut_55(
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


def x_build_execution_groups__mutmut_56(
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


def x_build_execution_groups__mutmut_57(
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
                )
        )
    if current_phase:
        batch, phase_events = _build_phase_batch(current_phase)
        batches.append(batch)
        events_list.extend(phase_events)

    events = tuple(events_list)
    _log_serialization_events(events)
    return ExecutionPlan(batches=tuple(batches), serialization_events=events)


def x_build_execution_groups__mutmut_58(
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
                reason="XXrequires_serialXX",
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


def x_build_execution_groups__mutmut_59(
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
                reason="REQUIRES_SERIAL",
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


def x_build_execution_groups__mutmut_60(
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
                tools_count=2,
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


def x_build_execution_groups__mutmut_61(
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
                requires_serial=False,
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


def x_build_execution_groups__mutmut_62(
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
                scheduling_decision="XXserial_barrierXX",
            )
        )
    if current_phase:
        batch, phase_events = _build_phase_batch(current_phase)
        batches.append(batch)
        events_list.extend(phase_events)

    events = tuple(events_list)
    _log_serialization_events(events)
    return ExecutionPlan(batches=tuple(batches), serialization_events=events)


def x_build_execution_groups__mutmut_63(
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
                scheduling_decision="SERIAL_BARRIER",
            )
        )
    if current_phase:
        batch, phase_events = _build_phase_batch(current_phase)
        batches.append(batch)
        events_list.extend(phase_events)

    events = tuple(events_list)
    _log_serialization_events(events)
    return ExecutionPlan(batches=tuple(batches), serialization_events=events)


def x_build_execution_groups__mutmut_64(
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
        batch, phase_events = None
        batches.append(batch)
        events_list.extend(phase_events)

    events = tuple(events_list)
    _log_serialization_events(events)
    return ExecutionPlan(batches=tuple(batches), serialization_events=events)


def x_build_execution_groups__mutmut_65(
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
        batch, phase_events = _build_phase_batch(None)
        batches.append(batch)
        events_list.extend(phase_events)

    events = tuple(events_list)
    _log_serialization_events(events)
    return ExecutionPlan(batches=tuple(batches), serialization_events=events)


def x_build_execution_groups__mutmut_66(
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
        batches.append(None)
        events_list.extend(phase_events)

    events = tuple(events_list)
    _log_serialization_events(events)
    return ExecutionPlan(batches=tuple(batches), serialization_events=events)


def x_build_execution_groups__mutmut_67(
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
        events_list.extend(None)

    events = tuple(events_list)
    _log_serialization_events(events)
    return ExecutionPlan(batches=tuple(batches), serialization_events=events)


def x_build_execution_groups__mutmut_68(
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

    events = None
    _log_serialization_events(events)
    return ExecutionPlan(batches=tuple(batches), serialization_events=events)


def x_build_execution_groups__mutmut_69(
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

    events = tuple(None)
    _log_serialization_events(events)
    return ExecutionPlan(batches=tuple(batches), serialization_events=events)


def x_build_execution_groups__mutmut_70(
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
    _log_serialization_events(None)
    return ExecutionPlan(batches=tuple(batches), serialization_events=events)


def x_build_execution_groups__mutmut_71(
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
    return ExecutionPlan(batches=None, serialization_events=events)


def x_build_execution_groups__mutmut_72(
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
    return ExecutionPlan(batches=tuple(batches), serialization_events=None)


def x_build_execution_groups__mutmut_73(
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
    return ExecutionPlan(serialization_events=events)


def x_build_execution_groups__mutmut_74(
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
    return ExecutionPlan(batches=tuple(batches), )


def x_build_execution_groups__mutmut_75(
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
    return ExecutionPlan(batches=tuple(None), serialization_events=events)

mutants_x_build_execution_groups__mutmut['_mutmut_orig'] = x_build_execution_groups__mutmut_orig # type: ignore # mutmut generated
mutants_x_build_execution_groups__mutmut['x_build_execution_groups__mutmut_1'] = x_build_execution_groups__mutmut_1 # type: ignore # mutmut generated
mutants_x_build_execution_groups__mutmut['x_build_execution_groups__mutmut_2'] = x_build_execution_groups__mutmut_2 # type: ignore # mutmut generated
mutants_x_build_execution_groups__mutmut['x_build_execution_groups__mutmut_3'] = x_build_execution_groups__mutmut_3 # type: ignore # mutmut generated
mutants_x_build_execution_groups__mutmut['x_build_execution_groups__mutmut_4'] = x_build_execution_groups__mutmut_4 # type: ignore # mutmut generated
mutants_x_build_execution_groups__mutmut['x_build_execution_groups__mutmut_5'] = x_build_execution_groups__mutmut_5 # type: ignore # mutmut generated
mutants_x_build_execution_groups__mutmut['x_build_execution_groups__mutmut_6'] = x_build_execution_groups__mutmut_6 # type: ignore # mutmut generated
mutants_x_build_execution_groups__mutmut['x_build_execution_groups__mutmut_7'] = x_build_execution_groups__mutmut_7 # type: ignore # mutmut generated
mutants_x_build_execution_groups__mutmut['x_build_execution_groups__mutmut_8'] = x_build_execution_groups__mutmut_8 # type: ignore # mutmut generated
mutants_x_build_execution_groups__mutmut['x_build_execution_groups__mutmut_9'] = x_build_execution_groups__mutmut_9 # type: ignore # mutmut generated
mutants_x_build_execution_groups__mutmut['x_build_execution_groups__mutmut_10'] = x_build_execution_groups__mutmut_10 # type: ignore # mutmut generated
mutants_x_build_execution_groups__mutmut['x_build_execution_groups__mutmut_11'] = x_build_execution_groups__mutmut_11 # type: ignore # mutmut generated
mutants_x_build_execution_groups__mutmut['x_build_execution_groups__mutmut_12'] = x_build_execution_groups__mutmut_12 # type: ignore # mutmut generated
mutants_x_build_execution_groups__mutmut['x_build_execution_groups__mutmut_13'] = x_build_execution_groups__mutmut_13 # type: ignore # mutmut generated
mutants_x_build_execution_groups__mutmut['x_build_execution_groups__mutmut_14'] = x_build_execution_groups__mutmut_14 # type: ignore # mutmut generated
mutants_x_build_execution_groups__mutmut['x_build_execution_groups__mutmut_15'] = x_build_execution_groups__mutmut_15 # type: ignore # mutmut generated
mutants_x_build_execution_groups__mutmut['x_build_execution_groups__mutmut_16'] = x_build_execution_groups__mutmut_16 # type: ignore # mutmut generated
mutants_x_build_execution_groups__mutmut['x_build_execution_groups__mutmut_17'] = x_build_execution_groups__mutmut_17 # type: ignore # mutmut generated
mutants_x_build_execution_groups__mutmut['x_build_execution_groups__mutmut_18'] = x_build_execution_groups__mutmut_18 # type: ignore # mutmut generated
mutants_x_build_execution_groups__mutmut['x_build_execution_groups__mutmut_19'] = x_build_execution_groups__mutmut_19 # type: ignore # mutmut generated
mutants_x_build_execution_groups__mutmut['x_build_execution_groups__mutmut_20'] = x_build_execution_groups__mutmut_20 # type: ignore # mutmut generated
mutants_x_build_execution_groups__mutmut['x_build_execution_groups__mutmut_21'] = x_build_execution_groups__mutmut_21 # type: ignore # mutmut generated
mutants_x_build_execution_groups__mutmut['x_build_execution_groups__mutmut_22'] = x_build_execution_groups__mutmut_22 # type: ignore # mutmut generated
mutants_x_build_execution_groups__mutmut['x_build_execution_groups__mutmut_23'] = x_build_execution_groups__mutmut_23 # type: ignore # mutmut generated
mutants_x_build_execution_groups__mutmut['x_build_execution_groups__mutmut_24'] = x_build_execution_groups__mutmut_24 # type: ignore # mutmut generated
mutants_x_build_execution_groups__mutmut['x_build_execution_groups__mutmut_25'] = x_build_execution_groups__mutmut_25 # type: ignore # mutmut generated
mutants_x_build_execution_groups__mutmut['x_build_execution_groups__mutmut_26'] = x_build_execution_groups__mutmut_26 # type: ignore # mutmut generated
mutants_x_build_execution_groups__mutmut['x_build_execution_groups__mutmut_27'] = x_build_execution_groups__mutmut_27 # type: ignore # mutmut generated
mutants_x_build_execution_groups__mutmut['x_build_execution_groups__mutmut_28'] = x_build_execution_groups__mutmut_28 # type: ignore # mutmut generated
mutants_x_build_execution_groups__mutmut['x_build_execution_groups__mutmut_29'] = x_build_execution_groups__mutmut_29 # type: ignore # mutmut generated
mutants_x_build_execution_groups__mutmut['x_build_execution_groups__mutmut_30'] = x_build_execution_groups__mutmut_30 # type: ignore # mutmut generated
mutants_x_build_execution_groups__mutmut['x_build_execution_groups__mutmut_31'] = x_build_execution_groups__mutmut_31 # type: ignore # mutmut generated
mutants_x_build_execution_groups__mutmut['x_build_execution_groups__mutmut_32'] = x_build_execution_groups__mutmut_32 # type: ignore # mutmut generated
mutants_x_build_execution_groups__mutmut['x_build_execution_groups__mutmut_33'] = x_build_execution_groups__mutmut_33 # type: ignore # mutmut generated
mutants_x_build_execution_groups__mutmut['x_build_execution_groups__mutmut_34'] = x_build_execution_groups__mutmut_34 # type: ignore # mutmut generated
mutants_x_build_execution_groups__mutmut['x_build_execution_groups__mutmut_35'] = x_build_execution_groups__mutmut_35 # type: ignore # mutmut generated
mutants_x_build_execution_groups__mutmut['x_build_execution_groups__mutmut_36'] = x_build_execution_groups__mutmut_36 # type: ignore # mutmut generated
mutants_x_build_execution_groups__mutmut['x_build_execution_groups__mutmut_37'] = x_build_execution_groups__mutmut_37 # type: ignore # mutmut generated
mutants_x_build_execution_groups__mutmut['x_build_execution_groups__mutmut_38'] = x_build_execution_groups__mutmut_38 # type: ignore # mutmut generated
mutants_x_build_execution_groups__mutmut['x_build_execution_groups__mutmut_39'] = x_build_execution_groups__mutmut_39 # type: ignore # mutmut generated
mutants_x_build_execution_groups__mutmut['x_build_execution_groups__mutmut_40'] = x_build_execution_groups__mutmut_40 # type: ignore # mutmut generated
mutants_x_build_execution_groups__mutmut['x_build_execution_groups__mutmut_41'] = x_build_execution_groups__mutmut_41 # type: ignore # mutmut generated
mutants_x_build_execution_groups__mutmut['x_build_execution_groups__mutmut_42'] = x_build_execution_groups__mutmut_42 # type: ignore # mutmut generated
mutants_x_build_execution_groups__mutmut['x_build_execution_groups__mutmut_43'] = x_build_execution_groups__mutmut_43 # type: ignore # mutmut generated
mutants_x_build_execution_groups__mutmut['x_build_execution_groups__mutmut_44'] = x_build_execution_groups__mutmut_44 # type: ignore # mutmut generated
mutants_x_build_execution_groups__mutmut['x_build_execution_groups__mutmut_45'] = x_build_execution_groups__mutmut_45 # type: ignore # mutmut generated
mutants_x_build_execution_groups__mutmut['x_build_execution_groups__mutmut_46'] = x_build_execution_groups__mutmut_46 # type: ignore # mutmut generated
mutants_x_build_execution_groups__mutmut['x_build_execution_groups__mutmut_47'] = x_build_execution_groups__mutmut_47 # type: ignore # mutmut generated
mutants_x_build_execution_groups__mutmut['x_build_execution_groups__mutmut_48'] = x_build_execution_groups__mutmut_48 # type: ignore # mutmut generated
mutants_x_build_execution_groups__mutmut['x_build_execution_groups__mutmut_49'] = x_build_execution_groups__mutmut_49 # type: ignore # mutmut generated
mutants_x_build_execution_groups__mutmut['x_build_execution_groups__mutmut_50'] = x_build_execution_groups__mutmut_50 # type: ignore # mutmut generated
mutants_x_build_execution_groups__mutmut['x_build_execution_groups__mutmut_51'] = x_build_execution_groups__mutmut_51 # type: ignore # mutmut generated
mutants_x_build_execution_groups__mutmut['x_build_execution_groups__mutmut_52'] = x_build_execution_groups__mutmut_52 # type: ignore # mutmut generated
mutants_x_build_execution_groups__mutmut['x_build_execution_groups__mutmut_53'] = x_build_execution_groups__mutmut_53 # type: ignore # mutmut generated
mutants_x_build_execution_groups__mutmut['x_build_execution_groups__mutmut_54'] = x_build_execution_groups__mutmut_54 # type: ignore # mutmut generated
mutants_x_build_execution_groups__mutmut['x_build_execution_groups__mutmut_55'] = x_build_execution_groups__mutmut_55 # type: ignore # mutmut generated
mutants_x_build_execution_groups__mutmut['x_build_execution_groups__mutmut_56'] = x_build_execution_groups__mutmut_56 # type: ignore # mutmut generated
mutants_x_build_execution_groups__mutmut['x_build_execution_groups__mutmut_57'] = x_build_execution_groups__mutmut_57 # type: ignore # mutmut generated
mutants_x_build_execution_groups__mutmut['x_build_execution_groups__mutmut_58'] = x_build_execution_groups__mutmut_58 # type: ignore # mutmut generated
mutants_x_build_execution_groups__mutmut['x_build_execution_groups__mutmut_59'] = x_build_execution_groups__mutmut_59 # type: ignore # mutmut generated
mutants_x_build_execution_groups__mutmut['x_build_execution_groups__mutmut_60'] = x_build_execution_groups__mutmut_60 # type: ignore # mutmut generated
mutants_x_build_execution_groups__mutmut['x_build_execution_groups__mutmut_61'] = x_build_execution_groups__mutmut_61 # type: ignore # mutmut generated
mutants_x_build_execution_groups__mutmut['x_build_execution_groups__mutmut_62'] = x_build_execution_groups__mutmut_62 # type: ignore # mutmut generated
mutants_x_build_execution_groups__mutmut['x_build_execution_groups__mutmut_63'] = x_build_execution_groups__mutmut_63 # type: ignore # mutmut generated
mutants_x_build_execution_groups__mutmut['x_build_execution_groups__mutmut_64'] = x_build_execution_groups__mutmut_64 # type: ignore # mutmut generated
mutants_x_build_execution_groups__mutmut['x_build_execution_groups__mutmut_65'] = x_build_execution_groups__mutmut_65 # type: ignore # mutmut generated
mutants_x_build_execution_groups__mutmut['x_build_execution_groups__mutmut_66'] = x_build_execution_groups__mutmut_66 # type: ignore # mutmut generated
mutants_x_build_execution_groups__mutmut['x_build_execution_groups__mutmut_67'] = x_build_execution_groups__mutmut_67 # type: ignore # mutmut generated
mutants_x_build_execution_groups__mutmut['x_build_execution_groups__mutmut_68'] = x_build_execution_groups__mutmut_68 # type: ignore # mutmut generated
mutants_x_build_execution_groups__mutmut['x_build_execution_groups__mutmut_69'] = x_build_execution_groups__mutmut_69 # type: ignore # mutmut generated
mutants_x_build_execution_groups__mutmut['x_build_execution_groups__mutmut_70'] = x_build_execution_groups__mutmut_70 # type: ignore # mutmut generated
mutants_x_build_execution_groups__mutmut['x_build_execution_groups__mutmut_71'] = x_build_execution_groups__mutmut_71 # type: ignore # mutmut generated
mutants_x_build_execution_groups__mutmut['x_build_execution_groups__mutmut_72'] = x_build_execution_groups__mutmut_72 # type: ignore # mutmut generated
mutants_x_build_execution_groups__mutmut['x_build_execution_groups__mutmut_73'] = x_build_execution_groups__mutmut_73 # type: ignore # mutmut generated
mutants_x_build_execution_groups__mutmut['x_build_execution_groups__mutmut_74'] = x_build_execution_groups__mutmut_74 # type: ignore # mutmut generated
mutants_x_build_execution_groups__mutmut['x_build_execution_groups__mutmut_75'] = x_build_execution_groups__mutmut_75 # type: ignore # mutmut generated
