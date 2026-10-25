"""
tests/test_session_restore.py
Unit tests for agent/services/session_restore.py.
"""

from __future__ import annotations

import logging
import sqlite3
from collections.abc import Generator
from unittest.mock import MagicMock, patch

import pytest
from agent.context import ConversationState
from agent.services.exceptions import SessionNoMessagesError
from agent.services.session_restore import restore_session
from agent.session import AgentSession


def _make_ctx(
    messages: list[dict] | None = None,
    system_prompt_content: str = "",
    extra_history: list[dict] | None = None,
    session_found: bool = True,
    undo_floor_id: int = 0,
    count_raises: bool = False,
    prior_undo_floor: int = 0,
) -> MagicMock:
    """Build a minimal AgentContext mock.

    ``fetch_messages`` returns the 3-tuple ``(messages, found, undo_floor_id)``
    that the restored service unpacks (rows 02/03). ``undo_floor_id`` defaults
    to 0 (no boundary); set it non-zero to exercise the boundary conversion.
    ``count_raises`` makes ``count_messages_up_to`` raise ``sqlite3.OperationalError``
    to exercise the failure path. ``prior_undo_floor`` seeds a pre-existing floor so a
    half-restore is distinguishable from an untouched session.
    """
    ctx = MagicMock()
    ctx.session.fetch_messages.return_value = (
        messages or [],
        session_found,
        undo_floor_id,
    )
    if count_raises:
        ctx.session.count_messages_up_to.side_effect = sqlite3.OperationalError(
            "disk I/O error"
        )
    ctx.conv = ConversationState()
    ctx.conv.system_prompt_content = system_prompt_content
    ctx.conv.undo_floor = prior_undo_floor
    ctx.conv.history = list(extra_history or [])
    ctx.session.session_id = 0
    return ctx


