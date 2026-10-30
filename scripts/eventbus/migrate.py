#!/usr/bin/env python3
"""scripts/eventbus/migrate.py — EventBus forward-only migration CLI.

Operator entry point for the ``eventbus.sqlite`` forward-only migration path
(dbmig001). ``--dry-run``, ``--apply``, and ``--status`` run through the
shared framework (``shared.db_migrations.MigrationRunner``) and the EventBus
registry (``eventbus.migrations.REGISTRY``). The CLI refuses to mutate while the
EventBus service holds the database (a listener on the configured port), keeping
the single-writer assumption (ADR-008). REQ-001 migration framework, REQ-002
backup gate, REQ-004 dry-run, REQ-006 ledger status.
"""

from __future__ import annotations

import argparse
import logging
import socket
import sqlite3
import sys
from pathlib import Path

from shared.db_migrations import (
    MigrationRefusalError,
    MigrationRefusalReason,
    read_ledger,
)

from eventbus.config import get_config_path, load_config
from eventbus.migrations import REGISTRY, runner, verify_backup

logger = logging.getLogger(__name__)

# Exit code classes (dbmig001 row 05 contract): distinguish refusal classes at
# the process boundary where tests can observe them.
EXIT_OK = 0
EXIT_GATE_FAILURE = 1
EXIT_REFUSAL = 2
EXIT_SERVICE_BUSY = 3

# Fallback port when the config cannot be parsed for one; the configured port
# always wins when present.
_DEFAULT_PORT = 8015


def _service_holds_db(port: int) -> bool:
    """Return True if a listener exists on port (another process holds the DB).

    A successful connect means something is already bound and serving on the
    eventbus port, so this process must not open a second writer (ADR-008).
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(1)
        return sock.connect_ex(("127.0.0.1", port)) == 0


def _current_version(conn: sqlite3.Connection) -> int:
    """Return the database's current ``PRAGMA user_version``."""
    return int(conn.execute("PRAGMA user_version").fetchone()[0])


def _cmd_status(conn: sqlite3.Connection) -> int:
    """Print the current version and every ledger row, then return success."""
    rows = read_ledger(conn)
    print(f"user_version={_current_version(conn)}")
    if not rows:
        print("ledger: (empty)")
        return EXIT_OK
    for row in rows:
        print(f"  {row.id}  {row.from_version} -> {row.to_version}  {row.applied_at}")
    return EXIT_OK


def main(argv: list[str] | None = None) -> int:
    """Parse flags, guard against a live service, and run the migration mode."""
    parser = argparse.ArgumentParser(
        prog="migrate.py",
        description="Eventbus forward-only migration operator CLI.",
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
        help="Print the current version and ledger rows.",
    )
    args = parser.parse_args(argv)

    if not (args.dry_run or args.apply or args.status):
        parser.print_help()
        return EXIT_REFUSAL

    cfg = load_config(get_config_path())
    port = getattr(cfg, "port", _DEFAULT_PORT)

    # Service-busy precheck: --apply/--dry-run may read the live file, so refuse
    # while a service listens (single-writer assumption, ADR-008).
    if (args.apply or args.dry_run) and _service_holds_db(port):
        logger.error("refusing: a service is listening on port %d (holds the DB)", port)
        return EXIT_SERVICE_BUSY

    conn = sqlite3.connect(Path(cfg.db_path))
    try:
        if args.status:
            return _cmd_status(conn)

        current = _current_version(conn)
        path = runner.plan(current, read_ledger(conn), REGISTRY)

        if not path:
            print(f"already at target version {current}; no migration needed.")
            return EXIT_OK

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
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
