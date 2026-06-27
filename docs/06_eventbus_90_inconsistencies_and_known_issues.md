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
| DLQ promotion uses `delivery_failure_count >= max_retry`, not `retry_count` | Code and schema.sql both use `delivery_failure_count` for DLQ promotion | Update docs referencing `retry_count` to use `delivery_failure_count` |

### Ack-Only Offset Advancement

| Item | Safe interpretation | Recommended action |
|---|---|---|
| Offsets advance only via ack endpoint, never on disconnect | Disconnect does not write offset; consumer resumes from last acked seq | Document this in consumer guide |

### Missing Ack Endpoint Documentation

| Item | Safe interpretation | Recommended action |
|---|---|---|
| No HTTP API doc for POST /events/{event_id}/ack | Only POST /ack is documented | Add POST /events/{event_id}/ack to reference API doc |

### DLQ Requeue Path Mismatch

| Item | Safe interpretation | Recommended action |
|---|---|---|
| DLQ requeue endpoint path `POST /dlq/{event_id}/requeue` not documented | Code implements this endpoint but docs only reference POST /ack for requeue | Add to HTTP API doc with edge cases (404 for unknown event, 404 for non-DLQ event) |

### Consumer ID Stability Ambiguity

| Item | Safe interpretation | Recommended action |
|---|---|---|
| Consumer IDs are client-supplied; `_make_consumer_id()` is dead code | No auto-generation in app.py; consumer_ids must be stable across restarts for offset resume | Resolved — removed misleading docs about auto-generated consumer IDs; clarified stability requirement in all Event Bus docs; added deprecation notice to _make_consumer_id() |

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

### Startup Safety Guard for Public Bind

| Item | Safe interpretation | Recommended action |
|---|---|---|
| Event Bus has no authentication; binding to 0.0.0.0 exposes API publicly | Need startup guard to detect public bind and warn/fail-fast | Resolved — added `host` and `allow_public_bind` fields to EventBusConfig; validated in `__post_init__`; fail-fast on public bind unless explicit override; app starts uvicorn programmatically using config values |

### Deprecated Config Fields

| Item | Safe interpretation | Recommended action |
|---|---|---|
| `poll_interval_ms` and `offset_checkpoint_interval` are no-op | Subscribe uses EventBroker push; offset checkpointing replaced with ack-only model | Resolved — added deprecation warnings when these fields are set to non-default values; removed from active TOML config example; documented in reference API docs |

## Resolved Items

| Item | Resolution |
|---|---|
| `/health` HTTP status on degraded state (200 vs 503) | **Resolved** — now returns HTTP 503 for non-ok states (fail-closed) |
| Startup safety guard for public bind | **Resolved** — added `host` and `allow_public_bind` fields to EventBusConfig; validated in `__post_init__`; fail-fast on public bind unless explicit override |
| SQLite/JSONL dual read path | **Resolved** — SQLite-only reads; JSONL is write-only |
| Consumer ID collision possibility | **Resolved** — hash-based stable IDs with collision detection |
| `/subscribe` polling vs push documentation mismatch | **Resolved** — removed stale "polling-based internally (not push)" description; confirmed hybrid model (replay from SQLite + live EventBroker push) |
| Consumer ID collision possibility | **Re-evaluated** — no collision detection exists; last write wins for offset file; consumer_ids must be stable across restarts for offset resume |

## Unconfirmed items (Needs Confirmation)

| Item | How to confirm |
|---|---|
| FastAPI thread pool worker usage | **Resolved** — all DB operations in app.py acquire `_db_lock` inside `asyncio.to_thread()` callables; SQLite WAL mode serializes concurrent writers at the SQLite level |
