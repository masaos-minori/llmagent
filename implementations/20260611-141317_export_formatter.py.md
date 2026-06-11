# Implementation: agent/services/export_formatter.py — ExportOutputPort + ExportFormat Enum

## Goal

1. Replace all `print()` calls in `write_export()` with `ExportOutputPort` delegation.
2. Replace `fmt: str` parameter in `render_export()` with `ExportFormat` Enum.
3. Replace `str(msg.get("content") or "")` with typed field access.
4. Wrap `OSError` in `write_export()` as `ExportWriteError`.

## Scope

**Target file**: `scripts/agent/services/export_formatter.py`

In scope:
- `write_export(content, outfile, n_messages)` → `write_export(content, outfile, n_messages, out: ExportOutputPort)`
- `render_export(history, fmt: str)` → `render_export(history, fmt: ExportFormat)`
- `str(msg.get("content") or "")` in `render_history_md()` → typed access via `LLMMessage`
- `OSError` → `ExportWriteError`

Out of scope:
- `CliExportOutput` implementation (lives in command layer, not service layer)

## Assumptions

1. `ExportOutputPort(Protocol)` in `io_ports.py`:
   `def write(self, content: str) -> None: ...`
   `def write_file(self, content: str, path: str, n_messages: int) -> None: ...`
2. `ExportFormat.JSON = "json"`, `ExportFormat.MARKDOWN = "markdown"` in `enums.py`.
3. `ExportWriteError(OSError)` in `exceptions.py`.
4. `LLMMessage` already has a typed `content` field accessible via typed dict access.
   Use `msg.get("content") or ""` replaced by `str(msg.get("content") or "")` → keep as-is
   but note this is a pre-existing pattern. Type checking handles the `str | None` case.
5. A `CliExportOutput` class implementing `ExportOutputPort` is created in the command layer
   (e.g., `cmd_export.py`) to provide the actual `print()` behavior.

## Implementation

### Target file

`scripts/agent/services/export_formatter.py`

### Procedure

**Update `render_history_md()`** — change `str(msg.get("content") or "")` to direct typed access:
```python
text = str(msg.get("content") or "")  # keep; LLMMessage is TypedDict, content is str | None
```
No change needed here if `LLMMessage.content` is `str | None`; the existing pattern is correct.

**Update `render_export()`**:
```python
from agent.services.enums import ExportFormat

def render_export(history: list[LLMMessage], fmt: ExportFormat) -> str:
    if fmt == ExportFormat.JSON:
        return orjson.dumps(history, option=orjson.OPT_INDENT_2).decode()
    return render_history_md(history)
```

**Update `write_export()`**:
```python
from agent.services.exceptions import ExportWriteError
from agent.services.io_ports import ExportOutputPort

def write_export(
    content: str,
    outfile: str | None,
    n_messages: int,
    out: ExportOutputPort,
) -> None:
    if not outfile:
        out.write(content)
        return
    try:
        Path(outfile).write_text(content, encoding="utf-8")
        out.write_file(content, outfile, n_messages)
        logger.info(f"Conversation exported to {outfile}")
    except OSError as e:
        raise ExportWriteError(str(e)) from e
```

Add a `CliExportOutput` class in the command layer that provides the `print()` behavior:
```python
class CliExportOutput:
    def write(self, content: str) -> None:
        print(content)
    def write_file(self, content: str, path: str, n_messages: int) -> None:
        print(f"Exported {n_messages} messages to {path} ({len(content)} chars)")
```

Update all call sites of `write_export()` to pass a `CliExportOutput()` instance.

### Method

`Edit` tool for `export_formatter.py`. Locate `write_export` and `render_export` and update them.
Add `CliExportOutput` to command layer with `Edit` or `Write` tool.

### Details

- The `out` parameter is added to `write_export()`; all call sites must be updated.
- `ExportOutputPort` is a Protocol, so `CliExportOutput` need not declare inheritance.
- `write_file()` method receives `content` for size calculation but does not write again
  (the file was already written by `Path.write_text()`).

## Validation plan

```bash
uv run pytest tests/ -k "export" -v
uv run ruff check scripts/agent/services/export_formatter.py
uv run mypy scripts/agent/services/export_formatter.py
ast-grep --pattern 'print($$$)' --lang python scripts/agent/services/export_formatter.py  # expect 0
```
