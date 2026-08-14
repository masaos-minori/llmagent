"""tests/test_tool_scheduler_serialization.py
Unit tests for ScheduledGroup.sequential and SerializationEvent fields/reason codes.
"""

from __future__ import annotations

from agent.tool_scheduler import build_execution_groups
from shared.tool_spec import ToolSpec


def _tc(name: str, call_id: str | None = None) -> dict:
    return {
        "function": {"name": name, "arguments": "{}"},
        "id": call_id or f"call_{name}",
    }


def _spec(
    tc: dict,
    *,
    scopes: tuple[str, ...] = (),
    is_write: bool = False,
    requires_serial: bool = False,
) -> ToolSpec:
    return ToolSpec(
        call_id=tc["id"],
        name=tc["function"]["name"],
        resource_scopes=scopes,
        is_write=is_write,
        requires_serial=requires_serial,
    )


# ── ScheduledGroup.sequential ─────────────────────────────────────────────────


class TestScheduledGroupSequential:
    def test_same_scope_write_group_is_sequential(self) -> None:
        tc_a, tc_b = _tc("write_a"), _tc("write_b")
        specs = {
            tc_a["id"]: _spec(tc_a, scopes=("file:/foo",), is_write=True),
            tc_b["id"]: _spec(tc_b, scopes=("file:/foo",), is_write=True),
        }
        plan = build_execution_groups([tc_a, tc_b], specs)
        group = plan.batches[0].groups[0]
        assert group.sequential is True

    def test_read_only_group_is_not_sequential(self) -> None:
        tc_a, tc_b = _tc("read_a"), _tc("read_b")
        specs = {tc_a["id"]: _spec(tc_a), tc_b["id"]: _spec(tc_b)}
        plan = build_execution_groups([tc_a, tc_b], specs)
        group = plan.batches[0].groups[0]
        assert group.sequential is False

    def test_scope_write_sequential_and_read_concurrent_in_same_batch(self) -> None:
        tc_a = _tc("write_a")
        tc_b = _tc("write_b")
        tc_c = _tc("read_c")
        specs = {
            tc_a["id"]: _spec(tc_a, scopes=("repo:X",), is_write=True),
            tc_b["id"]: _spec(tc_b, scopes=("repo:X",), is_write=True),
            tc_c["id"]: _spec(tc_c),
        }
        plan = build_execution_groups([tc_a, tc_b, tc_c], specs)
        batch = plan.batches[0]
        assert len(batch.groups) == 2
        write_group = next(g for g in batch.groups if g.sequential)
        assert {c.call_id for c in write_group.calls} == {tc_a["id"], tc_b["id"]}
        read_group = next(g for g in batch.groups if not g.sequential)
        assert {c.call_id for c in read_group.calls} == {tc_c["id"]}

    def test_different_scope_writes_each_form_their_own_sequential_group(self) -> None:
        tc_a, tc_b = _tc("write_a"), _tc("write_b")
        specs = {
            tc_a["id"]: _spec(tc_a, scopes=("repo:A",), is_write=True),
            tc_b["id"]: _spec(tc_b, scopes=("repo:B",), is_write=True),
        }
        plan = build_execution_groups([tc_a, tc_b], specs)
        batch = plan.batches[0]
        # Neither writer conflicts with the other (different scopes); each is
        # a singleton, pooled together into one concurrent group.
        assert len(batch.groups) == 1
        assert batch.groups[0].sequential is False

    def test_serial_barrier_batch_group_is_sequential(self) -> None:
        tc = _tc("shell_run")
        specs = {tc["id"]: _spec(tc, requires_serial=True)}
        plan = build_execution_groups([tc], specs)
        group = plan.batches[0].groups[0]
        assert group.sequential is True

    def test_scopeless_writes_form_sequential_group_via_global_write(self) -> None:
        tc_x, tc_y = _tc("write_x"), _tc("write_y")
        specs = {
            tc_x["id"]: _spec(tc_x, is_write=True),  # no scope
            tc_y["id"]: _spec(tc_y, is_write=True),  # no scope
        }
        plan = build_execution_groups([tc_x, tc_y], specs)
        group = plan.batches[0].groups[0]
        assert group.sequential is True

    def test_empty_input_has_empty_batches(self) -> None:
        plan = build_execution_groups([], {})
        assert plan.batches == ()


# ── SerializationEvent fields and reason codes ────────────────────────────────


