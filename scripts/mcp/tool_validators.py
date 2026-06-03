"""mcp/tool_validators.py
Tool-specific argument validators for high-risk MCP tools.

Usage:
    @register_validator("my_tool")
    def _validate_my_tool(args: dict[str, Any]) -> None:
        if not args.get("required_field"):
            raise ValueError("required_field must not be empty")

CallToolRequest.validate_args() calls validate_tool_args(name, args),
which runs the registered validator (if any) and propagates ValueError.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

_VALIDATORS: dict[str, Callable[[dict[str, Any]], None]] = {}


def register_validator(tool_name: str) -> Callable:
    """Decorator that registers a validator function for tool_name."""

    def decorator(fn: Callable[[dict[str, Any]], None]) -> Callable[[dict[str, Any]], None]:
        _VALIDATORS[tool_name] = fn
        return fn

    return decorator


def validate_tool_args(tool_name: str, args: dict[str, Any]) -> None:
    """Run the registered validator for tool_name; no-op if none registered."""
    fn = _VALIDATORS.get(tool_name)
    if fn:
        fn(args)


# ── High-risk tool validators ─────────────────────────────────────────────────


@register_validator("git_commit")
def _validate_git_commit(args: dict[str, Any]) -> None:
    if not str(args.get("message", "")).strip():
        raise ValueError("git_commit: message must not be blank")
    repo_path = str(args.get("repo_path", ""))
    if repo_path and not repo_path.startswith("/"):
        raise ValueError(f"git_commit: repo_path must be absolute, got {repo_path!r}")


@register_validator("git_push")
def _validate_git_push(args: dict[str, Any]) -> None:
    repo_path = str(args.get("repo_path", ""))
    if repo_path and not repo_path.startswith("/"):
        raise ValueError(f"git_push: repo_path must be absolute, got {repo_path!r}")
    remote = str(args.get("remote", "origin"))
    if not remote.strip():
        raise ValueError("git_push: remote must not be blank")


@register_validator("trigger_workflow")
def _validate_trigger_workflow(args: dict[str, Any]) -> None:
    if not str(args.get("repo", "")).strip():
        raise ValueError("trigger_workflow: repo must not be blank")
    if not str(args.get("workflow_id", "")).strip():
        raise ValueError("trigger_workflow: workflow_id must not be blank")


@register_validator("shell_run")
def _validate_shell_run(args: dict[str, Any]) -> None:
    cmd = args.get("command", "")
    if isinstance(cmd, list):
        if not cmd:
            raise ValueError("shell_run: command list must not be empty")
    elif not str(cmd).strip():
        raise ValueError("shell_run: command must not be blank")
