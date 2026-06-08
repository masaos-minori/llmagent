"""tests/test_tool_scheduler.py
Unit tests for agent/tool_scheduler.py — build_execution_groups.
"""

from __future__ import annotations

from agent.tool_scheduler import build_execution_groups


def _tc(name: str) -> dict:
    return {"function": {"name": name}, "id": f"call_{name}"}


def _meta(
    *,
    resource_scope: str = "",
    requires_serial: bool = False,
    is_write: bool = False,
) -> dict:
    return {
        "resource_scope": resource_scope,
        "requires_serial": requires_serial,
        "is_write": is_write,
    }


# ── empty / trivial inputs ────────────────────────────────────────────────────


class TestBuildExecutionGroupsEmpty:
    def test_empty_tool_calls_returns_empty(self) -> None:
        assert build_execution_groups([], {}) == []

    def test_single_parallel_tool_returns_one_group(self) -> None:
        tc = _tc("read_text_file")
        groups = build_execution_groups([tc], {"read_text_file": _meta()})
        assert groups == [[tc]]

    def test_unknown_tool_goes_to_parallel(self) -> None:
        tc = _tc("some_unknown_tool")
        groups = build_execution_groups([tc], {})
        assert groups == [[tc]]


# ── requires_serial barrier ───────────────────────────────────────────────────


class TestRequiresSerialBarrier:
    def test_serial_tool_forms_single_element_group(self) -> None:
        tc = _tc("shell_run")
        groups = build_execution_groups(
            [tc], {"shell_run": _meta(requires_serial=True)}
        )
        assert groups == [[tc]]

    def test_serial_tool_precedes_parallel_tools(self) -> None:
        serial = _tc("shell_run")
        parallel = _tc("read_text_file")
        groups = build_execution_groups(
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
        groups = build_execution_groups(
            [tc1, tc2], {"shell_run": _meta(requires_serial=True)}
        )
        assert [tc1] in groups
        assert [tc2] in groups


# ── resource_scope grouping ───────────────────────────────────────────────────


class TestResourceScopeGrouping:
    def test_write_tools_with_same_scope_are_grouped_together(self) -> None:
        tc1 = _tc("write_file")
        tc2 = _tc("write_file")
        groups = build_execution_groups(
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
        groups = build_execution_groups(
            [tc_file, tc_github],
            {
                "write_file": _meta(resource_scope="file", is_write=True),
                "github_push_files": _meta(resource_scope="github", is_write=True),
            },
        )
        assert len(groups) == 2

    def test_read_tool_with_scope_goes_to_parallel(self) -> None:
        tc = _tc("read_text_file")
        groups = build_execution_groups(
            [tc],
            {"read_text_file": _meta(resource_scope="file", is_write=False)},
        )
        assert groups == [[tc]]

    def test_write_tool_without_scope_goes_to_parallel(self) -> None:
        tc = _tc("write_file")
        groups = build_execution_groups(
            [tc],
            {"write_file": _meta(resource_scope="", is_write=True)},
        )
        assert groups == [[tc]]


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
        groups = build_execution_groups([tc_write1, tc_read, tc_write2], meta)
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
        groups = build_execution_groups([tc_shell, tc_read], meta)
        assert groups[0] == [tc_shell]

    def test_all_parallel_returns_one_group(self) -> None:
        tcs = [_tc("read_text_file"), _tc("list_directory"), _tc("search_files")]
        meta = {
            name: _meta()
            for name in ("read_text_file", "list_directory", "search_files")
        }
        groups = build_execution_groups(tcs, meta)
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
        groups = build_execution_groups([tc_serial, tc_write, tc_read], meta)
        assert groups[0] == [tc_serial]
        assert any(
            any(tc["function"]["name"] == "write_file" for tc in g) for g in groups
        )
        assert any(
            any(tc["function"]["name"] == "read_text_file" for tc in g) for g in groups
        )
