"""tests/db/test_write_gate.py

Unit tests for db/write_gate.py and the gate checks in db/helper.py: the three
gate states, the refusal of every SQLiteHelper write entry point, the
authorized-operation context, the statement classifier, the read paths that are
never gated, and the refused-write counter (cliplc004 REQ-004, REQ-005; AC-2).
"""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from pathlib import Path

import pytest
from db.helper import SQLiteHelper
from db.write_gate import (
    WriteGate,
    WriteGateClosed,
    WriteGateState,
    get_write_gate,
    is_write_statement,
)

_SCHEMA = "CREATE TABLE probe (id INTEGER PRIMARY KEY, val TEXT);"


@pytest.fixture()
def gate() -> Iterator[WriteGate]:
    """The process-wide gate, reset before and after the case.

    SQLiteHelper consults the module-level gate, so a case that closes it must
    hand the next test in the same xdist worker an open one.
    """
    shared = get_write_gate()
    shared.reset()
    yield shared
    shared.reset()


@pytest.fixture()
def helper(tmp_path: Path) -> Iterator[SQLiteHelper]:
    """A tmp-file-backed SQLiteHelper with one table and one open connection."""
    db_path = tmp_path / "probe.db"
    conn = sqlite3.connect(db_path)
    conn.execute(_SCHEMA)
    conn.commit()
    conn.close()
    helper = SQLiteHelper(db_path=str(db_path))
    helper.open(write_mode=True)
    try:
        yield helper
    finally:
        helper.close()


class TestGateStateMachine:
    def test_a_new_gate_is_open(self) -> None:
        assert WriteGate().state is WriteGateState.OPEN

    def test_close_steps_open_to_closing_to_closed(self) -> None:
        gate = WriteGate()
        gate.close()
        assert gate.state is WriteGateState.CLOSING
        gate.close()
        assert gate.state is WriteGateState.CLOSED

    def test_close_is_idempotent_past_closed(self) -> None:
        gate = WriteGate()
        gate.close()
        gate.close()
        gate.close()
        assert gate.state is WriteGateState.CLOSED

    def test_close_now_goes_straight_to_closed(self) -> None:
        gate = WriteGate()
        gate.close_now()
        assert gate.state is WriteGateState.CLOSED

    def test_reset_returns_the_gate_to_open_with_a_zero_counter(self) -> None:
        gate = WriteGate()
        gate.close_now()
        with pytest.raises(WriteGateClosed):
            gate.check_write("execute")
        gate.reset()
        assert gate.state is WriteGateState.OPEN
        assert gate.refused_count == 0


class TestCheckWrite:
    def test_open_allows_a_write_and_counts_nothing(self) -> None:
        gate = WriteGate()
        gate.check_write("execute")
        assert gate.refused_count == 0

    def test_closing_refuses_an_unauthorized_write(self) -> None:
        gate = WriteGate()
        gate.close()
        with pytest.raises(WriteGateClosed):
            gate.check_write("execute")

    def test_closed_refuses_every_write(self) -> None:
        gate = WriteGate()
        gate.close_now()
        with pytest.raises(WriteGateClosed):
            gate.check_write("execute")
        with pytest.raises(WriteGateClosed):
            gate.check_write("commit")

    def test_each_refusal_increments_the_counter_once(self) -> None:
        gate = WriteGate()
        gate.close_now()
        for _ in range(3):
            with pytest.raises(WriteGateClosed):
                gate.check_write("execute")
        assert gate.refused_count == 3

    def test_a_swallowed_refusal_is_still_counted(self) -> None:
        """REQ-012: the count is behavior, so a caller that eats the error shows up."""
        gate = WriteGate()
        gate.close_now()
        try:
            gate.check_write("execute")
        except WriteGateClosed:
            pass
        assert gate.refused_count == 1

    def test_the_refusal_names_the_state_and_operation_but_no_path(self) -> None:
        gate = WriteGate()
        gate.close_now()
        with pytest.raises(WriteGateClosed) as excinfo:
            gate.check_write("execute")
        message = str(excinfo.value)
        assert "closed" in message
        assert "execute" in message
        assert "/" not in message


