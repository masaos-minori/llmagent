"""tests/test_mdq_tool_layer_consistency.py

Guardrail tests preventing MDQ tool-definition drift across the four
independent layers: schema (`tools.py`), runtime dispatch (`server.py`),
registry population (`tool_constants.py`), and their write/serial flags.
"""

from __future__ import annotations

from mcp_servers.mdq.mdq_server import _DISPATCH_TABLE
from mcp_servers.mdq.mdq_tools import TOOL_LIST
from shared.tool_constants import MDQ_TOOLS, MDQ_WRITE_TOOLS
from shared.tool_registry import get_registry


def test_tool_list_subset_of_dispatch_table() -> None:
    schema_names = {t["name"] for t in TOOL_LIST}
    assert schema_names <= set(_DISPATCH_TABLE)


def test_dispatch_table_subset_of_tool_list() -> None:
    schema_names = {t["name"] for t in TOOL_LIST}
    assert set(_DISPATCH_TABLE) <= schema_names


def test_mdq_tools_matches_tool_list() -> None:
    assert MDQ_TOOLS == {t["name"] for t in TOOL_LIST}


def test_mdq_tools_registered_in_registry() -> None:
    registry = get_registry()
    assert set(registry.get_tool_names("mdq")) == MDQ_TOOLS


def test_write_tools_flagged_is_write() -> None:
    for t in TOOL_LIST:
        if t["name"] in MDQ_WRITE_TOOLS:
            assert t.get("is_write") is True


def test_serial_tools_flagged_requires_serial() -> None:
    for t in TOOL_LIST:
        if t["name"] in MDQ_WRITE_TOOLS:
            assert t.get("requires_serial") is True
