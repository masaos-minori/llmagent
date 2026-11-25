"""tests/agent/test_session_persister.py

SessionPersister: the write-or-skip gate and failure containment.

The gate is checked against a real in-memory ``session_diagnostics`` table with
row-count assertions, so a skipped write cannot be satisfied by accident.
"""

from __future__ import annotations

import logging
import sqlite3
import time
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import orjson
import pytest
from agent.config_dataclasses import DiagnosticsConfig
from agent.diagnostic_store import DiagnosticStore
from agent.session_persister import SessionPersistenceSnapshot, SessionPersister
from agent.workflow.state_store import StateStore

from tests.agent._config_test_defaults import MIN_DB_CONFIG

_SCHEMA = """
CREATE TABLE session_diagnostics (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id  INTEGER,
    kind        TEXT NOT NULL,
    content     TEXT NOT NULL,
    workflow_id TEXT,
    task_id     TEXT,
    storage_format TEXT NOT NULL DEFAULT 'plaintext',
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
    ):
        yield mem


def _ctx(session_id: int | None) -> MagicMock:
    ctx = MagicMock()
    ctx.session.session_id = session_id
    ctx.session.generation = 4
    ctx.session.memory_finalized_count.return_value = 0
    ctx.turn.current_turn_id = "turn-1"
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
        persister = SessionPersister(
            _ctx(None),
            DiagnosticStore(DiagnosticsConfig(), db_config=MIN_DB_CONFIG),
            view,
        )

        with caplog.at_level(logging.INFO, logger="agent.session_persister"):
            await persister.persist_session_diagnostics()

        assert db.count() == 0
        assert "no started session" in caplog.text
        view.write_warning.assert_not_called()

    @pytest.mark.asyncio
    async def test_writes_row_when_session_exists(self, db) -> None:
        persister = SessionPersister(
            _ctx(1),
            DiagnosticStore(DiagnosticsConfig(), db_config=MIN_DB_CONFIG),
            MagicMock(),
        )

        await persister.persist_session_diagnostics()

        rows = db.conn.execute("SELECT session_id, kind FROM session_diagnostics")
        assert rows.fetchall() == [(1, "session_summary")]

    @pytest.mark.asyncio
    async def test_store_accepts_null_session_id_directly(self, db) -> None:
        persister = SessionPersister(
            _ctx(None),
            DiagnosticStore(DiagnosticsConfig(), db_config=MIN_DB_CONFIG),
            MagicMock(),
        )
        await persister.persist_session_diagnostics()
        assert db.count() == 0

        DiagnosticStore(DiagnosticsConfig(), db_config=MIN_DB_CONFIG).save(
            None, kind="session_summary", content="{}"
        )

        assert db.count() == 1


class TestPersistSessionDiagnosticsContainment:
    @pytest.mark.asyncio
    async def test_payload_defect_is_reported_and_does_not_escape(self, db) -> None:
        ctx = _ctx(1)
        ctx.stats.stat_turns = MagicMock()  # not JSON serializable
        view = MagicMock()
        persister = SessionPersister(
            ctx, DiagnosticStore(DiagnosticsConfig(), db_config=MIN_DB_CONFIG), view
        )

        await persister.persist_session_diagnostics()

        view.write_warning.assert_called_once()
        assert "Session persistence failed" in view.write_warning.call_args[0][0]
        assert db.count() == 0

    @pytest.mark.asyncio
    async def test_store_failure_is_reported_and_does_not_escape(self, db) -> None:
        store = DiagnosticStore(DiagnosticsConfig(), db_config=MIN_DB_CONFIG)
        view = MagicMock()
        persister = SessionPersister(_ctx(1), store, view)

        with patch.object(store, "save", side_effect=RuntimeError("store down")):
            await persister.persist_session_diagnostics()

        view.write_warning.assert_called_once()
        assert "store down" in view.write_warning.call_args[0][0]


def _mock_store() -> MagicMock:
    store = MagicMock(spec=StateStore)
    store.get_task_count.return_value = 2
    store.get_workflow_count.return_value = 1
    store.get_execute_attempt_count.return_value = 3
    store.get_artifact_uris.return_value = []
    return store


class TestPersistSessionDiagnosticsStoreClose:
    """The StateStore the persister opens is closed on every exit path."""

    @staticmethod
    async def _persist(db_session_id: int, store: MagicMock) -> None:
        persister = SessionPersister(
            _ctx(db_session_id),
            DiagnosticStore(DiagnosticsConfig(), db_config=MIN_DB_CONFIG),
            MagicMock(),
        )
        with patch("agent.workflow.state_store.StateStore", return_value=store):
            await persister.persist_session_diagnostics()

    @pytest.mark.asyncio
    async def test_closes_store_on_success(self, db) -> None:
        store = _mock_store()

        await self._persist(1, store)

        store.close.assert_called_once_with()
        assert db.count() == 1

    @pytest.mark.asyncio
    async def test_closes_store_when_a_query_raises_sqlite_error(self, db) -> None:
        store = _mock_store()
        store.get_task_count.side_effect = sqlite3.Error("db")

        await self._persist(1, store)

        store.close.assert_called_once_with()

    @pytest.mark.asyncio
    async def test_closes_store_when_attempt_count_is_none(self, db) -> None:
        store = _mock_store()
        store.get_execute_attempt_count.return_value = None

        await self._persist(1, store)

        store.close.assert_called_once_with()

    @pytest.mark.asyncio
    async def test_close_failure_is_logged_and_contained(self, db, caplog) -> None:
        store = _mock_store()
        store.close.side_effect = sqlite3.Error("close failed")

        with caplog.at_level(logging.WARNING, logger="agent.session_persister"):
            await self._persist(1, store)

        assert "close" in caplog.text
        assert db.count() == 1


class TestPersistSessionDiagnosticsRoundTrip:
    """Producer/read symmetry: stored `session_summary` content must parse with
    orjson (the read-side serializer used by the rag_entries reader and the
    diagnostic store readers) and preserve every summary key and value."""

    EXPECTED_KEYS = {
        "session_id",
        "timestamp",
        "turns",
        "tool_calls",
        "tool_errors",
        "partial_completions",
        "parse_errors",
        "heartbeat_timeouts",
        "reconnects",
        "input_tokens",
        "output_tokens",
        "compress_count",
        "fallback_truncate_count",
        "latency_summary",
        "workflow_count",
        "task_count",
        "retry_count",
        "artifacts",
        "rag_query_count",
        "rag_stage_outcomes",
    }

    @staticmethod
    def _stored_content(db) -> str:
        (content,) = db.conn.execute(
            "SELECT content FROM session_diagnostics WHERE kind='session_summary'"
        ).fetchone()
        return content

    @pytest.mark.asyncio
    async def test_stored_content_parses_with_orjson_and_preserves_keys(
        self, db
    ) -> None:
        ctx = _ctx(1)
        persister = SessionPersister(
            ctx,
            DiagnosticStore(DiagnosticsConfig(), db_config=MIN_DB_CONFIG),
            MagicMock(),
        )

        await persister.persist_session_diagnostics()

        content = self._stored_content(db)
        assert isinstance(content, str)
        parsed = orjson.loads(content)
        assert set(parsed) == self.EXPECTED_KEYS
        assert parsed["session_id"] == 1
        assert parsed["turns"] == ctx.stats.stat_turns
        assert parsed["tool_calls"] == ctx.stats.stat_tool_calls
        assert parsed["tool_errors"] == ctx.stats.stat_tool_errors
        assert parsed["input_tokens"] == ctx.stats.stat_input_tokens
        assert parsed["output_tokens"] == ctx.stats.stat_output_tokens

    @pytest.mark.asyncio
    async def test_latency_summary_floats_survive_round_trip(self, db) -> None:
        ctx = _ctx(1)
        ctx.stats.stat_latency = {"tool_a": [1.5, 0.5], "tool_b": [2.0]}
        persister = SessionPersister(
            ctx,
            DiagnosticStore(DiagnosticsConfig(), db_config=MIN_DB_CONFIG),
            MagicMock(),
        )

        await persister.persist_session_diagnostics()

        parsed = orjson.loads(self._stored_content(db))
        assert parsed["latency_summary"] == {
            "tool_a": {"count": 2, "mean_ms": 1000.0, "max_ms": 1500.0},
            "tool_b": {"count": 1, "mean_ms": 2000.0, "max_ms": 2000.0},
        }


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

    @pytest.mark.asyncio
    async def test_tool_and_ephemeral_history_logs_no_warning_and_no_content(
        self, caplog
    ) -> None:
        secret = "sk-live-deadbeefcafe"
        ctx = _ctx(1)
        ctx.services = MagicMock()
        ctx.services.memory.on_session_stop = AsyncMock()
        ctx.conv.history = [
            {"role": "user", "content": "what is the weather?"},
            {
                "role": "assistant",
                "content": "checking",
                "tool_calls": [
                    {
                        "id": "tc1",
                        "function": {"name": "weather", "arguments": "{}"},
                    }
                ],
            },
            {"role": "tool", "content": secret, "tool_call_id": "tc1"},
            {"role": "system", "content": "produce a final answer", "_ephemeral": True},
        ]
        persister = SessionPersister(ctx, MagicMock(), MagicMock())

        with caplog.at_level(logging.WARNING, logger="agent.session_persister"):
            await persister.persist_session_memories()

        assert not any(record.levelname == "WARNING" for record in caplog.records), (
            f"unexpected warning: {caplog.text}"
        )
        assert secret not in caplog.text

    @pytest.mark.asyncio
    async def test_unexpected_key_logs_role_and_key_without_content(
        self, caplog
    ) -> None:
        secret = "sk-live-deadbeefcafe"
        ctx = _ctx(1)
        ctx.services = MagicMock()
        ctx.services.memory.on_session_stop = AsyncMock()
        ctx.conv.history = [
            {"role": "user", "content": "hello"},
            {"role": "user", "content": secret, "rogue_key": "value"},
        ]
        persister = SessionPersister(ctx, MagicMock(), MagicMock())

        with caplog.at_level(logging.WARNING, logger="agent.session_persister"):
            await persister.persist_session_memories()

        assert "user" in caplog.text
        assert "rogue_key" in caplog.text
        assert secret not in caplog.text


class TestSessionPersistenceSnapshot:
    def test_capture_copies_state_once(self) -> None:
        ctx = _ctx(7)
        ctx.conv.history = [{"role": "user", "content": "hello"}]
        ctx.stats.stat_latency = {"llm": [0.5, 1.5]}
        persister = SessionPersister(ctx, MagicMock(), MagicMock())

        snap = persister.capture_snapshot()

        assert snap.session_id == 7
        assert snap.generation == 4
        assert snap.turn_id == "turn-1"
        assert snap.stats.turns == 3
        assert snap.stats.latency["llm"] == (0.5, 1.5)
        assert snap.history == ({"role": "user", "content": "hello"},)

    def test_history_mutation_after_capture_does_not_change_snapshot(self) -> None:
        ctx = _ctx(7)
        ctx.conv.history = [{"role": "user", "content": "hello"}]
        persister = SessionPersister(ctx, MagicMock(), MagicMock())
        snap = persister.capture_snapshot()

        ctx.conv.history[0]["content"] = "changed"
        ctx.conv.history.append({"role": "assistant", "content": "extra"})
        ctx.stats.stat_turns = 99

        assert snap.history == ({"role": "user", "content": "hello"},)
        assert snap.stats.turns == 3

    def test_snapshot_is_frozen(self) -> None:
        persister = SessionPersister(_ctx(7), MagicMock(), MagicMock())
        snap = persister.capture_snapshot()
        with pytest.raises(AttributeError):
            snap.generation = 1  # type: ignore[misc] — frozen dataclass write is the assertion
        with pytest.raises(TypeError):
            snap.stats.latency["x"] = ()  # type: ignore[index] — read-only mapping write is the assertion

    @pytest.mark.asyncio
    async def test_both_steps_use_the_same_snapshot_state(self, db) -> None:
        ctx = _ctx(7)
        ctx.services = SimpleNamespace(
            memory=MagicMock(on_session_stop=AsyncMock()), llm=None, hist_mgr=None
        )
        ctx.conv.history = [{"role": "user", "content": "hello"}]
        persister = SessionPersister(
            ctx,
            DiagnosticStore(
                diagnostics_cfg=DiagnosticsConfig(), db_config=MIN_DB_CONFIG
            ),
            MagicMock(),
        )
        snap = persister.capture_snapshot()
        # Live state moves on after capture: the steps must still read the snapshot.
        ctx.conv.history = [{"role": "user", "content": "later"}]
        ctx.stats.stat_turns = 50

        await persister.persist_session_memories(snap)
        await persister.persist_session_diagnostics(snap)

        kwargs = ctx.services.memory.on_session_stop.await_args.kwargs
        assert kwargs["session_id"] == 7
        assert kwargs["turn_id"] == "turn-1"
        assert [m.content for m in kwargs["history"]] == ["hello"]
        row = db.conn.execute("SELECT content FROM session_diagnostics").fetchone()
        assert orjson.loads(row[0])["turns"] == 3

    @pytest.mark.asyncio
    async def test_stale_generation_rejected_without_writes(self, db, caplog) -> None:
        ctx = _ctx(7)
        ctx.services = MagicMock()
        ctx.services.memory.on_session_stop = AsyncMock()
        persister = SessionPersister(
            ctx,
            DiagnosticStore(
                diagnostics_cfg=DiagnosticsConfig(), db_config=MIN_DB_CONFIG
            ),
            MagicMock(),
        )
        snap = persister.capture_snapshot()
        ctx.session.generation = 5  # a transition advanced the generation

        with caplog.at_level(logging.WARNING, logger="agent.session_persister"):
            await persister.persist_session_memories(snap)
            await persister.persist_session_diagnostics(snap)

        ctx.services.memory.on_session_stop.assert_not_called()
        assert db.count() == 0
        assert caplog.text.count("no longer matches the live session") == 2

    @pytest.mark.asyncio
    async def test_snapshot_without_session_skips(self, db) -> None:
        ctx = _ctx(7)
        ctx.services = MagicMock()
        ctx.services.memory.on_session_stop = AsyncMock()
        persister = SessionPersister(ctx, MagicMock(), MagicMock())
        empty = SessionPersistenceSnapshot(
            session_id=None,
            generation=4,
            history=(),
            turn_id=None,
            stats=persister.capture_snapshot().stats,
        )

        await persister.persist_session_memories(empty)
        await persister.persist_session_diagnostics(empty)

        ctx.services.memory.on_session_stop.assert_not_called()
        assert db.count() == 0


class TestMemoryFinalizationGuard:
    @pytest.mark.asyncio
    async def test_second_finalization_of_same_history_is_skipped(self, caplog) -> None:
        ctx = _ctx(7)
        ctx.services = MagicMock()
        ctx.services.memory.on_session_stop = AsyncMock()
        ctx.conv.history = [{"role": "user", "content": "hello"}]
        ctx.session.memory_finalized_count.return_value = 1
        persister = SessionPersister(ctx, MagicMock(), MagicMock())

        with caplog.at_level(logging.INFO, logger="agent.session_persister"):
            await persister.persist_session_memories()

        ctx.services.memory.on_session_stop.assert_not_called()
        assert "already finalized" in caplog.text

    @pytest.mark.asyncio
    async def test_success_records_the_finalized_message_count(self) -> None:
        ctx = _ctx(7)
        ctx.services = MagicMock()
        ctx.services.memory.on_session_stop = AsyncMock()
        ctx.conv.history = [
            {"role": "user", "content": "a"},
            {"role": "assistant", "content": "b"},
        ]
        persister = SessionPersister(ctx, MagicMock(), MagicMock())

        await persister.persist_session_memories()

        ctx.session.record_memory_finalized.assert_called_once_with(7, 2)

    @pytest.mark.asyncio
    async def test_failure_does_not_record(self) -> None:
        ctx = _ctx(7)
        ctx.services = MagicMock()
        ctx.services.memory.on_session_stop = AsyncMock(side_effect=RuntimeError("x"))
        ctx.conv.history = [{"role": "user", "content": "a"}]
        persister = SessionPersister(ctx, MagicMock(), MagicMock())

        await persister.persist_session_memories()

        ctx.session.record_memory_finalized.assert_not_called()


class TestSingleSnapshotAndBoundedReads:
    """REQ-007, AC-3: one snapshot per step, and reads that stop at the deadline."""

    @pytest.mark.asyncio
    async def test_supplied_snapshot_is_never_recaptured(self, db) -> None:
        """A persist call that receives a snapshot does not read the session again."""
        persister = SessionPersister(
            _ctx(7),
            DiagnosticStore(DiagnosticsConfig(), db_config=MIN_DB_CONFIG),
            MagicMock(),
        )
        snap = persister.capture_snapshot()

        with patch.object(persister, "capture_snapshot") as capture:
            await persister.persist_session_memories(snap)
            await persister.persist_session_diagnostics(snap)

        capture.assert_not_called()

    @pytest.mark.asyncio
    async def test_both_persist_calls_consume_the_same_snapshot_object(
        self, db
    ) -> None:
        """The step's one snapshot is what both writes read, not a fresh read each."""
        ctx = _ctx(7)
        ctx.stats.stat_turns = 3
        persister = SessionPersister(
            ctx,
            DiagnosticStore(DiagnosticsConfig(), db_config=MIN_DB_CONFIG),
            MagicMock(),
        )
        snap = persister.capture_snapshot()
        ctx.stats.stat_turns = 99  # live state moves on after the step captured it

        await persister.persist_session_diagnostics(snap)

        row = db.conn.execute("SELECT content FROM session_diagnostics").fetchone()
        assert orjson.loads(row[0])["turns"] == 3

    @pytest.mark.asyncio
    async def test_spent_deadline_skips_both_read_groups_and_labels_the_summary(
        self, db
    ) -> None:
        """A bounded step reports the sections it did not read instead of hiding them."""
        view = MagicMock()
        persister = SessionPersister(
            _ctx(7),
            DiagnosticStore(DiagnosticsConfig(), db_config=MIN_DB_CONFIG),
            view,
        )

        await persister.persist_session_diagnostics(deadline=time.monotonic() - 0.1)

        summary = orjson.loads(
            db.conn.execute("SELECT content FROM session_diagnostics").fetchone()[0]
        )
        assert summary["partial_sections"] == ["workflow_counts", "rag_summary"]
        # The values the snapshot already holds are still persisted.
        assert summary["turns"] == 3
        warning = view.write_warning.call_args.args[0]
        assert "captured partially" in warning
        assert "workflow_counts" in warning and "rag_summary" in warning

    @pytest.mark.asyncio
    async def test_live_deadline_reads_normally_and_labels_nothing(self, db) -> None:
        """REQ-007: a deadline that has not passed changes nothing."""
        view = MagicMock()
        persister = SessionPersister(
            _ctx(7),
            DiagnosticStore(DiagnosticsConfig(), db_config=MIN_DB_CONFIG),
            view,
        )

        await persister.persist_session_diagnostics(deadline=time.monotonic() + 5.0)

        summary = orjson.loads(
            db.conn.execute("SELECT content FROM session_diagnostics").fetchone()[0]
        )
        assert "partial_sections" not in summary
        view.write_warning.assert_not_called()

    @pytest.mark.asyncio
    async def test_read_groups_are_checked_before_starting_not_inside_a_query(
        self, db, caplog
    ) -> None:
        """The deadline is a gate before each read group, so a partial snapshot is defined."""
        ctx = _ctx(7)
        persister = SessionPersister(
            ctx,
            DiagnosticStore(DiagnosticsConfig(), db_config=MIN_DB_CONFIG),
            MagicMock(),
        )
        deadline = time.monotonic() - 0.1
        with (
            patch.object(
                persister, "_workflow_counts", wraps=persister._workflow_counts
            ) as wf,
            patch.object(
                persister, "_rag_summary", wraps=persister._rag_summary
            ) as rag,
            caplog.at_level(logging.WARNING, logger="agent.session_persister"),
        ):
            await persister.persist_session_diagnostics(deadline=deadline)

        assert wf.call_args.args[1] == deadline
        assert rag.call_args.args[1] == deadline
        assert db.count() == 1  # the shortened summary is still written, labeled

    @pytest.mark.asyncio
    async def test_memories_are_skipped_and_reported_when_the_deadline_is_spent(
        self, caplog
    ) -> None:
        """No memory write is started past the deadline; the skip is visible."""
        ctx = _ctx(7)
        ctx.services = MagicMock()
        ctx.services.memory.on_session_stop = AsyncMock()
        view = MagicMock()
        persister = SessionPersister(ctx, MagicMock(), view)

        with caplog.at_level(logging.WARNING, logger="agent.session_persister"):
            await persister.persist_session_memories(deadline=time.monotonic() - 0.1)

        ctx.services.memory.on_session_stop.assert_not_called()
        assert "deadline" in caplog.text
        assert "not persisted" in view.write_warning.call_args.args[0]

    @pytest.mark.asyncio
    async def test_memories_run_when_the_deadline_has_not_passed(self) -> None:
        ctx = _ctx(7)
        ctx.services = MagicMock()
        ctx.services.memory.on_session_stop = AsyncMock()
        ctx.conv.history = [{"role": "user", "content": "hello"}]
        view = MagicMock()
        persister = SessionPersister(ctx, MagicMock(), view)

        await persister.persist_session_memories(deadline=time.monotonic() + 5.0)

        ctx.services.memory.on_session_stop.assert_awaited_once()
        view.write_warning.assert_not_called()