class TestAuthorizeContext:
    def test_authorize_lets_a_write_through_while_closing(self) -> None:
        gate = WriteGate()
        gate.close()
        with gate.authorize("persist_snapshot"):
            gate.check_write("execute")
        assert gate.refused_count == 0

    def test_authorize_lets_a_write_through_when_closed(self) -> None:
        gate = WriteGate()
        gate.close_now()
        with gate.authorize("checkpoint"):
            gate.check_write("checkpoint")

    def test_the_authorization_does_not_outlive_the_block(self) -> None:
        gate = WriteGate()
        gate.close_now()
        with gate.authorize("backup"):
            gate.check_write("execute")
        with pytest.raises(WriteGateClosed):
            gate.check_write("execute")

    def test_an_exception_inside_the_block_still_clears_the_authorization(self) -> None:
        gate = WriteGate()
        gate.close_now()
        with pytest.raises(RuntimeError, match="step failed"):
            with gate.authorize("persist_snapshot"):
                raise RuntimeError("step failed")
        with pytest.raises(WriteGateClosed):
            gate.check_write("execute")

    def test_nested_authorizations_release_inner_first(self) -> None:
        gate = WriteGate()
        gate.close_now()
        with gate.authorize("checkpoint"):
            with gate.authorize("backup"):
                gate.check_write("execute")
            gate.check_write("checkpoint")
        with pytest.raises(WriteGateClosed):
            gate.check_write("execute")

    def test_authorize_names_the_step_that_holds_it(self) -> None:
        gate = WriteGate()
        with gate.authorize("settle_writers") as step:
            assert step == "settle_writers"
            assert gate.authorized_step == "settle_writers"
        assert gate.authorized_step is None

    def test_authorize_rejects_an_empty_step_name(self) -> None:
        """An unnameable authorization is refused: the report needs a step name."""
        gate = WriteGate()
        with pytest.raises(ValueError, match="non-empty"):
            with gate.authorize(""):
                pass  # unreachable
        assert gate.authorized_step is None


class TestStatementClassifier:
    @pytest.mark.parametrize(
        "sql",
        [
            "SELECT val FROM probe",
            "  select 1",
            "EXPLAIN SELECT val FROM probe",
            "PRAGMA journal_mode",
            "PRAGMA quick_check",
            "-- a comment does not hide a read\nSELECT 1",
            "/* a block comment does not hide a read */ SELECT 1",
        ],
    )
    def test_read_statements_are_not_writes(self, sql: str) -> None:
        assert is_write_statement(sql) is False

    @pytest.mark.parametrize(
        "sql",
        [
            "INSERT INTO probe (val) VALUES (?)",
            "insert into probe (val) values (?)",
            "INSERT OR IGNORE INTO probe (val) VALUES (?)",
            "REPLACE INTO probe (id, val) VALUES (?, ?)",
            "UPDATE probe SET val = ?",
            "DELETE FROM probe WHERE id = ?",
            "CREATE TABLE other (id INTEGER)",
            "DROP TABLE probe",
            "VACUUM",
            "PRAGMA journal_mode=WAL",
            "PRAGMA foreign_keys=ON",
            "PRAGMA wal_checkpoint(TRUNCATE)",
            "WITH counted AS (SELECT 1) SELECT * FROM counted",
            "VALUES (1)",
            "SOMETHING ELSE",
            "",
            "-- only a comment",
            "/* unterminated block comment",
            "/* a block comment does not hide a write */ INSERT INTO probe (val) VALUES (1)",
        ],
    )
    def test_write_statements_and_unknown_keywords_are_writes(self, sql: str) -> None:
        """Fail closed: an operation the classifier cannot name is treated as a write."""
        assert is_write_statement(sql) is True


