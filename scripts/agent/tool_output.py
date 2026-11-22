"""scripts/agent/tool_output.py

CLI output helpers for the tool execution subsystem.

Centralises tool-related output so callers receive an OutputPort and
tests can capture output without patching print().
"""

from __future__ import annotations

from agent.commands.output_port import CliOutputPort, OutputPort
from agent.output_tags import OutputTag
from agent.secrets_masker import _mask_secrets

_DEFAULT_OUT: OutputPort = CliOutputPort()


def _resolve_out(output: OutputPort | None) -> OutputPort:
    """Return output if given, else the module default CLI output port."""
    return output if output is not None else _DEFAULT_OUT


def emit_tool_call(name: str, args_json: str, output: OutputPort | None = None) -> None:
    """Write a tool invocation line."""
    out = _resolve_out(output)
    out.write(f"  {OutputTag.TOOL} {name}({args_json})")


def emit_tool_result(name: str, display: str, output: OutputPort | None = None) -> None:
    """Write a tool result summary line."""
    out = _resolve_out(output)
    out.write(f"  {OutputTag.TOOL} {name}: {display}")


def emit_approval_prompt(
    risk: str,
    tool_name: str,
    preview: str,
    output: OutputPort | None = None,
    *,
    request_id: str = "",
    preview_source: str = "",
) -> None:
    """Write the approval prompt header and preview (masked as a last defense)."""
    out = _resolve_out(output)
    ref = f" (req {request_id[:8]})" if request_id else ""
    source = f" ({preview_source})" if preview_source else ""
    out.write(f"{OutputTag.APPROVAL} {risk} risk: {tool_name}{ref}")
    out.write(f"    preview{source}: {_mask_secrets(preview)}")


def emit_denied(reason: str, output: OutputPort | None = None) -> None:
    """Write the denial line for a tool call. `reason` must include the tool name."""
    out = _resolve_out(output)
    out.write(f"{OutputTag.DENIED} {_mask_secrets(reason)}")


def emit_plan_blocked(
    tool_name: str, args_json: str, output: OutputPort | None = None
) -> None:
    """Write plan-mode block notification."""
    out = _resolve_out(output)
    out.write(f"{OutputTag.PLAN_BLOCKED} {tool_name}")
    out.write(f"    args: {args_json}")


def emit_skipped(tool_name: str, output: OutputPort | None = None) -> None:
    """Write the 'skipped' confirmation after user denies a tool call."""
    out = _resolve_out(output)
    out.write(f"{OutputTag.SKIPPED} {tool_name}")
