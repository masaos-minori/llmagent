# Event Bus: Known Inconsistencies and Issues

## Active Items

### Non-DLQ Events Can Be Requeued

| Item | Safe interpretation | Recommended action |
|---|---|---|
| `POST /dlq/{event_id}/requeue` returns 409 for non-DLQ events, not 404 | Event exists but is not in DLQ — idempotent requeue behavior | Resolved — DLQ list response includes dlq_requeue_count; GET /dlq documents the field |

### Ack Idempotency Behavior

| Item | Safe interpretation | Recommended action |
|---|---|---|
| Repeated ack returns 200 with `already_acked: true`, not 404 | First ack returns 200 with `acked: true`; repeated ack returns 200 with `already_acked: true` for idempotency | Resolved — both `/events/{event_id}/ack` and legacy `/ack` endpoints updated; concurrent ack test validates behavior |

### Consumer ID Sanitization Docs Mismatch

| Item | Safe interpretation | Recommended action |
|---|---|---|
| Documentation says `. → _` but code does `.. → _`; no `. → _` in code | Both are needed for complete path traversal prevention; docs and code must agree | Resolved — updated both implementation and documentation to replace all three: `.`, `/`, `..` with `_`; added empty consumer_id handling (→ "default"); added 8 sanitization tests covering /, .., ., empty, long IDs, and path traversal attempts |

### Deploy/init_db.sh Schema Mismatch

| Item | Safe interpretation | Recommended action |
|---|---|---|
| `deploy/init_db.sh` Event Bus DDL missing `delivery_failure_count`, `dlq_requeue_count` columns and DLQ indexes | DDL must match schema.sql for reproducible initialization | Resolved — consolidated to single create_schema.py call; removed redundant workflow_schema.py call; added session.sqlite table verification |

## Docs-Only Items

These items are documentation improvements that do not require implementation changes.

### /health Degraded State Returns HTTP 503

| Item | Safe interpretation |
|---|---|
| `/health` returns HTTP 503 for `degraded`/`unhealthy` states, HTTP 200 for `ok` | Monitoring tools MUST use HTTP status code, not JSON body, for alerting |

### /replay?format=json Returns Paginated Object

| Item | Safe interpretation |
|---|---|
| `GET /replay?format=json` returns `{total, limit, offset, items}` not a raw array | Clients can paginate through replay results using limit/offset parameters |

### Offset Advancement Is Ack-Only

| Item | Safe interpretation |
|---|---|
| Offsets advance only via ack endpoint, never on disconnect or during streaming | Consumer must call `POST /events/{event_id}/ack` to advance offset; reconnect resumes from last acked seq |

### DLQ Promotion Is Inline-on-nack Plus Safety Sweep

| Item | Safe interpretation |
|---|---|
| Primary DLQ promotion is inline on `/nack` when `delivery_failure_count >= max_retry`; background loop is a safety sweep for orphans | The background DLQ loop catches events that reached the threshold but were not promoted inline; non-zero sweep results may indicate an inline promotion issue |

## Resolved Items

| Item | Resolution |
|---|---|
| Public bind guard exists | **Resolved** — added `host` and `allow_public_bind` fields to EventBusConfig; validated in `__post_init__`; fail-fast on public bind unless explicit override |
| `delivery_failure_count` exists in schema | **Resolved** — added `delivery_failure_count` and `dlq_requeue_count` columns to CREATE TABLE and field semantics table in docs/06_eventbus_03_persistence_schema_and_replay.md |
| JSONL is supplementary, SQLite is authoritative | **Resolved** — SQLite-only reads; JSONL is write-only |
| Push-based subscribe via EventBroker exists | **Resolved** — removed stale "polling-based internally (not push)" description; confirmed hybrid model (replay from SQLite + live EventBroker push) |

## Deferred Items

Agent runtime integration with Event Bus is intentionally not implemented at this time.

| Item | Status | Notes |
|---|---|---|
| Agent event publishing | Deferred | No Agent-side event producer is implemented. The Event Bus HTTP API supports publishing from any HTTP client; Agent-specific producers will be added in a future release. |
| Agent SSE subscription | Deferred | No Agent-side subscriber for consuming events via `/subscribe` SSE. Agent-side consumers will be added in a future release. |
| Agent event topics | Deferred | No Agent-defined topics exist today. Topic conventions for Agent lifecycle events will be defined when Agent integration is implemented. |

## Schema vs Implementation Differences

| Field | Schema definition | Runtime behavior | Status |
|---|---|---|---|
| `acked_at` | TEXT | Never set by any code path | Reserved/unused — see inline DDL in deploy/init_db.sh |
| `retry_count` | INTEGER NOT NULL DEFAULT 0 | Deprecated; use delivery_failure_count | Deprecated — not used for DLQ promotion. DLQ promotion uses `delivery_failure_count >= max_retry`. This field is incremented on DLQ requeue only (see `dlq_requeue_count`). |
