"""scripts/shared/mcp_dedup.py — Atomic owner-lease dedup store with store identity.

Keyed by the caller-supplied logical call id (the `X-Idempotency-Key` value;
nothing is derived). One typed acquisition (`try_acquire_execution`) replaces the
old lookup + record_pending pattern: exactly one caller owns a logical call at a
time under a renewable owner lease; terminal rows are immutable evidence and
repeats append to `call_attempt_history`. Lease expiry alone only yields
`reconciliation_required` and never re-authorizes execution.

The store carries an identity created at initialization (single-row `store_meta`:
store UUID, generation, schema/config fingerprints, created epoch; `PRAGMA
user_version = 2`; external installation marker `.mcp_dedup_installed`). Opening
a store classifies its start state: `first_initialization` and `healthy` open;
`lost`, `replaced`, `legacy_or_unverified`, and `schema_mismatch` raise the typed
`DedupStoreError` taxonomy with the state attached, blocking side-effecting use
until `resolve_store` performs an operator resolution (archive, new generation,
logged decision). The store remains a disposable cache (ADR-008: no backup, no
migration). The config file is located through resolve_config_dir and parsed
once per process. The store owns its own SQLite file (default
/opt/llm/db/mcp_dedup.sqlite) and never touches mdq.sqlite or rag.sqlite.

Module family (split by the scripts/ module size gate, 24576 B): this module
owns the store lifecycle (open/identity classification, the installation
marker, and operator resolution) and re-exports the public surface; every
`sqlite3.connect()` stays here. shared/mcp_dedup_config.py owns config loading
(REQ-010), shared/mcp_dedup_schema.py the canonical DDL and state vocabularies,
shared/mcp_dedup_rows.py the row/result records and typed errors, and
shared/mcp_dedup_ledger.py the call-ledger state machine (the DedupLedger base
of DedupStore), and shared/mcp_dedup_metrics.py the read-only capacity metrics
payload assembled from the ledger's metrics view (mcpdl005 REQ-004). The store opens only through an injected `DedupStoreConfig`
(REQ-001): this module performs no config discovery and keeps no cache
(REQ-003). The fingerprint written at first init is compared on every reopen
(`identity_mismatch` refusal, REQ-007).
"""

from __future__ import annotations

import logging
import os
import sqlite3
import threading
import time
import uuid
from pathlib import Path
from typing import Any

from shared.mcp_call_state_contract import (
    CONTROL_ERROR_CODES,
    RECONCILE_OUTCOMES,
    RESULT_CLASSES,
)
from shared.mcp_dedup_config import (
    _LEASE_SECONDS_RANGE,
    _MAX_ATTEMPTS_RANGE,
    DEFAULT_DB_PATH,
    DEFAULT_LEASE_SECONDS,
    DEFAULT_MAX_ATTEMPTS,
    DEFAULT_PENDING_TIMEOUT_MINUTES,
    DEFAULT_RETENTION_DAYS,
    DedupStoreConfig,
    _config_fingerprint,
    load_dedup_section,
)
from shared.mcp_dedup_ledger import DedupLedger
from shared.mcp_dedup_metrics import (
    METRICS_SCHEMA_VERSION,
    collect_dedup_metrics,
)
from shared.mcp_dedup_rows import (
    AcquisitionResult,
    CallStateView,
    DedupLeaseConflict,
    DedupRow,
    DedupStoreError,
    StoredResult,
    classify_interrupted,
    classify_result,
)
from shared.mcp_dedup_schema import (
    _ATTEMPT_HISTORY_SCHEMA,
    _CANONICAL_DDL,
    _INDEXES,
    _INSTALL_MARKER_NAME,
    _SCHEMA,
    _SCHEMA_FINGERPRINT,
    _STORE_META_SCHEMA,
    _USER_VERSION,
    ACQUISITION_STATES,
    RESULT_MAX_CHARS,
    RESULT_PREVIEW_CHARS,
    START_STATES,
    TERMINAL_STATES,
)
from shared.schema_fingerprint import REFUSAL_MESSAGE, assert_matches

