"""tests/shared/test_runtime_tool.py
Unit tests for RuntimeTool: field normalization, safe-default application, and immutability.
"""

from __future__ import annotations

import ast
import dataclasses
from pathlib import Path
from typing import Any

import pytest
from shared.runtime_tool import RuntimeTool, build_runtime_tool

from tests.shared.runtime_tool_factory import build_fixture_runtime_tool


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
            resource_scope_kind="filesystem",
            resource_scope_keys=("path",),
            agent_safety_tier="WRITE_DANGEROUS",
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
        assert tool.resource_scope_kind == "filesystem"
        assert tool.resource_scope_keys == ("path",)
        assert tool.agent_safety_tier == "WRITE_DANGEROUS"
        assert tool.enabled_for_llm is True

    def test_safe_defaults_when_unannotated(self) -> None:
        tool = build_fixture_runtime_tool(name="unknown_tool", server_key="srv")
        assert tool.agent_safety_tier == "WRITE_DANGEROUS"
        assert tool.enabled_for_llm is False
        # requires_serial defaults to True because is_write was also unannotated
        assert tool.requires_serial is True
        # is_write itself defaults to False per this module's stated decision
        assert tool.is_write is False

    def test_requires_serial_false_when_is_write_explicitly_false(self) -> None:
        tool = build_fixture_runtime_tool(
            name="read_text_file", server_key="fs", is_write=False
        )
        assert tool.is_write is False
        # explicit is_write=False removes the uncertainty, so requires_serial defaults False
        assert tool.requires_serial is False

    def test_requires_serial_explicit_override_wins(self) -> None:
        tool = build_fixture_runtime_tool(
            name="t", server_key="s", is_write=False, requires_serial=True
        )
        # explicit requires_serial value always wins over the derived default
        assert tool.requires_serial is True

    def test_is_frozen(self) -> None:
        name, server_key = _minimal_kwargs()
        tool = build_fixture_runtime_tool(name=name, server_key=server_key)
        with pytest.raises(dataclasses.FrozenInstanceError):
            tool.name = "changed"  # type: ignore[misc]

    def test_input_schema_and_raw_definition_default_to_empty_dict_not_shared_object(
        self,
    ) -> None:
        a = build_fixture_runtime_tool(name="a", server_key="s")
        b = build_fixture_runtime_tool(name="b", server_key="s")
        assert a.input_schema == {}
        assert b.input_schema == {}
        assert a.input_schema is not b.input_schema  # no shared mutable default
        assert a.raw_definition == {}
        assert b.raw_definition == {}
        assert a.raw_definition is not b.raw_definition  # no shared mutable default

    def test_capabilities_defaults_to_empty_tuple(self) -> None:
        tool = build_fixture_runtime_tool(name="t", server_key="s")
        assert tool.capabilities == ()

    def test_capabilities_stored_as_tuple_from_sequence(self) -> None:
        tool = build_fixture_runtime_tool(
            name="t", server_key="s", capabilities=("read", "write")
        )
        assert tool.capabilities == ("read", "write")

    def test_resource_scope_kind_defaults_to_empty_string(self) -> None:
        tool = build_fixture_runtime_tool(name="t", server_key="s")
        assert tool.resource_scope_kind == ""

    def test_resource_scope_keys_defaults_to_empty_tuple(self) -> None:
        tool = build_fixture_runtime_tool(name="t", server_key="s")
        assert tool.resource_scope_keys == ()

    def test_resource_scope_keys_stored_as_tuple_from_sequence(self) -> None:
        tool = build_fixture_runtime_tool(
            name="t", server_key="s", resource_scope_keys=("path", "destination")
        )
        assert tool.resource_scope_keys == ("path", "destination")

    def test_allow_extra_fields_defaults_to_false(self) -> None:
        tool = build_fixture_runtime_tool(name="t", server_key="s")
        assert tool.allow_extra_fields is False

    def test_allow_extra_fields_explicit_true_is_honored(self) -> None:
        tool = build_fixture_runtime_tool(
            name="t", server_key="s", allow_extra_fields=True
        )
        assert tool.allow_extra_fields is True

    def test_allow_extra_fields_explicit_false_is_honored(self) -> None:
        tool = build_fixture_runtime_tool(
            name="t", server_key="s", allow_extra_fields=False
        )
        assert tool.allow_extra_fields is False

    def test_llm_visibility_base_defaults_to_mirroring_enabled_for_llm(self) -> None:
        tool = build_fixture_runtime_tool(name="t", server_key="s")
        assert tool.llm_visibility_base is False

        tool_enabled = build_fixture_runtime_tool(
            name="t", server_key="s", enabled_for_llm=True
        )
        assert tool_enabled.llm_visibility_base is True

    def test_llm_visibility_base_explicit_override(self) -> None:
        tool = build_fixture_runtime_tool(
            name="t", server_key="s", llm_visibility_base=True
        )
        assert tool.llm_visibility_base is True

        tool_disabled = build_fixture_runtime_tool(
            name="t", server_key="s", llm_visibility_base=False
        )
        assert tool_disabled.llm_visibility_base is False

    def test_llm_visibility_base_preserved_under_replace(self) -> None:
        tool = build_fixture_runtime_tool(
            name="t", server_key="s", enabled_for_llm=True, llm_visibility_base=False
        )
        replaced = dataclasses.replace(tool, description="new desc")
        assert replaced.llm_visibility_base is False
        assert replaced.enabled_for_llm is True


