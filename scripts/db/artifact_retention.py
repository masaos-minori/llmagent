#!/usr/bin/env python3
"""scripts/db/artifact_retention.py — Bounded retention sweeps for non-corrupt DB artifacts.

Owns the four sweeps that keep the archive tree bounded: rotation archives,
drill JSON audit artifacts, recovery sidecar-quarantine directories, and stale
restore/drill working files (age rule then count rule per source database,
most-recent protected). The corrupt-archive contract stays in db.maintenance
(`purge_corrupt_archives`); this module is its sibling for the remaining
artifact classes.

ADR-008 recovery policy; Plan 008 artifact retention.
"""

import logging
import re
import shutil
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

from db.config import build_db_config
from db.maintenance import (
    MaintenanceMode,
    MaintenanceResult,
    _handle_maintenance_error,
    _load_agent_config,
    _non_negative_int,
    _retention_guard,
)
from db.rotation import _resolve_archive_dir

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ArtifactRetentionConfig:
    """Retention policy for the non-corrupt artifact classes swept by
    purge_archive_artifacts(): rotation archives, drill JSON artifacts, and
    recovery sidecar-quarantine directories; max_files keeps the most-recent N
    artifacts per source database; max_age_days deletes artifacts older than N days.

    Semantics: 0 disables the corresponding rule (deletes nothing); negative
    values are rejected with ValueError at config load and in the sweep helpers.
    """

    archive_max_files: int = 14
    archive_max_age_days: int = 30
    drill_artifact_max_files: int = 14
    drill_artifact_max_age_days: int = 30
    quarantine_max_files: int = 10
    quarantine_max_age_days: int = 90

    @classmethod
    def from_config(cls) -> "ArtifactRetentionConfig":
        """Construct from agent.toml values; raises on config load failure.

        Wrong-typed or negative values raise a key-naming ValueError.
        """
        cfg = _load_agent_config()
        return cls(
            archive_max_files=_non_negative_int(cfg, "sqlite_archive_max_files", 14),
            archive_max_age_days=_non_negative_int(
                cfg, "sqlite_archive_max_age_days", 30
            ),
            drill_artifact_max_files=_non_negative_int(
                cfg, "sqlite_drill_artifact_max_files", 14
            ),
            drill_artifact_max_age_days=_non_negative_int(
                cfg, "sqlite_drill_artifact_max_age_days", 30
            ),
            quarantine_max_files=_non_negative_int(
                cfg, "sqlite_quarantine_max_files", 10
            ),
            quarantine_max_age_days=_non_negative_int(
                cfg, "sqlite_quarantine_max_age_days", 90
            ),
        )


# ── Artifact retention sweeps (purge_archive_artifacts) ────────────────────────

#: Stale drill/restore working files older than this many seconds are swept.
_STALE_WORK_FILE_MAX_AGE_SECONDS = 86400


def _delete_candidates_by_age(
    candidates: Sequence[Path],
    max_age_days: int,
    key: str,
    min_keep: int,
    delete: Callable[[Path], None],
) -> int:
    """Delete candidates older than max_age_days, newest-first order, never the
    newest `min_keep` ones; returns count deleted (0 if disabled).

    `max_age_days == 0` disables the rule; a negative value raises ValueError.
    """
    if _retention_guard(max_age_days, key):
        return 0
    threshold = time.time() - max_age_days * 86400
    ordered = sorted(candidates, key=lambda p: p.stat().st_mtime, reverse=True)
    deleted = 0
    for path in ordered[min_keep:]:
        if path.stat().st_mtime < threshold:
            delete(path)
            deleted += 1
    return deleted


def _delete_candidates_beyond_limit(
    candidates: Sequence[Path],
    max_files: int,
    key: str,
    delete: Callable[[Path], None],
) -> int:
    """Delete candidates beyond the max_files most-recent limit; returns count
    deleted.

    `max_files == 0` disables the rule; a negative value raises ValueError.
    """
    if _retention_guard(max_files, key):
        return 0
    ordered = sorted(candidates, key=lambda p: p.stat().st_mtime, reverse=True)
    if len(ordered) <= max_files:
        return 0
    deleted = 0
    for path in ordered[max_files:]:
        delete(path)
        deleted += 1
    return deleted


