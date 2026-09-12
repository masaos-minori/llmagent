# `TestRunSqliteErrorMessage` hardcodes `/tmp/llm/db`, which does not exist on this machine

## Priority
Low

## Summary
`TestRunSqliteErrorMessage::test_error_message_includes_class_name` and
`::test_runtime_error_includes_class_name` (`tests/agent/test_repl.py`) fail with
`ValueError: rag_db_path parent directory does not exist: /tmp/llm/db` when constructing
a `DbConfig`. Confirmed environment/fixture gap, not a production defect:
`DbConfig.__post_init__`'s parent-directory validation
(`scripts/db/config.py`) is intentional and correct; the tests hardcode a path
(`/tmp/llm/db/...`) that happens not to exist in this environment instead of using a
pytest-managed temporary directory.

## Background
`Explicit in code`: `scripts/db/config.py`'s `DbConfig.__post_init__` validates each
configured DB path's parent directory exists, with an explicit design comment
explaining why (SQLite creates the DB file itself on first open, so only the parent
directory needs to pre-exist). This validation is working as intended — the failure is
purely because `/tmp/llm` does not exist as a directory on this machine, not because the
validation logic is wrong.

## Problem
Both tests construct a real `DbConfig` with `rag_db_path` (and likely sibling paths)
under a hardcoded `/tmp/llm/db/...` location, assuming that directory tree already
exists. On a machine/environment where it does not (as observed here), config
construction itself fails before either test reaches its actual assertion about the
error-message format it's meant to verify (`class name` inclusion in a `RuntimeError`
message).

## Reason for Change
2 tests intended to verify SQLite error-message formatting currently fail for an
unrelated environment reason, providing no coverage of the actual formatting behavior
they target, and would produce a false failure on any developer machine or CI runner
without a pre-existing `/tmp/llm/db` directory.

## Implementation Intent
Use pytest's `tmp_path` fixture (or an equivalent, already-existing temporary directory
mechanism used elsewhere in this test suite for `DbConfig`-constructing tests) instead
of a hardcoded `/tmp/llm/db` path, so the parent directory is guaranteed to exist
regardless of the running environment.

## Target Files or Areas
- `tests/agent/test_repl.py`
  (`TestRunSqliteErrorMessage::test_error_message_includes_class_name`,
  `::test_runtime_error_includes_class_name`)
- `scripts/db/config.py` (reference only — confirms `DbConfig.__post_init__`'s
  intentional parent-directory validation; not a modification target)

## Required Changes
- Replace the hardcoded `/tmp/llm/db/...` path construction in both tests with a
  `tmp_path`-derived path (or this suite's existing equivalent convention for
  `DbConfig`-constructing tests — check for one before introducing a new pattern).
- No change to `scripts/db/config.py`.

## Constraints
Do not weaken or bypass `DbConfig.__post_init__`'s parent-directory validation — it is
confirmed intentional and correct.

## Acceptance Criteria
- [ ] Both tests construct their `DbConfig` using a guaranteed-to-exist temporary
  directory, not a hardcoded `/tmp/llm/db` path
- [ ] `uv run pytest "tests/agent/test_repl.py::TestRunSqliteErrorMessage" -q` passes on
  a machine without a pre-existing `/tmp/llm/db` directory
- [ ] No change to `scripts/db/config.py`

## Testing Expectations
- `uv run pytest "tests/agent/test_repl.py::TestRunSqliteErrorMessage" -q` — both cases
  pass, verifying the actual error-message class-name-inclusion behavior they target

## Documentation Impact
N/A: test-only environment-portability fix; no documented behavior change.

## Out of Scope
- `TestGetWorkflowStatus`'s 2 failures — tracked separately as `repl002`.
- `TestPersistSessionDiagnostics`'s 2 failures — tracked separately as `repl003`.
- `TestSigtermHandlerTurnActiveGuard`'s 1 failure — tracked separately as `repl005`.
- Any change to `scripts/db/config.py`'s validation.

## Dependencies
N/A: none. Discovered while investigating `test_repl.py`'s post-`repl001`-fix remaining
failures — independent of that fix.

## Unresolved Questions
N/A: none — root cause (hardcoded nonexistent path vs. intentional, correct
validation) confirmed by direct read of both the test and `DbConfig.__post_init__`.

## AI Implementation Instruction
Replace the hardcoded path with `tmp_path` (or this suite's existing convention) only;
do not modify `scripts/db/config.py`'s validation.

## Traceability
- **Workflow phase**: N/A: manually filed
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260909-130516
- **Related target files**: see Target Files or Areas above
