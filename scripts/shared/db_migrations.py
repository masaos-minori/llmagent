"""scripts/shared/db_migrations.py — Domain-neutral forward-only migration framework.

Provides a registry-entry dataclass, a path-resolving runner, a pre-migration
backup/integrity gate, ledger primitives, dry-run mode, and refusal semantics so
the ``db`` and ``eventbus`` layers share one migration lifecycle
(REQ-001 migration framework, REQ-002 backup gate, REQ-003 refusal semantics,
REQ-004 dry-run, REQ-006 ledger).

The framework lives in ``shared`` because ``.importlinter`` forbids
``eventbus`` -> ``db`` and ``shared`` -> ``db``; both layers may import ``shared``,
and ``shared`` already holds DB-adjacent helpers (``eventbus_schema_fingerprint``,
``db_maintenance``). It imports only the standard library so ``shared-is-leaf``
stays KEPT.

Domain-specific backup verification (database identity, schema fingerprint) cannot
be imported into ``shared`` (that would violate the leaf contract), so the runner
receives it as an injected callable from the calling domain layer. The ``db``
layer passes a wrapper around ``db.recovery._backup_is_usable``; the ``eventbus``
layer passes a wrapper around ``eventbus_schema_fingerprint.assert_matches``.
"""

from __future__ import annotations

import logging
import os
import shutil
import sqlite3
import tempfile
from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum

logger = logging.getLogger(__name__)

# Ledger table contract (Plan Design):
#   schema_migrations(id TEXT PRIMARY KEY, applied_at TEXT,
#                     from_version INTEGER, to_version INTEGER)
_LEDGER_TABLE = "schema_migrations"
_LEDGER_CREATE = (
    f"CREATE TABLE IF NOT EXISTS {_LEDGER_TABLE} ("
    "id TEXT PRIMARY KEY,"
    " applied_at TEXT,"
    " from_version INTEGER,"
    " to_version INTEGER"
    ")"
)

# ISO-8601 UTC stamp, consistent with the defaults in db/schema_sql.py.
_LEDGER_APPLIED_AT = "strftime('%Y-%m-%dT%H:%M:%SZ','now')"

# Type alias for a registered migration set keyed by spec id.
Registry = dict[str, "MigrationSpec"]

# Signature of the caller-injected backup verifier: it receives the verified
# backup connection and its temp path and MUST raise on a bad backup.
BackupVerifier = Callable[[sqlite3.Connection, str], None]


class MigrationRefusalReason(StrEnum):
    """Refusal class raised before any mutation (REQ-003)."""

    DOWNGRADE = "downgrade"
    UNKNOWN_PATH = "unknown_path"
    CYCLE = "cycle"
    NO_VERIFIED_BACKUP = "no_verified_backup"


_DEFAULT_REFUSAL_MESSAGES: dict[MigrationRefusalReason, str] = {
    MigrationRefusalReason.DOWNGRADE: "migration would downgrade the schema version",
    MigrationRefusalReason.UNKNOWN_PATH: "no ordered forward path exists to the target",
    MigrationRefusalReason.CYCLE: "migration path revisits a version (cycle)",
    MigrationRefusalReason.NO_VERIFIED_BACKUP: "no verified backup exists before migration",
}


class MigrationRefusalError(RuntimeError):
    """Raised before any mutation when a migration path is refused (REQ-003).

    ``reason`` carries the refusal class so callers (CLIs) can map it to an exit
    code; the message is human-readable.
    """

    def __init__(
        self,
        reason: MigrationRefusalReason,
        message: str | None = None,
    ) -> None:
        self.reason = reason
        super().__init__(message or _DEFAULT_REFUSAL_MESSAGES[reason])


@dataclass(frozen=True)
class MigrationSpec:
    """A single forward migration step in a domain registry.

    ``mutation_sql`` runs inside one transaction; ``postcondition`` re-verifies the
    resulting schema shape. ``preconditions`` run against the live connection before
    the mutation. Versions are integers defined per domain registry.
    """

    id: str
    from_version: int
    to_version: int
    preconditions: tuple[
        Callable[[sqlite3.Connection], None],
        ...,
    ] = ()
    mutation_sql: str = ""
    postcondition: Callable[[sqlite3.Connection], None] | None = None


@dataclass(frozen=True)
class LedgerRow:
    """One applied migration recorded in the ``schema_migrations`` ledger."""

    id: str
    applied_at: str
    from_version: int
    to_version: int


def ensure_ledger(conn: sqlite3.Connection) -> None:
    """Create the ``schema_migrations`` ledger table if it does not yet exist."""
    conn.execute(_LEDGER_CREATE)