def _unlink_candidate(path: Path) -> None:
    """Delete one file candidate."""
    path.unlink()


def _rmtree_candidate(path: Path) -> None:
    """Delete one directory candidate (caller has verified name and is_dir)."""
    shutil.rmtree(path)


def _sweep_rotation_archives(
    archive_dir: Path,
    db_path: Path,
    cfg: ArtifactRetentionConfig,
) -> tuple[int, int]:
    """Age-then-count sweep of one source database's rotation archives;
    returns (age_deleted, count_deleted).

    `{stem}_corrupt_*` names are excluded as a safety guard: corrupt archives
    live in the DB directory and belong to purge_corrupt_archives. The newest
    archive survives the age rule even when older than the age limit. Each
    rule globs fresh so a count rule never sees a path the age rule deleted.
    """

    def candidates() -> list[Path]:
        return [
            path
            for path in archive_dir.glob(f"{db_path.stem}_*{db_path.suffix}")
            if not path.name.startswith(f"{db_path.stem}_corrupt_")
        ]

    age_deleted = _delete_candidates_by_age(
        candidates(),
        cfg.archive_max_age_days,
        "sqlite_archive_max_age_days",
        1,
        _unlink_candidate,
    )
    count_deleted = _delete_candidates_beyond_limit(
        candidates(),
        cfg.archive_max_files,
        "sqlite_archive_max_files",
        _unlink_candidate,
    )
    if age_deleted or count_deleted:
        logger.info(
            "Retention: removed %s archives older than %s days and %s beyond limit of %s (%s)",
            age_deleted,
            cfg.archive_max_age_days,
            count_deleted,
            cfg.archive_max_files,
            db_path.stem,
        )
    return age_deleted, count_deleted


def _sweep_drill_artifacts(
    drill_dir: Path,
    db_path: Path,
    cfg: ArtifactRetentionConfig,
) -> tuple[int, int]:
    """Age-then-count sweep of one domain's drill JSON audit artifacts in the
    drills directory; returns (age_deleted, count_deleted).

    The count rule protects the most-recent artifacts; the age rule has no
    min_keep guard here (maintainer decision: drill JSONs are pure history,
    unlike the archives and quarantine directories).
    """

    def candidates() -> list[Path]:
        return list(drill_dir.glob(f"{db_path.stem}_*.json"))

    age_deleted = _delete_candidates_by_age(
        candidates(),
        cfg.drill_artifact_max_age_days,
        "sqlite_drill_artifact_max_age_days",
        0,
        _unlink_candidate,
    )
    count_deleted = _delete_candidates_beyond_limit(
        candidates(),
        cfg.drill_artifact_max_files,
        "sqlite_drill_artifact_max_files",
        _unlink_candidate,
    )
    if age_deleted or count_deleted:
        logger.info(
            "Retention: removed %s drill artifacts older than %s days and %s beyond limit of %s (%s)",
            age_deleted,
            cfg.drill_artifact_max_age_days,
            count_deleted,
            cfg.drill_artifact_max_files,
            db_path.stem,
        )
    return age_deleted, count_deleted


def _sweep_quarantine_dirs(
    db_dir: Path,
    db_path: Path,
    cfg: ArtifactRetentionConfig,
) -> tuple[int, int]:
    """Age-then-count sweep of one source database's sidecar-quarantine
    directories; returns (age_deleted, count_deleted).

    Security guard: a directory is rmtree'd only when its full name matches
    `{stem}_sidecar_quarantine_{digits/underscores}` and it is a directory;
    anything else in the DB directory is untouched. The newest quarantine
    survives the age rule even when older than the age limit.
    """
    name_pattern = re.compile(
        rf"^{re.escape(db_path.stem)}_sidecar_quarantine_[0-9_]*$"
    )

    def candidates() -> list[Path]:
        return [
            path
            for path in db_dir.iterdir()
            if path.is_dir() and name_pattern.fullmatch(path.name)
        ]

    age_deleted = _delete_candidates_by_age(
        candidates(),
        cfg.quarantine_max_age_days,
        "sqlite_quarantine_max_age_days",
        1,
        _rmtree_candidate,
    )
    count_deleted = _delete_candidates_beyond_limit(
        candidates(),
        cfg.quarantine_max_files,
        "sqlite_quarantine_max_files",
        _rmtree_candidate,
    )
    if age_deleted or count_deleted:
        logger.info(
            "Retention: removed %s quarantine dirs older than %s days and %s beyond limit of %s (%s)",
            age_deleted,
            cfg.quarantine_max_age_days,
            count_deleted,
            cfg.quarantine_max_files,
            db_path.stem,
        )
    return age_deleted, count_deleted


