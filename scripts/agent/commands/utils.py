"""agent/commands/utils.py
Shared utilities for command mixins.

These helpers are used by multiple mixins and must not create circular imports.
"""

from __future__ import annotations

from shared.types import LLMMessage


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
