## Goal

Add HTTP-level NACK idempotency tests to `tests/eventbus/test_eventbus_ack_endpoint.py` covering the recommended contract: a repeated delivery-attempt key returns a no-op 200 with an unchanged failure count, a distinct key increments once, and a keyless NACK is rejected per UNK-01 (`REQ-002`, `REQ-006`).

## Scope

- **In-Scope** (`tests/eventbus/test_eventbus_ack_endpoint.py` only):
  - Add a `TestNackEndpointIdempotency` (new) class with same-key no-op, keyless-400, and distinct-key-once HTTP tests against `/nack`.
- **Out-of-Scope** (handled by sibling documents this Plan generates):
  - Route key source + keyless handling (`scripts/eventbus/ack_route.py`, seq 01) — creates the `idempotency_key` query param these tests send.
  - Repository guard live-ification (`scripts/eventbus/delivery_repo.py`, seq 02).
  - Repo-level idempotency tests including the retention-window boundary (`tests/eventbus/test_eventbus_ack_nack.py`, seq 05).
  - Contract doc (seq 07), ADR close (seq 08).

## Assumptions

- UNK-02 = client-generated key: the route accepts the idempotency key as a NACK query parameter (created by seq 01); HTTP tests send it via the `params=` dict.
- UNK-03 recommended = latest-key-only: a repeated key dedups; a distinct key increments. The retention-window OUT-OF-ORDER boundary (`NACK(A)`, `NACK(B)`, `NACK(A retry)`) is asserted at the repo layer (seq 05), where `max_retry` promotion does not interfere.
- UNK-01 recommended = reject keyless with 400: a `/nack` request without the key returns 400 (`REQ-006`).
- The `client` fixture (`eventbus_test_tokens("test-token")`, `test_eventbus_ack_endpoint.py:20`) has no consumer-id restriction, so the ownership check passes for any `consumer_id` — matching the existing `test_nack_http_200_on_different_consumer_after_acked` pattern in `test_eventbus_ack_nack.py`.
- DLQ promotion stays gated on the per-consumer failure count (`INV-13`); with the fixture's `max_retry=2`, a second distinct increment promotes (response carries `dlq_promoted: true`), which the distinct-key test asserts rather than treats as a failure.

## Design decisions

- **HTTP evidence for the route contract.** Idempotency at the route layer proves the caller key flows through `_nack_and_promote()` → `nack_event()` and dedups (`REQ-001`, `REQ-002`). The same-key no-op and distinct-once tests assert the `consumer_delivery_failure_count` field in the `/nack` JSON response.
- **Boundary belongs at the repo layer.** The retention-window boundary needs multiple non-promoting increments on one event; the `client` fixture's fixed `max_retry=2` promotes on the second increment, so the out-of-order boundary is asserted cleanly at the repo layer (seq 05). An HTTP boundary test would require a dedicated higher-`max_retry` fixture (documented as a possible extension).

## Alternatives considered

- **Higher-`max_retry` fixture for HTTP boundary:** add a fixture with `max_retry` raised so the full `NACK(A)`/`NACK(B)`/`NACK(A retry)` sequence runs without promotion. Rejected as default — it adds fixture surface; the repo layer (seq 05) already covers the boundary deterministically.
- **HTTP-only idempotency:** deferring all idempotency verification to this file. Rejected — the guard lives in the repository, so the primary no-double-count evidence belongs at the repo layer (`REQ-003`).

## Implementation

### Target file

`tests/eventbus/test_eventbus_ack_endpoint.py`

### Procedure

1. Add a `TestNackEndpointIdempotency` (new) class after `TestAckEndpoint` in `test_eventbus_ack_endpoint.py`.
2. Add three methods using the existing `client` fixture and `_simulate_delivery` helper: same-key no-op, keyless-400, distinct-key-once. Each sends the caller key as the NACK query parameter.
3. Run the validation sequence.

### Method

The current file tests the ACK endpoint (`TestAckEndpoint`, test_eventbus_ack_endpoint.py:124) and monotonic-offset behavior (`TestAckMonotonicOffset`, test_eventbus_ack_endpoint.py:258); NACK HTTP behavior lives in the sibling `test_eventbus_ack_nack.py`. The `client` fixture (test_eventbus_ack_endpoint.py:20) builds a `TestClient` over `eventbus.app` with `test-token`. The `/nack` endpoint returns `{"event_id", "consumer_delivery_failure_count"}` and adds `dlq_promoted: true` when the per-consumer count reaches `max_retry`. The new class follows the existing `_simulate_delivery` + `client` pattern and sends the caller key as the NACK query parameter (created by seq 01).

