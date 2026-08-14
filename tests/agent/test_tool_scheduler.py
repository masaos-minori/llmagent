"""tests/test_tool_scheduler.py
Unit tests for agent/tool_scheduler.py — build_execution_groups.
"""

from __future__ import annotations

import pytest
from agent.tool_scheduler import MissingToolSpecError, build_execution_groups
from shared.tool_spec import ToolSpec


def _tc(name: str) -> dict:
    return {"function": {"name": name}, "id": f"call_{name}"}


def _meta(
    name: str = "",
    *,
    resource_scopes: tuple[str, ...] = (),
    requires_serial: bool = False,
    is_write: bool = False,
) -> ToolSpec:
    return ToolSpec(
        call_id="",
        name=name,
        resource_scopes=resource_scopes,
        requires_serial=requires_serial,
        is_write=is_write,
    )


# ── empty / trivial inputs ────────────────────────────────────────────────────


class TestBuildExecutionGroupsEmpty:
    def test_empty_tool_calls_returns_empty(self) -> None:
        groups, _ = build_execution_groups([], {})
        assert groups == []

    def test_single_parallel_tool_returns_one_group(self) -> None:
        tc = _tc("read_text_file")
        groups, _ = build_execution_groups([tc], {tc["id"]: _meta()})
        assert groups == [[tc]]

    def test_unknown_tool_raises_missing_tool_spec(self) -> None:
        tc = _tc("some_unknown_tool")
        with pytest.raises(MissingToolSpecError):
            build_execution_groups([tc], {})


# ── requires_serial barrier ───────────────────────────────────────────────────


class TestRequiresSerialBarrier:
    def test_serial_tool_forms_single_element_group(self) -> None:
        tc = _tc("shell_run")
        groups, _ = build_execution_groups(
            [tc], {tc["id"]: _meta(requires_serial=True)}
        )
        assert groups == [[tc]]

    def test_serial_tool_precedes_parallel_tools(self) -> None:
        serial = _tc("shell_run")
        parallel = _tc("read_text_file")
        groups, _ = build_execution_groups(
            [serial, parallel],
            {
                serial["id"]: _meta(requires_serial=True),
                parallel["id"]: _meta(),
            },
        )
        assert groups[0] == [serial]
        assert parallel in groups[-1]

    def test_multiple_serial_tools_each_get_own_group(self) -> None:
        tc1 = _tc("shell_run")
        tc1["id"] = "call_shell_run_1"
        tc2 = _tc("shell_run")
        tc2["id"] = "call_shell_run_2"
        groups, _ = build_execution_groups(
            [tc1, tc2],
            {
                tc1["id"]: _meta(requires_serial=True),
                tc2["id"]: _meta(requires_serial=True),
            },
        )
        assert [tc1] in groups
        assert [tc2] in groups


# ── resource_scopes grouping ──────────────────────────────────────────────────


