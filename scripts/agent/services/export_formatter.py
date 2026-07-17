"""agent/services/export_formatter.py

Export formatter and I/O service for conversation history.

Extracted from agent.commands.utils so the rendering and write logic
can be tested independently and reused outside the command layer.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import orjson
from shared.json_utils import dumps as _json_dumps
from shared.types import LLMMessage

from agent.services.enums import ExportFormat
from agent.services.exceptions import ExportWriteError
from agent.services.io_ports import ExportOutputPort

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
        content = msg.get("content") or ""
        text = content if isinstance(content, str) else str(content)
        if role == "user":
            lines.append(f"## User\n\n{text}\n")
        elif role == "assistant":
            lines.append(f"## Assistant\n\n{text}\n")
        elif role == "tool":
            tc_id = msg.get("tool_call_id", "")
            lines.append(f"## Tool ({tc_id})\n\n```\n{text}\n```\n")
    return "\n".join(lines)


def render_export(history: list[LLMMessage], fmt: ExportFormat | str) -> str:
    """Render conversation history to a string in the requested format."""
    if fmt == ExportFormat.JSON or fmt == "json":
        json_str: str = _json_dumps(history, option=orjson.OPT_INDENT_2)
        return json_str
    return render_history_md(history)


class _CliExportOutput:
    """Default CLI implementation of ExportOutputPort used when no port is supplied."""

    def write(self, content: str) -> None:
        """Write content to stdout with a trailing newline."""
        sys.stdout.write(content + "\n")

    def write_file(self, content: str, path: str, n_messages: int) -> None:
        """Confirm file export by writing status message to stdout."""
        sys.stdout.write(
            f"Exported {n_messages} messages to {path} ({len(content)} chars)\n"
        )


def write_export(
    content: str,
    outfile: str | None,
    n_messages: int,
    out: ExportOutputPort = _CliExportOutput(),
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
