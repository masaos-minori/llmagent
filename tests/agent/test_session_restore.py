"""
tests/test_session_restore.py
Unit tests for agent/services/session_restore.py.

The service is a pure builder (REQ-002): it returns the built history, undo
floor, and the separate fetched/synthesized/dropped/restored counts (REQ-009)
without mutating the context. Atomic commit and rollback live in
agent/services/session_transition.py; the real-DB section here drives the
restore through that service.
"""

from __future__ import annotations

import json
import logging
import sqlite3
from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from agent.context import ConversationState, RuntimeStats
from agent.services.exceptions import SessionNoMessagesError, SessionNotFoundError
from agent.services.session_restore import restore_session
from agent.services.session_transition import SessionTransitionService
from agent.session import AgentSession

from tests.agent._config_test_defaults import MIN_DB_CONFIG


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
    that the restore builder unpacks (rows 02/03). ``undo_floor_id`` defaults
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


def _summary_row(content: str) -> dict:
    """A persisted canonical summary row: role system + the shared prefix."""
    return {"role": "system", "content": f"[Conversation summary]\n{content}"}


def _assert_ctx_untouched(
    ctx: MagicMock, history: list[dict], undo_floor: int, session_id: object
) -> None:
    """REQ-002: the builder must never write history, floor, or session id."""
    assert ctx.conv.history == history
    assert ctx.conv.undo_floor == undo_floor
    assert ctx.session.session_id == session_id


