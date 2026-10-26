# Ingestion batch aborts on sqlite3 error despite the no-stop contract

## Priority
Medium

## Summary
`_process_url_groups` in `scripts/rag/ingestion/ingester.py` catches only
`(OSError, RuntimeError, ValueError)`, so any `sqlite3.Error` raised while ingesting one
URL group propagates out of `ingest_all`, aborting every remaining URL group in the run and
skipping the post-ingestion consistency check. Add `sqlite3.Error` to the caught tuple so
the documented "log exceptions without stopping" behavior holds.

## Background
Both the module docstring and the `_process_url_groups` docstring state that the loop logs
exceptions "without stopping". Elsewhere in the same subsystem the authors already handle DB
errors explicitly:

- `DocumentManager.check_consistency` catches
  `(sqlite3.OperationalError, sqlite3.DatabaseError, ValueError)`
  (`scripts/rag/ingestion/document_manager.py`).
- `SQLiteHelper._begin_transaction` rolls back on any `Exception` and re-raises
  (`scripts/db/helper.py`).
- `tests/rag/ingestion/test_rag_ingester.py::TestAtomicity::test_database_failure_during_replacement`
  asserts that a `sqlite3.DatabaseError` raised inside `TransactionManager.commit` propagates
  out of `ingest_url_group`.

## Problem
The caught exception tuple omits `sqlite3.Error`. Empirically none of `sqlite3.Error`,
`sqlite3.OperationalError`, `sqlite3.IntegrityError`, `sqlite3.DatabaseError`,
`sqlite3.ProgrammingError`, `sqlite3.DataError`, `sqlite3.InternalError`, or
`sqlite3.NotSupportedError` is a subclass of `(OSError, RuntimeError, ValueError)`.

Therefore a DB error during one URL group — a lock beyond `sqlite_busy_timeout_ms`, disk
full, an integrity/unique violation, a malformed image, or an FTS5/chunks_vec write failure
inside `_insert_chunks_batch` — escapes `_process_url_groups`, unwinds `ingest_all` before
`check_consistency` runs, and leaves all subsequent URL groups unprocessed. The unprocessed
chunk files remain in `chunk_dir` (they are only routed on success), so the workload
self-heals on the next invocation, but the current run silently drops work and skips its
consistency gate.

## Reason for Change
The code's stated contract ("log exceptions without stopping") is violated for the entire
class of database errors, which are precisely the transient/environmental failures most
worth surviving during a batch. The fix aligns runtime behavior with the documented intent
and with `check_consistency`'s own handling of the same error hierarchy.

## Implementation Intent
Add `sqlite3.Error` to the exception tuple in `RagIngester._process_url_groups` so DB errors
are logged via the existing `logger.exception` and the URL is recorded as an unexpected
failure, then continue to the next group. Keep the other three categories. Do not broaden to
a bare `except Exception` (which would hide programming errors). Add a regression test that
drives `_process_url_groups` / `ingest_all` with a `sqlite3.OperationalError` on one group
and asserts the remaining groups still process.

## Target Files or Areas
- `scripts/rag/ingestion/ingester.py` (`_process_url_groups`, the `except` at line ~377)
- `tests/rag/ingestion/test_rag_ingester.py` (add regression test)

## Required Changes
- Add `sqlite3.Error` to the `except` tuple in `RagIngester._process_url_groups`.
- Import `sqlite3` in `ingester.py` if not already present (current imports are argparse,
  dataclasses, pathlib, httpx, and internal modules — no `sqlite3`).
- Add a regression test asserting batch continuation across a per-group `sqlite3` error.

## Constraints
- Add only the SQLite error hierarchy; do not catch a bare `Exception` or `BaseException`.
- Preserve the existing `logger.exception` logging and `IngestUrlResult.unexpected_failure`
  recording.
- Do not change transaction semantics: `SQLiteHelper.begin_immediate` already rolls back
  correctly on any exception, so transaction integrity is not the problem here.

## Acceptance Criteria
- A `sqlite3.OperationalError` (or any `sqlite3.Error`) raised while processing one URL group
  is caught, logged, and that group is marked failed.
- All remaining URL groups in the same run still process and appear in the returned results.
- The post-ingestion consistency check still runs after such an error.
- New and existing ingestion tests pass.

## Testing Expectations
- Run `tests/rag/ingestion/test_rag_ingester.py` and confirm all pass, including the new
  regression test.
- Re-confirm that no `sqlite3.*` exception is a subclass of `(OSError, RuntimeError,
  ValueError)` and that the widened tuple covers `sqlite3.OperationalError` and
  `sqlite3.IntegrityError`.

## Documentation Impact
None expected. The module and method docstrings already document the no-stop intent; the fix
makes the code match them rather than changing documented behavior.

## Out of Scope
- Changing the transaction boundary or rollback behavior.
- Broadening the catch to all exceptions.
- Fixing the unrelated project-wide `int(cfg[...])` type-coercion style seen in
  `crawler.py`, `chunk_splitter.py`, `db/config.py`, and `db/maintenance.py` — that is a
  separate, repository-wide concern and is not isolated to this module.

## Dependencies
N/A: this is a self-contained change to one method plus a test.

## Unresolved Questions
- Whether callers also expect `httpx` transport errors surfaced here — embedding/HTTP errors
  are already contained inside `ChunkFactory.prepare` and converted to `failed_paths`, so
  they never reach this handler. No change needed for them.

## AI Implementation Instruction
In `scripts/rag/ingestion/ingester.py`, change the
`except (OSError, RuntimeError, ValueError):` line in `RagIngester._process_url_groups` to
also catch `sqlite3.Error` (add `import sqlite3` at the top of the module). Keep logging via
the existing `logger.exception` and `IngestUrlResult.unexpected_failure(url)`. Do not widen
to a bare `except Exception`. Add a regression test in
`tests/rag/ingestion/test_rag_ingester.py` that makes one URL group raise
`sqlite3.OperationalError` and asserts the remaining groups still ingest.

## Traceability
```
- **Workflow phase**: python-code-review
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261027-074526
- **Related target files**: scripts/rag/ingestion/ingester.py, tests/rag/ingestion/test_rag_ingester.py
```
