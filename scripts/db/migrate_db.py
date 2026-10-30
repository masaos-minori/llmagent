#!/usr/bin/env python3
"""scripts/db/migrate_db.py — Workflow forward-only migration CLI.

Operator entry point for the ``workflow.sqlite`` forward-only migration path
(dbmig001). ``--dry-run``, ``--apply``, and ``--status`` run through the shared
framework (``shared.db_migrations.MigrationRunner``) and the workflow registry
(``db.migrations_workflow.REGISTRY``). Unlike the eventbus CLI (row 05) the
workflow database is embedded in the agent process rather than behind a
listening service, so no service-listener guard is needed; the CLI relies on
SQLite busy/lock handling and refuses when the exclusive step fails.
REQ-001 migration framework, REQ-002 backup gate, REQ-004 dry-run, REQ-006
ledger status.
"""

from __future__ import annotations

import argparse
import logging
import sqlite3
import sys

from shared.db_migrations import (
    MigrationRefusalError,
    MigrationRefusalReason,
    read_ledger,
)

from db.helper import SQLiteHelper
from db.migrations_workflow import REGISTRY, runner, verify_backup

logger = logging.getLogger(__name__)

# Exit code classes (dbmig001 row 07 contract): distinguish refusal classes at
# the process boundary where tests can observe them.
EXIT_OK = 0
EXIT_GATE_FAILURE = 1
EXIT_REFUSAL = 2

# Legacy workflow schema marker table: the string version log that predates the
# integer ledger. Read for a cross-check on --status.
_WORKFLOW_VERSION_TABLE = "workflow_schema_version"


def _current_version(conn: sqlite3.Connection) -> int:
    """Return the database's current ``PRAGMA user_version``."""
    return int(conn.execute("PRAGMA user_version").fetchone()[0])


def _legacy_marker(conn: sqlite3.Connection) -> str | None:
    """Return the latest recorded ``workflow_schema_version`` string, if any.

    Returns None when the table is absent (a fresh database has not recorded a
    marker yet) so --status can cross-check the string against the ledger.
    """
    try:
        row = conn.execute(
            f"SELECT version FROM {_WORKFLOW_VERSION_TABLE} "
            "ORDER BY applied_at DESC LIMIT 1"
        ).fetchone()
    except sqlite3.OperationalError:
        # The table is absent on a fresh database; nothing to cross-check.
        return None
    return row[0] if row else None


def _cmd_status(conn: sqlite3.Connection) -> int:
    """Print the current version, legacy marker, and every ledger row.

    Output is machine-readable with stable field names because row 11's drill
    harness reports ledger state next to drill artifacts.
    """
    rows = read_ledger(conn)
    print(f"user_version={_current_version(conn)}")
    print(f"marker={_legacy_marker(conn)}")
    if not rows:
        print("ledger: (empty)")
        return EXIT_OK
    for row in rows:
        print(f"  {row.id}  {row.from_version} -> {row.to_version}  {row.applied_at}")
    return EXIT_OK


def main(argv: list[str] | None = None) -> int:
    """Parse flags and run the workflow migration mode."""
    parser = argparse.ArgumentParser(
        prog="migrate_db.py",
        description="Workflow forward-only migration operator CLI.",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--dry-run",
        action="store_true",
        help="Gate against a throwaway copy; mutate nothing.",
    )
    mode.add_argument(
        "--apply",
        action="store_true",
        help="Apply the registered forward path, gate-gated.",
    )
    mode.add_argument(
        "--status",
        action="store_true",
        help="Print the current version, legacy marker, and ledger rows.",
    )
    args = parser.parse_args(argv)

    if not (args.dry_run or args.apply or args.status):
        parser.print_help()
        return EXIT_REFUSAL

    # Resolve the workflow DB path via the db layer's own configuration, the
    # same mechanism create_schema.py and rotation.py use.
    helper = SQLiteHelper("workflow").open(write_mode=True)
    conn = helper.conn
    if conn is None:
        logger.error("failed to open workflow.sqlite")
        return EXIT_GATE_FAILURE
    try:
        if args.status:
            return _cmd_status(conn)

        current = _current_version(conn)
        path = runner.plan(current, read_ledger(conn), REGISTRY)

        if not path:
            print(f"already at target version {current}; no migration needed.")
            return EXIT_OK

        # Run each step's preconditions before any mutation. The shared runner
        # commits the ledger table before the step loop, so a step refusal raised
        # inside apply() would otherwise leave a dangling empty ledger behind.
        # Preflighting here keeps the "a refusal never touches the database"
        # invariant (AC-2) at the CLI boundary; preconditions are read-only, so
        # re-running them inside apply() is harmless.
        for spec in path:
            for precondition in spec.preconditions:
                precondition(conn)

        if args.dry_run:
            runner.apply(conn, path, verify_backup, dry_run=True)
            print(
                f"dry-run: {len(path)} step(s) would apply "
                f"({current} -> {path[-1].to_version})."
            )
            return EXIT_OK

        applied = runner.apply(conn, path, verify_backup)
        print(
            f"applied {len(applied)} step(s); "
            f"user_version now {_current_version(conn)}."
        )
        return EXIT_OK
    except MigrationRefusalError as exc:
        if exc.reason == MigrationRefusalReason.NO_VERIFIED_BACKUP:
            logger.error("gate failed (no verified backup): %s", exc)
            return EXIT_GATE_FAILURE
        logger.error("refused: %s", exc)
        return EXIT_REFUSAL
    except (sqlite3.Error, RuntimeError) as exc:
        logger.error("migration failed: %s", exc)
        return EXIT_GATE_FAILURE
    finally:
        helper.close()


if __name__ == "__main__":
    sys.exit(main())
