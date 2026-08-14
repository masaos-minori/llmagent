"""tests/test_tool_scheduler.py
Unit tests for agent/tool_scheduler.py — build_execution_groups() and its
single ExecutionPlan/ScheduledBatch/ScheduledGroup return shape.
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


# ── empty / trivial inputs ────────────────────────────────────────────────────


class TestBuildExecutionGroupsEmpty:
    def test_empty_tool_calls_returns_empty_plan(self) -> None:
        plan = build_execution_groups([], {})
        assert plan.batches == ()
        assert plan.serialization_events == ()

    def test_single_parallel_tool_returns_one_concurrent_group(self) -> None:
        tc = _tc("read_text_file")
        plan = build_execution_groups([tc], {tc["id"]: _spec(tc)})
        assert len(plan.batches) == 1
        assert len(plan.batches[0].groups) == 1
        group = plan.batches[0].groups[0]
        assert group.sequential is False
        assert _ids(group) == {tc["id"]}

    def test_unknown_tool_raises_missing_tool_spec(self) -> None:
        tc = _tc("some_unknown_tool")
        with pytest.raises(MissingToolSpecError):
            build_execution_groups([tc], {})


# ── requires_serial barrier ───────────────────────────────────────────────────


class TestRequiresSerialBarrier:
    def test_serial_tool_forms_single_call_sequential_group(self) -> None:
        tc = _tc("shell_run")
        plan = build_execution_groups([tc], {tc["id"]: _spec(tc, requires_serial=True)})
        assert len(plan.batches) == 1
        group = plan.batches[0].groups[0]
        assert group.sequential is True
        assert group.reason == "requires_serial"
        assert _ids(group) == {tc["id"]}

    def test_serial_precedes_parallel_when_serial_appears_first(self) -> None:
        serial = _tc("shell_run")
        parallel = _tc("read_text_file")
        plan = build_execution_groups(
            [serial, parallel],
            {
                serial["id"]: _spec(serial, requires_serial=True),
                parallel["id"]: _spec(parallel),
            },
        )
        assert len(plan.batches) == 2
        assert _ids(plan.batches[0].groups[0]) == {serial["id"]}
        assert _ids(plan.batches[1].groups[0]) == {parallel["id"]}

    def test_parallel_precedes_serial_when_parallel_appears_first(self) -> None:
        """Proves the barrier is applied in-place, not hoisted to the front of
        the batch regardless of where it appears in the input — the inverse
        of test_serial_precedes_parallel_when_serial_appears_first, which a
        leading-bucket implementation would get wrong."""
        parallel = _tc("read_text_file")
        serial = _tc("shell_run")
        plan = build_execution_groups(
            [parallel, serial],
            {
                parallel["id"]: _spec(parallel),
                serial["id"]: _spec(serial, requires_serial=True),
            },
        )
        assert len(plan.batches) == 2
        assert _ids(plan.batches[0].groups[0]) == {parallel["id"]}
        assert plan.batches[0].groups[0].sequential is False
        assert _ids(plan.batches[1].groups[0]) == {serial["id"]}
        assert plan.batches[1].groups[0].sequential is True

    def test_multiple_serial_tools_each_get_own_batch(self) -> None:
        tc1 = _tc("shell_run", "call_shell_run_1")
        tc2 = _tc("shell_run", "call_shell_run_2")
        plan = build_execution_groups(
            [tc1, tc2],
            {
                tc1["id"]: _spec(tc1, requires_serial=True),
                tc2["id"]: _spec(tc2, requires_serial=True),
            },
        )
        assert len(plan.batches) == 2
        assert _ids(plan.batches[0].groups[0]) == {tc1["id"]}
        assert _ids(plan.batches[1].groups[0]) == {tc2["id"]}

    def test_multiple_barriers_split_batch_into_phases_in_order(self) -> None:
        """[read_a, serial_1, read_b, serial_2, read_c] must produce five
        batches in exactly that order — phases split around *every* barrier
        encountered while walking in order, not just the first."""
        read_a = _tc("read_a")
        serial_1 = _tc("serial_1")
        read_b = _tc("read_b")
        serial_2 = _tc("serial_2")
        read_c = _tc("read_c")
        specs = {
            read_a["id"]: _spec(read_a),
            serial_1["id"]: _spec(serial_1, requires_serial=True),
            read_b["id"]: _spec(read_b),
            serial_2["id"]: _spec(serial_2, requires_serial=True),
            read_c["id"]: _spec(read_c),
        }
        plan = build_execution_groups(
            [read_a, serial_1, read_b, serial_2, read_c], specs
        )
        assert len(plan.batches) == 5
        assert _ids(plan.batches[0].groups[0]) == {read_a["id"]}
        assert _ids(plan.batches[1].groups[0]) == {serial_1["id"]}
        assert _ids(plan.batches[2].groups[0]) == {read_b["id"]}
        assert _ids(plan.batches[3].groups[0]) == {serial_2["id"]}
        assert _ids(plan.batches[4].groups[0]) == {read_c["id"]}


# ── resource_scopes grouping ──────────────────────────────────────────────────


class TestResourceScopeGrouping:
    def test_write_tools_with_same_scope_are_grouped_and_sequential(self) -> None:
        tc1 = _tc("write_file", "call_write_file_1")
        tc2 = _tc("write_file", "call_write_file_2")
        specs = {
            tc1["id"]: _spec(tc1, resource_scopes=("filesystem:/file",), is_write=True),
            tc2["id"]: _spec(tc2, resource_scopes=("filesystem:/file",), is_write=True),
        }
        plan = build_execution_groups([tc1, tc2], specs)
        assert len(plan.batches) == 1
        group = plan.batches[0].groups[0]
        assert group.sequential is True
        assert group.reason == "resource_write_write_conflict"
        assert _ids(group) == {tc1["id"], tc2["id"]}

    def test_write_tools_with_different_scopes_do_not_conflict(self) -> None:
        tc_file = _tc("write_file")
        tc_github = _tc("github_push_files")
        specs = {
            tc_file["id"]: _spec(
                tc_file, resource_scopes=("filesystem:/file",), is_write=True
            ),
            tc_github["id"]: _spec(
                tc_github, resource_scopes=("github_repo:github",), is_write=True
            ),
        }
        plan = build_execution_groups([tc_file, tc_github], specs)
        assert len(plan.batches) == 1
        group = plan.batches[0].groups[0]
        assert group.sequential is False
        assert _ids(group) == {tc_file["id"], tc_github["id"]}

    def test_read_tool_with_scope_alone_is_concurrent(self) -> None:
        tc = _tc("read_text_file")
        plan = build_execution_groups(
            [tc], {tc["id"]: _spec(tc, resource_scopes=("filesystem:/file",))}
        )
        group = plan.batches[0].groups[0]
        assert group.sequential is False
        assert _ids(group) == {tc["id"]}

    def test_solitary_scopeless_write_has_nothing_to_conflict_with(self) -> None:
        """A lone scope-less write with nothing else in its phase is pooled
        into the concurrent group like any other un-conflicted call — there
        is no separate write-first bucket anymore."""
        tc = _tc("write_file")
        plan = build_execution_groups([tc], {tc["id"]: _spec(tc, is_write=True)})
        group = plan.batches[0].groups[0]
        assert group.sequential is False
        assert _ids(group) == {tc["id"]}

    def test_scopeless_writes_now_serialize_via_global_write_scope(self) -> None:
        """Regression lock for this plan's fix: two scope-less writes used to
        share one *concurrently-gathered* group (racing each other, per the
        old write-first bucket); they now resolve to the same synthetic
        global:write scope and serialize instead."""
        tc1 = _tc("write_file")
        tc2 = _tc("delete_file")
        specs = {
            tc1["id"]: _spec(tc1, is_write=True),
            tc2["id"]: _spec(tc2, is_write=True),
        }
        plan = build_execution_groups([tc1, tc2], specs)
        assert len(plan.batches) == 1
        group = plan.batches[0].groups[0]
        assert group.sequential is True
        assert group.reason == "global_write_scope"
        assert _ids(group) == {tc1["id"], tc2["id"]}

    def test_scopeless_write_and_unrelated_read_do_not_conflict(self) -> None:
        tc_write = _tc("write_file")
        tc_read = _tc("read_text_file")
        specs = {
            tc_write["id"]: _spec(tc_write, is_write=True),
            tc_read["id"]: _spec(tc_read),
        }
        plan = build_execution_groups([tc_read, tc_write], specs)
        assert len(plan.batches) == 1
        group = plan.batches[0].groups[0]
        assert group.sequential is False
        assert _ids(group) == {tc_write["id"], tc_read["id"]}


# ── multi-scope conflict cases (ancestor/descendant, dual-scope) ─────────────


class TestMultiScopeConflicts:
    def test_ancestor_descendant_filesystem_paths_conflict(self) -> None:
        """A directory-level write and a descendant-path write must serialize
        together despite their scope strings not being equal."""
        tc_dir = _tc("write_file")
        tc_file = _tc("edit_file")
        specs = {
            tc_dir["id"]: _spec(
                tc_dir, resource_scopes=("filesystem:/data",), is_write=True
            ),
            tc_file["id"]: _spec(
                tc_file,
                resource_scopes=("filesystem:/data/sub/file.txt",),
                is_write=True,
            ),
        }
        plan = build_execution_groups([tc_dir, tc_file], specs)
        assert len(plan.batches) == 1
        group = plan.batches[0].groups[0]
        assert group.sequential is True
        assert _ids(group) == {tc_dir["id"], tc_file["id"]}

    def test_directory_read_conflicts_with_descendant_write(self) -> None:
        """A directory read must conflict with a descendant-path write despite
        unequal scope strings."""
        tc_read_dir = _tc("list_directory")
        tc_write_desc = _tc("write_file")
        specs = {
            tc_read_dir["id"]: _spec(
                tc_read_dir, resource_scopes=("filesystem:/data",)
            ),
            tc_write_desc["id"]: _spec(
                tc_write_desc,
                resource_scopes=("filesystem:/data/sub/file.txt",),
                is_write=True,
            ),
        }
        plan = build_execution_groups([tc_read_dir, tc_write_desc], specs)
        assert len(plan.batches) == 1
        group = plan.batches[0].groups[0]
        assert group.sequential is True
        assert group.reason == "resource_read_write_conflict"
        assert _ids(group) == {tc_read_dir["id"], tc_write_desc["id"]}

    def test_move_file_dual_scope_bridges_two_components(self) -> None:
        """move_file has two independent resource_scopes; each conflicts with
        a different unrelated call, bridging what would otherwise be two
        separate connected components into one."""
        tc_move = _tc("move_file")
        tc_conflict_a = _tc("write_file")
        tc_conflict_b = _tc("edit_file")
        specs = {
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
        }
        plan = build_execution_groups([tc_move, tc_conflict_a, tc_conflict_b], specs)
        assert len(plan.batches) == 1
        group = plan.batches[0].groups[0]
        assert group.sequential is True
        assert _ids(group) == {tc_move["id"], tc_conflict_a["id"], tc_conflict_b["id"]}


# ── missing ToolSpec ──────────────────────────────────────────────────────────


class TestMissingToolSpec:
    def test_missing_call_id_raises(self) -> None:
        tc = _tc("write_file")
        with pytest.raises(MissingToolSpecError):
            build_execution_groups([tc], {})

    def test_missing_call_id_among_known_calls_raises(self) -> None:
        tc_known = _tc("read_text_file")
        tc_unknown = _tc("write_file")
        with pytest.raises(MissingToolSpecError):
            build_execution_groups(
                [tc_known, tc_unknown], {tc_known["id"]: _spec(tc_known)}
            )

    def test_missing_call_id_raises_even_with_force_serial(self) -> None:
        tc = _tc("write_file")
        with pytest.raises(MissingToolSpecError):
            build_execution_groups([tc], {}, force_serial=True)


# ── force_serial ──────────────────────────────────────────────────────────────


class TestForceSerial:
    def test_force_serial_overrides_scope_based_grouping(self) -> None:
        """Two writes sharing an explicit scope would normally group into one
        sequential ScheduledGroup together; force_serial=True instead gives
        each its own single-call sequential phase, in original order —
        proving the short-circuit actually overrides normal grouping rather
        than coincidentally agreeing with it."""
        tc1 = _tc("write_file", "call_1")
        tc2 = _tc("write_file", "call_2")
        specs = {
            tc1["id"]: _spec(tc1, resource_scopes=("filesystem:/file",), is_write=True),
            tc2["id"]: _spec(tc2, resource_scopes=("filesystem:/file",), is_write=True),
        }
        plan = build_execution_groups([tc1, tc2], specs, force_serial=True)
        assert len(plan.batches) == 2
        for batch, tc in zip(plan.batches, [tc1, tc2]):
            assert len(batch.groups) == 1
            group = batch.groups[0]
            assert group.sequential is True
            assert group.reason == "forced_serial"
            assert _ids(group) == {tc["id"]}

    def test_force_serial_ignores_requires_serial_metadata_too(self) -> None:
        """force_serial bypasses phase-building entirely, so a requires_serial
        call is treated the same as any other — one phase per call, in
        original order."""
        tc_serial = _tc("shell_run")
        tc_read = _tc("read_text_file")
        specs = {
            tc_serial["id"]: _spec(tc_serial, requires_serial=True),
            tc_read["id"]: _spec(tc_read),
        }
        plan = build_execution_groups([tc_read, tc_serial], specs, force_serial=True)
        assert len(plan.batches) == 2
        assert _ids(plan.batches[0].groups[0]) == {tc_read["id"]}
        assert _ids(plan.batches[1].groups[0]) == {tc_serial["id"]}
        assert plan.batches[0].groups[0].reason == "forced_serial"
        assert plan.batches[1].groups[0].reason == "forced_serial"

    def test_force_serial_empty_batch(self) -> None:
        plan = build_execution_groups([], {}, force_serial=True)
        assert plan.batches == ()
        assert plan.serialization_events == ()


# ── mixed scenarios ───────────────────────────────────────────────────────────


class TestMixedScenarios:
    def test_serial_resource_and_parallel_all_present(self) -> None:
        tc_serial = _tc("shell_run")
        tc_write = _tc("write_file")
        tc_read = _tc("read_text_file")
        specs = {
            tc_serial["id"]: _spec(tc_serial, requires_serial=True),
            tc_write["id"]: _spec(
                tc_write, resource_scopes=("filesystem:/file",), is_write=True
            ),
            tc_read["id"]: _spec(tc_read),
        }
        plan = build_execution_groups([tc_serial, tc_write, tc_read], specs)
        assert len(plan.batches) == 2
        assert _ids(plan.batches[0].groups[0]) == {tc_serial["id"]}
        phase_batch = plan.batches[1]
        assert len(phase_batch.groups) == 1
        assert _ids(phase_batch.groups[0]) == {tc_write["id"], tc_read["id"]}
        assert phase_batch.groups[0].sequential is False

    def test_all_parallel_returns_one_concurrent_group(self) -> None:
        tcs = [_tc("read_text_file"), _tc("list_directory"), _tc("search_files")]
        specs = {tc["id"]: _spec(tc) for tc in tcs}
        plan = build_execution_groups(tcs, specs)
        assert len(plan.batches) == 1
        assert len(plan.batches[0].groups) == 1
        group = plan.batches[0].groups[0]
        assert group.sequential is False
        assert len(group.calls) == 3

    def test_conflicting_write_and_unrelated_reads_share_one_phase(self) -> None:
        """A same-scope write pair and an unrelated read all appear in the
        same non-barrier phase: the write pair serializes; the read is pooled
        concurrently in the same batch, not a separate one."""
        tc_write1 = _tc("write_file", "call_write_file_1")
        tc_read = _tc("read_text_file")
        tc_write2 = _tc("write_file", "call_write_file_2")
        specs = {
            tc_write1["id"]: _spec(
                tc_write1, resource_scopes=("filesystem:/file",), is_write=True
            ),
            tc_read["id"]: _spec(tc_read),
            tc_write2["id"]: _spec(
                tc_write2, resource_scopes=("filesystem:/file",), is_write=True
            ),
        }
        plan = build_execution_groups([tc_write1, tc_read, tc_write2], specs)
        assert len(plan.batches) == 1
        batch = plan.batches[0]
        assert len(batch.groups) == 2
        write_group = next(g for g in batch.groups if g.sequential)
        assert _ids(write_group) == {tc_write1["id"], tc_write2["id"]}
        read_group = next(g for g in batch.groups if not g.sequential)
        assert _ids(read_group) == {tc_read["id"]}


# ── batch shape ────────────────────────────────────────────────────────────────


class TestConcurrentBatches:
    def test_scope_group_and_parallel_share_one_batch(self) -> None:
        tc_write1 = _tc("write_file", "call_write_file_1")
        tc_write2 = _tc("write_file", "call_write_file_2")
        tc_read = _tc("read_text_file")
        specs = {
            tc_write1["id"]: _spec(
                tc_write1, resource_scopes=("filesystem:/file",), is_write=True
            ),
            tc_write2["id"]: _spec(
                tc_write2, resource_scopes=("filesystem:/file",), is_write=True
            ),
            tc_read["id"]: _spec(tc_read),
        }
        plan = build_execution_groups([tc_write1, tc_write2, tc_read], specs)
        assert len(plan.batches) == 1
        assert len(plan.batches[0].groups) == 2

    def test_serial_barrier_gets_own_batch(self) -> None:
        tc_serial = _tc("shell_run")
        tc_read = _tc("read_text_file")
        specs = {
            tc_serial["id"]: _spec(tc_serial, requires_serial=True),
            tc_read["id"]: _spec(tc_read),
        }
        plan = build_execution_groups([tc_serial, tc_read], specs)
        assert len(plan.batches) == 2
        assert len(plan.batches[0].groups) == 1
        assert _ids(plan.batches[0].groups[0]) == {tc_serial["id"]}

    def test_fts_rebuild_does_not_serialize_unrelated_reads(self) -> None:
        tc_rebuild = _tc("fts_rebuild")
        tc_read_a = _tc("search_docs")
        tc_read_b = _tc("get_chunk")
        specs = {
            tc_rebuild["id"]: _spec(tc_rebuild, requires_serial=True, is_write=True),
            tc_read_a["id"]: _spec(tc_read_a),
            tc_read_b["id"]: _spec(tc_read_b),
        }
        plan = build_execution_groups([tc_rebuild, tc_read_a, tc_read_b], specs)
        assert len(plan.batches) == 2
        assert _ids(plan.batches[0].groups[0]) == {tc_rebuild["id"]}
        read_group = plan.batches[1].groups[0]
        assert read_group.sequential is False
        assert _ids(read_group) == {tc_read_a["id"], tc_read_b["id"]}

    def test_empty_calls_empty_batches(self) -> None:
        plan = build_execution_groups([], {})
        assert plan.batches == ()
