"""tests/test_workflow_schema.py
Unit tests for db/workflow_schema.py — init_schema creates the 5 required tables.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest
from db.workflow_schema import init_schema


@pytest.fixture()
def workflow_db(tmp_path: Path) -> Path:
    from unittest.mock import patch

    from db.config import DbConfig

    db_path = tmp_path / "workflow.sqlite"
    rag_path = tmp_path / "rag.sqlite"
    session_path = tmp_path / "session.sqlite"
    with patch(
        "db.helper.build_db_config",
        return_value=DbConfig(
            rag_db_path=str(rag_path),
            session_db_path=str(session_path),
            workflow_db_path=str(db_path),
        ),
    ):
        init_schema()
    return db_path


class TestInitSchema:
    def test_creates_all_tables(self, workflow_db: Path) -> None:
        conn = sqlite3.connect(str(workflow_db))
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        conn.close()
        assert {
            "tasks",
            "attempts",
            "processed_events",
            "artifacts",
            "approvals",
        } <= tables

    def test_idempotent_second_call(self, workflow_db: Path) -> None:
        init_schema()  # must not raise

    def test_tasks_idempotency_key_unique(self, workflow_db: Path) -> None:
        conn = sqlite3.connect(str(workflow_db))
        now = "2026-01-01T00:00:00+00:00"
        conn.execute(
            "INSERT INTO tasks VALUES (?,?,?,?,?,?,?,?,?)",
            ("t1", "s1", None, 1, "1.0.0", "pending", "s1:1", now, now),
        )
        conn.commit()
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO tasks VALUES (?,?,?,?,?,?,?,?,?)",
                ("t2", "s1", None, 1, "1.0.0", "pending", "s1:1", now, now),
            )
            conn.commit()
        conn.close()

    def test_attempts_foreign_key_cascade(self, workflow_db: Path) -> None:
        conn = sqlite3.connect(str(workflow_db))
        conn.execute("PRAGMA foreign_keys=ON")
        now = "2026-01-01T00:00:00+00:00"
        conn.execute(
            "INSERT INTO tasks VALUES (?,?,?,?,?,?,?,?,?)",
            ("t1", "s1", None, 1, "1.0.0", "pending", "s1:1", now, now),
        )
        conn.execute(
            "INSERT INTO attempts VALUES (?,?,?,?,?,?,?)",
            ("a1", "t1", "plan", "running", now, None, None),
        )
        conn.commit()
        conn.execute("DELETE FROM tasks WHERE task_id='t1'")
        conn.commit()
        rows = conn.execute("SELECT * FROM attempts WHERE attempt_id='a1'").fetchall()
        assert rows == []
        conn.close()
