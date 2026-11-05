# Match the consistency-check callback's exception scope to the ingestion loop

## Priority
Low

## Summary
`RagIngester._run_ingest_callback` logs the post-ingestion consistency-check result and
swallows failures, but its `except (OSError, RuntimeError, ValueError)` does not cover
`sqlite3.Error`, while the main ingestion loop it follows catches `Exception`. A DB error
raised inside the consistency check therefore escapes `ingest_all` after a fully
successful ingestion, contradicting the log message "consistency check failed (logged;
does not affect ingestion)".

## Problem
- `scripts/rag/ingestion/ingester.py` `_process_url_groups` documents and implements
  "log exceptions without stopping" using a broad `Exception` handler (a prior fix, see
  `issues/done/20261027-074526_rag004_ingester-sqlite3-error-aborts-batch.md`).
- `_run_ingest_callback` logs `report['consistent']` (including when the check *ran but
  reported inconsistency*) but only catches `(OSError, RuntimeError, ValueError)`;
  `sqlite3.Error` subclasses (e.g. `OperationalError` from a locked DB during the check)
  propagate out of `ingest_all` and out of `main()` as an unhandled exception.
- The failure appears *after* all ingestion work succeeded, so the run's exit status and
  traceback misreport a successful ingestion as a crash.

## Background
The callback was added to satisfy the ingestion-consistency reporting requirement
(REQ-007 area); the exception tuple was written before the main loop was broadened to
`Exception`, and the two scopes have since diverged.

## Reason for Change
Consistency with the established "ingestion completion must not be broken by reporting
failures" contract (same principle `bump_index_generation` follows with its never-raises
docstring).

## Implementation Intent
Broaden `_run_ingest_callback`'s handler to the same scope the ingestion loop uses
(`Exception`, or at minimum add `sqlite3.Error`), with a log line that names the failure
class, keeping the callback's never-raises contract.

## Target Files or Areas
- `scripts/rag/ingestion/ingester.py`
- `tests/rag/ingestion/test_rag_ingester_callback.py`

## Required Changes
- Extend the caught exception set in `_run_ingest_callback`.
- Add a regression test: a consistency check that raises `sqlite3.Error` is logged, and
  `ingest_all` returns normally with correct totals.

## Constraints
- Do not hide genuine ingestion failures: the callback wraps only the consistency-check
  invocation, not the ingestion path.
- Keep the existing log-key style of the surrounding code.

## Acceptance Criteria
- A `sqlite3.Error` from the consistency-check callback does not propagate out of
  `ingest_all` (covered by test).
- Existing callback tests pass.

## Testing Expectations
- New regression test in `tests/rag/ingestion/test_rag_ingester_callback.py`.
- `uv run pytest tests/rag/ingestion`.

## Documentation Impact
N/A: behavior already documented as "logged; does not affect ingestion".

## Out of Scope
- Redesigning the consistency report contents.

## Dependencies
- N/A: none (the earlier `_process_url_groups` fix is already deployed).

## Unresolved Questions
- None.

## AI Implementation Instruction
Single handler-scope change plus one test; do not alter DocumentManager or the ingestion
loop.

## Traceability
- **Workflow phase**: python-code-review
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261106-073538
- **Related target files**: `scripts/rag/ingestion/ingester.py`, `tests/rag/ingestion/test_rag_ingester_callback.py`
