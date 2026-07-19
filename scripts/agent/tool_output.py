"""agent/tool_output.py

CLI output helpers for the tool execution subsystem.

Centralises tool-related output so callers receive an OutputPort and
tests can capture output without patching print().
"""

from __future__ import annotations

from agent.commands.output_port import CliOutputPort, OutputPort
from agent.output_tags import OutputTag

_DEFAULT_OUT: OutputPort = CliOutputPort()


def emit_tool_call(name: str, args_json: str, output: OutputPort | None = None) -> None:
    """Write a tool invocation line."""
    out = output if output is not None else _DEFAULT_OUT
    out.write(f"  {OutputTag.TOOL} {name}({args_json})")


def emit_tool_result(name: str, display: str, output: OutputPort | None = None) -> None:
    """Write a tool result summary line."""
    out = output if output is not None else _DEFAULT_OUT
    out.write(f"  {OutputTag.TOOL} {name}: {display}")


def emit_approval_prompt(
    risk: str, tool_name: str, preview: str, output: OutputPort | None = None
) -> None:
    """Write the approval prompt header and preview."""
    out = output if output is not None else _DEFAULT_OUT
    out.write(f"{OutputTag.APPROVAL} {risk} risk: {tool_name}")
    out.write(f"    preview: {preview}")


def emit_denied(reason: str, output: OutputPort | None = None) -> None:
    """Write the denial line for a tool call. `reason` must include the tool name."""
    out = output if output is not None else _DEFAULT_OUT
    out.write(f"{OutputTag.DENIED} {reason}")


def emit_plan_blocked(
    tool_name: str, args_json: str, output: OutputPort | None = None
) -> None:
    """Write plan-mode block notification."""
    out = output if output is not None else _DEFAULT_OUT
    out.write(f"{OutputTag.PLAN_BLOCKED} {tool_name}")
    out.write(f"    args: {args_json}")


def emit_skipped(tool_name: str, output: OutputPort | None = None) -> None:
    """Write the 'skipped' confirmation after user denies a tool call."""
    out = output if output is not None else _DEFAULT_OUT
    out.write(f"{OutputTag.SKIPPED} {tool_name}")


def emit_approval_pending_notice(
    approval_id: str,
    task_id: str,
    output: OutputPort | None = None,
) -> None:
    """Write a visible terminal notice when a workflow turn is suspended for approval."""
    out = output if output is not None else _DEFAULT_OUT
    out.write(
        f"\n{OutputTag.APPROVAL_PENDING} task '{task_id}' is waiting for approval."
        f" Use /approve [reason] or /reject [reason]. (id: {approval_id})"
    )
