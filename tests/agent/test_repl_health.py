"""
tests/test_repl_health.py
Unit tests for repl_health module-level functions.

httpx.AsyncClient and AgentContext are mocked.
"""

from __future__ import annotations

import sqlite3
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from agent.services.mcp_health import (
    _probe_mcp_health_detail,
    check_readiness,
    check_service_health,
)
from agent.services.tool_validation import _check_tool_definitions
from agent.services.workflow_schema import (
    check_workflow_definition,
    check_workflow_schema,
)
from db.schema_sql import WORKFLOW_SCHEMA_VERSION


def _async_result(value: object) -> AsyncMock:
    """Return an AsyncMock whose call returns the given value as a coroutine."""
    m = AsyncMock()
    m.return_value = value
    return m


# ── _probe_mcp_health_detail() ────────────────────────────────────────────────


class TestProbeMcpHealthDetail:
    @pytest.mark.asyncio
    async def test_reachable_true_restart_false_when_200_no_body_field(self) -> None:
        """HTTP 200 with no restart_recommended field: reachable=True, restart_recommended=False."""
        http = AsyncMock(spec=httpx.AsyncClient)
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = {"status": "ok", "ready": True}
        http.get = _async_result(resp)

        result = await _probe_mcp_health_detail(http, "http://localhost:8000")

        assert result.reachable is True
        assert result.status_code == 200
        assert result.restart_recommended is False
        assert result.operator_action_required is False
        http.get.assert_called_once_with("http://localhost:8000/health", timeout=5.0)

    @pytest.mark.asyncio
    async def test_reachable_true_restart_true_when_503_and_restart_recommended(
        self,
    ) -> None:
        """HTTP 503 + restart_recommended=true in body: reachable=True, restart_recommended=True."""
        http = AsyncMock(spec=httpx.AsyncClient)
        resp = MagicMock()
        resp.status_code = 503
        resp.json.return_value = {
            "status": "degraded",
            "ready": False,
            "restart_recommended": True,
            "operator_action_required": False,
        }
        http.get = _async_result(resp)

        result = await _probe_mcp_health_detail(http, "http://localhost:8000")

        assert result.reachable is True
        assert result.status_code == 503
        assert result.restart_recommended is True
        assert result.operator_action_required is False

    @pytest.mark.asyncio
    async def test_reachable_false_on_connection_exception(self) -> None:
        """Connection failure: reachable=False, status_code=None."""
        http = AsyncMock(spec=httpx.AsyncClient)
        http.get.side_effect = httpx.ConnectError("fail")

        result = await _probe_mcp_health_detail(http, "http://localhost:8000")

        assert result.reachable is False
        assert result.status_code is None
        assert result.restart_recommended is False
        assert result.operator_action_required is False
        assert result.body == {}

    @pytest.mark.asyncio
    async def test_reachable_true_parse_failed_on_malformed_json_body(self) -> None:
        """HTTP 200 with a body that fails JSON parsing: parse_failed=True, parse_error populated."""
        http = AsyncMock(spec=httpx.AsyncClient)
        resp = MagicMock()
        resp.status_code = 200
        resp.json.side_effect = ValueError("Expecting value: line 1 column 1 (char 0)")
        resp.text = "not json"
        http.get = _async_result(resp)

        result = await _probe_mcp_health_detail(http, "http://localhost:8000")

        assert result.reachable is True
        assert result.status_code == 200
        assert result.restart_recommended is False
        assert result.operator_action_required is False
        assert result.body == {}
        assert result.parse_failed is True
        assert result.parse_error is not None
        assert "not json" in result.parse_error


# ── _check_tool_definitions() ──────────────────────────────────────────────────


