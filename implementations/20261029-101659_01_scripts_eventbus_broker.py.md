## Goal

Make `EventBroker.slow_consumer_count()` a side-effect-free read and give the gauge write a separately named refresh, with one shared threshold comparison (`REQ-001`: pure read; `REQ-002`: gauge written only by an explicit refresh; `REQ-005`: `/health` meaning unchanged).

## Scope

Modify `scripts/eventbus/broker.py` only: the slow-consumer count and refresh methods and the `unsubscribe()` call. No change to `publish()`, `subscribe()`, `shutdown()`, thresholds, or other metrics. The health route call (seq 02), tests (seq 03), and docs (seq 04, 05) are separate documents.

## Assumptions

- Source claims re-verified this cycle: `_refresh_slow_consumer_gauge` at `scripts/eventbus/broker.py:129` counts subscribers with `queue.qsize() >= self._slow_consumer_threshold` (line 134) and sets the gauge (line 136); `slow_consumer_count` (line 139) returns it; `unsubscribe` calls it at line 83; `shutdown` sets the gauge to 0 at line 118; `subscribe()` (lines 60-73) does not refresh the gauge (corrects the Issue).
- `_refresh_slow_consumer_gauge` has no caller outside `broker.py` (`rg` over `scripts/`, `tests/`, `docs/` this cycle), so renaming it is safe; `slow_consumer_count` is called only by `scripts/eventbus/health_route.py:66` and `tests/eventbus/test_eventbus_slow_consumer.py`.
- Option B is the Plan's decision (UNK-01, non-blocking: owner may choose Option A instead); this document implements Option B only.
- No overlap with another Frozen Plan on this file (`tools/check_plan_target_overlaps.py`).

## Design decisions

- One private counter `_count_slow_consumers` (new) holds the only `>=` comparison; the read and the refresh both use it, so the gauge and `/health` cannot disagree.
- The public refresh is named `refresh_slow_consumer_gauge` (new) and returns the count, so `health_check()` needs a single call.

## Alternatives considered

- Refreshing the gauge on publish and drain (Option A): rejected here, it needs a change to the SSE drain loop and is justified only with a scrape endpoint (Plan UNK-01).

## Implementation

### Target file

`scripts/eventbus/broker.py`

### Procedure

1. Open `scripts/eventbus/broker.py` and locate `_refresh_slow_consumer_gauge` (line 129) and `slow_consumer_count` (line 139).
2. Replace those two methods with `_count_slow_consumers` (new), `refresh_slow_consumer_gauge` (new), and a pure `slow_consumer_count`, as shown in Method.
3. In `unsubscribe()` (line 83), change `self._refresh_slow_consumer_gauge()` to `self.refresh_slow_consumer_gauge()`.
4. Leave `shutdown()` (gauge set to 0) unchanged.

### Method

```python
    def _count_slow_consumers(self) -> int:
        """Count subscribers whose queue depth reaches the slow consumer threshold."""
        return sum(
            1
            for sub in list(self._subscribers)
            if sub.queue.qsize() >= self._slow_consumer_threshold
        )

    def refresh_slow_consumer_gauge(self) -> int:
        """Publish the current slow-consumer count to the gauge and return it."""
        count = self._count_slow_consumers()
        _slow_consumer_current.set(count)
        return count

    def slow_consumer_count(self) -> int:
        """Count slow consumers without touching the gauge."""
        return self._count_slow_consumers()
```

### Details

- The gauge is now written in exactly three places: `refresh_slow_consumer_gauge()`, `unsubscribe()` (through it; this also covers an overflow disconnect from `publish()`), and `shutdown()` (zero).
- `list(self._subscribers)` snapshot is kept, as in the moved code.

## Compatibility considerations

`/health` output is unchanged once seq 02 switches to the refresh. Any other caller that relied on `slow_consumer_count()` writing the gauge would stop refreshing it; the dependency check found none outside the slow-consumer tests, which seq 03 updates. Land seq 01 and seq 02 together so `/health` keeps refreshing the gauge.

## Security considerations

N/A: in-process counters only, no input, credentials, or I/O.

## Rollback considerations

Revert the commit; seq 02 and seq 03 depend on the new method, so revert them together.

## Validation plan

1. `uv run pytest tests/eventbus/test_eventbus_slow_consumer.py -v` after seq 03 is applied (before seq 03, the old gauge assertions fail by design).
2. `uv run pytest tests/eventbus`.
3. `uv run ruff check scripts/eventbus`; `uv run mypy --no-namespace-packages scripts/ tests/eventbus`; `uv run bandit -r scripts/eventbus -c pyproject.toml -ll`; `uv run python tools/check_module_size.py` (file is 5474 B).
4. `uv run python tools/generate_reference_table.py --check` (the reference lists `EventBroker` at class level only).
5. `uv run python tools/stale_detector.py implementations/20261029-101659_01_scripts_eventbus_broker.py.md`.

## Completion criteria

- `slow_consumer_count()` does not write the gauge; `refresh_slow_consumer_gauge()` does and returns the count; both use `_count_slow_consumers` (new).
- `unsubscribe()` calls the refresh; no reference to `_refresh_slow_consumer_gauge` remains.
- Tests (seq 03) pass; ruff, mypy, bandit, module-size, and reference-table checks are clean.

## Out of Scope

- The `/health` call site (seq 02), tests (seq 03), docs (seq 04, 05), publish or drain refresh (Option A), and any scrape endpoint.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Split the read from the refresh and update `unsubscribe()` (Implementation > Procedure/Method/Details) | Pending | — | — | |
| 2 | Tests are updated in seq 03 (Validation plan) | Pending | — | — | Old gauge assertions fail until seq 03 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A | — | — | Docs are seq 04 and 05 |

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
- **Requirement ID**: `REQ-001`, `REQ-002`, `REQ-005`
- **Source issue**: `issues/20261029-090247_eventbus002_slow-consumer-gauge-refresh.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261029-092153_eventbus002_slow-consumer-gauge-refresh.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261029-101659
- **Related target files**: `scripts/eventbus/broker.py`
