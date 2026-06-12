# Goal

Remove the backward-compatibility `out: ExportOutputPort | None = None` default
from `write_export()`, making the concrete `_CliExportOutput()` the explicit default,
and remove the backward-compat comment. Update `cmd_ingest.py` to pass the port
explicitly.

# Scope

- `scripts/agent/services/export_formatter.py` — lines 52–72 (signature + body + comment)
- `scripts/agent/commands/cmd_ingest.py` — line 40 (`write_export` call)

# Assumptions

1. `_CliExportOutput` is a stateless class (no mutable instance fields). Using it
   as a default argument is safe — there is no mutable-default-argument risk.
2. `cmd_ingest.py:40` is the only caller of `write_export` without `out` argument
   (confirmed by grep). After this change it passes `_CliExportOutput()` explicitly.
3. `_CliExportOutput` remains module-private; `cmd_ingest.py` imports it from
   `agent.services.export_formatter`.

# Implementation

## Target files

`scripts/agent/services/export_formatter.py`,
`scripts/agent/commands/cmd_ingest.py`

## Procedure

### A. `export_formatter.py` — remove backward compat

```python
# Before
def write_export(
    content: str,
    outfile: str | None,
    n_messages: int,
    out: ExportOutputPort | None = None,
) -> None:
    """Write export content to stdout or a file.

    When out is None, falls back to the built-in CliExportOutput behaviour
    for backward compatibility with call sites that have not been updated.
    """
    _out = out if out is not None else _CliExportOutput()

# After
def write_export(
    content: str,
    outfile: str | None,
    n_messages: int,
    out: ExportOutputPort = _CliExportOutput(),
) -> None:
    """Write export content to stdout or a file."""
    _out = out
```

Note: `_CliExportOutput()` must be defined **before** `write_export` in the file.
Check current ordering and move the class definition above `write_export` if needed.

### B. `cmd_ingest.py` — pass port explicitly

```python
# Before (line 40)
write_export(content, outfile, len(ctx.conv.history))

# After
from agent.services.export_formatter import _CliExportOutput  # add to imports
write_export(content, outfile, len(ctx.conv.history), _CliExportOutput())
```

Or add `_CliExportOutput` to the existing import at the top of `cmd_ingest.py`.

## Method

- `export_formatter.py`: signature change (remove `None` path) + comment removal
- `cmd_ingest.py`: import addition + argument addition

# Validation plan

- `grep -n "backward compat\|out.*None.*= None" scripts/agent/services/export_formatter.py` → 0 hits
- `uv run ruff check scripts/agent/services/export_formatter.py scripts/agent/commands/cmd_ingest.py`
- `uv run mypy scripts/agent/services/export_formatter.py scripts/agent/commands/cmd_ingest.py`
- `uv run pytest tests/ -k "export or ingest" --ignore=tests/test_create_schema.py -v`
