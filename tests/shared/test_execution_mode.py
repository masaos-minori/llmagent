"""
tests/shared/test_execution_mode.py

Contract tests for shared/execution_mode.py: the closed vocabulary and the
resolver rule over validated arguments and declared preview capability.
"""

from __future__ import annotations

import pytest
from shared.execution_mode import EXECUTION_MODES, ExecutionMode, resolve_execution_mode


def test_vocabulary_is_closed() -> None:
    assert EXECUTION_MODES == {"preview", "applied", "no_op"}
    assert set(ExecutionMode.__args__) == EXECUTION_MODES


@pytest.mark.parametrize(
    ("preview_capable", "args", "expected"),
    [
        (True, {"dry_run": True}, "preview"),
        (True, {"dry_run": False}, "applied"),
        (True, {}, "applied"),
        (True, {"dry_run": None}, "applied"),
        (False, {"dry_run": True}, "applied"),
        (False, {"dry_run": "true"}, "applied"),
    ],
)
def test_resolver_table(preview_capable: bool, args: dict, expected: str) -> None:
    assert resolve_execution_mode("write_file", args, preview_capable) == expected


@pytest.mark.parametrize("bad", ["true", 1, 0, 1.0, ["x"]])
def test_non_bool_dry_run_on_capable_tool_is_rejected(bad: object) -> None:
    with pytest.raises(ValueError) as excinfo:
        resolve_execution_mode("write_file", {"dry_run": bad}, True)
    message = str(excinfo.value)
    assert "write_file" in message
    assert type(bad).__name__ in message
    assert repr(bad) not in message


def test_non_bool_dry_run_on_non_capable_tool_is_not_rejected() -> None:
    assert resolve_execution_mode("read_file", {"dry_run": 1}, False) == "applied"
