"""tests/test_sqlite_helper.py
Unit tests for db/helper.py: SQLiteHelper connection management and transactions.
"""

from __future__ import annotations

import sqlite3
import threading
from pathlib import Path

import pytest
from db.helper import SQLiteHelper

from tests.agent._config_test_defaults import MIN_DB_CONFIG, PERMISSIVE_SQLITE_VEC_SO

# ── In-memory DB helper ───────────────────────────────────────────────────────


class _InMemoryHelper:
    """Minimal SQLiteHelper drop-in backed by a real in-memory SQLite connection."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn
        self.conn = conn  # public attribute used by begin_* methods

    def open(
        self,
        *,
        write_mode: bool = False,
        row_factory: bool = False,
        read_only: bool = False,
    ) -> _InMemoryHelper:
        self._conn.row_factory = sqlite3.Row if row_factory else None
        self._read_only = read_only  # stored so tests can assert the kwarg reached
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

    def __enter__(self) -> _InMemoryHelper:
        return self

    def __exit__(self, *_: object) -> None:
        pass


@pytest.fixture
def conn() -> sqlite3.Connection:
    """Open a real in-memory SQLite connection."""
    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    c.execute(
        "CREATE TABLE IF NOT EXISTS test_table (id INTEGER PRIMARY KEY, value TEXT)"
    )
    c.commit()
    return c


@pytest.fixture
def helper(conn: sqlite3.Connection) -> SQLiteHelper:
    """Create a SQLiteHelper with an in-memory connection.

    The helper resolves no configuration file, so the typed configuration comes from the
    shared fixture; the tests below replace the connection with an in-memory one, and only
    the target decision (which owns vec0) is exercised here.
    """
    h = SQLiteHelper("rag", db_config=MIN_DB_CONFIG)
    h.conn = conn
    return h


class TestBeginImmediateRollback:
    def test_rollback_on_value_error(self, helper: SQLiteHelper) -> None:
        """begin_immediate() rolls back when ValueError is raised inside the block."""

        def _raise_value_error() -> None:
            raise ValueError("test error")

        with pytest.raises(ValueError, match="test error"):
            with helper.begin_immediate():
                _raise_value_error()

    def test_rollback_on_runtime_error(self, helper: SQLiteHelper) -> None:
        """begin_immediate() rolls back when RuntimeError is raised inside the block."""

        def _raise_runtime_error() -> None:
            raise RuntimeError("test error")

        with pytest.raises(RuntimeError, match="test error"):
            with helper.begin_immediate():
                _raise_runtime_error()

    def test_rollback_on_type_error(self, helper: SQLiteHelper) -> None:
        """begin_immediate() rolls back when TypeError is raised inside the block."""

        def _raise_type_error() -> None:
            raise TypeError("test error")

        with pytest.raises(TypeError, match="test error"):
            with helper.begin_immediate():
                _raise_type_error()

    def test_subsequent_insert_after_rollback(self, helper: SQLiteHelper) -> None:
        """A subsequent insert can run after rollback — no dangling transaction."""

        def _raise_value_error() -> None:
            raise ValueError("test error")

        with pytest.raises(ValueError):
            with helper.begin_immediate():
                helper.execute(
                    "INSERT INTO test_table (id, value) VALUES (1, 'before-error')"
                )
                _raise_value_error()

        # Verify the transaction was rolled back — insert should not have happened
        rows = helper.fetchall("SELECT * FROM test_table WHERE id=1")
        assert rows == []

        # Subsequent insert should succeed
        with helper.begin_immediate():
            helper.execute(
                "INSERT INTO test_table (id, value) VALUES (2, 'after-rollback')"
            )
        rows = helper.fetchall("SELECT * FROM test_table WHERE id=2")
        assert len(rows) == 1
        assert rows[0]["value"] == "after-rollback"

    def test_sqlite3_error_still_rolled_back(self, helper: SQLiteHelper) -> None:
        """Existing sqlite3 error behavior remains unchanged — rollback on sqlite3.Error."""
        with pytest.raises(sqlite3.IntegrityError):
            with helper.begin_immediate():
                helper.execute("INSERT INTO test_table (id, value) VALUES (1, 'first')")
                # Insert duplicate to trigger IntegrityError
                helper.execute(
                    "INSERT INTO test_table (id, value) VALUES (1, 'duplicate')"
                )

        # Verify the transaction was rolled back — no inserts should exist
        rows = helper.fetchall("SELECT * FROM test_table WHERE id=1")
        assert len(rows) == 0


class TestBeginExclusiveRollback:
    def test_rollback_on_value_error(self, helper: SQLiteHelper) -> None:
        """begin_exclusive() rolls back when ValueError is raised inside the block."""

        def _raise_value_error() -> None:
            raise ValueError("test error")

        with pytest.raises(ValueError, match="test error"):
            with helper.begin_exclusive():
                _raise_value_error()

    def test_rollback_on_runtime_error(self, helper: SQLiteHelper) -> None:
        """begin_exclusive() rolls back when RuntimeError is raised inside the block."""

        def _raise_runtime_error() -> None:
            raise RuntimeError("test error")

        with pytest.raises(RuntimeError, match="test error"):
            with helper.begin_exclusive():
                _raise_runtime_error()

    def test_rollback_on_type_error(self, helper: SQLiteHelper) -> None:
        """begin_exclusive() rolls back when TypeError is raised inside the block."""

        def _raise_type_error() -> None:
            raise TypeError("test error")

        with pytest.raises(TypeError, match="test error"):
            with helper.begin_exclusive():
                _raise_type_error()

    def test_subsequent_insert_after_rollback(self, helper: SQLiteHelper) -> None:
        """A subsequent insert can run after rollback — no dangling transaction."""

        def _raise_value_error() -> None:
            raise ValueError("test error")

        with pytest.raises(ValueError):
            with helper.begin_exclusive():
                helper.execute(
                    "INSERT INTO test_table (id, value) VALUES (1, 'before-error')"
                )
                _raise_value_error()

        # Verify the transaction was rolled back — insert should not have happened
        rows = helper.fetchall("SELECT * FROM test_table WHERE id=1")
        assert rows == []

        # Subsequent insert should succeed
        with helper.begin_exclusive():
            helper.execute(
                "INSERT INTO test_table (id, value) VALUES (2, 'after-rollback')"
            )
        rows = helper.fetchall("SELECT * FROM test_table WHERE id=2")
        assert len(rows) == 1
        assert rows[0]["value"] == "after-rollback"

    def test_sqlite3_error_still_rolled_back(self, helper: SQLiteHelper) -> None:
        """Existing sqlite3 error behavior remains unchanged — rollback on sqlite3.Error."""
        with pytest.raises(sqlite3.IntegrityError):
            with helper.begin_exclusive():
                helper.execute("INSERT INTO test_table (id, value) VALUES (1, 'first')")
                # Insert duplicate to trigger IntegrityError
                helper.execute(
                    "INSERT INTO test_table (id, value) VALUES (1, 'duplicate')"
                )

        # Verify the transaction was rolled back — no inserts should exist
        rows = helper.fetchall("SELECT * FROM test_table WHERE id=1")
        assert len(rows) == 0


class TestSQLiteHelperTargetValidation:
    """Characterization tests for SQLiteHelper.__init__'s target resolution —
    previously untested branches (DbTarget enum member, invalid string target)."""

    def test_dbtarget_enum_member_resolves_to_value(self) -> None:
        """Passing a DbTarget enum member resolves to its string value."""
        from db.helper import DbTarget

        h = SQLiteHelper(DbTarget.RAG, db_config=MIN_DB_CONFIG)
        assert h._target == "rag"
        assert h._default_load_vec is True

    def test_invalid_string_target_raises_value_error(self) -> None:
        """An unrecognized string target raises ValueError with the expected message."""
        with pytest.raises(
            ValueError,
            match=r"target must be 'rag', 'session', or 'workflow', got: 'bogus'",
        ):
            SQLiteHelper("bogus")


class TestSQLiteHelperMissingDbPathMessage:
    """The fail-closed wording names the supplied configuration, not a config file (Plan row 15)."""

    def test_constructing_without_a_configuration_names_the_contract(self) -> None:
        """A helper that is given neither a path nor a configuration raises before connecting."""
        with pytest.raises(ValueError, match="db_config must be supplied"):
            SQLiteHelper("workflow")

    def test_empty_path_names_the_supplied_configuration(self) -> None:
        """A supplied configuration that resolves to an empty path is named at connect."""
        from db.config import DbConfig

        cfg = DbConfig(
            rag_db_path="/tmp/rag.sqlite",
            session_db_path="/tmp/session.sqlite",
            workflow_db_path="/opt/llm/db/workflow.sqlite",
        )
        helper = SQLiteHelper("workflow", db_config=cfg)
        # Simulate the case where _db_path was never set (e.g., stale DbConfig)
        helper._db_path = ""
        with pytest.raises(ValueError, match="supplied DbConfig"):
            helper._connect()


class TestReuseConnection:
    def test_reuse_connection_skips_reconnect(self, tmp_path: Path) -> None:
        from unittest.mock import patch

        helper = SQLiteHelper(db_path=str(tmp_path / "test.sqlite"))
        with patch.object(helper, "_connect", wraps=helper._connect) as spy:
            helper.open(reuse_connection=True)
            first_conn = helper.conn
            helper.open(reuse_connection=True)
            assert helper.conn is first_conn
            assert spy.call_count == 1

    def test_reuse_connection_skips_close_on_exit(self, tmp_path: Path) -> None:
        helper = SQLiteHelper(db_path=str(tmp_path / "test.sqlite"))
        with helper.open(reuse_connection=True):
            pass
        assert helper.conn is not None
        helper.conn.execute("SELECT 1")


class TestSQLiteHelperVecDefault:
    """The sqlite-vec default follows ownership of vec0 tables: rag and session."""

    @pytest.mark.parametrize(
        ("target", "expected"),
        [
            ("rag", True),
            ("session", True),
            ("workflow", False),
        ],
    )
    def test_default_load_vec_per_target(self, target: str, expected: bool) -> None:

        from db.config import DbConfig

        cfg = DbConfig(
            rag_db_path="/tmp/rag.sqlite",
            session_db_path="/tmp/session.sqlite",
            workflow_db_path="/tmp/workflow.sqlite",
        )
        assert SQLiteHelper(target, db_config=cfg)._default_load_vec is expected

    def test_explicit_load_vec_overrides_default(self, tmp_path: Path) -> None:
        from unittest.mock import patch

        # Default True (sqlite_vec_so set): explicit False skips the load.
        on = SQLiteHelper(db_path=str(tmp_path / "on.sqlite"), sqlite_vec_so="/x.so")
        with patch.object(on, "_load_vec_extension") as load:
            with on.open(load_vec=False):
                pass
            load.assert_not_called()
        # Default False (no sqlite_vec_so): explicit True loads once a path is set.
        off = SQLiteHelper(db_path=str(tmp_path / "off.sqlite"))
        off._vec_so = "/x.so"
        with patch.object(off, "_load_vec_extension") as load:
            with off.open(load_vec=True):
                pass
            load.assert_called_once()


class TestSQLiteHelperVecExtensionLoading:
    """Real-connection behavior of the sqlite-vec load policy (docs/41_db, 4b)."""

    @staticmethod
    def _config(tmp_path: Path, vec_so: str) -> object:
        from db.config import DbConfig

        return DbConfig(
            rag_db_path=str(tmp_path / "rag.sqlite"),
            session_db_path=str(tmp_path / "session.sqlite"),
            workflow_db_path=str(tmp_path / "workflow.sqlite"),
            sqlite_vec_so=vec_so,
        )

    @pytest.mark.parametrize("target", ["rag", "session"])
    def test_empty_vec_so_opens_without_the_extension(
        self, tmp_path: Path, target: str
    ) -> None:
        """Empty sqlite_vec_so skips the load; a later vec0 access fails visibly."""

        cfg = self._config(tmp_path, "")
        with SQLiteHelper(target, db_config=cfg).open(write_mode=True) as db:
            assert db.conn is not None
            loaded = db.conn.execute(
                "SELECT count(*) FROM pragma_module_list WHERE name = 'vec0'"
            ).fetchone()[0]
            assert loaded == 0
            with pytest.raises(sqlite3.OperationalError):
                db.conn.execute("CREATE VIRTUAL TABLE v USING vec0(embedding float[4])")

    @pytest.mark.parametrize("target", ["rag", "session"])
    def test_unloadable_vec_so_raises_at_open(
        self, tmp_path: Path, target: str
    ) -> None:
        """A configured but unloadable extension fails at open, not on first use."""

        cfg = self._config(tmp_path, str(tmp_path / "missing" / "vec0.so"))
        helper = SQLiteHelper(target, db_config=cfg)
        with pytest.raises(sqlite3.OperationalError):
            helper.open()
        assert helper.conn is None

    def test_workflow_ignores_a_configured_unloadable_vec_so(
        self, tmp_path: Path
    ) -> None:
        """Targets that own no vec0 table never attempt the load."""

        cfg = self._config(tmp_path, str(tmp_path / "missing" / "vec0.so"))
        with SQLiteHelper("workflow", db_config=cfg).open() as db:
            assert db.conn is not None


class TestBuildDbConfigVecSoRequirement:
    """REQ-005: build_db_config() rejects an empty or absent sqlite_vec_so in the mapping it is given.

    The builder reads no configuration file, so the mapping is what the owning process passes;
    the requirement itself is asserted in tests/db/test_db_config.py (Plan row 25). What is
    asserted here is the helper side of the same boundary: a helper built from an accepted
    configuration uses exactly the values it was given, and a helper given no configuration
    fails closed.
    """

    def test_empty_vec_so_raises_value_error(self) -> None:
        """An empty sqlite_vec_so makes the builder raise naming the key."""
        from db.config import build_db_config

        with pytest.raises(ValueError, match="sqlite_vec_so"):
            build_db_config({"sqlite_vec_so": ""})

    def test_absent_key_raises_value_error(self) -> None:
        """A missing sqlite_vec_so makes the builder raise naming the key."""
        from db.config import build_db_config

        with pytest.raises(ValueError, match="sqlite_vec_so"):
            build_db_config({})

    def test_non_empty_missing_file_is_accepted(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A non-empty sqlite_vec_so naming a missing file is accepted (existence is not checked)."""
        from db.config import build_db_config

        values = {
            "rag_db_path": str(tmp_path / "rag.sqlite"),
            "session_db_path": str(tmp_path / "session.sqlite"),
            "workflow_db_path": str(tmp_path / "workflow.sqlite"),
            "sqlite_vec_so": str(tmp_path / "missing" / "vec0.so"),
        }
        cfg = build_db_config(values)
        assert cfg.sqlite_vec_so == str(tmp_path / "missing" / "vec0.so")

    def test_helper_uses_the_configuration_it_is_given(self, tmp_path: Path) -> None:
        """The helper takes the values from the configuration supplied by its caller."""
        from db.config import build_db_config

        cfg = build_db_config(
            {
                "rag_db_path": str(tmp_path / "rag.sqlite"),
                "session_db_path": str(tmp_path / "session.sqlite"),
                "workflow_db_path": str(tmp_path / "workflow.sqlite"),
                "sqlite_vec_so": str(tmp_path / "missing" / "vec0.so"),
            }
        )
        helper = SQLiteHelper("session", db_config=cfg)
        assert helper.DB_PATH == str(tmp_path / "session.sqlite")
        assert helper._vec_so == str(tmp_path / "missing" / "vec0.so")


