"""tests/test_tool_scheduler_comprehensive.py
Comprehensive/edge-case unit tests for agent/tool_scheduler.py —
build_execution_groups() at scale and under dense mixed batches.
"""

from __future__ import annotations

import pytest
from agent.tool_scheduler import (
    MissingToolSpecError,
    ScheduledGroup,
    build_execution_groups,
)
from shared.tool_spec import ToolSpec


def _tc(name: str, call_id: str | None = None) -> dict:
    return {"function": {"name": name}, "id": call_id or f"call_{name}"}


def _spec(
    tc: dict,
    *,
    resource_scopes: tuple[str, ...] = (),
    requires_serial: bool = False,
    is_write: bool = False,
) -> ToolSpec:
    return ToolSpec(
        call_id=tc["id"],
        name=tc["function"]["name"],
        resource_scopes=resource_scopes,
        requires_serial=requires_serial,
        is_write=is_write,
    )


def _ids(group: ScheduledGroup) -> set[str]:
    return {c.call_id for c in group.calls}


def _all_groups(plan) -> list[ScheduledGroup]:
    return [g for batch in plan.batches for g in batch.groups]


class TestBuildExecutionGroupsEdgeCases:
    def test_mixed_tool_types_with_complex_dependencies(self) -> None:
        """A dense batch covering every mechanism at once: a barrier, a
        same-scope write pair, a solitary scope-less write, and two reads."""
        tc_serial = _tc("shell_run")
        tc_scope_write1 = _tc("write_file")
        tc_scope_write2 = _tc("edit_file")
        tc_noscope_write = _tc("create_directory")
        tc_read1 = _tc("read_text_file")
        tc_read2 = _tc("list_directory")

        specs = {
            tc_serial["id"]: _spec(tc_serial, requires_serial=True),
            tc_scope_write1["id"]: _spec(
                tc_scope_write1, resource_scopes=("filesystem:/file",), is_write=True
            ),
            tc_scope_write2["id"]: _spec(
                tc_scope_write2, resource_scopes=("filesystem:/file",), is_write=True
            ),
            tc_noscope_write["id"]: _spec(tc_noscope_write, is_write=True),
            tc_read1["id"]: _spec(tc_read1),
            tc_read2["id"]: _spec(tc_read2),
        }

        plan = build_execution_groups(
            [
                tc_serial,
                tc_scope_write1,
                tc_read1,
                tc_noscope_write,
                tc_scope_write2,
                tc_read2,
            ],
            specs,
        )

        # Barrier phase, then one phase for everything after it.
        assert len(plan.batches) == 2
        assert _ids(plan.batches[0].groups[0]) == {tc_serial["id"]}

        phase_groups = plan.batches[1].groups
        # The same-scope write pair must serialize together...
        scope_group = next(g for g in phase_groups if g.sequential)
        assert _ids(scope_group) == {tc_scope_write1["id"], tc_scope_write2["id"]}
        # ...while the solitary scope-less write and both reads have nothing
        # to conflict with and are pooled concurrently.
        pooled_group = next(g for g in phase_groups if not g.sequential)
        assert _ids(pooled_group) == {
            tc_noscope_write["id"],
            tc_read1["id"],
            tc_read2["id"],
        }

    def test_move_file_dual_scope_inside_dense_mixed_batch(self) -> None:
        """A move_file-style dual-scope call inside the same dense mixed batch
        as unrelated serial/scope-less-write/read calls: the dual-scope call
        must bridge exactly the two calls whose scope it independently
        overlaps, without disturbing the unrelated groups."""
        tc_serial = _tc("shell_run")
        tc_move = _tc("move_file")
        tc_conflict_a = _tc("write_file")
        tc_conflict_b = _tc("edit_file")
        tc_noscope_write = _tc("create_directory")
        tc_read = _tc("read_text_file")

        specs = {
            tc_serial["id"]: _spec(tc_serial, requires_serial=True),
            tc_move["id"]: _spec(
                tc_move,
                resource_scopes=("filesystem:/a", "filesystem:/b"),
                is_write=True,
            ),
            tc_conflict_a["id"]: _spec(
                tc_conflict_a, resource_scopes=("filesystem:/a",), is_write=True
            ),
            tc_conflict_b["id"]: _spec(
                tc_conflict_b, resource_scopes=("filesystem:/b",), is_write=True
            ),
            tc_noscope_write["id"]: _spec(tc_noscope_write, is_write=True),
            tc_read["id"]: _spec(tc_read),
        }

        plan = build_execution_groups(
            [
                tc_serial,
                tc_move,
                tc_conflict_a,
                tc_noscope_write,
                tc_conflict_b,
                tc_read,
            ],
            specs,
        )

        assert len(plan.batches) == 2
        assert _ids(plan.batches[0].groups[0]) == {tc_serial["id"]}

        phase_groups = plan.batches[1].groups
        bridge_group = next(g for g in phase_groups if g.sequential)
        assert _ids(bridge_group) == {
            tc_move["id"],
            tc_conflict_a["id"],
            tc_conflict_b["id"],
        }
        pooled_group = next(g for g in phase_groups if not g.sequential)
        assert _ids(pooled_group) == {tc_noscope_write["id"], tc_read["id"]}

    def test_same_scope_read_write_conflict(self) -> None:
        """A write and a read sharing an explicit scope must serialize —
        exercised independently of the global:write fallback path."""
        tc_write = _tc("write_file")
        tc_read = _tc("read_text_file")
        specs = {
            tc_write["id"]: _spec(
                tc_write, resource_scopes=("filesystem:/shared",), is_write=True
            ),
            tc_read["id"]: _spec(tc_read, resource_scopes=("filesystem:/shared",)),
        }
        plan = build_execution_groups([tc_write, tc_read], specs)
        assert len(plan.batches) == 1
        group = plan.batches[0].groups[0]
        assert group.sequential is True
        assert group.reason == "resource_read_write_conflict"
        assert _ids(group) == {tc_write["id"], tc_read["id"]}

    def test_same_scope_write_write_conflict(self) -> None:
        """Two writes sharing an explicit scope must serialize — distinct
        from the global:write fallback path (both writes have their own
        real, non-empty resource_scopes here)."""
        tc_write_a = _tc("write_file")
        tc_write_b = _tc("edit_file")
        specs = {
            tc_write_a["id"]: _spec(
                tc_write_a, resource_scopes=("filesystem:/shared",), is_write=True
            ),
            tc_write_b["id"]: _spec(
                tc_write_b, resource_scopes=("filesystem:/shared",), is_write=True
            ),
        }
        plan = build_execution_groups([tc_write_a, tc_write_b], specs)
        assert len(plan.batches) == 1
        group = plan.batches[0].groups[0]
        assert group.sequential is True
        assert group.reason == "resource_write_write_conflict"
        assert _ids(group) == {tc_write_a["id"], tc_write_b["id"]}

    def test_complex_resource_scopes(self) -> None:
        """Test with complex resource scope strings."""
        tc_write_a = _tc("write_file")
        tc_write_b = _tc("edit_file")
        tc_write_c = _tc("create_directory")

        specs = {
            tc_write_a["id"]: _spec(
                tc_write_a,
                resource_scopes=("filesystem:/path/to/project/a",),
                is_write=True,
            ),
            tc_write_b["id"]: _spec(
                tc_write_b,
                resource_scopes=("filesystem:/path/to/project/b",),
                is_write=True,
            ),
            tc_write_c["id"]: _spec(
                tc_write_c,
                resource_scopes=("filesystem:/path/to/project/a",),
                is_write=True,
            ),
        }

        plan = build_execution_groups([tc_write_a, tc_write_b, tc_write_c], specs)
        groups = plan.batches[0].groups
        # One sequential group for /path/to/project/a (write_file + create_directory)
        # and one concurrent singleton for /path/to/project/b (edit_file).
        assert len(groups) == 2
        a_group = next(g for g in groups if tc_write_a["id"] in _ids(g))
        assert _ids(a_group) == {tc_write_a["id"], tc_write_c["id"]}
        assert a_group.sequential is True
        b_group = next(g for g in groups if tc_write_b["id"] in _ids(g))
        assert _ids(b_group) == {tc_write_b["id"]}
        assert b_group.sequential is False

    def test_all_tools_same_resource_scope(self) -> None:
        """Test when all tools share the same resource scope."""
        tc_write1 = _tc("write_file")
        tc_write2 = _tc("edit_file")
        tc_write3 = _tc("create_directory")

        specs = {
            tc_write1["id"]: _spec(
                tc_write1, resource_scopes=("filesystem:shared",), is_write=True
            ),
            tc_write2["id"]: _spec(
                tc_write2, resource_scopes=("filesystem:shared",), is_write=True
            ),
            tc_write3["id"]: _spec(
                tc_write3, resource_scopes=("filesystem:shared",), is_write=True
            ),
        }

        plan = build_execution_groups([tc_write1, tc_write2, tc_write3], specs)

        assert len(plan.batches) == 1
        group = plan.batches[0].groups[0]
        assert group.sequential is True
        assert len(group.calls) == 3

    def test_tool_with_no_metadata_raises(self) -> None:
        """A call with no entry in call_specs raises MissingToolSpecError
        instead of silently defaulting to an unscoped, non-write ToolSpec —
        the failure holds both with and without force_serial."""
        tc_write = _tc("write_file")
        tc_read = _tc("read_text_file")

        with pytest.raises(MissingToolSpecError):
            build_execution_groups([tc_write, tc_read], {})

        with pytest.raises(MissingToolSpecError):
            build_execution_groups([tc_write, tc_read], {}, force_serial=True)

    def test_large_number_of_tools(self) -> None:
        """Test with a large number of tools."""
        tools = [_tc(f"read_file_{i}") for i in range(20)]
        specs = {tc["id"]: _spec(tc) for tc in tools}

        plan = build_execution_groups(tools, specs)

        # All in one concurrent group.
        assert len(plan.batches) == 1
        group = plan.batches[0].groups[0]
        assert group.sequential is False
        assert len(group.calls) == 20

    def test_large_all_read_batch_never_conflicts_at_scale(self) -> None:
        """A large all-read batch stays in one concurrent group regardless of
        size — the conflict graph must never build an edge between two reads,
        even at scale."""
        tools = [_tc(f"read_file_{i}") for i in range(50)]
        specs = {tc["id"]: _spec(tc) for tc in tools}

        plan = build_execution_groups(tools, specs)

        assert len(plan.batches) == 1
        assert len(plan.batches[0].groups) == 1
        group = plan.batches[0].groups[0]
        assert group.sequential is False
        assert len(group.calls) == 50

    def test_large_number_of_tools_with_overlapping_multi_scope_subset(self) -> None:
        """A large batch where most tools are unscoped reads, but a subset
        shares overlapping multi-valued resource_scopes (including one
        ancestor/descendant filesystem pair) — the conflict-graph logic must
        scale correctly and not accidentally merge unrelated components."""
        tools = [_tc(f"read_file_{i}") for i in range(15)]
        specs = {tc["id"]: _spec(tc) for tc in tools}

        tc_write_a = _tc("write_file_a")
        tc_write_b = _tc("write_file_b")
        tc_dir = _tc("create_directory")
        tc_nested = _tc("write_nested")
        tc_isolated = _tc("write_isolated")
        specs[tc_write_a["id"]] = _spec(
            tc_write_a, resource_scopes=("filesystem:/shared",), is_write=True
        )
        specs[tc_write_b["id"]] = _spec(
            tc_write_b, resource_scopes=("filesystem:/shared",), is_write=True
        )
        specs[tc_dir["id"]] = _spec(
            tc_dir, resource_scopes=("filesystem:/tree",), is_write=True
        )
        specs[tc_nested["id"]] = _spec(
            tc_nested,
            resource_scopes=("filesystem:/tree/nested/file.txt",),
            is_write=True,
        )
        specs[tc_isolated["id"]] = _spec(
            tc_isolated, resource_scopes=("filesystem:/lonely",), is_write=True
        )

        all_tools = tools + [tc_write_a, tc_write_b, tc_dir, tc_nested, tc_isolated]
        plan = build_execution_groups(all_tools, specs)

        groups = _all_groups(plan)
        shared_group = next(g for g in groups if tc_write_a["id"] in _ids(g))
        assert _ids(shared_group) == {tc_write_a["id"], tc_write_b["id"]}
        assert shared_group.sequential is True

        tree_group = next(g for g in groups if tc_dir["id"] in _ids(g))
        assert _ids(tree_group) == {tc_dir["id"], tc_nested["id"]}
        assert tree_group.sequential is True

        # tc_isolated has nothing to conflict with, so it is pooled into the
        # concurrent group alongside the 15 unrelated reads.
        pooled_group = next(g for g in groups if not g.sequential)
        assert tc_isolated["id"] in _ids(pooled_group)
        assert len(pooled_group.calls) == 16

    def test_single_tool_with_complex_metadata(self) -> None:
        """Test a single tool carrying requires_serial, resource_scopes, and
        is_write all at once — requires_serial wins, forming a barrier."""
        tc = _tc("shell_run")
        specs = {
            tc["id"]: _spec(
                tc,
                requires_serial=True,
                resource_scopes=("filesystem:complex",),
                is_write=True,
            )
        }

        plan = build_execution_groups([tc], specs)

        assert len(plan.batches) == 1
        group = plan.batches[0].groups[0]
        assert group.sequential is True
        assert group.reason == "requires_serial"
        assert _ids(group) == {tc["id"]}
