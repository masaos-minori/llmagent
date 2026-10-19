# SessionTitleService primary path lets sqlite3.Error from set_title propagate uncaught instead of triggering fallback

## Priority
Low

## Summary
Wrap the `set_title` call in `SessionTitleService.generate` so a database error is converted to `SessionTitleGenerationError`, matching the fallback path in `SessionTitleGen` and letting the LLM-title fallback trigger on DB failure as well as on LLM/HTTP failure.

## Background
`SessionTitleService.generate` calls the chat LLM, then persists the title via `AgentSession.set_title`. `set_title` performs DB writes and can raise `sqlite3.Error`. `SessionTitleGen.generate` (the command-layer generator) treats any `SessionTitleGenerationError` as a trigger for a local fallback title and wraps its own `set_title` call in a broad, logged `except`.

## Problem
In `SessionTitleService.generate`, the `set_title` call sits inside a `try` whose `except` clauses catch `SessionTitleGenerationError`, `httpx` errors, `ValueError`, and `(RuntimeError, OSError)`. `sqlite3.Error` matches none of these, so a DB failure while persisting the LLM-generated title escapes `generate` unconverted. `SessionTitleGen` only falls back on `SessionTitleGenerationError`, so the raw `sqlite3.Error` bypasses the fallback entirely instead of degrading gracefully to the input-based title.

## Reason for Change
The fallback is meant to be the safety net for any title-generation failure. The primary path currently has weaker error handling than the fallback: HTTP/parse failures degrade gracefully, but a DB write failure does not. Making `set_title` failures convert to `SessionTitleGenerationError` restores a single, consistent failure contract.

## Implementation Intent
Convert the `sqlite3.Error` raised by `set_title` inside `SessionTitleService.generate` into `SessionTitleGenerationError` (add an `except (sqlite3.Error)` clause before the generic handlers, or extend the final generic handler to include it). Do not change which failures are considered retryable; only ensure DB errors funnel through the same `SessionTitleGenerationError` that the fallback consumes.

## Target Files or Areas
- `scripts/agent/services/session_title.py` (`SessionTitleService.generate`)

## Required Changes
- Add handling so a `sqlite3.Error` from `set_title` becomes `SessionTitleGenerationError`.
- Keep the existing re-raise ordering (`SessionTitleGenerationError` first, then network/parse, then generic).

## Constraints
- Do not swallow the original cause; chain it with `from e`.
- Do not change behavior for already-handled failure types.

## Acceptance Criteria
- A DB error during `SessionTitleService.generate` raises `SessionTitleGenerationError`, not a raw `sqlite3.Error`.
- `SessionTitleGen.generate` then applies its fallback title as it does for other generation failures.

## Testing Expectations
- Add a test where `set_title` raises `sqlite3.Error` and assert `SessionTitleService.generate` raises `SessionTitleGenerationError`.
- `ruff` and `mypy` clean on touched files.

## Documentation Impact
None required.

## Out of Scope
- Changes to the fallback title logic in `SessionTitleGen`.
- Changes to `AgentSession.set_title` itself.

## Dependencies
- N/A: none

## Unresolved Questions
- Confirm whether DB errors during title generation should fall back to the input-based title (this issue assumes yes) or be surfaced to the user.

## AI Implementation Instruction
Add an `except (sqlite3.Error)` clause in `SessionTitleService.generate` that raises `SessionTitleGenerationError` chained from the cause, placed before the generic handler. Do not touch the fallback path or `set_title`. Keep the change minimal.

## Traceability
- **Workflow phase**: `python-code-review` + `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261019-202210
- **Related target files**: `scripts/agent/services/session_title.py`
