"""tests/test_tool_scheduler_comprehensive.py
Comprehensive unit tests for agent/tool_scheduler.py — build_execution_groups.
"""

from __future__ import annotations

from agent.tool_scheduler import build_execution_groups
from shared.tool_spec import ToolSpec


def _tc(name: str) -> dict:
    return {"function": {"name": name}, "id": f"call_{name}"}


def _meta(
    *,
    resource_scope: str = "",
    requires_serial: bool = False,
    is_write: bool = False,
) -> ToolSpec:
    return ToolSpec(
        call_id="",
        name="",
        resource_scope=resource_scope,
        requires_serial=requires_serial,
        is_write=is_write,
    )


class TestBuildExecutionGroupsEdgeCases:
    def test_mixed_tool_types_with_complex_dependencies(self) -> None:
        """Test complex scenario with all tool types."""
        # Create tools with various attributes
        tc_serial = _tc("shell_run")  # requires_serial=True
        tc_scope_write1 = _tc("write_file")  # resource_scope="file", is_write=True
        tc_scope_write2 = _tc("edit_file")  # resource_scope="file", is_write=True
        tc_noscope_write = _tc("create_directory")  # no scope, is_write=True
        tc_read1 = _tc("read_text_file")  # read tool
        tc_read2 = _tc("list_directory")  # read tool

        meta = {
            "shell_run": _meta(requires_serial=True),
            "write_file": _meta(resource_scope="file", is_write=True),
            "edit_file": _meta(resource_scope="file", is_write=True),
            "create_directory": _meta(resource_scope="", is_write=True),
            "read_text_file": _meta(),
            "list_directory": _meta(),
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

    def test_empty_resource_scopes_and_no_scopes(self) -> None:
        """Test with empty strings as resource scopes."""
        tc_write1 = _tc("write_file")
        tc_write2 = _tc("edit_file")
        tc_read = _tc("read_text_file")

        meta = {
            "write_file": _meta(resource_scope="", is_write=True),
            "edit_file": _meta(resource_scope="", is_write=True),
            "read_text_file": _meta(),
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
            "write_file": _meta(resource_scope="/path/to/project/a", is_write=True),
            "edit_file": _meta(resource_scope="/path/to/project/b", is_write=True),
            "create_directory": _meta(
                resource_scope="/path/to/project/a", is_write=True
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
            "write_file": _meta(resource_scope="shared", is_write=True),
            "edit_file": _meta(resource_scope="shared", is_write=True),
            "create_directory": _meta(resource_scope="shared", is_write=True),
        }

        groups, _ = build_execution_groups([tc_write1, tc_write2, tc_write3], meta)

        # Should be grouped together
        assert len(groups) == 1
        assert len(groups[0]) == 3

    def test_tool_with_no_metadata(self) -> None:
        """Test handling of tools with no metadata."""
        tc_write = _tc("write_file")
        tc_read = _tc("read_text_file")

        # Empty metadata dict for unknown tool
        groups, _ = build_execution_groups([tc_write, tc_read], {})

        # Should default to parallel group
        assert len(groups) == 1
        assert len(groups[0]) == 2

    def test_large_number_of_tools(self) -> None:
        """Test with a large number of tools."""
        tools = []
        for i in range(20):
            tools.append(_tc(f"read_file_{i}"))

        meta = {f"read_file_{i}": _meta() for i in range(20)}

        groups, _ = build_execution_groups(tools, meta)

        # Should all be in one parallel group
        assert len(groups) == 1
        assert len(groups[0]) == 20

    def test_single_tool_with_complex_metadata(self) -> None:
        """Test single tool with complex metadata."""
        tc = _tc("shell_run")
        meta = {
            "shell_run": _meta(
                requires_serial=True, resource_scope="complex", is_write=True
            )
        }

        groups, _ = build_execution_groups([tc], meta)

        # Should be in a single-element group (serial barrier)
        assert len(groups) == 1
        assert groups[0] == [tc]
