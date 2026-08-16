# Implementation Procedure: Separate session-not-found vs no-messages error paths

## Goal

Distinguish between "session does not exist" and "session exists but has no messages" in `restore_session()`, enabling precise error reporting and differentiated caller handling.

## Scope

- Add `SessionNoMessagesError` exception class in `scripts/agent/services/exceptions.py`
- Modify `fetch_messages()` in `scripts/agent/session_message_repo.py` to return `(messages, session_found)` tuple
- Update `fetch_messages()` wrapper in `scripts/agent/session.py` to propagate the tuple return type
- Update `restore_session()` in `scripts/agent/services/session_restore.py` to use distinct error messages

## Assumptions

1. A `sessions` table exists with `session_id INTEGER PRIMARY KEY AUTOINCREMENT` column (confirmed in `scripts/agent/session.py:122`)
2. Querying `sessions` table to determine existence is acceptable overhead (single index lookup via PRIMARY KEY)
3. Callers currently expect `fetch_messages()` to raise `SessionNotFoundError` — they need updating to catch both exception types
4. Test mocks (`ctx.session.fetch_messages.return_value`) will need adjustment to return tuples instead of plain lists

## Design decisions

- `SessionNoMessagesError` inherits from `RuntimeError` (same base as `SessionNotFoundError`), NOT from `SessionNotFoundError`. This allows callers to catch either individually or catch both via `except RuntimeError`. If callers want uniform handling, they can catch `RuntimeError` or explicitly catch both.
- The `sessions` table check uses `SELECT 1 FROM sessions WHERE session_id = ?` — minimal query, leverages PRIMARY KEY index, no measurable latency impact.

## Alternatives considered

1. **Inherit `SessionNoMessagesError` from `SessionNotFoundError`**: Would allow single `except SessionNotFoundError` clause to catch both. Drawback: semantic mismatch — "no messages" is not a subset of "not found".
2. **Return sentinel value `None` instead of tuple**: Would break existing callers silently. Tuple return is explicit and type-safe.
3. **Add separate `session_exists()` method**: Adds API surface area. Combining existence check into `fetch_messages()` reduces round-trips.

## Compatibility considerations

- Breaking change: all callers must be updated to handle the new tuple return type
- Two production callers identified:
  - `scripts/agent/session.py:105` — wrapper method, propagates tuple unchanged
  - `scripts/agent/services/session_restore.py:31` — unpacks tuple, raises appropriate exception
- No other production callers outside `scripts/` directory

## Security considerations

N/A — no security implications. Only changes error classification logic.

## Rollback considerations

- Revert source code changes to restore original `fetch_messages()` signature
- Remove `SessionNoMessagesError` class from exceptions.py
- Restore `restore_session()` to original error message: `"Session {session_id} not found or has no messages."`

## Validation plan

- Unit test for `fetch_messages()` returning `(msgs, True)` when session exists with messages
- Unit test for `fetch_messages()` returning `([], True)` when session exists but has no messages
- Unit test for `fetch_messages()` returning `([], False)` when session does not exist
- Integration test verifying `restore_session()` raises `SessionNotFoundError` for non-existent session
- Integration test verifying `restore_session()` raises `SessionNoMessagesError` for empty session
- Full test suite run (`uv run pytest`) to ensure no regressions across all `fetch_messages()` call sites

## Out of scope

- Modifying `fetch_messages()` to accept optional `check_existence` flag
- Adding migration scripts for schema changes
- Updating documentation files (`docs/*.md`)
- Changes to `AgentSession.start()` or other session lifecycle methods

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: requires/20260815-161935_require.md
- Source plan: plans/20260815-175147_plan.md
- Source implementation procedure: N/A
- Generated at: 20260816-073647
- Related target files: scripts/agent/session_message_repo.py, scripts/agent/session.py, scripts/agent/services/session_restore.py, scripts/agent/services/exceptions.py

---

## Implementation

### Target file: `scripts/agent/services/exceptions.py`

#### Procedure

1. Add `SessionNoMessagesError(RuntimeError)` class after `SessionNotFoundError` definition (after line 38)

#### Method

Append new exception class definition to the file.

#### Details

```python
class SessionNoMessagesError(RuntimeError):
    """Raised when a requested session exists but has no messages."""
```

Insert after line 38 (the `SessionNotFoundError` docstring closing line).

---

### Target file: `scripts/agent/session_message_repo.py`

#### Procedure

1. Read `scripts/agent/session.py` around line 122 to confirm `sessions` table schema and index availability
2. Modify `fetch_messages()` method to first check if session exists in `sessions` table
3. Return `(messages, session_found)` tuple instead of just `list[LLMMessage]`