logger = logging.getLogger(__name__)

__all__ = [
    "ACQUISITION_STATES",
    "AcquisitionResult",
    "CONTROL_ERROR_CODES",
    "CallStateView",
    "DEFAULT_DB_PATH",
    "DEFAULT_LEASE_SECONDS",
    "DEFAULT_MAX_ATTEMPTS",
    "DEFAULT_PENDING_TIMEOUT_MINUTES",
    "DEFAULT_RETENTION_DAYS",
    "DedupLeaseConflict",
    "DedupRow",
    "DedupStore",
    "DedupStoreConfig",
    "DedupStoreError",
    "METRICS_SCHEMA_VERSION",
    "RECONCILE_OUTCOMES",
    "RESULT_CLASSES",
    "RESULT_MAX_CHARS",
    "RESULT_PREVIEW_CHARS",
    "START_STATES",
    "StoredResult",
    "TERMINAL_STATES",
    "classify_interrupted",
    "classify_result",
    "collect_dedup_metrics",
    "load_dedup_section",
    "open_dedup_store",
    "read_store_identity",
    "resolve_store",
]


class DedupStore(DedupLedger):
    """Store handle over one dedup_call_state SQLite file with owner leases.

    Sync methods, held connection with a threading.Lock, matching the
    memory_store pattern; whether the caller wraps calls in asyncio.to_thread
    is decided at the dispatcher integration point. All writes run under
    BEGIN IMMEDIATE with an explicit connect timeout so cross-process lease
    acquisition is deterministic. The ledger verbs (acquisition, lease,
    finalization, reconciliation, reads, purge) are inherited from
    shared.mcp_dedup_ledger.DedupLedger; this class owns the open, the start-
    state identity classification, the installation marker, and close.
    """

    def __init__(
        self,
        db_path: str,
        *,
        lease_seconds: int = DEFAULT_LEASE_SECONDS,
        max_attempts: int = DEFAULT_MAX_ATTEMPTS,
        busy_timeout_ms: int = 5000,
        config: DedupStoreConfig | None = None,
    ) -> None:
        self._db_path = str(db_path)
        self._config = config
        self._lease_seconds = int(lease_seconds)
        self._max_attempts = int(max_attempts)
        if (
            not _LEASE_SECONDS_RANGE[0]
            <= self._lease_seconds
            <= _LEASE_SECONDS_RANGE[1]
        ):
            raise ValueError(f"lease_seconds out of range: {self._lease_seconds}")
        if not _MAX_ATTEMPTS_RANGE[0] <= self._max_attempts <= _MAX_ATTEMPTS_RANGE[1]:
            raise ValueError(f"max_attempts out of range: {self._max_attempts}")
        self._marker_path = Path(self._db_path).parent / _INSTALL_MARKER_NAME
        self._lock = threading.Lock()
        Path(self._db_path).parent.mkdir(parents=True, exist_ok=True)
        # Existence must be sampled before connect(): sqlite3.connect creates an
        # empty file, which would otherwise erase the first-initialization signal.
        db_file = Path(self._db_path)
        self._db_existed = db_file.exists() and db_file.stat().st_size > 0
        self._conn = sqlite3.connect(
            self._db_path,
            check_same_thread=False,
            timeout=max(busy_timeout_ms, 0) / 1000,
        )
        self._conn.row_factory = sqlite3.Row
        # Explicit transaction control: every write path issues its own
        # BEGIN IMMEDIATE; the module-level implicit transaction handling must
        # stay off or BEGIN would nest.
        self._conn.isolation_level = None
        self._conn.execute(f"PRAGMA busy_timeout = {int(busy_timeout_ms)}")
        self._conn.execute("PRAGMA synchronous = NORMAL")
        self._identity: dict[str, Any] | None = None
        try:
            # Classification first: `PRAGMA journal_mode = WAL` persists into the
            # database header, so a refused open (legacy / mismatched store) must
            # never reach it — refusals stay read-only, fail-closed (ADR-008).
            self._start_state = self._classify_or_create()
            self._conn.execute("PRAGMA journal_mode = WAL")
        except Exception:
            # A refused open must not leak the handle (start-state errors
            # surface before any usable store exists).
            self._conn.close()
            raise

    def _classify_or_create(self) -> str:
        if not self._db_existed:
            # Absent or empty (touched) file with a surviving installation
            # marker is `lost`: an empty file alone never resolves (REQ-007).
            if self._marker_path.exists():
                marker_meta = _read_marker(self._marker_path)
                raise DedupStoreError(
                    "lost",
                    f"the store file {self._db_path} is gone while the installation "
                    f"marker {self._marker_path.name} remains; operator resolution "
                    f"required (marker generation: {marker_meta[1] if marker_meta else 'unknown'})",
                )
            return self._first_initialization()
        return self._classify_existing()

    def _first_initialization(self) -> str:
        store_uuid = str(uuid.uuid4())
        with self._lock:
            try:
                self._conn.execute("BEGIN IMMEDIATE")
                self._conn.execute(_SCHEMA)
                self._conn.execute(_STORE_META_SCHEMA)
                self._conn.execute(_ATTEMPT_HISTORY_SCHEMA)
                for ddl in _INDEXES:
                    self._conn.execute(ddl)
                self._conn.execute(
                    "INSERT INTO store_meta (store_uuid, generation, schema_fingerprint,"
                    " config_fingerprint, created_epoch) VALUES (?, 1, ?, ?, ?)",
                    (
                        store_uuid,
                        _SCHEMA_FINGERPRINT,
                        _config_fingerprint(self._effective_config()),
                        time.time(),
                    ),
                )
                self._conn.execute(f"PRAGMA user_version = {_USER_VERSION}")
                self._conn.commit()
            except sqlite3.Error:
                self._conn.rollback()
                raise
        self._write_marker(store_uuid, 1)
        self._identity = {
            "store_uuid": store_uuid,
            "generation": 1,
            "schema_fingerprint": _SCHEMA_FINGERPRINT,
        }
        logger.info(
            "dedup store first initialization uuid=%s generation=1 path=%s",
            store_uuid[:8],
            self._db_path,
        )
        return "first_initialization"

    def _classify_existing(self) -> str:
        db_path = Path(self._db_path)
        conn = self._conn
        has_meta = (
            conn.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='store_meta'"
            ).fetchone()
            is not None
        )
        if not has_meta:
            # Pre-change or empty file: no identity row exists anywhere in it;
            # never first_initialization and never healthy (REQ-006).
            raise DedupStoreError(
                "legacy_or_unverified",
                f"{db_path} carries no store_meta identity row (pre-change or "
                "unverifiable shape); archive-and-recreate via resolve_store",
            )
        user_version = int(conn.execute("PRAGMA user_version").fetchone()[0])
        if user_version != _USER_VERSION:
            raise DedupStoreError(
                "schema_mismatch",
                f"PRAGMA user_version={user_version} does not match the identity "
                f"stamp {_USER_VERSION}. {REFUSAL_MESSAGE} For this store the "
                "resolution is archive-and-recreate via resolve_store.",
            )
        marker_meta = _read_marker(self._marker_path)
        if marker_meta is None:
            # Marker-state asymmetry: a DB identity exists without its
            # installation marker; classification is refusal, not silent health.
            raise DedupStoreError(
                "legacy_or_unverified",
                f"store_meta exists but the installation marker "
                f"{self._marker_path.name} is missing; identity unverifiable",
            )
        rec = conn.execute(
            "SELECT store_uuid, generation, schema_fingerprint, config_fingerprint"
            " FROM store_meta"
        ).fetchone()
        if rec is None:
            raise DedupStoreError(
                "legacy_or_unverified",
                f"store_meta table carries no identity row. {REFUSAL_MESSAGE} "
                "For this store the resolution is archive-and-recreate via "
                "resolve_store.",
            )
        if marker_meta[0] != str(rec["store_uuid"]):
            raise DedupStoreError(
                "replaced",
                f"the store file carries uuid {str(rec['store_uuid'])[:8]} while the "
                f"installation marker records {marker_meta[0][:8]}; a foreign store "
                "replaced this path",
            )
        if self._config is not None:
            # REQ-007 reopen gate: the fingerprint written at first init must
            # match the injected validated set. A process whose [dedup]
            # semantics drifted from the store's must not start. The
            # config-less DedupStore seam (operator resolution, test
            # fixtures) carries no validated injection, so identity checks
            # alone govern there and the fingerprint is not compared.
            stored_fp = str(rec["config_fingerprint"])
            effective_fp = _config_fingerprint(self._config)
            if stored_fp != effective_fp:
                raise DedupStoreError(
                    "identity_mismatch",
                    f"the store was initialized under a different validated "
                    f"parameter set (stored config fingerprint {stored_fp[:12]}..., "
                    f"injected {effective_fp[:12]}...); a shared store cannot be "
                    f"reopened with drifted semantics. {REFUSAL_MESSAGE} For this "
                    "store the resolution is archive-and-recreate via resolve_store.",
                )
        try:
            assert_matches(conn, _CANONICAL_DDL, label="mcp_dedup.sqlite")
        except RuntimeError as exc:
            raise DedupStoreError("schema_mismatch", str(exc)) from exc
        self._identity = {
            "store_uuid": str(rec["store_uuid"]),
            "generation": int(rec["generation"]),
            "schema_fingerprint": str(rec["schema_fingerprint"]),
        }
        return "healthy"

    def _write_marker(self, store_uuid: str, generation: int) -> None:
        tmp = self._marker_path.with_suffix(".tmp")
        tmp.write_text(f"{store_uuid}\n{generation}\n", encoding="utf-8")
        os.replace(tmp, self._marker_path)

    def _effective_config(self) -> DedupStoreConfig:
        if self._config is not None:
            return self._config
        return DedupStoreConfig(
            db_path=self._db_path,
            lease_seconds=self._lease_seconds,
            max_attempts=self._max_attempts,
        )

    # --- public identity surface -------------------------------------
    @property
    def db_path(self) -> str:
        return self._db_path

    @property
    def start_state(self) -> str:
        return self._start_state

    @property
    def store_uuid(self) -> str | None:
        return str(self._identity["store_uuid"]) if self._identity else None

    @property
    def generation(self) -> int | None:
        return int(self._identity["generation"]) if self._identity else None

    @property
    def schema_fingerprint(self) -> str | None:
        return str(self._identity["schema_fingerprint"]) if self._identity else None

    @property
    def lease_seconds(self) -> int:
        return self._lease_seconds

    @property
    def max_attempts(self) -> int:
        return self._max_attempts

    def close(self) -> None:
        with self._lock:
            self._conn.close()

    def _stamp_generation(self, generation: int) -> None:
        """Record an operator-resolution generation rollover in the identity.

        Only used by resolve_store right after a fresh creation; the marker is
        refreshed so DB identity and installation marker agree on the generation.
        """
        self._write_txn([("UPDATE store_meta SET generation = ?", (generation,))])
        assert self._identity is not None
        self._identity["generation"] = generation
        self._write_marker(str(self._identity["store_uuid"]), generation)


