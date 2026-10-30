"""scripts/shared/db_migrations.py — Domain-neutral forward-only SQLite migration framework.

A domain (eventbus, workflow) supplies a `MigrationDomain` (how its schema version is
read and written, and how its shape is verified) and a registry of `MigrationSpec`
steps. `run_migrations` resolves a unique forward path, takes a verified backup,
applies each step in one write transaction together with its ledger row, and refuses
downgrades, unknown paths, and any run without a verified backup. Imports only the
standard library so shared-is-leaf and eventbus-is-isolated stay KEPT.
"""

from __future__ import annotations

import logging
import shutil
import sqlite3
import tempfile
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

logger = logging.getLogger(__name__)

LEDGER_DDL = """CREATE TABLE IF NOT EXISTS schema_migrations (
    id           TEXT PRIMARY KEY,
    applied_at   TEXT NOT NULL,
    from_version TEXT NOT NULL,
    to_version   TEXT NOT NULL
)"""


class MigrationError(RuntimeError):
    """Base class for migration errors; keeps `except RuntimeError` handlers working."""


class MigrationRefusedError(MigrationError):
    """Raised when a migration is refused before any mutation of the database."""


class MigrationFailedError(MigrationError):
    """Raised when a step failed and was rolled back; names the migration id."""

    def __init__(self, migration_id: str, cause: BaseException) -> None:
        self.migration_id = migration_id
        super().__init__(
            f"migration {migration_id} failed and was rolled back: {cause}"
        )


@dataclass(frozen=True)
class MigrationSpec:
    """One forward step. `apply` must use `conn.execute`, never `executescript`.

    `executescript` commits the caller's transaction first, which would break the
    one-transaction-per-step boundary.
    """

    migration_id: str
    from_version: str
    to_version: str
    apply: Callable[[sqlite3.Connection], None]
    precondition: Callable[[sqlite3.Connection], None] | None = None
    postcondition: Callable[[sqlite3.Connection], None] | None = None


@dataclass(frozen=True)
class MigrationDomain:
    """How one database is opened, stores its version, and has its shape verified.

    `connect` opens a database file by path. The framework never opens database
    files itself, so the shared layer keeps no direct access to any domain database.
    """

    name: str
    connect: Callable[[str], sqlite3.Connection]
    read_version: Callable[[sqlite3.Connection], str | None]
    write_version: Callable[[sqlite3.Connection, str], None]
    verify_shape: Callable[[sqlite3.Connection, str], None]


@dataclass(frozen=True)
class MigrationReport:
    """Outcome of one `run_migrations` call."""

    domain: str
    from_version: str | None
    to_version: str
    applied: tuple[str, ...]
    backup_path: Path | None
    dry_run: bool


def _now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def ensure_ledger(conn: sqlite3.Connection) -> None:
    """Create the `schema_migrations` ledger when absent (idempotent)."""
    conn.execute(LEDGER_DDL)


def read_ledger(conn: sqlite3.Connection) -> list[str]:
    """Return the applied migration ids in application order."""
    rows = conn.execute(
        "SELECT id FROM schema_migrations ORDER BY applied_at, rowid"
    ).fetchall()
    return [str(r[0]) for r in rows]


def resolve_path(
    specs: Sequence[MigrationSpec], current: str | None, target: str
) -> list[MigrationSpec]:
    """Return the ordered specs leading from `current` to `target`.

    Raises MigrationRefusedError for an unversioned database, a downgrade, an
    unknown version, a missing hop, two specs leaving one version, or a cycle.
    """
    if current is None:
        raise MigrationRefusedError("database carries no schema version")
    if current == target:
        return []
    by_from: dict[str, list[MigrationSpec]] = {}
    for spec in specs:
        by_from.setdefault(spec.from_version, []).append(spec)
    path: list[MigrationSpec] = []
    seen = {current}
    version = current
    while version != target:
        candidates = by_from.get(version, [])
        if not candidates:
            raise MigrationRefusedError(
                f"no registered forward path from {current!r} to {target!r} "
                f"(downgrade or unknown version; stuck at {version!r})"
            )
        if len(candidates) > 1:
            ids = ", ".join(c.migration_id for c in candidates)
            raise MigrationRefusedError(f"ambiguous path from {version!r}: {ids}")
        spec = candidates[0]
        if spec.to_version in seen:
            raise MigrationRefusedError(
                f"migration cycle at {spec.migration_id}: {spec.to_version!r}"
            )
        seen.add(spec.to_version)
        path.append(spec)
        version = spec.to_version
    return path


def _integrity_ok(
    path: Path, connect: Callable[[str], sqlite3.Connection]
) -> tuple[bool, str]:
    """Run PRAGMA integrity_check on a database file; return (ok, detail)."""
    conn = connect(str(path))
    try:
        detail = str(conn.execute("PRAGMA integrity_check").fetchone()[0])
    finally:
        conn.close()
    return detail == "ok", detail


