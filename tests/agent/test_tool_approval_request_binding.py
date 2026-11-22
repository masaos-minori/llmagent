"""tests/agent/test_tool_approval_request_binding.py

Approval binding (REQ-005), preview rules and redaction (REQ-006), and audit
provenance (REQ-007): a late answer never approves a later operation, HIGH risk fails
closed on any preview failure, previews are masked before truncation, and the audit
event records the request without the operator's answer.
"""

from __future__ import annotations

import asyncio
import json
import threading
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from agent.repl_input_controller import (
    InputOutcome,
    InputRequest,
    InputResult,
    PromptKind,
    ReplInputController,
)
from agent.stdin_reader import StdinReader
from agent.tool_approval import check_approval
from shared.transport_dto import ToolCallResult

from tests.agent.test_tool_approval_preflight import _make_cfg, _make_ctx

_PATCH_CONTROLLER = "agent.tool_approval.get_input_controller"


class _Script:
    """A scripted read function; ``block`` makes reads wait for ``release``."""

    def __init__(self, outcomes: list[str], block: bool = False) -> None:
        self.outcomes = list(outcomes)
        self.release = threading.Event()
        if not block:
            self.release.set()

    def __call__(self, _prompt: str) -> str:
        self.release.wait(5)
        return self.outcomes.pop(0) if self.outcomes else ""


def _controller(script: _Script) -> ReplInputController:
    return ReplInputController(StdinReader(read_fn=script))


def _stub_controller(outcome: InputOutcome, text: str = "y") -> MagicMock:
    ctl = MagicMock()
    ctl.submit = AsyncMock(
        return_value=InputResult(InputRequest(PromptKind.NORMAL, ""), outcome, text)
    )
    return ctl


def _ctx(*, high: bool = False, dry_run: str | Exception = "Dry-run: ok") -> MagicMock:
    """A context for delete_file: MEDIUM risk, or HIGH when ``high`` (protected path)."""
    cfg = _make_cfg(approval_protected_paths=["/tmp/"] if high else [])
    ctx = _make_ctx(cfg)
    ctx.services_required.tools = MagicMock()
    if isinstance(dry_run, Exception):
        ctx.services_required.tools.execute = AsyncMock(side_effect=dry_run)
    else:
        ctx.services_required.tools.execute = AsyncMock(
            return_value=ToolCallResult(
                output=dry_run, is_error=False, request_id="", server_key=""
            )
        )
    return ctx


def _audit(ctx: MagicMock) -> MagicMock:
    audit = MagicMock()
    ctx.services_required.audit_logger = audit
    return audit


def _events(audit: MagicMock) -> list[dict[str, Any]]:
    return [json.loads(c.args[0]) for c in audit.info.call_args_list]


_ARGS = {"path": "/tmp/f.txt"}