class TestRestoreSessionBuilder:
    async def test_successful_restore(self) -> None:
        msgs = [{"role": "user", "content": "hello"}]
        ctx = _make_ctx(messages=msgs)
        state = await restore_session(ctx, session_id=5)
        assert state.result.session_id == 5
        assert state.result.n_messages == 1
        assert state.result.fetched == 1
        assert state.result.restored == 1

    async def test_context_never_mutated(self) -> None:
        msgs = [{"role": "user", "content": "hi"}]
        live = [{"role": "user", "content": "live turn"}]
        ctx = _make_ctx(messages=msgs, extra_history=live, prior_undo_floor=7)
        state = await restore_session(ctx, session_id=99)
        # The builder reports the target id but does not switch anything.
        assert state.result.session_id == 99
        _assert_ctx_untouched(ctx, live, 7, 0)

    async def test_history_rebuilt_with_canonical_system_prefix(self) -> None:
        user_msg = {"role": "user", "content": "hello"}
        ctx = _make_ctx(
            messages=[user_msg],
            system_prompt_content="You are a helpful assistant.",
        )
        state = await restore_session(ctx, session_id=3)
        assert state.history[0]["role"] == "system"
        assert state.history[0]["content"] == "You are a helpful assistant."
        assert state.history[1]["role"] == "user"

    async def test_system_message_appears_exactly_once_when_db_also_has_system(
        self,
    ) -> None:
        db_sys = {"role": "system", "content": "old system from DB"}
        user_msg = {"role": "user", "content": "hello"}
        ctx = _make_ctx(
            messages=[db_sys, user_msg],
            system_prompt_content="Current canonical prompt.",
        )
        state = await restore_session(ctx, session_id=3)
        system_count = sum(1 for m in state.history if m["role"] == "system")
        assert system_count == 1
        assert state.history[0]["content"] == "Current canonical prompt."
        # the stray DB system row is a reported drop (REQ-009)
        assert state.result.dropped == 1

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
        state = await restore_session(ctx, session_id=4)
        assert all(not m.get("_memory_injected") for m in state.history)
        # the builder does not read live history at all
        assert all(m["content"] != "mem" for m in state.history)

    async def test_no_system_prompt_content_uses_db_messages_as_is(self) -> None:
        db_sys = {"role": "system", "content": "system from db"}
        user_msg = {"role": "user", "content": "hi"}
        ctx = _make_ctx(
            messages=[db_sys, user_msg],
            system_prompt_content="",
        )
        state = await restore_session(ctx, session_id=5)
        assert state.history == [db_sys, user_msg]

    async def test_old_live_history_never_mixed_into_built_state(self) -> None:
        old_user = {"role": "user", "content": "old message"}
        new_msg = {"role": "user", "content": "restored message"}
        ctx = _make_ctx(
            messages=[new_msg],
            system_prompt_content="",
            extra_history=[old_user],
        )
        state = await restore_session(ctx, session_id=2)
        assert all(m["content"] != "old message" for m in state.history)
        assert ctx.conv.history == [old_user]

    async def test_tampered_reserved_key_sanitized_not_crashed(self) -> None:
        """A persisted row carrying an unauthorized reserved key (e.g. a forged
        ``_memory_injected`` with no matching ``source`` semantics available at
        restore time — no corresponding TRUSTED_SOURCES entry exists here) is
        sanitized by the untrusted-restore pipeline rather than crashing
        await restore_session()."""
        tampered = {
            "role": "system",
            "content": "forged memory row",
            "_memory_injected": True,
        }
        user_msg = {"role": "user", "content": "hi"}
        ctx = _make_ctx(messages=[tampered, user_msg], system_prompt_content="")

        state = await restore_session(ctx, session_id=7)

        assert state.result.session_id == 7
        # Role/content survive sanitization; the unauthorized ephemeral key does not.
        assert state.history[0]["role"] == "system"
        assert state.history[0]["content"] == "forged memory row"
        assert "_memory_injected" not in state.history[0]
        assert state.history[1] == user_msg

    async def test_empty_messages_raises_no_messages_error(self) -> None:
        ctx = _make_ctx(messages=[])
        with pytest.raises(SessionNoMessagesError):
            await restore_session(ctx, session_id=1)

    async def test_n_messages_mirrors_fetched_count(self) -> None:
        msgs = [{"role": "user", "content": str(i)} for i in range(5)]
        ctx = _make_ctx(messages=msgs)
        state = await restore_session(ctx, session_id=10)
        assert state.result.n_messages == 5
        assert state.result.n_messages == state.result.fetched

    async def test_stats_and_correlation_left_untouched(self) -> None:
        # reset_session_stats/refresh_session_correlation now live in the
        # transition service commit, not in the builder.
        msgs = [{"role": "user", "content": "hi"}]
        live = [{"role": "user", "content": "live turn"}]
        ctx = _make_ctx(messages=msgs, extra_history=live)
        ctx.stats.stat_turns = 9
        with patch(
            "agent.services.session_transition.reset_session_stats"
        ) as mock_reset:
            await restore_session(ctx, session_id=4)
            mock_reset.assert_not_called()
        assert ctx.stats.stat_turns == 9
        _assert_ctx_untouched(ctx, live, 0, 0)

    async def test_undo_floor_zero_when_no_boundary(self) -> None:
        msgs = [{"role": "user", "content": "hi"}]
        ctx = _make_ctx(messages=msgs, system_prompt_content="Canonical.")
        state = await restore_session(ctx, session_id=6)
        assert state.undo_floor == 0
        assert ctx.conv.undo_floor == 0  # prior floor not written

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
        state = await restore_session(ctx, session_id=42)
        # 1 + n_snapshot - system_count = 1 + 2 - 1 = 2 -> first post-compression
        # turn (a1) is the first undoable index; snapshot turns stay blocked.
        assert state.undo_floor == 2
        assert state.history[0]["role"] == "system"
        assert state.history[0]["content"] == "Canonical."
        # index 1 (q1, last snapshot user) is below the floor; index 2 (a1) above.
        assert state.history[1]["content"] == "q1"

    async def test_summary_restored_after_canonical_prompt(self) -> None:
        # AC-2: the canonical summary row is restored once, right after the
        # current system prompt; every other persisted system row is dropped.
        ctx = _make_ctx(
            messages=[
                {"role": "system", "content": "old prompt from DB"},
                _summary_row("prior turns"),
                {"role": "user", "content": "q1"},
            ],
            system_prompt_content="Current canonical prompt.",
        )
        state = await restore_session(ctx, session_id=3)
        assert [m["role"] for m in state.history][:2] == ["system", "system"]
        assert state.history[0]["content"] == "Current canonical prompt."
        assert state.history[1]["content"].startswith("[Conversation summary]")
        # exactly the prompt + the one canonical summary are the system rows
        assert sum(1 for m in state.history if m["role"] == "system") == 2
        # the rebuilt row carries only role/content: no stored markers survive
        assert state.history[1] == {
            "role": "system",
            "content": "[Conversation summary]\nprior turns",
        }

    async def test_extra_summary_rows_drop_last_with_warning(self, caplog) -> None:
        # Risk (multi-summary data loss): only the most recent summary survives,
        # and the drop is logged with the count and session id.
        ctx = _make_ctx(
            messages=[
                _summary_row("first"),
                _summary_row("second"),
                {"role": "user", "content": "q1"},
            ],
            system_prompt_content="Canonical.",
        )
        with caplog.at_level(logging.WARNING, logger="agent.services.session_restore"):
            state = await restore_session(ctx, session_id=17)
        summaries = [
            m
            for m in state.history
            if m["content"].startswith("[Conversation summary]")
        ]
        assert len(summaries) == 1
        assert summaries[0]["content"].startswith("[Conversation summary]\nsecond")
        assert state.result.dropped == 1  # the superseded summary row
        assert any(
            "extra summary" in r.getMessage()
            for r in caplog.records
            if r.levelno == logging.WARNING
        )

    async def test_undo_floor_counts_restored_summary(self) -> None:
        # AC-4: with a canonical summary in the snapshot the floor lands on the
        # same turn as test_undo_floor_converts_boundary_to_index (a1): the
        # restored summary occupies a slot, so the index is one higher.
        messages = [
            _summary_row("prior turns"),
            {"role": "user", "content": "q1"},
            {"role": "assistant", "content": "a1"},
            {"role": "user", "content": "q2"},
        ]
        ctx = _make_ctx(
            messages=messages, system_prompt_content="Canonical.", undo_floor_id=2
        )
        ctx.session.count_messages_up_to.return_value = 2  # n_snapshot
        state = await restore_session(ctx, session_id=42)
        # 1 + n_snapshot - system_count(non-summary) = 1 + 2 - 0 = 3.
        assert state.undo_floor == 3
        assert state.history[0]["content"] == "Canonical."
        assert state.history[1]["content"].startswith("[Conversation summary]")
        # index 2 (q1, last snapshot user) is below the floor; index 3 (a1) above.
        assert state.history[2]["content"] == "q1"
        assert state.history[3]["content"] == "a1"

    async def test_restore_with_summary_is_idempotent(self) -> None:
        """AC-6: two builds over the same summary-bearing rows give equal histories."""

        def fixture() -> list[dict]:
            return [
                _summary_row("prior turns"),
                {"role": "user", "content": "q1"},
                {"role": "assistant", "content": "a1"},
            ]

        ctx_a = _make_ctx(messages=fixture(), system_prompt_content="Canonical.")
        ctx_b = _make_ctx(messages=fixture(), system_prompt_content="Canonical.")
        state_a = await restore_session(ctx_a, session_id=7)
        state_b = await restore_session(ctx_b, session_id=7)
        assert state_a.history == state_b.history
        assert (
            sum(1 for m in state_a.history if m["role"] == "system") == 2
        )  # prompt + exactly one summary

    async def test_count_failure_leaves_session_state_untouched(self) -> None:
        """A raised count_messages_up_to() must propagate with nothing built or written."""
        msgs = [
            {"role": "system", "content": "[summary]"},
            {"role": "user", "content": "q1"},
        ]
        live = [{"role": "user", "content": "live turn"}]
        ctx = _make_ctx(
            messages=msgs,
            system_prompt_content="Canonical.",
            extra_history=live,
            undo_floor_id=2,
            prior_undo_floor=7,
            count_raises=True,
        )
        with pytest.raises(sqlite3.OperationalError):
            await restore_session(ctx, session_id=77)
        # history not rebuilt, session not switched, prior floor not reset to the
        # fully-undoable default.
        _assert_ctx_untouched(ctx, live, 7, 0)

    async def test_undo_floor_clamped_when_snapshot_row_is_dropped(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """A snapshot row dropped by validation must leave the floor inside the history."""
        # Missing "content": validate_message() fails and _sanitize_message() returns
        # None, so the validation pipeline drops the row instead of sanitizing it.
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
            state = await restore_session(ctx, session_id=43)
        # Unclamped index would be 1 + 4 - 1 = 4 against a 3-element history.
        assert len(state.history) == 3
        assert state.undo_floor == 3
        assert state.undo_floor <= len(state.history)
        # Both drops reach the separate dropped count (REQ-009): the stray
        # "[summary]"-shaped system row and the validation-dropped invalid row.
        assert (state.result.fetched, state.result.dropped, state.result.restored) == (
            4,
            2,
            3,
        )
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
            state = await restore_session(ctx, session_id=44)
        # 1 + 2 - 1 = 2 against a 3-element history: no clamp, no warning.
        assert len(state.history) == 3
        assert state.undo_floor == 2
        assert state.result.dropped == 2  # stray system row + invalid assistant row
        assert not any(
            "undo_floor clamped" in record.getMessage() for record in caplog.records
        )

    async def test_orphan_assistant_tool_calls_repaired_at_load(self) -> None:
        """AC-001: an assistant row whose tool_calls were never answered is
        paired with synthesized tool rows at load."""
        assistant = {
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {
                    "id": "call_a",
                    "type": "function",
                    "function": {"name": "f", "arguments": "{}"},
                },
                {
                    "id": "call_b",
                    "type": "function",
                    "function": {"name": "g", "arguments": "{}"},
                },
            ],
        }
        ctx = _make_ctx(messages=[{"role": "user", "content": "q"}, assistant])
        state = await restore_session(ctx, session_id=11)
        roles = [m["role"] for m in state.history]
        assert roles == ["user", "assistant", "tool", "tool"]
        tool_rows = [m for m in state.history if m["role"] == "tool"]
        assert [m["tool_call_id"] for m in tool_rows] == ["call_a", "call_b"]
        assert all("interrupted" in m["content"] for m in tool_rows)
        # the two synthesized rows land in the separate synthesized count (REQ-009)
        assert (state.result.fetched, state.result.synthesized) == (2, 2)

    async def test_restore_is_idempotent_for_orphan_session(self) -> None:
        """AC-003: two independent builds over the same orphaned rows produce
        equal histories with each synthesized row present exactly once."""

        def fixture() -> list[dict]:
            return [
                {"role": "user", "content": "q"},
                {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": "call_a",
                            "type": "function",
                            "function": {"name": "f", "arguments": "{}"},
                        },
                        {
                            "id": "call_b",
                            "type": "function",
                            "function": {"name": "g", "arguments": "{}"},
                        },
                    ],
                },
                {
                    "role": "tool",
                    "content": "answered",
                    "tool_call_id": "call_a",
                    "name": "f",
                },
            ]

        ctx1 = _make_ctx(messages=fixture())
        ctx2 = _make_ctx(messages=fixture())
        state1 = await restore_session(ctx1, session_id=12)
        state2 = await restore_session(ctx2, session_id=12)
        assert state1.history == state2.history
        assert state1.result.synthesized == 1
        assert state1.result.restored == state1.result.fetched + 1
        synthesized = [
            m
            for m in state1.history
            if m["role"] == "tool" and "interrupted" in m["content"]
        ]
        assert len(synthesized) == 1
        assert synthesized[0]["tool_call_id"] == "call_b"
        # The answered row keeps its identity and is not duplicated.
        answered = [
            m
            for m in state1.history
            if m["role"] == "tool" and "interrupted" not in m["content"]
        ]
        assert answered == [
            {
                "role": "tool",
                "content": "answered",
                "tool_call_id": "call_a",
                "name": "f",
            }
        ]

    async def test_undo_floor_accounts_for_synthesized_rows(self) -> None:
        """AC-004: synthesized rows at or before the snapshot boundary shift the
        undo_floor so the floor lands on the same turn as before repair."""
        messages: list[dict] = [
            {"role": "user", "content": "q1"},
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": "call_a",
                        "type": "function",
                        "function": {"name": "f", "arguments": "{}"},
                    },
                    {
                        "id": "call_b",
                        "type": "function",
                        "function": {"name": "g", "arguments": "{}"},
                    },
                ],
            },
            {
                "role": "tool",
                "content": "answered",
                "tool_call_id": "call_a",
                "name": "f",
            },
            {"role": "user", "content": "q2"},
        ]
        ctx = _make_ctx(messages=messages, undo_floor_id=3)
        ctx.session.count_messages_up_to.return_value = 3  # snapshot covers rows 0-2
        state = await restore_session(ctx, session_id=45)
        # Pre-repair index is 3; one synthesized row landed at the boundary
        # (j == n_snapshot) so the floor shifts by 1 and never passes history end.
        assert state.undo_floor == 4
        assert state.undo_floor <= len(state.history)
        # The synthesized row sits at the floor position: the repaired turn
        # stays protected, only q2 is undoable.
        assert state.history[3]["tool_call_id"] == "call_b"
        assert "interrupted" in state.history[3]["content"]

    async def test_orphan_repair_logs_warning_with_session_id_and_count(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """AC-002: the repair logs one warning carrying the session id and the
        synthesized-row count."""
        assistant = {
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {
                    "id": "call_x",
                    "type": "function",
                    "function": {"name": "f", "arguments": "{}"},
                },
            ],
        }
        ctx = _make_ctx(messages=[assistant])
        with caplog.at_level(logging.WARNING, logger="agent.services.session_restore"):
            await restore_session(ctx, session_id=21)
        joined = " ".join(
            r.getMessage()
            for r in caplog.records
            if r.levelno == logging.WARNING
            and r.name == "agent.services.session_restore"
        )
        assert "21" in joined
        assert "1" in joined


