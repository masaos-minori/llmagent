# Remove or fix unreachable SQLITE_NOTFOUND 1017 fallback in AgentSession.start

## Priority
Medium

## Summary
`AgentSession.start()` checks `e.args[0] == 1017` on `sqlite3.OperationalError` to
detect a missing sessions table. `args[0]` is the error message string, so the
branch can never fire. Replace the dead comparison with the real extended error
code (`sqlite_errorcode` / `sqlite_errorname`) or remove the fallback, and cover
the decision with a test.

## Background
`scripts/agent/session.py` lines 140-147: after a `sqlite_master` pre-flight check,
an `INSERT INTO sessions` failure is inspected with
`err_code = e.args[0] if e.args else None; if err_code == 1017:` to raise
`SchemaMissingError`. The fallback was introduced as an edge-case guard per
`implementations/done/20260724-230132_session.py.md` ("Extended error code 1017
(SQLITE_NOTFOUND) uniquely identifies 'no such table' errors") — that claim is
false in this runtime.

Confirmed by reproduction (Evidence: confirmed, Confidence: High): a live
`INSERT` against a missing table raises `sqlite3.OperationalError` with
`args[0] == 'no such table: sessions'` and `sqlite_errorcode == 1` (SQLITE_ERROR),
not 1017. `sqlite3.Error.sqlite_errorcode` / `sqlite_errorname` (Python 3.11+) are
the attributes that carry the extended code.

## Problem
The 1017 branch is dead code. If the pre-flight check passes but the INSERT still
fails with a missing-table error (e.g. a concurrent schema change race), the user
gets a raw `OperationalError` instead of the actionable `SchemaMissingError`
("Run: bash deploy/init_db.sh") the branch was written to produce. The comment
also misleads readers into thinking extended codes are checked.

## Reason for Change
Dead error-handling code in the startup path hides the intended failure behavior
and contradicts the archived implementation document cited above. Fixing it now
prevents a future maintainer from "repairing" startup diagnostics around a branch
that never executes.

## Implementation Intent
Either:
- Compare against `getattr(e, "sqlite_errorcode", None)` (and/or
  `sqlite_errorname == "SQLITE_ERROR"` / message inspection) so the fallback can
  actually fire; or
- Delete the fallback and rely solely on the `sqlite_master` pre-flight check, if
  planning confirms the race scenario does not need dedicated handling.

Keep `SchemaMissingError` as the public failure contract for a missing sessions
schema. Do not otherwise change `start()` behavior (session row creation, repo
rebind, logging).

## Target Files or Areas
- scripts/agent/session.py
- tests/agent/ (session startup / schema-missing tests)

## Required Changes
- Fix or remove the `e.args[0] == 1017` comparison in `AgentSession.start()`.
- Update the accompanying comment so it matches the actual mechanism.
- Add a test that a missing sessions table raises `SchemaMissingError` with the
  actionable message (with the table actually absent, mocks aside).

## Constraints
- Python 3.13 runtime: `sqlite_errorcode` / `sqlite_errorname` are available.
- Do not swallow or broaden exception types beyond the existing
  `SchemaMissingError` / re-raise contract.
- No unrelated reformatting of `start()`.

## Acceptance Criteria
- No comparison of `args[0]` against an integer error code remains.
- A missing sessions table at `start()` yields `SchemaMissingError` (verified by a
  test against a real DB without the table).
- All existing session tests pass.

## Testing Expectations
- Unit test: real temp DB without the sessions table → `SchemaMissingError`.
- Unit test (if the fallback is kept): error path with the extended code correctly
  detected.
- `uv run ruff check` and `uv run mypy --no-namespace-packages` on the changed file.

## Documentation Impact
No documentation update required if behavior is unchanged (pre-flight check already
produces `SchemaMissingError`). If a Needs Confirmation item surfaces about the
concurrent-drop race, record it in the session data-layer doc's Known Issues only if
the planning phase confirms the scenario.

## Out of Scope
- The repo-binding fix in `AgentSession` (tracked by
  `issues/20261025-115501_sess001_repo-staleness-after-restore.md`).
- Schema initialization scripts (`deploy/init_db.sh`).

## Dependencies
- `issues/20261025-115501_sess001_repo-staleness-after-restore.md` — same file; fix
  sess001 first and re-verify this issue's line references against the updated
  source before implementing.

## Unresolved Questions
- Which contract is desired for a missing-table error that arrives after the
  pre-flight check: `SchemaMissingError` or a plain `sqlite3.OperationalError`?
  不明 — decide in planning; the fix-or-remove choice depends on it.
- Whether `SchemaMissingError` handling elsewhere (REPL fatal path) assumes the
  fallback still exists. 不明 — verify during planning.

## AI Implementation Instruction
Touch only the error-code fallback block and its tests. Do not restructure
`start()`. Write the failing test first. If planning chooses deletion, confirm with
a test that the pre-flight path alone still raises `SchemaMissingError`.

## Traceability
- **Workflow phase**: python-code-review
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261025-115550
- **Related target files**: scripts/agent/session.py, tests/agent/ (session startup / schema-missing tests)
