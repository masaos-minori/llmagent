#!/usr/bin/env python3
"""db/rotation.py — Database rotation operations."""

import logging
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from shared.config_loader import ConfigLoader

from db.config import build_db_config

logger = logging.getLogger(__name__)


def _archive_db_file(db_path: Path, archive_dir: str | Path | None) -> Path:
    """Create a WAL-consistent backup of db_path using the SQLite online backup API."""
    if not db_path.exists():
        raise FileNotFoundError(f"DB file not found: {db_path}")

    if archive_dir is None:
        cfg = ConfigLoader().load("agent.toml")
        raw_archive_dir: str | None = cfg.get("sqlite_archive_dir")
        if raw_archive_dir is None or not isinstance(raw_archive_dir, str):
            raw_archive_dir = "/opt/llm/db/archive"
        archive_dir = raw_archive_dir

    dest_dir = Path(archive_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")  # noqa: UP017
    dest = dest_dir / f"{db_path.stem}_{ts}{db_path.suffix}"

    src = sqlite3.connect(str(db_path))
    dst = sqlite3.connect(str(dest))
    try:
        src.backup(dst)
    finally:
        dst.close()
        src.close()

    size = dest.stat().st_size
    logger.info("DB archived: %s (%s bytes)", dest, size)
    return dest


def rotate_session_db(archive_dir: str | Path | None = None) -> Path:
    """Archive session.sqlite to archive_dir with a timestamp suffix; returns the archive path."""
    db_cfg = build_db_config()
    return _archive_db_file(Path(db_cfg.session_db_path), archive_dir)


def rotate_workflow_db(archive_dir: str | Path | None = None) -> Path:
    """Archive workflow.sqlite to archive_dir with a timestamp suffix; returns the archive path."""
    db_cfg = build_db_config()
    return _archive_db_file(Path(db_cfg.workflow_db_path), archive_dir)


def rotate_all_dbs(archive_dir: str | Path | None = None) -> tuple[Path, Path, Path]:
    """Archive all three databases (rag, session, workflow); returns (rag_archive_path, session_archive_path, workflow_archive_path)."""
    db_cfg = build_db_config()
    rag_dest = _archive_db_file(Path(db_cfg.rag_db_path), archive_dir)
    ses_dest = rotate_session_db(archive_dir)
    wf_dest = rotate_workflow_db(archive_dir)
    return rag_dest, ses_dest, wf_dest


def rotate_db(archive_dir: str | Path | None = None) -> tuple[Path, Path]:
    """Archive both rag.sqlite and session.sqlite; returns (rag_archive_path, session_archive_path)."""
    db_cfg = build_db_config()
    rag_dest = _archive_db_file(Path(db_cfg.rag_db_path), archive_dir)
    ses_dest = rotate_session_db(archive_dir)
    return rag_dest, ses_dest