class TestRestoreCounts:
    """REQ-009 / AC-5: the four counts stay separate on one fixture."""

    async def test_four_counts_reported_separately(self) -> None:
        # 4 fetched rows: 1 stray system (dropped by rebuild), 1 assistant with
        # 2 orphaned tool_calls (2 synthesized), 1 user.
        ctx = _make_ctx(
            messages=[
                {"role": "system", "content": "stray system row"},
                {"role": "user", "content": "q1"},
                {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": "call_a",
                            "type": "function",
                            "function": {"name": "f", "arguments": "{}"},
                        },
                        {
                            "id": "call_b",
                            "type": "function",
                            "function": {"name": "g", "arguments": "{}"},
                        },
                    ],
                },
                {"role": "user", "content": "q2"},
            ],
            system_prompt_content="Canonical.",
        )
        state = await restore_session(ctx, session_id=8)
        # rebuilt: canonical prompt + user + assistant + 2 synthesized tools + user
        assert (
            state.result.fetched,
            state.result.synthesized,
            state.result.dropped,
            state.result.restored,
        ) == (4, 2, 1, 6)


# ── Real-DB persistence after a committed restore (sess001 regression) ──────────

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

    def _make(target: str = "session", db_config=None) -> _FakeSQLiteHelper:  # noqa: ARG001 — target kept for factory-signature parity, intentionally unused
        return _FakeSQLiteHelper(conn)

    with (
        patch("agent.session.SQLiteHelper", side_effect=_make),
        patch("agent.session_message_repo.SQLiteHelper", side_effect=_make),
    ):
        s = AgentSession(db_config=MIN_DB_CONFIG)
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
    ctx.stats = RuntimeStats()  # rollback copies fields via dataclasses.fields
    ctx.turn.current_turn_id = None  # idle: required by the transition service
    return ctx


