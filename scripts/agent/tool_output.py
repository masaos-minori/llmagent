"""agent/tool_output.py

CLI output helpers for the tool execution subsystem.

Centralises tool-related output so callers receive an OutputPort and
tests can capture output without patching print().
"""

from __future__ import annotations

from agent.commands.output_port import CliOutputPort, OutputPort

_DEFAULT_OUT: OutputPort = CliOutputPort()


def emit_tool_call(name: str, args_json: str, output: OutputPort | None = None) -> None:
    """Write a tool invocation line."""
    out = output if output is not None else _DEFAULT_OUT
    out.write(f"  [tool] {name}({args_json})")


def emit_tool_result(name: str, display: str, output: OutputPort | None = None) -> None:
    """Write a tool result summary line."""
    out = output if output is not None else _DEFAULT_OUT
    out.write(f"  [tool] {name} → {display}")


def emit_approval_prompt(
    risk: str, tool_name: str, preview: str, output: OutputPort | None = None
) -> None:
    """Write the approval prompt header and preview."""
    out = output if output is not None else _DEFAULT_OUT
    out.write(f"\n[{risk} risk] {tool_name}")
    out.write(f"  Preview: {preview}")


def emit_denied(
    tool_name: str, args_json: str, output: OutputPort | None = None
) -> None:
    """Write the args line shown when a tool call is denied."""
    out = output if output is not None else _DEFAULT_OUT
    out.write(f"  args: {args_json}")


def emit_plan_blocked(
    tool_name: str, args_json: str, output: OutputPort | None = None
) -> None:
    """Write plan-mode block notification."""
    out = output if output is not None else _DEFAULT_OUT
    out.write(f"  [plan mode] Blocked: {tool_name}")
    out.write(f"  args: {args_json}")


def emit_skipped(tool_name: str, output: OutputPort | None = None) -> None:
    """Write the 'skipped' confirmation after user denies a tool call."""
    out = output if output is not None else _DEFAULT_OUT
    out.write(f"  Skipped: {tool_name}")


def emit_approval_pending_notice(
    approval_id: str,
    task_id: str,
    output: OutputPort | None = None,
) -> None:
    """Write a visible terminal notice when a workflow turn is suspended for approval."""
    out = output if output is not None else _DEFAULT_OUT
    out.write(
        f"\n[APPROVAL PENDING] Workflow task '{task_id}' is waiting for approval."
        f" Use /approve [reason] or /reject [reason]. (id: {approval_id})"
    )
