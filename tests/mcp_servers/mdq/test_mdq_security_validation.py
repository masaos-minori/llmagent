"""tests/mcp_servers/mdq/test_mdq_security_validation.py

Tests for scripts/mcp_servers/mdq/mdq_security_validation.py and health_check.py:
validate_mdq_security() reports mdq-mcp's own configuration as a Security Posture, the config view
carries no Secret and no value a fingerprint may not hash, the published posture carries the common
checks the Agent-side validator requires, and no database path, allowed-directory path, or token
value is echoed.
"""

from __future__ import annotations

import re
import sqlite3
from pathlib import Path
from unittest.mock import patch

from fastapi.responses import JSONResponse
from httpx import ASGITransport, AsyncClient
from mcp_servers.mdq.mdq_security_validation import (
    MDQ_OWN_CONFIG_FILE,
    _mdq_config_view,
    build_mdq_posture,
    validate_mdq_security,
)
from mcp_servers.mdq.mdq_server import app
from shared.security.posture_contract import (
    COMMON_CHECK_IDS,
    REQUIRED_CHECK_IDS,
    SecurityPosture,
    compute_config_fingerprint,
)
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
from shared.security.startup_flow import OWN_CONFIG_FILE_VIEW_KEY

from tests.mcp_servers._auth_headers import MCP_TEST_AUTH_HEADERS

MDQ_CHECK_IDS = (
    "server.auth_token_configured",
    "server.allowed_dirs_configured",
    "server.allowed_dirs_exist",
    "server.db_path_valid",
    "server.schema_valid",
    "server.index_available",
)
SECRET_DB_PATH = "/opt/secret-host/mdq.sqlite"
SECRET_DIR = "/secret/path"
SECRET_TOKEN = "sk-secret-token-value"
HEALTHY_STATS = {"document_count": 1, "chunk_count": 2, "fts_row_count": 3}
EMPTY_INDEX_STATS = {"document_count": 4, "chunk_count": 5, "fts_row_count": 0}


def _create_db(tmp_path: Path) -> str:
    """Create the smallest schema check_health() accepts: tables, triggers, FTS5 probe column."""
    path = str(tmp_path / "mdq_security_test.sqlite")
    conn = sqlite3.connect(path)
    try:
        conn.execute(
            "CREATE TABLE documents (doc_id TEXT PRIMARY KEY, source_path TEXT, mtime_ns "
            "INTEGER, size_bytes INTEGER, content_hash TEXT, indexed_at REAL)"
        )
        conn.execute(
            "CREATE TABLE chunks (id INTEGER PRIMARY KEY AUTOINCREMENT, doc_id TEXT, "
            "source_path TEXT, content TEXT, content_hash TEXT, indexed_at REAL)"
        )
        conn.execute(
            "CREATE TABLE chunks_fts (rowid INTEGER PRIMARY KEY, chunks_fts TEXT, "
            "normalized_content TEXT, source_path TEXT)"
        )
        conn.execute(
            "CREATE TRIGGER chunks_ai AFTER INSERT ON chunks BEGIN SELECT 1; END"
        )
        conn.execute(
            "CREATE TRIGGER chunks_ad AFTER DELETE ON chunks BEGIN SELECT 1; END"
        )
        conn.execute(
            "CREATE TRIGGER chunks_au AFTER UPDATE ON chunks BEGIN SELECT 1; END"
        )
        conn.commit()
    finally:
        conn.close()
    return path


def _cfg(tmp_path: Path, **overrides: object) -> dict[str, object]:
    """A config with only the keys a test cares about overridden."""
    cfg: dict[str, object] = {
        "db_path": str(tmp_path / "mdq.sqlite"),
        "allowed_dirs": [str(tmp_path)],
        "auth_token": "test-token",
        "enable_grep": True,
        "max_results_limit": 100,
    }
    cfg.update(overrides)
    return cfg


def _results(
    tmp_path: Path,
    *,
    cfg: dict[str, object] | None = None,
    db_file_present: bool = True,
    schema_error: tuple[str, str] | None = None,
    schema_checked: bool = True,
    index_stats: dict[str, object] | None = HEALTHY_STATS,
) -> dict[str, SecurityCheckResult]:
    """The MDQ check results keyed by check id."""
    checks = validate_mdq_security(
        cfg if cfg is not None else _cfg(tmp_path),
        db_file_present=db_file_present,
        schema_error=schema_error,
        schema_checked=schema_checked,
        index_stats=index_stats,
    )
    return {result.check_id: result for result in checks}


