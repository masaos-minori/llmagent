## Goal
- Add multi-consumer tests for the sweep and the inline path, and correct seed data that contradicts the adopted rule (`REQ-004`).

## Scope
- A new test class in `tests/eventbus/test_eventbus_dlq_promotion.py` and the `acked` value in three existing tests' seed rows.
- No change to fixtures or other test files.

## Assumptions
- Verified against current source: three existing tests (`test_dlq_promotion_when_consumer_delivery_failure_count_gte_max_retry`, `test_requeue_returns_dlq_imminent_when_consumer_delivery_failure_count_gte_max_retry`, `test_dlq_requeue_increments_dlq_requeue_count_not_consumer_delivery_failure_count`) insert a delivery row with `acked = 1` and a count at the limit and expect promotion; the adopted rule forbids promotion with an ACKed row, so their seed data must use `acked = 0`.
- Verified against current source: the other tests in this file and in `test_eventbus_dlq.py` and `test_eventbus_requeue_edge_cases.py` seed `acked = 0` rows with a count at the limit for one consumer, which stay promotable.
- Depends on procedures 01 and 02.

## Design decisions
- Sweep tests use the existing pattern (`open_db`, direct inserts, `sweep_orphans`); inline tests use the `client` fixture, seed rows through the app's connection with a count of `max_retry - 1` and a `seeded-attempt` marker, and POST `/nack`.
- Cases for both paths: another consumer below the limit (no promotion); another consumer ACKed (no promotion); all consumers at the limit (promotion; for the inline path, the NACK of the last consumer promotes); and an event with no delivery rows (not promoted by the sweep).

## Alternatives considered
- Put the tests in a new file: rejected; the plan fixes this file as the target.

## Implementation
### Target file
`tests/eventbus/test_eventbus_dlq_promotion.py`

### Procedure
1. Re-read the three seeded tests and the fixtures.
2. Change `acked` from `1` to `0` in the three seed inserts and add a short comment that the consumer has exhausted its retries without ACKing.
3. Add `class TestMultiConsumerPromotion` with these tests: `test_sweep_does_not_promote_when_other_consumer_below_limit`, `test_sweep_does_not_promote_when_other_consumer_acked`, `test_sweep_promotes_when_all_consumers_exhausted`, `test_sweep_ignores_event_without_delivery_rows`, `test_inline_does_not_promote_when_other_consumer_below_limit`, `test_inline_does_not_promote_when_other_consumer_acked`, `test_inline_promotes_when_last_consumer_reaches_limit`.
4. Run the file; confirm the new "does not promote" tests fail against the pre-change code (use `git stash` on the two source files or run before applying procedures 01 and 02) and pass after.
5. Run the whole `tests/eventbus` directory.

### Method
- Use the Edit tool for the three seed changes and append the class at the end of the file.

### Details
- Assertions per test: the sweep's return value, existence of `deadletter/<event_id>.json`, and `events.dlq_at`; for inline tests, the NACK response (`dlq_promoted` absent or true) and `events.dlq_at`.
- Seed a second consumer row for `consumer-B` with `acked = 0` and a count below the limit, or with `acked = 1`.

## Compatibility considerations
- Test-only change.

## Security considerations
N/A: test code only.

## Rollback considerations
Revert with `git revert` of the implementing commit, or `git checkout -- tests/eventbus/test_eventbus_dlq_promotion.py` before it is committed.

## Validation plan
- Run `uv run pytest tests/eventbus/test_eventbus_dlq_promotion.py` then `tests/eventbus`; run `ruff` and `mypy`; record diff-cover for the changed lines per `rules/toolchain.md` section 7.

## Completion criteria
- The new tests cover the four multi-consumer cases for both paths and pass; the three corrected tests pass; the full eventbus suite passes.

## Out of scope
- Source changes, documents, and other test files.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Correct the three seeded tests | Completed | 20261012-105300 | 20261012-105300 | — Three seeded tests changed to acked=0 |
| 2 | Add the multi-consumer test class | Completed | 20261012-105300 | 20261012-105300 | — Added TestMultiConsumerPromotion (7 tests); 5 fail on the pre-change code, all pass after |
| 3 | Run the file and tests/eventbus, ruff, mypy, and diff-cover | Completed | 20261012-105300 | 20261012-105300 | — tests/eventbus passes; diff-cover 100% on changed source lines |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-004`
- **Source issue**: issues/20261012-100156_eb019dlqmulti_resolve-multi-consumer-dlq-promotion-rule-mismatch-between-adr-006-and-code.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261012-102459_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261012-104559
- **Related target files**: tests/eventbus/test_eventbus_dlq_promotion.py