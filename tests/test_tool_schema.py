"""tests/test_tool_schema.py

Static TOOL_LIST schema validation for file-server and git-server tool definitions.

Validates every tool dict in the file-server and git-server TOOL_LIST exports against
the post-requirement-14 schema contract: name/description/inputSchema/status well-typed
and non-empty, config_dependent present as bool, and requires_config absent.

See also tests/test_mcp_tools_validation.py (requirement 14) for a broader-server,
narrower-field config_dependent/requires_config check across all 13 MCP tool modules;
this file is the authoritative full-field-set check for the 4 file+git modules only.
"""

from __future__ import annotations

import importlib
from typing import Any

import pytest

_SCHEM_MODULES: list[tuple[str, str]] = [
    ("mcp_servers.file.read_tools", "TOOL_LIST"),
    ("mcp_servers.file.write_tools", "TOOL_LIST"),
    ("mcp_servers.file.delete_tools", "TOOL_LIST"),
    ("mcp_servers.git.tools", "TOOL_LIST"),
]


@pytest.mark.parametrize("module_path, attr_name", _SCHEM_MODULES)
def test_static_schema_required_fields(module_path: str, attr_name: str) -> None:
    """Assert basic required fields exist and have correct types."""
    mod = importlib.import_module(module_path)
    tool_list: list[dict[str, Any]] = getattr(mod, attr_name)
    for tool in tool_list:
        assert isinstance(tool["name"], str) and tool["name"]
        assert isinstance(tool["description"], str) and tool["description"]
        assert isinstance(tool["inputSchema"], dict)
        assert isinstance(tool["status"], str) and tool["status"]


@pytest.mark.parametrize("module_path, attr_name", _SCHEM_MODULES)
def test_config_dependent_field_present_and_requires_config_absent(
    module_path: str, attr_name: str
) -> None:
    """Assert config_dependent is present as bool and requires_config is absent."""
    mod = importlib.import_module(module_path)
    tool_list: list[dict[str, Any]] = getattr(mod, attr_name)
    for tool in tool_list:
        assert "config_dependent" in tool
        assert isinstance(tool["config_dependent"], bool)
        assert "requires_config" not in tool
