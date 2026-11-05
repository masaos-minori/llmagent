#!/usr/bin/env python3
"""scripts/db/migrate_db.py — Workflow forward-only migration CLI.

Operator entry point for the ``workflow.sqlite`` forward-only migration path
(dbmig001). ``--dry-run``, ``--apply``, and ``--status`` run through the shared
framework (``shared.db_migrations.MigrationRunner``) and the workflow registry
(``db.migrations_workflow.REGISTRY``). ``--apply`` requires ``--archive-dir``:
the operator-supplied durable pre-migration archive target (REQ-001). Unlike
the eventbus CLI (row 05) the workflow database is embedded in the agent
process rather than behind a listening service, so no service-listener guard
is needed; the CLI relies on SQLite busy/lock handling and refuses when the
exclusive step fails. REQ-001 migration framework and archive, REQ-002 backup
gate, REQ-004 dry-run and refusal exit classes, REQ-006 ledger status.
"""

from __future__ import annotations

import argparse
import logging
import sqlite3
import sys
from pathlib import Path

from shared.db_migrations import (
    MigrationRefusalError,
    MigrationRefusalReason,
    read_ledger,
)

from db.helper import SQLiteHelper
from db.migrations_workflow import REGISTRY, runner, verify_backup

logger = logging.getLogger(__name__)

# Exit code classes (dbmig001 row 07 contract): distinguish refusal classes at
# the process boundary where tests can observe them. Gate-family reasons
# (dbmigsafe001 REQ-004) map to EXIT_GATE_FAILURE; all other refusals map to
# EXIT_REFUSAL.
EXIT_OK = 0
EXIT_GATE_FAILURE = 1
EXIT_REFUSAL = 2

# Refusal reasons whose failure is a pre-migration safety-gate failure rather
# than a planning/semantic refusal.
_GATE_FAMILY_REASONS = frozenset(
    {
        MigrationRefusalReason.NO_VERIFIED_BACKUP,
        MigrationRefusalReason.CHECKPOINT_BUSY,
        MigrationRefusalReason.NO_ARCHIVE_TARGET,
        MigrationRefusalReason.ARCHIVE_FAILURE,
    }
)

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
            f"SELECT version FROM {_WORKFLOW_VERSION_TABLE} "  # nosec B608 — table name is a module-level constant, no user input
            "ORDER BY applied_at DESC LIMIT 1"
        ).fetchone()
    except sqlite3.OperationalError:
        # The table is absent on a fresh database; nothing to cross-check.
        return None
    return row[0] if row else None


def _cmd_status(conn: sqlite3.Connection) -> int:
    """Print the current version, legacy marker, and every ledger row.

    Field semantics (REQ-006): ``user_version=`` is the integer migration code
    from ``PRAGMA user_version``; ``marker=`` is the semantic
    ``workflow_schema_version`` string. Both names are stable machine-readable
    fields because row 11's drill harness reports ledger state next to drill
    artifacts.
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
        help="Gate against a throwaway backup-API snapshot; mutate nothing.",
    )
    mode.add_argument(
        "--apply",
        action="store_true",
        help="Apply the registered forward path, gate-gated, archiving the "
        "pre-run state to --archive-dir (required).",
    )
    mode.add_argument(
        "--status",
        action="store_true",
        help="Print user_version= (integer migration code), marker= (semantic "
        "workflow_schema_version string), and ledger rows.",
    )
    parser.add_argument(
        "--db",
        type=str,
        default=None,
        help=(
            "Operate on this database file instead of the configured workflow "
            "database (rehearsal on a copy)."
        ),
    )
    parser.add_argument(
        "--archive-dir",
        type=Path,
        default=None,
        help=(
            "Durable pre-migration archive directory (required for --apply; "
            "must already exist and be writable). Never inferred or defaulted."
        ),
    )
    args = parser.parse_args(argv)

    if not (args.dry_run or args.apply or args.status):
        parser.print_help()
        return EXIT_REFUSAL

    # A missing --db path is a refusal, checked before any connect: opening it
    # with sqlite3 would silently create an empty file (REQ-006).
    if args.db is not None and not Path(args.db).is_file():
        logger.error("refused: --db path %s is not an existing file", args.db)
        return EXIT_REFUSAL

    # Resolve the workflow DB path via the db layer's own configuration, the
    # same mechanism create_schema.py and rotation.py use. With --db the helper
    # bypasses configuration and operates on the given file.
    helper = SQLiteHelper("workflow", db_path=args.db).open(write_mode=True)
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

        # Preflight the first step's preconditions before any mutation: only the
        # first step's preconditions are defined against the current database
        # state. Later steps' preconditions describe the state the preceding step
        # produces, so they are evaluated inside apply()'s per-step transaction
        # (a mid-chain refusal leaves the database at the last completed step —
        # AC-2, exercised by the step-failure tests). Preflighting the first step
        # keeps the "a refusal never touches the database" invariant: the shared
        # runner commits the ledger table before the step loop, so a first-step
        # refusal raised inside apply() would otherwise leave a dangling empty
        # ledger behind (dbmig001 row 07).
        for precondition in path[0].preconditions:
            precondition(conn)

        if args.dry_run:
            runner.apply(conn, path, verify_backup, dry_run=True)
            print(
                f"dry-run: {len(path)} step(s) would apply "
                f"({current} -> {path[-1].to_version})."
            )
            return EXIT_OK

        # REQ-001: every --apply run names a durable archive target; no default
        # location is ever inferred (parser.error exits with code 2 = refusal).
        if args.archive_dir is None:
            parser.error("--apply requires --archive-dir")

        applied = runner.apply(conn, path, verify_backup, archive_dir=args.archive_dir)
        print(
            f"applied {len(applied)} step(s); "
            f"user_version now {_current_version(conn)}."
        )
        return EXIT_OK
    except MigrationRefusalError as exc:
        if exc.reason in _GATE_FAMILY_REASONS:
            logger.error("gate failed (%s): %s", exc.reason, exc)
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
