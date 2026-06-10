# Implementation: db/tool_results.py + cmd_tooling.py — reraise exceptions, remove full_text from list_recent

## Goal

1. `ToolResultStore.store()` / `get()` / `list_recent()`: log + reraise all exceptions
   (no more silent failure).
2. `list_recent()`: remove `full_text` from the SELECT; return only `{id, tool_name, summary, is_error}`.
3. `cmd_tooling.py` `/tool list` display: update to use `summary` instead of `full_text`.
4. `agent/tool_runner.py` and `orchestrator.py`: wrap `store()` calls in try/except so that
   a DB error does not crash the REPL.
5. Add tests for the reraise behaviour in `tests/test_tool_result_store.py`.

## Scope

- `scripts/db/tool_results.py` — primary
- `scripts/agent/commands/cmd_tooling.py` — line 35 (`full_text` reference in list view)
- `scripts/agent/tool_runner.py` — wrap `store()` call
- `scripts/agent/orchestrator.py` — wrap `store()` call
- `tests/test_tool_result_store.py` — add reraise tests

## Assumptions

1. `store()` reraise: callers in `tool_runner.py` and `orchestrator.py` currently do not
   catch the exception. Wrapping them with try/except (log + continue) is needed to avoid
   crashing the REPL on DB errors.
2. `get()` reraise: callers in `cmd_tooling.py` (`/tool show`) already display error messages;
   re-throwing lets `cmd_tooling.py` handle it. Check that `/tool show` has its own try/except.
3. `list_recent()` reraise: caller in `cmd_tooling.py` (`/tool list`) needs a try/except too.
4. Removing `full_text` from `list_recent()` result: `cmd_tooling.py:35` prints
   `len(entry['full_text'])` chars — replace with `len(entry.get('summary') or '')` or just
   remove the char count display.
5. `get()` still returns `full_text` (used by `/tool show <id>`). Do not change `get()` SELECT.

## Implementation

### Target file

`scripts/db/tool_results.py`

### Procedure

1. In `store()`: change `except Exception: logger.exception(...); return None` to
   `except Exception: logger.exception(...); raise`.
   Return type changes from `int | None` to `int` (always returns on success, raises on failure).

2. In `get()`: change `except Exception: logger.exception(...); return None` to
   `except Exception: logger.exception(...); raise`.
   Return type: keep `dict | None` (None still returned when row not found).

3. In `list_recent()`: change SELECT to exclude `full_text`:
   ```sql
   SELECT id, tool_name, summary, is_error
   FROM tool_results WHERE session_id = ? ORDER BY id DESC LIMIT ?
   ```
   Change `except Exception: logger.exception(...); return []` to reraise.

4. In `cmd_tooling.py:35`: replace `len(entry['full_text'])` with `len(entry.get('summary') or '')`.

5. In `tool_runner.py`: wrap `result_id = ctx.tool_result_store.store(...)` in try/except:
   ```python
   try:
       result_id = ctx.tool_result_store.store(...)
   except Exception:
       logger.warning("ToolResultStore.store failed; result not persisted")
       result_id = None
   ```

6. In `orchestrator.py`: wrap the `ctx.tool_result_store.store(...)` call similarly.

### Method

Direct textual edit for all files.

### Details

`list_recent()` SELECT after change:
```python
rows = db.fetchall(
    "SELECT id, tool_name, summary, is_error"
    " FROM tool_results"
    " WHERE session_id = ?"
    " ORDER BY id DESC LIMIT ?",
    (session_id, n),
)
```

`store()` return type update:
```python
def store(...) -> int | None:  # keep | None for callers that check it
```
Actually keep `int | None` return type — on exception it raises, so None is never returned.
But to avoid breaking type annotations downstream, keep `int | None` and change only the
exception handling behaviour.

## Validation plan

| Check | Command | Target |
|---|---|---|
| Lint | `uv run ruff check scripts/db/tool_results.py scripts/agent/commands/cmd_tooling.py` | 0 errors |
| Type | `uv run mypy scripts/db/tool_results.py` | no new errors |
| Tests | `uv run pytest tests/test_tool_result_store.py -x -v` | all pass |
| No full_text in list | `grep -n "full_text" scripts/db/tool_results.py` | only in `get()` SELECT |
| No swallowed exc | `grep -A2 "except Exception" scripts/db/tool_results.py` | each has `raise` |
