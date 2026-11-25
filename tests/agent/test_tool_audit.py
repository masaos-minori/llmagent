"""tests/test_tool_audit.py
Unit tests for agent/tool_audit.py: audit logging functions.
"""

from __future__ import annotations

import ast
import dataclasses
import json
import logging
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest
from agent.config_builders import build_agent_config
from agent.config_dataclasses import AgentConfig
from agent.shared.models import ToolExecEvent
from agent.tool_audit import (
    AUDIT_ARGS_PREVIEW_MAX_CHARS,
    audit_approval,
    audit_tool_exec,
    write_round_exec,
)
from agent.tool_enums import ApprovalDecisionType, RiskLevel
from agent.tool_exceptions import AuditUnavailableError
from shared.json_utils import dumps as _json_dumps

from tests.agent._config_test_defaults import (
    ALL_TOOL_NAMES,
    PERMISSIVE_ALLOWED_ROOT,
    PERMISSIVE_SQLITE_VEC_SO,
    SHIPPED_DB_PATH_KEYS,
)
from tests.agent._producer_registry import make_producer_registry

_CALL_ID = "018f0000-0000-7000-8000-000000000005"  # logical call id fixture (REQ-008)


def _make_cfg(**overrides: Any) -> AgentConfig:
    """Build a minimal AgentConfig with test-safe defaults."""
    base = build_agent_config(
        {
            "allowed_tools": ALL_TOOL_NAMES,
            "context_char_limit": 8000,
            "context_compress_turns": 4,
            "llm_retry_base_delay": 1.0,
            "masked_fields": [],
            "plan_blocked_tools": [],
            "llm_temperature": 0.2,
            "llm_max_tokens": 1024,
            "tool_dedup_max_repeats": 3,
            "tool_cycle_detect_window": 2,
            "tool_error_max_consecutive": 3,
            # memory_embed_enabled now defaults to True; memory_embed_url must be non-empty
            # to satisfy MemoryConfig.__post_init__'s cross-field validation.
            "memory_embed_url": "http://127.0.0.1:9999",
            # build_agent_config() resolves the typed DB configuration from the mapping, so the fixture supplies the mirrored path keys.
            **SHIPPED_DB_PATH_KEYS,
            "mcp_servers": {
                "_dummy": {
                    "transport": "http",
                    "url": "http://127.0.0.1:9999",
                    "auth_token": "test-token",
                }
            },
            "allowed_root": PERMISSIVE_ALLOWED_ROOT,
            "sqlite_vec_so": PERMISSIVE_SQLITE_VEC_SO,
            **overrides,
        }
    )
    return base


def _make_ctx(cfg: AgentConfig | None = None) -> MagicMock:
    """Build a minimal AgentContext mock."""
    ctx = MagicMock()
    ctx.cfg = cfg or _make_cfg()
    ctx.turn.current_turn_id = "test-turn-id"
    ctx.workflow.workflow_id = "wf-test-id"
    ctx.workflow.current_task_id = "test-task-id"
    ctx.session.session_id = None
    ctx.services_required.audit_logger = None
    # Registry None: classify_operation_type fails closed to UNKNOWN for
    # unregistered tools (REQ-007 authority inversion: declarations only).
    ctx.services_required.runtime_tools = None
    return ctx


class TestAuditApprovalInv11:
    """INV-11: every tool-level approval decision is a tool_approval audit event
    that carries the workflow_id and the task_id field (the turn ID)."""

    @staticmethod
    def _logged_event(decision: ApprovalDecisionType) -> dict[str, Any]:
        ctx = _make_ctx()
        ctx.services_required.audit_logger = MagicMock()
        ctx.turn.current_turn_id = "turn-xyz"
        audit_approval(
            ctx, "write_file", RiskLevel.MEDIUM, {"path": "/tmp/x.txt"}, decision
        )
        ctx.services_required.audit_logger.info.assert_called_once()
        payload: dict[str, Any] = json.loads(
            ctx.services_required.audit_logger.info.call_args[0][0]
        )
        return payload

    def test_approved_decision_is_recorded_with_workflow_context(self) -> None:
        event = self._logged_event(ApprovalDecisionType.APPROVED)
        assert event["event"] == "tool_approval"
        assert event["decision"] == "approved"
        assert event["workflow_id"] == "wf-test-id"
        assert event["task_id"] == "turn-xyz"
        # mcpai007 REQ-004: the new fields are additive alongside task_id.
        assert event["turn_id"] == "turn-xyz"
        assert event["task_linkage"] == "test-task-id"

    def test_denied_decision_is_recorded_with_workflow_context(self) -> None:
        event = self._logged_event(ApprovalDecisionType.DENIED)
        assert event["event"] == "tool_approval"
        assert event["decision"] == "denied"
        assert event["workflow_id"] == "wf-test-id"
        assert event["task_id"] == "turn-xyz"


