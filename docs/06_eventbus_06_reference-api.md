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

`dlq_list(request, limit=100, offset=0)`: `GET /dlq`. `dlq_requeue(request, event_id)`: `POST /dlq/{event_id}/requeue`. If `failure_count >= max_retry`, it may be re-moved to the DLQ.

### scripts/eventbus/replay_route.py

`replay(request, since_seq=0, fmt=sse, limit=100, offset=0)`: `GET /replay`. SSE stream or paginated JSON.

### scripts/eventbus/subscribe_route.py

`subscribe(request, topic=[], since_seq=0, consumer_id="")`: `GET /subscribe`. SSE streaming + replay+push.

### scripts/eventbus/health_route.py

`health_check(request)`: `GET /health`.

### HTTP Endpoints Summary

`/publish`(POST), `/replay`(GET), `/subscribe`(GET), `/health`(GET), `/dlq`(GET), `/dlq/{id}/requeue`(POST), `/events/{id}/ack`(POST), `/nack`(POST).

---

## Broker and Offsets

### scripts/eventbus/broker.py

`_Subscriber`: Internal data structure holding the queue and topic list. `EventBroker`: In-memory pub/sub broker with topic-based fanout.

Methods: `subscribe(topics→_Subscriber)`, `unsubscribe(sub→None)`, `publish(event→int)`, `shutdown()`, `subscriber_count()→int`, `max_queue_depth()→int`, `slow_consumer_count()→int`.

### scripts/eventbus/offsets.py

`read_offset(offsets_dir, consumer_id)→int`: Reads saved offset (returns 0 if not found). `write_offset(offsets_dir, consumer_id, seq)→None`: Only writes to file if `seq` is greater than the current committed offset. Skips and logs a warning if `seq <= current` (ensures monotonicity).

## Related Documents

- `06_eventbus_00_document-guide.md`
- `06_eventbus_01_system-overview.md`
- `06_eventbus_02_operations.md`
