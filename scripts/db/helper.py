#!/usr/bin/env python3
"""db/helper.py
SQLite connection manager for RAG, session, workflow, and eventbus databases.

Provides open/close lifecycle with optional sqlite-vec extension and WAL setup.
target="rag" (default) loads vec extension by default.
target="session", "workflow", "eventbus" skip vec extension by default.
Config is resolved at construction time; failure raises RuntimeError immediately.
"""

import logging
import sqlite3
from collections.abc import Generator
from contextlib import contextmanager
from enum import StrEnum
from typing import Any

from db.config import build_db_config
from db.models import DbHealthMetrics, WalCheckpointCounts

logger = logging.getLogger(__name__)

_DEFAULT_BUSY_TIMEOUT_MS: int = 30000


class DbTarget(StrEnum):
    """SQLite database target type."""

    RAG = "rag"
    SESSION = "session"
    WORKFLOW = "workflow"
    EVENTBUS = "eventbus"


class SQLiteHelper:
    """SQLite connection manager with optional sqlite-vec extension; WAL/synchronous=NORMAL/busy_timeout applied to every connection."""

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
    ) -> None:
        """Accepts DbTarget enum members or string literals ('rag', 'session', 'workflow', 'eventbus').

        When db_path is provided, bypasses build_db_config() and uses the supplied path and
        connection settings directly. This allows callers (e.g. MCP servers) to self-contain
        their DB config without loading agent.toml.
        """
        self.conn: sqlite3.Connection | None = None
        self._reuse_connection: bool = False

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
        else:
            if target not in ("rag", "session", "workflow", "eventbus"):
                raise ValueError(
                    f"target must be 'rag', 'session', 'workflow', or 'eventbus', got: {target!r}"
                )
            resolved = target
        self._target = resolved
        self._default_load_vec = resolved == "rag"
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
        elif resolved == "workflow":
            self._db_path = db_cfg.workflow_db_path
        else:
            self._db_path = db_cfg.eventbus_db_path
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
        """Open a raw SQLite connection; raise on DB_PATH misconfiguration."""
        if not self._db_path:
            raise ValueError(
                f"{self._target}_db_path is not configured in agent.toml or DB config"
            )
        try:
            return sqlite3.connect(self._db_path, timeout=self._sqlite_timeout)
        except sqlite3.OperationalError as e:
            logger.error("Failed to connect to '%s': %s", self._db_path, e)
            raise

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
    ) -> None:
        """Apply WAL/synchronous=NORMAL/busy_timeout; foreign_keys enforced only in write_mode."""
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute(f"PRAGMA busy_timeout={self._busy_timeout_ms}")
        if write_mode:
            conn.execute("PRAGMA foreign_keys=ON")

    def open(
        self,
        *,
        write_mode: bool = False,
        row_factory: bool = False,
        load_vec: bool | None = None,
        reuse_connection: bool = False,
    ) -> "SQLiteHelper":
        """Open a connection with optional vec extension and WAL pragmas.

        load_vec: None = use instance default (True for rag, False for session).
        write_mode: enforce FK constraints.
        row_factory: enable column-name access on result rows.
        reuse_connection: skip reconnect if already connected; skip close in __exit__.
        """
        self._reuse_connection = reuse_connection
        if reuse_connection and self.conn is not None:
            return self
        use_vec = self._default_load_vec if load_vec is None else load_vec
        conn = self._connect()
        if use_vec and self._vec_so:
            self._load_vec_extension(conn)
        self._apply_connection_pragmas(conn, write_mode=write_mode)
        if row_factory:
            conn.row_factory = sqlite3.Row
        self.conn = conn
        logger.debug(
            "SQLite connection opened: %s (write=%s)", self._db_path, write_mode
        )
        return self

    def __enter__(self) -> "SQLiteHelper":
        return self

    def __exit__(self, *_: object) -> None:
        if not self._reuse_connection:
            self.close()

    def close(self) -> None:
        """Close self.conn if open and reset it to None."""
        if self.conn is None:
            return
        try:
            self.conn.close()
        except OSError as e:
            logger.warning("Error while closing SQLite connection: %s", e)
        finally:
            self.conn = None

    @contextmanager
    def begin_immediate(self) -> Generator[None]:
        """Wrap a block in BEGIN IMMEDIATE...COMMIT; serializes concurrent writers.

        Rolls back on any normal exception (not just sqlite3.Error), ensuring
        no dangling transaction remains. Re-raises the original exception.
        Does not catch BaseException (KeyboardInterrupt, SystemExit).
        """
        conn = self._require_conn()
        conn.execute("BEGIN IMMEDIATE")
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
    def begin_exclusive(self) -> Generator[None]:
        """Wrap a block in BEGIN EXCLUSIVE...COMMIT; use only for VACUUM or schema migrations.

        Rolls back on any normal exception (not just sqlite3.Error), ensuring
        no dangling transaction remains. Re-raises the original exception.
        Does not catch BaseException (KeyboardInterrupt, SystemExit).
        """
        conn = self._require_conn()
        conn.execute("BEGIN EXCLUSIVE")
        try:
            yield
            conn.execute("COMMIT")
        except Exception:
            try:
                conn.execute("ROLLBACK")
            except sqlite3.OperationalError:
                pass
            raise

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
        row = conn.execute(f"PRAGMA wal_checkpoint({mode})").fetchone()
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