class TestCheckToolDefinitions:
    @pytest.mark.asyncio
    async def test_no_mismatch_returns_empty(self) -> None:
        ctx = MagicMock()
        ctx.cfg.tool.tool_definitions = [
            {"function": {"name": "read_file"}},
            {"function": {"name": "write_file"}},
        ]

        with patch(
            "agent.services.tool_validation._collect_server_tool_names",
            new_callable=AsyncMock,
        ) as mock_collect:
            mock_collect.return_value = ({"read_file", "write_file"}, [])
            result = await _check_tool_definitions(ctx, strict=False)

        assert not result.has_issues

    @pytest.mark.asyncio
    async def test_returns_warning_on_missing_in_server(self) -> None:
        ctx = MagicMock()
        ctx.cfg.tool.tool_definitions = [
            {"function": {"name": "read_file"}},
            {"function": {"name": "write_file"}},
        ]

        with patch(
            "agent.services.tool_validation._collect_server_tool_names",
            new_callable=AsyncMock,
        ) as mock_collect:
            mock_collect.return_value = ({"read_file"}, [])
            result = await _check_tool_definitions(ctx, strict=False)

        msgs = result.warning_messages()
        assert len(msgs) == 1
        assert "write_file" in msgs[0]

    @pytest.mark.asyncio
    async def test_logs_warning_on_missing_in_cfg(self) -> None:
        ctx = MagicMock()
        ctx.cfg.tool.tool_definitions = [
            {"function": {"name": "read_file"}},
        ]

        with patch(
            "agent.services.tool_validation._collect_server_tool_names",
            new_callable=AsyncMock,
        ) as mock_collect:
            mock_collect.return_value = ({"read_file", "delete_file"}, [])
            result = await _check_tool_definitions(ctx, strict=False)

        assert not result.has_issues

    @pytest.mark.asyncio
    async def test_raises_in_strict_mode(self) -> None:
        ctx = MagicMock()
        ctx.cfg.tool.tool_definitions = [
            {"function": {"name": "read_file"}},
        ]

        with patch(
            "agent.services.tool_validation._collect_server_tool_names",
            new_callable=AsyncMock,
        ) as mock_collect:
            mock_collect.return_value = ({"read_file", "delete_file"}, [])
            with pytest.raises(RuntimeError, match="Strict mode"):
                await _check_tool_definitions(ctx, strict=True)

    @pytest.mark.asyncio
    async def test_returns_empty_when_all_servers_unreachable(self) -> None:
        ctx = MagicMock()
        ctx.cfg.tool.tool_definitions = [
            {"function": {"name": "read_file"}},
        ]

        with patch(
            "agent.services.tool_validation._collect_server_tool_names",
            new_callable=AsyncMock,
        ) as mock_collect:
            mock_collect.return_value = (set(), [])
            result = await _check_tool_definitions(ctx, strict=False)

        assert not result.has_issues

    @pytest.mark.asyncio
    async def test_raises_in_strict_mode_when_all_unreachable(self) -> None:
        ctx = MagicMock()
        ctx.cfg.tool.tool_definitions = [
            {"function": {"name": "read_file"}},
        ]

        with patch(
            "agent.services.tool_validation._collect_server_tool_names",
            new_callable=AsyncMock,
        ) as mock_collect:
            mock_collect.return_value = (
                set(),
                ["srv-a"],
            )  # empty names, non-empty unreachable
            with pytest.raises(
                RuntimeError, match="Strict mode: all MCP servers unreachable"
            ):
                await _check_tool_definitions(ctx, strict=True)

    @pytest.mark.asyncio
    async def test_partial_unreachable_non_strict_returns_warning_if_mismatch(
        self,
    ) -> None:
        ctx = MagicMock()
        ctx.cfg.tool.tool_definitions = [
            {"function": {"name": "read_file"}},
            {"function": {"name": "write_file"}},
        ]

        with patch(
            "agent.services.tool_validation._collect_server_tool_names",
            new_callable=AsyncMock,
        ) as mock_collect:
            mock_collect.return_value = ({"read_file"}, ["srv-b"])
            result = await _check_tool_definitions(ctx, strict=False)

        msgs = result.warning_messages()
        assert len(msgs) == 1
        assert "write_file" in msgs[0]

    @pytest.mark.asyncio
    async def test_partial_unreachable_strict_raises(self) -> None:
        ctx = MagicMock()
        ctx.cfg.tool.tool_definitions = [
            {"function": {"name": "read_file"}},
            {"function": {"name": "write_file"}},
        ]

        with patch(
            "agent.services.tool_validation._collect_server_tool_names",
            new_callable=AsyncMock,
        ) as mock_collect:
            mock_collect.return_value = ({"read_file"}, ["srv-b"])
            with pytest.raises(RuntimeError, match="Strict mode"):
                await _check_tool_definitions(ctx, strict=True)

    @pytest.mark.asyncio
    async def test_all_unreachable_non_strict_skips_validation(self) -> None:
        ctx = MagicMock()
        ctx.cfg.tool.tool_definitions = [
            {"function": {"name": "read_file"}},
        ]

        with patch(
            "agent.services.tool_validation._collect_server_tool_names",
            new_callable=AsyncMock,
        ) as mock_collect:
            mock_collect.return_value = (set(), ["srv-a"])
            result = await _check_tool_definitions(ctx, strict=False)

        assert not result.has_issues


