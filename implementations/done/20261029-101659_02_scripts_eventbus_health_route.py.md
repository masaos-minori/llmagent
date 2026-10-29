## Goal

Make `health_check()` call the explicit gauge refresh instead of the read, so the documented trigger (a `/health` read) is the only reason the gauge changes there (`REQ-002`: refresh through the explicit method; `REQ-005`: response fields and degraded reason unchanged).

## Scope

Modify `scripts/eventbus/health_route.py` only: one call in `health_check()`. No change to response fields, thresholds, or degraded-reason names.

## Assumptions

- Source claims re-verified this cycle: `health_check` at `scripts/eventbus/health_route.py:34` assigns `slow_consumers = broker.slow_consumer_count()` at line 66 inside `if broker is not None:` and uses `slow_consumers > 0` for `slow_consumers_detected` (lines 78-79); the response carries `"slow_consumers": slow_consumers` (line 112).
- Name created by an earlier row: `refresh_slow_consumer_gauge` is created by seq 01 (`scripts/eventbus/broker.py`), which `code-implementation` runs first.
- No test replaces the broker with a stub lacking the new method (`rg slow_consumer_count tests/` finds only `test_eventbus_slow_consumer.py`).
- No overlap with another Frozen Plan on this file.

## Design decisions

- Keep the `slow_consumers` value and degraded logic identical; only the method called changes (refresh returns the same count the read did).
- Add a one-line comment naming the refresh as the `/health` trigger so the contract is visible at the call site.

## Alternatives considered

N/A: single-call substitution; alternatives are covered by the Plan's Option A/B decision.

## Implementation

### Target file

`scripts/eventbus/health_route.py`

### Procedure

1. Open `scripts/eventbus/health_route.py` and locate line 66.
2. Replace `slow_consumers = broker.slow_consumer_count()` with `slow_consumers = broker.refresh_slow_consumer_gauge()`.
3. Add the comment line above it.

### Method

```python
        # A health read is a documented refresh trigger for the slow-consumer gauge.
        slow_consumers = broker.refresh_slow_consumer_gauge()
```

### Details

- `health_check` is rated C (15) by radon before the change; the substitution does not add a branch.
- The value `slow_consumers` still feeds both the response body and the `slow_consumers_detected` reason.

## Compatibility considerations

Response fields, the `slow_consumers_detected` reason, and the 503 behavior are unchanged; the gauge still refreshes on every health read, as before.

## Security considerations

N/A: no input handling or credentials involved.

## Rollback considerations

N/A: revert the commit (single-line change); if seq 01 is reverted too, this row must be reverted with it.

## Validation plan

1. `uv run pytest tests/eventbus/test_eventbus_slow_consumer.py tests/eventbus/test_eventbus_health.py -v`.
2. `uv run ruff check scripts/eventbus`; `uv run mypy --no-namespace-packages scripts/ tests/eventbus`.
3. `uv run python tools/stale_detector.py implementations/20261029-101659_02_scripts_eventbus_health_route.py.md`.

## Completion criteria

- `health_check()` calls `broker.refresh_slow_consumer_gauge()`; no call to `slow_consumer_count()` remains in `health_route.py`.
- Health and slow-consumer tests pass; ruff and mypy are clean.

## Out of Scope

- Broker changes (seq 01), tests (seq 03), docs (seq 04, 05), and any new `/health` field.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Switch `health_check()` to the explicit refresh (Implementation > Procedure/Method/Details) | Completed | 20261029-114512 | 20261029-115335 | Needs seq 01 first Changed: scripts/eventbus/health_route.py. stale check (before edit): clean after seq 01 |
| 2 | Run the health and slow-consumer tests (Validation plan) | Completed | 20261029-114512 | 20261029-115335 | targeted: 22 passed (shared run with seq 01 and 03) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261029-114512 | 20261029-115335 | ruff, format, mypy (475 files), lint-imports, bandit, module-size, reference-table clean; full suite (run once for seq 01-03 together, after seq 03) 10396 passed 8 skipped 15 deselected; diff-cover 100% |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261029-115335 | 20261029-115335 | Docs are seq 04 and 05 N/A: docs are handled by seq 04 and 05 |

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
- **Requirement ID**: `REQ-002`, `REQ-005`
- **Source issue**: `issues/20261029-090247_eventbus002_slow-consumer-gauge-refresh.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261029-092153_eventbus002_slow-consumer-gauge-refresh.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261029-101659
- **Related target files**: `scripts/eventbus/health_route.py`