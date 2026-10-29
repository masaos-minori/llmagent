## Goal

Pin the Option B gauge contract in `tests/eventbus/test_eventbus_slow_consumer.py`: a queue drain without unsubscribe leaves the gauge stale until a refresh, repeated `slow_consumer_count()` calls do not touch the gauge, a `/health` read refreshes it, and unsubscribe, overflow disconnect, and shutdown return it to zero (`REQ-003`; `REQ-001` and `REQ-005` through the assertions).

## Scope

Modify `tests/eventbus/test_eventbus_slow_consumer.py` only: rewrite the recovery test, change the four gauge assertions that relied on the read refreshing the gauge, and add two tests. No production code or docs.

## Assumptions

- Source claims re-verified this cycle: `_slow_gauge()` (line 177) reads the collector; `_small_broker()` (line 186) uses threshold 2 and queue size 4; `TestSlowConsumerGauge` (line 205) holds the recovery test (lines 208-221) and the unsubscribe, overflow, and shutdown tests (lines 223-260), which each assert `broker.slow_consumer_count() == 1` followed by `_slow_gauge() == 1` (lines 214-215, 228-229, 240-241, 255-256). The `client` fixture (line 19) enters `make_eventbus_client`, and `eventbus_auth_headers` is imported at line 13.
- Names created by earlier rows: `refresh_slow_consumer_gauge` is created by seq 01 (`scripts/eventbus/broker.py`), which runs first.
- The gauge is module-level and shared across tests, so the health test sets it to 0 explicitly before the `/health` request; publishing never refreshes it.
- Overlap: `plans/20261028-234655_ebtestdrift007_test-lifecycle-terminology.md` and `plans/20261029-092424_eventbus003_test-lifecycle-production-path.md` touch the shared `make_eventbus_client` helper used by this file's fixture, not this file; no overlap on this file (`tools/check_plan_target_overlaps.py`).

## Design decisions

- Change only assertions that encode the old read-refreshes-gauge behavior; leave the other tests in `TestSlowConsumer` untouched (they call `slow_consumer_count()` as a read).
- Use the collector read (`_slow_gauge()`), never a health call, to observe the gauge.

## Alternatives considered

N/A: the Plan fixes the Option B contract; no alternative test shape is needed.

## Implementation

### Target file

`tests/eventbus/test_eventbus_slow_consumer.py`

### Procedure

1. In the unsubscribe, overflow, and shutdown tests (lines 214, 228, 240, 255), replace `assert broker.slow_consumer_count() == 1` with `assert broker.refresh_slow_consumer_gauge() == 1`; keep the following `_slow_gauge() == 1` assertions.
2. Replace `test_slow_consumer_gauge_returns_to_zero_after_recovery` (lines 208-221) with `test_drain_without_unsubscribe_keeps_gauge_until_refresh` (new), as in Method.
3. Add `test_slow_consumer_count_is_a_pure_read` (new) and `test_health_read_refreshes_gauge` (new) to `TestSlowConsumerGauge`.

### Method

```python
    def test_drain_without_unsubscribe_keeps_gauge_until_refresh(self) -> None:
        broker = _small_broker()
        sub = broker.subscribe([])
        broker.publish(_event())
        broker.publish(_event())
        assert broker.refresh_slow_consumer_gauge() == 1
        assert _slow_gauge() == 1

        sub.queue.get_nowait()
        sub.queue.get_nowait()

        assert _slow_gauge() == 1  # a drain alone does not refresh the gauge
        assert broker.refresh_slow_consumer_gauge() == 0
        assert _slow_gauge() == 0

    def test_slow_consumer_count_is_a_pure_read(self) -> None:
        broker = _small_broker()
        sub = broker.subscribe([])
        broker.publish(_event())
        broker.publish(_event())
        broker.refresh_slow_consumer_gauge()
        sub.queue.get_nowait()
        sub.queue.get_nowait()

        for _ in range(3):
            assert broker.slow_consumer_count() == 0
            assert _slow_gauge() == 1  # reads never touch the gauge

    def test_health_read_refreshes_gauge(self, client: TestClient) -> None:
        from eventbus import app as eb_app
        from eventbus.broker import _slow_consumer_current

        broker = eb_app.app.state.broker
        sub = broker.subscribe([])
        try:
            for _ in range(120):  # default threshold is 100
                assert client.post("/publish", json=_event()).status_code == 200
            _slow_consumer_current.set(0)  # publish never refreshes the gauge
            resp = client.get("/health", headers=eventbus_auth_headers("monitoring"))
            assert resp.json()["slow_consumers"] == 1
            assert _slow_gauge() == 1
        finally:
            broker.unsubscribe(sub)
```

### Details

- The overflow test keeps its structure; only the first assertion changes.
- `/health` returns 503 here (slow consumer is a degraded reason); the test reads the JSON body and does not assert the status code, matching `test_health_503_when_slow_consumer_threshold_exceeded`'s precedent of an explicit 503 elsewhere.

## Compatibility considerations

N/A: test-only change; the old assertions encode the behavior seq 01 removes.

## Security considerations

N/A: fixture tokens only.

## Rollback considerations

N/A: revert the commit.

## Validation plan

1. `uv run pytest tests/eventbus/test_eventbus_slow_consumer.py -v` (repeat 3x for flakiness; the gauge is shared state).
2. `uv run pytest tests/eventbus`.
3. `uv run ruff check tests/eventbus`; `uv run ruff format --check tests/eventbus`; `uv run mypy --no-namespace-packages scripts/ tests/eventbus`.
4. `uv run python tools/stale_detector.py implementations/20261029-101659_03_tests_eventbus_test_eventbus_slow_consumer.py.md`.

## Completion criteria

- The four old gauge assertions use the explicit refresh; the recovery test is replaced by the stale-until-refresh test.
- The pure-read and health-refresh tests exist and pass; no test relies on `slow_consumer_count()` writing the gauge.
- ruff, format, and mypy are clean.

## Out of Scope

- Production code (seq 01, 02), docs (seq 04, 05), and the identifier-comment cleanup of `eventbus004` (this file is not in that Plan).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update the four gauge assertions and replace the recovery test (Implementation > Procedure/Method/Details) | Completed | 20261029-114544 | 20261029-115335 | Needs seq 01 first Changed: tests/eventbus/test_eventbus_slow_consumer.py (4 assertions to explicit refresh, recovery test replaced, 2 tests added). Pre-edit stale check showed only the earlier-seq name; the later mismatch was the replaced test name |
| 2 | Add the pure-read and health-refresh tests (Validation plan) | Completed | 20261029-114544 | 20261029-115335 | targeted: 22 passed, repeated with and without randomization |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261029-114544 | 20261029-115335 | ruff, format, mypy (475 files), lint-imports, bandit, module-size, reference-table clean; full suite (run once for seq 01-03 together, after seq 03) 10396 passed 8 skipped 15 deselected; diff-cover 100% |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261029-115335 | 20261029-115335 | Tests-only row N/A: tests-only row |

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
- **Requirement ID**: `REQ-003`
- **Source issue**: `issues/20261029-090247_eventbus002_slow-consumer-gauge-refresh.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261029-092153_eventbus002_slow-consumer-gauge-refresh.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261029-101659
- **Related target files**: `tests/eventbus/test_eventbus_slow_consumer.py`