class TestAuditToolExec:
    def test_writes_to_audit_logger_when_conditions_met(self) -> None:
        ctx = _make_ctx()
        ctx.services_required.audit_logger = MagicMock()
        ctx.cfg.tool.masked_fields = []
        ctx.cfg.approval.approval_resource_keys = {}
        ctx.turn.current_turn_id = "turn-abc"

        audit_tool_exec(ctx, "read_text_file", {"path": "/tmp/f"}, False, "req-123")

        ctx.services_required.audit_logger.info.assert_called_once()
        logged = ctx.services_required.audit_logger.info.call_args[0][0]
        assert "tool_exec" in logged
        assert "req-123" in logged
        assert "operation_type" in logged
        assert "resource_scope" in logged

    def test_skips_when_audit_logger_is_none(self) -> None:
        ctx = _make_ctx()
        ctx.services_required.audit_logger = None
        # No error raised even though logger is None
        audit_tool_exec(ctx, "read_text_file", {}, False, "req-123")

    def test_skips_event_when_mcp_request_id_is_empty_and_source_is_empty(self) -> None:
        ctx = _make_ctx()
        ctx.services_required.audit_logger = MagicMock()
        ctx.cfg.tool.masked_fields = []
        ctx.cfg.approval.approval_resource_keys = {}
        audit_tool_exec(ctx, "read_text_file", {}, False, "", source="")
        ctx.services_required.audit_logger.info.assert_not_called()

    def test_emits_event_when_mcp_request_id_empty_but_source_set(self) -> None:
        ctx = _make_ctx()
        ctx.services_required.audit_logger = MagicMock()
        ctx.cfg.tool.masked_fields = []
        ctx.cfg.approval.approval_resource_keys = {}
        audit_tool_exec(ctx, "read_text_file", {}, False, "", source="cache")
        ctx.services_required.audit_logger.info.assert_called_once()
        logged = ctx.services_required.audit_logger.info.call_args[0][0]
        assert "tool_exec" in logged
        assert '"source":"cache"' in logged or '"source": "cache"' in logged
        assert "read_text_file" in logged

    def test_source_default_agent_in_audit_event(self) -> None:
        ctx = _make_ctx()
        ctx.services_required.audit_logger = MagicMock()
        ctx.cfg.tool.masked_fields = []
        ctx.cfg.approval.approval_resource_keys = {}
        audit_tool_exec(ctx, "read_text_file", {"path": "/tmp/f"}, False, "req-123")
        ctx.services_required.audit_logger.info.assert_called_once()
        logged = ctx.services_required.audit_logger.info.call_args[0][0]
        assert '"source":"agent"' in logged or '"source": "agent"' in logged

    def test_resource_scope_from_declared_path_key(self) -> None:
        """REQ-004/REQ-008: scope keys come from the declared mapping only."""
        ctx = _make_ctx()
        ctx.services_required.audit_logger = MagicMock()
        ctx.services_required.runtime_tools = make_producer_registry()
        ctx.cfg.tool.masked_fields = []
        audit_tool_exec(
            ctx,
            "write_file",
            {"path": "/tmp/x"},
            False,
            "req-1",
            idempotency_key=_CALL_ID,
        )
        payload = json.loads(ctx.services_required.audit_logger.info.call_args[0][0])
        assert payload["resource_scope"] == {"path": "/tmp/x"}

    def test_declared_path_list_joined_with_semicolon(self) -> None:
        """Declared path-kind list values keep the ';'-joined recording."""
        ctx = _make_ctx()
        ctx.services_required.audit_logger = MagicMock()
        ctx.services_required.runtime_tools = make_producer_registry()
        ctx.cfg.tool.masked_fields = []
        audit_tool_exec(
            ctx,
            "read_multiple_files",
            {"paths": ["/tmp/a", "", "/tmp/b"]},
            False,
            "req-1",
        )
        payload = json.loads(ctx.services_required.audit_logger.info.call_args[0][0])
        assert payload["resource_scope"] == {"paths": "/tmp/a;/tmp/b"}

    def test_non_escalating_key_not_in_audit_scope(self) -> None:
        """T-04/T-06: `non_escalating` and undeclared args are never recorded."""
        ctx = _make_ctx()
        ctx.services_required.audit_logger = MagicMock()
        ctx.services_required.runtime_tools = make_producer_registry()
        ctx.cfg.tool.masked_fields = []
        audit_tool_exec(
            ctx,
            "github_create_pull_request",
            {"owner": "org", "repo": "r", "base": "main"},
            False,
            "req-1",
            idempotency_key=_CALL_ID,
        )
        payload = json.loads(ctx.services_required.audit_logger.info.call_args[0][0])
        assert payload["resource_scope"] == {"repo": "r"}

    def test_unknown_tool_yields_empty_scope(self) -> None:
        """No registry means no scope: the config-map fallback is removed."""
        ctx = _make_ctx()  # runtime_tools None
        ctx.services_required.audit_logger = MagicMock()
        ctx.cfg.tool.masked_fields = []
        audit_tool_exec(ctx, "mystery_tool", {"path": "/tmp/x"}, False, "req-1")
        payload = json.loads(ctx.services_required.audit_logger.info.call_args[0][0])
        assert payload["resource_scope"] == {}