def _read_marker(marker_path: Path) -> tuple[str, int] | None:
    try:
        raw = marker_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return None
    lines = [line.strip() for line in raw.splitlines() if line.strip()]
    if not lines:
        return ("", 0)
    generation = 0
    if len(lines) > 1:
        try:
            generation = int(lines[1])
        except ValueError:
            generation = 0
    return (lines[0], generation)


def read_store_identity(db_path: str | Path) -> tuple[int, str] | None:
    """Read-only identity read (generation, schema fingerprint) for snapshot
    consumers.

    Strictly read-only: never creates, classifies, or mutates the store, and
    never raises. Returns None for an absent, empty, or identity-less file.
    """
    path = Path(db_path)
    try:
        if not path.exists() or path.stat().st_size == 0:
            return None
        conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
        try:
            rec = conn.execute(
                "SELECT generation, schema_fingerprint FROM store_meta"
            ).fetchone()
        finally:
            conn.close()
    except (sqlite3.Error, OSError):
        return None
    if rec is None:
        return None
    return (int(rec[0]), str(rec[1]))


def open_dedup_store(
    config: DedupStoreConfig, *, busy_timeout_ms: int = 5000
) -> DedupStore:
    """Open (and initialize) a store handle for an injected store config.

    The injected `DedupStoreConfig` is the only way to open a store through
    this entry point (REQ-001): no path string, no discovery fallback, no
    cache (REQ-003).
    """
    return DedupStore(
        config.db_path,
        lease_seconds=config.lease_seconds,
        max_attempts=config.max_attempts,
        busy_timeout_ms=busy_timeout_ms,
        config=config,
    )


