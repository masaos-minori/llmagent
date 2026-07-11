"""agent/tool_result_formatter.py
Tool argument masking and result preview/display helpers.
"""

from __future__ import annotations

from typing import Any

from shared.json_utils import dumps as _json_dumps

# Hint appended to history when a tool result is dropped due to the per-turn limit
TURN_LIMIT_HINT = "[Result omitted: per-turn tool result limit reached.]"


def mask_args(args: dict[str, Any], masked_fields: list[str]) -> dict[str, Any]:
    """Return a copy of args with masked_fields values replaced by '***'.

    Used before logging to prevent sensitive data leakage.
    """
    return {k: ("***" if k in masked_fields else v) for k, v in args.items()}


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
    path = args.get("path") or args.get("file_path", "?")
    raw_content = args.get("content") or args.get("new_content") or ""
    content = raw_content[:200] if isinstance(raw_content, str) else ""
    return f"{path}\n    content: {content!r}"


def _preview_file_path(args: dict[str, Any]) -> str:
    raw_path = args.get("path") or args.get("directory_path")
    return raw_path if isinstance(raw_path, str) else "?"


def _preview_shell_cmd(args: dict[str, Any]) -> str:
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
    raw: str = _json_dumps(args)
    return raw[:300]
