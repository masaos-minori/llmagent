#!/usr/bin/env python3
"""scripts/mcp_servers/mdq/mdq_security_validation.py

MDQ's own security self-validation — validate_mdq_security() reports mdq-mcp's configuration as
SecurityCheckResult values, _mdq_config_view() builds the non-secret view the posture fingerprint
is hashed from, and build_mdq_posture() runs the common stage plus these checks.

Dependency direction: mdq_security_validation → mdq_tools
Import from here:  from mcp_servers.mdq.mdq_security_validation import build_mdq_posture
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from shared.security.posture_contract import SecurityPosture
from shared.security.result_dto import (
    REASON_ALLOWED_DIR_INVALID,
    REASON_ALLOWLIST_EMPTY,
    REASON_AUTH_TOKEN_MISSING,
    REASON_DB_PATH_INVALID,
    REASON_DEPENDENCY_UNREACHABLE,
    REASON_NOT_APPLICABLE,
    REASON_OK,
    SecurityCheckResult,
    SecurityCheckStatus,
)
from shared.security.startup_flow import (
    OWN_CONFIG_FILE_VIEW_KEY,
    run_startup_validation,
)

from mcp_servers.mdq.mdq_tools import TOOL_LIST

MDQ_SERVER_KEY = "mdq"
MDQ_OWN_CONFIG_FILE = "mdq_mcp_server.toml"


_MDQ_SCALAR_SETTINGS: tuple[str, ...] = (
    "max_snippet_chars",
    "max_chunk_chars",
    "max_file_chars",
    "max_results_limit",
    "max_chars_per_chunk",
    "max_total_result_chars",
    "max_outline_items",
    "max_grep_matches",
    "search_timeout_sec",
)


def configured_allowed_dirs(mdq_cfg: Mapping[str, object]) -> list[object]:
    """The configured allowed directories as a list: empty when absent or not a list.

    check_health() reports the count and validate_mdq_security() judges the entries, so both read
    the same narrowed value.
    """
    value = mdq_cfg.get("allowed_dirs")
    if isinstance(value, (list, tuple)):
        return list(value)
    return []


def _count(stats: Mapping[str, object], key: str) -> int:
    """A row count from the index stats: zero when the key is absent or not a number."""
    value = stats.get(key)
    return int(value) if isinstance(value, (int, float)) else 0


def _mdq_config_view(mdq_cfg: Mapping[str, object]) -> dict[str, object]:
    """Build the non-secret view the posture fingerprint is computed from.

    db_path and the allowed directories are sensitive paths, and compute_config_fingerprint()
    rejects an absolute path, so the view carries their state (present, count) instead of their
    values. auth_token is never carried by value.
    """
    allowed_dirs = configured_allowed_dirs(mdq_cfg)
    view: dict[str, object] = {
        OWN_CONFIG_FILE_VIEW_KEY: MDQ_OWN_CONFIG_FILE,
        "auth_token_present": bool(mdq_cfg.get("auth_token")),
        "db_path_present": bool(mdq_cfg.get("db_path")),
        "allowed_dirs_count": len(allowed_dirs),
        "enable_grep": bool(mdq_cfg.get("enable_grep", True)),
    }
    for key in _MDQ_SCALAR_SETTINGS:
        value = mdq_cfg.get(key)
        if isinstance(value, (bool, int, float)):
            view[key] = value
    return view


def validate_mdq_security(
    mdq_cfg: Mapping[str, object],
    *,
    db_file_present: bool,
    schema_error: tuple[str, str] | None,
    schema_checked: bool,
    index_stats: Mapping[str, object] | None,
) -> list[SecurityCheckResult]:
    """MDQ's own configuration checks, in the order the posture contract expects.

    The verdicts are the ones check_health() already computed, so the deps channel and the posture
    channel report the same facts and cannot disagree. No check reads a token value, and no message
    carries a database or directory path.
    """
    return [
        _auth_token_check(mdq_cfg),
        _allowed_dirs_configured_check(mdq_cfg),
        _allowed_dirs_exist_check(mdq_cfg),
        _db_path_check(mdq_cfg, db_file_present),
        _schema_check(schema_error, schema_checked),
        _index_check(index_stats),
    ]


def _auth_token_check(mdq_cfg: Mapping[str, object]) -> SecurityCheckResult:
    """Presence only: mdq_server.py already refuses to start without a token."""
    if mdq_cfg.get("auth_token"):
        return SecurityCheckResult(
            check_id="server.auth_token_configured",
            status=SecurityCheckStatus.OK,
            reason_code=REASON_OK,
            message="auth_token is configured",
        )
    return SecurityCheckResult(
        check_id="server.auth_token_configured",
        status=SecurityCheckStatus.FAILED,
        reason_code=REASON_AUTH_TOKEN_MISSING,
        message="auth_token is empty",
    )


def _allowed_dirs_configured_check(
    mdq_cfg: Mapping[str, object],
) -> SecurityCheckResult:
    """A deny-all mdq-mcp can serve no document, so it is not Ready."""
    allowed_dirs = configured_allowed_dirs(mdq_cfg)
    if not allowed_dirs:
        return SecurityCheckResult(
            check_id="server.allowed_dirs_configured",
            status=SecurityCheckStatus.FAILED,
            reason_code=REASON_ALLOWLIST_EMPTY,
            message="allowed_dirs is empty so no document can be served",
        )
    return SecurityCheckResult(
        check_id="server.allowed_dirs_configured",
        status=SecurityCheckStatus.OK,
        reason_code=REASON_OK,
        message=f"allowed_dirs has {len(allowed_dirs)} entry(ies)",
    )


def _allowed_dirs_exist_check(mdq_cfg: Mapping[str, object]) -> SecurityCheckResult:
    """A configured directory that does not exist authorizes nothing."""
    allowed_dirs = configured_allowed_dirs(mdq_cfg)
    if not allowed_dirs:
        return SecurityCheckResult(
            check_id="server.allowed_dirs_exist",
            status=SecurityCheckStatus.NOT_APPLICABLE,
            reason_code=REASON_NOT_APPLICABLE,
            message="allowed_dirs is empty so there is no entry to resolve",
        )
    invalid = sum(
        1 for entry in allowed_dirs if not str(entry) or not Path(str(entry)).is_dir()
    )
    if invalid:
        return SecurityCheckResult(
            check_id="server.allowed_dirs_exist",
            status=SecurityCheckStatus.FAILED,
            reason_code=REASON_ALLOWED_DIR_INVALID,
            message=f"{invalid} allowed_dirs entry is not an existing directory",
        )
    return SecurityCheckResult(
        check_id="server.allowed_dirs_exist",
        status=SecurityCheckStatus.OK,
        reason_code=REASON_OK,
        message="every allowed_dirs entry is an existing directory",
    )


def _db_path_check(
    mdq_cfg: Mapping[str, object], db_file_present: bool
) -> SecurityCheckResult:
    """Mirrors the existing db_file dependency entry without repeating the path."""
    if not mdq_cfg.get("db_path"):
        return SecurityCheckResult(
            check_id="server.db_path_valid",
            status=SecurityCheckStatus.FAILED,
            reason_code=REASON_DB_PATH_INVALID,
            message="db_path is not configured",
        )
    if not db_file_present:
        return SecurityCheckResult(
            check_id="server.db_path_valid",
            status=SecurityCheckStatus.FAILED,
            reason_code=REASON_DB_PATH_INVALID,
            message="db file not found",
        )
    return SecurityCheckResult(
        check_id="server.db_path_valid",
        status=SecurityCheckStatus.OK,
        reason_code=REASON_OK,
        message="db file exists",
    )


def _schema_check(
    schema_error: tuple[str, str] | None, schema_checked: bool
) -> SecurityCheckResult:
    """Reports the existing _check_schema_health() verdict by dependency key, never by message."""
    if not schema_checked:
        return SecurityCheckResult(
            check_id="server.schema_valid",
            status=SecurityCheckStatus.NOT_APPLICABLE,
            reason_code=REASON_NOT_APPLICABLE,
            message="schema check did not run because the db file is unavailable",
        )
    if schema_error is not None:
        return SecurityCheckResult(
            check_id="server.schema_valid",
            status=SecurityCheckStatus.FAILED,
            reason_code=REASON_DEPENDENCY_UNREACHABLE,
            message=f"schema check failed: {schema_error[0]}",
        )
    return SecurityCheckResult(
        check_id="server.schema_valid",
        status=SecurityCheckStatus.OK,
        reason_code=REASON_OK,
        message="schema tables, triggers, and the FTS5 query are healthy",
    )


def _index_check(index_stats: Mapping[str, object] | None) -> SecurityCheckResult:
    """Documents with no FTS rows is a data-consistency finding, not a policy violation."""
    if index_stats is None:
        return SecurityCheckResult(
            check_id="server.index_available",
            status=SecurityCheckStatus.NOT_APPLICABLE,
            reason_code=REASON_NOT_APPLICABLE,
            message="index stats were not collected",
        )
    fts_count = _count(index_stats, "fts_row_count")
    doc_count = _count(index_stats, "document_count")
    chunk_count = _count(index_stats, "chunk_count")
    if fts_count == 0 and (doc_count > 0 or chunk_count > 0):
        return SecurityCheckResult(
            check_id="server.index_available",
            status=SecurityCheckStatus.WARNING,
            reason_code=REASON_DEPENDENCY_UNREACHABLE,
            message="documents exist while the FTS index holds no rows",
        )
    return SecurityCheckResult(
        check_id="server.index_available",
        status=SecurityCheckStatus.OK,
        reason_code=REASON_OK,
        message=f"FTS index holds {fts_count} row(s)",
    )


def build_mdq_posture(
    mdq_cfg: Mapping[str, object],
    db_file_present: bool,
    schema_error: tuple[str, str] | None,
    schema_checked: bool,
    index_stats: Mapping[str, object] | None,
) -> SecurityPosture:
    """Run the common stage plus mdq's own checks and return the posture to publish.

    The flow never raises, so a validation problem still produces a posture the Agent can read.
    Only the server-security stage is supplied: the common stage supplies the shared checks the
    Agent-side validator requires, and mdq has no schema-migration or dependency-install stage.
    """
    return run_startup_validation(
        MDQ_SERVER_KEY,
        own_config_file=MDQ_OWN_CONFIG_FILE,
        config_view=_mdq_config_view(mdq_cfg),
        auth_token=str(mdq_cfg.get("auth_token") or ""),
        declared_tools=tuple(tool["name"] for tool in TOOL_LIST),
        server_checks=lambda: validate_mdq_security(
            mdq_cfg,
            db_file_present=db_file_present,
            schema_error=schema_error,
            schema_checked=schema_checked,
            index_stats=index_stats,
        ),
    )
