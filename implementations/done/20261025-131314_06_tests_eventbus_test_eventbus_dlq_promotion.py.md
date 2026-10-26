## Goal

Verify that DLQ `total` and `items` describe one consistent snapshot when a promotion happens around a list/read (`REQ-004`): the combined count+fetch under a single lock must not expose a torn page during a concurrent `sweep_orphans` promotion.

## Scope

- Modify `tests/eventbus/test_eventbus_dlq_promotion.py`: add a test that lists the DLQ while a promotion is in flight and asserts snapshot consistency.
- Do not modify `scripts/eventbus/dlq_route.py` — the single-lock snapshot lives there (seq-02).

## Assumptions

- `dlq_list()` runs one `run_with_db_lock` closure calling both `count_dlq()` and `fetch_dlq()`, so `total` and `items` come from one snapshot (`REQ-004`).
- Promotion seeds a `consumer_delivery` row with `consumer_delivery_failure_count >= max_retry` and calls `sweep_orphans(db, deadletter, max_retry)`, which writes a new DLQ file and sets `dlq_at`.
- The `/dlq` endpoint is operator-authenticated; the promotion path uses `open_db` + `sweep_orphans` directly.

## Design decisions

- **Drive a list through HTTP while a promotion runs in a worker thread**, and assert every response is internally consistent (`len(items) <= total`, non-negative offset bounds). This catches a torn count/fetch where `items` exceeds `total` or pages overlap oddly.
- **Assert eventual convergence**: after the promotion settles, a final list reports `total >= 1` including the promoted event.

## Alternatives considered

- Asserting exact equality of `total` before and after: rejected — a promotion legitimately changes `total`; the invariant is per-response internal consistency plus eventual convergence, not a frozen count.

## Implementation

### Target file

`tests/eventbus/test_eventbus_dlq_promotion.py`

### Procedure

1. Add `test_dlq_list_snapshot_consistent_during_promotion (new)`: publish an event, seed `consumer_delivery_failure_count = max_retry`, then run GET `/dlq` in a polling loop in the main thread while `sweep_orphans` promotes the event in a worker thread; assert each response is internally consistent and the final report includes the promoted event.

### Method

```python
def test_dlq_list_snapshot_consistent_during_promotion(
    self, client: TestClient, tmp_path: Path
) -> None:
    import threading

    from eventbus.db import open_db
    from eventbus.dlq import sweep_orphans

    body = _event("dlq_promo")
    assert client.post("/publish", json=body).status_code == 200
    event_id = body["event_id"]

    dlq_headers = {"Authorization": "Bearer operator-token"}
    stop = threading.Event()
    errors: list[str] = []

    def _promote() -> None:
        db = open_db(str(tmp_path / "eventbus.sqlite"))
        try:
            db.execute(
                "INSERT INTO consumer_delivery "
                "(consumer_id, event_id, acked, consumer_delivery_failure_count) "
                "VALUES ('consumer-A', ?, 0, 2)",
                (event_id,),
            )
            db.commit()
            sweep_orphans(db, str(tmp_path / "deadletter"), max_retry=2)
        finally:
            db.close()

    worker = threading.Thread(target=_promote)
    worker.start()

    while not stop.is_set():
        r = client.get("/dlq?limit=100&offset=0", headers=dlq_headers)
        assert r.status_code == 200
        body_json = r.json()
        # One snapshot: items never exceed the reported total.
        assert len(body_json["items"]) <= body_json["total"]
        assert body_json["total"] >= 0
        assert body_json["offset"] == 0
    stop.set()
    worker.join()

    # Convergence: the promoted event is now visible.
    r = client.get("/dlq?limit=100&offset=0", headers=dlq_headers)
    assert r.json()["total"] >= 1
    ids = {item["event_id"] for item in r.json()["items"]}
    assert event_id in ids
```

> Note: if the platform does not allow reliable interleaving, fall back to a coarse version — perform the promotion and immediately list once, asserting `len(items) <= total` and that the promoted `event_id` appears exactly once (no duplicate page).

### Details

- The per-response invariant `len(items) <= total` is what a torn count/fetch (count taken before promotion, fetch after, or vice versa) would break; the single-lock snapshot guarantees it.
- `sweep_orphans` returns the promotion count; the worker commits and promotes under its own handle, mirroring the other tests in this file.

## Compatibility considerations

- Adds one test method to `TestDLQPromotionSemantics`; requires the seq-02 single-lock snapshot to exist.

## Security considerations

- No change: promotion and listing use their existing auth paths.

## Rollback considerations

- Remove `test_dlq_list_snapshot_consistent_during_promotion (new)`.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `scripts/eventbus/dlq_route.py` | Integration: DLQ snapshot consistency during promotion | `uv run pytest tests/eventbus/` | `total`/`items` one snapshot; promoted event visible once |
| `scripts/eventbus/*` | Static analysis | `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/`, `uv run bandit -r scripts/ -c pyproject.toml -ll`, `PYTHONPATH=scripts uv run lint-imports` | Clean |

## Completion criteria

- `test_dlq_list_snapshot_consistent_during_promotion (new)` asserts per-response `len(items) <= total` throughout a concurrent promotion and converges to a list containing the promoted event.

## Out of Scope

- Requeue transaction/rollback — handled by the sibling procedure for `test_eventbus_requeue_edge_cases.py` (`REQ-002`).
- Pagination timestamp paths — handled by the sibling procedure for `test_eventbus_dlq_pagination.py` (`REQ-004`, `REQ-005`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Done | 2026-10-26 | 2026-10-26 | Added `test_dlq_list_snapshot_consistent_during_promotion` to `TestDLQPromotionSemantics`. Deviation from the doc snippet: its `while not stop.is_set()` polling loop never sets `stop` inside the loop (infinite-loop defect, flagged by the existing seq-06 caveat); final version polls GET `/dlq` while the promotion worker thread is alive, bounded to 50 iterations, then joins. Auth uses the file's existing `client` fixture headers (`Bearer test-token`) instead of a separate operator-token header. |
| 2 | Add or update tests per Validation plan | Done | 2026-10-26 | 2026-10-26 | Each in-flight response asserts `len(items) <= total`, `total >= 0`, `offset == 0`; convergence asserts the promoted `event_id` appears exactly once. Full suite: 336 passed, 1 skipped across 2 random-order runs. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Done | 2026-10-26 | 2026-10-26 | ruff clean; `run_validation_gates.py`: all checks Pass. |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Done | 2026-10-26 | 2026-10-26 | No docs change required (test-only procedure). |

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
- **Requirement ID**: `REQ-004` (DLQ `total`/`items` one snapshot during promotion)
- **Source issue**: `issues/20261023-154325_eventbus001_dlq-requeue-transactional.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261025-095644_eventbus001_dlq-requeue-transactional.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261025-131314
- **Related target files**: `tests/eventbus/test_eventbus_dlq_promotion.py`