def _args_preview_after_write(writer: str, args: dict[str, Any]) -> dict[str, Any]:
    """Run one audit writer with a mock sink and return the logged args_preview."""
    ctx = _make_ctx()
    ctx.services_required.audit_logger = MagicMock()
    ctx.cfg.tool.masked_fields = ["secret"]
    ctx.cfg.approval.approval_resource_keys = {}
    if writer == "approval":
        audit_approval(ctx, "write_file", RiskLevel.MEDIUM, args, "approved")
    else:
        audit_tool_exec(
            ctx, "write_file", args, False, "req-1", idempotency_key=_CALL_ID
        )
    logged = ctx.services_required.audit_logger.info.call_args[0][0]
    preview: dict[str, Any] = json.loads(logged)["args_preview"]
    return preview


def _args_of_serialized_length(length: int) -> dict[str, Any]:
    """Build args whose serialized form is exactly ``length`` characters."""
    base = len(_json_dumps({"k": ""}))
    return {"k": "x" * (length - base)}


@pytest.mark.parametrize("writer", ["approval", "exec"])
class TestArgsPreviewBound:
    def test_oversized_value_becomes_envelope(self, writer: str) -> None:
        preview = _args_preview_after_write(writer, {"k": "x" * 5000})
        assert preview["truncated"] is True
        assert len(preview["preview"]) <= AUDIT_ARGS_PREVIEW_MAX_CHARS
        assert "k" not in preview

    def test_exactly_at_cap_is_unchanged(self, writer: str) -> None:
        args = _args_of_serialized_length(AUDIT_ARGS_PREVIEW_MAX_CHARS)
        assert _args_preview_after_write(writer, args) == args

    def test_one_over_cap_becomes_envelope(self, writer: str) -> None:
        args = _args_of_serialized_length(AUDIT_ARGS_PREVIEW_MAX_CHARS + 1)
        preview = _args_preview_after_write(writer, args)
        assert preview["truncated"] is True
        assert len(preview["preview"]) == AUDIT_ARGS_PREVIEW_MAX_CHARS

    def test_masked_value_survives_prefix_and_marker_is_distinct(
        self, writer: str
    ) -> None:
        args = {"secret": "RAW-SECRET-VALUE", "z": "x" * 5000}
        preview = _args_preview_after_write(writer, args)
        assert preview["truncated"] is True
        assert "***" in preview["preview"]
        assert "RAW-SECRET-VALUE" not in preview["preview"]


