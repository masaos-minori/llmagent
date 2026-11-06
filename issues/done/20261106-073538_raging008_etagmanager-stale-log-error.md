# Fix malformed log format in ETagManager's stored-timestamp guard

## Priority
Low

## Summary
`ETagManager.update`'s skip branch logs a message whose format string mixes `%s < %s` with
a `%d` placeholder but passes only two arguments, and uses numeric comparison placeholders
for ISO-8601 timestamps. Every invocation of the stored-timestamp guard produces a
`--- Logging error ---` traceback (`TypeError: not enough arguments for format string`)
instead of a clean log line.

### Verification (issue-to-plan cycle 20261106-103659)
- Confirmed at HEAD `bdb9bed66`: format string at `etag_manager.py:47-52` has 3 placeholders
  (`%s < %s` plus `%d`) but passes only 2 args (`new_fetched_at`, `self._doc_id`); the stored
  timestamp is never passed. Reproduction emits
  `TypeError: not enough arguments for format string` inside logging (`/tmp/opencode/raging008/repro.py`).
- Correction: the guard comparison is NOT lexicographic — `_is_stale_update` parses both
  sides with `datetime.fromisoformat` and compares datetimes (`:57-90`, `<` at `:90`). The
  issue's "lexicographic (`>=` on ISO strings)" description is wrong, and the Out-of-Scope
  "lexicographic-vs-parsed comparison" item is moot: the comparison is already parsed.
- New finding: the stored timestamp is only accessible inside `_is_stale_update` (fetched at
  `:73-76`); `update()` cannot name it without a change. Required fix shape: the private
  helper (single caller: `update()`; no test calls it directly) returns the stored timestamp
  when stale (or `None`), so the log can pass both values without a second DB query. Guard
  decision logic and exception behavior stay identical.
- Test status confirmed: `tests/rag/ingestion/test_ingester_etag_guard.py` has 9 tests, all
  asserting DB behavior; no `caplog` usage anywhere — the log line is unvalidated.
- Coordination: `plans/20261106-094942_raging002_etag-updated-before-reingestion.md` also
  targets `etag_manager.py` (new `resolve_incoming` method) and deliberately leaves
  `update()` unchanged; this log-line fix is compatible — sequence after 002 to avoid
  same-file rebase friction.

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
