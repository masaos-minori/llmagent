# SQLiteHelper.open leaks connections on failure and silently ignores load_vec=True without a library path

## Priority
Medium

## Summary
`SQLiteHelper.open` can leave a raw connection open on several failure paths, overwrites an existing `self.conn` without closing it, and skips the vec extension silently when `load_vec=True` is requested but no library path is configured.

## Background
Found by an adversarial review of `scripts/db` at commit 0fe68d3 (Review finding F-005). Evidence label: `Verified by test` (second pass, ad hoc reproduction) for the leak when `_apply_connection_pragmas` raises (the captured connection stayed usable after `open` raised `database is locked`), for the leak on re-open (the first connection stayed open), and for the silent `load_vec=True` skip (no error with no library path). The `enable_load_extension` `AttributeError` leak is `Explicit in code` only (not reproduced). Confidence High.

## Problem
- `open` assigns `self.conn` only at the end. If `_apply_connection_pragmas` raises (for example `PRAGMA journal_mode=WAL` on a locked or read-only file), the connection created by `_connect` is never closed.
- `_load_vec_extension` closes the connection only for `sqlite3.OperationalError`. An `AttributeError` from `enable_load_extension` (Python built without extension support) or any other exception leaks it.
- Calling `open()` with `reuse_connection=False` while `self.conn` is already set replaces the attribute and drops the earlier connection unclosed.
- `use_vec and self._vec_so` makes an explicit `load_vec=True` a no-op when `_vec_so` is empty; the `ValueError` guard in `_load_vec_extension` is unreachable. Callers then fail later with `no such module: vec0`, which the fail-closed logical layer reports as corruption (see `issues/20261114-092848_dbreview001_logical-verify-vec-extension.md`).

## Reason for Change
Leaked connections hold file locks and WAL readers, which can block checkpoints and the very maintenance operations in this package. The silent skip converts a configuration error into misleading downstream failures.

## Implementation Intent
Make `open` exception-safe (close on any failure before the connection is stored), close or refuse a previously open connection, and raise when `load_vec=True` is explicit but the library path is missing.

## Target Files or Areas
- `scripts/db/helper.py` (`open`, `_connect`, `_load_vec_extension`)
- `tests/db/test_sqlite_helper.py`

## Required Changes
- Wrap the post-connect steps of `open` in `try/except BaseException` that closes the connection and re-raises.
- Close the existing connection (or raise) when `open` is called on an already-open non-reuse helper.
- Raise `ValueError` when `load_vec=True` is passed with no `sqlite_vec_so`.
- Add tests covering each path.

## Constraints
- `reuse_connection=True` semantics must stay unchanged.
- The instance-default behavior for `load_vec=None` must stay unchanged.

## Acceptance Criteria
- After a failing `open`, no connection to the file remains (verified by obtaining an exclusive lock from another connection).
- Re-opening a helper does not leak the first connection.
- `load_vec=True` without a path raises `ValueError`.

## Testing Expectations
Unit tests in `tests/db/test_sqlite_helper.py` with a temporary database, a held lock, and a stubbed `enable_load_extension` failure.

## Documentation Impact
Not required beyond the existing docstring of `open`.

## Out of Scope
- Changing the default pragma set.
- Thread-safety design (`check_same_thread`).

## Dependencies
N/A: none

## Unresolved Questions
N/A: none

## AI Implementation Instruction
Follow `skills/python-implementation/SKILL.md`. Keep the public signature of `open` compatible. English comments and logs.

## Traceability
- **Workflow phase**: python-code-review
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261114-092853
- **Related target files**: scripts/db/helper.py, tests/db/test_sqlite_helper.py
