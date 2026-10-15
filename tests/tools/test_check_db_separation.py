"""Tests for tools/check_db_separation.py."""

from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

from tools import check_db_separation as mod


def _ddl() -> dict[str, str]:
    return dict(mod._schema_ddl())


def test_live_repository_has_no_violations() -> None:
    assert mod.run_checks() == []


def test_detects_table_in_wrong_database() -> None:
    ddl = _ddl()
    ddl["eventbus"] += "\nCREATE TABLE IF NOT EXISTS tasks (id INTEGER);"
    problems = mod.check_table_ownership(ddl)
    assert any("belongs to workflow.sqlite" in p for p in problems)


def test_detects_unregistered_table() -> None:
    ddl = _ddl()
    ddl["rag"] += "\nCREATE TABLE IF NOT EXISTS extra (id INTEGER);"
    problems = mod.check_table_ownership(ddl)
    assert any("not in the inventory" in p for p in problems)


def test_detects_cross_db_foreign_key() -> None:
    ddl = _ddl()
    ddl["session"] += (
        "\nCREATE TABLE IF NOT EXISTS x (d INTEGER REFERENCES documents(doc_id));"
    )
    problems = mod.check_table_ownership(ddl)
    assert any("[cross-db-fk]" in p and "rag.sqlite" in p for p in problems)


def test_detects_vec0_outside_inventory() -> None:
    ddl = _ddl()
    ddl["workflow"] += (
        "\nCREATE VIRTUAL TABLE IF NOT EXISTS v USING vec0(id INTEGER PRIMARY KEY);"
    )
    problems = mod.check_table_ownership(ddl)
    assert any("[vec-scope] vec0 table 'v'" in p for p in problems)


def test_detects_shared_physical_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cfg = tmp_path / "config"
    cfg.mkdir()
    (cfg / "agent.toml").write_text(
        'rag_db_path = "/d/rag.sqlite"\nsession_db_path = "/d/rag.sqlite"\n',
        encoding="utf-8",
    )
    monkeypatch.setattr(mod, "CONFIG_DIR", cfg)
    monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
    problems = mod.check_db_paths()
    assert any("point to the same file" in p for p in problems)
    assert any("session_db_path" in p and "session.sqlite" in p for p in problems)


def test_detects_attach_and_qualified_access(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    (scripts / "bad.py").write_text(
        '"""Docstring: FROM rag.x is ignored."""\n'
        "A = \"ATTACH DATABASE 'x.db' AS other\"\n"
        'B = "SELECT * FROM rag.documents JOIN session.sessions"\n',
        encoding="utf-8",
    )
    monkeypatch.setattr(mod, "SCRIPTS_DIR", scripts)
    monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
    problems = mod.check_cross_db_access()
    assert any("ATTACH statement" in p for p in problems)
    assert any("schema-qualified" in p for p in problems)
    assert len(problems) == 2
