# Goal

Remove all direct `print()` calls from `cmd_ingest.py`, `cmd_debug.py`, `cmd_notes.py`,
and `cmd_session.py` by routing output through `OutputPort`, and replace raw dict access
in `cmd_session.py` with explicit type-safe patterns.

# Scope

- `scripts/agent/commands/cmd_ingest.py`
- `scripts/agent/commands/cmd_debug.py`
- `scripts/agent/commands/cmd_notes.py`
- `scripts/agent/commands/cmd_session.py`

# Assumptions

1. `OutputPort` from `output_port.py` (Step 1 prerequisite).
2. `UnknownSubcommandError` from `exceptions.py` (Step 1).
3. `print_success`, `print_no_data`, `print_table`, `print_validation_error` in `cmd_session.py` are imported from `formatter.py` — all replaced with `self._out`.
4. `cmd_session.py` line 82: `r["title"] or ""` is a silent None fallback for session title; replace with `r["title"] if r["title"] is not None else ""`.
5. `cmd_ingest.py` imports `render_export` and `write_export` from `agent.commands.utils` (Step 9 backward-compat plan: these are re-exports from `agent.services.export_formatter` — keep as-is for now).
6. `cmd_debug.py` and `cmd_notes.py` have minimal print usage — straightforward substitution.
7. `self._out` is available via MRO.

# Implementation

## Target file

`cmd_ingest.py`, `cmd_debug.py`, `cmd_notes.py`, `cmd_session.py`

## Procedure

### cmd_session.py

1. Remove `from agent.commands.formatter import print_no_data, print_success, print_table, print_validation_error`.
2. Replace each `print_*` call with `self._out.*`.
3. Fix `r["title"] or ""` → `r["title"] if r["title"] is not None else ""`.

### cmd_ingest.py

1. Replace all `print(...)` → `self._out.write(...)`.
2. Keep `render_export` / `write_export` imports (they write to file/stdout directly; no OutputPort needed for file writes).

### cmd_debug.py

1. Replace all `print(...)` → `self._out.write(...)`.

### cmd_notes.py

1. Replace all `print(...)` → `self._out.write(...)`.
2. Unknown-subcommand fallback → `raise UnknownSubcommandError(sub, ("add", "list", "delete"))`.

## Method

Direct substitution. `cmd_session.py` needs one additional semantic fix for the None-coalesce pattern.

## Details

### cmd_session.py changes

```python
# Remove formatter imports; _out is via MRO

# _session_load_safe
self._out.write_validation_error(f"Invalid session ID: {arg}")

# _session_delete
self._out.write_validation_error(f"Invalid session ID: {arg}")
self._out.write_validation_error("Cannot delete the current session.")
if ok:
    self._out.write_success(f"Session {sid} deleted.")
else:
    self._out.write_no_data(f"Session {sid} not found.")

# _cmd_session list
if not rows:
    self._out.write_no_data("No sessions found")
    return
table_rows = [
    [
        f"{r['session_id']:>4}{'*' if r['is_current'] else ' '}",
        (title := r["title"] if r["title"] is not None else "")[:29] + "..."
        if len(title) > 32 else title,
        r["created_at"],
    ]
    for r in rows
]
self._out.write_table(["ID  ", "Title", "Created"], table_rows)

# _load_session
self._out.write_success(
    f"Session {result.session_id} loaded: {result.n_messages} messages restored."
)
```

### cmd_ingest.py changes

```python
# All bare print() → self._out.write()
# e.g.
if not parts:
    self._out.write("Usage: /ingest <url|path> [lang=ja|en] [--snippets-only]")
    return
...
for msg in result.messages:
    self._out.write(f"  {msg}")
...
except IngestStageError as e:
    self._out.write(f"  [ingest] error ({e.stage}): {e.detail}")
```

### cmd_notes.py changes

```python
# At unknown-subcommand fallback:
raise UnknownSubcommandError(sub, ("add", "list", "delete"))

# All print() → self._out.write*()
```

# Validation plan

- `uv run ruff check scripts/agent/commands/cmd_ingest.py scripts/agent/commands/cmd_debug.py scripts/agent/commands/cmd_notes.py scripts/agent/commands/cmd_session.py`
- `uv run mypy scripts/agent/commands/cmd_session.py`
- `grep -rn "print(" scripts/agent/commands/cmd_ingest.py scripts/agent/commands/cmd_debug.py scripts/agent/commands/cmd_notes.py scripts/agent/commands/cmd_session.py` → 0 hits
- `uv run pytest tests/test_agent_cmd_session.py -v`