# ── read_only open mode (dbreview004, REQ-001/REQ-006) ────────────────────────


class TestReadOnlyOpen:
    """Unit coverage for SQLiteHelper.open(read_only=True) (REQ-001/AC-1, AC-2)."""

    @staticmethod
    def _make_db(path: Path, *, wal: bool = False) -> None:
        conn = sqlite3.connect(path)
        if wal:
            conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("CREATE TABLE t (id INTEGER PRIMARY KEY)")
        conn.execute("INSERT INTO t VALUES (1)")
        conn.commit()
        conn.close()

    def test_read_only_open_skips_write_pragmas(self, tmp_path: Path) -> None:
        """REQ-001/AC-1: only busy_timeout is applied; journal_mode stays delete."""
        db_file = tmp_path / "probe.sqlite"
        self._make_db(db_file)

        helper = SQLiteHelper(db_path=str(db_file), sqlite_busy_timeout_ms=12345)
        with helper.open(read_only=True) as db:
            assert db.execute("PRAGMA journal_mode").fetchone()[0] == "delete"
            assert db.execute("PRAGMA busy_timeout").fetchone()[0] == 12345

        assert sorted(p.name for p in tmp_path.iterdir()) == ["probe.sqlite"]
        probe = sqlite3.connect(db_file)
        try:
            assert probe.execute("PRAGMA journal_mode").fetchone()[0] == "delete"
        finally:
            probe.close()

    def test_read_only_open_missing_path_raises(self, tmp_path: Path) -> None:
        """REQ-001/AC-2: a missing path raises and is never created."""
        missing = tmp_path / "missing.sqlite"

        with pytest.raises(sqlite3.OperationalError):
            SQLiteHelper(db_path=str(missing)).open(read_only=True)

        assert not missing.exists()

    def test_default_open_unchanged(self, tmp_path: Path) -> None:
        """REQ-001 default-invariance: the default open still applies WAL."""
        db_file = tmp_path / "default.sqlite"

        helper = SQLiteHelper(db_path=str(db_file), sqlite_vec_so="")
        with helper.open() as db:
            mode = db.execute("PRAGMA journal_mode").fetchone()[0]

        assert mode == "wal"

    def test_read_only_open_loads_vec_when_requested(self, tmp_path: Path) -> None:
        """Vec loading on a read-only connection is legal (Plan Design assumption)."""
        # The explicit-path route is what the test exercises, so the extension path comes from
        # the shared mirror of the shipped config rather than from a configuration load.
        vec_so = Path(PERMISSIVE_SQLITE_VEC_SO)
        if not vec_so.is_file():
            pytest.skip(f"sqlite-vec extension not available at {vec_so}")
        db_file = tmp_path / "vec.sqlite"
        self._make_db(db_file)

        helper = SQLiteHelper(db_path=str(db_file), sqlite_vec_so=str(vec_so))
        with helper.open(read_only=True, load_vec=True) as db:
            assert db.execute("SELECT vec_version()").fetchone()[0]

    def test_read_only_open_removes_sidecars_it_created(self, tmp_path: Path) -> None:
        """REQ-006: a ro open of a WAL DB leaves no new -wal/-shm residue behind."""
        db_file = tmp_path / "wal.sqlite"
        helper = SQLiteHelper(db_path=str(db_file), sqlite_vec_so="")
        with helper.open() as db:
            db.execute("CREATE TABLE t (id INTEGER PRIMARY KEY)")
            db.execute("INSERT INTO t VALUES (1)")
            db.commit()
        before_listing = sorted(p.name for p in tmp_path.iterdir())

        with helper.open(read_only=True):
            pass

        assert sorted(p.name for p in tmp_path.iterdir()) == before_listing

    def test_read_only_open_preserves_existing_sidecars(self, tmp_path: Path) -> None:
        """REQ-006: sidecars that already exist (hot WAL) are never touched."""
        db_file = tmp_path / "hot.sqlite"
        conn = sqlite3.connect(db_file)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("CREATE TABLE t (id INTEGER PRIMARY KEY)")
        conn.commit()
        other = sqlite3.connect(db_file)
        other.execute("INSERT INTO t VALUES (1)")
        other.commit()  # committed frames stay hot in -wal (well below autocheckpoint)
        before_listing = sorted(p.name for p in tmp_path.iterdir())
        assert any(name.endswith("-wal") for name in before_listing)

        helper = SQLiteHelper(db_path=str(db_file), sqlite_vec_so="")
        with helper.open(read_only=True) as db:
            rows = db.execute("SELECT id FROM t").fetchall()
        assert rows  # the hot WAL contents are visible to the probe

        assert sorted(p.name for p in tmp_path.iterdir()) == before_listing
        other.close()
        conn.close()


