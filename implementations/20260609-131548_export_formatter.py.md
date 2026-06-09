# Implementation: export_formatter.py — Move export rendering to service

## Goal

Create `agent/services/export_formatter.py` with `render_history_md`, `render_export`, and
`write_export` moved from `utils.py`. Keep backward-compatible re-exports in `utils.py`.

## Scope

- `scripts/agent/services/export_formatter.py`: new file with the three functions.
- `scripts/agent/commands/utils.py`: import and re-export them for backward compatibility.

## Assumptions

1. `render_history_md`, `render_export`, `write_export` are called from `cmd_ingest.py`
   via `from agent.commands.utils import render_export, write_export`.
2. `utils.py` re-exports them so no callers break.
3. The function bodies are identical — no behavior change.

## Implementation

### Target files

- `scripts/agent/services/export_formatter.py` (new)
- `scripts/agent/commands/utils.py`

### Procedure

**export_formatter.py:**

```python
"""agent/services/export_formatter.py
Export formatter and I/O for conversation history.
"""
from __future__ import annotations
import logging
from pathlib import Path
import orjson
from shared.types import LLMMessage

logger = logging.getLogger(__name__)


def render_history_md(history: list[LLMMessage]) -> str:
    """Render conversation history as a Markdown export string."""
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
        print(f"Exported {n_messages} messages to {outfile} ({len(content)} chars)")
        logger.info(f"Conversation exported to {outfile}")
    except OSError as e:
        print(f"Export failed: {e}")
```

**utils.py — add re-exports at end of file:**

```python
# Re-exported from agent.services.export_formatter for backward compatibility.
from agent.services.export_formatter import (  # noqa: E402, F401
    render_export,
    render_history_md,
    write_export,
)
```

### Method

Create service file with identical bodies; add re-exports to `utils.py`.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Service exists | `ls scripts/agent/services/export_formatter.py` | present |
| Re-exports work | `python -c "from agent.commands.utils import render_export"` | no error |
| Lint | `uv run ruff check scripts/agent/` | 0 errors |
| Tests | `uv run pytest tests/ -q -k "export"` | all pass |