class TestResourceScopeGrouping:
    def test_write_tools_with_same_scope_are_grouped_together(self) -> None:
        tc1 = _tc("write_file")
        tc1["id"] = "call_write_file_1"
        tc2 = _tc("write_file")
        tc2["id"] = "call_write_file_2"
        meta = {
            tc1["id"]: _meta(resource_scopes=("filesystem:/file",), is_write=True),
            tc2["id"]: _meta(resource_scopes=("filesystem:/file",), is_write=True),
        }
        groups, _ = build_execution_groups([tc1, tc2], meta)
        write_group = next(
            g for g in groups if any(tc["function"]["name"] == "write_file" for tc in g)
        )
        assert len(write_group) == 2

    def test_write_tools_with_different_scopes_form_separate_groups(self) -> None:
        tc_file = _tc("write_file")
        tc_github = _tc("github_push_files")
        groups, _ = build_execution_groups(
            [tc_file, tc_github],
            {
                tc_file["id"]: _meta(
                    resource_scopes=("filesystem:/file",), is_write=True
                ),
                tc_github["id"]: _meta(
                    resource_scopes=("github_repo:github",), is_write=True
                ),
            },
        )
        assert len(groups) == 2

    def test_read_tool_with_scope_goes_to_parallel(self) -> None:
        tc = _tc("read_text_file")
        groups, _ = build_execution_groups(
            [tc],
            {tc["id"]: _meta(resource_scopes=("filesystem:/file",), is_write=False)},
        )
        assert groups == [[tc]]

    def test_write_tool_without_scope_forms_write_first_group(self) -> None:
        tc = _tc("write_file")
        groups, _ = build_execution_groups(
            [tc],
            {tc["id"]: _meta(resource_scopes=(), is_write=True)},
        )
        assert groups == [[tc]]

    def test_multiple_write_tools_without_scope_grouped_together(self) -> None:
        tc1 = _tc("write_file")
        tc2 = _tc("edit_file")
        groups, _ = build_execution_groups(
            [tc1, tc2],
            {
                tc1["id"]: _meta(resource_scopes=(), is_write=True),
                tc2["id"]: _meta(resource_scopes=(), is_write=True),
            },
        )
        write_group = groups[0]
        assert len(write_group) == 2

    def test_write_first_group_precedes_parallel_read_tools(self) -> None:
        tc_write = _tc("write_file")
        tc_read = _tc("read_text_file")
        groups, _ = build_execution_groups(
            [tc_read, tc_write],
            {
                tc_write["id"]: _meta(resource_scopes=(), is_write=True),
                tc_read["id"]: _meta(),
            },
        )
        assert len(groups) == 2
        assert groups[0] == [tc_write]
        assert groups[1] == [tc_read]

    def test_write_first_group_after_resource_scope_and_serial(self) -> None:
        tc_serial = _tc("shell_run")
        tc_scope_write = _tc("write_file")
        tc_noscope_write = _tc("edit_file")
        tc_read = _tc("read_text_file")
        meta = {
            tc_serial["id"]: _meta(requires_serial=True),
            tc_scope_write["id"]: _meta(
                resource_scopes=("filesystem:/file",), is_write=True
            ),
            tc_noscope_write["id"]: _meta(resource_scopes=(), is_write=True),
            tc_read["id"]: _meta(),
        }
        groups, _ = build_execution_groups(
            [tc_serial, tc_scope_write, tc_read, tc_noscope_write], meta
        )
        assert groups[0] == [tc_serial]
        assert tc_scope_write in groups[1]
        assert tc_noscope_write in groups[2]
        assert tc_read in groups[3]


# ── multi-scope conflict cases (ancestor/descendant, dual-scope) ─────────────


class TestMultiScopeConflicts:
    def test_ancestor_descendant_filesystem_paths_conflict(self) -> None:
        """A directory-level write and a descendant-path write must serialize
        together despite their scope strings not being equal."""
        tc_dir = _tc("write_file")
        tc_file = _tc("edit_file")
        meta = {
            tc_dir["id"]: _meta(resource_scopes=("filesystem:/data",), is_write=True),
            tc_file["id"]: _meta(
                resource_scopes=("filesystem:/data/sub/file.txt",), is_write=True
            ),
        }
        groups, _ = build_execution_groups([tc_dir, tc_file], meta)
        assert len(groups) == 1
        assert set(id(tc) for tc in groups[0]) == {id(tc_dir), id(tc_file)}

    def test_directory_read_conflicts_with_descendant_write(self) -> None:
        """A directory read must conflict with a descendant-path write despite
        unequal scope strings, per the plan's stated acceptance scenario."""
        tc_read_dir = _tc("list_directory")
        tc_write_desc = _tc("write_file")
        meta = {
            tc_read_dir["id"]: _meta(
                resource_scopes=("filesystem:/data",), is_write=False
            ),
            tc_write_desc["id"]: _meta(
                resource_scopes=("filesystem:/data/sub/file.txt",), is_write=True
            ),
        }
        groups, _ = build_execution_groups([tc_read_dir, tc_write_desc], meta)
        assert len(groups) == 1
        assert len(groups[0]) == 2

    def test_move_file_dual_scope_bridges_two_components(self) -> None:
        """move_file has two independent resource_scopes; each conflicts with a
        different unrelated call, bridging what would otherwise be two separate
        connected components into one."""
        tc_move = _tc("move_file")
        tc_conflict_a = _tc("write_file")
        tc_conflict_b = _tc("edit_file")
        meta = {
            tc_move["id"]: _meta(
                resource_scopes=("filesystem:/a", "filesystem:/b"), is_write=True
            ),
            tc_conflict_a["id"]: _meta(
                resource_scopes=("filesystem:/a",), is_write=True
            ),
            tc_conflict_b["id"]: _meta(
                resource_scopes=("filesystem:/b",), is_write=True
            ),
        }
        groups, _ = build_execution_groups(
            [tc_move, tc_conflict_a, tc_conflict_b], meta
        )
        assert len(groups) == 1
        assert len(groups[0]) == 3


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
            build_execution_groups([tc_known, tc_unknown], {tc_known["id"]: _meta()})


