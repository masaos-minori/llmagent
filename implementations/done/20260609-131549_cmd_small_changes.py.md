# Implementation: Small changes — cmd_mcp, cmd_tooling, cmd_notes, cmd_debug, cmd_config

## Goal

Apply the small targeted changes to five command files:
- `cmd_mcp.py`: change default behavior to show usage instead of status
- `cmd_tooling.py`: no code change needed (plan says "clarify responsibility")
- `cmd_notes.py`: extract `_note_list` formatter to a function
- `cmd_debug.py`: replace hardcoded `20` and logger names with constants
- `cmd_config.py`: add comment about `SQLiteHelper` private attribute usage

## Scope

- `scripts/agent/commands/cmd_mcp.py`: change else branch to print usage
- `scripts/agent/commands/cmd_notes.py`: extract `_format_notes_table()` helper
- `scripts/agent/commands/cmd_debug.py`: constants for audit tail count and logger names
- `scripts/agent/commands/cmd_config.py`: comment on `_RAG_PATH`/`_SESSION_PATH` usage

## Assumptions

1. `cmd_tooling.py` already has clean responsibility (tool list + plan toggle); no code change needed.
2. `cmd_mcp.py` change: empty args prints usage; `"status"` sub-command shows the status table.
3. `cmd_notes.py` formatter extraction is a local refactor (no service needed for 3 simple methods).
4. `cmd_debug.py` constants: `_AUDIT_TAIL_LINES = 20`, `_LOGGER_NAMES = ("agent_repl", "orchestrator")`.
5. `cmd_config.py` private attribute usage: add inline comment, no behavior change.

## Implementation

### Target files

All modifications are small targeted edits.

### cmd_mcp.py — change default to usage

Before:
```python
async def _cmd_mcp(self, args: str = "") -> None:
    parts = args.strip().split(None, 1)
    sub = parts[0] if parts else ""
    if sub == "install":
        ...
    else:
        await self._cmd_mcp_status()
```

After:
```python
async def _cmd_mcp(self, args: str = "") -> None:
    parts = args.strip().split(None, 1)
    sub = parts[0] if parts else ""
    if sub == "install":
        name = parts[1].strip() if len(parts) > 1 else ""
        await self._cmd_mcp_install(name)
    elif sub in ("status", ""):
        if not sub:
            print("Usage: /mcp [status|install <name>]")
            print()
        await self._cmd_mcp_status()
    else:
        print(f"Unknown subcommand: {sub!r}. Usage: /mcp [status|install <name>]")
```

### cmd_notes.py — extract formatter

```python
def _format_notes_table(notes: list[dict]) -> list[str]:
    """Format notes as printable lines."""
    lines = [f"{'ID':>4}  {'Created':>19}  Content", "-" * 70]
    for n in notes:
        preview = n["content"][:41] + "..." if len(n["content"]) > 44 else n["content"]
        lines.append(f"{n['note_id']:>4}  {n['created_at'][:19]:>19}  {preview}")
    return lines
```

`_note_list` calls `_format_notes_table` and prints lines.

### cmd_debug.py — constants

```python
_AUDIT_TAIL_LINES = 20
_DEBUG_LOGGER_NAMES = ("agent_repl", "orchestrator")
```

Replace `lines[-20:]` → `lines[-_AUDIT_TAIL_LINES:]`
Replace hardcoded logger names in `verbose`/`normal` branches.

### cmd_config.py — comment

In `_print_rag_config()`, above `SQLiteHelper._ensure_config()`:
```python
# NOTE: _RAG_PATH/_SESSION_PATH are convention-private class attributes set by
# _ensure_config(). No public getter exists; direct access is intentional here.
```

## Validation plan

| Check | Command | Expected |
|---|---|---|
| mcp default | `grep "else:" scripts/agent/commands/cmd_mcp.py` | no bare status call |
| debug constants | `grep "_AUDIT_TAIL_LINES\|_DEBUG_LOGGER" scripts/agent/commands/cmd_debug.py` | present |
| Lint | `uv run ruff check scripts/agent/commands/` | 0 errors |
| Tests | `uv run pytest tests/ -q` | all pass |
