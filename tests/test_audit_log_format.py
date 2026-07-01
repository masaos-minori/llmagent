"""tests/test_audit_log_format.py
Validation tests for MCP and agent-side audit log formats.

Ensures:
- MCP server audit log uses JSON-lines format.
- Agent-side audit log uses JSON-lines format.
- Required fields are present in each format.
- Correlation keys (session, request) match across log types.
"""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import MagicMock

from mcp.audit import _audit_log as _mcp_audit_log

# ---------------------------------------------------------------------------
# MCP server audit log — JSON-lines format
# ---------------------------------------------------------------------------


class TestMcpAuditLogFormat:
    """Tests for MCP server audit log (JSON-lines format)."""

    def _get_parsed(self, **kwargs) -> dict[str, object]:
        """Helper to call _mcp_audit_log and return parsed JSON."""
        logger = MagicMock()
        logger.info.return_value = None
        _mcp_audit_log(logger, **kwargs)
        call_args = logger.info.call_args[0][0]
        return json.loads(call_args)

    def test_emits_json_lines(self) -> None:
        """MCP server audit log must use JSON-lines format."""
        parsed = self._get_parsed(
            session_id="sess-1",
            request_id="req-1",
            action="read_text_file",
            target="/tmp/f.txt",
            outcome="ok",
        )
        assert isinstance(parsed, dict)
        assert "event" in parsed
        assert parsed["event"] == "mcp_tool_exec"
        assert "source" in parsed
        assert parsed["source"] == "mcp_server"

    def test_outcome_error_format(self) -> None:
        """Error outcome must be reflected in JSON-lines record."""
        parsed = self._get_parsed(
            session_id="sess-2",
            request_id="req-2",
            action="write_text_file",
            target="/tmp/g.txt",
            outcome="error",
            detail="permission denied",
        )
        assert parsed["outcome"] == "error"
        assert parsed["detail"] == "permission denied"

    def test_empty_session_id_becomes_dash(self) -> None:
        """Empty session_id must become dash in JSON-lines record."""
        parsed = self._get_parsed(
            session_id="",
            request_id="req-3",
            action="shell_run",
            target="ls",
            outcome="ok",
        )
        assert parsed["session"] == "-"

    def test_empty_request_id_becomes_dash(self) -> None:
        """Empty request_id must become dash in JSON-lines record."""
        parsed = self._get_parsed(
            session_id="sess-4",
            request_id="",
            action="shell_run",
            target="ls",
            outcome="ok",
        )
        assert parsed["request"] == "-"

    def test_emits_json_not_key_value(self) -> None:
        """MCP server audit log must use JSON-lines format, not key=value."""
        parsed = self._get_parsed(
            session_id="sess-5",
            request_id="req-5",
            action="read_text_file",
            target="/tmp/h.txt",
            outcome="ok",
        )
        assert isinstance(parsed, dict)
        assert "event" in parsed

    def test_required_fields_present(self) -> None:
        """All required fields must be present in MCP audit log."""
        parsed = self._get_parsed(
            session_id="sess-6",
            request_id="req-6",
            action="write_file",
            target="/tmp/i.txt",
            outcome="ok",
            detail="created",
        )
        for field in ("event", "source", "ts", "session", "request", "tool", "target", "outcome"):
            assert field in parsed

    def test_no_key_value_format_in_mcp_log(self) -> None:
        """MCP server audit log must NOT use key=value format."""
        logger = MagicMock()
        logger.info.return_value = None
        _mcp_audit_log(
            logger,
            session_id="sess-7",
            request_id="req-7",
            action="read_text_file",
            target="/tmp/j.txt",
            outcome="ok",
            detail="",
        )
        call_args = logger.info.call_args[0][0]
        # Must not contain key=value pairs like "session=", "action="
        assert "session=sess-7" not in call_args
        assert "action=read_text_file" not in call_args

    def test_no_key_value_quoted_values_in_mcp_log(self) -> None:
        """MCP server audit log must NOT use key=value format with quoted values."""
        logger = MagicMock()
        logger.info.return_value = None
        _mcp_audit_log(
            logger,
            session_id="sess-8",
            request_id="req-8",
            action="read_text_file",
            target="/tmp/j.txt",
            outcome="ok",
            detail="",
        )
        call_args = logger.info.call_args[0][0]
        # Must not contain key=value pairs like "outcome=ok"
        assert "outcome=ok" not in call_args

    def test_json_lines_format_not_key_value(self) -> None:
        """MCP audit log must use JSON-lines, not key=value."""
        parsed = self._get_parsed(
            session_id="sess-9",
            request_id="req-9",
            action="read_text_file",
            target="/tmp/k.txt",
            outcome="ok",
        )
        assert isinstance(parsed, dict)
        assert "event" in parsed

    def test_server_key_field_present(self) -> None:
        """Rendered MCP audit log line contains server_key field."""
        parsed = self._get_parsed(
            session_id="sess-1",
            request_id="req-1",
            action="call_tool",
            target="repo/owner",
            outcome="ok",
            server_key="mdq",
        )
        assert "server_key" in parsed
        assert parsed["server_key"] == "mdq"

    def test_error_type_field_present(self) -> None:
        """Rendered MCP audit log line contains error_type field when outcome is error."""
        parsed = self._get_parsed(
            session_id="sess-1",
            request_id="req-1",
            action="call_tool",
            target="",
            outcome="error",
            detail="connection_refused",
            error_type="ConnectionRefusedError",
        )
        assert "error_type" in parsed
        assert parsed["error_type"] == "ConnectionRefusedError"

    def test_error_type_absent_when_ok(self) -> None:
        """Rendered MCP audit log line omits error_type when outcome is ok and no error_type given."""
        parsed = self._get_parsed(
            session_id="sess-1",
            request_id="req-1",
            action="call_tool",
            target="repo/owner",
            outcome="ok",
        )
        assert "error_type" not in parsed