def _make_service(ctx: MagicMock) -> SessionTransitionService:
    persister = MagicMock()
    persister.capture_snapshot.return_value = MagicMock()
    persister.persist_session_memories = AsyncMock()
    persister.persist_session_diagnostics = AsyncMock()
    return SessionTransitionService(ctx, persister)


class TestRestorePersistenceRealDB:
    """After a committed transition, persistence must bind to the restored session_id."""

    async def test_persist_after_restore_attributes_to_restored_id(
        self,
        restore_env: tuple[AgentSession, sqlite3.Connection, int],
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        s, conn, original_sid = restore_env
        ctx = _make_restore_ctx(s)
        generation_before = s.generation
        with caplog.at_level(logging.WARNING):
            await _make_service(ctx).load(200)
        assert s.session_id == 200
        assert s.generation == generation_before + 1  # REQ-001 generation bump on load

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
            if "Persistence skipped" in r.getMessage()
            or "Invalid role" in r.getMessage()
        ]

    async def test_restore_keeps_both_session_rows(
        self, restore_env: tuple[AgentSession, sqlite3.Connection, int]
    ) -> None:
        s, conn, original_sid = restore_env
        await _make_service(_make_restore_ctx(s)).load(200)
        # AC-003: restore is non-destructive; both sessions rows survive.
        sids = {r[0] for r in conn.execute("SELECT session_id FROM sessions")}
        assert sids == {original_sid, 200}

    async def test_restore_of_orphan_session_keeps_db_row_count(
        self, restore_env: tuple[AgentSession, sqlite3.Connection, int]
    ) -> None:
        """AC-003 (memory-only): restoring a session whose last assistant row
        has orphaned tool_calls must not write synthesized rows to the DB."""
        s, conn, _ = restore_env
        conn.execute(
            "INSERT INTO messages (session_id, role, content, tool_calls) "
            "VALUES (200, 'assistant', '', ?)",
            (
                json.dumps(
                    [
                        {
                            "id": "call_orphan",
                            "type": "function",
                            "function": {"name": "f", "arguments": "{}"},
                        }
                    ]
                ),
            ),
        )
        conn.commit()
        before = conn.execute(
            "SELECT COUNT(*) FROM messages WHERE session_id = 200"
        ).fetchone()[0]

        ctx = _make_restore_ctx(s)
        result = await _make_service(ctx).load(200)

        after = conn.execute(
            "SELECT COUNT(*) FROM messages WHERE session_id = 200"
        ).fetchone()[0]
        assert after == before
        # The synthesized pairing exists only in the in-memory history, and the
        # service reports it through the separate count (REQ-009).
        assert result.synthesized == 1
        tool_rows = [m for m in ctx.conv.history if m["role"] == "tool"]
        assert [m["tool_call_id"] for m in tool_rows] == ["call_orphan"]
        assert "interrupted" in tool_rows[0]["content"]

    async def test_failed_restore_leaves_live_session_intact(
        self, restore_env: tuple[AgentSession, sqlite3.Connection, int]
    ) -> None:
        """AC-1 through the real builder: a missing target id leaves everything."""
        s, conn, original_sid = restore_env
        ctx = _make_restore_ctx(s)
        ctx.conv.history = [{"role": "user", "content": "live turn"}]
        generation_before = s.generation
        with pytest.raises(SessionNotFoundError):
            await _make_service(ctx).load(123456)
        assert s.session_id == original_sid
        assert s.generation == generation_before
        assert ctx.conv.history == [{"role": "user", "content": "live turn"}]
