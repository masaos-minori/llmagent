"""scripts/eventbus/db_tools.py — EventBus-owned database tooling.

Create-or-validate, archive, and verify eventbus.sqlite, resolving the database path
from the EventBus configuration file only. Deploy and operator entry point (``python -m eventbus.db_tools``); it is not
part of the service request path.

The path is read from the ``db_path`` key with the standard library instead of
``eventbus.config.load_config``: load_config resolves token references and rejects an
empty ``auth_token``, and ``deploy/init_db.sh`` runs without the EventBus token
variables.
"""

from __future__ import annotations

import argparse
import logging
import sqlite3
import sys
import tomllib
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import quote

from shared.schema_fingerprint import apply_ddl_in_memory, assert_matches

from eventbus.config import get_config_path
from eventbus.db_conn import open_db
from eventbus.schema import _SCHEMA_PATH

logger = logging.getLogger(__name__)

_ARCHIVE_TIMESTAMP_FORMAT = "%Y%m%d_%H%M%S"


def read_db_path() -> Path:
    """Return the database path from the EventBus configuration file's ``db_path``."""
    config_path = get_config_path()
    try:
        data = tomllib.loads(config_path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ValueError(f"cannot read eventbus config {config_path}: {exc}") from exc
    except tomllib.TOMLDecodeError as exc:
        raise ValueError(f"invalid eventbus config {config_path}: {exc}") from exc
    value = data.get("db_path")
    if not isinstance(value, str) or not value:
        raise ValueError(
            f"eventbus config {config_path} must set a non-empty string 'db_path'"
        )
    return Path(value)


def schema_sql() -> str:
    """Return the canonical DDL text of ``scripts/eventbus/schema.sql``."""
    return _SCHEMA_PATH.read_text(encoding="utf-8")


def schema_version() -> int:
    """Return the ``PRAGMA user_version`` the canonical DDL produces.

    ``schema.sql`` no longer stamps a version, so the create path leaves a fresh
    database at the SQLite default (0); the value is derived from an in-memory
    apply of the DDL so it stays consistent with that path.
    """
    conn = apply_ddl_in_memory(schema_sql())
    try:
        return int(conn.execute("PRAGMA user_version").fetchone()[0])
    finally:
        conn.close()


def ensure(db_path: Path | None = None) -> Path:
    """Create the database when absent, or validate it when present.

    Reuses the service's own open path, so a fresh file receives the canonical DDL,
    a current database is fingerprint-validated, and any other database raises
    ``RuntimeError`` and is left unchanged.
    """
    path = db_path if db_path is not None else read_db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    open_db(str(path)).close()
    return path


def _check_database(path: Path) -> None:
    """Raise ``RuntimeError`` unless ``path`` is intact and has the canonical shape."""
    uri = f"file:{quote(str(path))}?mode=ro"
    try:
        conn = sqlite3.connect(uri, uri=True)
        try:
            result = conn.execute("PRAGMA integrity_check").fetchone()
            if result is None or result[0] != "ok":
                raise RuntimeError(f"{path}: integrity_check reported {result}")
            assert_matches(conn, schema_sql(), label=str(path))
        finally:
            conn.close()
    except sqlite3.Error as exc:
        raise RuntimeError(f"{path}: cannot be verified: {exc}") from exc


def verify(db_path: Path | None = None) -> Path:
    """Verify integrity and canonical shape of the database; return its path."""
    path = db_path if db_path is not None else read_db_path()
    if not path.exists():
        raise FileNotFoundError(f"eventbus database not found: {path}")
    _check_database(path)
    return path


def rotate(archive_dir: str | Path | None = None) -> Path:
    """Write a verified, WAL-consistent archive of the database and return its path.

    The SQLite online backup API produces the copy, which then passes the same
    checks as :func:`verify`. A failing archive raises and stays in place for
    forensics.
    """
    path = read_db_path()
    if not path.exists():
        raise FileNotFoundError(f"eventbus database not found: {path}")
    dest_dir = Path(archive_dir) if archive_dir is not None else path.parent / "archive"
    dest_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime(_ARCHIVE_TIMESTAMP_FORMAT)
    dest = dest_dir / f"{path.stem}_{stamp}{path.suffix}"
    src = sqlite3.connect(str(path))
    dst = sqlite3.connect(str(dest))
    try:
        src.backup(dst)
    finally:
        dst.close()
        src.close()
    _check_database(dest)
    logger.info("eventbus database archived and verified: %s", dest)
    return dest


def main(argv: Sequence[str] | None = None) -> int:
    """Command-line entry point; returns the process exit code."""
    parser = argparse.ArgumentParser(prog="eventbus.db_tools", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("ensure", help="create the database or validate it")
    sub.add_parser("verify", help="check integrity and canonical shape")
    rotate_parser = sub.add_parser("rotate", help="write a verified archive")
    rotate_parser.add_argument("--archive-dir", default=None)
    sub.add_parser("path", help="print the configured database path")
    sub.add_parser("version", help="print the canonical schema version")
    args = parser.parse_args(sys.argv[1:] if argv is None else list(argv))
    try:
        if args.command == "ensure":
            sys.stdout.write(f"{ensure()}\n")
        elif args.command == "verify":
            sys.stdout.write(f"{verify()}\n")
        elif args.command == "rotate":
            sys.stdout.write(f"{rotate(args.archive_dir)}\n")
        elif args.command == "path":
            sys.stdout.write(f"{read_db_path()}\n")
        else:
            sys.stdout.write(f"{schema_version()}\n")
    except (ValueError, RuntimeError, OSError, sqlite3.Error) as exc:
        sys.stderr.write(f"eventbus.db_tools {args.command}: {exc}\n")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
