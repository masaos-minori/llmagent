"""tests/test_tool_scheduler.py
Unit tests for agent/tool_scheduler.py — build_execution_groups.
"""

from __future__ import annotations

from agent.tool_scheduler import build_execution_groups
from shared.tool_spec import ToolSpec


def _tc(name: str) -> dict:
    return {"function": {"name": name}, "id": f"call_{name}"}


def _meta(
    name: str = "",
    *,
    resource_scope: str = "",
    requires_serial: bool = False,
    is_write: bool = False,
) -> ToolSpec:
    return ToolSpec(
        call_id="",
        name=name,
        resource_scope=resource_scope,
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
        groups, _ = build_execution_groups([tc], {"read_text_file": _meta()})
        assert groups == [[tc]]

    def test_unknown_tool_goes_to_parallel(self) -> None:
        tc = _tc("some_unknown_tool")
        groups, _ = build_execution_groups([tc], {})
        assert groups == [[tc]]


# ── requires_serial barrier ───────────────────────────────────────────────────


class TestRequiresSerialBarrier:
    def test_serial_tool_forms_single_element_group(self) -> None:
        tc = _tc("shell_run")
        groups, _ = build_execution_groups(
            [tc], {"shell_run": _meta(requires_serial=True)}
        )
        assert groups == [[tc]]

    def test_serial_tool_precedes_parallel_tools(self) -> None:
        serial = _tc("shell_run")
        parallel = _tc("read_text_file")
        groups, _ = build_execution_groups(
            [serial, parallel],
            {
                "shell_run": _meta(requires_serial=True),
                "read_text_file": _meta(),
            },
        )
        assert groups[0] == [serial]
        assert parallel in groups[-1]

    def test_multiple_serial_tools_each_get_own_group(self) -> None:
        tc1 = _tc("shell_run")
        tc2 = _tc("shell_run")
        groups, _ = build_execution_groups(
            [tc1, tc2], {"shell_run": _meta(requires_serial=True)}
        )
        assert [tc1] in groups
        assert [tc2] in groups


# ── resource_scope grouping ───────────────────────────────────────────────────


class TestResourceScopeGrouping:
    def test_write_tools_with_same_scope_are_grouped_together(self) -> None:
        tc1 = _tc("write_file")
        tc2 = _tc("write_file")
        groups, _ = build_execution_groups(
            [tc1, tc2],
            {"write_file": _meta(resource_scope="file", is_write=True)},
        )
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
                "write_file": _meta(resource_scope="file", is_write=True),
                "github_push_files": _meta(resource_scope="github", is_write=True),
            },
        )
        assert len(groups) == 2

    def test_read_tool_with_scope_goes_to_parallel(self) -> None:
        tc = _tc("read_text_file")
        groups, _ = build_execution_groups(
            [tc],
            {"read_text_file": _meta(resource_scope="file", is_write=False)},
        )
        assert groups == [[tc]]

    def test_write_tool_without_scope_forms_write_first_group(self) -> None:
        tc = _tc("write_file")
        groups, _ = build_execution_groups(
            [tc],
            {"write_file": _meta(resource_scope="", is_write=True)},
        )
        assert groups == [[tc]]

    def test_multiple_write_tools_without_scope_grouped_together(self) -> None:
        tc1 = _tc("write_file")
        tc2 = _tc("edit_file")
        groups, _ = build_execution_groups(
            [tc1, tc2],
            {
                "write_file": _meta(resource_scope="", is_write=True),
                "edit_file": _meta(resource_scope="", is_write=True),
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
                "write_file": _meta(resource_scope="", is_write=True),
                "read_text_file": _meta(),
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
            "shell_run": _meta(requires_serial=True),
            "write_file": _meta(resource_scope="file", is_write=True),
            "edit_file": _meta(resource_scope="", is_write=True),
            "read_text_file": _meta(),
        }
        groups, _ = build_execution_groups(
            [tc_serial, tc_scope_write, tc_read, tc_noscope_write], meta
        )
        assert groups[0] == [tc_serial]
        assert tc_scope_write in groups[1]
        assert tc_noscope_write in groups[2]
        assert tc_read in groups[3]


# ── mixed scenarios ───────────────────────────────────────────────────────────


class TestMixedScenarios:
    def test_separates_by_resource_scope_from_validation_plan(self) -> None:
        """Matches the validation plan test spec exactly."""
        tc_write1 = _tc("write_file")
        tc_read = _tc("read_text_file")
        tc_write2 = _tc("write_file")
        meta = {
            "write_file": _meta(resource_scope="file", is_write=True),
            "read_text_file": _meta(),
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
            "shell_run": _meta(requires_serial=True),
            "read_text_file": _meta(),
        }
        groups, _ = build_execution_groups([tc_shell, tc_read], meta)
        assert groups[0] == [tc_shell]

    def test_all_parallel_returns_one_group(self) -> None:
        tcs = [_tc("read_text_file"), _tc("list_directory"), _tc("search_files")]
        meta = {
            name: _meta()
            for name in ("read_text_file", "list_directory", "search_files")
        }
        groups, _ = build_execution_groups(tcs, meta)
        assert len(groups) == 1
        assert len(groups[0]) == 3

    def test_serial_resource_and_parallel_all_present(self) -> None:
        tc_serial = _tc("shell_run")
        tc_write = _tc("write_file")
        tc_read = _tc("read_text_file")
        meta = {
            "shell_run": _meta(requires_serial=True),
            "write_file": _meta(resource_scope="file", is_write=True),
            "read_text_file": _meta(),
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
                "write_file": _meta(resource_scope="file", is_write=True),
                "read_text_file": _meta(),
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
                "write_file": _meta(resource_scope="file", is_write=True),
                "github_push_files": _meta(resource_scope="github", is_write=True),
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
                "shell_run": _meta(requires_serial=True),
                "read_text_file": _meta(),
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
                "write_file": _meta(resource_scope="", is_write=True),
                "read_text_file": _meta(),
            },
        )
        # write_first and parallel must be in separate batches
        assert len(metadata.concurrent_groups) == 2
        assert metadata.concurrent_groups[0].groups == [[tc_write]]

    def test_empty_calls_empty_concurrent_groups(self) -> None:
        _groups, metadata = build_execution_groups([], {})
        assert metadata.concurrent_groups == []