class TestWriteRoundExec:
    def test_logs_new_fields_when_provided(self) -> None:
        ctx = _make_ctx()
        ctx.services_required.audit_logger = MagicMock()
        write_round_exec(
            ctx,
            round_id="r-1",
            tool_count=2,
            mode="serial",
            has_side_effect=True,
            trigger_tool="write_file",
            elapsed_ms=50.0,
            affected_tools=["write_file", "read_text_file"],
            serial_reason="side_effect",
            estimated_parallel_ms=20.0,
        )
        ctx.services_required.audit_logger.info.assert_called_once()
        logged = ctx.services_required.audit_logger.info.call_args[0][0]
        extra = json.loads(logged)
        assert extra["affected_tools"] == ["write_file", "read_text_file"]
        assert extra["serial_reason"] == "side_effect"
        assert extra["estimated_parallel_ms"] == 20.0

    def test_defaults_to_empty_when_omitted(self) -> None:
        ctx = _make_ctx()
        ctx.services_required.audit_logger = MagicMock()
        write_round_exec(
            ctx,
            round_id="r-2",
            tool_count=1,
            mode="parallel",
            has_side_effect=False,
            trigger_tool=None,
            elapsed_ms=10.0,
        )
        logged = ctx.services_required.audit_logger.info.call_args[0][0]
        extra = json.loads(logged)
        assert extra["affected_tools"] == []
        assert extra["serial_reason"] is None
        assert extra["estimated_parallel_ms"] is None

    def test_no_op_when_audit_logger_none(self) -> None:
        ctx = _make_ctx()
        ctx.services_required.audit_logger = None
        write_round_exec(
            ctx,
            round_id="r-3",
            tool_count=1,
            mode="parallel",
            has_side_effect=False,
            trigger_tool=None,
            elapsed_ms=5.0,
        )  # must not raise


class TestAuditToolExecSnapshotDedup:
    """toolexec001 row 05: execution_snapshot_json + dedup_state in the tool_exec record."""

    def _ctx(self) -> Any:
        ctx = _make_ctx()
        ctx.services_required.audit_logger = MagicMock()
        ctx.cfg.tool.masked_fields = []
        ctx.cfg.approval.approval_resource_keys = {}
        return ctx

    def test_snapshot_key_present_and_parseable(self) -> None:
        ctx = self._ctx()
        audit_tool_exec(ctx, "read_text_file", {"path": "/tmp/f"}, False, "req-123")
        logged = ctx.services_required.audit_logger.info.call_args[0][0]
        payload = json.loads(logged)
        snapshot = json.loads(payload["execution_snapshot_json"])
        assert isinstance(snapshot, dict)
        assert {"deployed_rev", "git_sha", "config_hash", "schema_versions"} <= set(
            snapshot
        )

    def test_dedup_state_omitted_when_empty(self) -> None:
        ctx = self._ctx()
        audit_tool_exec(ctx, "read_text_file", {}, False, "req-123")
        payload = json.loads(ctx.services_required.audit_logger.info.call_args[0][0])
        assert "dedup_state" not in payload

    def test_dedup_state_serialized_when_provided(self) -> None:
        ctx = self._ctx()
        audit_tool_exec(
            ctx,
            "write_file",
            {"path": "/p"},
            False,
            "req-9",
            dedup_state="duplicate_hit",
            idempotency_key=_CALL_ID,
        )
        payload = json.loads(ctx.services_required.audit_logger.info.call_args[0][0])
        assert payload["dedup_state"] == "duplicate_hit"

    def test_existing_record_fields_byte_stable(self) -> None:
        ctx = self._ctx()
        audit_tool_exec(ctx, "read_text_file", {"path": "/tmp/f"}, False, "req-123")
        payload = json.loads(ctx.services_required.audit_logger.info.call_args[0][0])
        expected = {
            "event",
            "task_id",
            "tool",
            "operation_type",
            "resource_scope",
            "mcp_request_id",
            "is_error",
            "args_preview",
            "ts",
            "source",
            "error_type",
            "workflow_id",
            "session_id",
            "idempotency_key",
            "task_linkage",
            "artifact_uri",
            "turn_id",
        }
        assert expected <= set(payload)
        assert set(payload) == expected | {"execution_snapshot_json"}

    def test_turn_id_and_task_linkage_carry_the_context_ids(self) -> None:
        """mcpai007 REQ-004: turn_id is the turn id, task_linkage the workflow task id."""
        ctx = self._ctx()
        audit_tool_exec(ctx, "read_text_file", {}, False, "req-123")
        payload = json.loads(ctx.services_required.audit_logger.info.call_args[0][0])
        assert payload["turn_id"] == "test-turn-id"
        assert payload["task_linkage"] == "test-task-id"

    def test_caller_supplied_task_linkage_wins_over_context(self) -> None:
        ctx = self._ctx()
        audit_tool_exec(
            ctx, "read_text_file", {}, False, "req-123", task_linkage="caller-task"
        )
        payload = json.loads(ctx.services_required.audit_logger.info.call_args[0][0])
        assert payload["task_linkage"] == "caller-task"

    def test_older_shape_record_without_the_new_fields_still_parses(self) -> None:
        """REQ-006/AC-4: records written before the change (no turn_id, empty
        task_linkage) remain parseable: the dataclass defaults fill them in."""
        older = ToolExecEvent(
            event="tool_exec",
            task_id="turn-xyz",
            tool="read_text_file",
            operation_type="READ",
            resource_scope={},
            mcp_request_id="req-1",
            is_error=False,
            args_preview={},
            ts=1.0,
        )
        payload = json.loads(json.dumps(dataclasses.asdict(older)))
        assert payload["turn_id"] == ""
        assert payload["task_linkage"] == ""