# ── check_service_health() ────────────────────────────────────────────────────


class TestCheckServiceHealth:
    @pytest.mark.asyncio
    async def test_returns_empty_when_all_healthy(self) -> None:
        ctx = MagicMock()
        ctx.cfg.llm.llm_url = "http://localhost:8000/v1/chat/completions"
        ctx.cfg.rag.embed_url = "http://localhost:8080/v1/embeddings"
        resp = MagicMock()
        resp.status_code = 200
        http = AsyncMock(spec=httpx.AsyncClient)
        http.get = _async_result(resp)
        ctx.services_required.http = http

        result = await check_service_health(ctx)

        assert not result.has_issues

    @pytest.mark.asyncio
    async def test_returns_error_on_non_200_for_llm(self) -> None:
        # llm is a required service: a non-200 health status is reported as an error.
        ctx = MagicMock()
        ctx.cfg.llm.llm_url = "http://localhost:8000/v1/chat/completions"
        ctx.cfg.rag.embed_url = ""
        resp = MagicMock()
        resp.status_code = 503
        http = AsyncMock(spec=httpx.AsyncClient)
        http.get = _async_result(resp)
        ctx.services_required.http = http

        result = await check_service_health(ctx)

        msgs = result.error_messages()
        assert len(msgs) == 1
        assert "503" in msgs[0]
        assert not result.warning_messages()

    @pytest.mark.asyncio
    async def test_returns_error_on_exception_for_llm(self) -> None:
        # llm is a required service: an unreachable probe is reported as an error.
        ctx = MagicMock()
        ctx.cfg.llm.llm_url = "http://localhost:8000/v1/chat/completions"
        ctx.cfg.rag.embed_url = ""
        http = AsyncMock(spec=httpx.AsyncClient)
        http.get = AsyncMock(side_effect=httpx.ConnectError("refused"))
        ctx.services_required.http = http

        result = await check_service_health(ctx)

        msgs = result.error_messages()
        assert len(msgs) == 1
        assert "refused" in msgs[0]
        assert not result.warning_messages()

    @pytest.mark.asyncio
    async def test_embed_llm_failure_is_warning_not_error(self) -> None:
        # embed-llm is optional: its failure degrades to a warning, never an error.
        healthy = MagicMock()
        healthy.status_code = 200
        embed_resp = MagicMock()
        embed_resp.status_code = 503

        async def _get(url: str, *args, **kwargs):
            if url.startswith("http://localhost:8000"):
                return healthy
            return embed_resp

        ctx = MagicMock()
        ctx.cfg.llm.llm_url = "http://localhost:8000/v1/chat/completions"
        ctx.cfg.rag.embed_url = "http://localhost:8081/embedding"
        http = AsyncMock(spec=httpx.AsyncClient)
        http.get = _get
        ctx.services_required.http = http

        result = await check_service_health(ctx)

        msgs = result.warning_messages()
        assert len(msgs) == 1
        assert "embed-llm" in msgs[0]
        assert not result.error_messages()

    @pytest.mark.asyncio
    async def test_skips_empty_urls(self) -> None:
        ctx = MagicMock()
        ctx.cfg.llm.llm_url = ""
        ctx.cfg.rag.embed_url = ""

        result = await check_service_health(ctx)

        assert not result.has_issues