def _posture(
    tmp_path: Path,
    *,
    cfg: dict[str, object] | None = None,
    db_file_present: bool = True,
    schema_error: tuple[str, str] | None = None,
    schema_checked: bool = True,
    index_stats: dict[str, object] | None = HEALTHY_STATS,
) -> SecurityPosture:
    """The posture check_health() publishes, built the way the server builds it."""
    return build_mdq_posture(
        cfg if cfg is not None else _cfg(tmp_path),
        db_file_present,
        schema_error,
        schema_checked,
        index_stats,
    )


class TestCheckSet:
    """The six MDQ checks are always present, in the contract order."""

    def test_ids_match_the_frozen_contract(self, tmp_path: Path) -> None:
        results = _results(tmp_path)
        server_ids = [
            cid for cid in REQUIRED_CHECK_IDS["mdq"] if cid not in COMMON_CHECK_IDS
        ]
        assert list(results) == list(MDQ_CHECK_IDS)
        assert set(results) == set(server_ids)

    def test_deny_all_still_reports_every_check(self, tmp_path: Path) -> None:
        results = _results(tmp_path, cfg=_cfg(tmp_path, allowed_dirs=[]))
        assert len(results) == len(MDQ_CHECK_IDS)

    def test_posture_carries_the_common_checks_too(self, tmp_path: Path) -> None:
        posture = _posture(tmp_path)
        published = {check.check_id for check in posture.checks}
        assert set(REQUIRED_CHECK_IDS["mdq"]) <= published
        assert set(COMMON_CHECK_IDS) <= published


class TestAuthTokenConfigured:
    """Presence only: the token value never reaches a result (REQ-002)."""

    def test_empty_token_is_failed(self, tmp_path: Path) -> None:
        result = _results(tmp_path, cfg=_cfg(tmp_path, auth_token=""))[
            "server.auth_token_configured"
        ]
        assert result.status is SecurityCheckStatus.FAILED
        assert result.reason_code == REASON_AUTH_TOKEN_MISSING

    def test_missing_key_is_failed(self, tmp_path: Path) -> None:
        cfg = _cfg(tmp_path)
        del cfg["auth_token"]
        result = _results(tmp_path, cfg=cfg)["server.auth_token_configured"]
        assert result.status is SecurityCheckStatus.FAILED

    def test_configured_token_is_ok_without_the_value(self, tmp_path: Path) -> None:
        results = _results(tmp_path, cfg=_cfg(tmp_path, auth_token=SECRET_TOKEN))
        result = results["server.auth_token_configured"]
        assert result.status is SecurityCheckStatus.OK
        assert result.reason_code == REASON_OK
        assert SECRET_TOKEN not in result.message


class TestAllowedDirsConfigured:
    """A deny-all mdq-mcp can serve no document, so it is not Ready."""

    def test_empty_allowlist_is_failed(self, tmp_path: Path) -> None:
        result = _results(tmp_path, cfg=_cfg(tmp_path, allowed_dirs=[]))[
            "server.allowed_dirs_configured"
        ]
        assert result.status is SecurityCheckStatus.FAILED
        assert result.reason_code == REASON_ALLOWLIST_EMPTY

    def test_missing_key_is_failed(self, tmp_path: Path) -> None:
        cfg = _cfg(tmp_path)
        del cfg["allowed_dirs"]
        result = _results(tmp_path, cfg=cfg)["server.allowed_dirs_configured"]
        assert result.status is SecurityCheckStatus.FAILED
        assert result.reason_code == REASON_ALLOWLIST_EMPTY

    def test_non_empty_allowlist_is_ok_with_a_count_only(self, tmp_path: Path) -> None:
        result = _results(tmp_path, cfg=_cfg(tmp_path, allowed_dirs=[SECRET_DIR]))[
            "server.allowed_dirs_configured"
        ]
        assert result.status is SecurityCheckStatus.OK
        assert SECRET_DIR not in result.message


