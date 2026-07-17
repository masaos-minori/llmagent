"""tests/shared/test_runtime_tool.py
Unit tests for RuntimeTool: field normalization, safe-default application, and immutability.
"""

from __future__ import annotations

import dataclasses

import pytest
from shared.runtime_tool import RuntimeTool, build_runtime_tool


def _minimal_kwargs() -> tuple[str, str]:
    """Minimum required positional args for build_runtime_tool(): (name, server_key)."""
    return "t", "s"


class TestRuntimeTool:
    def test_construct_with_full_annotation(self) -> None:
        tool: RuntimeTool = build_runtime_tool(
            name="delete_file",
            server_key="fs",
            server_url="http://x",
            description="desc",
            input_schema={"type": "object"},
            raw_definition={"name": "delete_file"},
            status="active",
            is_write=True,
            requires_serial=True,
            resource_scope="delete_file",
            agent_safety_tier="WRITE_DANGEROUS",
            requires_approval=True,
            enabled_for_llm=True,
        )
        assert tool.name == "delete_file"
        assert tool.server_key == "fs"
        assert tool.server_url == "http://x"
        assert tool.description == "desc"
        assert tool.input_schema == {"type": "object"}
        assert tool.raw_definition == {"name": "delete_file"}
        assert tool.status == "active"
        assert tool.is_write is True
        assert tool.requires_serial is True
        assert tool.resource_scope == "delete_file"
        assert tool.agent_safety_tier == "WRITE_DANGEROUS"
        assert tool.requires_approval is True
        assert tool.enabled_for_llm is True

    def test_safe_defaults_when_unannotated(self) -> None:
        tool = build_runtime_tool(name="unknown_tool", server_key="srv")
        assert tool.agent_safety_tier == "WRITE_DANGEROUS"
        assert tool.requires_approval is True
        assert tool.enabled_for_llm is False
        # requires_serial defaults to True because is_write was also unannotated
        assert tool.requires_serial is True
        # is_write itself defaults to False per this module's stated decision
        assert tool.is_write is False

    def test_requires_serial_false_when_is_write_explicitly_false(self) -> None:
        tool = build_runtime_tool(
            name="read_text_file", server_key="fs", is_write=False
        )
        assert tool.is_write is False
        # explicit is_write=False removes the uncertainty, so requires_serial defaults False
        assert tool.requires_serial is False

    def test_requires_serial_explicit_override_wins(self) -> None:
        tool = build_runtime_tool(
            name="t", server_key="s", is_write=False, requires_serial=True
        )
        # explicit requires_serial value always wins over the derived default
        assert tool.requires_serial is True

    def test_is_frozen(self) -> None:
        name, server_key = _minimal_kwargs()
        tool = build_runtime_tool(name=name, server_key=server_key)
        with pytest.raises(dataclasses.FrozenInstanceError):
            tool.name = "changed"  # type: ignore[misc]

    def test_input_schema_and_raw_definition_default_to_empty_dict_not_shared_object(
        self,
    ) -> None:
        a = build_runtime_tool(name="a", server_key="s")
        b = build_runtime_tool(name="b", server_key="s")
        assert a.input_schema == {}
        assert b.input_schema == {}
        assert a.input_schema is not b.input_schema  # no shared mutable default
        assert a.raw_definition == {}
        assert b.raw_definition == {}
        assert a.raw_definition is not b.raw_definition  # no shared mutable default