class TestOpenLeakSafety:
    """REQ-001..REQ-004: `open` leaves no unclosed connection on any failure path.

    The connection `open` operates on is captured by wrapping `SQLiteHelper._connect`,
    and closedness is asserted by the `ProgrammingError` a closed connection raises, so
    the check is direct instead of a proxy for the helper's reference
    (`helper.conn is None` alone only proves the reference was dropped).
    """

    @staticmethod
    def _config(tmp_path: Path, vec_so: str) -> object:
        from db.config import DbConfig

        return DbConfig(
            rag_db_path=str(tmp_path / "rag.sqlite"),
            session_db_path=str(tmp_path / "session.sqlite"),
            workflow_db_path=str(tmp_path / "workflow.sqlite"),
            sqlite_vec_so=vec_so,
        )

    @staticmethod
    def _assert_closed(conn: sqlite3.Connection) -> None:
        """Assert the connection is closed by the closed-database it refuses to use.

        `sqlite3.Connection.closed` is not available on this runtime, so the
        ProgrammingError a closed connection raises is the leak assertion.
        """
        with pytest.raises(sqlite3.ProgrammingError):
            conn.execute("SELECT 1")

    def test_post_connect_failure_closes_connection(self, tmp_path: Path) -> None:
        """AC-1: a pragma failure closes the connection and releases its locks."""
        from unittest.mock import patch

        db_file = tmp_path / "session.sqlite"
        cfg = self._config(tmp_path, "")
        captured: list[sqlite3.Connection] = []
        real_connect = SQLiteHelper._connect

        def _capture(helper: SQLiteHelper) -> sqlite3.Connection:
            conn = real_connect(helper)
            captured.append(conn)
            return conn

        with (
            patch.object(SQLiteHelper, "_connect", _capture),
            patch.object(
                SQLiteHelper,
                "_apply_connection_pragmas",
                side_effect=RuntimeError("boom"),
            ),
        ):
            helper = SQLiteHelper("session", db_config=cfg)
            with pytest.raises(RuntimeError, match="boom"):
                helper.open(write_mode=True)

        assert helper.conn is None
        assert captured
        for conn in captured:
            self._assert_closed(conn)
        # Integration proof: the failed open left no lock on the file, so a fresh
        # connection acquires an exclusive one immediately (no busy timeout hit).
        probe = sqlite3.connect(db_file)
        try:
            probe.execute("BEGIN EXCLUSIVE")
            probe.execute("ROLLBACK")
        finally:
            probe.close()

    def test_attribute_error_vec_failure_closes_connection(
        self, tmp_path: Path
    ) -> None:
        """AC-1/AC-2: an `AttributeError` from `enable_load_extension` also tears down.

        `sqlite3.Connection` is a C-extension type, so the failure is built with a
        subclass rather than by patching the class method.
        """
        from unittest.mock import patch

        class _NoLoadExtension(sqlite3.Connection):
            def enable_load_extension(self, _enable: bool) -> None:
                raise AttributeError("enable_load_extension is unavailable")

        cfg = self._config(tmp_path, str(tmp_path / "missing" / "vec0.so"))
        captured: list[sqlite3.Connection] = []

        def _connect_with_factory(helper: SQLiteHelper) -> sqlite3.Connection:
            conn = sqlite3.connect(
                helper._db_path,
                timeout=helper._sqlite_timeout,
                check_same_thread=helper._check_same_thread,
                factory=_NoLoadExtension,
            )
            captured.append(conn)
            return conn

        with (
            patch.object(SQLiteHelper, "_connect", _connect_with_factory),
        ):
            helper = SQLiteHelper("session", db_config=cfg)
            with pytest.raises(AttributeError):
                helper.open()

        assert helper.conn is None
        assert captured
        for conn in captured:
            self._assert_closed(conn)

    def test_reopen_closes_previous_connection(self, tmp_path: Path) -> None:
        """AC-3: a non-reuse `open()` closes the connection it replaces."""

        cfg = self._config(tmp_path, "")
        helper = SQLiteHelper("session", db_config=cfg)
        helper.open(write_mode=True)
        conn_a = helper.conn
        assert conn_a is not None
        helper.open(write_mode=True)
        try:
            assert helper.conn is not conn_a
            with pytest.raises(sqlite3.ProgrammingError):
                conn_a.execute("SELECT 1")
        finally:
            helper.close()

    def test_explicit_load_vec_without_vec_so_raises_value_error(
        self, tmp_path: Path
    ) -> None:
        """AC-4: explicit `load_vec=True` fails before any connection is created."""

        db_file = tmp_path / "session.sqlite"
        cfg = self._config(tmp_path, "")
        helper = SQLiteHelper("session", db_config=cfg)
        with pytest.raises(ValueError, match="sqlite_vec_so"):
            helper.open(load_vec=True)
        assert helper.conn is None
        assert not db_file.exists()
        # The instance-default path is unchanged: it opens without the extension.
        with helper.open(write_mode=True) as db:
            loaded = db.conn.execute(
                "SELECT count(*) FROM pragma_module_list WHERE name = 'vec0'"
            ).fetchone()[0]
            assert loaded == 0


