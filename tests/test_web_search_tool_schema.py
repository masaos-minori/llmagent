"""
tests/test_web_search_tool_schema.py
Drift tests between TOOL_LIST["search_web"].inputSchema (web_search_tools.py) and
the live Pydantic field constraints on SearchRequest (web_search_models.py).

This module is intentionally scoped to schema/model *drift* detection only (not
bound-value correctness, which is tests/test_web_search_models.py's job). A later
requirement adds agent.toml/TOOL_LIST parity tests to this same file — keep new
test classes separate from TestSearchWebSchemaDrift below rather than mixing
concerns into one class.
"""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any

from mcp_servers.web_search.web_search_models import SearchRequest
from mcp_servers.web_search.web_search_tools import TOOL_LIST


def _search_web_schema() -> dict[str, Any]:
    """Locate the search_web tool's inputSchema by name, not index."""
    matches = [tool for tool in TOOL_LIST if tool["name"] == "search_web"]
    assert len(matches) == 1
    schema: dict[str, Any] = matches[0]["inputSchema"]
    return schema


def _query_constraint(attr: str) -> Any:
    """Extract a constraint value (e.g. min_length/max_length) from
    SearchRequest.model_fields["query"].metadata (annotated_types objects)."""
    for constraint in SearchRequest.model_fields["query"].metadata:
        if hasattr(constraint, attr):
            return getattr(constraint, attr)
    raise AssertionError(
        f"no constraint with attribute {attr!r} found on SearchRequest.query"
    )


def _max_results_constraint(attr: str) -> Any:
    """Extract a constraint value (e.g. ge/le) from
    SearchRequest.model_fields["max_results"].metadata (annotated_types objects)."""
    for constraint in SearchRequest.model_fields["max_results"].metadata:
        if hasattr(constraint, attr):
            return getattr(constraint, attr)
    raise AssertionError(
        f"no constraint with attribute {attr!r} found on SearchRequest.max_results"
    )


class TestSearchWebSchemaDrift:
    """Assert TOOL_LIST[...]["inputSchema"] numerically matches SearchRequest's
    live Pydantic field constraints, so the two never silently diverge."""

    def test_search_web_tool_present(self) -> None:
        assert any(tool["name"] == "search_web" for tool in TOOL_LIST)

    def test_query_min_length_matches_model(self) -> None:
        schema = _search_web_schema()
        assert schema["properties"]["query"]["minLength"] == _query_constraint(
            "min_length"
        )

    def test_query_max_length_matches_model(self) -> None:
        schema = _search_web_schema()
        assert schema["properties"]["query"]["maxLength"] == _query_constraint(
            "max_length"
        )

    def test_max_results_minimum_matches_model(self) -> None:
        schema = _search_web_schema()
        assert schema["properties"]["max_results"][
            "minimum"
        ] == _max_results_constraint("ge")

    def test_max_results_maximum_matches_model(self) -> None:
        schema = _search_web_schema()
        assert schema["properties"]["max_results"][
            "maximum"
        ] == _max_results_constraint("le")


def _agent_toml_search_web() -> dict[str, Any]:
    """Locate the search_web tool definition's parameters block in the real
    config/agent.toml, matched by name (not array index)."""
    path = Path(__file__).parent.parent / "config" / "agent.toml"
    with open(path, "rb") as f:
        cfg = tomllib.load(f)
    matches = [
        td["function"]
        for td in cfg["tool_definitions"]
        if td["function"]["name"] == "search_web"
    ]
    assert len(matches) == 1
    parameters: dict[str, Any] = matches[0]["parameters"]
    return parameters


def _tool_list_search_web_schema() -> dict[str, Any]:
    return _search_web_schema()


class TestAgentTomlVsToolListParity:
    """Assert config/agent.toml's search_web [[tool_definitions]] parameter set
    stays consistent with TOOL_LIST["search_web"].inputSchema (the MCP server's
    own accepted schema) — catches drift such as a parameter present in the
    server's schema but missing from the LLM-facing agent.toml definition."""

    def test_agent_toml_search_web_properties_subset_of_tool_list(self) -> None:
        agent_props = set(_agent_toml_search_web()["properties"])
        tool_list_props = set(_tool_list_search_web_schema()["properties"])
        assert agent_props <= tool_list_props

    def test_agent_toml_search_web_max_results_present(self) -> None:
        assert "max_results" in _agent_toml_search_web()["properties"]

    def test_agent_toml_search_web_max_results_not_required(self) -> None:
        assert "max_results" not in _agent_toml_search_web()["required"]

    def test_agent_toml_search_web_required_matches_tool_list(self) -> None:
        assert (
            _agent_toml_search_web()["required"]
            == _tool_list_search_web_schema()["required"]
        )
