## Goal

Make post-commit partial failures observable and recoverable without changing the documented publish success criterion (database commit) unintentionally.

## Scope

Add Prometheus Counters for JSONL append failures and broker notification failures; declare SQLite as canonical store; provide deterministic reconciliation mechanism; document failure behavior and recovery procedures.

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
`scripts/eventbus/publish_route.py`

### Procedure
1. Add Prometheus Counter for JSONL append failures after successful database commit.
2. Add Prometheus Counter for broker notification failures after successful database commit.
3. Increment both counters in their respective exception handlers.

### Method
- Import `Counter` from `prometheus_client` (already imported in `broker.py`).
- Define module-level counters following the naming convention `eventbus_<component>_failure_total`.
- In the JSONL append `except OSError` block (line 70-73), call `.inc()` on the new counter.
- In the broker notification `except Exception` block (line 87-88), call `.inc()` on the new counter.

### Details
```python
# At module level (after imports):
from prometheus_client import Counter

_jsonl_append_failure_counter = Counter(
    "eventbus_jsonl_append_failure_total",
    "Number of JSONL append failures after successful database commit",
)

_broker_notify_failure_counter = Counter(
    "eventbus_broker_notify_failure_total",
    "Number of broker notification failures after successful database commit",
)

# In the JSONL append block (around line 70):
except OSError as exc:
    _jsonl_append_failure_counter.inc()
    logger.warning(
        "eventbus: JSONL append failed (event still committed): %s", exc
    )

# In the broker notification block (around line 87):
except Exception:
    _broker_notify_failure_counter.inc()
    logger.exception("publish broker notify error seq=%d", seq)
```

## Compatibility considerations

- Prometheus metrics are additive-only; no breaking changes to existing behavior.
- Existing `_slow_consumer_total` in `broker.py` confirms Prometheus is acceptable for new metrics.
- The counter names follow the existing naming convention (`eventbus_` prefix).

## Security considerations

- No new secrets, credentials, or sensitive data exposure.
- Metrics do not include event payloads or PII — only failure counts.

## Rollback considerations

- Removing the counters reverts observability gains but does not affect functional correctness.
- If Prometheus scraping is not configured, the counters are harmless no-ops.

## Validation plan

| Target | Testing Strategy | Tool / Command | Expected Outcome |
|--------|------------------|----------------|------------------|
| publish_route.py | Unit: metric increment on JSONL failure; Unit: metric increment on broker failure | uv run pytest tests/eventbus/test_eventbus_publish.py -v | New metric tests pass; existing tests unchanged |

## Completion criteria

- [ ] `_jsonl_append_failure_counter` defined at module level and incremented in the `OSError` handler
- [ ] `_broker_notify_failure_counter` defined at module level and incremented in the `Exception` handler
- [ ] Both counters follow `eventbus_*_failure_total` naming convention
- [ ] Existing publish tests still pass

## Out of scope

- Creating the `docs/eventbus/` directory and documentation (handled by separate procedure)
- Creating the reconciliation script (handled by separate procedure)
- Adding Prometheus scrape configuration (infrastructure concern)

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add Prometheus Counter for JSONL append failures | Pending | — | — | REQ-002 |
| 2 | Add Prometheus Counter for broker notification failures | Pending | — | — | REQ-005 |

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
- **Requirement ID**: REQ-002, REQ-005
- **Source issue**: issues/20260914-102458_eventbus07_publish-durability-recovery-observability.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260914-174450_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260914-232906
- **Related target files**: scripts/eventbus/publish_route.py
