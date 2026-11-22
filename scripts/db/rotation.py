#!/usr/bin/env python3
"""scripts/db/rotation.py — Database rotation operations."""

import logging
import sqlite3
from pathlib import Path

from db.config import DbConfig, format_timestamp, resolve_unique_path
from db.maintenance import DbMaintenanceConfig
from db.recovery import run_integrity_check, verify_domain_identity
from db.recovery_classification import DbCondition

logger = logging.getLogger(__name__)


def _resolve_archive_dir(maintenance: DbMaintenanceConfig) -> str:
    """Resolve the default archive directory from the injected typed configuration.

    The owning process supplies the configuration; this module reads no config
    file. An absent `sqlite_archive_dir` keeps the documented hardcoded fallback.
    """
    if not maintenance.archive_dir:
        return "/opt/llm/db/archive"
    return maintenance.archive_dir


def _archive_db_file(
    db_path: Path,
    archive_dir: str | Path | None,
    *,
    target: str,
    maintenance: DbMaintenanceConfig,
) -> Path:
    """Create a WAL-consistent, verified backup of db_path.

    The SQLite online backup API produces the copy; the archive then passes the
    domain integrity and identity checks before it is returned as a recovery
    point. A failing archive raises and is left in place for forensics
    (verified recovery points).

    `maintenance` supplies the default archive directory when `archive_dir` is
    not given; the caller that owns the configuration builds it.
    """
    if not db_path.exists():
        raise FileNotFoundError(f"DB file not found: {db_path}")

    if archive_dir is None:
        archive_dir = _resolve_archive_dir(maintenance)

    dest_dir = Path(archive_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)

    ts = format_timestamp()
    dest = resolve_unique_path(dest_dir / f"{db_path.stem}_{ts}{db_path.suffix}")

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
    table is defined (rag/session). Unmapped targets (workflow) pass
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


def rotate_session_db(
    db_cfg: DbConfig,
    maintenance: DbMaintenanceConfig,
    archive_dir: str | Path | None = None,
) -> Path:
    """Archive session.sqlite to archive_dir with a timestamp suffix; returns the archive path.

    `db_cfg` and `maintenance` are supplied by the caller that owns the
    configuration; this module reads no config file.
    """
    return _archive_db_file(
        Path(db_cfg.session_db_path),
        archive_dir,
        target="session",
        maintenance=maintenance,
    )


def rotate_workflow_db(
    db_cfg: DbConfig,
    maintenance: DbMaintenanceConfig,
    archive_dir: str | Path | None = None,
) -> Path:
    """Archive workflow.sqlite to archive_dir with a timestamp suffix; returns the archive path.

    `db_cfg` and `maintenance` are supplied by the caller that owns the
    configuration; this module reads no config file.
    """
    return _archive_db_file(
        Path(db_cfg.workflow_db_path),
        archive_dir,
        target="workflow",
        maintenance=maintenance,
    )


def rotate_all_dbs(
    db_cfg: DbConfig,
    maintenance: DbMaintenanceConfig,
    archive_dir: str | Path | None = None,
) -> tuple[Path, Path, Path]:
    """Archive rag, session, and workflow databases.

    Returns (rag_archive_path, session_archive_path, workflow_archive_path).
    eventbus.sqlite is owned by the EventBus service and is archived by
    ``python -m eventbus.db_tools rotate``.

    `db_cfg` and `maintenance` are supplied by the caller that owns the
    configuration; this module reads no config file.
    """
    rag_dest = _archive_db_file(
        Path(db_cfg.rag_db_path), archive_dir, target="rag", maintenance=maintenance
    )
    ses_dest = rotate_session_db(db_cfg, maintenance, archive_dir)
    wf_dest = rotate_workflow_db(db_cfg, maintenance, archive_dir)
    return rag_dest, ses_dest, wf_dest


def rotate_db(
    db_cfg: DbConfig,
    maintenance: DbMaintenanceConfig,
    archive_dir: str | Path | None = None,
) -> tuple[Path, Path]:
    """Archive both rag.sqlite and session.sqlite; returns (rag_archive_path, session_archive_path).

    `db_cfg` and `maintenance` are supplied by the caller that owns the
    configuration; this module reads no config file.
    """
    rag_dest = _archive_db_file(
        Path(db_cfg.rag_db_path), archive_dir, target="rag", maintenance=maintenance
    )
    ses_dest = rotate_session_db(db_cfg, maintenance, archive_dir)
    return rag_dest, ses_dest
