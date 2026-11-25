"""
tests/agent/test_dedup_audit_correlation.py
End-to-end correlation test (mcpai007 REQ-009, AC-7): a real HttpTransport over
httpx.MockTransport, the tool_exec audit line, and the transport_failure
diagnostic record must carry the same call identity — request id, session id,
logical call id, workflow task id, and turn id.
"""

from __future__ import annotations

import json
import sqlite3
from typing import Any
from unittest.mock import MagicMock, patch

import httpx
import pytest
from agent.config_builders import build_agent_config
from agent.config_dataclasses import AgentConfig
from agent.diagnostic_store import DiagnosticStore
from agent.tool_loop_guard import ToolLoopGuard
from agent.tool_preparation import PreparedToolCall
from agent.tool_runner import execute_one_tool_call
from mcp_servers.models import CallToolResponse
from shared.mcp_config import McpServerConfig, StartupMode, TransportType
from shared.mcp_health import McpServerHealthRegistry
from shared.runtime_tool import build_runtime_tool
from shared.runtime_tool_registry import RuntimeToolRegistry
from shared.tool_executor import ToolExecutor
from shared.tool_spec import ToolSpec
from shared.transport_dto import ToolExecutionContext

from tests.agent._config_test_defaults import (
    ALL_TOOL_NAMES,
    MIN_DB_CONFIG,
    PERMISSIVE_ALLOWED_ROOT,
    SHIPPED_DB_PATH_KEYS,
)

_CALL_ID_A = "018f0000-0000-7000-8000-000000000011"
_CALL_ID_B = "018f0000-0000-7000-8000-000000000012"
_REQUEST_ID = "req-corr-1"
_TURN_ID = "turn-corr"
_TASK_ID = "task-corr"
_SESSION_ID = 7
_SERVER_KEY = "mcp-corr"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS session_diagnostics (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id  INTEGER,
    kind        TEXT NOT NULL,
    content     TEXT NOT NULL,
    workflow_id TEXT,
    task_id     TEXT,
    storage_format TEXT NOT NULL DEFAULT 'plaintext',
    created_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
)
"""


class _FakeSQLiteHelper:
    """SQLiteHelper drop-in backed by in-memory SQLite."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def open(
        self,
        *,
        write_mode: bool = False,
        row_factory: bool = False,
        **_: object,
    ) -> _FakeSQLiteHelper:
        return self

    def __enter__(self) -> _FakeSQLiteHelper:
        return self

    def __exit__(self, *_: object) -> None:
        pass

    def execute(self, sql: str, params: tuple = ()) -> sqlite3.Cursor:
        return self._conn.execute(sql, params)

    def fetchall(self, sql: str, params: tuple = ()) -> list:
        return self._conn.execute(sql, params).fetchall()

    def commit(self) -> None:
        self._conn.commit()


def _cfg() -> AgentConfig:
    defaults: dict[str, Any] = {
        "context_char_limit": 8000,
        "context_compress_turns": 4,
        "llm_retry_base_delay": 1.0,
        "tool_result_max_llm_chars": 4000,
        "masked_fields": [],
        "allowed_tools": list(ALL_TOOL_NAMES),
        "tool_definitions": [],
        "tool_safety_tiers": {},
        "approval_risk_rules": {},
        "approval_protected_paths": [],
        "approval_github_allowed_repos": [],
        "approval_high_risk_branches": [],
        "approval_shell_safe_prefixes": [],
        "approval_resource_keys": {"path_keys": [], "branch_keys": []},
        "allowed_root": PERMISSIVE_ALLOWED_ROOT,
        "tool_results_turn_max_chars": 0,
        "memory_embed_url": "http://127.0.0.1:9999",
        **SHIPPED_DB_PATH_KEYS,
        "mcp_servers": {
            _SERVER_KEY: {
                "transport": "http",
                "url": "http://127.0.0.1:9999",
                "auth_token": "test-token",
            }
        },
    }
    with patch("agent.config_builders.ProductionConfigValidator") as mock_validator:
        mock_validator.return_value.validate.return_value.errors = []
        mock_validator.return_value.validate.return_value.warnings = []
        return build_agent_config(defaults)


def _registry() -> RuntimeToolRegistry:
    tool = build_runtime_tool(
        name="read_text_file",
        server_key=_SERVER_KEY,
        is_write=False,
        requires_serial=False,
        resource_scope_kind="filesystem",
        resource_scope_keys={"path": "path"},
        agent_safety_tier="READ_ONLY",
        side_effect_class="read_only",
        retry_policy="safe_read_retry",
        reconciliation_policy="not_required",
        idempotency_required=False,
        preview_capability="none",
        policy_version="v2",
    )
    return RuntimeToolRegistry(
        tools={"read_text_file": tool}, allowed_servers=frozenset({_SERVER_KEY})
    )


