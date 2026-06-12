# Goal

Replace `str(message.get("content", "")).strip()` with an explicit isinstance
check that raises `SessionTitleGenerationError` when `content` is not a string.

# Scope

- `scripts/agent/services/session_title.py` — line 65

# Assumptions

1. `message` is already validated as `dict` at line 61. `message.get("content")`
   returns `Any` — could be `str`, `None`, or another type.
2. If `content` is `None` or empty string → existing `if not title:` check catches it.
   But `str(None)` produces `"None"` which passes the empty check silently.
3. If `content` is not `str` (e.g. `list` for tool_calls-only message) → raise
   `SessionTitleGenerationError` immediately.
4. The `SessionTitleGenerationError` is re-raised and handled by the caller.

# Implementation

## Target file

`scripts/agent/services/session_title.py`

## Procedure

Replace line 65:

```python
# Before
title = str(message.get("content", "")).strip()
if not title:
    raise SessionTitleGenerationError("LLM returned empty title")

# After
content_raw = message.get("content")
if not isinstance(content_raw, str):
    raise SessionTitleGenerationError(
        f"LLM title content must be str, got {type(content_raw).__name__}"
    )
title = content_raw.strip()
if not title:
    raise SessionTitleGenerationError("LLM returned empty title")
```

## Method

Replace one line with four lines. No logic change for the str→str path.

# Validation plan

- `grep -n "str(message\.get" scripts/agent/services/session_title.py` → 0 hits
- `uv run ruff check scripts/agent/services/session_title.py`
- `uv run mypy scripts/agent/services/session_title.py`
- `uv run pytest tests/ -k "session_title" --ignore=tests/test_create_schema.py -v`