def _sweep_stale_work_files(
    db_dir: Path,
    drill_dir: Path,
    db_path: Path,
) -> int:
    """Remove stale restore/drill working files older than
    _STALE_WORK_FILE_MAX_AGE_SECONDS; returns count removed.

    Backstop for crashed runs only: a completed drill unlinks its `_restored`
    copy itself, and `_stage_restore` consumes `.tmp_` files. Younger files
    belong to a possibly-running recovery and are never touched.
    """
    threshold = time.time() - _STALE_WORK_FILE_MAX_AGE_SECONDS
    candidates = list(db_dir.glob(f"{db_path.stem}.tmp_*{db_path.suffix}"))
    candidates += list(drill_dir.glob(f"*_restored{db_path.suffix}"))
    removed = 0
    for path in candidates:
        if path.stat().st_mtime < threshold:
            path.unlink()
            removed += 1
    if removed:
        logger.info(
            "Retention: removed %s stale work files older than %s seconds",
            removed,
            _STALE_WORK_FILE_MAX_AGE_SECONDS,
        )
    return removed


def purge_archive_artifacts(
    cfg: ArtifactRetentionConfig | None = None,
    mode: MaintenanceMode = MaintenanceMode.STRICT,
) -> MaintenanceResult:
    """Sweep the non-corrupt artifact classes: rotation archives, drill JSON
    artifacts, sidecar-quarantine directories, and stale restore/drill working
    files (age-based then count-based, applied independently per source
    database, with the most-recent artifact never deleted by the count rule).

    In STRICT mode (default), raises on filesystem errors.
    In BEST_EFFORT mode, returns MaintenanceResult with partial counts on error.
    Config-load failures (`ArtifactRetentionConfig.from_config`,
    `build_db_config`) propagate in both modes, as do negative-retention
    `ValueError`s raised by the sweep helpers.
    """
    if cfg is None:
        cfg = ArtifactRetentionConfig.from_config()

    counts: dict[str, dict[str, int]] = {
        "archives": {"age_deleted": 0, "count_deleted": 0},
        "drill_artifacts": {"age_deleted": 0, "count_deleted": 0},
        "quarantine": {"age_deleted": 0, "count_deleted": 0},
        "stale_work": {"removed": 0},
    }

    try:
        db_cfg = build_db_config()
        archive_dir = Path(_resolve_archive_dir())
        drill_dir = archive_dir / "drills"
        for raw_path in (
            db_cfg.rag_db_path,
            db_cfg.session_db_path,
            db_cfg.workflow_db_path,
        ):
            db_path = Path(raw_path)
            age_deleted, count_deleted = _sweep_rotation_archives(
                archive_dir, db_path, cfg
            )
            counts["archives"]["age_deleted"] += age_deleted
            counts["archives"]["count_deleted"] += count_deleted

            age_deleted, count_deleted = _sweep_drill_artifacts(drill_dir, db_path, cfg)
            counts["drill_artifacts"]["age_deleted"] += age_deleted
            counts["drill_artifacts"]["count_deleted"] += count_deleted

            age_deleted, count_deleted = _sweep_quarantine_dirs(
                db_path.parent, db_path, cfg
            )
            counts["quarantine"]["age_deleted"] += age_deleted
            counts["quarantine"]["count_deleted"] += count_deleted

            counts["stale_work"]["removed"] += _sweep_stale_work_files(
                db_path.parent, drill_dir, db_path
            )

        return MaintenanceResult(
            success=True,
            action="purge_archive_artifacts",
            mode=mode,
            data=counts,
        )
    except OSError as e:
        return _handle_maintenance_error(
            e,
            "purge_archive_artifacts",
            mode,
            extra_data=counts,
        )
