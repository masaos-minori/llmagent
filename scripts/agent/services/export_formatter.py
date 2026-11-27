"""scripts/agent/services/export_formatter.py

Export formatter and I/O service for conversation history.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path

import orjson
from shared.json_utils import dumps as _json_dumps
from shared.types import LLMMessage

from agent.commands.output_port import CliOutputPort, OutputPort
from agent.services.enums import ExportFormat
from agent.services.exceptions import ExportWriteError

logger = logging.getLogger(__name__)


def fence_for(text: str) -> str:
    """The code fence that can close `text`: longest backtick run plus one, minimum three."""
    longest = max((len(run) for run in re.findall(r"`+", text)), default=0)
    return "`" * max(3, longest + 1)


def escape_md(value: str) -> str:
    """Neutralise the Markdown structure a value could introduce in a heading line."""
    escaped = value.replace("`", "\\`")
    if escaped.startswith("#"):
        escaped = f"\\{escaped}"
    return escaped


def render_history_md(history: list[LLMMessage]) -> str:
    """Render conversation history as a Markdown export string with a closable fence.

    Skips system messages. Tool results are wrapped in a fence longer than the longest
    backtick run in the content, and the tool call id is escaped so it cannot read as a
    heading.
    """
    lines: list[str] = ["# Conversation Export\n"]
    for msg in history:
        role = msg.get("role", "")
        if role == "system":
            continue
        content = msg.get("content") or ""
        text = content if isinstance(content, str) else str(content)
        if role == "user":
            lines.append(f"## User\n\n{text}\n")
        elif role == "assistant":
            lines.append(f"## Assistant\n\n{text}\n")
        elif role == "tool":
            tc_id = escape_md(msg.get("tool_call_id", ""))
            fence = fence_for(text)
            lines.append(f"## Tool ({tc_id})\n\n{fence}\n{text}\n{fence}\n")
    return "\n".join(lines)


def render_export(history: list[LLMMessage], fmt: ExportFormat | str) -> str:
    """Render conversation history to a string in the requested format."""
    if fmt == ExportFormat.JSON or fmt == "json":
        return _json_dumps(history, option=orjson.OPT_INDENT_2)
    return render_history_md(history)


def write_export(
    content: str,
    outfile: str | None,
    n_messages: int,
    out: OutputPort = CliOutputPort(),
) -> None:
    """Write export content to stdout or a file."""
    if not outfile:
        out.write(content)
        return
    try:
        Path(outfile).write_text(content, encoding="utf-8")
        out.write_file(content, outfile, n_messages)
        logger.info("Conversation exported to %s", outfile)
    except OSError as e:
        raise ExportWriteError(str(e)) from e