class TestAllowedDirsExist:
    """A configured directory that does not exist authorizes nothing."""

    def test_empty_allowlist_is_not_applicable(self, tmp_path: Path) -> None:
        result = _results(tmp_path, cfg=_cfg(tmp_path, allowed_dirs=[]))[
            "server.allowed_dirs_exist"
        ]
        assert result.status is SecurityCheckStatus.NOT_APPLICABLE
        assert result.reason_code == REASON_NOT_APPLICABLE

    def test_missing_directory_is_failed(self, tmp_path: Path) -> None:
        missing = str(tmp_path / "no-such-dir")
        result = _results(tmp_path, cfg=_cfg(tmp_path, allowed_dirs=[missing]))[
            "server.allowed_dirs_exist"
        ]
        assert result.status is SecurityCheckStatus.FAILED
        assert result.reason_code == REASON_ALLOWED_DIR_INVALID
        assert missing not in result.message

    def test_empty_entry_is_failed(self, tmp_path: Path) -> None:
        result = _results(tmp_path, cfg=_cfg(tmp_path, allowed_dirs=[""]))[
            "server.allowed_dirs_exist"
        ]
        assert result.status is SecurityCheckStatus.FAILED
        assert result.reason_code == REASON_ALLOWED_DIR_INVALID

    def test_existing_directory_is_ok(self, tmp_path: Path) -> None:
        result = _results(tmp_path)["server.allowed_dirs_exist"]
        assert result.status is SecurityCheckStatus.OK


class TestDbPathValid:
    """The db file state mirrors the existing db_file dependency entry, without the path."""

    def test_empty_db_path_is_failed(self, tmp_path: Path) -> None:
        result = _results(tmp_path, cfg=_cfg(tmp_path, db_path=""))[
            "server.db_path_valid"
        ]
        assert result.status is SecurityCheckStatus.FAILED
        assert result.reason_code == REASON_DB_PATH_INVALID

    def test_missing_file_is_failed(self, tmp_path: Path) -> None:
        result = _results(tmp_path, db_file_present=False)["server.db_path_valid"]
        assert result.status is SecurityCheckStatus.FAILED
        assert result.reason_code == REASON_DB_PATH_INVALID
        assert str(tmp_path) not in result.message

    def test_existing_file_is_ok(self, tmp_path: Path) -> None:
        result = _results(tmp_path)["server.db_path_valid"]
        assert result.status is SecurityCheckStatus.OK
        assert result.reason_code == REASON_OK


class TestSchemaValid:
    """The existing schema verdict maps to a posture check by dependency key."""

    def test_unrun_check_is_not_applicable(self, tmp_path: Path) -> None:
        result = _results(tmp_path, schema_checked=False)["server.schema_valid"]
        assert result.status is SecurityCheckStatus.NOT_APPLICABLE
        assert result.reason_code == REASON_NOT_APPLICABLE

    def test_schema_error_is_failed_by_key(self, tmp_path: Path) -> None:
        result = _results(
            tmp_path,
            schema_error=("db_schema", "missing chunks_fts FTS5 table"),
        )["server.schema_valid"]
        assert result.status is SecurityCheckStatus.FAILED
        assert result.reason_code == REASON_DEPENDENCY_UNREACHABLE
        assert "db_schema" in result.message
        assert "chunks_fts" not in result.message

    def test_healthy_schema_is_ok(self, tmp_path: Path) -> None:
        result = _results(tmp_path)["server.schema_valid"]
        assert result.status is SecurityCheckStatus.OK


class TestIndexAvailable:
    """An empty FTS index over existing documents is a finding, not a policy violation."""

    def test_missing_stats_are_not_applicable(self, tmp_path: Path) -> None:
        result = _results(tmp_path, index_stats=None)["server.index_available"]
        assert result.status is SecurityCheckStatus.NOT_APPLICABLE
        assert result.reason_code == REASON_NOT_APPLICABLE

    def test_empty_index_over_documents_is_a_warning(self, tmp_path: Path) -> None:
        result = _results(tmp_path, index_stats=EMPTY_INDEX_STATS)[
            "server.index_available"
        ]
        assert result.status is SecurityCheckStatus.WARNING
        assert result.reason_code == REASON_DEPENDENCY_UNREACHABLE

    def test_empty_database_is_ok(self, tmp_path: Path) -> None:
        stats = {"document_count": 0, "chunk_count": 0, "fts_row_count": 0}
        result = _results(tmp_path, index_stats=stats)["server.index_available"]
        assert result.status is SecurityCheckStatus.OK

    def test_populated_index_is_ok(self, tmp_path: Path) -> None:
        result = _results(tmp_path, index_stats=HEALTHY_STATS)["server.index_available"]
        assert result.status is SecurityCheckStatus.OK
        assert result.reason_code == REASON_OK