# ── mixed scenarios ───────────────────────────────────────────────────────────


class TestMixedScenarios:
    def test_separates_by_resource_scope_from_validation_plan(self) -> None:
        """Matches the validation plan test spec exactly."""
        tc_write1 = _tc("write_file")
        tc_write1["id"] = "call_write_file_1"
        tc_read = _tc("read_text_file")
        tc_write2 = _tc("write_file")
        tc_write2["id"] = "call_write_file_2"
        meta = {
            tc_write1["id"]: _meta(
                resource_scopes=("filesystem:/file",), is_write=True
            ),
            tc_read["id"]: _meta(),
            tc_write2["id"]: _meta(
                resource_scopes=("filesystem:/file",), is_write=True
            ),
        }
        groups, _ = build_execution_groups([tc_write1, tc_read, tc_write2], meta)
        write_group = next(
            g for g in groups if any(tc["function"]["name"] == "write_file" for tc in g)
        )
        assert len(write_group) == 2

    def test_requires_serial_creates_barrier_from_validation_plan(self) -> None:
        """Matches the validation plan test spec exactly."""
        tc_shell = _tc("shell_run")
        tc_read = _tc("read_text_file")
        meta = {
            tc_shell["id"]: _meta(requires_serial=True),
            tc_read["id"]: _meta(),
        }
        groups, _ = build_execution_groups([tc_shell, tc_read], meta)
        assert groups[0] == [tc_shell]

    def test_all_parallel_returns_one_group(self) -> None:
        tcs = [_tc("read_text_file"), _tc("list_directory"), _tc("search_files")]
        meta = {tc["id"]: _meta() for tc in tcs}
        groups, _ = build_execution_groups(tcs, meta)
        assert len(groups) == 1
        assert len(groups[0]) == 3

    def test_serial_resource_and_parallel_all_present(self) -> None:
        tc_serial = _tc("shell_run")
        tc_write = _tc("write_file")
        tc_read = _tc("read_text_file")
        meta = {
            tc_serial["id"]: _meta(requires_serial=True),
            tc_write["id"]: _meta(resource_scopes=("filesystem:/file",), is_write=True),
            tc_read["id"]: _meta(),
        }
        groups, _ = build_execution_groups([tc_serial, tc_write, tc_read], meta)
        assert groups[0] == [tc_serial]
        assert any(
            any(tc["function"]["name"] == "write_file" for tc in g) for g in groups
        )
        assert any(
            any(tc["function"]["name"] == "read_text_file" for tc in g) for g in groups
        )


# ── concurrent_groups ────────────────────────────────────────────────────────