class TestHelperWriteEntryPoints:
    """Every write entry point the Plan lists refuses once the gate is closed."""

    def test_open_in_write_mode_is_refused(
        self, gate: WriteGate, tmp_path: Path
    ) -> None:
        helper = SQLiteHelper(db_path=str(tmp_path / "probe.db"))
        gate.close_now()
        with pytest.raises(WriteGateClosed):
            helper.open(write_mode=True)
        assert helper.conn is None

    def test_open_in_write_mode_is_allowed_inside_an_authorization(
        self, gate: WriteGate, tmp_path: Path
    ) -> None:
        helper = SQLiteHelper(db_path=str(tmp_path / "probe.db"))
        gate.close_now()
        with gate.authorize("persist_snapshot"):
            helper.open(write_mode=True)
        helper.close()

    def test_execute_of_a_write_is_refused(
        self, gate: WriteGate, helper: SQLiteHelper
    ) -> None:
        gate.close_now()
        with pytest.raises(WriteGateClosed):
            helper.execute("INSERT INTO probe (val) VALUES (?)", ("x",))
        assert gate.refused_count == 1

    def test_executemany_is_refused(
        self, gate: WriteGate, helper: SQLiteHelper
    ) -> None:
        gate.close_now()
        with pytest.raises(WriteGateClosed):
            helper.executemany("INSERT INTO probe (val) VALUES (?)", [("a",), ("b",)])

    def test_executescript_is_refused(
        self, gate: WriteGate, helper: SQLiteHelper
    ) -> None:
        gate.close_now()
        with pytest.raises(WriteGateClosed):
            helper.executescript("INSERT INTO probe (val) VALUES ('a');")

    def test_commit_of_an_open_transaction_is_refused(
        self, gate: WriteGate, helper: SQLiteHelper
    ) -> None:
        """A write that began before shutdown cannot be made durable after it."""
        helper.execute("INSERT INTO probe (val) VALUES (?)", ("in-flight",))
        gate.close_now()
        with pytest.raises(WriteGateClosed):
            helper.commit()

    def test_commit_with_nothing_to_commit_is_not_a_write(
        self, gate: WriteGate, helper: SQLiteHelper
    ) -> None:
        helper.execute("SELECT val FROM probe").fetchall()
        gate.close_now()
        helper.commit()
        assert gate.refused_count == 0

    def test_begin_immediate_is_refused(
        self, gate: WriteGate, helper: SQLiteHelper
    ) -> None:
        gate.close_now()
        with pytest.raises(WriteGateClosed):
            with helper.begin_immediate():
                pass

    def test_begin_exclusive_is_refused(
        self, gate: WriteGate, helper: SQLiteHelper
    ) -> None:
        gate.close_now()
        with pytest.raises(WriteGateClosed):
            with helper.begin_exclusive():
                pass

    def test_checkpoint_is_refused(self, gate: WriteGate, helper: SQLiteHelper) -> None:
        gate.close_now()
        with pytest.raises(WriteGateClosed):
            helper.checkpoint("TRUNCATE")

    def test_vacuum_is_refused(self, gate: WriteGate, helper: SQLiteHelper) -> None:
        gate.close_now()
        with pytest.raises(WriteGateClosed):
            helper.vacuum()

    def test_an_authorized_step_writes_through_the_closed_gate(
        self, gate: WriteGate, helper: SQLiteHelper
    ) -> None:
        gate.close_now()
        with gate.authorize("persist_snapshot"):
            helper.execute("INSERT INTO probe (val) VALUES (?)", ("authorized",))
            helper.commit()
        rows = helper.fetchall("SELECT val FROM probe")
        assert [row[0] for row in rows] == ["authorized"]
        assert gate.refused_count == 0

    def test_a_write_after_the_authorized_step_is_refused(
        self, gate: WriteGate, helper: SQLiteHelper
    ) -> None:
        gate.close_now()
        with gate.authorize("persist_snapshot"):
            helper.execute("INSERT INTO probe (val) VALUES (?)", ("authorized",))
        with pytest.raises(WriteGateClosed):
            helper.execute("INSERT INTO probe (val) VALUES (?)", ("late",))


class TestReadPathsAreNeverGated:
    def test_execute_of_a_select_succeeds_in_every_state(
        self, gate: WriteGate, helper: SQLiteHelper
    ) -> None:
        for step in (None, gate.close, gate.close):
            if step is not None:
                step()
            rows = helper.execute("SELECT val FROM probe").fetchall()
            assert rows == []
        assert gate.state is WriteGateState.CLOSED
        assert gate.refused_count == 0

    def test_fetchall_succeeds_when_closed(
        self, gate: WriteGate, helper: SQLiteHelper
    ) -> None:
        gate.close_now()
        assert helper.fetchall("SELECT val FROM probe") == []

    def test_health_check_succeeds_when_closed(
        self, gate: WriteGate, helper: SQLiteHelper
    ) -> None:
        gate.close_now()
        metrics = helper.health_check()
        assert metrics.journal_mode.lower() == "wal"

    def test_interrupt_when_succeeds_when_closed(
        self, gate: WriteGate, helper: SQLiteHelper
    ) -> None:
        gate.close_now()
        helper.interrupt_when(None)

    def test_a_read_only_open_succeeds_when_closed(
        self, gate: WriteGate, tmp_path: Path
    ) -> None:
        db_path = tmp_path / "probe.db"
        conn = sqlite3.connect(db_path)
        conn.execute(_SCHEMA)
        conn.commit()
        conn.close()
        helper = SQLiteHelper(db_path=str(db_path))
        gate.close_now()
        with helper.open() as opened:
            assert opened.fetchall("SELECT val FROM probe") == []


class TestProcessWideAccessor:
    def test_get_write_gate_returns_the_same_instance(self) -> None:
        assert get_write_gate() is get_write_gate()

    def test_the_helper_and_the_accessor_see_one_gate(
        self, gate: WriteGate, helper: SQLiteHelper
    ) -> None:
        """REQ-005: the refusal is enforced in the db layer, not per caller."""
        assert gate is get_write_gate()
        gate.close_now()
        with pytest.raises(WriteGateClosed):
            helper.execute("INSERT INTO probe (val) VALUES (?)", ("x",))
