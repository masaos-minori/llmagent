#!/usr/bin/env python3
"""scripts/mcp_servers/mdq/health_check.py — Health check logic for mdq-mcp server.

check_health() reads the shared startup-configuration result instead of loading configuration
itself, and publishes the Security Posture mdq_security_validation builds. The ordinary health
body carries only non-sensitive state: the service name, the size of the authorized-root list,
and the deny-all flag. Dependency values are reason codes from the closed health vocabulary, so
a health response holds no absolute database path, no database-wide count, no database-wide
timestamp, and no configuration path (REQ-003).

Dependency direction: health_check → models, security_validation, startup_config
Import from here:  from mcp_servers.mdq.health_check import check_health
"""

from __future__ import annotations

import sqlite3
from collections.abc import Mapping
from pathlib import Path

from db.helper import apply_connection_pragmas
from fastapi.responses import JSONResponse
from shared.mcp_health_contract import (
    CAPABILITY_STATE_OK,
    CAPABILITY_STATE_UNAVAILABLE,
    HEALTH_REASON_SERVER_UNAVAILABLE,
    CapabilityState,
)
from shared.security.posture_contract import SecurityPosture

from mcp_servers.health_response import make_health_response
from mcp_servers.mdq.mdq_models import STALE_SQL_CONDITION
from mcp_servers.mdq.mdq_security_validation import (
    build_mdq_posture,
    configured_allowed_dirs,
)
from mcp_servers.mdq.startup_config import StartupConfig

# The capability the tool catalog names for mdq (`config/tool_catalog.toml`), so the state the
# server reports is the state the Agent reads.
MDQ_CAPABILITY = "mdq.corpus"

# The seven-value shape `build_mdq_posture()` and the health body share: the dependency result,
# the non-sensitive details, the startup result, and the four probe facts the posture consumes.
HealthProbe = tuple[
    dict[str, str],
    dict[str, object],
    StartupConfig,
    bool,
    tuple[str, str] | None,
    bool,
    Mapping[str, object] | None,
]


def _corpus_capability(deps: Mapping[str, str]) -> dict[str, CapabilityState]:
    """The corpus capability state, read from the same dependency result the body reports.

    A dependency failure means the corpus cannot be served, so the state is `unavailable` with
    the availability reason code; with no failure the state is `ok`. Only the closed state and
    reason vocabularies are used, and no path or count is carried.
    """
    if HEALTH_REASON_SERVER_UNAVAILABLE in set(deps.values()):
        return {
            MDQ_CAPABILITY: CapabilityState(
                CAPABILITY_STATE_UNAVAILABLE, HEALTH_REASON_SERVER_UNAVAILABLE
            )
        }
    return {MDQ_CAPABILITY: CapabilityState(CAPABILITY_STATE_OK)}


def _health_response(
    deps: Mapping[str, str],
    details: Mapping[str, object],
    posture: SecurityPosture,
) -> JSONResponse:
    """Build the health body from the dependency result, the non-sensitive details, and the posture."""
    capabilities = _corpus_capability(deps)
    reasons = [
        state.reason_code
        for state in capabilities.values()
        if state.reason_code is not None
    ]
    result: JSONResponse = make_health_response(
        dict(deps),
        dict(details),
        security=posture,
        capabilities=capabilities,
        degraded_reasons=reasons,
    )
    return result


def _check_stale_documents(conn: sqlite3.Connection) -> int | None:
    """Check for documents with mtime_ns > indexed_at."""
    try:
        result = conn.execute(
            f"SELECT COUNT(*) as cnt FROM documents WHERE {STALE_SQL_CONDITION}"  # nosec B608 — STALE_SQL_CONDITION is a fixed string constant
        ).fetchone()
        return result["cnt"] if result is not None else 0
    except sqlite3.OperationalError:
        return None