def read_ledger(conn: sqlite3.Connection) -> list[LedgerRow]:
    """Return every applied migration ordered by ``applied_at`` then id.

    Tolerates a database that predates the ledger (no ``schema_migrations`` table
    yet): such a database has applied nothing, so an empty list is returned. Callers
    planning a migration on an existing database therefore never need a separate
    table-exists probe.
    """
    has_table = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
        (_LEDGER_TABLE,),
    ).fetchone()
    if has_table is None:
        return []
    rows = conn.execute(
        f"SELECT id, applied_at, from_version, to_version FROM {_LEDGER_TABLE} "
        "ORDER BY applied_at, id"
    ).fetchall()
    return [
        LedgerRow(
            id=row[0],
            applied_at=row[1],
            from_version=int(row[2]),
            to_version=int(row[3]),
        )
        for row in rows
    ]


def record_applied(
    conn: sqlite3.Connection,
    spec: MigrationSpec,
    *,
    applied_at: str | None = None,
) -> None:
    """Record one applied migration in the ledger.

    Args:
        conn: Open connection to the canonical database being migrated.
        spec: The migration step that was applied.
        applied_at: Optional explicit timestamp (tests); defaults to an
            ISO-8601 UTC ``strftime`` stamp.
    """
    conn.execute(
        f"INSERT INTO {_LEDGER_TABLE} (id, applied_at, from_version, to_version) "
        f"VALUES (?, {applied_at or _LEDGER_APPLIED_AT}, ?, ?)",
        (spec.id, spec.from_version, spec.to_version),
    )


def _run_pre_migration_gate(
    live_conn: sqlite3.Connection,
    backup_verifier: BackupVerifier,
) -> None:
    """Run the pre-migration gate and refuse without a verified backup (REQ-002).

    Order: WAL checkpoint -> SQLite backup-API copy into a temp file ->
    ``PRAGMA integrity_check`` on the copy -> injected domain verifier. A clean
    checkpoint is required (a non-zero busy count means the WAL could not be
    flushed, so no recovery point exists). The temp copy is always closed and
    deleted, even on failure, and never overwrites the live DB file.
    """
    checkpoint = live_conn.execute("PRAGMA wal_checkpoint(FULL)").fetchone()
    if int(checkpoint[0]) != 0:
        raise MigrationRefusalError(
            MigrationRefusalReason.NO_VERIFIED_BACKUP,
            "WAL checkpoint did not complete cleanly; refusing migration",
        )

    db_path = live_conn.execute("PRAGMA database_list").fetchone()[2]
    if not db_path or db_path == ":memory:":
        raise MigrationRefusalError(
            MigrationRefusalReason.NO_VERIFIED_BACKUP,
            "cannot back up an in-memory database before migration",
        )

    fd, tmp_path = tempfile.mkstemp(suffix=".sqlite", prefix="migration-backup-")
    os.close(fd)
    backup_conn: sqlite3.Connection | None = None
    try:
        backup_conn = sqlite3.connect(tmp_path)
        live_conn.backup(backup_conn)
        integrity = str(backup_conn.execute("PRAGMA integrity_check").fetchone()[0])
        if integrity != "ok":
            raise MigrationRefusalError(
                MigrationRefusalReason.NO_VERIFIED_BACKUP,
                f"backup integrity check failed: {integrity}",
            )
        try:
            backup_verifier(backup_conn, tmp_path)
        except MigrationRefusalError:
            raise
        except Exception as e:
            # A failing domain verifier means the backup is not a usable recovery
            # point (REQ-002/AC-4).
            raise MigrationRefusalError(
                MigrationRefusalReason.NO_VERIFIED_BACKUP,
                f"backup verification failed: {e}",
            ) from e
    finally:
        if backup_conn is not None:
            backup_conn.close()
        try:
            os.unlink(tmp_path)
        except OSError as e:
            logger.warning("Failed to remove backup temp file %s: %s", tmp_path, e)