# ---------------------------------------------------------------------------
# Agent-side audit log — JSON-lines format
# ---------------------------------------------------------------------------


class TestAgentAuditLogFormat:
    """Tests for agent-side audit log (JSON-lines format)."""

    def test_emits_json_lines(self) -> None:
        """Agent-side audit log must use JSON-lines format."""
        from agent.tool_audit import audit_tool_exec

        ctx = MagicMock()
        ctx.services.audit_logger = MagicMock()
        ctx.cfg.masked_fields = []
        ctx.turn.current_turn_id = "turn-xyz"
        ctx.workflow.workflow_id = "wf-1"
        ctx.session.session_id = "sess-abc"

        audit_tool_exec(ctx, "shell_run", {"cmd": "ls"}, False, "req-9")

        call_args = ctx.services.audit_logger.info.call_args[0][0]
        # Must be valid JSON
        parsed = json.loads(call_args)
        assert isinstance(parsed, dict)
        assert "event" in parsed
        assert parsed["event"] == "tool_exec"
        assert "tool" in parsed
        assert "mcp_request_id" in parsed

    def test_error_type_in_json_lines(self) -> None:
        """error_type field must be present in agent-side audit log."""
        from agent.tool_audit import audit_tool_exec

        ctx = MagicMock()
        ctx.services.audit_logger = MagicMock()
        ctx.cfg.masked_fields = []
        ctx.turn.current_turn_id = "turn-abc"
        ctx.workflow.workflow_id = ""
        ctx.session.session_id = ""

        audit_tool_exec(
            ctx, "shell_run", {"cmd": "ls"}, True, "req-10", error_type="transport"
        )

        call_args = ctx.services.audit_logger.info.call_args[0][0]
        parsed = json.loads(call_args)
        assert "error_type" in parsed
        assert parsed["error_type"] == "transport"

    def test_no_key_value_format_in_agent_log(self) -> None:
        """Agent-side audit log must NOT use key=value format."""
        from agent.tool_audit import audit_tool_exec

        ctx = MagicMock()
        ctx.services.audit_logger = MagicMock()
        ctx.cfg.masked_fields = []
        ctx.turn.current_turn_id = "turn-def"
        ctx.workflow.workflow_id = ""
        ctx.session.session_id = ""

        audit_tool_exec(ctx, "shell_run", {"cmd": "ls"}, False, "req-11")

        call_args = ctx.services.audit_logger.info.call_args[0][0]
        # Must not start with AUDIT (key=value format)
        assert not call_args.startswith("AUDIT")
        # Must not contain key=value pairs like "session="
        assert "session=" not in call_args

    def test_required_agent_fields_present(self) -> None:
        """Required fields must be present in agent-side audit log."""
        from agent.tool_audit import audit_tool_exec

        ctx = MagicMock()
        ctx.services.audit_logger = MagicMock()
        ctx.cfg.masked_fields = []
        ctx.turn.current_turn_id = "turn-ghi"
        ctx.workflow.workflow_id = "wf-2"
        ctx.session.session_id = "sess-def"

        audit_tool_exec(ctx, "write_file", {"path": "/tmp/k.txt"}, False, "req-12")

        call_args = ctx.services.audit_logger.info.call_args[0][0]
        parsed = json.loads(call_args)
        # Required fields: event, task_id, tool, mcp_request_id, is_error, ts
        for field in ("event", "task_id", "tool", "mcp_request_id", "is_error", "ts"):
            assert field in parsed

    def test_correlation_via_mcp_request_id(self) -> None:
        """MCP server request and agent-side mcp_request_id must correlate."""
        from agent.tool_audit import audit_tool_exec

        correlation_id = "corr-123"
        ctx = MagicMock()
        ctx.services.audit_logger = MagicMock()
        ctx.cfg.masked_fields = []
        ctx.turn.current_turn_id = "turn-jkl"
        ctx.workflow.workflow_id = ""
        ctx.session.session_id = ""

        audit_tool_exec(
            ctx, "read_text_file", {"path": "/tmp/l.txt"}, False, correlation_id
        )

        call_args = ctx.services.audit_logger.info.call_args[0][0]
        parsed = json.loads(call_args)
        assert parsed["mcp_request_id"] == correlation_id

    def test_json_lines_format_not_key_value(self) -> None:
        """Agent-side audit log must use JSON-lines, not key=value."""
        from agent.tool_audit import audit_tool_exec

        ctx = MagicMock()
        ctx.services.audit_logger = MagicMock()
        ctx.cfg.masked_fields = []
        ctx.turn.current_turn_id = "turn-mno"
        ctx.workflow.workflow_id = ""
        ctx.session.session_id = ""

        audit_tool_exec(ctx, "shell_run", {"cmd": "ls"}, False, "req-13")

        call_args = ctx.services.audit_logger.info.call_args[0][0]
        # Must start with { (JSON-lines)
        assert call_args.startswith("{")
        # Must be valid JSON
        parsed = json.loads(call_args)
        assert isinstance(parsed, dict)
