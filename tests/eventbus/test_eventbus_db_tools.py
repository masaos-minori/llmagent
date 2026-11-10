"""tests/eventbus/test_eventbus_db_tools.py

EventBus-owned database tool: path resolution from the EventBus configuration only,
create-or-validate, refusal of stale databases, verified archives, and the CLI.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest
from eventbus import db_tools


@pytest.fixture
def db_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Point EVENTBUS_CONFIG_PATH at a minimal eventbus.toml owning a tmp db_path."""
    path = tmp_path / "db" / "eventbus.sqlite"
    config = tmp_path / "eventbus.toml"
    config.write_text(f'db_path = "{path}"\n', encoding="utf-8")
    monkeypatch.setenv("EVENTBUS_CONFIG_PATH", str(config))
    for name in ("EVENTBUS_AUTH_TOKEN", "LLMAGENT_CONFIG_DIR"):
        monkeypatch.delenv(name, raising=False)
    return path


def _state(path: Path) -> tuple[int, list[tuple[str, str]]]:
    conn = sqlite3.connect(path)
    try:
        version = int(conn.execute("PRAGMA user_version").fetchone()[0])
        rows = conn.execute(
            "SELECT type, sql FROM sqlite_master ORDER BY type, name"
        ).fetchall()
    finally:
        conn.close()
    return version, [(str(r[0]), str(r[1])) for r in rows]


class TestReadDbPath:
    def test_reads_db_path_without_token_variables(self, db_path: Path) -> None:
        assert db_tools.read_db_path() == db_path

    def test_does_not_consult_agent_toml(
        self, db_path: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        agent_dir = tmp_path / "agent_cfg"
        agent_dir.mkdir()
        (agent_dir / "agent.toml").write_text(
            'eventbus_db_path = "/should/not/be/used.sqlite"\n', encoding="utf-8"
        )
        monkeypatch.setenv("LLMAGENT_CONFIG_DIR", str(agent_dir))
        assert db_tools.read_db_path() == db_path

    @pytest.mark.parametrize("body", ["", 'db_path = ""\n', "db_path = 5\n"])
    def test_rejects_missing_or_invalid_db_path(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, body: str
    ) -> None:
        config = tmp_path / "eventbus.toml"
        config.write_text(body, encoding="utf-8")
        monkeypatch.setenv("EVENTBUS_CONFIG_PATH", str(config))
        with pytest.raises(ValueError, match="db_path"):
            db_tools.read_db_path()

    def test_rejects_unreadable_config(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("EVENTBUS_CONFIG_PATH", str(tmp_path / "missing.toml"))
        with pytest.raises(ValueError, match="cannot read"):
            db_tools.read_db_path()


class TestEnsure:
    def test_creates_fresh_database_and_accepts_current(self, db_path: Path) -> None:
        assert db_tools.ensure() == db_path
        version, rows = _state(db_path)
        assert version == db_tools.schema_version()
        assert any(r[0] == "table" for r in rows)
        db_tools.ensure()
        assert _state(db_path) == (version, rows)

    def test_refuses_stale_version(self, db_path: Path) -> None:
        db_tools.ensure()
        conn = sqlite3.connect(db_path)
        conn.execute(f"PRAGMA user_version = {db_tools.schema_version() - 1}")
        conn.commit()
        conn.close()
        before = _state(db_path)
        with pytest.raises(RuntimeError, match="does not match the current schema"):
            db_tools.ensure()
        assert _state(db_path) == before

    def test_refuses_unstamped_existing_database(self, db_path: Path) -> None:
        db_tools.ensure()
        conn = sqlite3.connect(db_path)
        conn.execute("PRAGMA user_version = 0")
        conn.commit()
        conn.close()
        before = _state(db_path)
        with pytest.raises(RuntimeError, match="user_version 0"):
            db_tools.ensure()
        assert _state(db_path) == before

    def test_refuses_shape_drift_at_current_version(self, db_path: Path) -> None:
        db_tools.ensure()
        conn = sqlite3.connect(db_path)
        conn.execute("ALTER TABLE events ADD COLUMN extra TEXT")
        conn.commit()
        conn.close()
        before = _state(db_path)
        with pytest.raises(RuntimeError, match="differ|missing|unexpected"):
            db_tools.ensure()
        assert _state(db_path) == before


class TestCreatedSchemaContent:
    """The database ensure() creates carries the delivery tables and event columns
    the service relies on (moved from the Agent-side create_schema tests)."""

    def _tables(self, path: Path) -> set[str]:
        conn = sqlite3.connect(path)
        try:
            rows = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        finally:
            conn.close()
        return {str(r[0]) for r in rows}

    def test_delivery_and_offset_tables_exist(self, db_path: Path) -> None:
        db_tools.ensure()
        assert {"events", "consumer_delivery", "consumer_offsets"} <= self._tables(
            db_path
        )

    def test_events_table_has_redelivered_from_column(self, db_path: Path) -> None:
        db_tools.ensure()
        conn = sqlite3.connect(db_path)
        try:
            columns = {row[1] for row in conn.execute("PRAGMA table_info(events)")}
        finally:
            conn.close()
        assert "redelivered_from" in columns


class TestVerifyAndRotate:
    def test_verify_accepts_canonical_database(self, db_path: Path) -> None:
        db_tools.ensure()
        assert db_tools.verify() == db_path

    def test_verify_rejects_missing_database(self, db_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            db_tools.verify()

    def test_verify_rejects_shape_drift(self, db_path: Path) -> None:
        db_tools.ensure()
        conn = sqlite3.connect(db_path)
        conn.execute("ALTER TABLE events ADD COLUMN extra TEXT")
        conn.commit()
        conn.close()
        with pytest.raises(RuntimeError):
            db_tools.verify()

    def test_verify_rejects_a_file_that_is_not_a_database(self, db_path: Path) -> None:
        db_path.parent.mkdir(parents=True)
        db_path.write_bytes(b"not a sqlite database" * 64)
        with pytest.raises(RuntimeError):
            db_tools.verify()

    def test_rotate_writes_verified_archive(
        self, db_path: Path, tmp_path: Path
    ) -> None:
        db_tools.ensure()
        archive = db_tools.rotate(tmp_path / "arch")
        assert archive.parent == tmp_path / "arch"
        assert archive.name.startswith(f"{db_path.stem}_")
        assert archive.suffix == db_path.suffix
        assert db_tools.verify(archive) == archive

    def test_rotate_defaults_next_to_database(self, db_path: Path) -> None:
        db_tools.ensure()
        archive = db_tools.rotate()
        assert archive.parent == db_path.parent / "archive"

    def test_rotate_rejects_missing_source(self, db_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            db_tools.rotate()


class TestCli:
    def test_path_and_version(
        self, db_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        assert db_tools.main(["path"]) == 0
        assert capsys.readouterr().out.strip() == str(db_path)
        assert db_tools.main(["version"]) == 0
        assert capsys.readouterr().out.strip() == str(db_tools.schema_version())

    def test_ensure_then_verify_then_rotate(
        self, db_path: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        assert db_tools.main(["ensure"]) == 0
        assert db_tools.main(["verify"]) == 0
        assert db_tools.main(["rotate", "--archive-dir", str(tmp_path / "a")]) == 0
        assert str(tmp_path / "a") in capsys.readouterr().out

    def test_errors_return_exit_code_one(
        self, db_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        assert db_tools.main(["verify"]) == 1
        assert "eventbus.db_tools verify" in capsys.readouterr().err