class TestConfigView:
    """The view is the fingerprint input, so it must be hashable and carry no Secret."""

    def test_carries_the_own_config_file_key(self, tmp_path: Path) -> None:
        view = _mdq_config_view(_cfg(tmp_path))
        assert MDQ_OWN_CONFIG_FILE == "mdq_mcp_server.toml"
        assert view[OWN_CONFIG_FILE_VIEW_KEY] == MDQ_OWN_CONFIG_FILE

    def test_is_hashable_with_the_deployed_shape(self, tmp_path: Path) -> None:
        cfg = _cfg(
            tmp_path,
            db_path=SECRET_DB_PATH,
            allowed_dirs=[SECRET_DIR, "/opt/llm/docs"],
            auth_token=SECRET_TOKEN,
        )
        digest = compute_config_fingerprint(_mdq_config_view(cfg))
        assert re.fullmatch(r"[0-9a-f]{64}", digest)

    def test_carries_no_path_or_token_value(self, tmp_path: Path) -> None:
        cfg = _cfg(
            tmp_path,
            db_path=SECRET_DB_PATH,
            allowed_dirs=[SECRET_DIR],
            auth_token=SECRET_TOKEN,
        )
        view = _mdq_config_view(cfg)
        values = list(view.values())
        assert SECRET_DB_PATH not in values
        assert SECRET_DIR not in values
        assert SECRET_TOKEN not in values
        assert view["db_path_present"] is True
        assert view["auth_token_present"] is True
        assert view["allowed_dirs_count"] == 1

    def test_skips_a_value_a_fingerprint_may_not_hash(self, tmp_path: Path) -> None:
        view = _mdq_config_view(_cfg(tmp_path, max_results_limit=SECRET_DB_PATH))
        assert "max_results_limit" not in view
        assert compute_config_fingerprint(view)


class TestPostureOutcome:
    """validated and ready follow the checks, and an audit-only finding stays non-fatal."""

    def test_healthy_config_is_validated_and_ready(self, tmp_path: Path) -> None:
        posture = _posture(tmp_path)
        assert posture.validated is True
        assert posture.ready is True
        assert posture.server_key == "mdq"

    def test_deny_all_is_not_ready(self, tmp_path: Path) -> None:
        posture = _posture(tmp_path, cfg=_cfg(tmp_path, allowed_dirs=[]))
        assert posture.validated is False
        assert posture.ready is False

    def test_empty_index_warning_keeps_the_posture_validated(
        self, tmp_path: Path
    ) -> None:
        posture = _posture(tmp_path, index_stats=EMPTY_INDEX_STATS)
        assert posture.validated is True
        assert posture.ready is True

    def test_no_message_carries_a_secret_value(self, tmp_path: Path) -> None:
        cfg = _cfg(
            tmp_path,
            db_path=SECRET_DB_PATH,
            allowed_dirs=[SECRET_DIR],
            auth_token=SECRET_TOKEN,
        )
        posture = _posture(tmp_path, cfg=cfg, db_file_present=False)
        text = " ".join(check.message for check in posture.checks)
        for secret in (SECRET_DB_PATH, SECRET_DIR, SECRET_TOKEN):
            assert secret not in text


class TestHealthEndpointPosture:
    """check_health() publishes the posture on /health without changing the other keys."""

    async def _get_health(self, tmp_path: Path, cfg: dict[str, object]) -> JSONResponse:
        with patch("mcp_servers.mdq.health_check.ConfigLoader") as mock_config:
            mock_config.return_value.load.return_value = cfg
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test",
                headers=MCP_TEST_AUTH_HEADERS,
            ) as client:
                return await client.get("/health")

    async def test_ready_body_carries_the_security_block(self, tmp_path: Path) -> None:
        cfg = _cfg(tmp_path, db_path=_create_db(tmp_path))
        resp = await self._get_health(tmp_path, cfg)
        assert resp.status_code == 200
        security = resp.json()["security"]
        assert security["server_key"] == "mdq"
        assert security["validated"] is True
        assert security["ready"] is True
        assert re.fullmatch(r"[0-9a-f]{64}", security["fingerprint"])
        assert {check["id"] for check in security["checks"]} >= set(
            REQUIRED_CHECK_IDS["mdq"]
        )

    async def test_deny_all_body_reports_not_ready(self, tmp_path: Path) -> None:
        cfg = _cfg(tmp_path, db_path=_create_db(tmp_path), allowed_dirs=[])
        resp = await self._get_health(tmp_path, cfg)
        assert resp.status_code == 503
        body = resp.json()
        assert body["ready"] is False
        assert body["dependencies"] == {}
        assert body["security"]["validated"] is False
        assert body["details"]["deny_all"] is True

    async def test_security_block_carries_no_configured_path(
        self, tmp_path: Path
    ) -> None:
        cfg = _cfg(tmp_path, db_path=_create_db(tmp_path), allowed_dirs=[SECRET_DIR])
        resp = await self._get_health(tmp_path, cfg)
        assert resp.status_code == 503
        assert SECRET_DIR not in str(resp.json()["security"])
