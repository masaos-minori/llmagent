"""scripts/agent/tool_result_formatter.py

Tool argument masking and result preview/display helpers.
"""

from __future__ import annotations

from typing import Any, cast

from shared.json_utils import dumps as _json_dumps


def turn_limit_hint(omitted_chars: int, omitted_lines: int, limit: int) -> str:
    """Build the hint shown to the LLM in place of a tool result dropped for
    exceeding the per-turn char limit.

    Reports the omitted result's size (so the LLM can gauge how much was cut)
    without including the omitted content itself.
    """
    return (
        f"[Result omitted: per-turn tool result limit reached. "
        f"Omitted result: {omitted_chars} chars, {omitted_lines} lines. "
        f"Configured per-turn limit: {limit} chars.]"
    )


def build_execution_failure_text(exc: Exception) -> str:
    """Build the LLM-facing text for a tool call whose execution raised.

    Mirrors turn_limit_hint(): a fixed bracketed marker that distinguishes an
    execution failure from a tool-reported error and from a preparation
    rejection, followed by the exception class name and message so the model
    can gauge severity. An empty message still yields a usable single-line
    marker.
    """
    class_name = type(exc).__name__
    message = str(exc).strip()
    detail = f"{class_name}: {message}" if message else class_name
    return f"[Tool execution failed: {detail}]"


def _mask_value(value: object, masked_fields: list[str]) -> object:
    """Recursively replace masked_fields keys with '***' at any depth, returning a new tree.

    Dicts are rebuilt with matching keys set to '***' and other values recursed;
    lists are rebuilt with each item recursed; every other value is returned as-is.
    """
    if isinstance(value, dict):
        return {
            k: ("***" if k in masked_fields else _mask_value(v, masked_fields))
            for k, v in value.items()
        }
    if isinstance(value, list):
        return [_mask_value(item, masked_fields) for item in value]
    return value


def mask_args(args: dict[str, Any], masked_fields: list[str]) -> dict[str, Any]:
    """Return a copy of args with masked_fields keys replaced by '***' at any depth.

    Masking is applied before logging and audit writes; it is not applied to the
    interactive approval preview built by build_preview.
    """
    return cast(dict[str, Any], _mask_value(args, masked_fields))


def build_github_preview(args: dict[str, Any]) -> str:
    """Build preview string for github_* tools showing repo and extra args."""
    _owner = args.get("owner")
    owner = _owner if isinstance(_owner, str) else ""
    _repo = args.get("repo")
    repo = _repo if isinstance(_repo, str) else ""
    repo_str = f"{owner}/{repo}" if owner and repo else owner or repo or "?"
    extra = {k: v for k, v in args.items() if k not in ("owner", "repo")}
    extra_str = _json_dumps(extra)[:200]
    return f"{repo_str} {extra_str}"


def _preview_file_write(args: dict[str, Any]) -> str:
    """Generate a preview string for file write/edit operations showing path and content snippet."""
    path = args.get("path") or args.get("file_path", "?")
    raw_content = args.get("content") or args.get("new_content") or ""
    content = raw_content[:200] if isinstance(raw_content, str) else ""
    return f"{path}\n    content: {content!r}"


def _preview_file_path(args: dict[str, Any]) -> str:
    """Generate a preview string for directory/file path operations."""
    raw_path = args.get("path") or args.get("directory_path")
    return raw_path if isinstance(raw_path, str) else "?"


def _preview_shell_cmd(args: dict[str, Any]) -> str:
    """Generate a preview string for shell command execution."""
    raw_cmd = args.get("command")
    return raw_cmd if isinstance(raw_cmd, str) else "?"


def build_preview(tool_name: str, args: dict[str, Any]) -> str:
    """Build a human-readable operation preview shown before approval prompts."""
    if tool_name in ("write_file", "edit_file"):
        return _preview_file_write(args)
    if tool_name in ("delete_file", "delete_directory", "create_directory"):
        return _preview_file_path(args)
    if tool_name == "move_file":
        return f"{args.get('source', '?')} → {args.get('destination', '?')}"
    if tool_name == "shell_run":
        return _preview_shell_cmd(args)
    if tool_name.startswith("github_"):
        return build_github_preview(args)
    if tool_name.startswith("git_"):
        repo = args.get("repo_path", "?")
        branch = args.get("branch")
        remote = args.get("remote")
        parts = [f"git@{repo}"]
        if branch:
            parts.append(f"branch={branch}")
        if remote:
            parts.append(f"remote={remote}")
        return " ".join(parts)
    return _json_dumps(args)[:300]
