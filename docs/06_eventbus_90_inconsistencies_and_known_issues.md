# Event Bus: Known Inconsistencies and Issues

## Schema vs implementation differences

| Field | Schema definition | Runtime behavior | Status |
|---|---|---|---|
| `acked_at` | TEXT | Never set by any code path | Reserved/unused — see inline DDL in deploy/init_db.sh |
| `delivery_failure_count` | INTEGER DEFAULT 0 | Incremented on nack; triggers DLQ promotion at >= max_retry | By design |
| `/subscribe` | SSE endpoint | Replay from SQLite + live EventBroker push | Resolved — polling-based description removed |

## Active Items

### DLQ Promotion Semantics

| Item | Safe interpretation | Recommended action |
|---|---|---|
| DLQ promotion uses `delivery_failure_count >= max_retry`, not `retry_count` | Code and schema.sql both use `delivery_failure_count` for DLQ promotion | Resolved — all Event Bus docs now consistently use `delivery_failure_count >= max_retry` for DLQ promotion criteria |

### Ack-Only Offset Advancement

| Item | Safe interpretation | Recommended action |
|---|---|---|
| Offsets advance only via ack endpoint, never on disconnect | Disconnect does not write offset; consumer resumes from last acked seq | Resolved — updated HTTP API docs to clarify ack-only model; added reconnect semantics to DLQ/offsets doc |

### Missing Ack Endpoint Documentation

| Item | Safe interpretation | Recommended action |
|---|---|---|
| No HTTP API doc for POST /events/{event_id}/ack | Only POST /ack is documented | Resolved — added POST /events/{event_id}/ack to HTTP API docs with full contract (path params, query params, response, offset behavior); added to reference API endpoint table |

### DLQ Requeue Path Mismatch

| Item | Safe interpretation | Recommended action |
|---|---|---|
| DLQ requeue endpoint path `POST /dlq/{event_id}/requeue` not documented | Code implements this endpoint but docs only reference POST /ack for requeue | Resolved — added to HTTP API doc with edge cases (404 for unknown event, 409 Conflict for non-DLQ event); fixed requeue_event() to check dlq_at IS NOT NULL before allowing requeue; ack endpoint made idempotent with already_acked flag |

### Consumer ID Stability Ambiguity

| Item | Safe interpretation | Recommended action |
|---|---|---|
| Consumer IDs are client-supplied; `_make_consumer_id()` is dead code | No auto-generation in app.py; consumer_ids must be stable across restarts for offset resume | Resolved — removed misleading docs about auto-generated consumer IDs; clarified stability requirement in all Event Bus docs; added deprecation notice to _make_consumer_id() |

### Consumer ID Sanitization Mismatch

| Item | Safe interpretation | Recommended action |
|---|---|---|
| Documentation says `. → _` but code does `.. → _`; no `. → _` in code | Both are needed for complete path traversal prevention; docs and code must agree | Resolved — updated both implementation and documentation to replace all three: `.`, `/`, `..` with `_`; added empty consumer_id handling (→ "default"); added 8 sanitization tests covering /, .., ., empty, long IDs, and path traversal attempts |

### Host Config Ownership Mismatch

| Item | Safe interpretation | Recommended action |
|---|---|---|
| `host` field not loaded by EventBusConfig; controlled via uvicorn CLI --host | TOML config example with `host = "127.0.0.1"` is dead config | Resolved — removed from TOML example; documented host binding as deployment configuration; added startup log for effective bind address |

### SQLite Thread-Safety Confirmation

| Item | Safe interpretation | Recommended action |
|---|---|---|
| Shared connection with `asyncio.to_thread()` serialization | All DB operations in app.py acquire `_db_lock` inside `asyncio.to_thread()` callables | Document the DB access model in known-issues |

### DLQ Retry Count Semantics

| Item | Safe interpretation | Recommended action |
|---|---|---|
| `delivery_failure_count` incremented on nack, not DLQ requeue; `dlq_requeue_count` incremented on requeue | Two separate counters: delivery failures vs requeue attempts | Resolved — updated docs/06_eventbus_04_dlq_offsets_and_delivery_semantics.md, docs/06_eventbus_03_persistence_schema_and_replay.md, docs/06_eventbus_02_http_api_and_runtime.md to use `delivery_failure_count >= max_retry` for DLQ promotion criteria |

### DLQ Promotion Primary vs Safety Path

| Item | Safe interpretation | Recommended action |
|---|---|---|
| Background DLQ loop documented as primary promotion path; inline nack promotion undocumented | Inline on /nack is the primary path; background loop is a safety sweep for orphans | Resolved — updated docs/06_eventbus_04_dlq_offsets_and_delivery_semantics.md to document inline nack as primary promotion path, background loop as safety sweep with optimistic lock; added health endpoint fix (no "unhealthy" status, only "degraded") |

