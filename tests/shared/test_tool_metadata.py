"""tests/shared/test_tool_metadata.py

Contract tests for the closed policy vocabulary in shared/tool_metadata.py (T-01):
each dimension is a closed value set matching its Literal alias, the field-set
version is a single constant, and the module imports nothing from `agent`.
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

import pytest
import shared.tool_metadata as tool_metadata
from shared.tool_metadata import (
    PREVIEW_CAPABILITY_VALUES,
    RECONCILIATION_POLICY_VALUES,
    RESOURCE_KEY_KIND_VALUES,
    RETRY_POLICY_VALUES,
    SIDE_EFFECT_CLASS_VALUES,
    TOOL_FIELD_SET_VERSION,
    PreviewCapability,
    ReconciliationPolicy,
    ResourceKeyKind,
    RetryPolicy,
    SideEffectClass,
)

_MODULE_PATH = (
    Path(__file__).resolve().parents[2] / "scripts" / "shared" / "tool_metadata.py"
)

_CLOSED_SETS: list[tuple[Any, frozenset[str]]] = [
    (SideEffectClass, SIDE_EFFECT_CLASS_VALUES),
    (RetryPolicy, RETRY_POLICY_VALUES),
    (ReconciliationPolicy, RECONCILIATION_POLICY_VALUES),
    (ResourceKeyKind, RESOURCE_KEY_KIND_VALUES),
    (PreviewCapability, PREVIEW_CAPABILITY_VALUES),
]


@pytest.mark.parametrize(("alias", "value_set"), _CLOSED_SETS)
def test_closed_value_sets_match_their_literal_aliases(
    alias: Any, value_set: frozenset[str]
) -> None:
    assert isinstance(value_set, frozenset)
    assert value_set == frozenset(alias.__args__)


def test_resource_key_kind_includes_non_escalating() -> None:
    expected = {"path", "branch", "repo", "issue", "pull_request", "non_escalating"}
    assert expected == RESOURCE_KEY_KIND_VALUES


def test_field_set_version_is_the_only_version_constant() -> None:
    assert TOOL_FIELD_SET_VERSION == "2.1"
    version_attributes = [
        name for name in vars(tool_metadata) if name.endswith("_VERSION")
    ]
    assert version_attributes == ["TOOL_FIELD_SET_VERSION"]


def test_module_imports_nothing_from_agent() -> None:
    tree = ast.parse(_MODULE_PATH.read_text(encoding="utf-8"))
    offenders: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            if node.module.split(".")[0] == "agent":
                offenders.append(f"from {node.module}")
        elif isinstance(node, ast.Import):
            offenders.extend(
                f"import {alias.name}"
                for alias in node.names
                if alias.name.split(".")[0] == "agent"
            )
    assert offenders == []
