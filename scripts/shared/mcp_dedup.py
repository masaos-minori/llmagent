"""scripts/shared/mcp_dedup.py — Idempotent tool-call state store for MCP tools.

Keyed by the sha256 idempotency key derived from (method, tool_name, args, uid).
State machine: pending -> completed, pending -> failed, pending -> interrupted.
Terminal states never regress. The store owns its own SQLite file (default
/opt/llm/db/mcp_dedup.sqlite, overridable via config/mcp_dedup.toml) and never
touches mdq.sqlite or rag.sqlite.
"""

from __future__ import annotations

import hashlib
import json
import logging
import sqlite3
import threading
import time
import tomllib
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from shared.config_errors import ConfigMissingError, ConfigParseError
from shared.execution_snapshot import snapshot_json

logger = logging.getLogger(__name__)

DEFAULT_CONFIG_PATH = Path("config/mcp_dedup.toml")
DEFAULT_DB_PATH = "/opt/llm/db/mcp_dedup.sqlite"
DEFAULT_RETENTION_DAYS = 14
DEFAULT_PENDING_TIMEOUT_MINUTES = 10

TERMINAL_STATES = frozenset({"completed", "failed", "interrupted"})

# Stored-result cap: payloads over this many serialized characters are replaced
# by a truncated sentinel (preview + hash of the full payload). Tunable; raise
# if replayed results are observed to be truncated in normal operation.
RESULT_MAX_CHARS = 8000
RESULT_PREVIEW_CHARS = 1000

_SCHEMA = """
CREATE TABLE IF NOT EXISTS tool_call_state (
    key TEXT PRIMARY KEY,
    tool_name TEXT NOT NULL,
    args_hash TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('pending', 'completed', 'failed', 'interrupted')),
    snapshot_json TEXT NOT NULL,
    created_epoch REAL NOT NULL,
    updated_epoch REAL NOT NULL,
    result_json TEXT
)
"""
_INDEXES = (
    "CREATE INDEX IF NOT EXISTS idx_tcs_updated ON tool_call_state(updated_epoch)",
    "CREATE INDEX IF NOT EXISTS idx_tcs_status ON tool_call_state(status)",
)
_USER_VERSION = 1


@dataclass(frozen=True)
class DedupConfig:
    db_path: str = DEFAULT_DB_PATH
    retention_days: int = DEFAULT_RETENTION_DAYS
    pending_timeout_minutes: int = DEFAULT_PENDING_TIMEOUT_MINUTES
    retry_class: dict[str, str] = field(default_factory=dict)


def load_dedup_config(path: str | Path = DEFAULT_CONFIG_PATH) -> DedupConfig:
    """Load config/mcp_dedup.toml. Missing file and bad values raise typed ConfigErrors."""
    filename = Path(path).name
    try:
        raw = Path(path).read_bytes()
    except FileNotFoundError as exc:
        raise ConfigMissingError(filename) from exc

    try:
        data = tomllib.loads(raw.decode("utf-8"))
    except (tomllib.TOMLDecodeError, UnicodeDecodeError) as exc:
        raise ConfigParseError(filename, exc) from exc

    dedup = data.get("dedup", {})
    if not isinstance(dedup, dict):
        raise ConfigParseError(filename, ValueError("[dedup] section must be a table"))

    db_path = dedup.get("db_path", DEFAULT_DB_PATH)
    retention_days = dedup.get("retention_days", DEFAULT_RETENTION_DAYS)
    pending_timeout = dedup.get(
        "pending_timeout_minutes", DEFAULT_PENDING_TIMEOUT_MINUTES
    )
    retry_section = data.get("retry_class", {})
    if not isinstance(retry_section, dict):
        raise ConfigParseError(
            filename, ValueError("[retry_class] section must be a table")
        )

    for key, value in (
        ("db_path", db_path),
        ("retention_days", retention_days),
        ("pending_timeout_minutes", pending_timeout),
    ):
        if key == "db_path":
            if not isinstance(value, str) or not value:
                raise ConfigParseError(
                    filename, ValueError(f"dedup.{key} must be a non-empty string")
                )
        elif not isinstance(value, int) or isinstance(value, bool):
            raise ConfigParseError(
                filename, ValueError(f"dedup.{key} must be an integer")
            )

    retry_class: dict[str, str] = {}
    for tool_name, cls in retry_section.items():
        if not isinstance(cls, str):
            raise ConfigParseError(
                filename, ValueError(f"retry_class.{tool_name} must be a string")
            )
        retry_class[str(tool_name)] = cls

    return DedupConfig(
        db_path=str(db_path),
        retention_days=int(retention_days),
        pending_timeout_minutes=int(pending_timeout),
        retry_class=retry_class,
    )


