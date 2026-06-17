# Implementation: session_message_repo.py — counters and strict mode

## Goal

Add skip counters and an optional strict mode to `SessionMessageRepository` so that
silent persistence skips become visible through logging and counters, and optionally
raise `RuntimeError` in strict mode.

## Scope

`scripts/agent/session_message_repo.py` only.

## Assumptions

1. Counters are per-repository-instance (per-session) attributes.
2. Strict mode is set at construction time and is immutable per instance.
3. `save()` already logs a warning for invalid role — we must also increment the counter there.
4. `save_many()` currently silently filters invalid roles; we add counting and logging.
5. `save_many()` currently silently no-ops when `session_id is None` with no log — we add a warning and counter.

## Implementation

### Target file

`scripts/agent/session_message_repo.py`

### Procedure

1. Add `strict_mode: bool = False` parameter and three counter attributes to `__init__`.
2. Update `save()`:
   - When `session_id is None`: increment `stat_skipped_no_session`, log warning, raise if strict.
   - When invalid role: increment `stat_skipped_invalid_role` (warning already present), raise if strict.
3. Update `save_many()`:
   - When `session_id is None`: increment `stat_skipped_no_session`, log warning, raise if strict.
   - After filtering invalid roles: increment `stat_skipped_invalid_role` by count of skipped rows, log warning.

### Method

Minimal, additive changes. Preserve all existing behavior when `strict_mode=False` (default).

### Details

```python
def __init__(self, session_id: int | None = None, *, strict_mode: bool = False) -> None:
    self.session_id = session_id
    self.strict_mode = strict_mode
    self.stat_skipped_no_session: int = 0
    self.stat_skipped_invalid_role: int = 0
```

`save()` changes (replace the two early-return blocks):

```python
def save(self, role, content, tool_calls=None, tool_call_id=None, _diagnostic=False):
    if self.session_id is None:
        self.stat_skipped_no_session += 1
        logger.warning("Persistence skipped: no session_id (role=%r)", role)
        if self.strict_mode:
            raise RuntimeError(f"Cannot save message: no session_id (strict mode)")
        return
    if not _diagnostic and role not in _VALID_ROLES:
        self.stat_skipped_invalid_role += 1
        logger.warning("Invalid role %r; message not saved", role)
        if self.strict_mode:
            raise RuntimeError(f"Cannot save message with invalid role {role!r} (strict mode)")
        return
    # ... existing DB insert logic unchanged
```

`save_many()` changes:

```python
def save_many(self, messages):
    if self.session_id is None or not messages:
        if self.session_id is None and messages:
            self.stat_skipped_no_session += 1
            logger.warning(
                "Persistence skipped: no session_id (save_many, %d messages)", len(messages)
            )
            if self.strict_mode:
                raise RuntimeError("Cannot save messages: no session_id (strict mode)")
        return
    invalid_count = sum(1 for role, _, _, _ in messages if role not in _VALID_ROLES)
    rows = [
        (self.session_id, role, content, _json_dumps(tc) if tc else None, tc_id)
        for role, content, tc, tc_id in messages
        if role in _VALID_ROLES
    ]
    if invalid_count:
        self.stat_skipped_invalid_role += invalid_count
        logger.warning("Persistence skipped: %d messages had invalid roles", invalid_count)
    if not rows:
        return
    # ... existing executemany logic unchanged
```

## Validation plan

```bash
uv run ruff format scripts/agent/session_message_repo.py
uv run ruff check scripts/agent/session_message_repo.py
uv run mypy scripts/agent/session_message_repo.py
uv run pytest tests/test_session_message_repo.py -v
```
