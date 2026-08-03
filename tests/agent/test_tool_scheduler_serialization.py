"""tests/test_tool_scheduler_serialization.py
Unit tests for ScheduledBatch.serialize_flags and _SerializationEvent new fields.
"""

from __future__ import annotations

from agent.tool_scheduler import build_execution_groups
from shared.tool_spec import ToolSpec


def _tc(name: str) -> dict:
    return {"function": {"name": name, "arguments": "{}"}, "id": f"call_{name}"}


def _spec(
    name: str, *, scope: str = "", is_write: bool = False, requires_serial: bool = False
) -> ToolSpec:
    return ToolSpec(
        call_id="",
        name=name,
        resource_scope=scope,
        is_write=is_write,
        requires_serial=requires_serial,
    )


# ── serialize_flags ────────────────────────────────────────────────────────────


class TestSerializeFlags:
    def test_same_scope_write_group_has_serialize_true(self) -> None:
        tcs = [_tc("write_a"), _tc("write_b")]
        meta = {
            "write_a": _spec("write_a", scope="file:/foo", is_write=True),
            "write_b": _spec("write_b", scope="file:/foo", is_write=True),
        }
        _groups, md = build_execution_groups(tcs, meta)
        # The last concurrent batch contains the scope group
        scope_batch = md.concurrent_groups[-1]
        # write_a and write_b share one group in the batch
        assert len(scope_batch.groups) == 1
        assert scope_batch.serialize_flags[0] is True

    def test_read_only_group_has_serialize_false(self) -> None:
        tcs = [_tc("read_a"), _tc("read_b")]
        meta = {
            "read_a": _spec("read_a"),
            "read_b": _spec("read_b"),
        }
        _groups, md = build_execution_groups(tcs, meta)
        read_batch = md.concurrent_groups[-1]
        assert all(flag is False for flag in read_batch.serialize_flags)

    def test_scope_write_serialize_true_read_serialize_false_in_same_batch(
        self,
    ) -> None:
        tcs = [_tc("write_a"), _tc("write_b"), _tc("read_c")]
        meta = {
            "write_a": _spec("write_a", scope="repo:X", is_write=True),
            "write_b": _spec("write_b", scope="repo:X", is_write=True),
            "read_c": _spec("read_c"),
        }
        _groups, md = build_execution_groups(tcs, meta)
        # One concurrent batch with scope group + parallel group
        last_batch = md.concurrent_groups[-1]
        assert len(last_batch.groups) == 2
        # First group: scope writes — serialize=True
        assert last_batch.serialize_flags[0] is True
        # Second group: reads — serialize=False
        assert last_batch.serialize_flags[1] is False

    def test_different_scope_writes_in_same_batch_each_serialized(self) -> None:
        tcs = [_tc("write_a"), _tc("write_b")]
        meta = {
            "write_a": _spec("write_a", scope="repo:A", is_write=True),
            "write_b": _spec("write_b", scope="repo:B", is_write=True),
        }
        _groups, md = build_execution_groups(tcs, meta)
        last_batch = md.concurrent_groups[-1]
        # Two separate scope groups; both serialize=True
        assert len(last_batch.groups) == 2
        assert last_batch.serialize_flags[0] is True
        assert last_batch.serialize_flags[1] is True

    def test_serial_barrier_batch_has_serialize_false(self) -> None:
        tcs = [_tc("shell_run")]
        meta = {"shell_run": _spec("shell_run", requires_serial=True)}
        _groups, md = build_execution_groups(tcs, meta)
        barrier_batch = md.concurrent_groups[0]
        assert barrier_batch.groups == [[tcs[0]]]
        assert barrier_batch.serialize_flags[0] is False

    def test_write_first_batch_has_serialize_false(self) -> None:
        tcs = [_tc("write_x"), _tc("write_y")]
        meta = {
            "write_x": _spec("write_x", is_write=True),  # no scope
            "write_y": _spec("write_y", is_write=True),  # no scope
        }
        _groups, md = build_execution_groups(tcs, meta)
        write_first_batch = md.concurrent_groups[0]
        assert write_first_batch.serialize_flags[0] is False

    def test_empty_input_has_empty_concurrent_groups(self) -> None:
        _groups, md = build_execution_groups([], {})
        assert md.concurrent_groups == []


# ── _SerializationEvent new fields ────────────────────────────────────────────


class TestSerializationEventFields:
    def test_serial_barrier_event_fields(self) -> None:
        tcs = [_tc("shell_run")]
        meta = {"shell_run": _spec("shell_run", requires_serial=True)}
        _groups, md = build_execution_groups(tcs, meta)
        evt = next(e for e in md.serialization_events if e.reason == "requires_serial")
        assert evt.requires_serial is True
        assert evt.is_write is True
        assert evt.resource_scope == ""
        assert evt.scheduling_decision == "serial_barrier"

    def test_resource_scope_event_fields(self) -> None:
        tcs = [_tc("write_a"), _tc("write_b")]
        meta = {
            "write_a": _spec("write_a", scope="file:/foo", is_write=True),
            "write_b": _spec("write_b", scope="file:/foo", is_write=True),
        }
        _groups, md = build_execution_groups(tcs, meta)
        evt = next(
            e for e in md.serialization_events if e.reason == "resource_scope_conflict"
        )
        assert evt.resource_scope == "file:/foo"
        assert evt.is_write is True
        assert evt.requires_serial is False
        assert evt.scheduling_decision == "resource_scope"

    def test_write_first_event_fields(self) -> None:
        tcs = [_tc("write_x")]
        meta = {"write_x": _spec("write_x", is_write=True)}
        _groups, md = build_execution_groups(tcs, meta)
        evt = next(e for e in md.serialization_events if e.reason == "is_write_overlap")
        assert evt.is_write is True
        assert evt.resource_scope == ""
        assert evt.requires_serial is False
        assert evt.scheduling_decision == "write_first"

    def test_read_only_produces_no_serialization_events(self) -> None:
        tcs = [_tc("read_a"), _tc("read_b")]
        meta = {"read_a": _spec("read_a"), "read_b": _spec("read_b")}
        _groups, md = build_execution_groups(tcs, meta)
        assert md.serialization_events == []

    def test_serialization_event_tools_count(self) -> None:
        tcs = [_tc("write_a"), _tc("write_b"), _tc("write_c")]
        meta = {
            "write_a": _spec("write_a", scope="s", is_write=True),
            "write_b": _spec("write_b", scope="s", is_write=True),
            "write_c": _spec("write_c", scope="s", is_write=True),
        }
        _groups, md = build_execution_groups(tcs, meta)
        evt = next(
            e for e in md.serialization_events if e.reason == "resource_scope_conflict"
        )
        assert evt.tools_count == 3