class TestNoAnswerCrossover:
    @pytest.mark.asyncio
    async def test_consecutive_requests_get_their_own_answers(self) -> None:
        ctx = _ctx()
        audit = _audit(ctx)
        ctl = _controller(_Script(["y", "n"]))
        with patch(_PATCH_CONTROLLER, return_value=ctl):
            first = await check_approval(ctx, "delete_file", _ARGS, "call-1")
            second = await check_approval(ctx, "delete_file", _ARGS, "call-2")
        assert (first, second) == (True, False)
        events = _events(audit)
        assert [e["decision"] for e in events] == ["approved", "denied"]
        assert events[0]["request_id"] != events[1]["request_id"]
        assert all(len(e["request_id"]) == 32 for e in events)

    @pytest.mark.asyncio
    async def test_stale_line_after_a_timeout_never_approves_a_later_request(
        self,
    ) -> None:
        script = _Script(["stale-y", "n"], block=True)
        ctl = _controller(script)
        ctx = _ctx()
        with patch(_PATCH_CONTROLLER, return_value=ctl):
            timed = await ctl.submit(
                InputRequest(PromptKind.NORMAL, "> ", timeout_s=0.05)
            )
            assert timed.outcome is InputOutcome.TIMED_OUT
            # The abandoned read still blocks: the approval is refused, not answered.
            refused = await check_approval(ctx, "delete_file", _ARGS, "call-1")
            assert refused is False
            script.release.set()
            await asyncio.sleep(0.1)
            # The stale line was consumed and dropped; the next approval reads afresh.
            answered = await check_approval(ctx, "delete_file", _ARGS, "call-2")
        assert answered is False  # the fresh answer is "n", not the stale "y"

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "outcome",
        [
            InputOutcome.TIMED_OUT,
            InputOutcome.CANCELLED,
            InputOutcome.EOF,
            InputOutcome.SHUTDOWN,
        ],
    )
    async def test_non_completed_outcome_denies(self, outcome: InputOutcome) -> None:
        ctx = _ctx()
        with patch(_PATCH_CONTROLLER, return_value=_stub_controller(outcome, "y")):
            assert await check_approval(ctx, "delete_file", _ARGS) is False

    @pytest.mark.asyncio
    async def test_request_is_destructive_and_bound_to_the_call_id(self) -> None:
        ctx = _ctx()
        ctl = _stub_controller(InputOutcome.COMPLETED, "y")
        with patch(_PATCH_CONTROLLER, return_value=ctl):
            await check_approval(ctx, "delete_file", _ARGS, "call-42")
        request = ctl.submit.await_args.args[0]
        assert request.prompt_kind is PromptKind.TOOL_APPROVAL
        assert request.operation_id == "call-42"
        assert request.destructive is True


