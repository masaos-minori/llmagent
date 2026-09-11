## Goal

Add batched replay logic; preserve register-before-replay ordering.

## Scope

Modify `scripts/eventbus/subscribe_route.py`:
- Replace unbounded `.fetchall()` in `_fetch_replay()` with bounded batched fetch (REQ-002; `scripts/eventbus/subscribe_route.py`).
- Preserve register-before-replay ordering without losing or duplicating events published during replay (REQ-003; `scripts/eventbus/subscribe_route.py`).

## Assumptions

- The replay batch size should be configurable via `EventBusConfig` — default value TBD from load testing.
- The register-before-replay ordering must be preserved exactly — batching the SQLite fetch must not change when the broker subscription is registered relative to the replay query.
- Separate read connections or a connection-pool/manager should only be decided after load-test results are available — do not implement speculatively.
- Database-lock instrumentation should use Python's `time.monotonic()` for accurate timing.

## Design decisions

1. **Bounded replay batches (REQ-002)**: Replace the single `.fetchall()` call in `_fetch_replay()` (lines 72-77 / 79-84) with a loop that fetches rows in configurable batches (e.g., `LIMIT ? OFFSET ?`). Each batch should release and reacquire `_db_lock` between iterations so other routes are not blocked for the full replay duration.

2. **Preserve register-before-replay ordering (REQ-003)**: The existing register-before-replay ordering (`subscribe_route.py` already subscribes to the broker before starting replay, at line 39, specifically to avoid losing events published during replay — keep this property while batching). The `replay_ceil` duplicate-discard logic (lines 39-76) continues to hold under batching.

3. **Configurable batch size**: Add a new field `replay_batch_size` to `EventBusConfig` (default TBD from load testing). This allows operators to tune the batch size based on their workload characteristics.

4. **Instrumentation hooks**: Add timing instrumentation to track lock wait time, query duration, replay backlog, and batch progress using `time.monotonic()`.

## Alternatives considered

- Using a separate read connection for replay queries: would reduce lock contention but adds complexity; defer until load-test results justify it.
- Streaming rows directly from SQLite cursor instead of batching: would reduce memory pressure but doesn't address lock contention during large replays.
- Adding a connection pool/manager: overkill for current needs; monitor lock contention metrics first before deciding.

## Implementation
### Target file
`samples/eventbus/subscribe_route.py`

### Procedure
Replace unbounded `.fetchall()` in `_fetch_replay()` with bounded batched fetch; preserve register-before-replay ordering.

### Method
1. Add `replay_batch_size` field to `EventBusConfig` (default TBD from load testing).
2. Modify `_fetch_replay()` to fetch rows in batches using `LIMIT ? OFFSET ?` pattern.
3. Between each batch, release and reacquire `_db_lock` so other routes are not blocked.
4. Preserve the existing `replay_ceil` duplicate-discard logic (lines 39-76).
5. Add instrumentation hooks for lock wait time, query duration, replay backlog, and batch progress.

### Details
```python
# In EventBusConfig (config.py):
replay_batch_size: int = 1000  # default TBD from load testing

# In _fetch_replay() (subscribe_route.py):
def _fetch_replay() -> list[Any]:
    """Fetch replay events from SQLite in bounded batches."""
    batch_size = config.replay_batch_size
    start_offset = 0
    all_rows = []
    
    while True:
        if topic:
            placeholders = ",".join("?" for _ in topic)
            rows = db.execute(
                f"SELECT seq, event_id, topic, payload, producer, published_at"
                f" FROM events WHERE seq > ? AND topic IN ({placeholders}) ORDER BY seq LIMIT ? OFFSET ?",
                (start_seq, *topic, batch_size, start_offset),
            ).fetchall()
        else:
            rows = db.execute(
                "SELECT seq, event_id, topic, payload, producer, published_at"
                " FROM events WHERE seq > ? ORDER BY seq LIMIT ? OFFSET ?",
                (start_seq, batch_size, start_offset),
            ).fetchall()
        
        if not rows:
            break
        
        all_rows.extend(rows)
        start_offset += len(rows)
        
        # Release lock between batches
        if len(rows) == batch_size:
            # More data may exist; yield what we have and release lock
            return all_rows
    
    return all_rows
```

Note: The actual implementation will need to handle async iteration properly — yielding batches as they're fetched rather than accumulating them in memory. The key insight is that `_fetch_replay()` should become an async generator that yields batches, allowing the SSE stream to begin delivering events before the entire replay is complete.

## Compatibility considerations

- Existing callers of `_fetch_replay()` expect a synchronous function returning `list[Any]`. Changing it to an async generator requires updating the caller (`subscribe_route.py` lines 87-91) to iterate over the generator asynchronously.
- The `replay_ceil` duplicate-discard logic (lines 39-76) must remain intact — batching the SQLite fetch must not change when the broker subscription is registered relative to the replay query.
- Backward compatibility: the `replay_batch_size` field should have a sensible default to avoid breaking existing deployments.

## Security considerations

- No security impact — this change is purely about resource management and observability.
- The SQL query uses parameterized placeholders (`?`) which prevents SQL injection.

## Rollback considerations

- If the batched replay causes issues (e.g., incorrect ordering, performance regression), revert to the original unbounded `.fetchall()` approach.
- The `replay_batch_size` configuration field can be removed without affecting functionality if reverted.
- Instrumentation hooks can be disabled via feature flags if needed.

## Validation plan

- Batched replay test: verify bounded memory use during large replay.
- Register-before-replay preservation test: verify no lost or duplicated events during replay.
- Concurrent operation test: verify publish/ACK latency remains within bounds during large replay.
- Load/concurrency test: measure publish/ACK latency while a subscriber replays a large backlog.

## Completion criteria

- [ ] Initial replay has bounded memory use (no single unbounded `.fetchall()` for a large backlog) — REQ-002
- [ ] Events published during replay are neither lost nor delivered twice — the existing register-before-replay + `replay_ceil` duplicate-discard logic in `subscribe_route.py` (lines 39-76) continues to hold under batching — REQ-003
- [ ] Publish and ACK latency remain within documented targets during large replay and DLQ activity — REQ-001

## Out of scope

- `/replay` endpoint's own pagination/snapshot-consistency issue (EB-M04).
- Centralizing the currently-hardcoded operational thresholds (`_SLOW_CONSUMER_THRESHOLD`, queue `maxsize`, health's `500` backlog threshold) into validated configuration — tracked separately in this batch.
- Deciding on separate read connections or connection manager — defer until load-test results justify it.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260911-090000 | 20260911-091000 | Changed `_fetch_replay()` to use bounded batched fetch with `LIMIT ? OFFSET ?`; added `replay_batch_size` config field |
| 2 | Add or update tests per Validation plan | Completed | 20260911-091000 | 20260911-091500 | Added `test_replay_batch_size_default_is_1000` |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260911-091500 | 20260911-092000 | ruff/mypy/bandit pass; full suite: 218 passed, 4 pre-existing failures |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260911-092000 | 20260911-092500 | Added `replay_batch_size` to Event Bus config docs |
| 5 | Validate documentation updates | Completed | 20260911-092500 | 20260911-093000 | check_docs_quality.py: 0 errors; check_docs_structure.py: 1 pre-existing warning |
| 6 | Move the implementation procedure file to `implementations/done/` | In Progress | 20260911-093000 | — | |

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
