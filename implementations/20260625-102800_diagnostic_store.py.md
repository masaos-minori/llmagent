# diagnostic_store.py — add convenience methods and fetch_by_kind

**Plan:** `plans/20260625-094407_plan.md` (req #65)
**Target:** `scripts/agent/diagnostic_store.py`

## What to add

Add 4 methods after `save_serialization_event()` (after line 74).

### `save_partial_completion()`

```python
def save_partial_completion(
    self,
    session_id: int | None,
    turn: int,
    reason: str,
    content_length: int,
) -> None:
    """Persist a partial LLM completion event to session_diagnostics."""
    content = orjson.dumps(
        {
            "turn": turn,
            "reason": reason,
            "content_length": content_length,
        }
    ).decode()
    self.save(session_id=session_id, kind="partial_completion", content=content)
```

### `save_transport_failure()`

```python
def save_transport_failure(
    self,
    session_id: int | None,
    tool_name: str,
    server_key: str,
    error_msg: str,
) -> None:
    """Persist a transport-level tool execution failure."""
    content = orjson.dumps(
        {
            "tool_name": tool_name,
            "server_key": server_key,
            "error": error_msg,
        }
    ).decode()
    self.save(session_id=session_id, kind="transport_failure", content=content)
```

### `save_loop_guard_hint()`

```python
def save_loop_guard_hint(
    self,
    session_id: int | None,
    reason: str,
    turn_count: int,
) -> None:
    """Persist a tool loop guard hint (cycle or dedup threshold exceeded)."""
    content = orjson.dumps(
        {
            "reason": reason,
            "turn_count": turn_count,
        }
    ).decode()
    self.save(session_id=session_id, kind="loop_guard_hint", content=content)
```

### `fetch_by_kind()`

```python
def fetch_by_kind(self, session_id: int, kind: str) -> list[dict[str, Any]]:
    """Return diagnostics for a specific kind, newest first."""
    with SQLiteHelper("session").open(row_factory=True) as db:
        rows = db.fetchall(
            "SELECT id, session_id, kind, content, created_at"
            " FROM session_diagnostics WHERE session_id = ? AND kind = ?"
            " ORDER BY created_at DESC",
            (session_id, kind),
        )
    return [dict(r) for r in rows]
```

## Validation

```
ruff check scripts/agent/diagnostic_store.py
mypy scripts/agent/diagnostic_store.py
uv run pytest tests/test_diagnostic_store.py -q
```
