# Implementation: memory/injection.py + ingestion.py — remove broad exceptions

## Goal

1. `injection.py`: remove `except Exception: return []` from `on_session_start` and `on_user_prompt`.
2. `ingestion.py`: remove `except Exception` from `on_session_stop` and `_persist_entry`.
3. `repl.py`: wrap `on_session_stop` call to prevent REPL crash on memory failure.

## Scope

- `scripts/agent/memory/injection.py`
- `scripts/agent/memory/ingestion.py`
- `scripts/agent/repl.py` — add try/except around memory.on_session_stop call

## Assumptions

1. `injection.py` exception removal: `on_session_start` and `on_user_prompt` now propagate.
   Callers (`services.py` facade, `orchestrator.py`) must handle or propagate.
   Since `orchestrator.py` calls `on_user_prompt`, it needs a try/except to prevent turn failure.
2. `ingestion.py` exception removal: `on_session_stop` propagates failures.
   `repl.py:300` calls `await ctx.services.memory.on_session_stop(...)` in a `finally` block
   without try/except → REPL would terminate on failure. Add try/except there.
3. `orchestrator.py` already has try/except around `on_user_prompt` call (added earlier
   in the command layer refactoring? — check before assuming).
4. Keep entry-level logging (logger.exception) before re-raise so failures are observable.

## Implementation

### injection.py: on_session_start

```python
def on_session_start(self) -> list[str]:
    entries = self._retriever.top_semantic(...)
    if not entries:
        return []
    snippets = [...]
    logger.info("MemoryInjectionService.on_session_start: injecting %d entries", len(snippets))
    return snippets
    # No try/except — failures propagate
```

### injection.py: on_user_prompt

Remove the outer `try/except Exception` block. Keep empty-query early return.

### ingestion.py: on_session_stop

Remove `try/except Exception` wrapper. Add `logger.exception` before re-raise if needed.

### ingestion.py: _persist_entry

Remove `except Exception` wrapper (it has none currently — already clean after last refactor).

### repl.py: protect on_session_stop

```python
# In _run_repl_loop finally block:
if ctx.services.memory is not None:
    try:
        await ctx.services.memory.on_session_stop(...)
    except Exception:
        logger.exception("Memory on_session_stop failed; session data may be incomplete")
```

### orchestrator.py: check on_user_prompt protection

Already has try/except (added in previous commit). Verify; add if missing.

## Validation plan

| Check | Command | Target |
|---|---|---|
| Lint | `uv run ruff check scripts/agent/memory/injection.py scripts/agent/memory/ingestion.py scripts/agent/repl.py` | 0 errors |
| Type | `uv run mypy scripts/agent/memory/injection.py scripts/agent/memory/ingestion.py` | no new errors |
| Tests | `uv run pytest tests/test_memory_layer.py -x -v` | all pass |
| No broad except | `grep -n "except Exception" scripts/agent/memory/injection.py scripts/agent/memory/ingestion.py` | 0 hits |
