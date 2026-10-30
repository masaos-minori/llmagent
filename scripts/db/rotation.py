#!/usr/bin/env python3
"""scripts/db/rotation.py — Database rotation operations."""

import logging
import sqlite3
from pathlib import Path

from shared.config_loader import ConfigLoader

from db.config import build_db_config, format_timestamp
from db.recovery import DbCondition, run_integrity_check, verify_domain_identity

logger = logging.getLogger(__name__)


def _resolve_archive_dir() -> str:
    """Resolve the default archive directory from agent.toml, falling back to a hardcoded path."""
    cfg = ConfigLoader().load("agent.toml")
    raw_archive_dir: str | None = cfg.get("sqlite_archive_dir")
    if raw_archive_dir is None or not isinstance(raw_archive_dir, str):
        return "/opt/llm/db/archive"
    return raw_archive_dir


def _archive_db_file(
    db_path: Path,
    archive_dir: str | Path | None,
    *,
    target: str,
) -> Path:
    """Create a WAL-consistent, verified backup of db_path.

    The SQLite online backup API produces the copy; the archive then passes the
    domain integrity and identity checks before it is returned as a recovery
    point. A failing archive raises and is left in place for forensics
    (REQ-002 verified recovery points).
    """
    if not db_path.exists():
        raise FileNotFoundError(f"DB file not found: {db_path}")

    if archive_dir is None:
        archive_dir = _resolve_archive_dir()

    dest_dir = Path(archive_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)

    ts = format_timestamp()
    dest = dest_dir / f"{db_path.stem}_{ts}{db_path.suffix}"

    src = sqlite3.connect(str(db_path))
    dst = sqlite3.connect(str(dest))
    try:
        src.backup(dst)
    finally:
        dst.close()
        src.close()

    _verify_archive(dest, target)

    size = dest.stat().st_size
    logger.info("DB archived and verified: %s (%s bytes)", dest, size)
    return dest


def _verify_archive(dest: Path, target: str) -> None:
    """Raise RuntimeError unless ``dest`` passes integrity and identity checks.

    Integrity runs for every domain; domain identity runs only where a required
    table is defined (rag/session). Unmapped targets (workflow/eventbus) pass
    identity and are covered by their integrity result.
    """
    condition, integrity_detail = run_integrity_check(dest, target)
    if condition != DbCondition.HEALTHY:
        raise RuntimeError(
            f"archive verification failed for {dest}: "
            f"integrity check reported {integrity_detail}"
        )
    domain_ok, domain_detail = verify_domain_identity(dest, target)
    if not domain_ok:
        raise RuntimeError(f"archive verification failed for {dest}: {domain_detail}")


def rotate_session_db(archive_dir: str | Path | None = None) -> Path:
    """Archive session.sqlite to archive_dir with a timestamp suffix; returns the archive path."""
    db_cfg = build_db_config()
    return _archive_db_file(Path(db_cfg.session_db_path), archive_dir, target="session")


def rotate_workflow_db(archive_dir: str | Path | None = None) -> Path:
    """Archive workflow.sqlite to archive_dir with a timestamp suffix; returns the archive path."""
    db_cfg = build_db_config()
    return _archive_db_file(
        Path(db_cfg.workflow_db_path), archive_dir, target="workflow"
    )


def rotate_eventbus_db(archive_dir: str | Path | None = None) -> Path:
    """Archive eventbus.sqlite to archive_dir with a timestamp suffix; returns the archive path."""
    db_cfg = build_db_config()
    return _archive_db_file(
        Path(db_cfg.eventbus_db_path), archive_dir, target="eventbus"
    )


def rotate_all_dbs(
    archive_dir: str | Path | None = None,
) -> tuple[Path, Path, Path, Path]:
    """Archive all four databases (rag, session, workflow, eventbus); returns (rag_archive_path, session_archive_path, workflow_archive_path, eventbus_archive_path)."""
    db_cfg = build_db_config()
    rag_dest = _archive_db_file(Path(db_cfg.rag_db_path), archive_dir, target="rag")
    ses_dest = rotate_session_db(archive_dir)
    wf_dest = rotate_workflow_db(archive_dir)
    eb_dest = rotate_eventbus_db(archive_dir)
    return rag_dest, ses_dest, wf_dest, eb_dest


def rotate_db(archive_dir: str | Path | None = None) -> tuple[Path, Path]:
    """Archive both rag.sqlite and session.sqlite; returns (rag_archive_path, session_archive_path)."""
    db_cfg = build_db_config()
    rag_dest = _archive_db_file(Path(db_cfg.rag_db_path), archive_dir, target="rag")
    ses_dest = rotate_session_db(archive_dir)
    return rag_dest, ses_dest
