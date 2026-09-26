# session_message_repo foreign key constraint failure in custom roles test

## Priority
Medium

## Summary
`tests/agent/test_session_message_repo.py::TestCustomRoles::test_default_roles_fallback` fails with `sqlite3.IntegrityError: FOREIGN KEY constraint failed`, meaning the test's setup inserts or references a row that violates a foreign-key relationship (e.g. a message referencing a non-existent session).

## Background
Discovered during the post-docs-reorg full-suite validation sweep (`implementations/20260925-111411_04_tests___full_suite_.md`), which surfaced 97 failing tests; this is one root-cause cluster from that investigation.

## Problem
`sqlite3.IntegrityError: FOREIGN KEY constraint failed` raised during `test_default_roles_fallback`. The exact failing insert/statement was not captured in this investigation pass (only the top-level assertion/error was observed via `--tb=short`).

## Reason for Change
A foreign-key violation in a "default roles fallback" test suggests either the test's setup ordering (e.g. creating a session row before inserting messages) changed/broke, or a schema/fixture change altered which columns/tables enforce the FK relationship.

## Implementation Intent
Reproduce the test with `--tb=long` to capture the exact failing SQL statement and the FK relationship involved. Determine whether the test's own setup is missing a required prerequisite row (test bug) or whether the production schema/insert logic changed in a way that broke a previously-valid sequence (production bug).

## Target Files or Areas
- `tests/agent/test_session_message_repo.py`
- Session/message repo module and schema (confirm exact path, likely `scripts/agent/session_message_repo.py` and its schema definition)

## Required Changes
- Reproduce with full traceback to identify the exact FK relationship and failing statement.
- Fix the test's setup ordering/missing prerequisite row, or fix the production insert logic, per whichever is confirmed to be at fault.

## Constraints
Do not disable or loosen the foreign-key constraint itself to make the test pass — fix the actual ordering/data issue.

## Acceptance Criteria
- The listed test passes without weakening any FK constraint.

## Testing Expectations
Run `tests/agent/test_session_message_repo.py` with full traceback; run full suite once after the fix.

## Documentation Impact
N/A: internal test/schema fix, no expected documentation impact.

## Out of Scope
Other unrelated failing tests from the same full-suite run.

## Dependencies
N/A: none

## Unresolved Questions
Needs confirmation: the exact failing SQL statement/FK relationship — this investigation only captured the top-level `IntegrityError`, not the full traceback.

## AI Implementation Instruction
First reproduce with `--tb=long` to see the exact failing statement before making any change. Do not weaken the foreign-key constraint to work around the failure.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: implementations/20260925-111411_04_tests___full_suite_.md
- **Generated at**: 20260927-075330
- **Related target files**: tests/agent/test_session_message_repo.py