# ── check_readiness() — production vs development mode ───────────────────────


class TestCheckReadiness:
    """Tests for check_readiness() production/dev mode behavior."""

    def _make_ctx(self, mock_http: object) -> MagicMock:
        ctx = MagicMock()
        ctx.cfg.llm.llm_url = "http://127.0.0.1:8080/v1/chat"
        ctx.cfg.rag.embed_url = "http://127.0.0.1:8081/embedding"
        ctx.services_required.http = mock_http
        return ctx

    @pytest.mark.asyncio
    async def test_production_all_healthy_no_raise(self) -> None:
        resp = MagicMock()
        resp.status_code = 200
        http = AsyncMock(spec=httpx.AsyncClient)
        http.get = _async_result(resp)
        ctx = self._make_ctx(http)
        result = await check_readiness(ctx)
        assert not result.has_issues

    @pytest.mark.asyncio
    async def test_production_service_down_raises(self) -> None:
        http = AsyncMock(spec=httpx.AsyncClient)
        http.get = AsyncMock(side_effect=httpx.ConnectError("connection refused"))
        ctx = self._make_ctx(http)
        with pytest.raises(RuntimeError, match="Startup readiness check failed"):
            await check_readiness(ctx)

    @pytest.mark.asyncio
    async def test_production_non_200_raises(self) -> None:
        resp = MagicMock()
        resp.status_code = 503
        http = AsyncMock(spec=httpx.AsyncClient)
        http.get = _async_result(resp)
        ctx = self._make_ctx(http)
        with pytest.raises(RuntimeError, match="Startup readiness check failed"):
            await check_readiness(ctx)

    @pytest.mark.asyncio
    async def test_dev_mode_healthy_no_issues(self) -> None:
        resp = MagicMock()
        resp.status_code = 200
        http = AsyncMock(spec=httpx.AsyncClient)
        http.get = _async_result(resp)
        ctx = self._make_ctx(http)
        result = await check_readiness(ctx)
        assert not result.has_issues

    @pytest.mark.asyncio
    async def test_error_message_contains_service_label(self) -> None:
        http = AsyncMock(spec=httpx.AsyncClient)
        http.get = AsyncMock(side_effect=httpx.ConnectError("refused"))
        ctx = self._make_ctx(http)
        with pytest.raises(RuntimeError) as exc_info:
            await check_readiness(ctx)
        assert "llm" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_embed_llm_down_does_not_raise(self) -> None:
        # Only embed-llm is down; the LLM probe succeeds. Degraded mode must not raise.
        llm_resp = MagicMock()
        llm_resp.status_code = 200
        embed_resp = MagicMock()
        embed_resp.status_code = 503

        async def _get(url: str, *args, **kwargs):
            if url.startswith("http://127.0.0.1:8080"):
                return llm_resp
            return embed_resp

        http = AsyncMock(spec=httpx.AsyncClient)
        http.get = _get
        ctx = self._make_ctx(http)
        result = await check_readiness(ctx)
        assert result.warning_messages()
        assert not result.error_messages()


