#!/usr/bin/env python3
"""sqlite_helper.py
SQLite connection manager for RAG and session databases.
Provides open/close lifecycle methods with sqlite-vec extension and WAL setup.
target="rag" (default) → rag_db_path; target="session" → session_db_path (common.toml).
"""

import logging
import sqlite3
from collections.abc import Generator
from contextlib import contextmanager
from typing import Any

from shared.config_loader import ConfigLoader

logger = logging.getLogger(__name__)

_cfg: dict[str, Any] | None = None

# Default busy_timeout in milliseconds; overridable via sqlite_busy_timeout_ms in common.toml.
# 30 seconds matches the sqlite_timeout connect parameter (also 30 s) for consistent behaviour.
_DEFAULT_BUSY_TIMEOUT_MS: int = 30000


def _get_cfg() -> dict[str, Any]:
    """Load config on first call; cached for the module lifetime."""
    global _cfg
    if _cfg is None:
        try:
            _cfg = ConfigLoader().load("common.toml")
        except Exception as e:
            logger.warning(f"Config load failed: {e}")
            _cfg = {}
    return _cfg


class SQLiteHelper:
    """SQLite connection manager with sqlite-vec extension support; WAL/synchronous=NORMAL/busy_timeout applied to every connection."""

    _RAG_PATH: str = ""
    _SESSION_PATH: str = ""
    SQLITE_VEC_SO: str = ""
    _config_loaded: bool = False

    @classmethod
    def _ensure_config(cls) -> None:
        """Populate _RAG_PATH, _SESSION_PATH and SQLITE_VEC_SO from config on first call."""
        if cls._config_loaded:
            return
        cfg = _get_cfg()
        cls._RAG_PATH = cfg.get("rag_db_path", "")
        cls._SESSION_PATH = cfg.get("session_db_path", "")
        cls.SQLITE_VEC_SO = cfg.get("sqlite_vec_so", "")
        cls._config_loaded = True

    def __init__(self, target: str = "rag") -> None:
        if target not in ("rag", "session"):
            raise ValueError(f"target must be 'rag' or 'session', got: {target!r}")
        self._target = target
        self.conn: sqlite3.Connection | None = None

    @property
    def DB_PATH(self) -> str:
        """Return the configured DB path for this instance's target."""
        self._ensure_config()
        return self._RAG_PATH if self._target == "rag" else self._SESSION_PATH

    def _connect(self) -> sqlite3.Connection:
        """Open a raw SQLite connection; raise on DB_PATH misconfiguration."""
        self._ensure_config()
        db_path = self.DB_PATH
        key = "rag_db_path" if self._target == "rag" else "session_db_path"
        if not db_path:
            raise ValueError(f"{key} is not configured in common.toml")
        timeout = int(_get_cfg().get("sqlite_timeout", 30))
        try:
            return sqlite3.connect(db_path, timeout=timeout)
        except sqlite3.OperationalError as e:
            logger.error(f"Failed to connect to '{db_path}': {e}")
            raise

    def _load_vec_extension(self, conn: sqlite3.Connection) -> None:
        """Load the sqlite-vec extension and immediately disable extension loading."""
        if not self.SQLITE_VEC_SO:
            raise ValueError("SQLITE_VEC_SO is not configured in common.toml")
        try:
            conn.enable_load_extension(True)
            conn.load_extension(self.SQLITE_VEC_SO)
            conn.enable_load_extension(False)
        except sqlite3.OperationalError as e:
            conn.close()
            logger.error(f"Failed to load sqlite-vec '{self.SQLITE_VEC_SO}': {e}")
            raise

    def _apply_connection_pragmas(
        self,
        conn: sqlite3.Connection,
        *,
        write_mode: bool,
    ) -> None:
        """Apply WAL/synchronous=NORMAL/busy_timeout to every connection; foreign_keys enforced only in write_mode to avoid read overhead."""
        busy_ms = int(
            _get_cfg().get("sqlite_busy_timeout_ms", _DEFAULT_BUSY_TIMEOUT_MS),
        )
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute(f"PRAGMA busy_timeout={busy_ms}")
        if write_mode:
            conn.execute("PRAGMA foreign_keys=ON")

    def open(
        self,
        *,
        write_mode: bool = False,
        row_factory: bool = False,
    ) -> "SQLiteHelper":
        """Open a connection with sqlite-vec loaded and WAL pragmas applied; write_mode enforces FK constraints; row_factory enables column-name access; returns self."""
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
        """Wrap a block in BEGIN IMMEDIATE...COMMIT; serializes concurrent writers; use for atomic multi-statement write operations like chunk ingestion."""
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
        """Wrap a block in BEGIN EXCLUSIVE...COMMIT; blocks all readers and writers; use only for VACUUM or schema migrations."""
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
        """Return DB health metrics (journal mode, PRAGMA quick_check, page stats); quick_check catches common corruption patterns faster than integrity_check."""
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
        {"PASSIVE", "FULL", "RESTART", "TRUNCATE"},
    )

    def checkpoint(self, mode: str = "TRUNCATE") -> dict[str, int]:
        """Run WAL checkpoint and return {busy, pages_in_wal, pages_checkpointed}; PASSIVE=non-blocking, FULL/RESTART/TRUNCATE block until WAL flushed; default TRUNCATE reclaims disk."""
        if mode not in self._CHECKPOINT_MODES:
            raise ValueError(
                f"checkpoint mode must be one of {sorted(self._CHECKPOINT_MODES)}",
            )
        assert self.conn is not None, "DB not open — call open() first"
        row = self.conn.execute(f"PRAGMA wal_checkpoint({mode})").fetchone()
        result = {"busy": row[0], "pages_in_wal": row[1], "pages_checkpointed": row[2]}
        logger.info(f"WAL checkpoint ({mode}): {result}")
        return result

    def vacuum(self) -> None:
        """Rebuild the DB file in place to reclaim free pages; requires ~2× DB size in free disk space; cannot run inside a transaction."""
        assert self.conn is not None, "DB not open — call open() first"
        self.conn.execute("VACUUM")
        logger.info(f"VACUUM completed: {self.DB_PATH}")

    def _check_ready(self, sql: str) -> None:
        """Guard: raise if connection is not open or sql is invalid."""
        if self.conn is None:
            raise RuntimeError("DB not open — call open() first")
        if not isinstance(sql, str) or not sql.strip():
            raise ValueError("sql must be a non-empty string")

    def execute(
        self,
        sql: str,
        params: dict[str, Any] | tuple[Any, ...] = (),
    ) -> sqlite3.Cursor:
        """Execute a SQL statement with positional (tuple) or named (dict) params."""
        self._check_ready(sql)
        assert self.conn is not None  # guaranteed by _check_ready()
        return self.conn.execute(sql, params)

    def executemany(
        self,
        sql: str,
        params_seq: list[tuple[Any, ...]],
    ) -> sqlite3.Cursor:
        """Execute a SQL statement once per row in params_seq."""
        self._check_ready(sql)
        assert self.conn is not None
        return self.conn.executemany(sql, params_seq)

    def fetchall(
        self,
        sql: str,
        params: dict[str, Any] | tuple[Any, ...] = (),
    ) -> list[Any]:
        """Execute a SQL statement and return all result rows as a list."""
        self._check_ready(sql)
        assert self.conn is not None  # guaranteed by _check_ready()
        return self.conn.execute(sql, params).fetchall()

    def commit(self) -> None:
        """Commit the current transaction on self.conn."""
        if self.conn is None:
            raise RuntimeError("DB not open — call open() first")
        try:
            self.conn.commit()
        except sqlite3.OperationalError as e:
            logger.error(f"Commit failed: {e}")
            raise