class TestSerializationEventFields:
    def test_requires_serial_event_tracks_real_is_write_true(self) -> None:
        tc = _tc("shell_run")
        specs = {tc["id"]: _spec(tc, requires_serial=True, is_write=True)}
        plan = build_execution_groups([tc], specs)
        evt = next(
            e for e in plan.serialization_events if e.reason == "requires_serial"
        )
        assert evt.requires_serial is True
        assert evt.is_write is True
        assert evt.resource_scopes == ()
        assert evt.scheduling_decision == "serial_barrier"

    def test_requires_serial_event_tracks_real_is_write_false(self) -> None:
        """Regression: is_write must reflect the triggering call's actual
        metadata, not a hard-coded True regardless of the real spec."""
        tc = _tc("shell_run")
        specs = {tc["id"]: _spec(tc, requires_serial=True, is_write=False)}
        plan = build_execution_groups([tc], specs)
        evt = next(
            e for e in plan.serialization_events if e.reason == "requires_serial"
        )
        assert evt.requires_serial is True
        assert evt.is_write is False

    def test_resource_write_write_conflict_event_fields(self) -> None:
        tc_a, tc_b = _tc("write_a"), _tc("write_b")
        specs = {
            tc_a["id"]: _spec(tc_a, scopes=("file:/foo",), is_write=True),
            tc_b["id"]: _spec(tc_b, scopes=("file:/foo",), is_write=True),
        }
        plan = build_execution_groups([tc_a, tc_b], specs)
        evt = next(
            e
            for e in plan.serialization_events
            if e.reason == "resource_write_write_conflict"
        )
        assert evt.resource_scopes == ("file:/foo",)
        assert evt.is_write is True
        assert evt.requires_serial is False
        assert evt.scheduling_decision == "resource_scope"

    def test_resource_read_write_conflict_event_fields(self) -> None:
        tc_write, tc_read = _tc("write_a"), _tc("read_b")
        specs = {
            tc_write["id"]: _spec(tc_write, scopes=("file:/foo",), is_write=True),
            tc_read["id"]: _spec(tc_read, scopes=("file:/foo",)),
        }
        plan = build_execution_groups([tc_write, tc_read], specs)
        evt = next(
            e
            for e in plan.serialization_events
            if e.reason == "resource_read_write_conflict"
        )
        assert evt.resource_scopes == ("file:/foo",)
        assert evt.is_write is True
        assert evt.scheduling_decision == "resource_scope"

    def test_global_write_scope_event_fields(self) -> None:
        tc_x, tc_y = _tc("write_x"), _tc("write_y")
        specs = {
            tc_x["id"]: _spec(tc_x, is_write=True),
            tc_y["id"]: _spec(tc_y, is_write=True),
        }
        plan = build_execution_groups([tc_x, tc_y], specs)
        evt = next(
            e for e in plan.serialization_events if e.reason == "global_write_scope"
        )
        assert evt.resource_scopes == ("global:write",)
        assert evt.is_write is True
        assert evt.scheduling_decision == "resource_scope"

    def test_forced_serial_event_fields(self) -> None:
        tc_write, tc_read = _tc("write_a"), _tc("read_b")
        specs = {
            tc_write["id"]: _spec(tc_write, is_write=True),
            tc_read["id"]: _spec(tc_read),
        }
        plan = build_execution_groups([tc_write, tc_read], specs, force_serial=True)
        evt = next(e for e in plan.serialization_events if e.reason == "forced_serial")
        assert evt.is_write is True
        assert evt.tools_count == 2
        assert evt.scheduling_decision == "forced_serial"

    def test_forced_serial_with_only_reads_emits_no_event(self) -> None:
        """force_serial on a batch with no write call prevents no concurrency
        a write could have raced against, so no event fires."""
        tc = _tc("read_only")
        specs = {tc["id"]: _spec(tc)}
        plan = build_execution_groups([tc], specs, force_serial=True)
        assert plan.serialization_events == ()

    def test_resource_scope_event_union_multi_scope(self) -> None:
        """A move_file-style dual-scope call's event carries the union of all
        scopes observed across the connected component, not just one side."""
        tc_move = _tc("move_file")
        tc_other = _tc("write_other")
        specs = {
            tc_move["id"]: _spec(
                tc_move, scopes=("filesystem:/a", "filesystem:/b"), is_write=True
            ),
            tc_other["id"]: _spec(tc_other, scopes=("filesystem:/a",), is_write=True),
        }
        plan = build_execution_groups([tc_move, tc_other], specs)
        evt = next(
            e
            for e in plan.serialization_events
            if e.reason == "resource_write_write_conflict"
        )
        assert set(evt.resource_scopes) == {"filesystem:/a", "filesystem:/b"}

    def test_read_only_produces_no_serialization_events(self) -> None:
        tc_a, tc_b = _tc("read_a"), _tc("read_b")
        specs = {tc_a["id"]: _spec(tc_a), tc_b["id"]: _spec(tc_b)}
        plan = build_execution_groups([tc_a, tc_b], specs)
        assert plan.serialization_events == ()

    def test_distinct_non_overlapping_scopes_produce_no_serialization_events(
        self,
    ) -> None:
        """No global:write fallback triggered, no barrier, no scope overlap —
        every call is an unconflicted singleton, so zero events fire."""
        tc_a, tc_b = _tc("write_a"), _tc("write_b")
        specs = {
            tc_a["id"]: _spec(tc_a, scopes=("repo:A",), is_write=True),
            tc_b["id"]: _spec(tc_b, scopes=("repo:B",), is_write=True),
        }
        plan = build_execution_groups([tc_a, tc_b], specs)
        assert plan.serialization_events == ()

    def test_serialization_event_tools_count(self) -> None:
        tc_a, tc_b, tc_c = _tc("write_a"), _tc("write_b"), _tc("write_c")
        specs = {
            tc_a["id"]: _spec(tc_a, scopes=("s",), is_write=True),
            tc_b["id"]: _spec(tc_b, scopes=("s",), is_write=True),
            tc_c["id"]: _spec(tc_c, scopes=("s",), is_write=True),
        }
        plan = build_execution_groups([tc_a, tc_b, tc_c], specs)
        evt = next(
            e
            for e in plan.serialization_events
            if e.reason == "resource_write_write_conflict"
        )
        assert evt.tools_count == 3