class TestCheckWorkflowDefinition:
    """Tests for check_workflow_definition() preflight helper."""

    def test_missing_file_raises(self, tmp_path) -> None:
        """Missing default.json raises RuntimeError."""
        with pytest.raises(RuntimeError) as exc_info:
            check_workflow_definition(workflows_dir=tmp_path)
        assert "not found" in str(exc_info.value)
        assert "default.json" in str(exc_info.value)

    def test_present_file_passes(self, tmp_path) -> None:
        """A complete valid default.json raises no exception."""
        (tmp_path / "default.json").write_text(
            "{"
            '"name": "default", "version": "1.0.0", '
            '"stages": ['
            '{"id": "plan", "timeout_sec": 30, "retryable": false}, '
            '{"id": "execute", "timeout_sec": 120, "retryable": true}, '
            '{"id": "verify", "timeout_sec": 10, "retryable": false}'
            "], "
            '"retry_policy": {"max_attempts": 3, "backoff_sec": 1}'
            "}"
        )
        check_workflow_definition(workflows_dir=tmp_path)  # must not raise

    def test_error_message_includes_remediation(self, tmp_path) -> None:
        """RuntimeError message includes expected remediation hint."""
        with pytest.raises(RuntimeError) as exc_info:
            check_workflow_definition(workflows_dir=tmp_path)
        assert "default.json" in str(exc_info.value)

    def test_malformed_json_raises(self, tmp_path) -> None:
        """Invalid JSON raises RuntimeError naming the file (REQ-001)."""
        (tmp_path / "default.json").write_text("{ this is not valid json ")
        with pytest.raises(RuntimeError) as exc_info:
            check_workflow_definition(workflows_dir=tmp_path)
        assert "default.json" in str(exc_info.value)

    def test_missing_required_key_raises(self, tmp_path) -> None:
        """Missing a required key raises RuntimeError (REQ-002)."""
        (tmp_path / "default.json").write_text(
            '{"name": "default", '
            '"stages": ['
            '{"id": "plan", "timeout_sec": 30, "retryable": false}, '
            '{"id": "execute", "timeout_sec": 120, "retryable": true}, '
            '{"id": "verify", "timeout_sec": 10, "retryable": false}'
            "], "
            '"retry_policy": {"max_attempts": 3, "backoff_sec": 1}}'
        )
        with pytest.raises(RuntimeError) as exc_info:
            check_workflow_definition(workflows_dir=tmp_path)
        assert "default.json" in str(exc_info.value)

    def test_missing_required_stage_raises(self, tmp_path) -> None:
        """Missing a required stage raises RuntimeError (REQ-002)."""
        (tmp_path / "default.json").write_text(
            '{"name": "default", "version": "1.0.0", '
            '"stages": ['
            '{"id": "plan", "timeout_sec": 30, "retryable": false}, '
            '{"id": "execute", "timeout_sec": 120, "retryable": true}'
            "], "
            '"retry_policy": {"max_attempts": 3, "backoff_sec": 1}}'
        )
        with pytest.raises(RuntimeError) as exc_info:
            check_workflow_definition(workflows_dir=tmp_path)
        assert "default.json" in str(exc_info.value)


def _create_workflow_db(
    tmp_path: Any,
    *,
    exclude_table: str | None = None,
    missing_column: tuple[str, str] | None = None,
    schema_version: str | None = WORKFLOW_SCHEMA_VERSION,
) -> str:
    """Create a minimal workflow SQLite DB for testing check_workflow_schema().

    schema_version=None creates an empty workflow_schema_version table (simulates
    a pre-existing DB created before any version was ever recorded).
    """
    db_path = str(tmp_path / "workflow.sqlite")
    conn = sqlite3.connect(db_path)
    schemas = {
        "tasks": (
            "CREATE TABLE tasks (task_id TEXT, session_id TEXT, workflow_id TEXT, status TEXT, created_at TEXT)"
        ),
        "attempts": (
            "CREATE TABLE attempts (attempt_id TEXT, task_id TEXT, stage_id TEXT, status TEXT)"
        ),
        "processed_events": (
            "CREATE TABLE processed_events (event_id TEXT, task_id TEXT)"
        ),
        "artifacts": "CREATE TABLE artifacts (artifact_id TEXT, task_id TEXT)",
    }
    for table, ddl in schemas.items():
        if table == exclude_table:
            continue
        if missing_column and missing_column[0] == table:
            col = missing_column[1]
            ddl = ddl.replace(f", {col} TEXT", "").replace(f"{col} TEXT, ", "")
        conn.execute(ddl)
    if exclude_table != "workflow_schema_version":
        conn.execute(
            "CREATE TABLE workflow_schema_version (version TEXT NOT NULL, applied_at TEXT NOT NULL)"
        )
        if schema_version is not None:
            conn.execute(
                "INSERT INTO workflow_schema_version (version, applied_at) VALUES (?, ?)",
                (schema_version, "2026-01-01T00:00:00Z"),
            )
    conn.commit()
    conn.close()
    return db_path


