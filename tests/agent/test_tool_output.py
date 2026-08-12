"""tests/agent/test_tool_output.py

Characterization tests for agent/tool_output.py's default-output-port
resolution — previously untested (all callers either supply an explicit
OutputPort or rely on the module default). Added before extracting the
shared "output if output is not None else _DEFAULT_OUT" fallback used by
every emit_* function.
"""

from __future__ import annotations

from unittest.mock import MagicMock

from agent.output_tags import OutputTag
from agent.tool_output import (
    emit_approval_pending_notice,
    emit_approval_prompt,
    emit_denied,
    emit_plan_blocked,
    emit_skipped,
    emit_tool_call,
    emit_tool_result,
)


class TestEmitToolCall:
    def test_uses_explicit_output_port(self) -> None:
        out = MagicMock()
        emit_tool_call("read_file", '{"path": "a.py"}', output=out)
        out.write.assert_called_once_with(
            f'  {OutputTag.TOOL} read_file({{"path": "a.py"}})'
        )

    def test_uses_default_output_port_when_none(self) -> None:
        """No exception and no explicit port required — falls back to the module default."""
        emit_tool_call("read_file", "{}")


class TestEmitToolResult:
    def test_uses_explicit_output_port(self) -> None:
        out = MagicMock()
        emit_tool_result("read_file", "3 lines", output=out)
        out.write.assert_called_once_with(f"  {OutputTag.TOOL} read_file: 3 lines")


class TestEmitApprovalPrompt:
    def test_uses_explicit_output_port(self) -> None:
        out = MagicMock()
        emit_approval_prompt("HIGH", "write_file", "preview text", output=out)
        assert out.write.call_count == 2
        out.write.assert_any_call(f"{OutputTag.APPROVAL} HIGH risk: write_file")
        out.write.assert_any_call("    preview: preview text")


class TestEmitDenied:
    def test_uses_explicit_output_port(self) -> None:
        out = MagicMock()
        emit_denied("write_file: not allowed", output=out)
        out.write.assert_called_once_with(f"{OutputTag.DENIED} write_file: not allowed")


class TestEmitPlanBlocked:
    def test_uses_explicit_output_port(self) -> None:
        out = MagicMock()
        emit_plan_blocked("write_file", "{}", output=out)
        assert out.write.call_count == 2
        out.write.assert_any_call(f"{OutputTag.PLAN_BLOCKED} write_file")
        out.write.assert_any_call("    args: {}")


class TestEmitSkipped:
    def test_uses_explicit_output_port(self) -> None:
        out = MagicMock()
        emit_skipped("write_file", output=out)
        out.write.assert_called_once_with(f"{OutputTag.SKIPPED} write_file")


class TestEmitApprovalPendingNotice:
    def test_uses_explicit_output_port(self) -> None:
        out = MagicMock()
        emit_approval_pending_notice("approval-1", "task-1", output=out)
        out.write.assert_called_once()
        written = out.write.call_args[0][0]
        assert "approval-1" in written
        assert "task-1" in written
