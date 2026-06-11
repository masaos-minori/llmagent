"""agent/tool_output.py
CLI output helpers for the tool execution subsystem.

Centralises all print() calls so they can be captured in tests
and replaced with a different output mechanism later.
"""

from __future__ import annotations


def emit_tool_call(name: str, args_json: str) -> None:
    """Print a tool invocation line."""
    print(f"  [tool] {name}({args_json})")


def emit_tool_result(name: str, display: str) -> None:
    """Print a tool result summary line."""
    print(f"  [tool] {name} → {display}")


def emit_approval_prompt(risk: str, tool_name: str, preview: str) -> None:
    """Print the approval prompt header and preview."""
    print(f"\n[{risk} risk] {tool_name}")
    print(f"  Preview: {preview}")


def emit_denied(tool_name: str, args_json: str) -> None:
    """Print the args line shown when a tool call is denied."""
    print(f"  args: {args_json}")


def emit_plan_blocked(tool_name: str, args_json: str) -> None:
    """Print plan-mode block notification."""
    print(f"  [plan mode] Blocked: {tool_name}")
    print(f"  args: {args_json}")


def emit_skipped(tool_name: str) -> None:
    """Print the 'skipped' confirmation after user denies a tool call."""
    print(f"  Skipped: {tool_name}")
