"""scripts/shared/db_migrations.py — Domain-neutral forward-only migration framework.

Provides a registry-entry dataclass, a path-resolving runner, a pre-migration
backup/integrity gate, an opt-in durable archive, ledger primitives, dry-run
mode, and refusal semantics so the ``db`` and ``eventbus`` layers share one
migration lifecycle (REQ-001 migration framework and durable archive, REQ-002
backup gate, REQ-003 refusal semantics, REQ-004 dry-run, REQ-005 ledger append
order, REQ-006 ledger).

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

import hashlib
import json
import logging
import os
import sqlite3
import tempfile
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path

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
    """Refusal class raised before any mutation (REQ-003).

    The gate-family values name the unmet safety requirement;
    ``NO_VERIFIED_BACKUP`` is reserved for backup-integrity and verifier failures.
    """

    DOWNGRADE = "downgrade"
    UNKNOWN_PATH = "unknown_path"
    CYCLE = "cycle"
    NO_VERIFIED_BACKUP = "no_verified_backup"
    CHECKPOINT_BUSY = "checkpoint_busy"
    IN_MEMORY_DATABASE = "in_memory_database"
    NO_ARCHIVE_TARGET = "no_archive_target"
    ARCHIVE_FAILURE = "archive_failure"


_DEFAULT_REFUSAL_MESSAGES: dict[MigrationRefusalReason, str] = {
    MigrationRefusalReason.DOWNGRADE: "migration would downgrade the schema version",
    MigrationRefusalReason.UNKNOWN_PATH: "no ordered forward path exists to the target",
    MigrationRefusalReason.CYCLE: "migration path revisits a version (cycle)",
    MigrationRefusalReason.NO_VERIFIED_BACKUP: "no verified backup exists before migration",
    MigrationRefusalReason.CHECKPOINT_BUSY: "WAL checkpoint did not complete cleanly (busy)",
    MigrationRefusalReason.IN_MEMORY_DATABASE: "cannot gate or archive an in-memory database",
    MigrationRefusalReason.NO_ARCHIVE_TARGET: "archive target directory is missing or unwritable",
    MigrationRefusalReason.ARCHIVE_FAILURE: "durable pre-migration archive could not be created",
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

    ``mutation_sql`` runs inside one runner-owned transaction; ``preconditions`` run
    against the live connection before the mutation. ``postcondition`` re-verifies
    the resulting schema shape and is for observational checks only —
    mutation-integrity assertions belong in ``pre_commit_verification``, which runs
    inside the transaction and can reject the step before it commits (REQ-003).
    ``disable_foreign_keys`` opts the step into a foreign-key switch (restored
    after commit/rollback). Versions are integers defined per domain registry.
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
    disable_foreign_keys: bool = False
    pre_commit_verification: Callable[[sqlite3.Connection], None] | None = None


@dataclass(frozen=True)
class LedgerRow:
    """One applied migration recorded in the ``schema_migrations`` ledger.

    ``seq`` is the ledger ``rowid``: append order survives same-second
    ``applied_at`` collisions (REQ-005).
    """

    id: str
    applied_at: str
    from_version: int
    to_version: int
    seq: int = 0


def ensure_ledger(conn: sqlite3.Connection) -> None:
    """Create the ``schema_migrations`` ledger table if it does not yet exist."""
    conn.execute(_LEDGER_CREATE)


def read_ledger(conn: sqlite3.Connection) -> list[LedgerRow]:
    """Return every applied migration in append order (``rowid``, REQ-005).

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
        f"SELECT rowid, id, applied_at, from_version, to_version FROM {_LEDGER_TABLE} "  # nosec B608 — table name is a module-level constant, no user input
        "ORDER BY rowid"
    ).fetchall()
    return [
        LedgerRow(
            id=row[1],
            applied_at=row[2],
            from_version=int(row[3]),
            to_version=int(row[4]),
            seq=int(row[0]),
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
    applied_at_sql = "?" if applied_at else _LEDGER_APPLIED_AT
    applied_at_params: tuple[str, ...] = (applied_at,) if applied_at else ()
    conn.execute(
        f"INSERT INTO {_LEDGER_TABLE} (id, applied_at, from_version, to_version) "  # nosec B608 — table name and applied_at_sql are module constants or "?"; the caller's timestamp is bound as a parameter
        f"VALUES (?, {applied_at_sql}, ?, ?)",
        (spec.id, *applied_at_params, spec.from_version, spec.to_version),
    )


def _split_statements(sql: str) -> list[str]:
    """Split ``mutation_sql`` into individual complete statements.

    Fragments accumulate until ``sqlite3.complete_statement`` accepts the
    accumulated text, so semicolons inside trigger bodies do not cut a statement
    early. Empty or whitespace-only fragments are skipped; an incomplete trailing
    fragment is passed through so the execute call surfaces the syntax error.
    """
    statements: list[str] = []
    fragment = ""
    for char in sql:
        fragment += char
        if sqlite3.complete_statement(fragment):
            if fragment.strip():
                statements.append(fragment)
            fragment = ""
    if fragment.strip():
        statements.append(fragment)
    return statements


def _run_pre_migration_gate(
    live_conn: sqlite3.Connection,
    backup_verifier: BackupVerifier,
) -> None:
    """Run the pre-migration gate and refuse without a verified backup (REQ-002).

    Order: WAL checkpoint -> SQLite backup-API copy into a temp file ->
    ``PRAGMA integrity_check`` on the copy -> injected domain verifier. A
    non-zero busy count from ``PRAGMA wal_checkpoint(FULL)`` means another
    connection still holds the WAL (REQ-004). Only backup-integrity and
    verifier failures carry ``NO_VERIFIED_BACKUP``. The temp copy is always
    closed and deleted.
    """
    checkpoint = live_conn.execute("PRAGMA wal_checkpoint(FULL)").fetchone()
    if int(checkpoint[0]) != 0:
        raise MigrationRefusalError(
            MigrationRefusalReason.CHECKPOINT_BUSY,
            "WAL checkpoint busy; another connection holds the database",
        )

    db_path = live_conn.execute("PRAGMA database_list").fetchone()[2]
    if not db_path or db_path == ":memory:":
        raise MigrationRefusalError(
            MigrationRefusalReason.IN_MEMORY_DATABASE,
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


@dataclass(frozen=True)
class MigrationArchive:
    """One durable pre-migration archive plus its audit artifact (REQ-001)."""

    archive_path: Path
    audit_path: Path
    sha256: str
    source_version: int
    created_at: str


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 16), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _remove_incomplete_archive(*paths: Path) -> None:
    """Delete partial archive/audit files so a failed archive leaves no decoy."""
    for path in paths:
        try:
            path.unlink(missing_ok=True)
        except OSError:
            logger.warning("Failed to remove incomplete archive file %s", path)


def archive_pre_migration(
    live_conn: sqlite3.Connection,
    archive_dir: Path,
) -> MigrationArchive:
    """Copy the pre-run database state to a durable archive (REQ-001, fail closed).

    Called after the gate and before any mutation, so the archive captures the
    exact pre-run state. The target directory comes only from the caller and
    must exist and be writable, else ``NO_ARCHIVE_TARGET``; any other failure
    raises ``ARCHIVE_FAILURE`` and partial files are removed. Nothing prunes
    archives. The archive is ``<db-stem>-v<user_version>-<utc-stamp>.sqlite``
    with a ``<same-stem>.audit.json`` sidecar recording path, SHA-256, source
    database/version, creation time, and ``retention_status`` ``"unset"``.
    """
    archive_dir = Path(archive_dir)
    db_path = live_conn.execute("PRAGMA database_list").fetchone()[2]
    if not db_path or db_path == ":memory:":
        raise MigrationRefusalError(
            MigrationRefusalReason.IN_MEMORY_DATABASE,
            "cannot archive an in-memory database before migration",
        )

    if not archive_dir.is_dir() or not os.access(archive_dir, os.W_OK | os.X_OK):
        raise MigrationRefusalError(
            MigrationRefusalReason.NO_ARCHIVE_TARGET,
            f"archive target is missing or unwritable: {archive_dir}",
        )

    source_version = int(live_conn.execute("PRAGMA user_version").fetchone()[0])
    now = datetime.now(UTC)
    created_at = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    archive_path = archive_dir / (
        f"{Path(db_path).stem}-v{source_version}-{now.strftime('%Y%m%dT%H%M%SZ')}.sqlite"
    )
    audit_path = archive_path.with_suffix(".audit.json")

    archive_conn: sqlite3.Connection | None = None
    try:
        archive_conn = sqlite3.connect(str(archive_path))
        live_conn.backup(archive_conn)
        integrity = str(archive_conn.execute("PRAGMA integrity_check").fetchone()[0])
        if integrity != "ok":
            raise MigrationRefusalError(
                MigrationRefusalReason.ARCHIVE_FAILURE,
                f"archive integrity check failed: {integrity}",
            )
        archive_conn.close()
        archive_conn = None
        sha256 = _sha256_file(archive_path)
        audit = {
            "archive_path": str(archive_path),
            "sha256": sha256,
            "source_db": db_path,
            "source_version": source_version,
            "created_at": created_at,
            "retention_status": "unset",
        }
        audit_path.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    except MigrationRefusalError:
        _remove_incomplete_archive(archive_path, audit_path)
        raise
    except OSError as e:
        _remove_incomplete_archive(archive_path, audit_path)
        raise MigrationRefusalError(
            MigrationRefusalReason.NO_ARCHIVE_TARGET,
            f"cannot write archive to {archive_dir}: {e}",
        ) from e
    except sqlite3.Error as e:
        _remove_incomplete_archive(archive_path, audit_path)
        raise MigrationRefusalError(
            MigrationRefusalReason.ARCHIVE_FAILURE,
            f"archive copy failed: {e}",
        ) from e

    logger.info("Pre-migration archive: %s (sha256=%s).", archive_path, sha256)
    return MigrationArchive(
        archive_path, audit_path, sha256, source_version, created_at
    )


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
        archive_dir: Path | None = None,
    ) -> list[LedgerRow]:
        """Apply a resolved forward path, one transaction per step (REQ-001/004).

        Runs the pre-migration gate once, then each step in one runner-owned
        transaction: preconditions, optional foreign-key switch, BEGIN IMMEDIATE,
        the mutation statements, the ledger row, ``PRAGMA foreign_key_check`` when
        keys were switched off, any ``pre_commit_verification``, then commit; the
        postcondition re-check runs after commit and the foreign-key setting is
        restored in ``finally``. A failing step rolls back that step entirely and
        leaves the database at the last ledger-recorded version (AC-2). Dry-run
        gates a throwaway backup-API snapshot and mutates nothing (AC-5). With
        ``archive_dir`` supplied (apply only), the pre-run state is archived
        first (REQ-001).

        Args:
            conn: Open connection to the canonical database being migrated.
            path: Ordered forward path from :meth:`plan`.
            backup_verifier: Domain backup verifier injected by the caller.
            dry_run: When True, gate a throwaway snapshot and mutate nothing.
            archive_dir: Optional durable archive target; a failure refuses.
        """
        if not path:
            logger.info("No migration steps to apply.")
            return []

        if dry_run:
            logger.info(
                "Dry-run: gating %d step(s) against a throwaway snapshot.", len(path)
            )
            db_path = conn.execute("PRAGMA database_list").fetchone()[2]
            if not db_path or db_path == ":memory:":
                raise MigrationRefusalError(
                    MigrationRefusalReason.IN_MEMORY_DATABASE,
                    "cannot dry-run against an in-memory database",
                )
            fd, tmp_path = tempfile.mkstemp(suffix=".sqlite", prefix="migration-dryrun-")
            os.close(fd)
            try:
                # Backup-API snapshot (not a file copy): committed -wal content
                # is included, so the gate sees what the steps would see.
                dry_conn = sqlite3.connect(tmp_path)
                try:
                    conn.backup(dry_conn)
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

        if conn.in_transaction:
            raise RuntimeError(
                "refusing to migrate while the connection already has an open "
                "transaction; commit or roll it back before calling apply"
            )

        _run_pre_migration_gate(conn, backup_verifier)

        if archive_dir is not None:
            # Archive the exact pre-run state, before the ledger is created.
            archive_pre_migration(conn, archive_dir)

        # Create the ledger only after the gate passes, so a gate refusal leaves
        # the original database byte-for-byte intact (AC-2).
        ensure_ledger(conn)
        conn.commit()

        applied: list[LedgerRow] = []
        for spec in path:
            self._apply_step(conn, spec)
            if spec.postcondition is not None:
                spec.postcondition(conn)
            last = read_ledger(conn)[-1]
            applied.append(
                LedgerRow(
                    id=spec.id,
                    applied_at=last.applied_at,
                    from_version=spec.from_version,
                    to_version=spec.to_version,
                    seq=last.seq,
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
        """Run one migration step in a single runner-owned transaction.

        Order: preconditions; optional foreign-key switch (outside the
        transaction, because ``PRAGMA foreign_keys`` is a no-op inside one); an
        open-transaction guard; ``BEGIN IMMEDIATE``; each statement of
        ``mutation_sql`` split with :func:`_split_statements`; the ledger row;
        ``PRAGMA foreign_key_check`` when keys were switched off; any
        ``pre_commit_verification``; commit. Any failure rolls back the whole
        step — schema, ``user_version``, and ledger all stay unchanged (AC-1/AC-2/
        AC-4). A spec with empty ``mutation_sql`` still runs preconditions, the
        ledger write, and the commit in one transaction. The caller's
        ``isolation_level`` is untouched otherwise.
        """
        for precondition in spec.preconditions:
            precondition(conn)

        saved_fk: int | None = None
        try:
            if spec.disable_foreign_keys:
                saved_fk = int(conn.execute("PRAGMA foreign_keys").fetchone()[0])
                conn.execute("PRAGMA foreign_keys=OFF")

            if conn.in_transaction:
                raise RuntimeError(
                    f"step {spec.id!r}: refusing to start a migration step while "
                    "the connection already has an open transaction"
                )

            conn.execute("BEGIN IMMEDIATE")
            for statement in _split_statements(spec.mutation_sql):
                conn.execute(statement)
            record_applied(conn, spec)

            if spec.disable_foreign_keys:
                violations = conn.execute("PRAGMA foreign_key_check").fetchall()
                if violations:
                    raise RuntimeError(
                        f"step {spec.id!r}: PRAGMA foreign_key_check reported "
                        f"{len(violations)} dangling reference(s) after the mutation"
                    )

            if spec.pre_commit_verification is not None:
                spec.pre_commit_verification(conn)

            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            if saved_fk is not None:
                conn.execute(f"PRAGMA foreign_keys={saved_fk}")  # nosec B608 — saved_fk is a 0/1 pragma value read from the connection
