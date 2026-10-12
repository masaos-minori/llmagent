# Fix eventbus test seed INSERTs referencing non-existent last_nack_attempt column

## Priority
Medium

## Summary
Five eventbus tests fail because their `consumer_delivery` seed INSERTs reference a
non-existent column `last_nack_attempt` (the real column is
`consumer_last_nack_attempt`) and set `acked=NULL` instead of `acked=0`. Fix the seed
data so it matches the schema and those tests pass.

## Background
The per-consumer delivery model stores ack/nack state in the `consumer_delivery` table.
The "last NACK attempt" column is named `consumer_last_nack_attempt`
(`scripts/eventbus/_constants.py:_COL_CONSUMER_LAST_NACK_ATTEMPT`; added via
`ALTER TABLE` in `scripts/eventbus/schema.py`). Several test seed INSERTs were written
against an incorrect column name `last_nack_attempt`, which does not exist in the table,
so executing them raises `sqlite3.OperationalError: table consumer_delivery has no column
named last_nack_attempt`.

## Problem
Five tests fail on current source, all from one root cause — seed data that does not match
the schema:

- `tests/eventbus/test_eventbus_dlq_promotion.py::TestDLQPROMotionSemantics::test_requeue_returns_dlq_imminent_when_consumer_delivery_failure_count_gte_max_retry`
- `tests/eventbus/test_eventbus_dlq_promotion.py::TestDLQPROMotionSemantics::test_dlq_promotion_when_consumer_delivery_failure_count_gte_max_retry`
- `tests/eventbus/test_eventbus_dlq_promotion.py::TestDLQPROMotionSemantics::test_dlq_requeue_increments_dlq_requeue_count_not_consumer_delivery_failure_count`
- `tests/eventbus/test_eventbus_dlq_pagination.py::test_dlq_pagination`
- `tests/eventbus/test_eventbus_concurrent.py::TestConcurrentDlqRequeue::test_concurrent_dlq_requeue`

Evidence (`Confirmed by repository evidence`): direct reproduction raises
`sqlite3.OperationalError: table consumer_delivery has no column named last_nack_attempt`
(and a related `sqlite3.ProgrammingError: Incorrect number of bindings supplied` where a
seed lists `acked` but binds `NULL`, leaving the column list and tuple length mismatched).

## Reason for Change
The test suite is red on `master`, which hides further regressions in the eventbus. These
failures are mechanical (seed data does not match the schema) rather than semantic, but
they still prevent the suite from reporting a clean signal.

## Implementation Intent
Align the failing seed INSERTs with the real schema: use the column name
`consumer_last_nack_attempt` and set `acked=0` for a delivered-but-un-acked row. Preserve
each test's intent (max-retry promotion, DLQ requeue counting, pagination seeding); only
correct the column reference and the `acked` default.

## Target Files or Areas
- `tests/eventbus/test_eventbus_dlq_promotion.py`
- `tests/eventbus/test_eventbus_dlq_pagination.py`
- `tests/eventbus/test_eventbus_concurrent.py`

## Required Changes
- In each failing seed INSERT, replace the non-existent column `last_nack_attempt` with
  `consumer_last_nack_attempt`.
- Set `acked` to `0` (delivered but un-acked) instead of `NULL` where the seed represents a
  delivered row, so the column list and the binding tuple stay aligned.
- Do not alter the assertions or the semantic intent of any of the five tests.

## Constraints
- Do not modify production code (`scripts/eventbus/`); the schema and repository are
  correct — only the test seed data is wrong.
- Do not change the schema or migrations.
- Keep the column list and the binding tuple consistent after the rename.
- Production data must not be touched.

## Acceptance Criteria
- The five listed tests pass.
- `uv run pytest tests/eventbus` reports no failures attributable to this root cause.
- No previously-passing test under `tests/eventbus` regresses.

## Testing Expectations
Run the five named tests plus the full `tests/eventbus/` suite and confirm no
`sqlite3.OperationalError` / `sqlite3.ProgrammingError` about `last_nack_attempt`
remains. Run `uv run ruff check` and `uv run mypy` per `rules/toolchain.md`.

## Documentation Impact
None expected. No documentation references the test seed column names.

## Out of Scope
- The COALESCE ACK defect (`issues/20261011-204621_eb013_...md`) and the 3-tuple vs
  4-tuple return-contract mismatch (`issues/20261011-075321_eb012ack_...md`) — different
  root causes.
- Schema or migration changes.
- NACK idempotency or per-consumer failure-counter semantics.

## Dependencies
- Addressed by the same uncommitted WIP commit that corrects eb013
  (`issues/20261011-204621_eb013_...md`). Tracked here separately because it is a distinct
  root cause with distinct target files.

## Unresolved Questions
`N/A: none` — a scan of `tests/eventbus/` for the old column name confirms only the three
files above contain the mismatch; no latent occurrences are expected elsewhere.

## AI Implementation Instruction
- Only edit the five failing tests' seed INSERTs; do not touch production code or other
  tests.
- Keep the column list and the binding tuple aligned after renaming
  `last_nack_attempt` → `consumer_last_nack_attempt`.
- Set `acked=0` for delivered-but-un-acked seeds (not `NULL`).
- Verify the five named tests pass and the full `tests/eventbus/` suite stays green.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261012-075903
- **Related target files**: `tests/eventbus/test_eventbus_dlq_promotion.py`,
  `tests/eventbus/test_eventbus_dlq_pagination.py`, `tests/eventbus/test_eventbus_concurrent.py`