def create_verified_backup(
    db_path: Path,
    backup_dir: Path,
    connect: Callable[[str], sqlite3.Connection],
) -> Path:
    """Checkpoint the WAL, copy the database, and verify the copy's integrity.

    The copy uses the SQLite online backup API. A copy that fails
    `PRAGMA integrity_check` is deleted and the migration is refused.
    """
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    dest = backup_dir / f"{db_path.stem}_premigration_{stamp}{db_path.suffix}"
    src = connect(str(db_path))
    try:
        src.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchall()
        dst = connect(str(dest))
        try:
            src.backup(dst)
        finally:
            dst.close()
    finally:
        src.close()
    ok, detail = _integrity_ok(dest, connect)
    if not ok:
        dest.unlink(missing_ok=True)
        raise MigrationRefusedError(
            f"pre-migration backup failed integrity check: {detail}"
        )
    return dest


def _apply_step(
    conn: sqlite3.Connection, domain: MigrationDomain, spec: MigrationSpec
) -> None:
    """Apply one step and its ledger row in a single write transaction."""
    conn.execute("BEGIN IMMEDIATE")
    try:
        ensure_ledger(conn)
        found = domain.read_version(conn)
        if found != spec.from_version:
            raise MigrationRefusedError(
                f"{spec.migration_id} expects version {spec.from_version!r}, "
                f"found {found!r}"
            )
        if spec.precondition is not None:
            spec.precondition(conn)
        spec.apply(conn)
        domain.write_version(conn, spec.to_version)
        conn.execute(
            "INSERT INTO schema_migrations (id, applied_at, from_version, to_version)"
            " VALUES (?, ?, ?, ?)",
            (spec.migration_id, _now(), spec.from_version, spec.to_version),
        )
        if spec.postcondition is not None:
            spec.postcondition(conn)
        domain.verify_shape(conn, spec.to_version)
        conn.execute("COMMIT")
    except MigrationRefusedError:
        conn.execute("ROLLBACK")
        raise
    except Exception as exc:
        conn.execute("ROLLBACK")
        raise MigrationFailedError(spec.migration_id, exc) from exc
    except BaseException:
        if conn.in_transaction:
            conn.execute("ROLLBACK")
        raise


def _migrate(
    db_path: Path,
    domain: MigrationDomain,
    specs: Sequence[MigrationSpec],
    target_version: str,
    backup_dir: Path,
) -> MigrationReport:
    if not db_path.exists():
        raise MigrationRefusedError(f"database not found: {db_path}")
    conn = domain.connect(str(db_path))
    conn.isolation_level = None
    try:
        current = domain.read_version(conn)
        path = resolve_path(specs, current, target_version)
        if not path:
            return MigrationReport(
                domain.name, current, target_version, (), None, False
            )
        backup = create_verified_backup(db_path, backup_dir, domain.connect)
        logger.info(
            "migration %s: backup %s verified; applying %s",
            domain.name,
            backup,
            [s.migration_id for s in path],
        )
        applied: list[str] = []
        for spec in path:
            _apply_step(conn, domain, spec)
            applied.append(spec.migration_id)
        return MigrationReport(
            domain.name, current, target_version, tuple(applied), backup, False
        )
    except MigrationError as exc:
        logger.error("migration %s refused or failed: %s", domain.name, exc)
        raise
    finally:
        conn.close()


def run_migrations(
    db_path: Path,
    domain: MigrationDomain,
    specs: Sequence[MigrationSpec],
    target_version: str,
    backup_dir: Path,
    dry_run: bool = False,
) -> MigrationReport:
    """Migrate `db_path` to `target_version` along the registered forward path.

    A no-op path (already at the target) takes no backup and changes nothing. With
    `dry_run`, the whole sequence runs on a byte copy in a temporary directory, so
    the original file stays byte-identical.
    """
    if not dry_run:
        return _migrate(db_path, domain, specs, target_version, backup_dir)
    if not db_path.exists():
        raise MigrationRefusedError(f"database not found: {db_path}")
    with tempfile.TemporaryDirectory(prefix="dbmig-dryrun-") as tmp:
        tmp_dir = Path(tmp)
        copy = tmp_dir / db_path.name
        shutil.copy2(db_path, copy)
        wal = Path(f"{db_path}-wal")
        if wal.exists():
            shutil.copy2(wal, Path(f"{copy}-wal"))
        report = _migrate(copy, domain, specs, target_version, tmp_dir / "backups")
    return MigrationReport(
        report.domain,
        report.from_version,
        report.to_version,
        report.applied,
        None,
        True,
    )
