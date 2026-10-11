# Implementation Procedure: Fix eventbus test failures caused by delivery_repo.py API change

## Goal

Fix 17 failing tests across 8 test files caused by the per-consumer delivery state migration (commit b5663a371). The root cause is a mismatch between the new `ack_event_for_consumer()` return signature (3 values) and test expectations (4 values), plus stale SQL references in test fixtures.

## Scope

- `tests/eventbus/test_eventbus_offsets.py` — 4 tests: unpack 4 values expecting 3
- `tests/eventbus/test_eventbus_ack_endpoint.py` — 2 tests: KeyError 'already_acked', acked != 1
- `tests/eventbus/test_eventbus_ack_nack.py` — 2 tests: KeyError 'already_acked', 200 != 409
- `tests/eventbus/test_eventbus_restart_resume.py` — 2 tests: unpack 4 values expecting 3
- `tests/eventbus/test_eventbus_dlq_pagination.py` — 1 test: missing `last_nack_attempt` column
- `tests/eventbus/test_eventbus_concurrent.py` — 2 tests: concurrent ack assertion, missing column
- `tests/eventbus/test_eventbus_dlq_promotion.py` — 3 tests: incorrect number of bindings

## Assumptions

- The implementation change in `delivery_repo.py` is correct: `ack_event_for_consumer()` now returns `(found, newly_acked, seq)` — 3 values, not 4.
- The `consumer_delivery_failure_count` column is the authoritative DLQ promotion metric (not `delivery_failure_count`).
- Tests should be updated to match the new contract, not the other way around.

## Design decisions

- REQ-004: `ack_event_for_consumer()` return type changed from `tuple[bool, bool, bool, int | None]` to `tuple[bool, bool, int | None]` — the `already_acked` boolean was removed because `newly_acked` already conveys the same information (True = newly acked, False = already acked).
- REQ-001/REQ-003: Per-consumer delivery state means each consumer tracks its own ack/nack independently. Tests that assumed shared delivery state must be updated.
- REQ-002: DLQ promotion now uses `consumer_delivery_failure_count` instead of `delivery_failure_count`.

## Alternatives considered

1. Restore the 4-value return from `ack_event_for_consumer()` — rejected because it reintroduces the `already_acked` redundancy that was intentionally removed.
2. Update only the failing tests individually — chosen approach, minimal scope.
3. Add a compatibility shim layer — rejected because it adds unnecessary complexity for a known breaking change.

## Implementation

### Target file

`tests/eventbus/` — 8 test files across 6 categories of failure

### Procedure

1. Fix 4-value unpacking to 3-value unpacking (8 tests)
2. Remove `already_acked` assertions from HTTP response checks (2 tests)
3. Fix SQL column references in test fixtures (3 tests)
4. Fix concurrent ack assertion logic (1 test)
5. Fix SQL binding parameter counts (3 tests)
6. Fix HTTP status code expectations (1 test)

### Method

Update each failing test to match the new `ack_event_for_consumer()` contract:
- Replace `_, _, _, _` or `found, newly_acked, _, _` patterns with `found, newly_acked, _`
- Remove `already_acked` key assertions from HTTP responses
- Update SQL INSERT statements to include `consumer_last_nack_attempt` column
- Fix concurrent ack counting logic for per-consumer semantics
- Update SQL binding parameters to match current schema

### Details

#### 1. Fix 4-value unpacking → 3-value unpacking (8 tests)

**File: `tests/eventbus/test_eventbus_offsets.py`**

- Line 136: `found, newly_acked, result_seq, _ = ack_event_for_consumer(...)` → `found, newly_acked, result_seq = ack_event_for_consumer(...)`
- Line 412: `_, newly_acked, _, _ = ack_event_for_consumer(...)` → `_, newly_acked, _ = ack_event_for_consumer(...)`
- Line 583: `found, newly_acked, seq, _ = ack_event_for_consumer(...)` → `found, newly_acked, seq = ack_event_for_consumer(...)`
- Line 614: `found1, _, seq1, _ = ack_event_for_consumer(...)` → `found1, _, seq1 = ack_event_for_consumer(...)`

**File: `tests/eventbus/test_eventbus_restart_resume.py`**

- Line 223: `_, newly_acked_a, _, _ = ack_event_for_consumer(...)` → `_, newly_acked_a, _ = ack_event_for_consumer(...)`
- Line 227: `_, newly_acked_b, _, _ = ack_event_for_consumer(...)` → `_, newly_acked_b, _ = ack_event_for_consumer(...)`
- Line 342: `_, newly_acked_c, _, _ = ack_event_for_consumer(...)` → `_, newly_acked_c, _ = ack_event_for_consumer(...)`
- Line 396: `_, newly_acked_a, _, _ = ack_event_for_consumer(...)` → `_, newly_acked_a, _ = ack_event_for_consumer(...)`

#### 2. Remove `already_acked` assertions (2 tests)

**File: `tests/eventbus/test_eventbus_ack_endpoint.py`**

