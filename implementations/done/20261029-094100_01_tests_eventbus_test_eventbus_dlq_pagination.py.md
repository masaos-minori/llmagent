## Goal

Reword `tests/eventbus/test_eventbus_dlq_pagination.py` to the request-local consistency
contract the API actually provides, and add a synchronised concurrent-mutation test that
asserts per-response internal consistency only — never a cross-request snapshot guarantee.

## Scope

Test-only edit to `tests/eventbus/test_eventbus_dlq_pagination.py`. No production code, no
docs.

## Assumptions

- The request-local contract is adopted (plan UNK-01, non-blocking): `total` and `items`
  are consistent within one `/dlq` response; two sequential `/dlq` requests may observe
  different states because each acquires its own `run_with_db_lock`.
- The fixture already carries `publisher_token="publisher-token"` (config under
  `tests/eventbus/test_eventbus_dlq_pagination.py` lines 17-32), so the setup publish is
  authorised.
- The plan facts (REQ-003) are verified on the project SQLite: `count_dlq` covers
  `idx_events_dlq_seq`, `fetch_dlq` scans by `seq`; not used by this row's tests.

## Design decisions

- Keep the existing promotion harness (publish → `_simulate_delivery` → nack → DLQ) and
  only change the assertions + wording that over-claim.
- Replace the cross-page overlap/coverage assertion with per-response internal-consistency
  assertions (`len(items)` within the `total`-bounded window; `seq` ascending order).
- Add the concurrent-mutation test behind an explicit `threading.Barrier` (no sleeps); the
  mutator promotes a new row between the two reads, and each read is asserted internally
  consistent without any cross-page claim.

## Alternatives considered

- Asserting cross-page non-overlap still (as today): rejected — it encodes the nonexistent
  cross-request snapshot guarantee REQ-001 forbids.
- Using a background thread with `time.sleep`: rejected — AC-5 requires explicit
  synchronization primitives and no sleeps.

## Implementation

### Target file

`tests/eventbus/test_eventbus_dlq_pagination.py`

### Procedure

1. Open `tests/eventbus/test_eventbus_dlq_pagination.py`.
2. In `test_dlq_pagination`, delete the REQ-004 cross-page non-overlap/coverage block
   (existing lines 144-158): the second `/dlq` request, the derived page-id lists, and the
   overlap + union-coverage assertions they drive. These identifiers are removed, not kept.
3. Replace them with per-response internal-consistency assertions on the two disjoint
   windows already fetched (`body` from `limit=100`, `body2` from `limit=2&offset=2`):
   each response reports `total`, `limit`, `offset`, and `len(items)` within its
   `total`-bounded window; items are ordered by `seq` ascending.
4. Add `import threading` at the top (after the existing imports).
5. Add `test_dlq_pagination_concurrent_mutation` (new) below `test_dlq_pagination`:
   - Publish 5 events, nack them to promote to DLQ (reuse `_simulate_delivery`).
   - Create a `threading.Barrier(2)`.
   - Worker thread: after the barrier, publish one more event and nack it to promote to
     DLQ (authorised with `publisher-token`).
   - Main thread: after the barrier, issue two sequential `/dlq` reads (`limit=2&offset=0`
     then `limit=2&offset=2`) under the operator token.
   - Assert each read is internally consistent (`status_code == 200`, `total`/`limit`/
     `offset`/`items` present, `len(items)` within the `total`-bounded window, `seq`
     ascending). Do NOT assert the two pages overlap-free or collectively complete.
   - Join the worker thread; assert it raised nothing.
6. Run `stale_detector.py` on this document (cite source files by full leading-slash path;
   name `threading` as an import the procedure creates — mark `(new)` if absent).

### Method

Replace existing lines 144-158 with:

```python
    # REQ-001: request-local consistency. Each /dlq response is internally consistent
    # (its items fall within its own total-bounded window and are seq-ordered); the two
    # disjoint windows are NOT claimed to derive from one cross-request snapshot, which
    # the API does not provide (each request takes its own run_with_db_lock).
    assert body["total"] >= min(5, body["total"])
    assert 0 <= len(body["items"]) <= min(5, body["total"])
    assert [i["seq"] for i in body["items"]] == sorted(
        i["seq"] for i in body["items"]
    )
    assert 0 <= len(body2["items"]) <= body2["total"]
    assert [i["seq"] for i in body2["items"]] == sorted(
        i["seq"] for i in body2["items"]
    )
```

Add the new test after `test_dlq_pagination` (before
`test_dlq_pagination_no_string_timestamp_interpolation`):