def resolve_store(db_path: str | Path) -> None:
    """Operator resolution for a lost, replaced, legacy, or drifted store.

    Validates the current start state (a healthy store refuses resolution),
    archives the old file as `<path>.corrupt-<ts>` (ADR-008 Decision 22),
    creates a new store generation, refreshes the installation marker, and logs
    the decision durably. An empty file alone never resolves anything: only this
    operation does (REQ-007).
    """
    resolved = Path(db_path)
    marker_path = resolved.parent / _INSTALL_MARKER_NAME

    # 1. Validate the start state: only an unhealthy store is resolvable.
    try:
        probe = DedupStore(str(resolved))
    except DedupStoreError:
        pass  # lost / replaced / legacy_or_unverified / schema_mismatch
    else:
        state = probe.start_state
        probe.close()
        if state == "healthy":
            raise DedupStoreError(
                "healthy",
                f"resolve_store refused: {resolved} is a healthy store; resolution"
                " is only for lost, replaced, legacy or drifted stores",
            )
        # first_initialization: the probe created a fresh generation-1 store.
        logger.warning(
            "dedup operator resolution: no store at %s; created generation 1",
            resolved,
        )
        return

    # 2. Record the previous generation before archiving (identity row first,
    # then the installation marker as fallback).
    old_generation: int | None = None
    if resolved.exists():
        conn: sqlite3.Connection | None = None
        try:
            conn = sqlite3.connect(str(resolved))
            rec = conn.execute("SELECT generation FROM store_meta").fetchone()
            if rec is not None:
                old_generation = int(rec[0])
        except sqlite3.Error:
            old_generation = None
        finally:
            if conn is not None:
                conn.close()
    if old_generation is None:
        marker_meta = _read_marker(marker_path)
        if marker_meta is not None and marker_meta[1]:
            old_generation = marker_meta[1]

    # 3. Archive the old file, then remove the marker (ADR-008 Decision 22).
    archive: Path | None = None
    if resolved.exists():
        ts = time.strftime("%Y%m%d-%H%M%S", time.gmtime())
        archive = resolved.with_name(f"{resolved.name}.corrupt-{ts}")
        os.replace(resolved, archive)
        for suffix in ("-wal", "-shm"):
            sidecar = Path(str(resolved) + suffix)
            if sidecar.exists():
                os.replace(sidecar, Path(str(archive) + suffix))
    marker_path.unlink(missing_ok=True)

    # 4. Create the new generation and stamp the rollover into its identity.
    new_generation = (old_generation + 1) if old_generation is not None else 1
    store = DedupStore(str(resolved))  # marker removed -> first initialization
    try:
        store._stamp_generation(new_generation)
    finally:
        store.close()
    logger.warning(
        "dedup operator resolution completed: path=%s archived=%s previous_generation=%s"
        " new_generation=%s",
        resolved,
        archive if archive else "none",
        old_generation if old_generation is not None else "unknown",
        new_generation,
    )