def retry_class(tool_name: str, config: DedupConfig | None = None) -> str:
    """Return the retry classification for a tool; unknown tools are non_retryable."""
    if config is None:
        config = load_dedup_config()
    return config.retry_class.get(tool_name, "non_retryable")


@dataclass(frozen=True)
class DedupRow:
    key: str
    tool_name: str
    args_hash: str
    status: str
    snapshot: Mapping[str, str]
    created_epoch: float
    updated_epoch: float
    result: Any


def _row_from_record(rec: sqlite3.Row) -> DedupRow:
    raw_snapshot = rec["snapshot_json"]
    raw_result = rec["result_json"]
    try:
        snapshot = json.loads(raw_snapshot) if raw_snapshot else {}
    except json.JSONDecodeError:
        snapshot = {}
    try:
        result = json.loads(raw_result) if raw_result is not None else None
    except json.JSONDecodeError:
        result = raw_result
    return DedupRow(
        key=rec["key"],
        tool_name=rec["tool_name"],
        args_hash=rec["args_hash"],
        status=rec["status"],
        snapshot=snapshot,
        created_epoch=float(rec["created_epoch"]),
        updated_epoch=float(rec["updated_epoch"]),
        result=result,
    )


def _cap_result(result: Any) -> str:
    serialized = json.dumps(result, ensure_ascii=False)
    if len(serialized) <= RESULT_MAX_CHARS:
        return serialized
    full_hash = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
    return json.dumps(
        {
            "truncated": True,
            "sha256": full_hash,
            "preview": serialized[:RESULT_PREVIEW_CHARS],
        },
        ensure_ascii=False,
    )


