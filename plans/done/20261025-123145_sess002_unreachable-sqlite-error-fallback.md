# sess002 — Remove or fix unreachable SQLITE_NOTFOUND 1017 fallback in AgentSession.start

**Source issue**: `issues/20261025-115550_sess002_unreachable-sqlite-error-fallback.md`

> Path A (small bug fix, 2 target files, single module). All 22 sections kept; some
> collapsed per the Path A rule. Verification: issue claims independently reproduced
> on this runtime (2026-10-25): missing-table INSERT raises
> `sqlite3.OperationalError` with `args[0] == 'no such table: sessions'` (a string) and
> `sqlite_errorcode == 1` / `sqlite_errorname == 'SQLITE_ERROR'` — never 1017.
> Confidence: High.

## Goal

Make the missing-sessions-table error path in `AgentSession.start()` actually
reachable and honest: no `args[0] == 1017` comparison remains, and a missing sessions
table yields `SchemaMissingError` with the actionable message, proven by real-DB tests.

## Priority

Medium (issue-stated). Dead error-handling code in the startup path; misleading
comment; no current user-visible breakage because the pre-flight check already covers
the normal missing-schema case.

## Scope

In scope:
- `scripts/agent/session.py` — the `except sqlite3.OperationalError` fallback block in
  `start()` (lines 140-147 at audit time) and its comment.
- `tests/agent/test_agent_session.py` — real-DB tests for both error paths.

Out of scope (issue-stated, unchanged):
- The repo-binding fix (sess001; must land first — same file, see Risks).
- `start()` session-row creation, repo rebind, logging behavior.
- Schema initialization scripts (`deploy/init_db.sh`).

## Background

The 1017 fallback was introduced per `implementations/done/20260724-230132_session.py.md`
with the claim "Extended error code 1017 (SQLITE_NOTFOUND) uniquely identifies 'no
such table' errors" (line 13 of that file, verified). The claim is false on Python
3.13/sqlite in this runtime: measured `sqlite_errorcode == 1` (`SQLITE_ERROR`) for
"no such table". `e.args[0]` is the message string, so `err_code == 1017` can never
be true. `sqlite3.Error.sqlite_errorcode` / `sqlite_errorname` (Python 3.11+) carry
the real extended code and are settable on exception instances (measured).

## Problem

`if err_code == 1017:` (session.py line 143) is dead code: it compares a message
string against an integer. If an INSERT fails with a missing-table error after the
pre-flight check (schema-change race), the user gets a raw `OperationalError` instead
of the actionable `SchemaMissingError` ("Run: bash deploy/init_db.sh"). The comment
misleads readers into thinking extended codes are checked.

## Reason for Change

Confirmed dead branch (measured repro). Fixing it now prevents a future maintainer
from "repairing" startup diagnostics around a branch that never executes, and aligns
the source with the `SchemaMissingError` failure contract documented in the docstring.

## Implementation Intent

Fix the comparison rather than delete the fallback (decision recorded in Design):
detect the missing-table error via the real attributes (`sqlite_errorcode` /
message content), keep the re-raise for every other `OperationalError`, and update
the comment to match the actual mechanism.

## Requirements

| ID | Requirement | Priority | Target |
|---|---|---|---|
| REQ-001 | No comparison of `args[0]` against an integer error code remains in `start()`. | must | scripts/agent/session.py |
| REQ-002 | An INSERT-time missing-table `OperationalError` (after pre-flight) raises `SchemaMissingError` with the actionable message; all other `OperationalError`s re-raise unchanged. | must | scripts/agent/session.py |
| REQ-003 | A real DB without the sessions table makes `start()` raise `SchemaMissingError` (pre-flight path), covered by a test with no error mocking. | must | tests/agent/test_agent_session.py |
| REQ-004 | The fallback decision is covered by a test using a genuine `sqlite3.OperationalError` captured from a real missing-table INSERT. | must | tests/agent/test_agent_session.py |
| REQ-005 | `SchemaMissingError` remains the public failure contract; REPL handling (`repl_input_loop.py:90`) unchanged; `start()` otherwise unchanged. | must | scripts/agent/session.py |

