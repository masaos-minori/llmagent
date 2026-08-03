#!/usr/bin/env python3
"""Tests for MDQ `TOOL_LIST` `inputSchema` bounds/enum/items constraints.

Asserts that the publicly advertised JSON Schema in
`scripts/mcp_servers/mdq/mdq_tools.py::TOOL_LIST` matches the runtime caps
enforced in `mdq_service.py`/`mdq_models.py`.

Config-drift guard: `config/mdq_mcp_server.toml` only declares 5 of the 7
numeric caps as TOML keys (`max_results_limit`, `max_chars_per_chunk`,
`max_total_result_chars`, `max_outline_items`, `max_grep_matches`). The other
two bounded fields covered here (`outline.max_depth`,
`grep_docs.max_chars_per_match`) have no TOML key — their runtime value comes
solely from the `MdqConfig` Pydantic field default (`mdq_models.py`) — so they
are asserted against their literal expected value directly, not cross-checked
against the TOML file.
"""

from __future__ import annotations

from typing import Any

from mcp_servers.mdq.mdq_tools import TOOL_LIST
from shared.config_loader import ConfigLoader


def _tool_schema(name: str) -> dict[str, Any]:
    """Return the `inputSchema` dict for the named tool in `TOOL_LIST`."""
    for tool in TOOL_LIST:
        if tool["name"] == name:
            return tool["inputSchema"]
    raise AssertionError(f"tool {name!r} not found in TOOL_LIST")


def test_search_docs_mode_enum_bm25_only() -> None:
    props = _tool_schema("search_docs")["properties"]
    assert props["mode"]["enum"] == ["bm25"]


def test_search_docs_integer_bounds() -> None:
    props = _tool_schema("search_docs")["properties"]
    assert (props["limit"]["minimum"], props["limit"]["maximum"]) == (1, 100)
    assert (
        props["max_results_limit"]["minimum"],
        props["max_results_limit"]["maximum"],
    ) == (1, 100)
    assert (
        props["max_total_result_chars"]["minimum"],
        props["max_total_result_chars"]["maximum"],
    ) == (1, 100000)


def test_search_docs_tag_filter_items_type() -> None:
    props = _tool_schema("search_docs")["properties"]
    assert props["tag_filter"]["items"] == {"type": "string"}


def test_get_chunk_max_chars_per_chunk_bounds() -> None:
    props = _tool_schema("get_chunk")["properties"]
    assert (
        props["max_chars_per_chunk"]["minimum"],
        props["max_chars_per_chunk"]["maximum"],
    ) == (1, 10000)


def test_outline_bounds_and_max_depth_present() -> None:
    props = _tool_schema("outline")["properties"]
    assert (
        props["max_outline_items"]["minimum"],
        props["max_outline_items"]["maximum"],
    ) == (1, 500)
    assert "max_depth" in props
    assert (props["max_depth"]["minimum"], props["max_depth"]["maximum"]) == (1, 6)


def test_index_paths_and_refresh_index_paths_items_and_min_items() -> None:
    for tool_name in ("index_paths", "refresh_index"):
        props = _tool_schema(tool_name)["properties"]
        assert props["paths"]["items"] == {"type": "string"}, tool_name
        assert props["paths"]["minItems"] == 1, tool_name


def test_grep_docs_bounds_and_items() -> None:
    props = _tool_schema("grep_docs")["properties"]
    assert (
        props["max_grep_matches"]["minimum"],
        props["max_grep_matches"]["maximum"],
    ) == (1, 200)
    assert (
        props["max_chars_per_match"]["minimum"],
        props["max_chars_per_match"]["maximum"],
    ) == (1, 500)
    assert props["context_before"]["minimum"] == 0
    assert "maximum" not in props["context_before"]
    assert props["context_after"]["minimum"] == 0
    assert "maximum" not in props["context_after"]
    assert props["paths"]["items"] == {"type": "string"}
    assert "minItems" not in props["paths"]


def test_schema_maxima_match_config_defaults() -> None:
    """Guard against drift between advertised schema maxima and TOML config values.

    Only the 5 TOML-backed keys are cross-checked here; the fallback default
    passed to `.get()` mirrors the same default `MdqConfig` field default used
    at runtime, so this test passes whether or not the TOML file declares the
    key explicitly.
    """
    cfg = ConfigLoader().load("mdq_mcp_server.toml")
    assert _tool_schema("search_docs")["properties"]["max_results_limit"][
        "maximum"
    ] == cfg.get("max_results_limit", 100)
    assert _tool_schema("search_docs")["properties"]["max_total_result_chars"][
        "maximum"
    ] == cfg.get("max_total_result_chars", 100000)
    assert _tool_schema("get_chunk")["properties"]["max_chars_per_chunk"][
        "maximum"
    ] == cfg.get("max_chars_per_chunk", 10000)
    assert _tool_schema("outline")["properties"]["max_outline_items"][
        "maximum"
    ] == cfg.get("max_outline_items", 500)
    assert _tool_schema("grep_docs")["properties"]["max_grep_matches"][
        "maximum"
    ] == cfg.get("max_grep_matches", 200)
