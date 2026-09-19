"""tests/tools/test_generate_reference_table.py

Unit tests for tools/generate_reference_table.py's 3 new class/function
reference generators (agent/eventbus/memory), plus a regression test
confirming the pre-existing rag/mcp/deployment generators are unaffected.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tools.generate_reference_table import (
    generate_agent_reference_table,
    generate_deployment_reference_table,
    generate_eventbus_reference_table,
    generate_mcp_reference_table,
    generate_memory_reference_table,
    generate_rag_config_table,
)

_FIXTURE_MODULE = '''"""Fixture module for reference-table generator tests."""


class Widget:
    """A small, well-behaved widget."""

    def _private_helper(self) -> None:
        """Must not appear in the generated table."""


def build_widget(name: str, count: int = 1) -> "Widget":
    """Build a Widget instance."""
    return Widget()


def _private_function() -> None:
    """Must not appear in the generated table."""
'''


def test_agent_reference_table_extracts_public_symbols(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "widget.py").write_text(_FIXTURE_MODULE, encoding="utf-8")
    monkeypatch.setattr("tools.generate_reference_table.AGENT_DIR", tmp_path)
    table = generate_agent_reference_table()
    assert "`Widget`" in table
    assert "Build a Widget instance." in table
    assert "class Widget" in table
    assert "def build_widget(name, count)" in table
    assert "_private_helper" not in table
    assert "_private_function" not in table


def test_eventbus_reference_table_extracts_public_symbols(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "widget.py").write_text(_FIXTURE_MODULE, encoding="utf-8")
    monkeypatch.setattr("tools.generate_reference_table.EVENTBUS_DIR", tmp_path)
    table = generate_eventbus_reference_table()
    assert "`Widget`" in table
    assert "`build_widget`" in table


def test_memory_reference_table_extracts_public_symbols(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "widget.py").write_text(_FIXTURE_MODULE, encoding="utf-8")
    monkeypatch.setattr("tools.generate_reference_table.MEMORY_DIR", tmp_path)
    table = generate_memory_reference_table()
    assert "`Widget`" in table
    assert "`build_widget`" in table


def test_agent_reference_table_empty_directory_returns_header_only(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("tools.generate_reference_table.AGENT_DIR", tmp_path)
    table = generate_agent_reference_table()
    assert table == "| File | Class/Function | Signature | Summary |\n|---|---|---|---|"


def test_agent_reference_table_skips_private_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "_internal.py").write_text(_FIXTURE_MODULE, encoding="utf-8")
    monkeypatch.setattr("tools.generate_reference_table.AGENT_DIR", tmp_path)
    table = generate_agent_reference_table()
    assert "Widget" not in table


def test_agent_reference_table_skips_class_with_no_docstring(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "plain.py").write_text("class Plain:\n    pass\n", encoding="utf-8")
    monkeypatch.setattr("tools.generate_reference_table.AGENT_DIR", tmp_path)
    table = generate_agent_reference_table()
    assert "`Plain`" in table
    assert "class Plain" in table
    assert "| —" in table or " | — |" in table


# ---------------------------------------------------------------------------
# Regression: existing rag/mcp/deployment generators unaffected
# ---------------------------------------------------------------------------


def test_existing_generators_unaffected() -> None:
    assert generate_rag_config_table().startswith("| Key | Default | Description |")
    assert generate_mcp_reference_table().startswith(
        "| Server | Port | Tool Count | Tool Names |"
    )
    assert generate_deployment_reference_table().startswith(
        "| DB | Default path | Config key | Set in `agent.toml`? |"
    )