def _make_ctx(handler) -> tuple[Any, ToolExecutor, _FakeSQLiteHelper]:
    # The bridge writes diagnostics off the event loop, so the connection is
    # touched from another thread.
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    conn.executescript(_SCHEMA)
    fake_db = _FakeSQLiteHelper(conn)

    http = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    ex = ToolExecutor(
        http,
        server_configs={_SERVER_KEY: _http_cfg()},
        health_registry=McpServerHealthRegistry(),
    )
    ex.set_runtime_registry(_registry())

    ctx = MagicMock()
    ctx.cfg = _cfg()
    ctx.turn.current_turn_id = _TURN_ID
    ctx.workflow.workflow_id = "wf-corr"
    ctx.workflow.current_task_id = _TASK_ID
    ctx.session.session_id = _SESSION_ID
    ctx.services_required.audit_logger = MagicMock()
    ctx.services_required.gateway = None
    ctx.services_required.runtime_tools = _registry()
    ctx.services_required.tools = ex
    ctx.diagnostics = DiagnosticStore(
        diagnostics_cfg=_diagnostics_cfg(), db_config=MIN_DB_CONFIG
    )
    patcher = patch(
        "agent.diagnostic_store.SQLiteHelper",
        side_effect=lambda _, db_config=None: fake_db,
    )
    patcher.start()
    return ctx, ex, fake_db


def _http_cfg() -> McpServerConfig:
    return McpServerConfig(
        transport=TransportType.HTTP,
        url="http://127.0.0.1:9999",
        startup_mode=StartupMode.PERSISTENT,
        auth_token="test-token",
    )


def _diagnostics_cfg():
    from agent.config_dataclasses import DiagnosticsConfig

    return DiagnosticsConfig()


def _pc(call_id: str) -> PreparedToolCall:
    args = {"path": "/tmp/f"}
    context = ToolExecutionContext(
        call_id=call_id,
        tool="read_text_file",
        args_hash="",
        operation="call_tool",
        execution_mode="applied",
    )
    return PreparedToolCall(
        call_id=call_id,
        name="read_text_file",
        args=args,
        spec=ToolSpec(
            call_id=call_id, name="read_text_file", args=args, is_write=False
        ),
        original_call={"id": call_id, "name": "read_text_file", "arguments": args},
        context=context,
        grant=None,
    )


class TestDedupAuditCorrelation:
    @pytest.mark.asyncio
    async def test_ids_correlate_across_response_audit_and_diagnostics(self) -> None:
        """AC-7: the five identifiers join the transport response, the audit
        line, and the transport_failure record on one logical call."""
        seen_keys: dict[str, str] = {}

        def handler(request: httpx.Request) -> httpx.Response:
            call_id = request.headers.get("X-Idempotency-Key", "")
            seen_keys[call_id] = call_id
            if call_id == _CALL_ID_A:
                # Tool-level dedup outcome: dedup_state rides on the response.
                body = CallToolResponse(
                    result="duplicate hit",
                    is_error=True,
                    dedup_state="duplicate_hit",
                    execution_mode="applied",
                )
                return httpx.Response(
                    409, json=body.model_dump(), headers={"x-request-id": _REQUEST_ID}
                )
            # Transport-level failure: no response, so the record carries the
            # ids derived from context; request id stays empty (no response).
            raise httpx.ReadTimeout("boom")

        ctx, _, fake_db = _make_ctx(handler)
        guard = ToolLoopGuard(ctx)

        # Call A: tool-level error response with a dedup outcome.
        await execute_one_tool_call(ctx, _pc(_CALL_ID_A), guard=guard)
        audit_a = json.loads(ctx.services_required.audit_logger.info.call_args[0][0])
        assert _CALL_ID_A in seen_keys  # the wire saw the logical call id (AC-1)
        assert audit_a["mcp_request_id"] == _REQUEST_ID
        assert audit_a["idempotency_key"] == _CALL_ID_A
        assert audit_a["dedup_state"] == "duplicate_hit"
        assert audit_a["turn_id"] == _TURN_ID
        assert audit_a["task_linkage"] == _TASK_ID

        # Call B: transport failure -> diagnostics record.
        await execute_one_tool_call(ctx, _pc(_CALL_ID_B), guard=guard)
        audit_b = json.loads(
            ctx.services_required.audit_logger.info.call_args_list[1][0][0]
        )
        assert _CALL_ID_B in seen_keys
        row = fake_db.fetchall(
            "SELECT session_id, kind, content FROM session_diagnostics"
        )
        assert len(row) == 1
        session_id, kind, content = row[0]
        assert kind == "transport_failure"
        assert session_id == _SESSION_ID
        rec = json.loads(content)
        # Join: the same logical call id on the wire, the audit line, and the record.
        assert rec["call_id"] == _CALL_ID_B == audit_b["idempotency_key"]
        assert rec["turn_id"] == _TURN_ID == audit_b["turn_id"]
        assert rec["task_id"] == _TASK_ID == audit_b["task_linkage"]
        # No response was received for this call, so the request id is empty
        # on both sides; the join keys are the ids derived from context.
        assert rec["request_id"] == "" == audit_b["mcp_request_id"]
