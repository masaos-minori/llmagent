# Implementation: session_message_repo.py

## Goal

Replace all `except Exception` handlers with `sqlite3.OperationalError` / `sqlite3.DatabaseError` and propagate failures to the session layer instead of silently logging.

## Scope

- Target: `scripts/agent/session_message_repo.py`
- Replace `except Exception` in `save()`, `save_many()`, `fetch_messages()` with `except sqlite3.Error`
- Remove `return None` and warning-only fallback from `fetch_messages`; raise instead
- `save()` and `save_many()` raise on DB failure instead of silently swallowing

## Assumptions

1. `AgentSession.save()` is the only caller of `SessionMessageRepository.save()`; it must be updated to handle `sqlite3.Error`.
2. `AgentSession.fetch_messages()` callers (`cmd_session.py`) already handle `None` return; they must be updated to catch `sqlite3.Error`.
3. `session.py` facade will be updated to propagate exceptions (see `session_py.md`).

## Implementation

### Target file

`scripts/agent/session_message_repo.py`

### Procedure

1. Add `import sqlite3` at the top.
2. In `save()`: replace `except Exception as e: logger.warning(...)` with `except sqlite3.Error as e: raise` (let the error propagate to the session facade).
3. In `save_many()`: same change.
4. In `fetch_messages()`: replace `except Exception as e: logger.warning(...) return None` with `except sqlite3.Error: raise`. Remove the `return None` fallback; return `[]` when `rows` is empty (keep existing behavior for empty result, but not for DB error).
5. Keep the `orjson.JSONDecodeError` handler for corrupt `tool_calls` JSON — this is an expected data error, not a bug.

### Method

Replace broad catches with `sqlite3.Error` (parent of `OperationalError`, `DatabaseError`, `IntegrityError`). No interface change to callers of this class from the session facade.

### Details

```python
import sqlite3

def save(self, role, content, tool_calls=None, tool_call_id=None) -> None:
    if self.session_id is None:
        return
    if role not in _VALID_ROLES:
        raise ValueError(f"Invalid role {role!r}")  # was: logger.warning + return
    tc_json = orjson.dumps(tool_calls).decode() if tool_calls else None
    with SQLiteHelper("session").open(write_mode=True) as db:
        db.execute("INSERT INTO messages ...", (...))
        db.commit()
    # sqlite3.Error propagates to caller

def fetch_messages(self, session_id: int) -> list[LLMMessage]:
    with SQLiteHelper("session").open(row_factory=True) as db:
        rows = db.fetchall("SELECT ... FROM messages WHERE session_id = ?", (session_id,))
    if not rows:
        return []
    # ... build messages list
```

Note: change `fetch_messages` return type from `list[LLMMessage] | None` to `list[LLMMessage]`.

## Validation plan

| Check | Tool | Target |
|---|---|---|
| Lint | `uv run ruff check scripts/agent/session_message_repo.py` | 0 errors |
| Type check | `uv run mypy scripts/` | no new errors |
| Tests | `uv run pytest tests/ -k "session_message"` | all pass |