## Implementation Target Files

> One row per directly affected file. Contract frozen in "Exports to Keep".

| File | Action | Contract / Exports to Keep |
|---|---|---|
| scripts/agent/session.py | modify | `SchemaMissingError(RuntimeError)` public; `start()` signature, pre-flight check, session-row creation, `self.session_id` assignment, repo rebind, commit, logging unchanged. Only the `except sqlite3.OperationalError` block body + comment change. Exception contract: `SchemaMissingError` for missing sessions schema; re-raise for everything else. |
| tests/agent/test_agent_session.py | modify | Existing `_FakeSQLiteHelper` in-memory pattern and current `start()` tests unchanged; add the two new tests below. |

Not edited (verified): `scripts/agent/repl_input_loop.py` (catches
`SchemaMissingError` generically at line 90 — does not depend on the fallback
existing; resolves the issue's Unresolved Question 2), `implementations/done/`
(frozen history), docs (see Documentation Impact).

## Reference Files

- `scripts/agent/session.py:124-153` — `start()`; fallback block lines 140-147.
- `scripts/agent/repl_input_loop.py:15,90` — `SchemaMissingError` catch site.
- `tests/agent/test_agent_session.py:54` (`_FakeSQLiteHelper`) — real in-memory SQLite
  connection behind the SQLiteHelper facade — pattern for REQ-003 test. NOTE (2026-10-25
  re-verification): the plan's earlier `tests/agent/agent_session.py` path does not exist.
- `tests/agent/test_repl.py:988-999` — existing REPL operator-facing behavior for
  `SchemaMissingError` (characterization guard).
- `implementations/done/20260724-230132_session.py.md:13,89-103` — origin of the
  false 1017 claim (historical record, not edited).

## Acceptance Criteria

| ID | Criterion | Maps to |
|---|---|---|
| AC-001 | `grep '1017' scripts/agent/session.py` returns nothing; no `args[0]`-vs-int comparison in `start()`. | REQ-001 |
| AC-002 | Test: real in-memory DB without `sessions` table → `start()` raises `SchemaMissingError` containing "init_db.sh". | REQ-003 |
| AC-003 | Test: pre-flight passes, INSERT raises a genuine captured missing-table `OperationalError` → `SchemaMissingError` with the actionable message (red before fix, green after). | REQ-002, REQ-004 |
| AC-004 | Test: unrelated `OperationalError` (e.g. disk I/O message) still re-raises as `OperationalError`. | REQ-002 |
| AC-005 | All existing session/startup tests pass unmodified; `uv run ruff check` and `uv run mypy --no-namespace-packages` clean on the changed file. | REQ-005 |

## Tests

Add to `tests/agent/test_agent_session.py` (existing real-in-memory-SQLite pattern):
1. `test_start_missing_schema_raises_schema_missing_error` — `_FakeSQLiteHelper`
   backed by a fresh `sqlite3.connect(":memory:")` with NO schema applied →
   `SchemaMissingError` with the actionable message (pre-flight path; passes before
   and after the fix — regression guard).
2. `test_start_insert_race_missing_table_raises_schema_missing_error` — helper whose
   pre-flight SELECT succeeds (table row present in a scratch connection) but whose
   INSERT raises a genuine `sqlite3.OperationalError` captured from a real
   missing-table `INSERT` (carry `sqlite_errorcode`/`sqlite_errorname` by re-raising
   the captured instance) → `SchemaMissingError`. Red before the fix.
3. `test_start_unrelated_operational_error_reraises` — OperationalError with a
   different message (e.g. "no such column") re-raises unchanged.

Characterization guards: existing `test_agent_session.py` start() tests,
`test_repl.py` SchemaMissingError presentation test, full `tests/agent/test_session*.py`
set.

## Documentation Impact

N/A: behavior of the normal missing-schema path is unchanged (pre-flight already
raises `SchemaMissingError`); the race scenario is assessed unreachable-by-locking in
Design, so the issue's conditional "record in Known Issues" does not trigger. No docs
changed.

## Assumptions

| Assumption | Confidence | Verification |
|---|---|---|
| `sqlite_errorcode`/`sqlite_errorname` are available and populated on CPython 3.13 sqlite (issue constraint says 3.13; dev venv runs 3.14 — attributes verified on the runtime actually used by `uv run`, code uses `getattr(..., None)` defensively regardless). | High | Measured 2026-10-25: errorcode=1, errorname=SQLITE_ERROR on missing-table INSERT. |
| The pre-check→INSERT concurrent-drop race is practically unreachable under SQLite write-lock semantics (busy/sqlite_master snapshot behavior), so the fallback is a defensive guard, not an actively exercised path. | Medium | Design section reasoning; no production incident found in audit. Recorded as defense-in-depth, not a claimed live scenario. |
| `SchemaMissingError` catch sites depend only on the exception type, not on which raise-site produced it. | High | grep: only `repl_input_loop.py:90` + tests; verified. |

## Unknowns

| ID | Question | Confidence | Blocking | Verification Steps |
|---|---|---|---|---|
| U-001 | Issue's Unresolved Question 1 (SchemaMissingError vs raw OperationalError for post-pre-flight missing-table): resolved by decision — keep `SchemaMissingError` (issue Constraint line 49 mandates it as the public contract). Recorded in Design. | High (decision recorded) | No | Revisit only if a future design wants raw error propagation; tests AC-002/AC-003 encode the chosen contract. |
| U-002 | Exact production sqlite/journal-mode behavior under a concurrent DROP during a write transaction (would it ever surface as "no such table"?). | Low | No (fix is defensive either way) | Out of scope for implementation; would require production WAL-mode investigation. Noted in Design as why the guard is kept but no Known-Issue doc entry is added. |

## Affected areas

N/A: single function (`start()`) in `agent.session`; importers unchanged
(`lint-imports` contract unaffected — no new imports). `deploy.sh` impact: none
(No schema or script changes). DB runtime: none (error-path only).

## Adversarial Re-verification (2026-10-25, procedure generation)

- `repl_input_loop.py:15` imports and `:90` re-raises `SchemaMissingError` — verified.
- Fallback block is `session.py:139-147` (`try:` 139, `except sqlite3.OperationalError`
  141, `err_code = e.args[0]` 142, dead `if err_code == 1017` 144).
- Confirmed dead: CPython sets `OperationalError.args[0]` to the message string (verified
  on dev venv Python 3.14.7: `args[0]` = `'no such table: nope'`, `sqlite_errorcode` = 1,
  `sqlite_errorname` = `'SQLITE_ERROR'`). The integer-code fix is reachable.
- `tests/agent/test_agent_session.py` exists with `TestStart` (line 152) and
  `_FakeSQLiteHelper` (line 54); no `SchemaMissingError` test in this file yet.
- `test_repl.py` has an existing `SchemaMissingError` → "Database is not initialized."
  precedent test (the behavior the fix must not break).
- Historical "186 passed" figure not reproducible at HEAD:
  `tests/agent/test_agent_session.py` + `tests/agent/test_repl.py` collect 125 tests.
  Validation plan commands are authoritative.

## Design

Chosen: **fix the fallback** (issue option 1), delete rejected (issue option 2).
Rationale:
- The issue Constraint (line 49) mandates `SchemaMissingError` as the public failure
  contract for a missing sessions schema; deletion would leave the post-pre-flight
  race with a raw `OperationalError`, violating the stated intent even if the race is
  rare.
- Reachability analysis: under SQLite locking, a concurrent DROP between pre-check and
  INSERT in the same write transaction should surface as busy, not "no such table"
  (see Unknowns U-002) — the guard is defense-in-depth, kept cheap and honest.

Concrete contract for the fixed branch (implementation procedure will refine exact
expression):
- Treat as schema-missing when the error is a missing-table error for `sessions`:
  message contains `"no such table: sessions"` and
  (`getattr(e, "sqlite_errorcode", None)` is 1/None-defensive or
  `getattr(e, "sqlite_errorname", None)` == `"SQLITE_ERROR"`).
  Narrow on the table name so unrelated OperationalErrors keep re-raising (REQ-002,
  test 3).
- Replace the comment with one naming `sqlite_errorcode`/`sqlite_errorname` as the
  real mechanism.
- Do not touch pre-flight, creation, repo rebind, logging (issue AI-instruction line).

## Implementation steps

1. Write the failing tests first (issue AI-instruction): tests 1-3 above against
   current code (test 2 red, tests 1/3 green).
2. Replace the fallback block + comment in `start()` per Design.
3. Run targeted: `uv run pytest tests/agent/test_agent_session.py tests/agent/test_repl.py -x -q`;
   then `tests/agent/test_session*.py` selected set; ruff + mypy on the changed file.

## Validation plan

- Targeted: `uv run pytest tests/agent/test_agent_session.py tests/agent/test_repl.py -x -q`.
- Selected: `uv run pytest tests/agent/test_session*.py` (186-test set, green baseline).
- Full: `uv run pytest tests/ -q` (baseline 10082 passed / 9 skipped) +
  `rules/toolchain.md` sequence; `lint-imports` 6 kept.
- Static: `uv run ruff check` + `uv run mypy --no-namespace-packages` on
  `scripts/agent/session.py` (issue Testing Expectations); bandit baseline 0 findings
  on this file must stay 0.
- AC-001 grep check: no `1017` in `session.py`.

## Risks

| Risk | Severity | Likelihood | Mitigation |
|---|---|---|---|
| Message-string matching is brittle across sqlite versions (message text may change). | Low | Low | Match on the narrow table-name substring AND the extended-code attributes; tests pin current behavior. |
| Overly broad match converts unrelated OperationalErrors into SchemaMissingError (misdiagnosis). | Medium | Low | Narrow on "no such table: sessions"; test 3 pins re-raise for other messages. |
| Edit collision with sess001 in `session.py` (`start()` region: repo rebind lines 151-153). | Medium | High | Dependency stated in the issue: sess001 lands first; re-verify line references against updated source before implementing (issue Dependencies line 93). sess002 touches only the except-block, disjoint from sess001's property changes. |

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`.

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Tests first: fallback regression tests (`tests/agent/test_agent_session.py`) | In Progress | — | — | re-verified against HEAD fb9359f22 2026-10-25; corrections reflected in this plan |
| 2 | Fallback fix: code/name/message gate (`scripts/agent/session.py:141-146`) | In Progress | — | — | `REQ-001`, `REQ-002`, `REQ-004`, `REQ-005` |
| 3 | Full validation sequence | Pending | — | — | gate only; modifies no file |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261025-133350_01_scripts_agent_session.py.md | 2 | Procedure | Pending | — | — |
| implementations/20261025-133350_02_tests_agent_test_agent_session.py.md | 1 | Procedure | Pending | — | — |

## Traceability

- Implementation step 1 → REQ-002..REQ-004 (tests 2/1/3 encode AC-002..AC-004).
- Implementation step 2 → REQ-001, REQ-002, REQ-005.
- Implementation step 3 → AC-005.

## Requirement Traceability

| Requirement | Test / Evidence | Acceptance Criterion |
|---|---|---|
| REQ-001 | grep check | AC-001 |
| REQ-002 | tests 2 and 3 | AC-003, AC-004 |
| REQ-003 | test 1 (real DB, no table) | AC-002 |
| REQ-004 | test 2 uses genuine captured error attributes | AC-003 |
| REQ-005 | existing test_agent_session/test_repl suites, ruff, mypy | AC-005 |
