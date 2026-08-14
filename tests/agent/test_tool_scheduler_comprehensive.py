"""tests/test_tool_scheduler_comprehensive.py
Comprehensive unit tests for agent/tool_scheduler.py — build_execution_groups.
"""

from __future__ import annotations

import pytest
from agent.tool_scheduler import MissingToolSpecError, build_execution_groups
from shared.tool_spec import ToolSpec


def _tc(name: str, call_id: str | None = None) -> dict:
    return {"function": {"name": name}, "id": call_id or f"call_{name}"}


def _meta(
    *,
    resource_scopes: tuple[str, ...] = (),
    requires_serial: bool = False,
    is_write: bool = False,
) -> ToolSpec:
    return ToolSpec(
        call_id="",
        name="",
        resource_scopes=resource_scopes,
        requires_serial=requires_serial,
        is_write=is_write,
    )


class TestBuildExecutionGroupsEdgeCases:
    def test_mixed_tool_types_with_complex_dependencies(self) -> None:
        """Test complex scenario with all tool types."""
        # Create tools with various attributes
        tc_serial = _tc("shell_run")  # requires_serial=True
        tc_scope_write1 = _tc(
            "write_file"
        )  # resource_scopes=("filesystem:/file",), is_write=True
        tc_scope_write2 = _tc(
            "edit_file"
        )  # resource_scopes=("filesystem:/file",), is_write=True
        tc_noscope_write = _tc("create_directory")  # no scope, is_write=True
        tc_read1 = _tc("read_text_file")  # read tool
        tc_read2 = _tc("list_directory")  # read tool

        meta = {
            tc_serial["id"]: _meta(requires_serial=True),
            tc_scope_write1["id"]: _meta(
                resource_scopes=("filesystem:/file",), is_write=True
            ),
            tc_scope_write2["id"]: _meta(
                resource_scopes=("filesystem:/file",), is_write=True
            ),
            tc_noscope_write["id"]: _meta(resource_scopes=(), is_write=True),
            tc_read1["id"]: _meta(),
            tc_read2["id"]: _meta(),
        }

        groups, _ = build_execution_groups(
            [
                tc_serial,
                tc_scope_write1,
                tc_read1,
                tc_noscope_write,
                tc_scope_write2,
                tc_read2,
            ],
            meta,
        )

        # Should have 4 groups: serial barrier, resource scope group, write-first group, parallel group
        assert len(groups) == 4

        # First group should be serial
        assert groups[0] == [tc_serial]

        # Second group should contain resource scope tools
        scope_group = next(g for g in groups if tc_scope_write1 in g)
        assert len(scope_group) == 2  # Both write_file and edit_file

        # Third group should be write-first tools
        assert tc_noscope_write in groups[2]

        # Fourth group should be parallel tools
        parallel_group = next(g for g in groups if tc_read1 in g)
        assert len(parallel_group) == 2  # Both read tools

    def test_move_file_dual_scope_inside_dense_mixed_batch(self) -> None:
        """A move_file-style dual-scope call inside the same dense mixed batch
        as unrelated serial/write-first/parallel calls: the dual-scope call
        must bridge exactly the two calls whose scope it independently
        overlaps, without disturbing the unrelated buckets."""
        tc_serial = _tc("shell_run")
        tc_move = _tc("move_file")
        tc_conflict_a = _tc("write_file")
        tc_conflict_b = _tc("edit_file")
        tc_noscope_write = _tc("create_directory")
        tc_read = _tc("read_text_file")

        meta = {
            tc_serial["id"]: _meta(requires_serial=True),
            tc_move["id"]: _meta(
                resource_scopes=("filesystem:/a", "filesystem:/b"), is_write=True
            ),
            tc_conflict_a["id"]: _meta(
                resource_scopes=("filesystem:/a",), is_write=True
            ),
            tc_conflict_b["id"]: _meta(
                resource_scopes=("filesystem:/b",), is_write=True
            ),
            tc_noscope_write["id"]: _meta(resource_scopes=(), is_write=True),
            tc_read["id"]: _meta(),
        }

        groups, _ = build_execution_groups(
            [
                tc_serial,
                tc_move,
                tc_conflict_a,
                tc_noscope_write,
                tc_conflict_b,
                tc_read,
            ],
            meta,
        )

        assert len(groups) == 4
        assert groups[0] == [tc_serial]
        bridge_group = next(g for g in groups if tc_move in g)
        assert len(bridge_group) == 3
        assert tc_conflict_a in bridge_group
        assert tc_conflict_b in bridge_group
        assert tc_noscope_write in groups[2]
        assert groups[3] == [tc_read]

    def test_empty_resource_scopes_and_no_scopes(self) -> None:
        """Test with empty tuples as resource scopes."""
        tc_write1 = _tc("write_file")
        tc_write2 = _tc("edit_file")
        tc_read = _tc("read_text_file")

        meta = {
            tc_write1["id"]: _meta(resource_scopes=(), is_write=True),
            tc_write2["id"]: _meta(resource_scopes=(), is_write=True),
            tc_read["id"]: _meta(),
        }

        groups, _ = build_execution_groups([tc_write1, tc_read, tc_write2], meta)

        # Should have 2 groups: write-first and parallel
        assert len(groups) == 2
        assert tc_write1 in groups[0] or tc_write2 in groups[0]
        assert tc_read in groups[1]

    def test_complex_resource_scopes(self) -> None:
        """Test with complex resource scope strings."""
        tc_write_a = _tc("write_file")
        tc_write_b = _tc("edit_file")
        tc_write_c = _tc("create_directory")

        meta = {
            tc_write_a["id"]: _meta(
                resource_scopes=("filesystem:/path/to/project/a",), is_write=True
            ),
            tc_write_b["id"]: _meta(
                resource_scopes=("filesystem:/path/to/project/b",), is_write=True
            ),
            tc_write_c["id"]: _meta(
                resource_scopes=("filesystem:/path/to/project/a",), is_write=True
            ),
        }

        groups, _ = build_execution_groups([tc_write_a, tc_write_b, tc_write_c], meta)

        # Should have 2 groups: one for /path/to/project/a (write_file + create_directory)
        # and one for /path/to/project/b (edit_file)
        assert len(groups) == 2

    def test_all_tools_same_resource_scope(self) -> None:
        """Test when all tools share same resource scope."""
        tc_write1 = _tc("write_file")
        tc_write2 = _tc("edit_file")
        tc_write3 = _tc("create_directory")

        meta = {
            tc_write1["id"]: _meta(
                resource_scopes=("filesystem:shared",), is_write=True
            ),
            tc_write2["id"]: _meta(
                resource_scopes=("filesystem:shared",), is_write=True
            ),
            tc_write3["id"]: _meta(
                resource_scopes=("filesystem:shared",), is_write=True
            ),
        }

        groups, _ = build_execution_groups([tc_write1, tc_write2, tc_write3], meta)

        # Should be grouped together
        assert len(groups) == 1
        assert len(groups[0]) == 3

    def test_tool_with_no_metadata(self) -> None:
        """A call with no entry in tool_meta raises MissingToolSpecError instead
        of silently defaulting to an unscoped, non-write ToolSpec."""
        tc_write = _tc("write_file")
        tc_read = _tc("read_text_file")

        with pytest.raises(MissingToolSpecError):
            build_execution_groups([tc_write, tc_read], {})

    def test_large_number_of_tools(self) -> None:
        """Test with a large number of tools."""
        tools = []
        for i in range(20):
            tools.append(_tc(f"read_file_{i}"))

        meta = {tc["id"]: _meta() for tc in tools}

        groups, _ = build_execution_groups(tools, meta)

        # Should all be in one parallel group
        assert len(groups) == 1
        assert len(groups[0]) == 20

    def test_large_number_of_tools_with_overlapping_multi_scope_subset(self) -> None:
        """A large batch where most tools are unscoped reads, but a subset
        shares overlapping multi-valued resource_scopes (including one
        ancestor/descendant filesystem pair) — the conflict-graph logic must
        scale correctly and not accidentally merge unrelated components."""
        tools = [_tc(f"read_file_{i}") for i in range(15)]
        meta = {tc["id"]: _meta() for tc in tools}

        # Overlapping subset: two exact-match writers on the same scope, plus
        # an ancestor/descendant pair on a different scope, plus one
        # completely unrelated single write.
        tc_write_a = _tc("write_file_a")
        tc_write_b = _tc("write_file_b")
        tc_dir = _tc("create_directory")
        tc_nested = _tc("write_nested")
        tc_isolated = _tc("write_isolated")
        meta[tc_write_a["id"]] = _meta(
            resource_scopes=("filesystem:/shared",), is_write=True
        )
        meta[tc_write_b["id"]] = _meta(
            resource_scopes=("filesystem:/shared",), is_write=True
        )
        meta[tc_dir["id"]] = _meta(resource_scopes=("filesystem:/tree",), is_write=True)
        meta[tc_nested["id"]] = _meta(
            resource_scopes=("filesystem:/tree/nested/file.txt",), is_write=True
        )
        meta[tc_isolated["id"]] = _meta(
            resource_scopes=("filesystem:/lonely",), is_write=True
        )

        all_tools = tools + [tc_write_a, tc_write_b, tc_dir, tc_nested, tc_isolated]
        groups, _ = build_execution_groups(all_tools, meta)

        shared_group = next(g for g in groups if tc_write_a in g)
        assert set(id(tc) for tc in shared_group) == {id(tc_write_a), id(tc_write_b)}

        tree_group = next(g for g in groups if tc_dir in g)
        assert set(id(tc) for tc in tree_group) == {id(tc_dir), id(tc_nested)}

        isolated_group = next(g for g in groups if tc_isolated in g)
        assert isolated_group == [tc_isolated]

        parallel_group = next(g for g in groups if tools[0] in g)
        assert len(parallel_group) == 15

    def test_single_tool_with_complex_metadata(self) -> None:
        """Test single tool with complex metadata."""
        tc = _tc("shell_run")
        meta = {
            tc["id"]: _meta(
                requires_serial=True,
                resource_scopes=("filesystem:complex",),
                is_write=True,
            )
        }

        groups, _ = build_execution_groups([tc], meta)

        # Should be in a single-element group (serial barrier)
        assert len(groups) == 1
        assert groups[0] == [tc]