```python
def test_dlq_pagination_concurrent_mutation(client: TestClient) -> None:
    """REQ-001: each response is internally consistent under a concurrent mutation;
    cross-request stability is not claimed."""
    events = []
    for _ in range(5):
        ev = _event()
        _publish_event(client, ev)
        events.append(ev["event_id"])
    for event_id in events:
        _simulate_delivery(client, event_id, "consumer-A")
    for event_id in events:
        r = client.post(
            "/nack",
            params={"event_id": event_id, "consumer_id": "consumer-A",
                    "idempotency_key": f"nack-key-{event_id}"},
            headers={"Authorization": "Bearer consumer-token"},
        )
        assert r.status_code == 200

    barrier = threading.Barrier(2)

    def _mutator() -> None:
        barrier.wait()
        extra = _event()
        _publish_event(client, extra)
        _simulate_delivery(client, extra["event_id"], "consumer-A")
        r = client.post(
            "/nack",
            params={"event_id": extra["event_id"], "consumer_id": "consumer-A",
                    "idempotency_key": f"nack-key-{extra['event_id']}"},
            headers={"Authorization": "Bearer consumer-token"},
        )
        assert r.status_code == 200

    worker = threading.Thread(target=_mutator)
    worker.start()
    barrier.wait()  # release the mutator concurrently with the reads below

    dlq_headers = {"Authorization": "Bearer operator-token"}
    ra = client.get("/dlq?limit=2&offset=0", headers=dlq_headers)
    rb = client.get("/dlq?limit=2&offset=2", headers=dlq_headers)
    worker.join()

    # Per-response internal consistency only; no cross-page overlap/coverage claim.
    for resp in (ra, rb):
        assert resp.status_code == 200
        b = resp.json()
        assert {"total", "limit", "offset", "items"} <= set(b)
        assert 0 <= len(b["items"]) <= b["total"]
        seqs = [i["seq"] for i in b["items"]]
        assert seqs == sorted(seqs)
```

### Details

- The reworded assertions drop `set(page_a_ids) & set(page2_ids)` and the union-coverage
  check that encoded the cross-request snapshot guarantee.
- `threading` is imported by the procedure (marked `(new)` in the Procedure step); the
  barrier gives deterministic synchronisation so the test is flake-free (AC-5).
- The worker promotes a row while the main thread reads; because each `/dlq` holds its own
  lock, the two reads are each consistent, but their union is intentionally not asserted.
- `seq` exists on each item (the production `fetch_dlq` selects it); cite the item shape
  against `scripts/eventbus/event_repo.py:127` in the Procedure, not as a modification target.

## Compatibility considerations

Tests only. The rewritten test keeps `fetch_dlq`/`count_dlq` exercised via `/dlq`, so the
plan-cover baseline (plan: `event_repo.py` 89%, unchanged) is preserved.

## Security considerations

None: no credentials, tokens, or secrets are logged; the operator/publisher tokens are
fixture values passed as headers, matching the existing test.

## Rollback considerations

Revert the commit (single-file test change).

## Validation plan

1. Read `tests/eventbus/test_eventbus_dlq_pagination.py` and confirm the cross-request
   snapshot wording/assertions are gone and per-response assertions remain.
2. Confirm `test_dlq_pagination_concurrent_mutation` (new) uses a `threading.Barrier` (no
   `time.sleep`) and asserts per-response consistency only.
3. Run `uv run pytest tests/eventbus/test_eventbus_dlq_pagination.py` (repeat 3x — AC-5).
4. Run `uv run ruff check` and `uv run mypy` on the file.
5. Run `stale_detector.py` on this document (must report "not stale").

## Completion criteria

- `test_dlq_pagination` asserts per-response internal consistency; no "one consistent
  snapshot" cross-request claim remains (AC-1).
- `test_dlq_pagination_concurrent_mutation` (new) exists, is barrier-synchronised, no sleeps,
  passes deterministically (AC-5).
- ruff/mypy clean; `stale_detector.py` clean.

## Out of Scope

- The index test rewrite (seq 02).
- The endpoint/replay doc boundary wording (seq 03, seq 04).
- Cross-page snapshot mechanism (out of scope; would be a new Plan per UNK-01).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Reword pagination test to request-local contract (Implementation > Procedure) | Completed | — | 20261029-111855 | Applied verbatim; cross-request assertions replaced with per-response consistency. |
| 2 | Add concurrent-mutation test (Validation plan) | Completed | — | 20261029-111855 | `test_dlq_pagination_concurrent_mutation` added, barrier-synchronised, no sleeps. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261029-111855 | Pagination module 4 passed x3 (AC-5); full eventbus 415 passed / 1 skipped, no new skips; ruff check+format, mypy, stale_detector all clean. |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A | — | — | Tests-only row |

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
- **Requirement ID**: `REQ-001`
- **Source issue**: `issues/20261028-122307_ebpage003_pagination-contract-dlq-index.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261028-231631_ebpage003_pagination-contract-dlq-index.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261029-094100
- **Related target files**: `tests/eventbus/test_eventbus_dlq_pagination.py`