class DedupStore:
    """Store handle over one tool_call_state SQLite file.

    Sync methods, held connection with a threading.Lock, matching the
    memory_store pattern; whether the caller wraps calls in asyncio.to_thread
    is decided at the dispatcher integration point (implementation row 04).
    All writes run under BEGIN IMMEDIATE.
    """

    def __init__(self, db_path: str, *, busy_timeout_ms: int = 5000) -> None:
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode = WAL")
        self._conn.execute(f"PRAGMA busy_timeout = {int(busy_timeout_ms)}")
        self._conn.execute("PRAGMA synchronous = NORMAL")
        self._conn.execute(_SCHEMA)
        for ddl in _INDEXES:
            self._conn.execute(ddl)
        current = self._conn.execute("PRAGMA user_version").fetchone()[0]
        if current != _USER_VERSION:
            self._conn.execute(f"PRAGMA user_version = {_USER_VERSION}")
        self._conn.commit()

    def close(self) -> None:
        with self._lock:
            self._conn.close()

    def _write(self, sql: str, params: tuple[Any, ...]) -> None:
        with self._lock:
            try:
                self._conn.execute("BEGIN IMMEDIATE")
                self._conn.execute(sql, params)
                self._conn.commit()
            except sqlite3.Error:
                self._conn.rollback()
                raise

    def record_pending(
        self,
        key: str,
        tool_name: str,
        args_hash: str,
        snapshot: Mapping[str, str],
        *,
        now_epoch: float | None = None,
        force: bool = False,
    ) -> None:
        """Insert (or refresh) a pending row.

        Without force, completed/failed rows are left untouched (terminal states
        never regress). With force=True the row is reset to pending regardless
        of its prior status; the dispatcher uses this only for the policy-
        allowed fresh attempt on a snapshot-mismatched completed row (REQ-005).
        """
        now = time.time() if now_epoch is None else now_epoch
        self._write(
            "INSERT INTO tool_call_state "
            "(key, tool_name, args_hash, status, snapshot_json, created_epoch, updated_epoch, result_json) "
            "VALUES (?, ?, ?, 'pending', ?, ?, ?, NULL) "
            "ON CONFLICT(key) DO UPDATE SET status = 'pending', args_hash = excluded.args_hash, "
            "snapshot_json = excluded.snapshot_json, created_epoch = excluded.created_epoch, "
            "updated_epoch = excluded.updated_epoch, result_json = NULL "
            "WHERE (? OR tool_call_state.status IN ('pending', 'interrupted'))",
            (
                key,
                tool_name,
                args_hash,
                snapshot_json(snapshot),
                now,
                now,
                1 if force else 0,
            ),
        )
        logger.debug("dedup pending recorded key=%s tool=%s", key[:12], tool_name)

    def record_completed(
        self,
        key: str,
        snapshot: Mapping[str, str],
        result: Any,
        *,
        now_epoch: float | None = None,
    ) -> None:
        now = time.time() if now_epoch is None else now_epoch
        self._write(
            "UPDATE tool_call_state SET status = 'completed', snapshot_json = ?, "
            "updated_epoch = ?, result_json = ? WHERE key = ? AND status = 'pending'",
            (snapshot_json(snapshot), now, _cap_result(result), key),
        )

    def record_failed(
        self,
        key: str,
        error_class: str,
        *,
        now_epoch: float | None = None,
    ) -> None:
        now = time.time() if now_epoch is None else now_epoch
        self._write(
            "UPDATE tool_call_state SET status = 'failed', updated_epoch = ?, result_json = ? "
            "WHERE key = ? AND status = 'pending'",
            (now, json.dumps({"error_class": error_class}), key),
        )

    def mark_interrupted(self, key: str, *, now_epoch: float | None = None) -> None:
        now = time.time() if now_epoch is None else now_epoch
        self._write(
            "UPDATE tool_call_state SET status = 'interrupted', updated_epoch = ? "
            "WHERE key = ? AND status = 'pending'",
            (now, key),
        )

    def clear(self, key: str) -> None:
        """Delete the row for a key (used for dry-run outcomes that must not
        leave replayable state behind)."""
        self._write("DELETE FROM tool_call_state WHERE key = ?", (key,))

    def lookup(self, key: str) -> DedupRow | None:
        with self._lock:
            rec = self._conn.execute(
                "SELECT key, tool_name, args_hash, status, snapshot_json, created_epoch, "
                "updated_epoch, result_json FROM tool_call_state WHERE key = ?",
                (key,),
            ).fetchone()
        return _row_from_record(rec) if rec is not None else None

    def purge_expired(
        self, retention_days: int, *, now_epoch: float | None = None
    ) -> int:
        """Delete terminal (completed/failed/interrupted) rows older than retention.

        Pending rows are never purged here; their timeout path is classification.
        """
        now = time.time() if now_epoch is None else now_epoch
        cutoff = now - retention_days * 86400
        with self._lock:
            try:
                self._conn.execute("BEGIN IMMEDIATE")
                cur = self._conn.execute(
                    "DELETE FROM tool_call_state "
                    "WHERE status IN ('completed', 'failed', 'interrupted') AND updated_epoch < ?",
                    (cutoff,),
                )
                self._conn.commit()
            except sqlite3.Error:
                self._conn.rollback()
                raise
        if cur.rowcount:
            logger.info(
                "dedup purged %d expired rows (cutoff=%.0f)", cur.rowcount, cutoff
            )
        return cur.rowcount


def classify_interrupted(
    row: DedupRow,
    pending_timeout_minutes: int,
    *,
    now_epoch: float | None = None,
) -> str:
    """Read-time classification: a pending row older than the timeout is 'interrupted'.

    Non-mutating: the stored row only changes when mark_interrupted is called
    explicitly, so repeated lookups never advance updated_epoch.
    """
    if row.status != "pending":
        return row.status
    now = time.time() if now_epoch is None else now_epoch
    if now - row.created_epoch > pending_timeout_minutes * 60:
        return "interrupted"
    return "pending"


def open_dedup_store(
    config: DedupConfig | str, *, busy_timeout_ms: int = 5000
) -> DedupStore:
    """Open (and initialize) a store handle for the configured db_path."""
    db_path = config.db_path if isinstance(config, DedupConfig) else config
    return DedupStore(db_path, busy_timeout_ms=busy_timeout_ms)
