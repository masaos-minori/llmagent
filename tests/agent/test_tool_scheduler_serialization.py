"""tests/test_tool_scheduler_serialization.py
Unit tests for ScheduledBatch.serialize_flags and _SerializationEvent new fields.
"""

from __future__ import annotations

from agent.tool_scheduler import build_execution_groups
from shared.tool_spec import ToolSpec


def _tc(name: str) -> dict:
    return {"function": {"name": name, "arguments": "{}"}, "id": f"call_{name}"}


def _spec(
    name: str,
    *,
    scopes: tuple[str, ...] = (),
    is_write: bool = False,
    requires_serial: bool = False,
) -> ToolSpec:
    return ToolSpec(
        call_id="",
        name=name,
        resource_scopes=scopes,
        is_write=is_write,
        requires_serial=requires_serial,
    )


# ── serialize_flags ────────────────────────────────────────────────────────────


class TestSerializeFlags:
    def test_same_scope_write_group_has_serialize_true(self) -> None:
        tcs = [_tc("write_a"), _tc("write_b")]
        meta = {
            tcs[0]["id"]: _spec("write_a", scopes=("file:/foo",), is_write=True),
            tcs[1]["id"]: _spec("write_b", scopes=("file:/foo",), is_write=True),
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
            tcs[0]["id"]: _spec("read_a"),
            tcs[1]["id"]: _spec("read_b"),
        }
        _groups, md = build_execution_groups(tcs, meta)
        read_batch = md.concurrent_groups[-1]
        assert all(flag is False for flag in read_batch.serialize_flags)

    def test_scope_write_serialize_true_read_serialize_false_in_same_batch(
        self,
    ) -> None:
        tcs = [_tc("write_a"), _tc("write_b"), _tc("read_c")]
        meta = {
            tcs[0]["id"]: _spec("write_a", scopes=("repo:X",), is_write=True),
            tcs[1]["id"]: _spec("write_b", scopes=("repo:X",), is_write=True),
            tcs[2]["id"]: _spec("read_c"),
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
            tcs[0]["id"]: _spec("write_a", scopes=("repo:A",), is_write=True),
            tcs[1]["id"]: _spec("write_b", scopes=("repo:B",), is_write=True),
        }
        _groups, md = build_execution_groups(tcs, meta)
        last_batch = md.concurrent_groups[-1]
        # Two separate scope groups; both serialize=True
        assert len(last_batch.groups) == 2
        assert last_batch.serialize_flags[0] is True
        assert last_batch.serialize_flags[1] is True

    def test_serial_barrier_batch_has_serialize_false(self) -> None:
        tcs = [_tc("shell_run")]
        meta = {tcs[0]["id"]: _spec("shell_run", requires_serial=True)}
        _groups, md = build_execution_groups(tcs, meta)
        barrier_batch = md.concurrent_groups[0]
        assert barrier_batch.groups == [[tcs[0]]]
        assert barrier_batch.serialize_flags[0] is False

    def test_write_first_batch_has_serialize_false(self) -> None:
        tcs = [_tc("write_x"), _tc("write_y")]
        meta = {
            tcs[0]["id"]: _spec("write_x", is_write=True),  # no scope
            tcs[1]["id"]: _spec("write_y", is_write=True),  # no scope
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
        meta = {tcs[0]["id"]: _spec("shell_run", requires_serial=True)}
        _groups, md = build_execution_groups(tcs, meta)
        evt = next(e for e in md.serialization_events if e.reason == "requires_serial")
        assert evt.requires_serial is True
        assert evt.is_write is True
        assert evt.resource_scopes == ()
        assert evt.scheduling_decision == "serial_barrier"

    def test_resource_scope_event_fields(self) -> None:
        tcs = [_tc("write_a"), _tc("write_b")]
        meta = {
            tcs[0]["id"]: _spec("write_a", scopes=("file:/foo",), is_write=True),
            tcs[1]["id"]: _spec("write_b", scopes=("file:/foo",), is_write=True),
        }
        _groups, md = build_execution_groups(tcs, meta)
        evt = next(
            e for e in md.serialization_events if e.reason == "resource_scope_conflict"
        )
        assert evt.resource_scopes == ("file:/foo",)
        assert evt.is_write is True
        assert evt.requires_serial is False
        assert evt.scheduling_decision == "resource_scope"

    def test_resource_scope_event_fields_union_multi_scope(self) -> None:
        """A move_file-style dual-scope call's event carries the union of all
        scopes observed across the connected component, not just one side."""
        tc_move = _tc("move_file")
        tc_other = _tc("write_other")
        meta = {
            tc_move["id"]: _spec(
                "move_file", scopes=("filesystem:/a", "filesystem:/b"), is_write=True
            ),
            tc_other["id"]: _spec(
                "write_other", scopes=("filesystem:/a",), is_write=True
            ),
        }
        _groups, md = build_execution_groups([tc_move, tc_other], meta)
        evt = next(
            e for e in md.serialization_events if e.reason == "resource_scope_conflict"
        )
        assert set(evt.resource_scopes) == {"filesystem:/a", "filesystem:/b"}

    def test_write_first_event_fields(self) -> None:
        tcs = [_tc("write_x")]
        meta = {tcs[0]["id"]: _spec("write_x", is_write=True)}
        _groups, md = build_execution_groups(tcs, meta)
        evt = next(e for e in md.serialization_events if e.reason == "is_write_overlap")
        assert evt.is_write is True
        assert evt.resource_scopes == ()
        assert evt.requires_serial is False
        assert evt.scheduling_decision == "write_first"

    def test_read_only_produces_no_serialization_events(self) -> None:
        tcs = [_tc("read_a"), _tc("read_b")]
        meta = {tcs[0]["id"]: _spec("read_a"), tcs[1]["id"]: _spec("read_b")}
        _groups, md = build_execution_groups(tcs, meta)
        assert md.serialization_events == []

    def test_serialization_event_tools_count(self) -> None:
        tcs = [_tc("write_a"), _tc("write_b"), _tc("write_c")]
        meta = {
            tcs[0]["id"]: _spec("write_a", scopes=("s",), is_write=True),
            tcs[1]["id"]: _spec("write_b", scopes=("s",), is_write=True),
            tcs[2]["id"]: _spec("write_c", scopes=("s",), is_write=True),
        }
        _groups, md = build_execution_groups(tcs, meta)
        evt = next(
            e for e in md.serialization_events if e.reason == "resource_scope_conflict"
        )
        assert evt.tools_count == 3