_STRICT_FIELDS = (
    "is_write",
    "requires_serial",
    "resource_scope_kind",
    "resource_scope_keys",
)


def _full_kwargs() -> dict[str, object]:
    """Keyword arguments carrying all four required execution metadata fields."""
    return {
        "name": "t",
        "server_key": "s",
        "is_write": False,
        "requires_serial": True,
        "resource_scope_kind": "",
        "resource_scope_keys": (),
    }


class TestStrictBuilder:
    """Fail-closed contracts for `build_runtime_tool` (row 01 of the rtool008 batch).

    These tests run red until row 01 lands; the permissive builder currently
    accepts omitted and `None` values (procedure ordering note).
    """

    @pytest.mark.parametrize("field", _STRICT_FIELDS)
    def test_strict_builder_rejects_each_missing_required_field(
        self, field: str
    ) -> None:
        kwargs: dict[str, Any] = {k: v for k, v in _full_kwargs().items() if k != field}
        with pytest.raises(TypeError):
            build_runtime_tool(**kwargs)

    @pytest.mark.parametrize("field", _STRICT_FIELDS)
    def test_strict_builder_rejects_none_for_each_required_field(
        self, field: str
    ) -> None:
        kwargs: dict[str, Any] = dict(_full_kwargs())
        kwargs[field] = None
        with pytest.raises(ValueError):
            build_runtime_tool(**kwargs)


class TestFixtureBuilderEquivalence:
    def test_fixture_builder_matches_the_old_permissive_defaults(self) -> None:
        omitted = build_fixture_runtime_tool(name="t", server_key="s")
        assert omitted.is_write is False
        assert omitted.requires_serial is True
        assert omitted.resource_scope_kind == ""
        assert omitted.resource_scope_keys == ()

        explicit_write = build_fixture_runtime_tool(
            name="t", server_key="s", is_write=True
        )
        assert explicit_write.is_write is True
        assert explicit_write.requires_serial is False

        explicit_read = build_fixture_runtime_tool(
            name="t", server_key="s", is_write=False
        )
        assert explicit_read.is_write is False
        assert explicit_read.requires_serial is False

        strict = build_runtime_tool(**_full_kwargs())  # type: ignore[arg-type]
        assert omitted == strict


def test_scripts_do_not_import_the_fixture_builder() -> None:
    scripts_dir = Path(__file__).resolve().parents[2] / "scripts"
    offenders: list[str] = []
    for path in sorted(scripts_dir.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.ImportFrom)
                and node.module
                and node.module.startswith("tests.")
            ):
                offenders.append(f"{path}: from {node.module}")
            elif isinstance(node, ast.Import):
                offenders.extend(
                    f"{path}: import {alias.name}"
                    for alias in node.names
                    if alias.name.startswith("tests.")
                )
    assert offenders == []
