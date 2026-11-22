#!/usr/bin/env python3
"""scripts/db/recovery_drill.py — Recovery drill harness (dbmig001 row 11).

Drills recovery for the three Agent-side persistence domains (rag, session,
workflow). eventbus.sqlite is owned by the EventBus service and is verified by
``python -m eventbus.db_tools verify``. For each domain the harness takes a recovery point through the same
code path as rotation (``rotation._archive_db_file``), restores it into an
isolated copy under a drill directory, measures restore time and the data-loss
window, runs per-domain verification through the helpers exposed by
``db.recovery`` (row 10), and writes one JSON audit artifact per domain.

The live databases are never mutated: the recovery point is a WAL-consistent
SQLite backup-API copy and every check runs against the isolated copy only.

drill tooling.

Configuration ownership: this module resolves no configuration file. The typed
configuration is supplied by the caller; the CLI entry point is the boundary that
owns `config/agent.toml`, so it loads it once and passes the typed objects down
(REQ-004, AC-004). Every function below takes `db_config` and `maintenance`.
"""

from __future__ import annotations

import argparse
import json
import logging
import shutil
import sqlite3
import sys
import time
from pathlib import Path
from typing import Any

from shared.schema_fingerprint import assert_matches

from db.config import DbConfig, build_db_config, format_timestamp, resolve_unique_path
from db.helper import SQLiteHelper
from db.maintenance import DbMaintenanceConfig
from db.rag_consistency import check_rag_consistency
from db.rag_consistency import is_consistent as rag_is_consistent
from db.recovery import run_integrity_check, verify_domain_identity
from db.recovery_classification import DbCondition
from db.rotation import _archive_db_file, _resolve_archive_dir
from db.schema_sql import (
    build_rag_schema_sql,
    build_session_schema_sql,
    build_workflow_schema_sql,
)
from db.session_consistency import (
    check_session_consistency,
)
from db.session_consistency import (
    is_consistent as session_is_consistent,
)
from db.store_protocols import get_embedding_dims

logger = logging.getLogger(__name__)

#: The persistence domains the drill covers, in canonical order.
DOMAINS: tuple[str, ...] = ("rag", "session", "workflow")

#: Exit codes (row 11 contract): 0 all domains passed, 1 any domain failed.
EXIT_OK = 0
EXIT_DRILL_FAILED = 1


def _canonical_ddl(domain: str) -> str:
    """Canonical DDL text for a drill domain, from the shared accessor family."""
    if domain == "workflow":
        return build_workflow_schema_sql()
    dims = get_embedding_dims()
    if domain == "rag":
        return build_rag_schema_sql(dims)
    return build_session_schema_sql(dims)


def _schema_drift_error(domain: str, isolated: Path) -> str | None:
    """Fingerprint the restored copy against the canonical DDL.

    Returns None when the copy matches the current schema, or the fingerprint
    refusal text (which already carries the archive-and-recreate guidance) on
    any shape difference. The copy is opened read-only: nothing is written.
    """
    conn = sqlite3.connect(f"file:{isolated}?mode=ro", uri=True)
    try:
        try:
            assert_matches(conn, _canonical_ddl(domain), label=f"{domain}.sqlite")
        except RuntimeError as exc:
            return str(exc)
        return None
    finally:
        conn.close()


def _verify_rag_session(domain: str, isolated: Path, sqlite_vec_so: str = "") -> dict:
    """Per-domain checks for the recreate-only rag/session domains.

    ``sqlite_vec_so`` is threaded from the loaded DbConfig: the isolated copies
    carry vec0 virtual tables, and a helper without the extension path cannot
    read them (``no such module: vec0``), which the fail-closed logical layer
    would then report as an inconsistency of a healthy database.
    """
    condition, _ = run_integrity_check(isolated, domain)
    identity_ok, _ = verify_domain_identity(isolated, domain)
    verification = {
        "integrity": condition == DbCondition.HEALTHY,
        f"required_table_{domain}": identity_ok,
    }
    if domain == "rag":
        # Fail-closed logical layer (dbmig001 row 11 + ragverify001): an unverified
        # dimension or an inconsistent report fails the domain in the artifact.
        with SQLiteHelper(
            "rag", db_path=str(isolated), sqlite_vec_so=sqlite_vec_so
        ).open() as db:
            report = check_rag_consistency(db)
        verification["rag_consistency"] = bool(
            not report.fk_unverified
            and not report.embedding_unverified
            and not report.schema_unverified
            and rag_is_consistent(report)
        )
    elif domain == "session":
        # Fail-closed logical layer (drillmetrics001): an inconsistent report fails
        # the domain in the artifact. Read-only; no write path is added to the live
        # database.
        with SQLiteHelper(
            "session", db_path=str(isolated), sqlite_vec_so=sqlite_vec_so
        ).open() as db:
            sess_report = check_session_consistency(db)
        verification["session_consistent"] = session_is_consistent(sess_report)
    return verification


