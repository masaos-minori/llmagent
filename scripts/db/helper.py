#!/usr/bin/env python3
"""scripts/db/helper.py

SQLite connection manager for the RAG, session, and workflow databases.

Provides open/close lifecycle with optional sqlite-vec extension and WAL setup.
target="rag" (default) loads vec extension by default.
target="session" loads it too; target="workflow" skips it by default.
Config is resolved at construction time; failure raises RuntimeError immediately.
"""

import logging
import os
import sqlite3
from collections.abc import Generator
from contextlib import contextmanager
from enum import StrEnum
from typing import Any
from urllib.request import pathname2url

from db.config import build_db_config
from db.models import DbHealthMetrics, WalCheckpointCounts

logger = logging.getLogger(__name__)

_DEFAULT_BUSY_TIMEOUT_MS: int = 30000


def coalesce_str(value: str | None, default: str = "") -> str:
    """Return value if not None, otherwise return default."""
    return value if value is not None else default


def apply_connection_pragmas(
    conn: sqlite3.Connection,
    *,
    busy_timeout_ms: int = _DEFAULT_BUSY_TIMEOUT_MS,
    write_mode: bool = True,
    read_only: bool = False,
) -> None:
    """Apply WAL/synchronous=NORMAL/busy_timeout/foreign_keys pragmas to a connection.

    read_only: probe mode (REQ-001) — applies only busy_timeout and returns before
    the journal_mode/synchronous/foreign_keys statements; those are write-path policy.
    """
    if read_only:
        conn.execute(f"PRAGMA busy_timeout={busy_timeout_ms}")  # nosec B608
        return
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute(f"PRAGMA busy_timeout={busy_timeout_ms}")  # nosec B608
    if write_mode:
        conn.execute("PRAGMA foreign_keys=ON")


class DbTarget(StrEnum):
    """SQLite database target type."""

    RAG = "rag"
    SESSION = "session"
    WORKFLOW = "workflow"


