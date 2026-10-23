"""Table-driven tests for the shared numeric argument parser `parse_int_arg`.

Covers the absent -> default, absent-without-default -> None, valid-bounds, and
invalid/out-of-range behavior required by cmd002 REQ-001 / AC-1. The grammar is
`int()`-based: `'+5'`, `'1_0'`, `' 5 '` are accepted, and `'٣'`/`'１'` remain
accepted because `int()` accepts non-ASCII decimal digits.
"""

from __future__ import annotations

import pytest
from agent.commands.exceptions import CommandValidationError
from agent.commands.utils import parse_int_arg


class _Raises:
    """Marker for a parametrized case that must raise, carrying the usage string."""

    def __init__(self, usage: str) -> None:
        self.usage = usage


@pytest.mark.parametrize(
    "raw,kwargs,expected",
    [
        # absent -> default
        (None, {"usage": "/history [n]", "default": 5}, 5),
        # absent without a default -> None (absent stays distinguishable from invalid)
        (None, {"usage": "/history [n]"}, None),
        # valid within bounds
        ("5", {"usage": "/history [n]", "minimum": 1, "maximum": 200}, 5),
        # int()-grammar acceptances
        ("+5", {"usage": "/history [n]"}, 5),
        ("1_0", {"usage": "/history [n]"}, 10),
        (" 5 ", {"usage": "/history [n]"}, 5),
        ("٣", {"usage": "/history [n]"}, 3),
        ("１", {"usage": "/history [n]"}, 1),
        # invalid / out-of-range / bare flag -> raise carrying the usage string
        ("0", {"usage": "/session purge …", "minimum": 1}, _Raises("/session purge …")),
        (
            "-3",
            {"usage": "/session purge …", "minimum": 1},
            _Raises("/session purge …"),
        ),
        (
            "201",
            {"usage": "/memory list [n]", "maximum": 200},
            _Raises("/memory list [n]"),
        ),
        (
            True,
            {"usage": "/session purge …", "minimum": 1},
            _Raises("/session purge …"),
        ),
        (
            False,
            {"usage": "/session purge …", "minimum": 1},
            _Raises("/session purge …"),
        ),
        ("abc", {"usage": "/history [n]"}, _Raises("/history [n]")),
    ],
)
def test_parse_int_arg(raw: str | bool | None, kwargs: dict, expected: object) -> None:
    if isinstance(expected, _Raises):
        with pytest.raises(CommandValidationError) as excinfo:
            parse_int_arg(raw, **kwargs)
        assert expected.usage in str(excinfo.value)
    else:
        assert parse_int_arg(raw, **kwargs) == expected


def test_parse_int_arg_returns_none_only_when_default_is_none() -> None:
    # A present-but-invalid value never falls back to the default.
    with pytest.raises(CommandValidationError):
        parse_int_arg("abc", usage="/history [n]", default=5)