def _verify_workflow(isolated: Path) -> dict:
    """Per-domain checks for workflow."""
    with SQLiteHelper("workflow", db_path=str(isolated)).open() as db:
        condition, _ = run_integrity_check(isolated, "workflow")
        tasks = (
            db.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='tasks'"
            ).fetchone()
            is not None
        )
        verification = {
            "integrity": condition == DbCondition.HEALTHY,
            "tasks_table": tasks,
        }
    return verification


def _drill_one_domain(
    domain: str,
    db_config: DbConfig,
    maintenance: DbMaintenanceConfig,
    archive_dir: str,
    drill_dir: str,
) -> dict:
    """Drill a single domain and always return its audit artifact.

    The paths come from the supplied `db_config`; this function reads no
    configuration file. The artifact is written to disk even when a check fails,
    so a drill that hides failures cannot happen. Returns the artifact dict
    (also persisted).
    """
    live_paths = {
        "rag": db_config.rag_db_path,
        "session": db_config.session_db_path,
        "workflow": db_config.workflow_db_path,
    }
    live_path = Path(live_paths[domain])
    drill_start = time.time()
    drill_start_epoch = drill_start

    artifact: dict[str, Any] = {
        "domain": domain,
        "archive_path": None,
        "archive_ts": None,
        "drill_ts": format_timestamp(),
        "drill_start_ts": drill_start_epoch,
        "archive_ts_epoch": None,
        "restore_start_ts": None,
        "restore_end_ts": None,
        "rto_seconds": None,
        "backup_duration_seconds": None,
        "rpo_seconds": None,
        "integrity": None,
        "verification": {},
        "policy": "recreate",  # current-schema-only policy for every domain (compatrm001)
        "error": None,
    }

    # Take the recovery point through the rotation code path (a read-only
    # backup-API copy; the live file is never rewritten).
    try:
        recovery_point = _archive_db_file(
            live_path, archive_dir, target=domain, maintenance=maintenance
        )
    except FileNotFoundError as exc:
        artifact["verification"] = {"missing_source": False}
        artifact["error"] = str(exc)
        logger.error("drill %s: %s", domain, exc)
        _persist_artifact(drill_dir, artifact)
        return artifact
    except (RuntimeError, sqlite3.Error) as exc:
        # Archive-stage failures from rotation (_verify_archive raises
        # RuntimeError; connect/backup raise sqlite3.Error). The artifact is
        # persisted before continuing so the drill never aborts mid-loop.
        artifact["verification"] = {"archive_failed": False}
        artifact["error"] = str(exc)
        logger.error("drill %s: %s", domain, exc)
        _persist_artifact(drill_dir, artifact)
        return artifact

    artifact["archive_path"] = str(recovery_point)
    artifact["archive_ts"] = format_timestamp()
    archive_ts_epoch = time.time()
    artifact["archive_ts_epoch"] = archive_ts_epoch
    backup_duration_seconds = archive_ts_epoch - drill_start_epoch

    # Restore into an isolated copy and verify against that copy only.
    drill_dir_path = Path(drill_dir)
    drill_dir_path.mkdir(parents=True, exist_ok=True)
    isolated = resolve_unique_path(
        drill_dir_path / f"{recovery_point.name}_restored{live_path.suffix}"
    )
    # RTO clock starts before the copy: rto_seconds covers copy + verification.
    started = time.time()
    shutil.copy2(recovery_point, isolated)

    try:
        if domain in ("rag", "session"):
            verification = _verify_rag_session(
                domain, isolated, db_config.sqlite_vec_so
            )
        else:
            verification = _verify_workflow(isolated)
    except (sqlite3.Error, RuntimeError) as exc:
        # RuntimeError: the consistency layer's fingerprint refusal (session
        # scope) is recorded here; the shape gate below names the drift.
        logger.error("drill %s: restore read failed: %s", domain, exc)
        verification = {"integrity": False, "restore_error": False}
    finally:
        restore_end_epoch = time.time()

    artifact["restore_start_ts"] = started
    artifact["restore_end_ts"] = restore_end_epoch
    artifact["rto_seconds"] = round(restore_end_epoch - started, 6)
    artifact["backup_duration_seconds"] = round(backup_duration_seconds, 6)
    # RPO = recovery-point age at the assumed failure time. The assumed-failure
    # event defaults to the moment the restored copy became ready (a documented
    # operational decision): a measurement, not an objective RPO.
    # Non-negative by construction (archive precedes restore completion).
    assumed_failure_ts = restore_end_epoch
    artifact["rpo_seconds"] = round(assumed_failure_ts - archive_ts_epoch, 6)
    artifact["verification"] = verification

    # Shape gate on the restored copy: the archived copy must
    # match the current canonical schema. Any drift — a legacy extra table, a
    # missing table, a column or index difference — is one audited finding via
    # the fingerprint refusal, and the operator follows the archive-and-recreate
    # procedure. The live database is never touched.
    drift_error = _schema_drift_error(domain, isolated)
    verification["schema_matches"] = drift_error is None
    if drift_error is not None:
        artifact["error"] = drift_error

    artifact["integrity"] = bool(verification.get("integrity", False))

    _persist_artifact(drill_dir, artifact)
    # The artifact persists; the isolated working copy and the sidecars
    # verification left behind no longer serve any purpose.
    for candidate in (
        isolated,
        isolated.with_suffix(isolated.suffix + "-wal"),
        isolated.with_suffix(isolated.suffix + "-shm"),
    ):
        candidate.unlink(missing_ok=True)
    return artifact


