"""tests/test_workflow_schema.py
Unit tests for db/workflow_schema.py — init_schema creates the 5 required tables.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest
from db.workflow_schema import init_schema


class TestInitSchema:
    def test_creates_all_tables(self, tmp_path: Path) -> None:
        db_path = str(tmp_path / "workflow.sqlite")
        init_schema(db_path)
        conn = sqlite3.connect(db_path)
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

    def test_idempotent_second_call(self, tmp_path: Path) -> None:
        db_path = str(tmp_path / "workflow.sqlite")
        init_schema(db_path)
        init_schema(db_path)  # must not raise

    def test_tasks_idempotency_key_unique(self, tmp_path: Path) -> None:
        db_path = str(tmp_path / "workflow.sqlite")
        init_schema(db_path)
        conn = sqlite3.connect(db_path)
        now = "2026-01-01T00:00:00+00:00"
        conn.execute(
            "INSERT INTO tasks VALUES (?,?,?,?,?,?,?,?)",
            ("t1", "s1", 1, "1.0.0", "pending", "s1:1", now, now),
        )
        conn.commit()
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO tasks VALUES (?,?,?,?,?,?,?,?)",
                ("t2", "s1", 1, "1.0.0", "pending", "s1:1", now, now),
            )
            conn.commit()
        conn.close()

    def test_attempts_foreign_key_cascade(self, tmp_path: Path) -> None:
        db_path = str(tmp_path / "workflow.sqlite")
        init_schema(db_path)
        conn = sqlite3.connect(db_path)
        conn.execute("PRAGMA foreign_keys=ON")
        now = "2026-01-01T00:00:00+00:00"
        conn.execute(
            "INSERT INTO tasks VALUES (?,?,?,?,?,?,?,?)",
            ("t1", "s1", 1, "1.0.0", "pending", "s1:1", now, now),
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
