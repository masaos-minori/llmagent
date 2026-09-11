---
title: "Event Bus: Reference API"
area: eventbus
tags:
  - event-bus
  - api-reference
  - core-modules
  - app-py
  - config-py
  - db-py
  - dlq-py
  - route-handlers
  - publish-route
  - ack-route
  - dlq-route
  - replay-route
  - subscribe-route
  - health-route
  - broker
  - offsets
  - eventbroker
  - subscriber
related:
  - 06_eventbus_00_document-guide.md
  - 06_eventbus_01_system-overview.md
  - 06_eventbus_02_operations.md
---

# Event Bus: Reference API

Detailed API specifications (module responsibilities, route handlers, and internal
classes) for verification purposes. Refer to `06_eventbus_02_operations.md` for the
endpoint contracts (request/response shapes, status codes) — this document covers the
implementing modules, not the HTTP-level behavior.

## Core Modules

### scripts/eventbus/app.py

Application state and CLI entry point. See code for details.

### scripts/eventbus/config.py

`EventBusConfig` class and configuration loading functions. See code for details.

**New fields (REQ-001):** `sse_heartbeat_interval` (float, default 30.0) — interval in seconds between SSE comment heartbeats during live delivery phase. Optional TOML key; absent from TOML uses default. Validated as float type when present.

**New operational thresholds (REQ-001, REQ-002):** `slow_consumer_threshold` (int, default 100), `queue_backlog_threshold` (int, default 1000), `dlq_requeue_threshold` (int, default 500). All optional TOML keys; defaults used when absent. Relationship validation enforced: `slow_consumer_threshold < queue_backlog_threshold`.

### scripts/eventbus/db.py

DB connection and schema initialization. See code for details.

### scripts/eventbus/dlq.py

DLQ operation functions. See code for details.

### scripts/eventbus/route_helpers.py

Common route helpers. See code for details.

---

## Route Handlers

### scripts/eventbus/publish_route.py

`publish(request)`: `POST /publish`. JSON Schema validation → DB insertion → JSONL append → Broker notification. JSONL append failure does not surface as an HTTP error (Warning log + 200).

### scripts/eventbus/ack_route.py

`ack_event(request, event_id, consumer_id)`: `POST /events/{event_id}/ack`. `nack(request, event_id)`: `POST /nack`. Increments failure count; promotes to DLQ if `>= max_retry`.

### scripts/eventbus/dlq_route.py

`dlq_list(request, limit=100, offset=0)`: `GET /dlq`. `dlq_requeue(request, event_id)`: `POST /dlq/{event_id}/requeue`. If `failure_count >= max_retry`, it may be re-moved to the DLQ. See `06_eventbus_04_dlq_offsets_and_delivery_semantics.md` for DLQ semantics.

### scripts/eventbus/replay_route.py

`replay(request, since_seq=0, fmt=sse, limit=100, offset=0)`: `GET /replay`. SSE stream or paginated JSON. See `06_eventbus_04_dlq_offsets_and_delivery_semantics.md` for replay semantics.

**Format parameter:** Accepts only `sse` or `json`. Unsupported values return HTTP 422. Default is `sse`.

**Snapshot consistency:** When `fmt=json`, both `total` and `items` represent one internally consistent database snapshot — they are fetched under a single `run_with_db_lock()` acquisition, preventing interleaving with concurrent `/publish` calls.

**Paging behavior:** When `offset` exceeds available results, the response returns an empty `items` array with `total` reflecting the actual count of matching events.

**SSE event IDs:** Each SSE frame includes `id:<seq>` field where `seq` is the event's sequence number, enabling `EventSource`-based clients to auto-reconnect after interruption.

### scripts/eventbus/subscribe_route.py

`subscribe(request, topic=[], since_seq=0, consumer_id="")`: `GET /subscribe`. SSE streaming + replay+push. See `06_eventbus_04_dlq_offsets_and_delivery_semantics.md` for delivery semantics, offset semantics, and backpressure behavior.

**SSE-standard features (REQ-001 through REQ-005):**
- Heartbeat: During live delivery phase, emits `: heartbeat\n\n` comments at `cfg.sse_heartbeat_interval` intervals to keep idle connections alive through proxies/LBs.
- Event IDs: Each event frame includes `id:<seq>` field where `seq` is the monotonic sequence number, enabling `EventSource`-based clients to auto-reconnect.
- Last-Event-ID: Client can send `Last-Event-ID` HTTP header with a sequence number to resume from that point. Precedence: `since_seq` query param > persisted consumer offset > `Last-Event-ID` header.
- Stale reconnect rejection: If `Last-Event-ID` exceeds current max seq in SQLite, returns HTTP 412 Precondition Failed.

### scripts/eventbus/health_route.py

`health_check(request)`: `GET /health`. See `06_eventbus_05_configuration-and-operations.md` for monitoring thresholds.

### HTTP Endpoints Summary

`/publish`(POST), `/replay`(GET), `/subscribe`(GET), `/health`(GET), `/dlq`(GET), `/dlq/{id}/requeue`(POST), `/events/{id}/ack`(POST), `/nack`(POST).

---

## Broker and Offsets

### scripts/eventbus/broker.py

`_Subscriber`: Internal data structure holding the queue, topic list, and disconnect signal. `EventBroker`: In-memory pub/sub broker with topic-based fanout.

Methods: `subscribe(topics→_Subscriber, consumer_id=str)`, `unsubscribe(sub→None)`, `publish(event→int)`, `shutdown()`, `subscriber_count()→int`, `max_queue_depth()→int`, `slow_consumer_count()→int`, `overflow_disconnect_count()→int`, `duplicate_rejection_count()→int`.

### scripts/eventbus/offsets.py

`read_offset(offsets_dir, consumer_id)→int`: Reads saved offset (returns 0 if not found). `write_offset(offsets_dir, consumer_id, seq)→None`: Only writes to file if `seq` is greater than the current committed offset. Skips and logs a warning if `seq <= current` (ensures monotonicity).

## Related Documents

- `06_eventbus_00_document-guide.md`
- `06_eventbus_01_system-overview.md`
- `06_eventbus_02_operations.md`