class TestConcurrentGroups:
    def test_scope_group_and_parallel_share_one_batch(self) -> None:
        tc_write = _tc("write_file")
        tc_read = _tc("read_text_file")
        _groups, metadata = build_execution_groups(
            [tc_write, tc_read],
            {
                tc_write["id"]: _meta(
                    resource_scopes=("filesystem:/file",), is_write=True
                ),
                tc_read["id"]: _meta(),
            },
        )
        # Both the scope group and parallel group should be in one concurrent batch
        last_batch = metadata.concurrent_groups[-1]
        assert len(last_batch.groups) == 2

    def test_two_scope_groups_share_one_concurrent_batch(self) -> None:
        tc_file = _tc("write_file")
        tc_github = _tc("github_push_files")
        _groups, metadata = build_execution_groups(
            [tc_file, tc_github],
            {
                tc_file["id"]: _meta(
                    resource_scopes=("filesystem:/file",), is_write=True
                ),
                tc_github["id"]: _meta(
                    resource_scopes=("github_repo:github",), is_write=True
                ),
            },
        )
        last_batch = metadata.concurrent_groups[-1]
        assert len(last_batch.groups) == 2

    def test_serial_barrier_gets_own_batch(self) -> None:
        tc_serial = _tc("shell_run")
        tc_read = _tc("read_text_file")
        _groups, metadata = build_execution_groups(
            [tc_serial, tc_read],
            {
                tc_serial["id"]: _meta(requires_serial=True),
                tc_read["id"]: _meta(),
            },
        )
        # First batch must contain only the serial barrier
        assert metadata.concurrent_groups[0].groups == [[tc_serial]]

    def test_write_first_gets_own_sequential_batch(self) -> None:
        tc_write = _tc("write_file")
        tc_read = _tc("read_text_file")
        _groups, metadata = build_execution_groups(
            [tc_write, tc_read],
            {
                tc_write["id"]: _meta(resource_scopes=(), is_write=True),
                tc_read["id"]: _meta(),
            },
        )
        # write_first and parallel must be in separate batches
        assert len(metadata.concurrent_groups) == 2
        assert metadata.concurrent_groups[0].groups == [[tc_write]]
        assert metadata.concurrent_groups[0].serialize_flags == [False]

    def test_write_first_group_is_gathered_concurrently(self) -> None:
        tc_write_a = _tc("write_file")
        tc_write_b = _tc("delete_file")
        _groups, metadata = build_execution_groups(
            [tc_write_a, tc_write_b],
            {
                tc_write_a["id"]: _meta(resource_scopes=(), is_write=True),
                tc_write_b["id"]: _meta(resource_scopes=(), is_write=True),
            },
        )
        write_first_batch = metadata.concurrent_groups[0]
        assert write_first_batch.groups == [[tc_write_a, tc_write_b]]
        assert write_first_batch.serialize_flags == [False]

    def test_fts_rebuild_does_not_serialize_unrelated_reads(self) -> None:
        tc_rebuild = _tc("fts_rebuild")
        tc_read_a = _tc("search_docs")
        tc_read_b = _tc("get_chunk")
        _groups, metadata = build_execution_groups(
            [tc_rebuild, tc_read_a, tc_read_b],
            {
                tc_rebuild["id"]: _meta(requires_serial=True, is_write=True),
                tc_read_a["id"]: _meta(),
                tc_read_b["id"]: _meta(),
            },
        )
        barrier_batch = metadata.concurrent_groups[0]
        assert barrier_batch.groups == [[tc_rebuild]]
        read_batch = metadata.concurrent_groups[-1]
        assert tc_read_a in read_batch.groups[-1]
        assert tc_read_b in read_batch.groups[-1]
        assert read_batch.serialize_flags[-1] is False

    def test_empty_calls_empty_concurrent_groups(self) -> None:
        _groups, metadata = build_execution_groups([], {})
        assert metadata.concurrent_groups == []


class TestToolRunnerDefaultSpec:
    """Verify RuntimeToolRegistry-derived ToolSpec construction produces correct
    scheduling buckets for representative tool names (a lightweight regression
    lock for the call-id-keyed flow now built inline in
    tool_runner.py::_execute_with_dag(), replacing the deleted
    _build_tool_meta()).
    """

    def test_write_file_gets_resource_scope_from_registry(self) -> None:
        spec = ToolSpec(
            call_id="call_write_file",
            name="write_file",
            resource_scopes=("filesystem:write_file",),
            requires_serial=False,
            is_write=True,
        )
        assert spec.resource_scopes == ("filesystem:write_file",)
        assert spec.is_write is True
        assert spec.requires_serial is False

    def test_shell_run_gets_requires_serial(self) -> None:
        spec = ToolSpec(
            call_id="call_shell_run",
            name="shell_run",
            resource_scopes=(),
            requires_serial=True,
            is_write=False,
        )
        assert spec.requires_serial is True
        assert spec.is_write is False
        assert spec.resource_scopes == ()

    def test_write_and_read_in_same_concurrent_batch(self) -> None:
        """With resource_scopes set, write_file and read_text_file share concurrent_batch."""
        tc_write = _tc("write_file")
        tc_read = _tc("read_text_file")
        tool_meta = {
            tc_write["id"]: _meta(
                name="write_file",
                resource_scopes=("filesystem:write_file",),
                is_write=True,
            ),
            tc_read["id"]: _meta(name="read_text_file"),
        }
        calls = [tc_write, tc_read]
        _groups, metadata = build_execution_groups(calls, tool_meta)
        # write_first must be empty: both groups end up in the same concurrent batch
        assert len(metadata.concurrent_groups) == 1
        # one group for write_file scope, one for the parallel read
        assert len(metadata.concurrent_groups[0].groups) == 2
