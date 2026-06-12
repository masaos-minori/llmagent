# Goal

Replace `str(r.get("created_at", ""))` in `cmd_session.py` with an explicit
isinstance check, and apply the same validation to `int(r["session_id"])` and
`bool(r.get("is_current", False))` for consistency.

# Scope

- `scripts/agent/commands/cmd_session.py` — lines 73–81 (session_rows list comprehension)

# Assumptions

1. `AgentSession.list_sessions()` returns `list[dict]` where each dict has:
   - `session_id`: int (sqlite3 returns INTEGER as int)
   - `created_at`: str | None (DB TEXT, nullable)
   - `title`: str | None
   - `is_current`: bool (derived from comparison in AgentSession)
2. For `created_at`: if None → use `""`. If str → use as-is.
   If unexpected type → raise `TypeError`.
3. `session_id` should always be int from sqlite3. Keep `int()` cast but guard
   against non-int types.
4. `is_current` should always be bool. Keep `bool()` cast but guard non-bool.

# Implementation

## Target file

`scripts/agent/commands/cmd_session.py`

## Procedure

Replace the list comprehension (lines 73–81) with an extracted helper function:

```python
def _to_session_row(r: dict, ctx_session_id: int | None) -> SessionRow:
    sid = r["session_id"]
    if not isinstance(sid, int):
        raise TypeError(f"session_id must be int, got {type(sid).__name__}")
    ca = r.get("created_at")
    if ca is not None and not isinstance(ca, str):
        raise TypeError(f"created_at must be str or None, got {type(ca).__name__}")
    created_at = ca if ca is not None else ""
    is_current = r.get("is_current")
    if is_current is not None and not isinstance(is_current, bool):
        raise TypeError(f"is_current must be bool or None, got {type(is_current).__name__}")
    return SessionRow(
        session_id=sid,
        title=r.get("title"),
        created_at=created_at,
        is_current=bool(is_current) if is_current is not None else False,
    )
```

Then use it in the list comprehension:
```python
session_rows = [_to_session_row(r, None) for r in raw_rows]
```

If the helper is module-level or inlined, pick the simplest approach. Inline
is fine since it's one call site.

Alternatively (simpler inline approach):
```python
session_rows = []
for r in raw_rows:
    ca = r.get("created_at")
    if ca is not None and not isinstance(ca, str):
        raise TypeError(f"created_at must be str, got {type(ca).__name__}")
    session_rows.append(
        SessionRow(
            session_id=r["session_id"],
            title=r.get("title"),
            created_at=ca if ca is not None else "",
            is_current=bool(r.get("is_current", False)),
        )
    )
```

## Method

Replace str(r.get("created_at", "")) with explicit None → "" + isinstance check.
Simplest: inline isinstance guard, no helper needed.

# Validation plan

- `grep -n "str(r\.get" scripts/agent/commands/cmd_session.py` → 0 hits
- `uv run ruff check scripts/agent/commands/cmd_session.py`
- `uv run mypy scripts/agent/commands/cmd_session.py`
- `uv run pytest tests/test_agent_cmd_session.py -v`