class TestToolRunnerDefaultSpec:
    """Verify ToolSpec defaults applied in _execute_with_dag().

    These tests replicate the ToolSpec construction logic in tool_runner.py
    to ensure the defaulting rules produce correct scheduling buckets.
    """

    def test_write_file_gets_resource_scope_from_constant(self) -> None:
        from shared.tool_constants import DELETE_TOOLS, SHELL_TOOLS, WRITE_TOOLS

        fn: dict = {"name": "write_file"}
        name = fn.get("name", "")
        _is_write = name in WRITE_TOOLS or name in DELETE_TOOLS
        _default_scope = name if _is_write else ""
        spec = ToolSpec(
            call_id="",
            name=name,
            resource_scope=fn.get("resource_scope", _default_scope),
            requires_serial=fn.get("requires_serial", False) or name in SHELL_TOOLS,
            is_write=_is_write,
        )
        assert spec.resource_scope == "write_file"
        assert spec.is_write is True
        assert spec.requires_serial is False

    def test_shell_run_gets_requires_serial(self) -> None:
        from shared.tool_constants import DELETE_TOOLS, SHELL_TOOLS, WRITE_TOOLS

        fn: dict = {"name": "shell_run"}
        name = fn.get("name", "")
        _is_write = name in WRITE_TOOLS or name in DELETE_TOOLS
        _default_scope = name if _is_write else ""
        spec = ToolSpec(
            call_id="",
            name=name,
            resource_scope=fn.get("resource_scope", _default_scope),
            requires_serial=fn.get("requires_serial", False) or name in SHELL_TOOLS,
            is_write=_is_write,
        )
        assert spec.requires_serial is True
        assert spec.is_write is False
        assert spec.resource_scope == ""

    def test_write_and_read_in_same_concurrent_batch(self) -> None:
        """With resource_scope set, write_file and read_text_file share concurrent_batch."""
        tool_meta = {
            "write_file": _meta(
                name="write_file", resource_scope="write_file", is_write=True
            ),
            "read_text_file": _meta(name="read_text_file"),
        }
        calls = [
            _tc("write_file"),
            _tc("read_text_file"),
        ]
        _groups, metadata = build_execution_groups(calls, tool_meta)
        # write_first must be empty: both groups end up in the same concurrent batch
        assert len(metadata.concurrent_groups) == 1
        # one group for write_file scope, one for the parallel read
        assert len(metadata.concurrent_groups[0].groups) == 2
