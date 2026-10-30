#!/usr/bin/env python3
"""scripts/db/migrate_db.py — workflow.sqlite migration CLI.

Usage:
  migrate_db.py --status             print the current version and the ledger
  migrate_db.py --dry-run            run the migration on a throwaway copy
  migrate_db.py --apply              migrate behind a verified backup

Stop the agent before `--apply`: the agent process holds `workflow.sqlite`. `--dry-run`
and `--status` never modify the database file.

Exit codes: 0 success, 2 refused (downgrade, unknown path, no verified backup),
3 a migration failed and was rolled back.
"""

import argparse
import logging
import sqlite3
import sys
from pathlib import Path

from shared.db_migrations import (
    MigrationFailedError,
    MigrationRefusedError,
    read_ledger,
    run_migrations,
)

from db.config import build_db_config
from db.migrations_workflow import (
    MIGRATIONS,
    WORKFLOW_DOMAIN,
    read_workflow_version,
)
from db.schema_sql import WORKFLOW_SCHEMA_VERSION

logger = logging.getLogger(__name__)

EXIT_OK = 0
EXIT_REFUSED = 2
EXIT_FAILED = 3


def _parse(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Migrate workflow.sqlite.")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--status", action="store_true", help="print version and ledger")
    mode.add_argument("--dry-run", action="store_true", help="migrate a copy only")
    mode.add_argument("--apply", action="store_true", help="migrate the database")
    parser.add_argument("--db-path", default=None, help="override workflow_db_path")
    parser.add_argument("--backup-dir", default=None, help="pre-migration backup dir")
    return parser.parse_args(argv)


def _status(db_path: Path) -> int:
    if not db_path.exists():
        sys.stdout.write(f"workflow.sqlite not found: {db_path}\n")
        return EXIT_REFUSED
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        version = read_workflow_version(conn)
        has_ledger = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='schema_migrations'"
        ).fetchone()
        ledger = read_ledger(conn) if has_ledger else None
    finally:
        conn.close()
    sys.stdout.write(f"version: {version}\ntarget: {WORKFLOW_SCHEMA_VERSION}\n")
    if ledger is None:
        sys.stdout.write("ledger: absent\n")
    else:
        sys.stdout.write("ledger: " + (", ".join(ledger) or "empty") + "\n")
    return EXIT_OK


def main(argv: list[str] | None = None) -> int:
    """Run the CLI; return the process exit code."""
    args = _parse(argv)
    db_path = Path(args.db_path or build_db_config().workflow_db_path)
    if args.status:
        return _status(db_path)
    backup_dir = (
        Path(args.backup_dir)
        if args.backup_dir
        else (db_path.parent / "migration_backups")
    )
    try:
        report = run_migrations(
            db_path,
            WORKFLOW_DOMAIN,
            MIGRATIONS,
            WORKFLOW_SCHEMA_VERSION,
            backup_dir,
            dry_run=args.dry_run,
        )
    except MigrationRefusedError as exc:
        sys.stdout.write(f"refused: {exc}\n")
        return EXIT_REFUSED
    except MigrationFailedError as exc:
        sys.stdout.write(f"failed: {exc}\n")
        return EXIT_FAILED
    sys.stdout.write(
        f"{'dry-run ' if report.dry_run else ''}ok: {report.from_version} -> "
        f"{report.to_version}, applied: {', '.join(report.applied) or 'none'}"
        f"{'' if report.backup_path is None else f', backup: {report.backup_path}'}\n"
    )
    return EXIT_OK


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    sys.exit(main())
