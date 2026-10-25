## Goal

Add repository-level NACK idempotency tests to `tests/eventbus/test_eventbus_ack_nack.py` covering the recommended latest-key-only contract: a repeated delivery-attempt key is a no-op on the per-consumer failure counter, a distinct key increments once, and the retention-window boundary (`NACK(A)`, `NACK(B)`, `NACK(A retry)`) behaves as documented (`REQ-003`, `REQ-004`). Retain the existing `consumer_id=None` tests (the path is internalized, not removed, per `REQ-007`).

## Scope

- **In-Scope** (`tests/eventbus/test_eventbus_ack_nack.py` only):
  - Add `TestNackEvent` methods for sequential same-key no-op, distinct-key-once, concurrent same-key collapse, retention-window boundary, and `max_retry - 1` boundary.
  - Retain the existing `consumer_id=None` tests unchanged (the path is annotated internal-only in `delivery_repo.py`, seq 02).
- **Out-of-Scope** (handled by sibling documents this Plan generates):
  - Route key source + keyless handling (`scripts/eventbus/ack_route.py`, seq 01).
  - Repository guard live-ification (`scripts/eventbus/delivery_repo.py`, seq 02).
  - HTTP-level idempotency tests (`tests/eventbus/test_eventbus_ack_endpoint.py`, seq 06).
  - Contract doc (seq 07), ADR close (seq 08).

## Assumptions

- UNK-03 recommended = latest-key-only: the repository deduplicates only a repeat of the most recent attempt key; a non-latest key counts as a new attempt. The boundary test asserts this documented behavior.
- UNK-02 = client-generated key: repo-level tests call `nack_event(..., last_nack_attempt=<key>)` directly with an explicit key, mirroring what the route passes through (seq 01).
- REQ-007 resolved by internalize-with-comment (option a): the `consumer_id=None` path stays, so `test_nack_event_increments_failure_count`, `test_nack_event_increments_again`, and `test_nack_no_consumer_id_unaffected_by_consumer_acks` remain valid and are NOT modified.
- DLQ promotion stays gated on the per-consumer failure count (`INV-13`); the `max_retry - 1` boundary test exercises promotion indirectly.
- `NackResult` carries `consumer_failure_count` when `consumer_id` is provided (`NackResult("ok", consumer_failure_count=1)`); it is `None` when `consumer_id` is omitted.

## Design decisions

- **Repo-layer coverage of Acceptance 1/2/4.** Idempotency is verified at the repository where the guard lives: sequential/concurrent same-key no-op (`REQ-003`), distinct-key-once (`REQ-003`), and the retention-window boundary (`REQ-004`). HTTP-level coverage is the sibling seq 06 row.
- **Latest-key-only boundary contract.** The sequence `NACK(A)`, `NACK(B)`, `NACK(A retry)` is asserted to yield three increments under the recommended model — the "A retry" is a non-latest key and counts as a new attempt, matching the documented `eventbus_12` contract. This pins the chosen scope so a future bounded-set change is a deliberate, tested delta.

## Alternatives considered

- **Bounded-set boundary test:** if UNK-03 selected the storage change, `NACK(A retry)` after `NACK(B)` would dedup (count stays 2). Rejected as default; the latest-key-only assertion is recorded so the two scopes are distinguishable in tests.
- **HTTP-only coverage:** deferring idempotency verification entirely to seq 06. Rejected — the guard lives in the repository, so the primary no-double-count evidence belongs at the repo layer (`REQ-003`).

## Implementation

### Target file

`tests/eventbus/test_eventbus_ack_nack.py`

### Procedure

1. In `TestNackEvent` (test_eventbus_ack_nack.py:333), add a private helper to insert an event row following the existing inline pattern in `test_nack_event_increments_failure_count` (test_eventbus_ack_nack.py:340-354).
2. Add the idempotency test methods below (all `(new)`), each calling `nack_event(db, event_id, consumer_id="consumer-A", last_nack_attempt=<key>)` and asserting the resulting `NackResult`.
3. Leave the existing `consumer_id=None` tests (`test_nack_event_increments_failure_count`, `test_nack_event_increments_again`, `test_nack_no_consumer_id_unaffected_by_consumer_acks`) unchanged.
4. Run the validation sequence.

### Method

`TestNackEvent` (test_eventbus_ack_nack.py:333-581) currently covers basic nack semantics: `test_nack_event_increments_failure_count` (test_eventbus_ack_nack.py:340, `consumer_id=None`), `test_nack_event_increments_again` (test_eventbus_ack_nack.py:359, `consumer_id=None`), `test_nack_event_not_found` (test_eventbus_ack_nack.py:381), `test_nack_per_consumer_acked_then_nack_returns_invalid_transition` (test_eventbus_ack_nack.py:387), `test_nack_different_consumer_after_same_consumer_acks` (test_eventbus_ack_nack.py:417, asserts `NackResult("ok", consumer_failure_count=1)`), and `test_nack_no_consumer_id_unaffected_by_consumer_acks` (test_eventbus_ack_nack.py:447, `consumer_id=None`). Each existing test inserts an event inline via `db.execute(...)` then imports `nack_event` from `eventbus.db`. The new methods follow the same shape and pass an explicit `last_nack_attempt` key.

```python
# test_eventbus_ack_nack.py — sequential same-key no-op (REQ-003)  (new)
def test_nack_same_key_no_increment(self, db: sqlite3.Connection) -> None:
    """A repeated delivery-attempt key does not increment the failure counter (REQ-003)."""
    from eventbus.db import nack_event

    ev = _event()
    # insert event inline (same pattern as test_nack_event_increments_failure_count)
    ...
    nack_event(db, ev["event_id"], consumer_id="consumer-A", last_nack_attempt="key-A")
    result = nack_event(db, ev["event_id"], consumer_id="consumer-A", last_nack_attempt="key-A")
    assert result == NackResult("ok", consumer_failure_count=1)   # second call is a no-op
```

