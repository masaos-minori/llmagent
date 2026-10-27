# Report failure when /session rename cannot store the title

## Priority
Medium

## Summary
`/session rename` prints "Session renamed" even when `set_title` did nothing
because there is no active session id. Make the command report the failed rename
instead of a false success.

## Background
From a python-code-review pass over the REPL command path (finding F-009).
Evidence (Explicit in code):
- `scripts/agent/commands/cmd_session.py` calls `ctx.session.set_title(title)` and
  then unconditionally writes the success line.
- `scripts/agent/session.py` `set_title` returns silently when `self._session_id`
  is `None` — no DB row exists to update.
- Related earlier work on `set_title` (title truncation cap, archived
  `issues/done/20261019-202130_sess002_set_title-truncation-cap-50-inconsistent-with-session_title_max_chars-32-used-by-fallback-and-list-display.md`)
  addressed length, not the no-session no-op; this finding was re-verified against
  current source.

## Problem
With no active session row (e.g. before the first save, or after certain startup
failures), the user receives "Session renamed: 'x'" while nothing is persisted; the
next list/load shows the old title. Misleading success feedback.

## Reason for Change
Small fix that removes a false-success path in a user-facing command; false success
messages erode trust in all other success lines.

## Implementation Intent
Make the storage layer report the outcome (`set_title` returns a bool or raises a
specific error) and have the command layer map it to success vs. validation-error
output. No change to title parsing or truncation semantics.

## Target Files or Areas
- `scripts/agent/session.py` (`set_title`)
- `scripts/agent/commands/cmd_session.py` (rename branch)

## Required Changes
- `set_title` signals "no active session" explicitly.
- Rename branch prints a validation error (and usage hint) when nothing was
  renamed.
- Regression test for the no-session case.

## Constraints
- Keep the current success message format for real renames (tests and users rely on
  it).
- Do not change title truncation rules.

## Acceptance Criteria
- Test: rename with `session_id=None` → failure output, no success line.
- Test: normal rename unchanged.
- `mypy`/`ruff` pass.

## Testing Expectations
- Unit tests for both branches of `set_title` outcome.
- Command-level test asserting the printed line for the no-session case.

## Documentation Impact
Not required beyond the command usage doc if the error message follows the existing
validation-error pattern.

## Out of Scope
- Title generation/fallback logic.
- Auto-creating a session row on rename.

## Dependencies
- N/A: none

## Unresolved Questions
- N/A: none

## AI Implementation Instruction
Change only `set_title`'s return contract and the rename branch's output mapping;
keep all other `set_title` call sites working (check callers before changing the
signature). Do not auto-create sessions as a side effect of rename.

## Traceability
- **Workflow phase**: `python-code-review`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261026-225105
- **Related target files**: `scripts/agent/session.py`, `scripts/agent/commands/cmd_session.py`