class SQLiteHelper:
    """SQLite connection manager with optional sqlite-vec extension; WAL/synchronous=NORMAL/busy_timeout applied to every connection.

    Connections default to sqlite3 check_same_thread=True; False is only for
    sequential cross-thread reuse (see open/_connect).
    """

    _CHECKPOINT_MODES: frozenset[str] = frozenset(
        {"PASSIVE", "FULL", "RESTART", "TRUNCATE"},
    )

    def __init__(
        self,
        target: DbTarget | str = "rag",
        *,
        db_path: str | None = None,
        sqlite_vec_so: str = "",
        sqlite_timeout: int = 30,
        sqlite_busy_timeout_ms: int = 30000,
        check_same_thread: bool = True,
    ) -> None:
        """Accepts DbTarget enum members or string literals ('rag', 'session', 'workflow').

        When db_path is provided, bypasses build_db_config() and uses the supplied path and
        connection settings directly. This allows callers (e.g. MCP servers) to self-contain
        their DB config without loading agent.toml.

        check_same_thread: sqlite3 same-thread assertion (default True). Set False only
        for connections reused sequentially across threads (see open/_connect).
        """
        self.conn: sqlite3.Connection | None = None
        self._reuse_connection: bool = False
        self._check_same_thread = check_same_thread
        # Sidecar names that did not exist when the last read-only open began;
        # close() unlinks the ones that open created (REQ-006).
        self._ro_residue: list[str] = []

        if db_path is not None:
            self._target = "explicit"
            self._db_path = db_path
            self._default_load_vec = bool(sqlite_vec_so)
            self._vec_so = sqlite_vec_so
            self._sqlite_timeout = sqlite_timeout
            self._busy_timeout_ms = sqlite_busy_timeout_ms
            return

        if isinstance(target, DbTarget):
            resolved = target.value
        elif target in ("rag", "session", "workflow"):
            resolved = target
        else:
            raise ValueError(
                f"target must be 'rag', 'session', or 'workflow', got: {target!r}"
            )
        self._target = resolved
        self._default_load_vec = resolved in ("rag", "session")
        try:
            db_cfg = build_db_config()
        except ValueError as e:
            raise RuntimeError(
                f"DbConfig load failed for target={target!r}: {e}"
            ) from e
        if resolved == "rag":
            self._db_path = db_cfg.rag_db_path
        elif resolved == "session":
            self._db_path = db_cfg.session_db_path
        else:
            self._db_path = db_cfg.workflow_db_path
        self._vec_so = db_cfg.sqlite_vec_so
        self._sqlite_timeout = db_cfg.sqlite_timeout
        self._busy_timeout_ms = db_cfg.sqlite_busy_timeout_ms

    @property
    def DB_PATH(self) -> str:
        """Return the configured DB path for this instance's target."""
        return self._db_path

    def _require_conn(self) -> sqlite3.Connection:
        """Return self.conn or raise RuntimeError if not open."""
        if self.conn is None:
            raise RuntimeError("DB not open — call open() first")
        return self.conn

    def _connect(self) -> sqlite3.Connection:
        """Open a raw SQLite connection; raise on DB_PATH misconfiguration.

        check_same_thread is passed from the instance default; False connections are
        only legal for sequential cross-thread use, never concurrent.
        """
        if not self._db_path:
            raise ValueError(
                f"{self._target}_db_path is not configured in agent.toml or DB config"
            )
        self._ro_residue = []
        try:
            return sqlite3.connect(
                self._db_path,
                timeout=self._sqlite_timeout,
                check_same_thread=self._check_same_thread,
            )
        except sqlite3.OperationalError as e:
            logger.error("Failed to connect to '%s': %s", self._db_path, e)
            raise

    def _connect_read_only(self) -> sqlite3.Connection:
        """Open a raw read-only SQLite connection via a mode=ro URI.

        A missing path surfaces sqlite3.OperationalError; a read-only connect
        never creates the main file (REQ-001, AC-2). SQLite still creates
        -wal/-shm sidecars when probing a WAL-mode database; close() unlinks
        the sidecars this open created and nothing that already existed or was
        written by another connection (REQ-006). The path is escaped with
        pathname2url so exotic paths stay valid URIs.
        """
        if not self._db_path:
            raise ValueError(
                f"{self._target}_db_path is not configured in agent.toml or DB config"
            )
        self._ro_residue = [
            self._db_path + suffix
            for suffix in ("-wal", "-shm")
            if not os.path.exists(self._db_path + suffix)
        ]
        uri = f"file:{pathname2url(self._db_path)}?mode=ro"
        try:
            return sqlite3.connect(
                uri,
                uri=True,
                timeout=self._sqlite_timeout,
                check_same_thread=self._check_same_thread,
            )
        except sqlite3.OperationalError as e:
            logger.error("Failed to connect read-only to '%s': %s", self._db_path, e)
            raise

    @staticmethod
    def _wal_is_hot(wal_path: str) -> bool:
        """True when -wal exists with content: another connection owns it.

        A stat failure cannot tell whether the WAL is hot, so it reports hot
        and the caller preserves everything.
        """
        try:
            return os.path.exists(wal_path) and os.stat(wal_path).st_size > 0
        except OSError:
            return True

    def _cleanup_read_only_residue(self) -> None:
        """Unlink the -wal/-shm sidecars a read-only open created (REQ-006).

        Only names absent at the pre-open snapshot are candidates: sidecars
        that already existed belong to another connection's hot WAL and are
        never touched. A candidate -wal that is no longer empty was written
        by someone else after the snapshot, so it and its -shm are preserved;
        empty sidecars this probe created are removed (log-and-continue).
        """
        wal_path = self._db_path + "-wal" if self._db_path else ""
        wal_hot = self._wal_is_hot(wal_path) if wal_path else True
        for path in self._ro_residue:
            if wal_hot or (path == wal_path and self._wal_is_hot(path)):
                continue  # a hot WAL is live, or another connection wrote it
            try:
                if os.path.exists(path):
                    os.remove(path)
            except OSError as exc:
                logger.warning(
                    "Failed to remove read-only probe residue %s: %s", path, exc
                )
        self._ro_residue = []

    def _configure_connection(
        self,
        conn: sqlite3.Connection,
        *,
        use_vec: bool,
        write_mode: bool,
        read_only: bool,
    ) -> None:
        """Load the vec extension (when configured) and apply the pragma set."""
        if use_vec and self._vec_so:
            self._load_vec_extension(conn)
        self._apply_connection_pragmas(conn, write_mode=write_mode, read_only=read_only)

    def _load_vec_extension(self, conn: sqlite3.Connection) -> None:
        """Load the sqlite-vec extension and immediately disable extension loading."""
        if not self._vec_so:
            raise ValueError(
                "sqlite_vec_so is not configured — cannot load vec extension"
            )
        try:
            conn.enable_load_extension(True)
            conn.load_extension(self._vec_so)
            conn.enable_load_extension(False)
        except sqlite3.OperationalError as e:
            conn.close()
            logger.error("Failed to load sqlite-vec '%s': %s", self._vec_so, e)
            raise

    def _apply_connection_pragmas(
        self,
        conn: sqlite3.Connection,
        *,
        write_mode: bool,
        read_only: bool = False,
    ) -> None:
        """Apply WAL/synchronous=NORMAL/busy_timeout; foreign_keys enforced only in write_mode.

        read_only forwards probe mode to apply_connection_pragmas (busy_timeout only).
        """
        apply_connection_pragmas(
            conn,
            busy_timeout_ms=self._busy_timeout_ms,
            write_mode=write_mode,
            read_only=read_only,
        )

    def open(
        self,
        *,
        write_mode: bool = False,
        read_only: bool = False,
        row_factory: bool = False,
        load_vec: bool | None = None,
        reuse_connection: bool = False,
        check_same_thread: bool | None = None,
    ) -> "SQLiteHelper":
        """Open a connection with optional vec extension and WAL pragmas.

        load_vec: None = use instance default (True for rag and session, False for
            workflow).
        write_mode: enforce FK constraints.
        read_only: open via a mode=ro URI and apply only busy_timeout; a missing
            file raises sqlite3.OperationalError and is never created (REQ-001).
            Any -wal/-shm sidecar the WAL-mode open creates is removed at close
            (REQ-006); pre-existing or hot sidecars are left untouched.
        row_factory: enable column-name access on result rows.
        reuse_connection: skip reconnect if already connected; skip close in __exit__.
            A reused connection keeps the mode it was opened with: read_only cannot
            re-configure an existing connection (mirrors the check_same_thread caveat).
        check_same_thread: None = use instance default (True); an explicit value
            applies to this open and becomes the instance default for subsequent
            opens (mirrors how the override feeds _connect). False is legal only for
            sequential cross-thread use, never concurrent. An override cannot
            re-configure a connection already opened via reuse_connection.
        """
        self._reuse_connection = reuse_connection
        if reuse_connection and self.conn is not None:
            return self
        if check_same_thread is not None:
            self._check_same_thread = check_same_thread
        use_vec = self._default_load_vec if load_vec is None else load_vec
        conn = self._connect_read_only() if read_only else self._connect()
        try:
            self._configure_connection(
                conn, use_vec=use_vec, write_mode=write_mode, read_only=read_only
            )
        except Exception:
            if read_only:
                # A failed probe must leave no residue behind (REQ-006): drop the
                # connection and any sidecar its open created before re-raising.
                conn.close()
                self._cleanup_read_only_residue()
            raise
        if row_factory:
            conn.row_factory = sqlite3.Row
        self.conn = conn
        logger.debug(
            "SQLite connection opened: %s (write=%s)", self._db_path, write_mode
        )
        return self

    def __enter__(self) -> "SQLiteHelper":
        """Return self for context manager usage."""
        return self

    def __exit__(self, *_: object) -> None:
        """Close the connection when exiting the context if not reusing."""
        if not self._reuse_connection:
            self.close()

    def close(self) -> None:
        """Close self.conn if open and reset it to None.

        A read-only connection cannot checkpoint, so any sidecar its open
        created is unlinked here (REQ-006); write-path opens leave nothing
        recorded and are unaffected.
        """
        if self.conn is None:
            return
        try:
            self.conn.close()
        except OSError as e:
            logger.warning("Error while closing SQLite connection: %s", e)
        finally:
            self.conn = None
            self._cleanup_read_only_residue()

    @contextmanager
    def _begin_transaction(self, mode: str) -> Generator[None]:
        """Wrap a block in BEGIN <mode>...COMMIT with rollback on exception.

        Rolls back on any normal exception (not just sqlite3.Error), ensuring
        no dangling transaction remains. Re-raises the original exception.
        Does not catch BaseException (KeyboardInterrupt, SystemExit).
        """
        conn = self._require_conn()
        conn.execute(f"BEGIN {mode}")
        try:
            yield
            conn.execute("COMMIT")
        except Exception:
            try:
                conn.execute("ROLLBACK")
            except sqlite3.OperationalError:
                pass
            raise

    @contextmanager
    def begin_immediate(self) -> Generator[None]:
        """Wrap a block in BEGIN IMMEDIATE...COMMIT; serializes concurrent writers."""
        with self._begin_transaction("IMMEDIATE"):
            yield

    @contextmanager
    def begin_exclusive(self) -> Generator[None]:
        """Wrap a block in BEGIN EXCLUSIVE...COMMIT; use only for VACUUM or schema migrations."""
        with self._begin_transaction("EXCLUSIVE"):
            yield

    def health_check(self) -> DbHealthMetrics:
        """Return DB health metrics (journal mode, quick_check, page stats)."""
        conn = self._require_conn()
        journal_mode = conn.execute("PRAGMA journal_mode").fetchone()[0]
        integrity = conn.execute("PRAGMA quick_check").fetchone()[0]
        page_count = conn.execute("PRAGMA page_count").fetchone()[0]
        page_size = conn.execute("PRAGMA page_size").fetchone()[0]
        freelist = conn.execute("PRAGMA freelist_count").fetchone()[0]
        return DbHealthMetrics(
            journal_mode=str(journal_mode),
            integrity=str(integrity),
            page_count=int(page_count),
            page_size=int(page_size),
            freelist_count=int(freelist),
            db_size_bytes=int(page_count) * int(page_size),
        )

    def checkpoint(self, mode: str = "TRUNCATE") -> WalCheckpointCounts:
        """Run WAL checkpoint; return WalCheckpointCounts."""
        if mode not in self._CHECKPOINT_MODES:
            raise ValueError(
                f"checkpoint mode must be one of {sorted(self._CHECKPOINT_MODES)}",
            )
        conn = self._require_conn()
        row = conn.execute(f"PRAGMA wal_checkpoint({mode})").fetchone()  # nosec B608
        result = WalCheckpointCounts(
            busy=int(row[0]),
            log_size=int(row[1]),
            pages_checkpointed=int(row[2]),
        )
        logger.info("WAL checkpoint (%s): %s", mode, result)
        return result

    def vacuum(self) -> None:
        """Rebuild the DB file in place to reclaim free pages."""
        conn = self._require_conn()
        conn.execute("VACUUM")
        logger.info("VACUUM completed: %s", self._db_path)

    def execute(
        self,
        sql: str,
        params: dict[str, Any] | tuple[Any, ...] = (),
    ) -> sqlite3.Cursor:
        """Execute a SQL statement with positional (tuple) or named (dict) params."""
        conn = self._require_conn()
        return conn.execute(sql, params)

    def executescript(self, sql_script: str) -> None:
        """Execute multiple SQL statements; commits any pending transaction first."""
        conn = self._require_conn()
        conn.executescript(sql_script)

    def executemany(
        self,
        sql: str,
        params_seq: list[tuple[Any, ...]],
    ) -> sqlite3.Cursor:
        """Execute a SQL statement once per row in params_seq."""
        conn = self._require_conn()
        return conn.executemany(sql, params_seq)

    def fetchall(
        self,
        sql: str,
        params: dict[str, Any] | tuple[Any, ...] = (),
    ) -> list[Any]:
        """Execute a SQL statement and return all result rows as a list."""
        conn = self._require_conn()
        return conn.execute(sql, params).fetchall()

    def commit(self) -> None:
        """Commit the current transaction on self.conn."""
        conn = self._require_conn()
        try:
            conn.commit()
        except sqlite3.OperationalError as e:
            logger.error("Commit failed: %s", e)
            raise