#### Method

Modify the `fetch_messages` method body to add existence check before querying messages table.

#### Details

Current method (line 147-185):
```python
def fetch_messages(self, session_id: int) -> list[LLMMessage]:
    """Fetch and parse messages for a session from DB.

    Returns a list of message dicts (role/content/tool_calls) in insertion order.
    Returns [] if no messages exist. Raises sqlite3.Error on DB failure.
    """
    with SQLiteHelper("session").open(row_factory=True) as db:
        rows = db.fetchall(
            "SELECT message_id, role, content, tool_calls, tool_call_id"
            " FROM messages WHERE session_id = ? ORDER BY message_id",
            (session_id,),
        )
    ...
    return messages
```

New method:
```python
def fetch_messages(self, session_id: int) -> tuple[list[LLMMessage], bool]:
    """Fetch and parse messages for a session from DB.

    Returns a tuple of (messages, session_found).
    - messages: list of message dicts (role/content/tool_calls) in insertion order.
      Empty list if no messages exist for this session.
    - session_found: True if session exists in the sessions table, False otherwise.
    Returns ([], False) when session does not exist.
    Returns ([], True) when session exists but has no messages.
    Raises sqlite3.Error on DB failure.
    """
    with SQLiteHelper("session").open(row_factory=True) as db:
        row = db.fetchone(
            "SELECT 1 FROM sessions WHERE session_id = ?",
            (session_id,),
        )
        session_found = row is not None
    if not session_found:
        return ([], False)
    rows = db.fetchall(
        "SELECT message_id, role, content, tool_calls, tool_call_id"
        " FROM messages WHERE session_id = ? ORDER BY message_id",
        (session_id,),
    )
    ...
    return (messages, True)
```

Key changes:
- Line 147: Change return type annotation from `list[LLMMessage]` to `tuple[list[LLMMessage], bool]`
- Lines 148-151: Update docstring to describe tuple return
- After line 152 (opening DB connection): Add `SELECT 1 FROM sessions WHERE session_id = ?` check
- After line 158 (before `if not rows:`): Add early return `return ([], False)` when session not found
- Line 185: Change `return messages` to `return (messages, True)`

---

### Target file: `scripts/agent/session.py`

#### Procedure

1. Update `fetch_messages()` wrapper method to propagate the tuple return type

#### Method

Change return type annotation and docstring of the wrapper method.

#### Details

Current method (line 103-105):
```python
def fetch_messages(self, session_id: int) -> list[LLMMessage]:
    """Fetch messages for a session from DB. Returns [] when session has no messages."""
    return self._message_repo.fetch_messages(session_id)
```

New method:
```python
def fetch_messages(self, session_id: int) -> tuple[list[LLMMessage], bool]:
    """Fetch messages for a session from DB.

    Returns a tuple of (messages, session_found).
    - messages: list of message dicts in insertion order. Empty list if none.
    - session_found: True if session exists in the sessions table, False otherwise.
    """
    return self._message_repo.fetch_messages(session_id)
```

Key changes:
- Line 103: Change return type annotation
- Line 104: Update docstring to describe tuple return

---

### Target file: `scripts/agent/services/session_restore.py`

#### Procedure

1. Import `SessionNoMessagesError` from exceptions module
2. Unpack the tuple returned by `fetch_messages()`
3. Raise `SessionNotFoundError` when session not found
4. Raise `SessionNoMessagesError` when session exists but has no messages

#### Method

Modify the `restore_session` function to handle the new tuple return type.

#### Details

Current code (lines 31-35):
```python
messages = ctx.session.fetch_messages(session_id)
if not messages:
    raise SessionNotFoundError(
        f"Session {session_id} not found or has no messages."
    )
```

New code:
```python
messages, session_found = ctx.session.fetch_messages(session_id)
if not session_found:
    raise SessionNotFoundError(f"Session {session_id} not found.")
if not messages:
    raise SessionNoMessagesError(f"Session {session_id} has no messages.")
```

Key changes:
- Line 31: Unpack tuple: `messages, session_found = ctx.session.fetch_messages(session_id)`
- Line 32: Replace `if not messages:` with `if not session_found:`
- Line 33: Update error message to remove "or has no messages" ambiguity
- Line 34: Add new `if not messages:` branch raising `SessionNoMessagesError`

Also update import statement (line 15):
```python
from agent.services.exceptions import SessionNotFoundError, SessionNoMessagesError
```

And update docstring (line 27-29):
```python
"""Restore session: rebuild history, switch session ID, reset stats.

Raises SessionNotFoundError when the session does not exist.
Raises SessionNoMessagesError when the session exists but has no messages.
"""
```