```python
# test_eventbus_ack_endpoint.py — TestNackEndpointIdempotency (new)  (new)
class TestNackEndpointIdempotency:
    """HTTP-level NACK idempotency under the latest-key-only contract (REQ-002, REQ-006)."""

    def test_nack_same_key_no_op(self, client: Any) -> None:  # (new)
        """A repeated delivery-attempt key returns a no-op 200 with an unchanged count."""
        body = _event()
        client.post("/publish", json=body)
        _simulate_delivery(client, body["event_id"], "consumer-A")

        r1 = client.post(
            "/nack",
            params={
                "event_id": body["event_id"],
                "consumer_id": "consumer-A",
                "idempotency_key": "key-A",
            },
        )
        assert r1.status_code == 200
        assert r1.json()["consumer_delivery_failure_count"] == 1

        r2 = client.post(
            "/nack",
            params={
                "event_id": body["event_id"],
                "consumer_id": "consumer-A",
                "idempotency_key": "key-A",
            },
        )
        assert r2.status_code == 200
        assert r2.json()["consumer_delivery_failure_count"] == 1  # no-op: same key

    def test_nack_keyless_returns_400(self, client: Any) -> None:  # (new)
        """A NACK without an idempotency key is rejected with 400 (UNK-01)."""
        body = _event()
        client.post("/publish", json=body)
        _simulate_delivery(client, body["event_id"], "consumer-A")

        resp = client.post(
            "/nack",
            params={"event_id": body["event_id"], "consumer_id": "consumer-A"},
        )
        assert resp.status_code == 400

    def test_nack_distinct_key_increments_once(self, client: Any) -> None:  # (new)
        """A distinct delivery-attempt key increments the count exactly once."""
        body = _event()
        client.post("/publish", json=body)
        _simulate_delivery(client, body["event_id"], "consumer-A")

        r1 = client.post(
            "/nack",
            params={
                "event_id": body["event_id"],
                "consumer_id": "consumer-A",
                "idempotency_key": "key-A",
            },
        )
        assert r1.status_code == 200
        assert r1.json()["consumer_delivery_failure_count"] == 1

        r2 = client.post(
            "/nack",
            params={
                "event_id": body["event_id"],
                "consumer_id": "consumer-A",
                "idempotency_key": "key-B",
            },
        )
        assert r2.status_code == 200
        assert r2.json()["consumer_delivery_failure_count"] == 2  # distinct incremented once
        # count == max_retry (2) triggers promotion on this distinct attempt
        assert r2.json().get("dlq_promoted") is True
```

### Details

- **`REQ-002` (no per-request UUID dedup breakage):** `test_nack_same_key_no_op` (new) proves a repeated caller key yields two 200s with `consumer_delivery_failure_count` pinned at 1 — the dead-key problem (per-request UUID) is gone because seq 01 passes the stable caller key.
- **`REQ-006` / UNK-01:** `test_nack_keyless_returns_400` (new) asserts a keyless NACK returns 400, matching seq 01's reject-400 gate.
- **`REQ-003` (distinct increments once):** `test_nack_distinct_key_increments_once` (new) asserts the second distinct key moves the count 1 → 2; the promotion at the `max_retry` threshold (`dlq_promoted: true`) is asserted as correct `INV-13` behavior, not a test failure.
- **Boundary deferred to seq 05:** the out-of-order retention boundary is asserted at the repo layer where `max_retry` promotion does not truncate the sequence.

## Compatibility considerations

- Purely additive tests; no existing test is modified.
- The tests send the caller key query parameter created by seq 01; they are meaningful only after that route change.

## Security considerations

- Test-only change; no credentials, secrets, or injection surface introduced. Keys are opaque string literals in fixtures.

## Rollback considerations

- Revert the `test_eventbus_ack_endpoint.py` edit (`git checkout tests/eventbus/test_eventbus_ack_endpoint.py`) removes only the added class. Single logical commit; revert the commit.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `TestNackEndpointIdempotency` (new) | Integration: `/nack` same-key vs distinct vs keyless | `uv run pytest tests/eventbus/test_eventbus_ack_endpoint.py` | Same-key repeat = count 1; distinct = count 2 + promoted; keyless = 400 |
| Existing ACK endpoint tests | Regression | `uv run pytest tests/eventbus/test_eventbus_ack_endpoint.py` | `TestAckEndpoint`/`TestAckMonotonicOffset` still pass |
| Types / format | Quality gates | `uv run mypy`; `uv run ruff` | Pass |
| Import boundary | Architecture | `PYTHONPATH=scripts uv run lint-imports` | `eventbus-is-isolated` KEPT |

## Completion criteria

- `TestNackEndpointIdempotency` (new) gains same-key no-op, keyless-400, and distinct-key-once tests, all passing.
- Existing ACK-endpoint tests are unmodified and still pass.
- ruff, mypy, bandit, vulture, lint-imports pass.

## Out of Scope

- Route key source + keyless handling (`scripts/eventbus/ack_route.py`, seq 01).
- Repository guard live-ification (`scripts/eventbus/delivery_repo.py`, seq 02).
- Repo-level idempotency tests and retention boundary (`tests/eventbus/test_eventbus_ack_nack.py`, seq 05).
- Contract doc (seq 07), ADR close (seq 08).
- UNK-03 bounded-set boundary — recorded as the latest-key-only delta, not implemented.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `TestNackEndpointIdempotency` (new) class (same-key no-op, keyless-400, distinct-once) to the ACK-endpoint file | Done | 2026-10-26 | 2026-10-26 | Added 3 new tests using principal_client fixture (client fixture lacks publisher token) |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Done | 2026-10-26 | 2026-10-26 | ruff/mypy/bandit/vulture/lint-imports/radon all pass; 13/13 ack endpoint tests pass |

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
- **Requirement ID**: `REQ-002`, `REQ-006`
- **Source issue**: `issues/20261023-154326_eventbus005_nack-idempotency-retries.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261025-120857_eventbus005_nack-idempotency-retries.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261025-203128
- **Related target files**: `tests/eventbus/test_eventbus_ack_endpoint.py`