def _persist_artifact(drill_dir: str, artifact: dict) -> None:
    """Write the artifact JSON to the drill directory (even on failure)."""
    drill_dir_path = Path(drill_dir)
    drill_dir_path.mkdir(parents=True, exist_ok=True)
    artifact_path = resolve_unique_path(
        drill_dir_path / f"{artifact['domain']}_{format_timestamp()}.json"
    )
    artifact_path.write_text(json.dumps(artifact, indent=2), encoding="utf-8")
    logger.info("drill %s artifact written: %s", artifact["domain"], artifact_path)


def run_drill(
    db_config: DbConfig,
    maintenance: DbMaintenanceConfig,
    domain: str = "all",
    archive_dir: str | None = None,
    drill_dir: str | None = None,
) -> bool:
    """Drill one domain (or all) and report pass/fail.

    `db_config` supplies the live database paths and `maintenance` the archive
    directory; an explicit `archive_dir` argument keeps precedence over the
    configured value. This function reads no configuration file.

    Returns True only when every drilled domain passes all checks. Any failed
    domain still has its artifact written before this returns.
    """
    resolved_archive = archive_dir or _resolve_archive_dir(maintenance)
    resolved_drill = drill_dir or f"{resolved_archive}/drills"

    targets = DOMAINS if domain == "all" else (domain,)
    passed_all = True
    for target in targets:
        if target not in DOMAINS:
            raise ValueError(f"unknown domain {target!r}; choose from {DOMAINS}")
        artifact = _drill_one_domain(
            target, db_config, maintenance, resolved_archive, resolved_drill
        )
        ok = bool(artifact.get("integrity")) and all(
            verdict
            for verdict in artifact["verification"].values()
            if verdict is not None
        )
        status = "PASS" if ok else "FAIL"
        logger.info("[drill] %s: %s %s", target, status, artifact["verification"])
        passed_all = passed_all and ok
    return passed_all


def main(
    argv: list[str] | None = None,
    *,
    db_config: DbConfig,
    maintenance: DbMaintenanceConfig,
) -> int:
    """CLI entry point for the recovery drill.

    The typed configurations are supplied by the process that owns the
    configuration file; `main()` reads no configuration file itself.
    """
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(
        description="Recovery drill harness: rotate a recovery point, restore it "
        "into an isolated copy, and verify per-domain.",
    )
    parser.add_argument(
        "--domain",
        choices=list(DOMAINS) + ["all"],
        default="all",
        help="Domain to drill (default: all).",
    )
    parser.add_argument(
        "--archive-dir",
        default=None,
        help="Archive directory (default: the archive directory of the supplied "
        "maintenance configuration, falling back to the documented path when it "
        "is empty).",
    )
    parser.add_argument(
        "--drill-dir",
        default=None,
        help="Drill artifact directory (default: <archive-dir>/drills).",
    )
    args = parser.parse_args(argv)

    passed = run_drill(
        domain=args.domain,
        db_config=db_config,
        maintenance=maintenance,
        archive_dir=args.archive_dir,
        drill_dir=args.drill_dir,
    )
    return EXIT_OK if passed else EXIT_DRILL_FAILED


if __name__ == "__main__":
    # Entry boundary: this process owns config/agent.toml, so it loads it here and
    # passes the typed configuration down. No db/ function performs the load.
    from shared.config_loader import ConfigLoader

    raw = ConfigLoader().load("agent.toml")
    sys.exit(
        main(
            db_config=build_db_config(raw),
            maintenance=DbMaintenanceConfig.from_mapping(raw),
        )
    )