class TestInterruptWhen:
    """SQLiteHelper.interrupt_when installs/removes the progress handler that
    aborts a running statement once the stop event is set.

    Coverage is asserted by real behavior on a real in-memory connection: a
    pre-set event aborts a long query, and removing the hook lets the same query
    complete. ``sqlite3.Connection.get_progress_handler`` is unavailable on this
    runtime, so hook removal is proven functionally rather than by introspection.
    """

    _ABORT_CTE = (
        "WITH RECURSIVE c(x) AS (VALUES(1) "
        "UNION ALL SELECT x + 1 FROM c WHERE x < 100000) "
        "SELECT sum(x) FROM c"
    )

    def test_check_every_below_one_raises_value_error(
        self, helper: SQLiteHelper
    ) -> None:
        """check_every < 1 raises ValueError before any handler is installed."""
        with pytest.raises(ValueError, match="check_every must be >= 1"):
            helper.interrupt_when(threading.Event(), check_every=0)

    def test_without_open_connection_raises_runtime_error(
        self, helper: SQLiteHelper
    ) -> None:
        """A helper with no open connection raises RuntimeError from _require_conn."""
        helper.conn = None
        with pytest.raises(RuntimeError, match="DB not open"):
            helper.interrupt_when(threading.Event())

    def test_installs_handler_that_aborts_when_set(self, helper: SQLiteHelper) -> None:
        """A pre-set stop event aborts a running statement via the progress handler."""
        stop = threading.Event()
        stop.set()  # pre-set: deterministic abort on the first progress check
        helper.interrupt_when(stop, check_every=1)
        with pytest.raises(sqlite3.OperationalError, match="interrupted"):
            helper._require_conn().execute(self._ABORT_CTE)

    def test_removes_handler_when_stop_is_none(self, helper: SQLiteHelper) -> None:
        """interrupt_when(None) removes the hook; the aborted query then completes."""
        stop = threading.Event()
        stop.set()
        helper.interrupt_when(stop)  # install
        helper.interrupt_when(None)  # remove
        result = helper._require_conn().execute(self._ABORT_CTE).fetchone()
        assert result[0] == 5000050000


class TestCommitOnExit:
    """Leaving the open() context closes the connection without committing."""

    @staticmethod
    def _rows(path: Path) -> list[tuple[int]]:
        conn = sqlite3.connect(path)
        try:
            return conn.execute("SELECT v FROM t").fetchall()
        finally:
            conn.close()

    @staticmethod
    def _helper_with_table(path: Path) -> SQLiteHelper:
        helper = SQLiteHelper(db_path=str(path))
        with helper.open(write_mode=True) as db:
            db.execute("CREATE TABLE t (v INTEGER)")
            db.commit()
        return helper

    def test_write_without_commit_is_discarded_at_exit(self, tmp_path: Path) -> None:
        path = tmp_path / "commit.sqlite"
        helper = self._helper_with_table(path)

        with helper.open(write_mode=True) as db:
            db.execute("INSERT INTO t (v) VALUES (1)")

        assert self._rows(path) == []

    def test_write_with_commit_persists(self, tmp_path: Path) -> None:
        path = tmp_path / "commit.sqlite"
        helper = self._helper_with_table(path)

        with helper.open(write_mode=True) as db:
            db.execute("INSERT INTO t (v) VALUES (1)")
            db.commit()

        assert self._rows(path) == [(1,)]
