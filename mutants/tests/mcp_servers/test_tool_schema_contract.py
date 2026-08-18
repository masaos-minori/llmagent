"""tests/mcp_servers/test_tool_schema_contract.py

Schema-2.0 contract coverage across all MCP server TOOL_LIST modules.

Validates every tool dict exported by every MCP server's TOOL_LIST against the
schema-2.0 per-tool metadata contract (is_write, requires_serial,
resource_scope_kind, resource_scope_keys) via
scripts/shared/resource_scope.py::validate_tool_schema_v2(), and cross-checks full
tool-name coverage against shared.tool_constants.get_all_mcp_tool_names().

See also tests/mcp_servers/test_tool_schema.py for the narrower, pre-schema-2.0
field-presence check limited to the 4 file+git modules.
"""

from __future__ import annotations

import importlib
from typing import Any

import pytest
from shared.resource_scope import validate_tool_schema_v2
from shared.tool_constants import get_all_mcp_tool_names

_TOOL_LIST_MODULES: list[tuple[str, str]] = [
    ("mcp_servers.file.read_tools", "TOOL_LIST"),
    ("mcp_servers.file.write_tools", "TOOL_LIST"),
    ("mcp_servers.file.delete_tools", "TOOL_LIST"),
    ("mcp_servers.git.git_tools", "TOOL_LIST"),
    ("mcp_servers.github.tools_repository", "TOOL_LIST"),
    ("mcp_servers.github.tools_file", "TOOL_LIST"),
    ("mcp_servers.github.tools_issues", "TOOL_LIST"),
    ("mcp_servers.github.tools_pull_requests", "TOOL_LIST"),
    ("mcp_servers.cicd.cicd_tools", "TOOL_LIST"),
    ("mcp_servers.rag_pipeline.rag_pipeline_tools", "TOOL_LIST"),
    ("mcp_servers.mdq.mdq_tools", "TOOL_LIST"),
    ("mcp_servers.shell.shell_tools", "TOOL_LIST"),
    ("mcp_servers.web_search.web_search_tools", "TOOL_LIST"),
]


@pytest.mark.parametrize("module_path, attr_name", _TOOL_LIST_MODULES)
def test_all_tools_pass_schema_v2_contract(module_path: str, attr_name: str) -> None:
    """Assert every tool entry in module's TOOL_LIST passes the schema-2.0 contract."""
    mod = importlib.import_module(module_path)
    tool_list: list[dict[str, Any]] = getattr(mod, attr_name)
    for tool in tool_list:
        violations = validate_tool_schema_v2(tool)
        assert violations == [], f"{module_path}::{tool['name']}: {violations}"


def test_tool_name_coverage_matches_tool_constants() -> None:
    """Assert the union of all TOOL_LIST names equals get_all_mcp_tool_names()."""
    found: set[str] = set()
    for module_path, attr_name in _TOOL_LIST_MODULES:
        mod = importlib.import_module(module_path)
        found |= {t["name"] for t in getattr(mod, attr_name)}
    expected = get_all_mcp_tool_names()
    assert found == expected, f"mismatch: {found.symmetric_difference(expected)}"
