# Fix malformed log format in ETagManager's stored-timestamp guard

## Priority
Low

## Summary
`ETagManager.update`'s skip branch logs a message whose format string mixes `%s < %s` with
a `%d` placeholder but passes only two arguments, and uses numeric comparison placeholders
for ISO-8601 timestamps. Every invocation of the stored-timestamp guard produces a
`--- Logging error ---` traceback (`TypeError: not enough arguments for format string`)
instead of a clean log line.

## Problem
In `scripts/rag/ingestion/etag_manager.py`:

    logger.info(
        "skip-path etag update skipped: incoming stale (%s < %s) for doc_id=%d",
        new_fetched_at,
        self._doc_id,
    )

- Two placeholders pairs (`%s < %s`) describe the incoming and stored timestamps, but only
  `new_fetched_at` and `doc_id` are passed.
- Verified by reproduction: emitting this line raises a logging error with
  `TypeError: not enough arguments for format string`.
- The comparison being reported (`>=` on ISO strings) is lexicographic, so `%d` does not
  describe the values at all; a future `doc_id`-format mistake would be invisible because
  the line is already broken.

## Background
The guard was added by commit df1ff8ed4 era work on the skip path ("keep Japanese
sentences..." series touched the same file; the guard's stale-overwrite protection is
covered by `tests/rag/ingestion/test_ingester_etag_guard.py`). Tests assert the guard's
behavior but do not validate the log line, so the broken formatting survived.

## Reason for Change
Broken log output in a data-integrity guard path: the operator-visible evidence that a
stale update was skipped is an exception traceback rather than the intended message,
which pollutes logs and undermines trust in the guard's observability.

## Implementation Intent
Correct the format string and arguments so the line reports incoming timestamp, stored
timestamp, and doc_id with matching placeholders.

## Target Files or Areas
- `scripts/rag/ingestion/etag_manager.py`

## Required Changes
- Fix the `logger.info` call in the stored-timestamp guard so placeholder count and types
  match the arguments (include the stored `fetched_at` value in the message).
- Keep the message intent (report why the update was skipped).

## Constraints
- No behavior change to the guard logic itself.
- Keep the single-argument-free `Logger` calling convention used elsewhere in the file.

## Acceptance Criteria
- Triggering the skip path emits exactly one clean log line naming both timestamps and
  doc_id, with no logging error (verified by a test that captures log output).

## Testing Expectations
- Regression test using `caplog` (or equivalent) asserting the skip-path line formats
  without a logging error.
- `uv run pytest tests/rag/ingestion/test_ingester_etag_guard.py`.

## Documentation Impact
N/A: no documentation describes this log line.

## Out of Scope
- Lexicographic-vs-parsed comparison semantics for timestamp freshness.

## Dependencies
- N/A: none

## Unresolved Questions
- None.

## AI Implementation Instruction
Single-line-class fix; do not refactor ETagManager.

## Traceability
- **Workflow phase**: python-code-review
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261106-073538
- **Related target files**: `scripts/rag/ingestion/etag_manager.py`