def _logged_event_with_fields(
    writer: str, args: dict[str, Any], masked_fields: list[str]
) -> str:
    """Run one audit writer with custom masked_fields and return the logged JSON."""
    ctx = _make_ctx()
    ctx.services_required.audit_logger = MagicMock()
    ctx.cfg.tool.masked_fields = masked_fields
    ctx.cfg.approval.approval_resource_keys = {}
    if writer == "approval":
        audit_approval(ctx, "write_file", RiskLevel.MEDIUM, args, "approved")
    else:
        audit_tool_exec(
            ctx, "write_file", args, False, "req-scrub-1", idempotency_key=_CALL_ID
        )
    logged: str = ctx.services_required.audit_logger.info.call_args[0][0]
    return logged


@pytest.mark.parametrize("writer", ["approval", "exec"])
class TestAuditPreviewScrub:
    """Persisted args_preview carries content-scrubbed values (maskargs001 REQ-003)."""

    def test_writers_scrub_free_form_secret(self, writer: str) -> None:
        args = {"command": "curl -H 'Authorization: Bearer abc1234567890' https://x"}
        logged = _logged_event_with_fields(writer, args, [])
        assert "abc1234567890" not in logged
        marker = "tool_approval" if writer == "approval" else "tool_exec"
        assert marker in logged

    def test_scrubbed_inside_truncated_envelope(self, writer: str) -> None:
        # sort_keys=True in _json_dumps: the filler key sorts after "note" so the
        # secret sits inside the first AUDIT_ARGS_PREVIEW_MAX_CHARS of the envelope.
        args = {"note": "token=abc12345678", "zfiller": "x" * 2000}
        preview = json.loads(_logged_event_with_fields(writer, args, []))[
            "args_preview"
        ]
        assert preview["truncated"] is True
        assert "abc12345678" not in preview["preview"]

    def test_masked_fields_still_star(self, writer: str) -> None:
        args = {"content": "anything", "path": "/tmp/f"}
        preview = json.loads(_logged_event_with_fields(writer, args, ["content"]))[
            "args_preview"
        ]
        assert preview["content"] == "***"
        assert preview["path"] == "/tmp/f"


_SKIP_WRITERS: list[tuple[str, str, str]] = [
    # (branch key, public writer name, tool name used in the call)
    ("approval", "audit_approval", "read_text_file"),
    ("exec", "audit_tool_exec", "read_text_file"),
]


def _call_audit_writer(branch: str, ctx: MagicMock) -> None:
    """Call one of the two workflow-id-precondition writers on ctx."""
    if branch == "approval":
        audit_approval(
            ctx, "read_text_file", RiskLevel.MEDIUM, {"path": "/tmp/skip"}, "approved"
        )
    else:
        # non-empty mcp_request_id so the workflow-id check is reached
        audit_tool_exec(
            ctx, "read_text_file", {"path": "/tmp/skip"}, False, "req-skip-1"
        )