```python
# test_eventbus_ack_nack.py — distinct key increments once + retention boundary (REQ-003, REQ-004)  (new)
def test_nack_distinct_key_and_boundary(self, db: sqlite3.Connection) -> None:
    """Different keys each count once; a non-latest key counts as a new attempt (latest-key-only)."""
    from eventbus.db import nack_event

    ev = _event()
    ...
    nack_event(db, ev["event_id"], consumer_id="consumer-A", last_nack_attempt="A")  # count=1
    nack_event(db, ev["event_id"], consumer_id="consumer-A", last_nack_attempt="B")  # count=2
    nack_event(db, ev["event_id"], consumer_id="consumer-A", last_nack_attempt="A")  # "A retry": non-latest → count=3
    # assert consumer_delivery_failure_count == 3 (documented latest-key-only boundary)
```

```python
# test_eventbus_ack_nack.py — concurrent same-key collapse (REQ-003)  (new)
@pytest.mark.asyncio
async def test_nack_concurrent_same_key_collapses(
    self, db: sqlite3.Connection
) -> None:
    """Concurrent retries of the same attempt collapse to a single increment (REQ-003)."""
    import asyncio

    from eventbus.db import nack_event

    ev = _event()
    ...
    await asyncio.gather(
        nack_event(db, ev["event_id"], consumer_id="consumer-A", last_nack_attempt="key-A"),
        nack_event(db, ev["event_id"], consumer_id="consumer-A", last_nack_attempt="key-A"),
        nack_event(db, ev["event_id"], consumer_id="consumer-A", last_nack_attempt="key-A"),
    )
    # assert consumer_delivery_failure_count == 1
```

### Details

- **`REQ-003` (no double count):** `test_nack_same_key_no_increment` (new) asserts the second identical-key NACK returns `NackResult("ok", consumer_failure_count=1)`; `test_nack_distinct_key_and_boundary` (new) asserts distinct keys each increment; `test_nack_concurrent_same_key_collapses` (new) asserts concurrent same-key retries collapse to one increment.
- **`REQ-004` (retention boundary):** `test_nack_distinct_key_and_boundary` (new) pins the latest-key-only contract — `NACK(A)`, `NACK(B)`, `NACK(A retry)` yields three increments because the "A retry" is a non-latest key. This is the recommended-model assertion; a bounded-set adoption would flip the last step to a no-op (a deliberate, tested delta).
- **`REQ-007` (`consumer_id=None` retained):** the internalize-with-comment resolution keeps the path, so `test_nack_event_increments_failure_count`, `test_nack_event_increments_again`, and `test_nack_no_consumer_id_unaffected_by_consumer_acks` stay valid and unmodified.
- **`INV-13` preserved:** the `max_retry - 1` boundary (Acceptance 2) is covered by the HTTP-level seq 06 row, which drives the same counter through `/nack` and promotion.

## Compatibility considerations

- Purely additive tests; no existing test is modified, so no backward-incompatibility.
- The new tests call `nack_event()` with an explicit `last_nack_attempt`, matching the signature unchanged by seq 02.

## Security considerations

- Test-only change; no credentials, secrets, or injection surface introduced. Keys are opaque string literals in fixtures.

## Rollback considerations

- Revert the `test_eventbus_ack_nack.py` edit (`git checkout tests/eventbus/test_eventbus_ack_nack.py`) removes only the added tests. Single logical commit; revert the commit.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| Repo idempotency tests (new) | Unit: same-key no-op, distinct-once, concurrent collapse, boundary | `uv run pytest tests/eventbus/test_eventbus_ack_nack.py` | Same-key repeat = no-op; distinct = +1; concurrent collapse = 1; boundary = 3 |
| Existing `consumer_id=None` tests retained | Regression | `uv run pytest tests/eventbus/test_eventbus_ack_nack.py` | Pre-existing nack-semantics tests still pass |
| `delivery_repo.py` promotion unchanged | Integration | `uv run pytest tests/eventbus/test_eventbus_dlq_promotion.py` | `INV-13` promotion unchanged |
| Types / format | Quality gates | `uv run mypy`; `uv run ruff` | Pass |
| Import boundary | Architecture | `PYTHONPATH=scripts uv run lint-imports` | `eventbus-is-isolated` KEPT |

## Completion criteria

- `TestNackEvent` gains sequential same-key no-op, distinct-key-once, concurrent same-key collapse, and retention-window boundary tests, all passing.
- The existing `consumer_id=None` tests are unmodified and still pass.
- ruff, mypy, bandit, vulture, lint-imports pass; `test_eventbus_ack_nack.py` asserts same-key no-op and distinct-key +1.

## Out of Scope

- Route key source + keyless handling (`scripts/eventbus/ack_route.py`, seq 01).
- Repository guard live-ification (`scripts/eventbus/delivery_repo.py`, seq 02).
- HTTP-level idempotency tests (`tests/eventbus/test_eventbus_ack_endpoint.py`, seq 06).
- Contract doc (seq 07), ADR close (seq 08).
- UNK-03 bounded-set boundary assertion — recorded as the latest-key-only delta, not implemented.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add repo-level idempotency tests (sequential/concurrent/timeout/different-keys/boundary); retain `consumer_id=None` tests | Pending | — | — | Latest-key-only boundary asserted (recorded) |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-003`, `REQ-004`, `REQ-007`
- **Source issue**: `issues/20261023-154326_eventbus005_nack-idempotency-retries.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261025-120857_eventbus005_nack-idempotency-retries.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261025-203128
- **Related target files**: `tests/eventbus/test_eventbus_ack_nack.py`
