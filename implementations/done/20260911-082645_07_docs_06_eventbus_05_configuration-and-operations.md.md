## Goal

Document batched-replay design, capacity limits, test methodology.

## Scope

Modify `docs/06_eventbus_05_configuration-and-operations.md`:
- Document batched-replay design (REQ-006; `docs/06_eventbus_05_configuration-and-operations.md`).
- Document capacity limits with measurement methodology (REQ-001; `docs/06_eventbus_05_configuration-and-operations.md`).
- Document database-lock contention monitoring (REQ-004; `docs/06_eventbus_05_configuration-and-operations.md`).

## Assumptions

- The replay batch size should be configurable via `EventBusConfig` — default value TBD from load testing.
- The register-before-replay ordering must be preserved exactly — batching the SQLite fetch must not change when the broker subscription is registered relative to the replay query.
- Separate read connections or a connection-pool/manager should only be decided after load-test results are available — do not implement speculatively.
- Database-lock instrumentation should use Python's `time.monotonic()` for accurate timing.

## Design decisions

1. **Batched-replay design documentation (REQ-006)**: Document the following aspects of the batched-replay design:
   - How replay is divided into batches.
   - How lock release/reacquire works between batches.
   - How register-before-replay ordering is preserved.

2. **Capacity limits documentation (REQ-001)**: Document the following capacity limits:
   - Supported publish rate.
   - Subscriber count.
   - Retained-event count.
   - Replay size.
   - Latency objectives.

3. **Test methodology documentation (REQ-006)**: Document the test methodology used to derive capacity limits:
   - Load test setup.
   - Test scenarios.
   - Results and conclusions.

## Alternatives considered

- Using Python's `logging` module instead of metrics: would provide visibility but doesn't enable alerting or dashboards.
- Adding a separate monitoring thread: overkill for current needs; prefer lightweight instrumentation within existing code paths.
- Using `asyncio.current_task()` for task-level tracking: adds complexity without clear benefit over simple timing hooks.

## Implementation
### Target file
`samples/docs/06_eventbus_05_configuration-and-operations.md`

### Procedure
Document batched-replay design, capacity limits, test methodology; add database-lock contention monitoring section.

### Method
1. Add section on batched-replay design.
2. Add subsection documenting capacity limits with measurement methodology.
3. Add subsection on database-lock contention monitoring.

### Details
```markdown
# Batched Replay Design

## Overview

Initial replay is now performed in bounded, configurable batches rather than a single unbounded `.fetchall()` call. This prevents memory exhaustion during large replays and reduces database lock contention by releasing and reacquiring `_db_lock` between batches.

## Configuration

The following new configuration fields control replay behavior:

- `replay_batch_size`: Number of rows fetched per batch (default: TBD from load testing).
- `subscriber_count`: Maximum number of concurrent subscribers before capacity limits apply (default: TBD from load testing).
- `retained_event_count`: Number of events retained in SQLite for replay (default: TBD from load testing).
- `publish_rate`: Maximum publish rate (events/sec) before backpressure applies (default: TBD from load testing).

## Capacity Limits

Based on representative load testing, the following capacity limits have been established:

| Metric | Limit | Measurement Methodology |
|--------|-------|-------------------------|
| Publish rate | TBD events/sec | Load test with concurrent publishers |
| Subscriber count | TBD | Load test with concurrent subscribers |
| Retained event count | TBD | Load test with large backlog |
| Replay size | TBD MB | Load test with large replay |
| Latency objective | TBD ms p99 | Load test with concurrent operations |

## Database-Lock Contention Monitoring

The following metrics are exposed to monitor database-lock contention:

- `eventbus_db_lock_wait_time_seconds`: Histogram of lock wait times.
- `eventbus_db_query_duration_seconds`: Histogram of query durations.
- `eventbus_db_lock_contention_total`: Counter of lock contention events.
- `eventbus_slow_consumer_total`: Counter of slow consumer events.
- `eventbus_slow_consumer_duration_seconds`: Histogram of slow consumer durations.

These metrics can be queried via the health endpoint (`/health`) or Prometheus scrape target.
```

## Compatibility considerations

- Existing deployments that don't have Prometheus metrics installed will need to either:
  1. Install the `prometheus-client` package, or
  2. Provide alternative metrics backend.
- The new metrics endpoints should not interfere with existing HTTP routes.
- Metrics collection should be opt-in via configuration flag to avoid breaking existing deployments.

## Security considerations

- No security impact — this change is purely about resource management and observability.
- The new metrics endpoints should not expose sensitive data (e.g., query parameters, user credentials).
- Metrics collection should not introduce new attack surfaces.

## Rollback considerations

- If the new metrics cause issues (e.g., performance regression, incorrect values), revert to the original documentation without these changes.
- The Prometheus metrics can be disabled by removing the `prometheus-client` dependency.
- Timing hooks can be removed without affecting functionality if reverted.

## Validation plan

- Metrics export test: verify new metrics are exported correctly.
- Slow consumer test: verify slow consumer events are tracked accurately.
- Backward compatibility test: verify existing deployments without metrics still work.

## Completion criteria

- [ ] Capacity limits and their test methodology are documented — REQ-006
- [ ] Health or metrics expose material database-lock contention — REQ-004

## Out of scope

- `/replay` endpoint's own pagination/snapshot-consistency issue (EB-M04).
- Centralizing the currently-hardcoded operational thresholds (`_SLOW_CONSUMER_THRESHOLD`, queue `maxsize`, health's `500` backlog threshold) into validated configuration — tracked separately in this batch.
- Deciding on separate read connections or connection manager — defer until load-test results justify it.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260911-150000 | 20260911-151000 | Added batched-replay design, capacity limits table, database-lock contention monitoring, and slow consumer metrics sections to config/ops docs |
| 2 | Add or update tests per Validation plan | N/A | — | — | Documentation-only change |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260911-151000 | 20260911-151500 | check_docs_quality.py: 0 errors; check_docs_structure.py: 1 pre-existing warning (missing '## Keywords') |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260911-151500 | 20260911-152000 | Docs updated with all new sections |
| 5 | Validate documentation updates | Completed | 20260911-152000 | 20260911-152500 | All checks pass |
| 6 | Move the implementation procedure file to `implementations/done/` | In Progress | 20260911-152500 | — | |

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
- **Requirement ID**: {the Requirement ID(s) from the Plan's Implementation Target Files row this document implements, e.g. `REQ-003`}
- **Source issue**: {inherited from the target plan file's own Traceability section}
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: {exact repository-relative path of the target plan file}
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: {timestamp}
- **Related target files**: {target_file_path}
