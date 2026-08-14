"""tests/shared/test_tool_spec.py
Unit tests for ToolSpec: default construction and multi-scope construction.
"""

from __future__ import annotations

import dataclasses

import pytest
from shared.tool_spec import ToolSpec


class TestToolSpec:
    def test_default_construction_has_empty_resource_scopes_and_safe_defaults(
        self,
    ) -> None:
        spec = ToolSpec(call_id="c1", name="read_file")
        assert spec.args == {}
        assert spec.resource_scopes == ()
        assert spec.requires_serial is False
        assert spec.is_write is False

    def test_explicit_multi_scope_construction(self) -> None:
        spec = ToolSpec(
            call_id="c2",
            name="move_file",
            args={"source": "/a", "destination": "/b"},
            resource_scopes=("filesystem:/a", "filesystem:/b"),
            requires_serial=True,
            is_write=True,
        )
        assert spec.resource_scopes == ("filesystem:/a", "filesystem:/b")
        assert spec.call_id == "c2"
        assert spec.name == "move_file"
        assert spec.args == {"source": "/a", "destination": "/b"}
        assert spec.requires_serial is True
        assert spec.is_write is True

    def test_args_default_factory_not_shared_across_instances(self) -> None:
        a = ToolSpec(call_id="c1", name="read_file")
        b = ToolSpec(call_id="c2", name="read_file")
        assert a.args == {}
        assert b.args == {}
        assert a.args is not b.args

    def test_is_frozen(self) -> None:
        spec = ToolSpec(call_id="c1", name="read_file")
        with pytest.raises(dataclasses.FrozenInstanceError):
            spec.name = "changed"  # type: ignore[misc]
