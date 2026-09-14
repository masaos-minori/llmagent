## Goal

Make post-commit partial failures observable and recoverable without changing the documented publish success criterion (database commit) unintentionally.

## Scope

Add Prometheus Counter for broker publish failures within the EventBroker's `publish()` method.

## Assumptions

- A: The database commit in `run_with_db_lock(_insert)` is the publish success criterion — confirmed by `publish_route.py:54` where `seq, inserted, status = await run_with_db_lock(_insert)` returns before any post-commit work
- B: JSONL append uses `os.fsync()` for durability — confirmed by `publish_route.py:69`
- C: Broker notification uses `broker.publish(event_dict)` which fans out to subscriber queues — confirmed by `broker.py:79-100`
- D: The `prometheus_client.Counter` class is already used in `broker.py` for `_slow_consumer_total` — confirmed by `broker.py:10`
- E: The `docs/eventbus/` directory does not exist yet — confirmed by filesystem check
- F: The `storage_dir` configuration key defines the JSONL file location — confirmed by `publish_route.py:64`

## Design decisions

- Declare SQLite as canonical event store. Rationale: the database commit is the publish success criterion; JSONL is derived data that can be rebuilt from SQLite; broker notification is real-time delivery, not durable record.
- Use Prometheus Counters consistent with existing `_slow_consumer_total` in `broker.py`.
- Provide a standalone reconcile script (`scripts/eventbus/reconcile.py`) for rebuilding JSONL from SQLite.

## Alternatives considered

- Declaring JSONL as canonical: would require idempotent writes and conflict resolution on every insert instead of simple append; adds operational complexity without clear benefit since SQLite already serves as the authoritative store.
- Adding retry logic for JSONL/broker failures: retries add latency and complexity; the canonical-store declaration makes retries unnecessary since SQLite remains the source of truth.
- Embedding reconcile logic into an admin endpoint: a CLI script is simpler, more auditable, and avoids exposing internal state over HTTP.

## Implementation
### Target file
`scripts/eventbus/broker.py`

### Procedure
1. Add Prometheus Counter for broker publish failures within the `EventBroker.publish()` method.
2. Increment the counter when individual subscriber queue puts fail with exceptions other than `QueueFull`.

### Method
- The `prometheus_client.Counter` import already exists at line 10.
- Define a module-level counter following the naming convention `eventbus_<component>_failure_total`.
- In the `publish()` method, wrap the per-subscriber `put_nowait` in a try-except that catches non-`QueueFull` exceptions and increments the counter.

### Details
```python
# At module level (after _slow_consumer_total definition, around line 22):
_broker_publish_failure_counter = Counter(
    "eventbus_broker_publish_failure_total",
    "Number of broker publish failures to individual subscribers",
)

# In the publish() method (around line 88-90), replace the current inner loop body:
for sub in list(self._subscribers):
    if sub.topics and event_topic not in sub.topics:
        continue
    try:
        sub.queue.put_nowait(event)
        delivered += 1
    except asyncio.QueueFull:
        # ... existing overflow handling (lines 91-99) ...
        self._overflow_disconnect_count += 1
    except Exception:
        _broker_publish_failure_counter.inc()
        raise
```

Note: The existing `QueueFull` handler already disconnects the subscriber. The new exception handler covers other unexpected errors during `put_nowait` (e.g., `BrokenPipeError`, `RuntimeError`).

## Compatibility considerations

- Prometheus metrics are additive-only; no breaking changes to existing behavior.
- Existing `_slow_consumer_total` in `broker.py` confirms Prometheus is acceptable for new metrics.
- The counter names follow the existing naming convention (`eventbus_` prefix).

## Security considerations

- No new secrets, credentials, or sensitive data exposure.
- Metrics do not include event payloads or PII — only failure counts.

## Rollback considerations

- Removing the counter reverts observability gains but does not affect functional correctness.
- If Prometheus scraping is not configured, the counter is harmless no-op.

## Validation plan

| Target | Testing Strategy | Tool / Command | Expected Outcome |
|--------|------------------|----------------|------------------|
| broker.py | Unit: metric increment on publish failure | uv run pytest tests/eventbus/test_eventbus_publish.py -v | Broker failure metric test passes |

## Completion criteria

- [ ] `_broker_publish_failure_counter` defined at module level and incremented in the `except Exception` block within `publish()`
- [ ] Counter follows `eventbus_*_failure_total` naming convention
- [ ] Existing broker tests still pass

## Out of scope

- Creating the `docs/eventbus/` directory and documentation (handled by separate procedure)
- Creating the reconciliation script (handled by separate procedure)
- Adding Prometheus scrape configuration (infrastructure concern)

## execution_status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add Prometheus Counter for broker publish failures | Pending | — | — | REQ-005 |

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
- **Requirement ID**: REQ-005
- **Source issue**: issues/20260914-102458_eventbus07_publish-durability-recovery-observability.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260914-174450_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260914-232906
- **Related target files**: scripts/eventbus/broker.py
