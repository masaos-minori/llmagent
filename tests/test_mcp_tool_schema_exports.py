"""tests/test_mcp_tool_schema_exports.py

Cross-server unit test that asserts every active MCP tool schema module exports
TOOL_LIST as a non-empty list of dicts each containing a "name" key, and that no
module relies on the legacy _MCP_TOOLS name.

Enforces the export policy in docs/04_mcp_07_tool_schema_export_policy.md.
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest

# When adding a new MCP server with tools.py, add its import path here.
# github/github_tools.py is the aggregator; sub-files are tested indirectly.
_TOOL_MODULES: list[tuple[str, str]] = [
    ("mcp_servers.shell.shell_tools", "TOOL_LIST"),
    ("mcp_servers.cicd.cicd_tools", "TOOL_LIST"),
    ("mcp_servers.git.git_tools", "TOOL_LIST"),
    ("mcp_servers.rag_pipeline.rag_pipeline_tools", "TOOL_LIST"),
    ("mcp_servers.web_search.web_search_tools", "TOOL_LIST"),
    ("mcp_servers.mdq.mdq_tools", "TOOL_LIST"),
    ("mcp_servers.github.github_tools", "TOOL_LIST"),
    ("mcp_servers.file.read_tools", "TOOL_LIST"),
    ("mcp_servers.file.write_tools", "TOOL_LIST"),
    ("mcp_servers.file.delete_tools", "TOOL_LIST"),
]

# Ensure scripts/ is on the path (same pattern as conftest.py).
_SCRIPTS = Path(__file__).parent.parent / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))


@pytest.mark.parametrize("module_path,attr_name", _TOOL_MODULES)
def test_tool_list_export(module_path: str, attr_name: str) -> None:
    """Assert each module exports TOOL_LIST as a non-empty list of dicts with name."""
    mod = importlib.import_module(module_path)

    assert hasattr(mod, attr_name), f"{module_path} must export {attr_name}"

    tool_list = getattr(mod, attr_name)
    assert isinstance(tool_list, list), f"{module_path}.{attr_name} must be a list"
    assert len(tool_list) > 0, f"{module_path}.{attr_name} must not be empty"

    for i, tool in enumerate(tool_list):
        assert isinstance(tool, dict), (
            f"{module_path}.{attr_name}[{i}] must be a dict, got {type(tool).__name__}"
        )
        assert "name" in tool, f"{module_path}.{attr_name}[{i}] must have a 'name' key"
        assert isinstance(tool["name"], str), (
            f"{module_path}.{attr_name}[{i}]['name'] must be a string"
        )
        assert len(tool["name"]) > 0, (
            f"{module_path}.{attr_name}[{i}]['name'] must not be empty"
        )


def test_no_legacy_mcp_tools_export() -> None:
    """Assert no module exports the legacy _MCP_TOOLS name."""
    for module_path, _ in _TOOL_MODULES:
        mod = importlib.import_module(module_path)
        assert not hasattr(mod, "_MCP_TOOLS"), (
            f"{module_path} must not export _MCP_TOOLS (use TOOL_LIST)"
        )
