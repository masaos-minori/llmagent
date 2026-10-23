"""tests/agent/test_session_persister.py

SessionPersister: the write-or-skip gate and failure containment.

The gate is checked against a real in-memory ``session_diagnostics`` table with
row-count assertions, so a skipped write cannot be satisfied by accident.
"""

from __future__ import annotations

import logging
import sqlite3
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from agent.diagnostic_store import DiagnosticStore
from agent.session_persister import SessionPersister

_SCHEMA = """
CREATE TABLE session_diagnostics (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id  INTEGER,
    kind        TEXT NOT NULL,
    content     TEXT NOT NULL,
    workflow_id TEXT,
    task_id     TEXT,
    created_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);
"""


class _MemDb:
    """Minimal SQLiteHelper stand-in over one in-memory connection."""

    def __init__(self) -> None:
        self.conn = sqlite3.connect(":memory:")
        self.conn.executescript(_SCHEMA)

    def open(self, **_: object) -> _MemDb:
        return self

    def __enter__(self) -> _MemDb:
        return self

    def __exit__(self, *_: object) -> None:
        pass

    def execute(self, sql: str, params: tuple = ()) -> sqlite3.Cursor:
        return self.conn.execute(sql, params)

    def fetchall(self, sql: str, params: tuple = ()) -> list:
        return self.conn.execute(sql, params).fetchall()

    def commit(self) -> None:
        self.conn.commit()

    def count(self) -> int:
        return int(
            self.conn.execute("SELECT COUNT(*) FROM session_diagnostics").fetchone()[0]
        )


@pytest.fixture
def db():
    mem = _MemDb()
    with (
        patch("agent.diagnostic_store.SQLiteHelper", return_value=mem),
        patch("agent.workflow.state_store.StateStore", side_effect=RuntimeError),
        patch.object(
            DiagnosticStore,
            "_load_diagnostics_config",
            return_value=MagicMock(
                encryption_key="", retention_days=30, sensitive_fields=frozenset()
            ),
        ),
    ):
        yield mem


def _ctx(session_id: int | None) -> MagicMock:
    ctx = MagicMock()
    ctx.session.session_id = session_id
    ctx.stats.stat_latency = {}
    ctx.stats.stat_turns = 3
    ctx.stats.stat_tool_calls = 1
    ctx.stats.stat_tool_errors = 0
    ctx.stats.stat_partial_completions = 0
    ctx.stats.stat_input_tokens = 10
    ctx.stats.stat_output_tokens = 5
    ctx.services = None
    ctx.conv.history = []
    return ctx


class TestPersistSessionDiagnosticsGate:
    @pytest.mark.asyncio
    async def test_skips_write_when_no_session(self, db, caplog) -> None:
        view = MagicMock()
        persister = SessionPersister(_ctx(None), DiagnosticStore(), view)

        with caplog.at_level(logging.INFO, logger="agent.session_persister"):
            await persister.persist_session_diagnostics()

        assert db.count() == 0
        assert "no started session" in caplog.text
        view.write_warning.assert_not_called()

    @pytest.mark.asyncio
    async def test_writes_row_when_session_exists(self, db) -> None:
        persister = SessionPersister(_ctx(1), DiagnosticStore(), MagicMock())

        await persister.persist_session_diagnostics()

        rows = db.conn.execute("SELECT session_id, kind FROM session_diagnostics")
        assert rows.fetchall() == [(1, "session_summary")]

    @pytest.mark.asyncio
    async def test_store_accepts_null_session_id_directly(self, db) -> None:
        persister = SessionPersister(_ctx(None), DiagnosticStore(), MagicMock())
        await persister.persist_session_diagnostics()
        assert db.count() == 0

        DiagnosticStore().save(None, kind="session_summary", content="{}")

        assert db.count() == 1


class TestPersistSessionDiagnosticsContainment:
    @pytest.mark.asyncio
    async def test_payload_defect_is_reported_and_does_not_escape(self, db) -> None:
        ctx = _ctx(1)
        ctx.stats.stat_turns = MagicMock()  # not JSON serializable
        view = MagicMock()
        persister = SessionPersister(ctx, DiagnosticStore(), view)

        await persister.persist_session_diagnostics()

        view.write_warning.assert_called_once()
        assert "Session persistence failed" in view.write_warning.call_args[0][0]
        assert db.count() == 0

    @pytest.mark.asyncio
    async def test_store_failure_is_reported_and_does_not_escape(self, db) -> None:
        store = DiagnosticStore()
        view = MagicMock()
        persister = SessionPersister(_ctx(1), store, view)

        with patch.object(store, "save", side_effect=RuntimeError("store down")):
            await persister.persist_session_diagnostics()

        view.write_warning.assert_called_once()
        assert "store down" in view.write_warning.call_args[0][0]


class TestPersistSessionMemoriesGate:
    @pytest.mark.asyncio
    async def test_skips_ingestion_when_no_session(self, caplog) -> None:
        ctx = _ctx(None)
        ctx.services = MagicMock()
        ctx.services.memory.on_session_stop = AsyncMock()
        persister = SessionPersister(ctx, MagicMock(), MagicMock())

        with caplog.at_level(logging.INFO, logger="agent.session_persister"):
            await persister.persist_session_memories()

        ctx.services.memory.on_session_stop.assert_not_called()
        assert "no started session" in caplog.text

    @pytest.mark.asyncio
    async def test_writes_when_session_exists(self) -> None:
        ctx = _ctx(1)
        ctx.services = MagicMock()
        ctx.services.memory.on_session_stop = AsyncMock()
        persister = SessionPersister(ctx, MagicMock(), MagicMock())

        await persister.persist_session_memories()

        ctx.services.memory.on_session_stop.assert_awaited_once()
