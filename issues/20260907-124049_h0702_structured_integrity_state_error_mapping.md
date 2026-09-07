# Implement deterministic exception-to-state mapping for structured integrity classification

## Priority
Medium

## Summary
`scripts/db/recovery.py` already defines `DbCondition` (StrEnum: HEALTHY, CORRUPTION,
LOCK_CONTENTION, PERMISSION_FAILURE, INVALID_FORMAT, UNKNOWN) and routes recovery decisions
through it, satisfying most of memo2.md's Issue H-07-02 intent. However, `_classify_error()`
has no code path that ever returns `INVALID_FORMAT`, and its lock/permission classification
relies on lowercased substring matching of `str(e)` rather than SQLite error codes or
exception types. Replace the substring-matching fallback with a deterministic mapping
(SQLite error code / exception type first), and add the missing `INVALID_FORMAT`
classification path.

## Background
Confirmed by direct read of `scripts/db/recovery.py` lines 26-47: `DbCondition` already has
the six normative states from memo2.md's Issue H-07-02, and `_run_integrity_check()`/
`recover_corruption()` already dispatch on `DbCondition` rather than free-form messages
(satisfying most of H-07-02's "Proposed contract" intent, though as a
`tuple[DbCondition, str | None]` rather than an `IntegrityCheckResult` dataclass with
`quick_check_passed`/`sqlite_error_code`/`error_type` fields).

## Problem
- `_classify_error()` (lines 37-47) maps every `sqlite3.DatabaseError` or `ValueError` to
  `CORRUPTION` — there is no code path that returns `INVALID_FORMAT`, even though the enum
  defines it. A non-SQLite file (e.g. a text file with a `.sqlite` extension) raises
  `sqlite3.DatabaseError: file is not a database`, which is currently indistinguishable from
  genuine page-level corruption.
- Lock-contention and permission-failure detection depend on
  `"database is locked" in msg.lower()` / `"permission denied" in msg.lower()` substring
  matching against `str(e)`, not on `sqlite3.Error.sqlite_errorcode` (e.g. `SQLITE_BUSY`,
  `SQLITE_LOCKED`) or `OSError.errno` (e.g. `EACCES`). A differently worded SQLite build
  message could produce text that does not match these substrings, silently misclassifying a
  lock/permission condition as `UNKNOWN` or `CORRUPTION`.
- `tests/db/test_db_recovery.py` covers `LOCK_CONTENTION`/`PERMISSION_FAILURE`/`UNKNOWN` only
  by mocking `_run_integrity_check`'s return value directly — there is no test that exercises
  `_classify_error()` itself against a real or constructed exception, so the substring-matching
  gap above is not caught by the existing suite (confirmed by direct read of
  `tests/db/test_db_recovery.py`).

## Reason for Change
Substring matching against exception messages is fragile across SQLite versions/locales and
conflates "file is not a valid SQLite database" with "page-level corruption of an otherwise
valid SQLite file" — the backup-validation and atomic-replacement logic tracked separately in
this batch needs this distinction to reject a wrong-format backup candidate without treating
it identically to physical corruption.

## Implementation Intent
Keep `DbCondition` as the contract (no new states without justification, per memo2.md's
original constraint). Change `_classify_error()`'s internals to prefer
`sqlite3.Error.sqlite_errorcode` / `OSError.errno` over message substrings, and add a
deterministic path that returns `INVALID_FORMAT` for the "not a database" condition, distinct
from `CORRUPTION`. Preserve the existing public signatures (`_run_integrity_check` return
shape, `recover_corruption` action names) unless a caller genuinely needs the new distinction
surfaced.

## Target Files or Areas
- `scripts/db/recovery.py` (`_classify_error()`, `_run_integrity_check()`)
- `tests/db/test_db_recovery.py`

## Required Changes
- Replace substring matching in `_classify_error()` with `sqlite3.Error.sqlite_errorcode`
  (or `sqlite3.Error.sqlite_errorname` where available) for `LOCK_CONTENTION`/
  `PERMISSION_FAILURE`, falling back to substring matching only where the sqlite3 module does
  not expose a structured code.
- Add a deterministic condition (matching SQLite's `"file is not a database"` signal) that
  returns `DbCondition.INVALID_FORMAT` instead of `DbCondition.CORRUPTION`.
- Confirm `recover_corruption()`'s existing branch that groups `INVALID_FORMAT` with
  `LOCK_CONTENTION`/`PERMISSION_FAILURE` (returning `action="error"` without touching backups)
  still receives dispatch correctly once `_classify_error()` can produce `INVALID_FORMAT`.
- Add unit tests that call `_classify_error()` directly (not only `_run_integrity_check`'s
  mocked return) against constructed `sqlite3.OperationalError`/`sqlite3.DatabaseError`
  instances for each state, including the new `INVALID_FORMAT` case.

## Constraints
- Do not add new `DbCondition` states beyond `INVALID_FORMAT` without documenting the
  recovery decision and adding tests, per memo2.md's original constraint.
- Do not change `recover_corruption()`'s existing action names/values for
  `LOCK_CONTENTION`/`PERMISSION_FAILURE`/`UNKNOWN` — only the classification path feeding into
  `DbCondition` changes.

## Acceptance Criteria
- [ ] `_classify_error()` returns `DbCondition.INVALID_FORMAT` for a "not a database"
      `sqlite3.DatabaseError`, distinct from `DbCondition.CORRUPTION`.
- [ ] Lock-contention and permission-failure classification uses
      `sqlite3.Error.sqlite_errorcode`/`OSError.errno` where available, with substring
      matching only as a documented fallback.
- [ ] A direct unit test exists for `_classify_error()` covering all six `DbCondition`
      states, not only for `_run_integrity_check`'s mocked return.
- [ ] Existing `recover_corruption()` tests in `tests/db/test_db_recovery.py` continue to
      pass unchanged.

## Testing Expectations
`uv run pytest tests/db/test_db_recovery.py -v`; add new `_classify_error()`-targeted unit
tests per Required Changes.

## Documentation Impact
None expected — this is an internal classification-logic change; no documented action name
or recovery policy changes. If a canonical recovery specification under `docs/` enumerates
`DbCondition` states, confirm it already lists all six (no update expected).

## Out of Scope
- Do not implement backup-candidate domain-identity validation (tracked separately in this
  batch).
- Do not change staged atomic replacement or WAL/SHM handling (tracked separately in this
  batch).
- Do not add an `IntegrityCheckResult`-style dataclass replacing the current
  `tuple[DbCondition, str | None]` return shape unless a concrete caller need is identified —
  the existing shape already satisfies structured dispatch.

## Dependencies
Depends on `issues/done/20260903-110304_h0701_define-recovery-policy-per-sqlite-persistence-domain.md`
(H-07-01, terminology). The backup-candidate domain-identity validation issue filed alongside
this one needs a reliable `INVALID_FORMAT`/`CORRUPTION` distinction to reject malformed backup
candidates correctly, so this issue should land first.

## Unresolved Questions
N/A: none

## AI Implementation Instruction
Confirm the current `sqlite3` module's actual behavior for `sqlite_errorcode`/
`sqlite_errorname` on this project's Python 3.13 target before assuming API availability. Keep
the change scoped to `_classify_error()`'s internals and its direct tests — do not touch
`_restore_from_backup()`, `recover_corruption()`'s control flow, or WAL/SHM handling (out of
scope for this issue).
