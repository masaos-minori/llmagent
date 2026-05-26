#!/usr/bin/env python3
"""
sqlite_helper.py
SQLite connection manager for the RAG pipeline.
Provides open/close lifecycle methods with sqlite-vec extension and WAL setup.
"""

import logging
import sqlite3
from collections.abc import Generator
from contextlib import contextmanager
from typing import Any

from config_loader import ConfigLoader

logger = logging.getLogger(__name__)

_cfg: dict | None = None

# Default busy_timeout in milliseconds; overridable via sqlite_busy_timeout_ms in common.json.
# 30 seconds matches the sqlite_timeout connect parameter (also 30 s) for consistent behaviour.
_DEFAULT_BUSY_TIMEOUT_MS: int = 30000


def _get_cfg() -> dict:
    """Load config on first call; cached for the module lifetime."""
    global _cfg
    if _cfg is None:
        try:
            _cfg = ConfigLoader().load("common.json")
        except Exception as e:
            logger.warning(f"Config load failed: {e}")
            _cfg = {}
    return _cfg


class SQLiteHelper:
    """SQLite connection manager with sqlite-vec extension support.

    All connections are opened with WAL journal mode, synchronous=NORMAL,
    and busy_timeout applied unconditionally so every reader/writer
    benefits from crash-safe WAL semantics without separate configuration.
    """

    DB_PATH: str = ""
    SQLITE_VEC_SO: str = ""
    _config_loaded: bool = False

    @classmethod
    def _ensure_config(cls) -> None:
        """Populate DB_PATH and SQLITE_VEC_SO from config on first call."""
        if cls._config_loaded:
            return
        cfg = _get_cfg()
        cls.DB_PATH = cfg.get("db_path", "")
        cls.SQLITE_VEC_SO = cfg.get("sqlite_vec_so", "")
        cls._config_loaded = True

    def __init__(self) -> None:
        self.conn: sqlite3.Connection | None = None

    def _connect(self) -> sqlite3.Connection:
        """Open a raw SQLite connection; raise on DB_PATH misconfiguration."""
        self._ensure_config()
        if not self.DB_PATH:
            raise ValueError("DB_PATH is not configured in common.json")
        timeout = int(_get_cfg().get("sqlite_timeout", 30))
        try:
            return sqlite3.connect(self.DB_PATH, timeout=timeout)
        except sqlite3.OperationalError as e:
            logger.error(f"Failed to connect to '{self.DB_PATH}': {e}")
            raise

    def _load_vec_extension(self, conn: sqlite3.Connection) -> None:
        """Load the sqlite-vec extension and immediately disable extension loading."""
        if not self.SQLITE_VEC_SO:
            raise ValueError("SQLITE_VEC_SO is not configured in common.json")
        try:
            conn.enable_load_extension(True)
            conn.load_extension(self.SQLITE_VEC_SO)
            conn.enable_load_extension(False)
        except sqlite3.OperationalError as e:
            conn.close()
            logger.error(f"Failed to load sqlite-vec '{self.SQLITE_VEC_SO}': {e}")
            raise

    def _apply_connection_pragmas(
        self, conn: sqlite3.Connection, *, write_mode: bool
    ) -> None:
        """Apply WAL / synchronous=NORMAL / busy_timeout to every connection.

        These are set unconditionally so all readers and writers benefit from
        WAL concurrency and the busy_timeout prevents immediate lock errors.
        foreign_keys is only enforced when write_mode=True to avoid the overhead
        on read-only query connections.
        """
        busy_ms = int(
            _get_cfg().get("sqlite_busy_timeout_ms", _DEFAULT_BUSY_TIMEOUT_MS)
        )
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute(f"PRAGMA busy_timeout={busy_ms}")
        if write_mode:
            conn.execute("PRAGMA foreign_keys=ON")

    def open(
        self, *, write_mode: bool = False, row_factory: bool = False
    ) -> "SQLiteHelper":
        """Open a connection with sqlite-vec loaded and WAL pragmas applied.

        write_mode=True : enforces foreign key constraints in addition to WAL.
        row_factory=True: sets sqlite3.Row for column-name access.
        Returns self for use as a context manager.
        """
        conn = self._connect()
        self._load_vec_extension(conn)
        self._apply_connection_pragmas(conn, write_mode=write_mode)
        if row_factory:
            conn.row_factory = sqlite3.Row
        self.conn = conn
        logger.debug(f"SQLite connection opened: {self.DB_PATH} (write={write_mode})")
        return self

    def __enter__(self) -> "SQLiteHelper":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def close(self) -> None:
        """Close self.conn if open and reset it to None."""
        if self.conn is None:
            return
        try:
            self.conn.close()
        except Exception as e:
            logger.warning(f"Error while closing SQLite connection: {e}")
        finally:
            self.conn = None

    @contextmanager
    def begin_immediate(self) -> Generator[None]:
        """Wrap a block in BEGIN IMMEDIATE ... COMMIT.

        Serializes concurrent writers: the first writer to acquire the lock
        blocks others until COMMIT.  Use for multi-statement write operations
        that must be atomic (e.g. chunk ingestion, document deletion).

        Must be called before any DML on this connection; raises
        sqlite3.OperationalError if a transaction is already active.
        """
        assert self.conn is not None, "DB not open — call open() first"
        self.conn.execute("BEGIN IMMEDIATE")
        try:
            yield
            self.conn.execute("COMMIT")
        except BaseException:
            try:
                self.conn.execute("ROLLBACK")
            except Exception:
                pass
            raise

    @contextmanager
    def begin_exclusive(self) -> Generator[None]:
        """Wrap a block in BEGIN EXCLUSIVE ... COMMIT.

        Blocks all other readers and writers for the duration.  Use only for
        operations that must prevent concurrent reads, such as VACUUM or
        schema migrations.
        """
        assert self.conn is not None, "DB not open — call open() first"
        self.conn.execute("BEGIN EXCLUSIVE")
        try:
            yield
            self.conn.execute("COMMIT")
        except BaseException:
            try:
                self.conn.execute("ROLLBACK")
            except Exception:
                pass
            raise

    def health_check(self) -> dict[str, Any]:
        """Return DB health metrics: journal mode, integrity, page stats.

        Runs PRAGMA quick_check which is faster than integrity_check but
        catches the most common corruption patterns.
        """
        assert self.conn is not None, "DB not open — call open() first"
        journal_mode = self.conn.execute("PRAGMA journal_mode").fetchone()[0]
        integrity = self.conn.execute("PRAGMA quick_check").fetchone()[0]
        page_count = self.conn.execute("PRAGMA page_count").fetchone()[0]
        page_size = self.conn.execute("PRAGMA page_size").fetchone()[0]
        freelist = self.conn.execute("PRAGMA freelist_count").fetchone()[0]
        return {
            "journal_mode": journal_mode,
            "integrity": integrity,
            "page_count": page_count,
            "page_size": page_size,
            "freelist_count": freelist,
            "db_size_bytes": page_count * page_size,
        }

    _CHECKPOINT_MODES: frozenset[str] = frozenset(
        {"PASSIVE", "FULL", "RESTART", "TRUNCATE"}
    )

    def checkpoint(self, mode: str = "TRUNCATE") -> dict[str, int]:
        """Run WAL checkpoint and return page counters.

        mode: PASSIVE  — flush without waiting for readers (non-blocking)
              FULL     — wait for all readers, then flush
              RESTART  — like FULL, but reset the WAL write position
              TRUNCATE — like RESTART, then truncate WAL to zero bytes (default)

        Use TRUNCATE after large batch writes to reclaim disk space.
        Returns {"busy": 0|1, "pages_in_wal": n, "pages_checkpointed": n}.
        """
        if mode not in self._CHECKPOINT_MODES:
            raise ValueError(
                f"checkpoint mode must be one of {sorted(self._CHECKPOINT_MODES)}"
            )
        assert self.conn is not None, "DB not open — call open() first"
        row = self.conn.execute(f"PRAGMA wal_checkpoint({mode})").fetchone()
        result = {"busy": row[0], "pages_in_wal": row[1], "pages_checkpointed": row[2]}
        logger.info(f"WAL checkpoint ({mode}): {result}")
        return result

    def vacuum(self) -> None:
        """Rebuild the DB file in place to reclaim free pages and defragment.

        Requires ~2× the DB size in free disk space and cannot run inside a
        transaction.  Call after bulk deletions or at scheduled maintenance.
        """
        assert self.conn is not None, "DB not open — call open() first"
        self.conn.execute("VACUUM")
        logger.info(f"VACUUM completed: {self.DB_PATH}")

    def _check_ready(self, sql: str) -> None:
        """Guard: raise if connection is not open or sql is invalid."""
        if self.conn is None:
            raise RuntimeError("DB not open — call open() first")
        if not isinstance(sql, str) or not sql.strip():
            raise ValueError("sql must be a non-empty string")

    def execute(self, sql: str, params: dict | tuple = ()) -> sqlite3.Cursor:
        """Execute a SQL statement with positional (tuple) or named (dict) params."""
        self._check_ready(sql)
        return self.conn.execute(sql, params)  # type: ignore[union-attr]

    def fetchall(self, sql: str, params: dict | tuple = ()) -> list[Any]:
        """Execute a SQL statement and return all result rows as a list."""
        self._check_ready(sql)
        return self.conn.execute(sql, params).fetchall()  # type: ignore[union-attr]

    def commit(self) -> None:
        """Commit the current transaction on self.conn."""
        if self.conn is None:
            raise RuntimeError("DB not open — call open() first")
        try:
            self.conn.commit()
        except sqlite3.OperationalError as e:
            logger.error(f"Commit failed: {e}")
            raise
