"""agent/services/export_formatter.py
Export formatter and I/O service for conversation history.

Extracted from agent.commands.utils so the rendering and write logic
can be tested independently and reused outside the command layer.
"""

from __future__ import annotations

import logging
from pathlib import Path

import orjson
from shared.types import LLMMessage

logger = logging.getLogger(__name__)


def render_history_md(history: list[LLMMessage]) -> str:
    """Render conversation history as a Markdown export string.

    Skips system messages. Tool results are wrapped in code fences.
    """
    lines: list[str] = ["# Conversation Export\n"]
    for msg in history:
        role = msg.get("role", "")
        if role == "system":
            continue
        text = str(msg.get("content") or "")
        if role == "user":
            lines.append(f"## User\n\n{text}\n")
        elif role == "assistant":
            lines.append(f"## Assistant\n\n{text}\n")
        elif role == "tool":
            tc_id = msg.get("tool_call_id", "")
            lines.append(f"## Tool ({tc_id})\n\n```\n{text}\n```\n")
    return "\n".join(lines)


def render_export(history: list[LLMMessage], fmt: str) -> str:
    """Render conversation history to a string in the requested format."""
    if fmt == "json":
        return orjson.dumps(history, option=orjson.OPT_INDENT_2).decode()
    return render_history_md(history)


def write_export(content: str, outfile: str | None, n_messages: int) -> None:
    """Write export content to stdout or a file."""
    if not outfile:
        print(content)
        return
    try:
        Path(outfile).write_text(content, encoding="utf-8")
        print(
            f"Exported {n_messages} messages to {outfile} ({len(content)} chars)",
        )
        logger.info(f"Conversation exported to {outfile}")
    except OSError as e:
        print(f"Export failed: {e}")
