# Implementation: Add diagnostic role support to session_message_repo.py (req 27 — Step 1)

## Goal

Add `_DIAGNOSTIC_ROLE` constant and `_diagnostic` parameter to `save()` so diagnostic messages bypass role validation and persist to DB without appearing in normal history retrieval.

## Scope

- `scripts/agent/session_message_repo.py`

## Assumptions

1. `_DIAGNOSTIC_ROLE = "diagnostic"` — underscore prefix signals internal use.
2. `save()` gains `_diagnostic: bool = False`; when True, role validation is skipped.
3. `fetch_messages()` currently returns ALL roles including diagnostic — callers that need only normal messages must filter. This is acceptable per the plan.
4. `save_many()` unchanged (not used for diagnostic messages).

## Implementation

### Target file

`scripts/agent/session_message_repo.py`

### Procedure

1. Add `_DIAGNOSTIC_ROLE` constant after `_VALID_ROLES`.
2. Add `_diagnostic: bool = False` parameter to `save()`.
3. Change role validation: skip when `_diagnostic=True`.

### Method

Edit tool.

### Details

```python
_VALID_ROLES: frozenset[str] = frozenset({"user", "assistant", "tool", "system"})
_DIAGNOSTIC_ROLE: str = "diagnostic"

def save(
    self,
    role: str,
    content: str,
    tool_calls: list[dict] | None = None,
    tool_call_id: str | None = None,
    _diagnostic: bool = False,
) -> None:
    """Persist a single message to DB under the current session.
    If _diagnostic=True, role validation is skipped (internal use only).
    """
    if self.session_id is None:
        return
    if not _diagnostic and role not in _VALID_ROLES:
        logger.warning("Invalid role %r; message not saved", role)
        return
    ...
```

## Validation plan

| Check | Tool | Target |
|---|---|---|
| Type check | `uv run mypy scripts/agent/session_message_repo.py` | no errors |
| Tests | `uv run pytest tests/test_session_message_repo.py -v` | all pass |