- Line 161: `assert row is not None and row["acked"] == 1` — This test expects `acked == 1` but the per-consumer model means the consumer may have acked while another hasn't. Verify the test's intent: if it's testing "same consumer double-ack", the assertion should check `row["acked"] == 1` (which passes). If it's testing "different consumer can still ack", the test setup needs adjustment.
- Line 196: `assert data["already_acked"] is True` — Remove this assertion. The `already_acked` field was removed from the response. Replace with `assert data["status"] == "already_acked"` or verify the HTTP status code is 200 (idempotent ACK).

**File: `tests/eventbus/test_eventbus_ack_nack.py`**

- Line 232: `assert data["already_acked"] is True` — Same fix as above. Remove `already_acked` assertion, replace with HTTP status code verification.

#### 3. Fix SQL column references in test fixtures (3 tests)

**File: `tests/eventbus/test_eventbus_dlq_pagination.py`**

- Line 78: `_simulate_delivery(client, event_id, "consumer-A")` — The fixture inserts into `consumer_delivery` without `last_nack_attempt` column. Add `consumer_last_nack_attempt` to the INSERT statement.

**File: `tests/eventbus/test_eventbus_concurrent.py`**

- Line 179: Same issue — SQL INSERT missing `consumer_last_nack_attempt` column.

**File: `tests/eventbus/test_eventbus_dlq_promotion.py`**

- Lines 113, 144, 175: SQL INSERT statements missing `consumer_last_nack_attempt` column. Add the column to all three INSERT statements.

#### 4. Fix concurrent ack assertion logic (1 test)

**File: `tests/eventbus/test_eventbus_concurrent.py`**

- Line 110: `assert newly_acked_count == 1` — Under per-consumer model, multiple consumers can ack the same event independently. The assertion should count newly_acked events per consumer, not globally. Change to `assert newly_acked_count >= 1` or adjust the test to use a single consumer.

#### 5. Fix SQL binding parameter counts (3 tests)

**File: `tests/eventbus/test_eventbus_dlq_promotion.py`**

- Lines 113, 144, 175: `Incorrect number of bindings supplied. The current statement uses 2, and there are 3 supplied.` — These INSERT statements reference `consumer_delivery_failure_count` but the binding count doesn't match. Ensure the INSERT includes all columns being bound.

#### 6. Fix HTTP status code expectation (1 test)

**File: `tests/eventbus/test_eventbus_ack_nack.py`**

- Line 480: `assert resp.status_code == 409` — Under per-consumer model, NACK after another consumer has ACKed should return 200 (the NACK is for a different consumer's delivery). The 409 response is only returned when the SAME consumer has already ACKed. Change to `assert resp.status_code == 200` or adjust the test scenario.

## Compatibility considerations

- The change modifies test expectations to match the new per-consumer delivery state contract.
- Existing callers of `ack_event_for_consumer()` expect 3 return values — no backward compatibility issues.
- The `already_acked` field removal from HTTP responses is a breaking change for any external consumers relying on it.

## Security considerations

- No security implications. The change affects test assertions only.

## Rollback considerations

- If the merge causes issues, revert the test changes and re-evaluate whether the implementation change (3-value return) is correct.
- If the `consumer_last_nack_attempt` column addition causes issues, restore the original INSERT statements temporarily until the migration is confirmed.

## Validation plan

| Target | Strategy | Tool / Command | Expected Outcome |
|--------|----------|----------------|------------------|
| All eventbus tests | Integration: verify all tests pass | `uv run pytest tests/eventbus/ -v` | 0 failures |
| delivery_repo.py | Unit: verify return signature | rg + manual inspection | 3-value return confirmed |
| Test files | Lint/type: ruff, mypy | `uv run ruff check`, `uv run mypy --no-namespace-packages` | No lint/type errors |
| Schema consistency | Verify SQL matches schema | rg against schema.sql | Column references match |

## Completion criteria

- [ ] All 17 failing tests pass after the fix.
- [ ] No regressions in the 316 passing tests (full suite: 333 total).
- [ ] `ack_event_for_consumer()` return signature is consistently 3 values across all callers.
- [ ] No `already_acked` references remain in test assertions.
- [ ] All SQL INSERT statements include `consumer_last_nack_attempt` column where applicable.
- [ ] ruff and mypy pass with no errors.

## Out of scope

- Changes to `scripts/eventbus/delivery_repo.py` — the implementation is correct; only tests need updating.
- Changes to `scripts/eventbus/schema.py` — the schema migration is correct; only test fixtures need updating.
- Changes to `scripts/eventbus/ack_route.py` — covered by separate implementation procedure document.
- DLQ promotion logic changes — already implemented per REQ-002.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Investigate root cause of test failures | Pending | — | — | |
| 2 | Fix test assertions to match new API contract | Pending | — | — | |
| 3 | Fix SQL column references in test fixtures | Pending | — | — | |
| 4 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 5 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: REQ-001, REQ-002, REQ-003, REQ-004
- **Source issue**: N/A: no standalone requirement document is generated
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261008-160952_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261011-080000
- **Related target files**: `tests/eventbus/` (8 files)