def _check_schema_health(conn: sqlite3.Connection) -> tuple[str, str] | None:
    """Verify required tables, triggers, and FTS5 query health.

    Returns a `(dependency_key, reason_code)` pair describing the failure, or `None` when the
    schema and the FTS5 index are healthy. The reason code replaces the message that carried the
    database path (REQ-003); the dependency key stays so the posture names which part failed.
    """
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = {row[0] for row in cursor.fetchall()}

    if "documents" not in tables:
        return "db_schema", HEALTH_REASON_SERVER_UNAVAILABLE
    if "chunks" not in tables:
        return "db_schema", HEALTH_REASON_SERVER_UNAVAILABLE
    if "chunks_fts" not in tables:
        return "db_schema", HEALTH_REASON_SERVER_UNAVAILABLE

    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='trigger'")
    triggers = {row[0] for row in cursor.fetchall()}
    missing_triggers = {"chunks_ai", "chunks_ad", "chunks_au"} - triggers
    if missing_triggers:
        return "db_schema", HEALTH_REASON_SERVER_UNAVAILABLE

    try:
        cursor.execute(
            "SELECT COUNT(*) FROM chunks_fts WHERE chunks_fts = 'delete' LIMIT 1"
        )
        cursor.fetchone()
    except sqlite3.OperationalError:
        return "fts5", HEALTH_REASON_SERVER_UNAVAILABLE

    return None


def _collect_index_stats(conn: sqlite3.Connection) -> dict[str, object]:
    """Gather the index state the posture judges.

    The counts are the input to the posture's index check only. They are not written to the
    health body, because the ordinary health body reports state codes rather than database-wide
    counts (REQ-003).
    """
    chunk_count = conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
    doc_count = conn.execute(
        "SELECT COUNT(DISTINCT source_path) FROM documents"
    ).fetchone()[0]
    fts_count = conn.execute(
        "SELECT COUNT(*) FROM chunks_fts WHERE chunks_fts != 'delete'"
    ).fetchone()[0]

    return {
        "document_count": doc_count,
        "chunk_count": chunk_count,
        "fts_row_count": fts_count,
        "stale_document_count": _check_stale_documents(conn),
    }


def _collect_dependencies(startup: StartupConfig) -> HealthProbe:
    """Probe the database against the shared startup result for health and the posture.

    Shared by `check_health()` (the /health endpoint) and the import-time security-posture build
    in `mdq_server.py`. Returns `(deps, details, startup, db_file_present, schema_error,
    schema_checked, index_stats)`. The trailing four values plus the result are the contract
    `build_mdq_posture()` consumes; `deps` and `details` are returned alongside so the /health
    body can be composed by the caller.

    No configuration is read here: a missing production configuration is a pre-bind failure
    (AC-6), so no configuration dependency remains for a health request to report. `deps` values
    are reason codes, and `details` carries only non-sensitive state.
    """
    deps: dict[str, str] = {}
    details: dict[str, object] = {"service": "mdq-mcp"}

    allowed_dirs = configured_allowed_dirs(startup)
    details["allowed_dirs_count"] = len(allowed_dirs)
    details["deny_all"] = len(allowed_dirs) == 0

    db_file_present = Path(startup.db_path).is_file()
    if not db_file_present:
        deps["db_file"] = HEALTH_REASON_SERVER_UNAVAILABLE
        return (deps, details, startup, False, None, False, None)

    schema_error: tuple[str, str] | None = None
    schema_checked = False
    index_stats: Mapping[str, object] | None = None
    conn = sqlite3.connect(startup.db_path)
    conn.row_factory = sqlite3.Row
    apply_connection_pragmas(conn, write_mode=False)
    try:
        schema_error = _check_schema_health(conn)
        schema_checked = True
        if schema_error is not None:
            deps[schema_error[0]] = schema_error[1]
        else:
            index_stats = _collect_index_stats(conn)
    finally:
        conn.close()

    return (
        deps,
        details,
        startup,
        db_file_present,
        schema_error,
        schema_checked,
        index_stats,
    )


def check_health(
    startup: StartupConfig, extra_details: Mapping[str, object] | None = None
) -> JSONResponse:
    """Check mdq-mcp health and return the response for the shared result it is given.

    `extra_details` is the caller's non-sensitive addition to the details block, such as the
    read-only dedup metrics the server merges in, so the body stays composed in one place.
    """
    (
        deps,
        details,
        startup,
        db_file_present,
        schema_error,
        schema_checked,
        index_stats,
    ) = _collect_dependencies(startup)
    if extra_details:
        details.update(dict(extra_details))
    posture = build_mdq_posture(
        startup, db_file_present, schema_error, schema_checked, index_stats
    )
    return _health_response(deps, details, posture)