class TestCheckWorkflowSchema:
    """Tests for check_workflow_schema() preflight helper."""

    def test_valid_schema_passes(self, tmp_path: Any) -> None:
        db_path = _create_workflow_db(tmp_path)
        result = check_workflow_schema(db_path=db_path)
        assert result.valid is True

    def test_missing_tasks_table_fails(self, tmp_path: Any) -> None:
        db_path = _create_workflow_db(tmp_path, exclude_table="tasks")
        result = check_workflow_schema(db_path=db_path)
        assert result.valid is False
        assert result.error is not None and "tasks" in result.error

    def test_missing_attempts_table_fails(self, tmp_path: Any) -> None:
        db_path = _create_workflow_db(tmp_path, exclude_table="attempts")
        result = check_workflow_schema(db_path=db_path)
        assert result.valid is False
        assert result.error is not None and "attempts" in result.error

    def test_missing_processed_events_table_fails(self, tmp_path: Any) -> None:
        db_path = _create_workflow_db(tmp_path, exclude_table="processed_events")
        result = check_workflow_schema(db_path=db_path)
        assert result.valid is False
        assert result.error is not None and "processed_events" in result.error

    def test_missing_artifacts_table_fails(self, tmp_path: Any) -> None:
        db_path = _create_workflow_db(tmp_path, exclude_table="artifacts")
        result = check_workflow_schema(db_path=db_path)
        assert result.valid is False
        assert result.error is not None and "artifacts" in result.error

    def test_missing_required_column_fails(self, tmp_path: Any) -> None:
        db_path = _create_workflow_db(tmp_path, missing_column=("tasks", "workflow_id"))
        result = check_workflow_schema(db_path=db_path)
        assert result.valid is False
        assert result.error is not None and "workflow_id" in result.error

    def test_matching_schema_version_passes(self, tmp_path: Any) -> None:
        db_path = _create_workflow_db(tmp_path, schema_version=WORKFLOW_SCHEMA_VERSION)
        result = check_workflow_schema(db_path=db_path)
        assert result.valid is True

    def test_missing_schema_version_row_fails(self, tmp_path: Any) -> None:
        db_path = _create_workflow_db(tmp_path, schema_version=None)
        result = check_workflow_schema(db_path=db_path)
        assert result.valid is False
        assert result.error is not None and "schema version mismatch" in result.error

    def test_mismatched_schema_version_fails(self, tmp_path: Any) -> None:
        db_path = _create_workflow_db(tmp_path, schema_version="0.9.0")
        result = check_workflow_schema(db_path=db_path)
        assert result.valid is False
        assert result.error is not None and "schema version mismatch" in result.error

    def test_missing_workflow_schema_version_table_fails(self, tmp_path: Any) -> None:
        db_path = _create_workflow_db(tmp_path, exclude_table="workflow_schema_version")
        result = check_workflow_schema(db_path=db_path)
        assert result.valid is False
        assert result.error is not None and "workflow_schema_version" in result.error

    def test_missing_db_file_returns_error(self, tmp_path: Any) -> None:
        nonexistent = str(tmp_path / "nonexistent.db")
        result = check_workflow_schema(db_path=nonexistent)
        assert result.valid is False
        assert result.error is not None and "Workflow DB not found" in result.error


class TestProbeMcpHealthDetailHeaders:
    @pytest.mark.asyncio
    async def test_forwards_headers_to_the_health_request(self) -> None:
        http = AsyncMock(spec=httpx.AsyncClient)
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = {"status": "ok", "ready": True}
        http.get = _async_result(resp)

        await _probe_mcp_health_detail(
            http, "http://localhost:8000", {"Authorization": "Bearer s3cret"}
        )

        assert http.get.call_args.kwargs["headers"] == {
            "Authorization": "Bearer s3cret"
        }
