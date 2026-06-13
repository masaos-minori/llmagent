# Implementation: agent/repl.py + agent/orchestrator.py — pinned note injection + turn-level note injection

## Goal

Replace full-note injection in `repl.py:_setup_initial_prompt()` with pinned-only injection; add `_handle_note_injection()` to `orchestrator.py` and call it from `_process_turn()`.

## Scope

- `scripts/agent/repl.py` — `_setup_initial_prompt()` lines 282-287: change `get_all_note_contents()` → `get_pinned_notes()`
- `scripts/agent/orchestrator.py` — add `_handle_note_injection()` method; call from `_process_turn()` after `_handle_memory_injection()`

## Assumptions

- `session.get_pinned_notes()` is available (implemented in previous step)
- `session.search_notes()` is available (implemented in previous step)
- `ctx.cfg.tool.auto_inject_notes` is the existing guard flag
- `_handle_memory_injection()` pattern in orchestrator.py is the reference implementation
- `_memory_injected` flag is used (not `_note_injected`) so `undo_service.py` can remove injected messages on `/undo`
- `limit=3` to limit history accumulation per turn (Risk 4 mitigation)
- `_process_turn()` calls `_handle_memory_injection(line)` at line 165-168

## Implementation

### Target file

- `scripts/agent/repl.py`
- `scripts/agent/orchestrator.py`

### Procedure

1. Locate `_setup_initial_prompt()` in `repl.py` around line 282
2. Replace the 5-line full-note injection block with pinned-note injection
3. Locate `_handle_memory_injection()` in `orchestrator.py` as the reference pattern
4. Add `_handle_note_injection()` method after it
5. Add `await self._handle_note_injection(line)` after `_handle_memory_injection(line)` in `_process_turn()`

### Method

- Edit tool for both files
- grep to confirm `get_all_note_contents` removed from repl.py after edit

### Details

**`repl.py` — _setup_initial_prompt() change:**
```python
# Before (lines 282-287 approx)
if ctx.cfg.tool.auto_inject_notes:
    note_texts = ctx.session.get_all_note_contents()
    if note_texts:
        notes_block = "\n\n[Notes]\n" + "\n".join(f"- {t}" for t in note_texts)
        initial_prompt = initial_prompt + notes_block

# After
if ctx.cfg.tool.auto_inject_notes:
    pinned_notes = ctx.session.get_pinned_notes()
    if pinned_notes:
        notes_block = "\n\n[Pinned Notes]\n" + "\n".join(
            f"- {n['content']}" for n in pinned_notes
        )
        initial_prompt = initial_prompt + notes_block
```

**`orchestrator.py` — _handle_note_injection() new method:**
```python
async def _handle_note_injection(self, line: str) -> None:
    """Search notes by current query and inject relevant ones into history."""
    ctx = self._ctx
    if not ctx.cfg.tool.auto_inject_notes:
        return
    notes = ctx.session.search_notes(line, limit=3)
    if not notes:
        return
    note_block = "[Relevant Notes]\n" + "\n".join(
        f"- {n['content']}" for n in notes
    )
    ctx.conv.history.append(
        {
            "role": "system",
            "content": note_block,
            "_memory_injected": True,  # type: ignore[typeddict-unknown-key]
        }
    )
```

**`orchestrator.py` — _process_turn() addition:**
```python
# Before
await self._handle_memory_injection(line)
self._append_user_message(line)

# After
await self._handle_memory_injection(line)
await self._handle_note_injection(line)
self._append_user_message(line)
```

## Validation plan

- `grep "get_all_note_contents" scripts/agent/repl.py` — 0 matches
- `grep "_handle_note_injection" scripts/agent/orchestrator.py` — 2 matches (definition + call)
- `uv run mypy scripts/agent/repl.py scripts/agent/orchestrator.py` — 0 new errors
- `uv run pytest tests/test_orchestrator.py -v` — no new failures
- `uv run ruff check scripts/agent/repl.py scripts/agent/orchestrator.py` — 0 errors