### Startup Safety Guard for Public Bind

| Item | Safe interpretation | Recommended action |
|---|---|---|
| Event Bus has no authentication; binding to 0.0.0.0 exposes API publicly | Need startup guard to detect public bind and warn/fail-fast | Resolved — added `host` and `allow_public_bind` fields to EventBusConfig; validated in `__post_init__`; fail-fast on public bind unless explicit override; app starts uvicorn programmatically using config values |

### Deprecated Config Fields

| Item | Safe interpretation | Recommended action |
|---|---|---|
| `poll_interval_ms` and `offset_checkpoint_interval` are no-op | Subscribe uses EventBroker push; offset checkpointing replaced with ack-only model | Resolved — added deprecation warnings when these fields are set to non-default values; removed from active TOML config example; documented in reference API docs |

### Missing Schema Columns in Documentation

| Item | Safe interpretation | Recommended action |
|---|---|---|
| `delivery_failure_count` and `dlq_requeue_count` columns not listed in schema section of persistence doc | Both columns exist in schema.sql with NOT NULL DEFAULT 0; delivery_failure_count triggers DLQ promotion, dlq_requeue_count tracks requeue attempts | Resolved — added both columns to CREATE TABLE and field semantics table in docs/06_eventbus_03_persistence_schema_and_replay.md |

### Missing Indexes in Documentation

| Item | Safe interpretation | Recommended action |
|---|---|---|
| `idx_events_dlq_at` and `idx_events_dlq_seq` not documented | Both indexes exist in schema.sql; idx_events_dlq_at for DLQ queries, idx_events_dlq_seq for DLQ ordering by seq | Resolved — added both indexes to Indexes section in docs/06_eventbus_03_persistence_schema_and_replay.md |

### Publish Envelope Constraints Not Documented

| Item | Safe interpretation | Recommended action |
|---|---|---|
| event_id UUID v4 pattern, topic/producer length constraints (1–255), payload must be object not string not documented in POST /publish docs | JSON Schema validation enforces these at runtime but API docs only show example without constraints | Resolved — added constraints table to POST /publish docs with UUID v4 pattern, minLength/maxLength for topic and producer, payload type constraint, published_at date-time format, schema_version optional with default |

### Missing /nack Endpoint Documentation

| Item | Safe interpretation | Recommended action |
|---|---|---|
| POST /nack endpoint only listed in reference API table, no HTTP API contract documented (request params, response shape) | Increments delivery_failure_count; promotes to DLQ if >= max_retry; returns 404 for unknown events | Resolved — added POST /nack section to HTTP API docs with query param, response 200/404, and dlq_promoted flag |

### DLQ List Response Missing dlq_requeue_count Field

| Item | Safe interpretation | Recommended action |
|---|---|---|
| GET /dlq response docs missing `dlq_requeue_count` field | Response includes seq, event_id, topic, producer, published_at, delivery_failure_count, dlq_requeue_count, dlq_at | Resolved — added dlq_requeue_count to DLQ list response documentation with description of both failure counters |

## Resolved Items

| Item | Resolution |
|---|---|
| `/health` HTTP status on degraded state (200 vs 503) | **Resolved** — now returns HTTP 503 for non-ok states (fail-closed) |
| Startup safety guard for public bind | **Resolved** — added `host` and `allow_public_bind` fields to EventBusConfig; validated in `__post_init__`; fail-fast on public bind unless explicit override |
| SQLite/JSONL dual read path | **Resolved** — SQLite-only reads; JSONL is write-only |
| Consumer ID collision possibility | **Resolved** — hash-based stable IDs with collision detection |
| `/subscribe` polling vs push documentation mismatch | **Resolved** — removed stale "polling-based internally (not push)" description; confirmed hybrid model (replay from SQLite + live EventBroker push) |
| Consumer ID collision possibility | **Re-evaluated** — no collision detection exists; last write wins for offset file; consumer_ids must be stable across restarts for offset resume |

## Deferred — Agent Integration

Agent runtime integration with Event Bus is intentionally not implemented at this time.

| Item | Status | Notes |
|---|---|---|
| Agent event publishing | Deferred | No Agent-side event producer is implemented. The Event Bus HTTP API supports publishing from any HTTP client; Agent-specific producers will be added in a future release. |
| Agent SSE subscription | Deferred | No Agent-side subscriber for consuming events via `/subscribe` SSE. Agent-side consumers will be added in a future release. |
| Agent event topics | Deferred | No Agent-defined topics exist today. Topic conventions for Agent lifecycle events will be defined when Agent integration is implemented. |

## Unconfirmed items (Needs Confirmation)

| Item | How to confirm |
|---|---|
| FastAPI thread pool worker usage | **Resolved** — all DB operations in app.py acquire `_db_lock` inside `asyncio.to_thread()` callables; SQLite WAL mode serializes concurrent writers at the SQLite level |
