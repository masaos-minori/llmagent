"""tests/tools/test_tool_cli_convention.py
`--help` and unknown-flag behavior of the six tools that gained an argparse entry, and
the `sys.argv` independence of `main(None)` for the four fixed-input tools.
"""

from __future__ import annotations

import sys
from types import ModuleType

import pytest

from tools import (
    audit_plan_target_paths,
    check_dependency_graph_cycles,
    check_docs_japanese,
    check_needs_confirmation_inventory,
    check_tool_descriptions_sync,
    generate_reference_table,
)

NO_ARGUMENT_TOOLS = [
    check_docs_japanese,
    check_dependency_graph_cycles,
    check_needs_confirmation_inventory,
    check_tool_descriptions_sync,
]
TOOLS = [*NO_ARGUMENT_TOOLS, audit_plan_target_paths, generate_reference_table]


@pytest.mark.parametrize("tool", TOOLS, ids=lambda m: m.__name__)
def test_help_exits_zero_and_prints_usage(
    tool: ModuleType, capsys: pytest.CaptureFixture[str]
) -> None:
    with pytest.raises(SystemExit) as excinfo:
        tool.main(["--help"])

    assert excinfo.value.code == 0
    assert "usage:" in capsys.readouterr().out


@pytest.mark.parametrize("tool", TOOLS, ids=lambda m: m.__name__)
def test_unknown_flag_exits_two(
    tool: ModuleType, capsys: pytest.CaptureFixture[str]
) -> None:
    with pytest.raises(SystemExit) as excinfo:
        tool.main(["--no-such-flag"])

    assert excinfo.value.code == 2
    assert "unrecognized arguments" in capsys.readouterr().err


@pytest.mark.parametrize("tool", NO_ARGUMENT_TOOLS, ids=lambda m: m.__name__)
def test_fixed_input_tools_ignore_sys_argv(
    tool: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(sys, "argv", ["prog", "--no-such-flag"])

    parsed = tool._parse_args(None)

    assert vars(parsed) == {}


def test_audit_plan_target_paths_reads_plans_from_argv() -> None:
    parsed = audit_plan_target_paths._parse_args(["a.md", "b.md"])

    assert parsed.plans == ["a.md", "b.md"]


def test_audit_plan_target_paths_falls_back_to_sys_argv(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(sys, "argv", ["prog", "c.md"])

    assert audit_plan_target_paths._parse_args(None).plans == ["c.md"]


def test_generate_reference_table_requires_type(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as excinfo:
        generate_reference_table.main([])

    assert excinfo.value.code == 2
    assert "--type is required" in capsys.readouterr().err


def test_generate_reference_table_parser_keeps_its_options() -> None:
    options = {
        option
        for action in generate_reference_table._build_parser()._actions
        for option in action.option_strings
    }

    assert {"--type", "--dry-run", "--manifests", "--check"} <= options