class MigrationRunner:
    """Resolve and execute a unique ordered forward migration path."""

    def plan(
        self,
        current_version: int,
        ledger_rows: list[LedgerRow],
        registry: Registry,
        target_version: int | None = None,
    ) -> list[MigrationSpec]:
        """Resolve the unique ordered forward path starting at ``current_version``.

        Skips steps already present in ``ledger_rows``. Stops when no forward step
        remains (``target_version`` is None) or when ``target_version`` is reached.
        Refuses a downgrade, an unreachable target, or a cyclic registry before
        returning any spec (REQ-003).

        Args:
            current_version: Current ``PRAGMA user_version`` of the database.
            ledger_rows: Already-applied migrations (to skip on resume).
            registry: Full domain registry keyed by spec id.
            target_version: Optional stop version; None plans all remaining steps.
        """
        applied_ids = {row.id for row in ledger_rows}
        path: list[MigrationSpec] = []
        seen_versions: set[int] = {current_version}
        version = current_version

        while True:
            if target_version is not None and version == target_version:
                break

            candidates = [
                spec
                for spec in registry.values()
                if spec.from_version == version and spec.id not in applied_ids
            ]

            if not candidates:
                if target_version is not None:
                    raise MigrationRefusalError(
                        MigrationRefusalReason.UNKNOWN_PATH,
                        f"no ordered forward path reaches target version "
                        f"{target_version} from {current_version}",
                    )
                break

            if len(candidates) > 1:
                raise MigrationRefusalError(
                    MigrationRefusalReason.CYCLE,
                    f"ambiguous forward path at version {version}: "
                    f"{sorted(c.id for c in candidates)}",
                )

            spec = candidates[0]

            if spec.to_version in seen_versions:
                raise MigrationRefusalError(
                    MigrationRefusalReason.CYCLE,
                    f"step {spec.id!r} revisits version {spec.to_version}",
                )

            if spec.to_version < version:
                raise MigrationRefusalError(
                    MigrationRefusalReason.DOWNGRADE,
                    f"step {spec.id!r} moves {version} -> {spec.to_version}; "
                    "downgrade is rejected",
                )

            seen_versions.add(spec.to_version)
            path.append(spec)
            version = spec.to_version

        return path

    def apply(
        self,
        conn: sqlite3.Connection,
        path: list[MigrationSpec],
        backup_verifier: BackupVerifier,
        *,
        dry_run: bool = False,
    ) -> list[LedgerRow]:
        """Apply a resolved forward path, one transaction per step (REQ-001/004).

               Runs the pre-migration gate once, then each step in its own transaction:
               preconditions, mutation, commit, ledger write, postcondition re-check. A
               failing step rolls back only that step and leaves the database at the last
               ledger-recorded version (AC-2). Dry-run runs resolution + gate against a
               throwaway copy and mutates nothing (AC-5).

               Args:
                   conn: Open connection to the canonical database being migrated.
                   path: Ordered forward path from :meth:`plan`.
                   backup_verifier: Domain backup verifier injected by the caller.
                   dry_run: When True, run resolution + gate against a throwaway copy and
        mutate nothing.
        """
        if not path:
            logger.info("No migration steps to apply.")
            return []

        if dry_run:
            logger.info(
                "Dry-run: gating %d step(s) against a throwaway copy.", len(path)
            )
            db_path = conn.execute("PRAGMA database_list").fetchone()[2]
            if not db_path or db_path == ":memory:":
                raise MigrationRefusalError(
                    MigrationRefusalReason.NO_VERIFIED_BACKUP,
                    "cannot dry-run against an in-memory database",
                )
            fd, tmp_path = tempfile.mkstemp(
                suffix=".sqlite", prefix="migration-dryrun-"
            )
            os.close(fd)
            try:
                shutil.copyfile(db_path, tmp_path)
                dry_conn = sqlite3.connect(tmp_path)
                try:
                    _run_pre_migration_gate(dry_conn, backup_verifier)
                finally:
                    dry_conn.close()
            finally:
                try:
                    os.unlink(tmp_path)
                except OSError as e:
                    logger.warning(
                        "Failed to remove dry-run temp file %s: %s", tmp_path, e
                    )
            return []

        _run_pre_migration_gate(conn, backup_verifier)

        # Create the ledger only after the gate passes, so a gate refusal leaves
        # the original database byte-for-byte intact (AC-2).
        ensure_ledger(conn)
        conn.commit()

        applied: list[LedgerRow] = []
        for spec in path:
            self._apply_step(conn, spec)
            record_applied(conn, spec)
            conn.commit()
            if spec.postcondition is not None:
                spec.postcondition(conn)
            applied.append(
                LedgerRow(
                    id=spec.id,
                    applied_at=read_ledger(conn)[-1].applied_at,
                    from_version=spec.from_version,
                    to_version=spec.to_version,
                )
            )
            logger.info(
                "Applied migration %s (%s -> %s).",
                spec.id,
                spec.from_version,
                spec.to_version,
            )

        return applied

    @staticmethod
    def _apply_step(conn: sqlite3.Connection, spec: MigrationSpec) -> None:
        """Run one migration step atomically; roll back the whole step on error.

        ``executescript`` runs every statement of ``mutation_sql`` inside a single
        implicit transaction (SQLite rolls back all of them if any fails), so a
        step is all-or-nothing. ``executescript`` commits any transaction opened
        before this step, which is empty here because the previous step already
        committed.
        """
        for precondition in spec.preconditions:
            precondition(conn)
        if not spec.mutation_sql:
            return
        try:
            conn.executescript(spec.mutation_sql)
            conn.commit()
        except sqlite3.Error:
            conn.rollback()
            raise