class TestWorkflowIdSkipWarn:
    """Missing workflow_id skips the event with one warning (assertaudit001 REQ-001/REQ-003)."""

    @pytest.mark.parametrize("missing_id", [None, ""])
    @pytest.mark.parametrize("branch,writer_name,tool_name", _SKIP_WRITERS)
    def test_missing_workflow_id_skips_with_warning(
        self,
        branch: str,
        writer_name: str,
        tool_name: str,
        missing_id: str | None,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        ctx = _make_ctx()
        ctx.services_required.audit_logger = MagicMock()
        ctx.workflow.workflow_id = missing_id
        with caplog.at_level(logging.WARNING, logger="agent.tool_audit"):
            _call_audit_writer(branch, ctx)  # must not raise
        ctx.services_required.audit_logger.info.assert_not_called()
        warnings = [
            r
            for r in caplog.records
            if r.name == "agent.tool_audit" and r.levelno >= logging.WARNING
        ]
        assert len(warnings) == 1
        message = warnings[0].getMessage()
        assert writer_name in message
        assert tool_name in message
        assert "/tmp/skip" not in message  # warning must not carry argument values

    @pytest.mark.parametrize("branch", ["approval", "decision", "exec"])
    def test_no_warning_without_audit_logger(
        self,
        branch: str,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        ctx = _make_ctx()  # audit_logger = None by default
        ctx.workflow.workflow_id = None
        with caplog.at_level(logging.WARNING, logger="agent.tool_audit"):
            _call_audit_writer(branch, ctx)
        warnings = [
            r
            for r in caplog.records
            if r.name == "agent.tool_audit" and r.levelno >= logging.WARNING
        ]
        assert (
            not warnings
        )  # audit_logger guard precedes the workflow-id check (REQ-002)

    @pytest.mark.parametrize("missing_id", [None, ""])
    def test_early_return_precedes_workflow_check(
        self, missing_id: str | None, caplog: pytest.LogCaptureFixture
    ) -> None:
        ctx = _make_ctx()
        ctx.services_required.audit_logger = MagicMock()
        ctx.workflow.workflow_id = missing_id
        with caplog.at_level(logging.WARNING, logger="agent.tool_audit"):
            audit_tool_exec(ctx, "read_text_file", {}, False, "", source="")
        ctx.services_required.audit_logger.info.assert_not_called()
        warnings = [
            r
            for r in caplog.records
            if r.name == "agent.tool_audit" and r.levelno >= logging.WARNING
        ]
        assert (
            not warnings
        )  # mcp_request_id/source early return precedes the workflow check

    def test_no_assert_statements_in_source(self) -> None:
        source_path = (
            Path(__file__).resolve().parents[2] / "scripts/agent/tool_audit.py"
        )
        tree = ast.parse(source_path.read_text(encoding="utf-8"))
        assert not any(isinstance(node, ast.Assert) for node in ast.walk(tree))


class TestDeniedResultAudit:
    """Denied results are audited despite empty identity (toolaudit001 REQ-001/REQ-002)."""

    def test_denied_result_is_audited(self) -> None:
        ctx = _make_ctx()
        ctx.services_required.audit_logger = MagicMock()
        audit_tool_exec(
            ctx, "write_file", {"path": "/tmp/x"}, True, "", "denied", source=""
        )
        ctx.services_required.audit_logger.info.assert_called_once()
        record = json.loads(ctx.services_required.audit_logger.info.call_args[0][0])
        assert record["event"] == "tool_exec"
        assert record["error_type"] == "denied"
        assert record["is_error"] is True
        assert record["mcp_request_id"] == ""
        assert record["source"] == "agent"

    @pytest.mark.parametrize("error_type", ["", "tool"])
    def test_empty_identity_non_denied_still_skipped(self, error_type: str) -> None:
        ctx = _make_ctx()
        ctx.services_required.audit_logger = MagicMock()
        audit_tool_exec(ctx, "read_text_file", {}, False, "", error_type, source="")
        ctx.services_required.audit_logger.info.assert_not_called()

    def test_denied_record_keeps_full_field_set(self) -> None:
        denied_ctx = _make_ctx()
        denied_ctx.services_required.audit_logger = MagicMock()
        audit_tool_exec(
            denied_ctx, "write_file", {"path": "/tmp/x"}, True, "", "denied", source=""
        )
        denied = json.loads(
            denied_ctx.services_required.audit_logger.info.call_args[0][0]
        )

        control_ctx = _make_ctx()
        control_ctx.services_required.audit_logger = MagicMock()
        audit_tool_exec(
            control_ctx,
            "write_file",
            {"path": "/tmp/x"},
            True,
            "req-1",
            "",
            source="agent",
            idempotency_key=_CALL_ID,
        )
        control = json.loads(
            control_ctx.services_required.audit_logger.info.call_args[0][0]
        )
        assert set(denied) == set(control)


class TestMandatoryAuditForSideEffects:
    """mcpdl001 REQ-007/REQ-008 (AC-5): side-effecting calls fail closed when
    the audit record cannot be written; read-only calls stay best-effort."""

    def _logged_ctx(self) -> Any:
        ctx = _make_ctx()
        ctx.services_required.audit_logger = MagicMock()
        ctx.cfg.tool.masked_fields = []
        ctx.cfg.approval.approval_resource_keys = {}
        ctx.services_required.runtime_tools = make_producer_registry()
        return ctx

    def test_write_with_missing_audit_logger_raises(self) -> None:
        ctx = _make_ctx()  # audit_logger = None
        ctx.services_required.runtime_tools = make_producer_registry()
        ctx.services_required.tools.execute = MagicMock()
        with pytest.raises(AuditUnavailableError, match="write_file"):
            audit_tool_exec(
                ctx,
                "write_file",
                {"path": "/tmp/x"},
                False,
                "req-1",
                source="mcp",
                idempotency_key=_CALL_ID,
            )

    def test_delete_with_missing_audit_logger_raises(self) -> None:
        ctx = _make_ctx()
        ctx.services_required.runtime_tools = make_producer_registry()
        with pytest.raises(AuditUnavailableError, match="delete_file"):
            audit_tool_exec(
                ctx,
                "delete_file",
                {"path": "/tmp/x"},
                False,
                "req-1",
                source="mcp",
                idempotency_key=_CALL_ID,
            )

    def test_read_only_with_missing_audit_logger_stays_silent(self) -> None:
        ctx = _make_ctx()
        ctx.services_required.runtime_tools = make_producer_registry()
        audit_tool_exec(
            ctx,
            "read_text_file",
            {"path": "/tmp/f"},
            False,
            "req-1",
            source="mcp",
            idempotency_key=_CALL_ID,
        )  # must not raise (REQ-007 best-effort carve-out)

    def test_write_with_empty_logical_id_raises(self) -> None:
        ctx = self._logged_ctx()
        with pytest.raises(AuditUnavailableError, match="logical call id"):
            audit_tool_exec(ctx, "write_file", {"path": "/tmp/x"}, False, "req-1")

    def test_read_only_with_empty_logical_id_still_emits(self) -> None:
        ctx = self._logged_ctx()
        ctx.services_required.runtime_tools = make_producer_registry()
        audit_tool_exec(ctx, "read_text_file", {"path": "/tmp/f"}, False, "req-1")
        ctx.services_required.audit_logger.info.assert_called_once()

    def test_write_with_empty_identity_raises(self) -> None:
        ctx = self._logged_ctx()
        with pytest.raises(AuditUnavailableError, match="no mcp_request_id or source"):
            audit_tool_exec(
                ctx,
                "write_file",
                {"path": "/tmp/x"},
                False,
                "",
                source="",
                idempotency_key=_CALL_ID,
            )

    def test_write_without_workflow_id_raises_after_warning(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        ctx = self._logged_ctx()
        ctx.workflow.workflow_id = None
        with caplog.at_level(logging.WARNING, logger="agent.tool_audit"):
            with pytest.raises(AuditUnavailableError, match="outside workflow context"):
                audit_tool_exec(
                    ctx,
                    "write_file",
                    {"path": "/tmp/x"},
                    False,
                    "req-1",
                    idempotency_key=_CALL_ID,
                )
        assert "audit_tool_exec" in caplog.text
        assert "/tmp/x" not in caplog.text  # no argument values in the warning

    def test_denied_path_keeps_skip_and_empty_id_behavior(self) -> None:
        """Denied events never executed a side effect: skip behavior unchanged."""
        ctx_none = _make_ctx()  # audit_logger = None
        audit_tool_exec(
            ctx_none, "write_file", {"path": "/tmp/x"}, True, "", "denied", source=""
        )  # must not raise (Compatibility: denied path keeps skip behavior)

        ctx = self._logged_ctx()
        audit_tool_exec(
            ctx, "write_file", {"path": "/tmp/x"}, True, "", "denied", source=""
        )  # empty logical id stays allowed for denied events
        ctx.services_required.audit_logger.info.assert_called_once()

    def test_logical_id_lands_in_the_event(self) -> None:
        ctx = self._logged_ctx()
        audit_tool_exec(
            ctx,
            "write_file",
            {"path": "/tmp/x"},
            False,
            "req-1",
            source="mcp",
            idempotency_key=_CALL_ID,
        )
        payload = json.loads(ctx.services_required.audit_logger.info.call_args[0][0])
        assert payload["idempotency_key"] == _CALL_ID
