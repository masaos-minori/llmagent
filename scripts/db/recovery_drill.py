#!/usr/bin/env python3
"""scripts/db/recovery_drill.py — Recovery drill harness (dbmig001 row 11).

Drills recovery for all four persistence domains (rag, session, workflow,
eventbus). For each domain the harness takes a recovery point through the same
code path as rotation (``rotation._archive_db_file``), restores it into an
isolated copy under a drill directory, measures restore time and the data-loss
window, runs per-domain verification through the helpers exposed by
``db.recovery`` (row 10), and writes one JSON audit artifact per domain.

The live databases are never mutated: the recovery point is a WAL-consistent
SQLite backup-API copy and every check runs against the isolated copy only.

REQ-007 drill tooling.
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

from shared.db_migrations import read_ledger
from shared.eventbus_schema_fingerprint import assert_matches

from db.config import build_db_config, format_timestamp
from db.helper import SQLiteHelper
from db.recovery import DbCondition, run_integrity_check, verify_domain_identity
from db.rotation import _archive_db_file, _resolve_archive_dir

logger = logging.getLogger(__name__)

#: The four persistence domains the drill covers, in canonical order.
DOMAINS: tuple[str, ...] = ("rag", "session", "workflow", "eventbus")

#: Domains whose create policy is forward-migration (carry a ledger); the others
#: are recreate-only and record no ledger fields.
MIGRATE_POLICY_DOMAINS: frozenset[str] = frozenset({"workflow", "eventbus"})

#: Exit codes (row 11 contract): 0 all domains passed, 1 any domain failed.
EXIT_OK = 0
EXIT_DRILL_FAILED = 1

_LEDGER_TABLE = "schema_migrations"


def _has_ledger_table(conn: sqlite3.Connection) -> bool:
    """Return True when the ``schema_migrations`` ledger table exists."""
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
        (_LEDGER_TABLE,),
    ).fetchone()
    return row is not None


def _read_ledger_state(conn: sqlite3.Connection) -> dict:
    """Return current_version, ledger presence, and the baseline ledger row.

    The baseline row is the earliest recorded ledger row (the bootstrap/baseline
    stamp). A migrate-policy domain with no ledger table reports
    ``ledger_present=False`` so the caller can treat it as a drill finding.
    """
    try:
        current_version = int(conn.execute("PRAGMA user_version").fetchone()[0])
    except sqlite3.Error:
        current_version = None
    rows = read_ledger(conn)
    present = _has_ledger_table(conn)
    baseline_row = None
    if rows:
        first = rows[0]
        baseline_row = {
            "id": first.id,
            "from_version": first.from_version,
            "to_version": first.to_version,
            "applied_at": first.applied_at,
        }
    return {
        "current_version": current_version,
        "ledger_present": present,
        "baseline_row": baseline_row,
    }


def _verify_rag_session(domain: str, isolated: Path) -> dict:
    """Per-domain checks for the recreate-only rag/session domains."""
    condition, _ = run_integrity_check(isolated, domain)
    identity_ok, _ = verify_domain_identity(isolated, domain)
    return {
        "integrity": condition == DbCondition.HEALTHY,
        f"required_table_{domain}": identity_ok,
    }


def _verify_workflow(isolated: Path) -> tuple[dict, dict]:
    """Per-domain checks for workflow; returns (verification, ledger_state)."""
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
        ledger = _read_ledger_state(db._require_conn())
    return verification, ledger


def _verify_eventbus(isolated: Path) -> tuple[dict, dict]:
    """Per-domain checks for eventbus; returns (verification, ledger_state)."""
    with SQLiteHelper("eventbus", db_path=str(isolated)).open() as db:
        condition, _ = run_integrity_check(isolated, "eventbus")
        try:
            assert_matches(db._require_conn(), label="restored eventbus.sqlite")
            fingerprint_ok = True
        except RuntimeError as exc:
            logger.error("eventbus fingerprint mismatch: %s", exc)
            fingerprint_ok = False
        verification = {
            "integrity": condition == DbCondition.HEALTHY,
            "fingerprint": fingerprint_ok,
        }
        ledger = _read_ledger_state(db._require_conn())
    return verification, ledger


def _drill_one_domain(
    domain: str,
    archive_dir: str,
    drill_dir: str,
) -> dict:
    """Drill a single domain and always return its audit artifact.

    The artifact is written to disk even when a check fails, so a drill that
    hides failures cannot happen. Returns the artifact dict (also persisted).
    """
    cfg = build_db_config()
    live_paths = {
        "rag": cfg.rag_db_path,
        "session": cfg.session_db_path,
        "workflow": cfg.workflow_db_path,
        "eventbus": cfg.eventbus_db_path,
    }
    live_path = Path(live_paths[domain])
    drill_start = time.time()

    artifact: dict[str, Any] = {
        "domain": domain,
        "archive_path": None,
        "archive_ts": None,
        "drill_ts": format_timestamp(),
        "rto_seconds": None,
        "rpo_window_seconds": None,
        "integrity": None,
        "verification": {},
        "policy": "migrate" if domain in MIGRATE_POLICY_DOMAINS else "recreate",
        "error": None,
    }
    if domain in MIGRATE_POLICY_DOMAINS:
        artifact["ledger"] = {"current_version": None, "baseline_row": None}

    # Take the recovery point through the rotation code path (a read-only
    # backup-API copy; the live file is never rewritten).
    try:
        recovery_point = _archive_db_file(live_path, archive_dir, target=domain)
    except FileNotFoundError as exc:
        artifact["verification"] = {"missing_source": False}
        artifact["error"] = str(exc)
        logger.error("drill %s: %s", domain, exc)
        _persist_artifact(drill_dir, artifact)
        return artifact

    artifact["archive_path"] = str(recovery_point)
    artifact["archive_ts"] = format_timestamp()
    rpo_window = time.time() - drill_start

    # Restore into an isolated copy and verify against that copy only.
    drill_dir_path = Path(drill_dir)
    drill_dir_path.mkdir(parents=True, exist_ok=True)
    isolated = drill_dir_path / f"{recovery_point.name}_restored{live_path.suffix}"
    shutil.copy2(recovery_point, isolated)

    started = time.time()
    ledger: dict | None = None
    try:
        if domain in ("rag", "session"):
            verification = _verify_rag_session(domain, isolated)
        elif domain == "workflow":
            verification, ledger = _verify_workflow(isolated)
        else:
            verification, ledger = _verify_eventbus(isolated)
    except sqlite3.Error as exc:
        logger.error("drill %s: restore read failed: %s", domain, exc)
        verification = {"integrity": False, "restore_error": False}
        ledger = {
            "current_version": None,
            "baseline_row": None,
            "ledger_present": False,
        }
    finally:
        rto = time.time() - started

    artifact["rto_seconds"] = round(rto, 6)
    artifact["rpo_window_seconds"] = round(rpo_window, 6)
    artifact["verification"] = verification
    if ledger is not None:
        artifact["ledger"] = {
            "current_version": ledger["current_version"],
            "baseline_row": ledger["baseline_row"],
            "ledger_present": ledger["ledger_present"],
        }
    artifact["integrity"] = bool(verification.get("integrity", False))

    # A missing ledger table in a migrate-policy domain is itself a finding.
    if (
        domain in MIGRATE_POLICY_DOMAINS
        and ledger is not None
        and not ledger["ledger_present"]
    ):
        artifact["verification"]["ledger_present"] = False

    _persist_artifact(drill_dir, artifact)
    return artifact


def _last_archive(archive_dir: str, stem: str) -> Path:
    """Return the most recent archived file for ``stem`` in ``archive_dir``.

    ``_archive_db_file`` names each copy ``<stem>_<timestamp>.<ext>``; the newest
    is the latest recovery point. Returns a non-existent path when none exists so
    the caller records a missing-source finding instead of crashing.
    """
    dest_dir = Path(archive_dir)
    candidates = [
        child
        for child in dest_dir.glob(f"{stem}_*.sqlite*")
        if child.is_file() and child.name.startswith(f"{stem}_")
    ]
    if not candidates:
        return dest_dir / f"{stem}_none.sqlite"
    return max(candidates, key=lambda p: p.stat().st_mtime)


def _persist_artifact(drill_dir: str, artifact: dict) -> None:
    """Write the artifact JSON to the drill directory (even on failure)."""
    drill_dir_path = Path(drill_dir)
    drill_dir_path.mkdir(parents=True, exist_ok=True)
    artifact_path = drill_dir_path / f"{artifact['domain']}_{format_timestamp()}.json"
    artifact_path.write_text(json.dumps(artifact, indent=2), encoding="utf-8")
    logger.info("drill %s artifact written: %s", artifact["domain"], artifact_path)


def run_drill(
    domain: str = "all",
    archive_dir: str | None = None,
    drill_dir: str | None = None,
) -> bool:
    """Drill one domain (or all) and report pass/fail.

    Returns True only when every drilled domain passes all checks. Any failed
    domain still has its artifact written before this returns.
    """
    resolved_archive = archive_dir or _resolve_archive_dir()
    resolved_drill = drill_dir or f"{resolved_archive}/drills"

    targets = DOMAINS if domain == "all" else (domain,)
    passed_all = True
    for target in targets:
        if target not in DOMAINS:
            raise ValueError(f"unknown domain {target!r}; choose from {DOMAINS}")
        artifact = _drill_one_domain(target, resolved_archive, resolved_drill)
        ok = bool(artifact.get("integrity")) and all(
            verdict for verdict in artifact["verification"].values()
        )
        status = "PASS" if ok else "FAIL"
        print(f"[drill] {target}: {status} {artifact['verification']}")
        passed_all = passed_all and ok
    return passed_all


def main(argv: list[str] | None = None) -> int:
    """CLI entry point for the recovery drill."""
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
        help="Archive directory (default: rotation._resolve_archive_dir).",
    )
    parser.add_argument(
        "--drill-dir",
        default=None,
        help="Drill artifact directory (default: <archive-dir>/drills).",
    )
    args = parser.parse_args(argv)

    passed = run_drill(
        domain=args.domain,
        archive_dir=args.archive_dir,
        drill_dir=args.drill_dir,
    )
    return EXIT_OK if passed else EXIT_DRILL_FAILED


if __name__ == "__main__":
    sys.exit(main())
