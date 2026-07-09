# Implementation: Add /undo compressed-summary warning

## Goal

Warn the user (both in log and REPL) when `/undo` targets a `[Conversation summary]` message, because rolling past it destroys the compressed context and prevents recovery of original messages.

## Scope

- `scripts/agent/services/models.py` — extend `UndoResult`
- `scripts/agent/services/undo_service.py` — add detection and warning
- `scripts/agent/commands/cmd_context.py` — surface warning in REPL

## Assumptions

- Compressed summary message `content` begins with `[Conversation summary]`.
- The warning is informational; undo still executes.

## Implementation

### Step 1: Extend `UndoResult`

Target file: `scripts/agent/services/models.py`

Procedure: Add `warning: str | None = None` field to the `UndoResult` dataclass.

Note: `UndoResult` is `frozen=True`; a field with a default value (`None`) is allowed.

### Step 2: Add detection and warning in `undo_service.py`

Target file: `scripts/agent/services/undo_service.py`

Procedure: In `undo_last_turn()`, after computing `cut_idx`, check if any removed message's `content` starts with `"[Conversation summary]"`. If so:
1. Call `logger.warning("Undo is targeting a compressed session summary; previous messages may not be recoverable.")`
2. Set `warning` on the returned `UndoResult`

Method: Iterate `ctx.conv.history[cut_idx:]`, check `m.get("content", "").startswith("[Conversation summary]")`.

Details:
```python
removed_messages = ctx.conv.history[cut_idx:]
has_summary = any(
    m.get("content", "").startswith("[Conversation summary]")
    for m in removed_messages
)
warning = None
if has_summary:
    warning = "/undo is targeting a compressed session summary; previous messages may not be recoverable."
    logger.warning(warning)
```

The `return UndoResult(n_removed=removed)` becomes `return UndoResult(n_removed=removed, warning=warning)`.

### Step 3: Surface warning in `cmd_context.py`

Target file: `scripts/agent/commands/cmd_context.py`

Procedure: After the undo call at line 126, check `result.warning` and display if set.

Method: Insert after line 129:
```python
if result.warning:
    self._out.write_no_data(f"[warn] {result.warning}")
```

Note: `OutputPort` has `write_no_data` but not `write_warning`. Using `write_no_data` with a `[warn]` prefix matches the task requirement.

### Step 4: Run validation

Target: all changed files

Procedure:
- `uv run python -m compileall -q scripts/`
- `uv run ruff check scripts/`
- `uv run mypy scripts/`
- `uv run pytest -v`

## Validation plan

1. Syntax check: `uv run python -m compileall -q scripts/`
2. Lint: `uv run ruff check scripts/`
3. Type check: `uv run mypy scripts/` (no new errors vs pre-existing)
4. Tests: `uv run pytest -v` (existing undo tests pass)
