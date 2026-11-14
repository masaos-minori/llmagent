"""Tests for the checker's shared parse and its precompiled pattern tables."""

from __future__ import annotations

import re

from tools import check_compat_shims as checker
from tools._compat_leftover_phrases import python_nodes


def test_python_nodes_returns_every_node() -> None:
    nodes = python_nodes("import os\nvalue = 1\n")
    kinds = {type(node).__name__ for node in nodes}
    assert {"Module", "Import", "Assign"} <= kinds


def test_python_nodes_is_empty_on_a_syntax_error() -> None:
    assert python_nodes("def broken(:\n") == ()


def test_python_nodes_shares_one_parse_for_the_same_content() -> None:
    content = "x = 1  # shared-parse-probe\n"
    first = python_nodes(content)
    before = python_nodes.cache_info().hits
    assert python_nodes(content) is first
    assert python_nodes.cache_info().hits == before + 1


def test_precompiled_compat_table_mirrors_the_pattern_table() -> None:
    assert [name for name, _ in checker._COMPAT_RE] == list(checker.COMPAT_PATTERNS)
    for (name, regex), pattern in zip(
        checker._COMPAT_RE, checker.COMPAT_PATTERNS.values(), strict=True
    ):
        assert regex.pattern == pattern, name
        assert regex.flags & re.IGNORECASE, name


def test_precompiled_adr_table_mirrors_the_pattern_table() -> None:
    expected = [
        (name, adr_id, pattern)
        for name, (adr_id, pattern) in checker.ADR_PROHIBITED_PATTERNS.items()
    ]
    actual = [(name, adr_id, regex.pattern) for name, adr_id, regex in checker._ADR_RE]
    assert actual == expected
