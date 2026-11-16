"""tests/test_sqlite_helper.py
Unit tests for db/helper.py: SQLiteHelper connection management and transactions.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest
from db.helper import SQLiteHelper

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
    """Create a SQLiteHelper with an in-memory connection."""
    h = SQLiteHelper("rag")
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

        h = SQLiteHelper(DbTarget.RAG)
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
    def test_missing_workflow_db_path_mentions_agent_toml(self) -> None:
        """Missing workflow_db_path must mention agent.toml, not common.toml."""
        from unittest.mock import patch

        from db.config import DbConfig

        cfg = DbConfig(
            rag_db_path="/tmp/rag.sqlite",
            session_db_path="/tmp/session.sqlite",
            workflow_db_path="/opt/llm/db/workflow.sqlite",
        )
        with patch("db.helper.build_db_config", return_value=cfg):
            helper = SQLiteHelper("workflow")
            # Simulate the case where _db_path was never set (e.g., stale DbConfig)
            helper._db_path = ""
            with pytest.raises(ValueError, match="agent.toml"):
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
        from unittest.mock import patch

        from db.config import DbConfig

        cfg = DbConfig(
            rag_db_path="/tmp/rag.sqlite",
            session_db_path="/tmp/session.sqlite",
            workflow_db_path="/tmp/workflow.sqlite",
        )
        with patch("db.helper.build_db_config", return_value=cfg):
            assert SQLiteHelper(target)._default_load_vec is expected

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
        from unittest.mock import patch

        cfg = self._config(tmp_path, "")
        with patch("db.helper.build_db_config", return_value=cfg):
            with SQLiteHelper(target).open(write_mode=True) as db:
                assert db.conn is not None
                loaded = db.conn.execute(
                    "SELECT count(*) FROM pragma_module_list WHERE name = 'vec0'"
                ).fetchone()[0]
                assert loaded == 0
                with pytest.raises(sqlite3.OperationalError):
                    db.conn.execute(
                        "CREATE VIRTUAL TABLE v USING vec0(embedding float[4])"
                    )

    @pytest.mark.parametrize("target", ["rag", "session"])
    def test_unloadable_vec_so_raises_at_open(
        self, tmp_path: Path, target: str
    ) -> None:
        """A configured but unloadable extension fails at open, not on first use."""
        from unittest.mock import patch

        cfg = self._config(tmp_path, str(tmp_path / "missing" / "vec0.so"))
        with patch("db.helper.build_db_config", return_value=cfg):
            helper = SQLiteHelper(target)
            with pytest.raises(sqlite3.OperationalError):
                helper.open()
            assert helper.conn is None

    def test_workflow_ignores_a_configured_unloadable_vec_so(
        self, tmp_path: Path
    ) -> None:
        """Targets that own no vec0 table never attempt the load."""
        from unittest.mock import patch

        cfg = self._config(tmp_path, str(tmp_path / "missing" / "vec0.so"))
        with patch("db.helper.build_db_config", return_value=cfg):
            with SQLiteHelper("workflow").open() as db:
                assert db.conn is not None


class TestBuildDbConfigVecSoRequirement:
    """REQ-005: build_db_config() rejects an empty or absent sqlite_vec_so.

    Written first and shown failing before scripts/db/config.py gains the check.
    """

    @staticmethod
    def _patch_loader(monkeypatch: pytest.MonkeyPatch, values: dict[str, str]) -> None:
        class _FakeLoader:
            def load(self, _name: str) -> dict[str, str]:
                return values

        monkeypatch.setattr("db.config.ConfigLoader", _FakeLoader)

    def test_empty_vec_so_raises_value_error(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """An empty sqlite_vec_so makes build_db_config() raise naming the key."""
        from db.config import build_db_config

        self._patch_loader(monkeypatch, {"sqlite_vec_so": ""})
        with pytest.raises(ValueError, match="sqlite_vec_so"):
            build_db_config()

    def test_absent_key_raises_value_error(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A missing sqlite_vec_so makes build_db_config() raise naming the key."""
        from db.config import build_db_config

        self._patch_loader(monkeypatch, {})
        with pytest.raises(ValueError, match="sqlite_vec_so"):
            build_db_config()

    def test_non_empty_missing_file_is_accepted(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A non-empty sqlite_vec_so naming a missing file is accepted (existence is not checked)."""
        from db.config import build_db_config

        self._patch_loader(
            monkeypatch,
            {
                "rag_db_path": str(tmp_path / "rag.sqlite"),
                "session_db_path": str(tmp_path / "session.sqlite"),
                "workflow_db_path": str(tmp_path / "workflow.sqlite"),
                "sqlite_vec_so": str(tmp_path / "missing" / "vec0.so"),
            },
        )
        cfg = build_db_config()
        assert cfg.sqlite_vec_so == str(tmp_path / "missing" / "vec0.so")

    def test_target_based_helper_surfaces_the_failure(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """SQLiteHelper('session') wraps the build_db_config() error as its RuntimeError."""
        self._patch_loader(monkeypatch, {"sqlite_vec_so": ""})
        with pytest.raises(RuntimeError, match="DbConfig load failed"):
            SQLiteHelper("session")


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
        from db.config import build_db_config

        vec_so = Path(build_db_config().sqlite_vec_so)
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
            patch("db.helper.build_db_config", return_value=cfg),
            patch.object(SQLiteHelper, "_connect", _capture),
            patch.object(
                SQLiteHelper,
                "_apply_connection_pragmas",
                side_effect=RuntimeError("boom"),
            ),
        ):
            helper = SQLiteHelper("session")
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
            patch("db.helper.build_db_config", return_value=cfg),
            patch.object(SQLiteHelper, "_connect", _connect_with_factory),
        ):
            helper = SQLiteHelper("session")
            with pytest.raises(AttributeError):
                helper.open()

        assert helper.conn is None
        assert captured
        for conn in captured:
            self._assert_closed(conn)

    def test_reopen_closes_previous_connection(self, tmp_path: Path) -> None:
        """AC-3: a non-reuse `open()` closes the connection it replaces."""
        from unittest.mock import patch

        cfg = self._config(tmp_path, "")
        with patch("db.helper.build_db_config", return_value=cfg):
            helper = SQLiteHelper("session")
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
        from unittest.mock import patch

        db_file = tmp_path / "session.sqlite"
        cfg = self._config(tmp_path, "")
        with patch("db.helper.build_db_config", return_value=cfg):
            helper = SQLiteHelper("session")
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