class TestPreviewFailClosed:
    @pytest.mark.asyncio
    async def test_high_risk_dry_run_error_result_denies(self) -> None:
        ctx = _ctx(high=True)
        ctx.services_required.tools.execute = AsyncMock(
            return_value=ToolCallResult(
                output="boom", is_error=True, request_id="", server_key=""
            )
        )
        audit = _audit(ctx)
        ctl = _stub_controller(InputOutcome.COMPLETED, "yes")
        with patch(_PATCH_CONTROLLER, return_value=ctl):
            assert await check_approval(ctx, "delete_file", _ARGS) is False
        ctl.submit.assert_not_awaited()
        event = _events(audit)[0]
        assert event["decision"] == "denied_dry_run_error"
        assert event["fallback_reason"] == "dry_run_error"

    @pytest.mark.asyncio
    async def test_high_risk_dry_run_execution_failure_denies_too(self) -> None:
        ctx = _ctx(high=True, dry_run=RuntimeError("connection refused"))
        audit = _audit(ctx)
        ctl = _stub_controller(InputOutcome.COMPLETED, "yes")
        with patch(_PATCH_CONTROLLER, return_value=ctl):
            assert await check_approval(ctx, "delete_file", _ARGS) is False
        ctl.submit.assert_not_awaited()
        event = _events(audit)[0]
        assert event["decision"] == "denied_preview_failed"
        assert event["fallback_reason"] == "dry_run_failed"

    @pytest.mark.asyncio
    async def test_medium_risk_falls_back_to_the_static_preview_by_default(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        ctx = _ctx(dry_run=RuntimeError("connection refused"))
        audit = _audit(ctx)
        ctl = _stub_controller(InputOutcome.COMPLETED, "y")
        with patch(_PATCH_CONTROLLER, return_value=ctl):
            assert await check_approval(ctx, "delete_file", _ARGS) is True
        event = _events(audit)[0]
        assert event["preview_source"] == "static"
        assert event["fallback_reason"] == "dry_run_failed"
        assert "(static)" in capsys.readouterr().out

    @pytest.mark.asyncio
    async def test_medium_risk_denies_when_the_fallback_setting_is_off(self) -> None:
        ctx = _ctx(dry_run=RuntimeError("connection refused"))
        ctx.cfg.approval.approval_medium_preview_fallback = False
        audit = _audit(ctx)
        ctl = _stub_controller(InputOutcome.COMPLETED, "y")
        with patch(_PATCH_CONTROLLER, return_value=ctl):
            assert await check_approval(ctx, "delete_file", _ARGS) is False
        ctl.submit.assert_not_awaited()
        assert _events(audit)[0]["decision"] == "denied_preview_failed"


class TestPreviewRedaction:
    @pytest.mark.asyncio
    async def test_dry_run_text_is_masked_in_the_prompt(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        ctx = _ctx(dry_run="would delete, token=abcdef123456 used")
        with patch(
            _PATCH_CONTROLLER, return_value=_stub_controller(InputOutcome.COMPLETED)
        ):
            await check_approval(ctx, "delete_file", _ARGS)
        shown = capsys.readouterr().out
        assert "abcdef123456" not in shown
        assert "***MASKED***" in shown

    @pytest.mark.asyncio
    async def test_secret_straddling_the_truncation_point_is_redacted_first(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        ctx = _ctx(dry_run="Dry-run: ok")
        ctx.services_required.runtime_tools = _ctx().services_required.runtime_tools
        args = {
            "path": "/tmp/f.txt",
            "content": "x" * 190 + "password=supersecretvalue",
        }
        with patch(
            _PATCH_CONTROLLER, return_value=_stub_controller(InputOutcome.COMPLETED)
        ):
            await check_approval(ctx, "write_file", args)
        shown = capsys.readouterr().out
        assert "supers" not in shown
        assert "password=s" not in shown

    @pytest.mark.asyncio
    async def test_dry_run_error_text_and_exceptions_stay_out_of_the_prompt(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        ctx = _ctx(high=True)
        ctx.services_required.tools.execute = AsyncMock(
            return_value=ToolCallResult(
                output="failed at /etc/secret/path token=abc123xyz",
                is_error=True,
                request_id="",
                server_key="",
            )
        )
        with patch(
            _PATCH_CONTROLLER, return_value=_stub_controller(InputOutcome.COMPLETED)
        ):
            await check_approval(ctx, "delete_file", _ARGS)
        shown = capsys.readouterr().out
        assert "abc123xyz" not in shown
        assert "/etc/secret/path" not in shown

        ctx = _ctx(high=True, dry_run=RuntimeError("secret detail token=zzz999"))
        with patch(
            _PATCH_CONTROLLER, return_value=_stub_controller(InputOutcome.COMPLETED)
        ):
            await check_approval(ctx, "delete_file", _ARGS)
        shown = capsys.readouterr().out
        assert "zzz999" not in shown
        assert "secret detail" not in shown

    @pytest.mark.asyncio
    async def test_static_preview_is_built_from_masked_arguments(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        ctx = _ctx(dry_run=RuntimeError("down"))
        args = {"path": "/tmp/f.txt", "content": "api_key=PLAINVALUE12345"}
        with patch(
            _PATCH_CONTROLLER, return_value=_stub_controller(InputOutcome.COMPLETED)
        ):
            await check_approval(ctx, "write_file", args)
        assert "PLAINVALUE12345" not in capsys.readouterr().out


class TestAuditProvenance:
    @pytest.mark.asyncio
    async def test_event_carries_request_and_preview_provenance_but_no_answer(
        self,
    ) -> None:
        ctx = _ctx()
        audit = _audit(ctx)
        with patch(
            _PATCH_CONTROLLER,
            return_value=_stub_controller(InputOutcome.COMPLETED, "y"),
        ):
            await check_approval(ctx, "delete_file", _ARGS, "call-7")
        event = _events(audit)[0]
        assert event["decision"] == "approved"
        assert event["idempotency_key"] == "call-7"
        assert len(event["request_id"]) == 32
        assert event["preview_source"] == "dry_run"
        assert event["fallback_reason"] == ""
        assert not {"answer", "input", "text"} & set(event)
