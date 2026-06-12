"""agent/tool_result_formatter.py
Tool argument masking and result preview/display helpers.

Extracted from repl_tool_exec.py and agent/commands/registry.py.
mask_args moved here from registry.py (re-export removed).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import orjson

if TYPE_CHECKING:
    from agent.config import AgentConfig

# Hint appended to history when a tool result is dropped due to the per-turn limit
TURN_LIMIT_HINT = (
    "[Result omitted: per-turn tool result limit reached."
    " Use /tool show <id> to retrieve the full output.]"
)


def mask_args(args: dict, masked_fields: list[str]) -> dict:
    """Return a copy of args with masked_fields values replaced by '***'.

    Used before logging to prevent sensitive data leakage.
    """
    return {k: ("***" if k in masked_fields else v) for k, v in args.items()}


def is_summarized(
    cfg: AgentConfig,
    text: str,
    llm_text: str,
    is_error: bool,
) -> bool:
    """Return True when llm_text represents a summarized (not truncated) form of text."""
    if not cfg.tool.use_tool_summarize or is_error:
        return False
    if len(text) <= cfg.tool.tool_summarize_threshold:
        return False
    if llm_text == text:
        return False
    truncated = text[: cfg.tool.tool_result_max_llm_chars] + "\n... (truncated)"
    return llm_text != truncated


def build_github_preview(args: dict[str, Any]) -> str:
    """Build preview string for github_* tools showing repo and extra args."""
    _owner = args.get("owner")
    owner = _owner if isinstance(_owner, str) else ""
    _repo = args.get("repo")
    repo = _repo if isinstance(_repo, str) else ""
    repo_str = f"{owner}/{repo}" if owner and repo else owner or repo or "?"
    extra = {k: v for k, v in args.items() if k not in ("owner", "repo")}
    extra_str = orjson.dumps(extra, option=orjson.OPT_SORT_KEYS).decode()[:200]
    return f"{repo_str} {extra_str}"


def build_preview(tool_name: str, args: dict[str, Any]) -> str:
    """Build a human-readable operation preview shown before approval prompts."""
    if tool_name in ("write_file", "edit_file"):
        path = args.get("path") or args.get("file_path", "?")
        _content = args.get("content") or args.get("new_content") or ""
        content = _content[:200] if isinstance(_content, str) else ""
        return f"{path}\n    content: {content!r}"
    if tool_name in ("delete_file", "delete_directory", "create_directory"):
        _path = args.get("path") or args.get("directory_path")
        return _path if isinstance(_path, str) else "?"
    if tool_name == "move_file":
        return f"{args.get('source', '?')} → {args.get('destination', '?')}"
    if tool_name == "shell_run":
        _cmd = args.get("command")
        return _cmd if isinstance(_cmd, str) else "?"
    if tool_name.startswith("github_"):
        return build_github_preview(args)
    raw: str = orjson.dumps(args, option=orjson.OPT_SORT_KEYS).decode()
    return raw[:300]