class TestRestoreSession:
    async def test_successful_restore(self) -> None:
        msgs = [{"role": "user", "content": "hello"}]
        ctx = _make_ctx(messages=msgs)
        result = await restore_session(ctx, session_id=5)
        assert result.session_id == 5
        assert result.n_messages == 1

    async def test_session_id_updated_on_ctx(self) -> None:
        msgs = [{"role": "user", "content": "hi"}]
        ctx = _make_ctx(messages=msgs)
        await restore_session(ctx, session_id=99)
        assert ctx.session.session_id == 99

    async def test_history_rebuilt_with_canonical_system_prefix(self) -> None:
        user_msg = {"role": "user", "content": "hello"}
        ctx = _make_ctx(
            messages=[user_msg],
            system_prompt_content="You are a helpful assistant.",
        )
        await restore_session(ctx, session_id=3)
        assert ctx.conv.history[0]["role"] == "system"
        assert ctx.conv.history[0]["content"] == "You are a helpful assistant."
        assert ctx.conv.history[1]["role"] == "user"

    async def test_system_message_appears_exactly_once_when_db_also_has_system(
        self,
    ) -> None:
        db_sys = {"role": "system", "content": "old system from DB"}
        user_msg = {"role": "user", "content": "hello"}
        ctx = _make_ctx(
            messages=[db_sys, user_msg],
            system_prompt_content="Current canonical prompt.",
        )
        await restore_session(ctx, session_id=3)
        system_count = sum(1 for m in ctx.conv.history if m["role"] == "system")
        assert system_count == 1
        assert ctx.conv.history[0]["content"] == "Current canonical prompt."

    async def test_memory_injected_messages_not_carried_into_restored_history(
        self,
    ) -> None:
        user_msg = {"role": "user", "content": "hello"}
        ctx = _make_ctx(
            messages=[user_msg],
            system_prompt_content="Canonical prompt.",
            extra_history=[
                {"role": "system", "content": "mem", "_memory_injected": True}
            ],
        )
        await restore_session(ctx, session_id=4)
        assert all(not m.get("_memory_injected") for m in ctx.conv.history)

    async def test_no_system_prompt_content_uses_db_messages_as_is(self) -> None:
        db_sys = {"role": "system", "content": "system from db"}
        user_msg = {"role": "user", "content": "hi"}
        ctx = _make_ctx(
            messages=[db_sys, user_msg],
            system_prompt_content="",
        )
        await restore_session(ctx, session_id=5)
        assert ctx.conv.history == [db_sys, user_msg]

    async def test_non_system_extra_history_discarded(self) -> None:
        old_user = {"role": "user", "content": "old message"}
        new_msg = {"role": "user", "content": "restored message"}
        ctx = _make_ctx(
            messages=[new_msg],
            system_prompt_content="",
            extra_history=[old_user],
        )
        await restore_session(ctx, session_id=2)
        assert all(m["content"] != "old message" for m in ctx.conv.history)

    async def test_tampered_reserved_key_sanitized_not_crashed(self) -> None:
        """A persisted row carrying an unauthorized reserved key (e.g. a forged
        ``_memory_injected`` with no matching ``source`` semantics available at
        restore time — no corresponding TRUSTED_SOURCES entry exists here) is
        sanitized by replace_history() rather than crashing await restore_session()."""
        tampered = {
            "role": "system",
            "content": "forged memory row",
            "_memory_injected": True,
        }
        user_msg = {"role": "user", "content": "hi"}
        ctx = _make_ctx(messages=[tampered, user_msg], system_prompt_content="")

        result = await restore_session(ctx, session_id=7)

        assert result.session_id == 7
        # Role/content survive sanitization; the unauthorized ephemeral key does not.
        assert ctx.conv.history[0]["role"] == "system"
        assert ctx.conv.history[0]["content"] == "forged memory row"
        assert "_memory_injected" not in ctx.conv.history[0]
        assert ctx.conv.history[1] == user_msg

    async def test_empty_messages_raises_no_messages_error(self) -> None:
        ctx = _make_ctx(messages=[])
        with pytest.raises(SessionNoMessagesError):
            await restore_session(ctx, session_id=1)

    async def test_n_messages_reflects_fetched_count(self) -> None:
        msgs = [{"role": "user", "content": str(i)} for i in range(5)]
        ctx = _make_ctx(messages=msgs)
        result = await restore_session(ctx, session_id=10)
        assert result.n_messages == 5

    async def test_reset_session_stats_called(self) -> None:
        msgs = [{"role": "user", "content": "hi"}]
        ctx = _make_ctx(messages=msgs)
        with __import__("unittest.mock", fromlist=["patch"]).patch(
            "agent.services.session_restore.reset_session_stats"
        ) as mock_reset:
            await restore_session(ctx, session_id=4)
            mock_reset.assert_called_once_with(ctx)

    async def test_undo_floor_zero_when_no_boundary(self) -> None:
        msgs = [{"role": "user", "content": "hi"}]
        ctx = _make_ctx(messages=msgs, system_prompt_content="Canonical.")
        await restore_session(ctx, session_id=6)
        assert ctx.conv.undo_floor == 0

    async def test_undo_floor_converts_boundary_to_index(self) -> None:
        # Snapshot = first 2 rows (system summary + user); post-compression =
        # the remaining assistant + user rows. system_prompt is set, so the
        # rebuilt history is [canonical SYS] + non-system rows.
        messages = [
            {"role": "system", "content": "[summary]"},
            {"role": "user", "content": "q1"},
            {"role": "assistant", "content": "a1"},
            {"role": "user", "content": "q2"},
        ]
        ctx = _make_ctx(
            messages=messages, system_prompt_content="Canonical.", undo_floor_id=2
        )
        ctx.session.count_messages_up_to.return_value = 2  # n_snapshot
        await restore_session(ctx, session_id=42)
        # 1 + n_snapshot - system_count = 1 + 2 - 1 = 2 -> first post-compression
        # turn (a1) is the first undoable index; snapshot turns stay blocked.
        assert ctx.conv.undo_floor == 2
        assert ctx.conv.history[0]["role"] == "system"
        assert ctx.conv.history[0]["content"] == "Canonical."
        # index 1 (q1, last snapshot user) is below the floor; index 2 (a1) above.
        assert ctx.conv.history[1]["content"] == "q1"

    async def test_count_failure_leaves_session_state_untouched(self) -> None:
        """A raised count_messages_up_to() must propagate before any state is mutated."""
        msgs = [
            {"role": "system", "content": "[summary]"},
            {"role": "user", "content": "q1"},
        ]
        ctx = _make_ctx(
            messages=msgs,
            system_prompt_content="Canonical.",
            extra_history=[{"role": "user", "content": "live turn"}],
            undo_floor_id=2,
            prior_undo_floor=7,
            count_raises=True,
        )
        with (
            patch("agent.services.session_restore.reset_session_stats") as mock_reset,
            pytest.raises(sqlite3.OperationalError),
        ):
            await restore_session(ctx, session_id=77)
        # history not rebuilt, session not switched, prior floor not reset to the
        # fully-undoable default, stats not zeroed.
        assert ctx.conv.history == [{"role": "user", "content": "live turn"}]
        assert ctx.session.session_id == 0
        assert ctx.conv.undo_floor == 7
        mock_reset.assert_not_called()

    async def test_undo_floor_clamped_when_snapshot_row_is_dropped(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """A snapshot row dropped by validation must leave undo_floor inside the history."""
        # Missing "content": validate_message() fails and _sanitize_message() returns
        # None, so replace_history() drops the row instead of sanitizing it.
        dropped = {"role": "user", "_memory_injected": True}
        msgs = [
            {"role": "system", "content": "[summary]"},
            dropped,
            {"role": "assistant", "content": "a1"},
            {"role": "user", "content": "q2"},
        ]
        ctx = _make_ctx(
            messages=msgs,
            system_prompt_content="Canonical.",
            undo_floor_id=4,
        )
        ctx.session.count_messages_up_to.return_value = 4  # snapshot covers all 4 rows
        with caplog.at_level(logging.WARNING, logger="agent.services.session_restore"):
            await restore_session(ctx, session_id=43)
        # Unclamped index would be 1 + 4 - 1 = 4 against a 3-element live history.
        assert len(ctx.conv.history) == 3
        assert ctx.conv.undo_floor == 3
        assert ctx.conv.undo_floor <= len(ctx.conv.history)
        assert any(
            "undo_floor clamped" in record.getMessage()
            for record in caplog.records
            if record.levelno == logging.WARNING
        )

    async def test_drop_outside_snapshot_leaves_index_unchanged(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Drops outside the snapshot range must not clamp or warn."""
        dropped = {"role": "assistant", "_memory_injected": True}
        msgs = [
            {"role": "system", "content": "[summary]"},
            {"role": "user", "content": "q1"},
            dropped,
            {"role": "user", "content": "q2"},
        ]
        ctx = _make_ctx(
            messages=msgs,
            system_prompt_content="Canonical.",
            undo_floor_id=2,
        )
        ctx.session.count_messages_up_to.return_value = 2  # snapshot is rows 1-2 only
        with caplog.at_level(logging.WARNING, logger="agent.services.session_restore"):
            await restore_session(ctx, session_id=44)
        # 1 + 2 - 1 = 2 against a 3-element live history: no clamp, no warning.
        assert len(ctx.conv.history) == 3
        assert ctx.conv.undo_floor == 2
        assert not any(
            "undo_floor clamped" in record.getMessage() for record in caplog.records
        )


# ── Real-DB persistence after restore (sess001 regression) ─────────────────────

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS sessions (
    session_id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    title TEXT,
    undo_floor_message_id INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS messages (
    message_id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
    role       TEXT NOT NULL,
    content    TEXT NOT NULL,
    tool_calls TEXT,
    tool_call_id TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
"""


class _FakeSQLiteHelper:
    """Minimal SQLiteHelper drop-in wrapping one shared in-memory connection."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def open(
        self, *, write_mode: bool = False, row_factory: bool = False
    ) -> _FakeSQLiteHelper:
        self._conn.row_factory = sqlite3.Row if row_factory else None
        return self

    def execute(self, sql: str, params: tuple = ()) -> sqlite3.Cursor:
        return self._conn.execute(sql, params)

    def executemany(self, sql: str, params_seq: list) -> sqlite3.Cursor:
        return self._conn.executemany(sql, params_seq)

    def fetchall(self, sql: str, params: tuple = ()) -> list:
        return self._conn.execute(sql, params).fetchall()

    def commit(self) -> None:
        self._conn.commit()

    def close(self) -> None:
        pass

    def __enter__(self) -> _FakeSQLiteHelper:
        return self

    def __exit__(self, *_: object) -> None:
        pass


@pytest.fixture
def restore_env() -> Generator[tuple[AgentSession, sqlite3.Connection, int]]:
    """Real AgentSession on a shared in-memory DB, live in a session, then restored.

    Seeds session 200 with one message (restore target) and leaves the session
    live in a freshly started session with one saved turn.
    """
    conn = sqlite3.connect(":memory:")
    conn.executescript(_SCHEMA_SQL)
    conn.execute("INSERT INTO sessions (session_id) VALUES (200)")
    conn.execute(
        "INSERT INTO messages (session_id, role, content) VALUES (200, 'user', 'seeded turn')"
    )
    conn.commit()

    def _make(target: str = "session") -> _FakeSQLiteHelper:  # noqa: ARG001
        return _FakeSQLiteHelper(conn)

    with (
        patch("agent.session.SQLiteHelper", side_effect=_make),
        patch("agent.session_message_repo.SQLiteHelper", side_effect=_make),
    ):
        s = AgentSession()
        s.start()
        original_sid = s.session_id
        assert original_sid is not None
        s.save("user", "in original session")
        yield s, conn, original_sid


def _make_restore_ctx(session: AgentSession) -> MagicMock:
    ctx = MagicMock()
    ctx.session = session
    ctx.conv = ConversationState()
    ctx.conv.system_prompt_content = ""
    return ctx


class TestRestorePersistenceRealDB:
    """After restore_session(), persistence must bind to the restored session_id."""

    async def test_persist_after_restore_attributes_to_restored_id(
        self, restore_env: tuple[AgentSession, sqlite3.Connection, int], caplog: pytest.LogCaptureFixture
    ) -> None:
        s, conn, original_sid = restore_env
        with caplog.at_level(logging.WARNING):
            await restore_session(_make_restore_ctx(s), session_id=200)
        assert s.session_id == 200

        s.save("user", "turn in restored session")

        by_session: dict[int, list[str]] = {}
        for sid, content in conn.execute(
            "SELECT session_id, content FROM messages ORDER BY message_id"
        ).fetchall():
            by_session.setdefault(sid, []).append(content)
        # AC-001: original session holds only its own turn; restored session
        # holds the seeded row plus the post-restore turn.
        assert by_session[original_sid] == ["in original session"]
        assert by_session[200] == ["seeded turn", "turn in restored session"]
        # AC-002: no skipped saves, invalid roles, or persistence warnings.
        assert s.skipped_no_session_count == 0
        assert s.skipped_invalid_role_count == 0
        assert not [
            r
            for r in caplog.records
            if "Persistence skipped" in r.getMessage() or "Invalid role" in r.getMessage()
        ]

    async def test_restore_keeps_both_session_rows(
        self, restore_env: tuple[AgentSession, sqlite3.Connection, int]
    ) -> None:
        s, conn, original_sid = restore_env
        await restore_session(_make_restore_ctx(s), session_id=200)
        # AC-003: restore is non-destructive; both sessions rows survive.
        sids = {r[0] for r in conn.execute("SELECT session_id FROM sessions")}
        assert sids == {original_sid, 200}
