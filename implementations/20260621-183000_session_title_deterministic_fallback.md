# Implementation: Deterministic Fallback and Visible Failure for Session Title Generation

## Goal

Ensure every session has a non-empty title even when LLM title generation fails, and make failures operator-visible. Two gaps remain after the 20260620-143558 implementation:

1. `SessionTitleService.generate()` does not wrap unexpected `Exception` types
2. `_session_list()` displays an empty string if `sr.title == ""` (DB-persisted edge case)

## Scope

**In-Scope:**
- `session_title.py`: add `except Exception` wrapper so ALL exception types become `SessionTitleGenerationError`
- `cmd_session.py`: change `elif sr.title is not None` → `elif sr.title` in `_session_list`
- `tests/test_session_title.py`: add test for unexpected exception wrapping
- `tests/test_agent_cmd_session.py`: add test for empty-string title in list display

**Out-of-Scope:**
- Redesigning `SessionTitleService` or replacing the background-task model
- Changing title truncation logic or constants
- Adding audit-event models or new logging infrastructure

## Assumptions

1. `asyncio.CancelledError` inherits from `BaseException` (Python 3.8+), so `except Exception` does NOT catch it — cancellation propagates correctly.
2. The only reachable path to an empty-string `sr.title` in the DB is a race or external direct DB write; the normal fallback path always sets a non-empty string.
3. `logger.warning` in `_generate_session_title` is already emitted for all `SessionTitleGenerationError` paths — no new log infrastructure needed.

## Unknowns & Gaps

| ID | Unknown | Evidence Missing | Resolution | Blocking |
|---|---|---|---|---|
| UNK-01 | Can `orjson.loads` raise `ValueError` not covered by `JSONDecodeError`? | `JSONDecodeError` is a subclass of `ValueError` — other `ValueError` sources not present in the try block | No action needed; existing except covers JSON path | False |
| UNK-02 | Does any existing test assert on `logger.warning` level (not just message)? | Test uses `AsyncMock(side_effect=SessionTitleGenerationError(...))` without asserting log level | Low risk; add the `except Exception` test without breaking existing level assertions | False |

## Implementation

### Target files

- `scripts/agent/services/session_title.py` — add `except Exception` wrapper (1-line change)
- `scripts/agent/commands/cmd_session.py` — change `elif sr.title is not None` to `elif sr.title` (1-line change)
- `tests/test_session_title.py` — add test for unexpected exception wrapping
- `tests/test_agent_cmd_session.py` — add test for empty-string title in list display

### Procedure

#### Step 1: Fix `session_title.py` — wrap unexpected exceptions

In the outer `try` block of `SessionTitleService.generate()`, after the existing `except (orjson.JSONDecodeError, KeyError)` block:

```python
except Exception as e:
    raise SessionTitleGenerationError(f"Unexpected error: {e}") from e
```

This covers any exception not already caught (e.g., `AttributeError`, `TypeError`).

#### Step 2: Fix `cmd_session.py` — guard empty-string title in list view

In `_session_list()`, change:
```python
elif sr.title is not None:
```
to:
```python
elif sr.title:
```

Empty string now falls to the `else: title_display = "(no title)"` branch.

#### Step 3: Add test — unexpected exception wrapping in `test_session_title.py`

New async test `test_generate_unexpected_exception_wrapped_as_title_error`:
- Mock `ctx.services.http.post` to raise `RuntimeError("boom")`
- Assert `SessionTitleGenerationError` is raised with "Unexpected error" in message

#### Step 4: Add test — empty-string title in list view in `test_agent_cmd_session.py`

New test `test_session_list_empty_string_title_displays_no_title`:
- Call `_session_list("")` with a session row where `title=""`
- Assert `write_table` received "(no title)" in the row data

### Method

- Minimal code changes (1 line each) in existing functions
- No new public API or interface changes
- Tests follow existing patterns in respective test files

### Details

- The `except Exception` wraps any unhandled exception, preserving the original as `__cause__` via `from e`
- The `elif sr.title` change is safe: empty string is falsy, so it falls to the else branch showing "(no title)"
- No existing test asserts on empty-string title display

## Validation plan

| Target | Test Strategy | Command | Expected |
|---|---|---|---|
| `session_title.py` unexpected exception | Unit — mock raises `RuntimeError` | `uv run pytest tests/test_session_title.py -v` | all pass |
| `cmd_session.py` empty title display | Unit — mock list returns `title=""` | `uv run pytest tests/test_agent_cmd_session.py -v` | all pass |
| Lint | Static | `uv run ruff check scripts/` | 0 errors |
| Type check | Static | `uv run mypy scripts/` | no new errors |
| Full suite | Regression | `uv run pytest -q` | no new failures |

## Risks

- **Risk:** `except Exception` in `session_title.py` masks a real programming error silently
  → **Mitigation:** the `logger.warning` in `cmd_session.py` already logs all fallback events; the original exception is preserved as `__cause__` on the wrapped `SessionTitleGenerationError`
- **Risk:** Changing `elif sr.title is not None` to `elif sr.title` breaks a test expecting empty-string display
  → **Mitigation:** grep confirms no test asserts empty-string title display; new test covers the fixed behavior
