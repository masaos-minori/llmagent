---
title: "Event Bus: Reference API — Route Handlers"
area: eventbus
tags:
  - event-bus
  - api-reference
  - route-handlers
  - publish-route
  - ack-route
  - dlq-route
  - replay-route
  - subscribe-route
  - health-route
related:
  - 06_eventbus_00_document-guide.md
  - 06_eventbus_01_system-overview.md
  - 06_eventbus_06_01_reference-api-core-modules.md
  - 06_eventbus_06_03_reference-api-broker-and-offsets.md
source:
  - 06_eventbus_06_01_reference-api-core-modules.md
---

# Event Bus: Reference API — Route Handlers

## scripts/eventbus/publish_route.py

`publish(request)`: `POST /publish`. JSON Schema validation → DB insertion → JSONL append → Broker notification. JSONL append failure does not surface as an HTTP error (Warning log + 200).

## scripts/eventbus/ack_route.py

`ack_event(request, event_id, consumer_id)`: `POST /events/{event_id}/ack`. `nack(request, event_id)`: `POST /nack`. Increments failure count; promotes to DLQ if `>= max_retry`.

## scripts/eventbus/dlq_route.py

`dlq_list(request, limit=100, offset=0)`: `GET /dlq`. `dlq_requeue(request, event_id)`: `POST /dlq/{event_id}/requeue`. If `failure_count >= max_retry`, it may be re-moved to the DLQ.

## scripts/eventbus/replay_route.py

`replay(request, since_seq=0, fmt=sse, limit=100, offset=0)`: `GET /replay`. SSE stream or paginated JSON.

## scripts/eventbus/subscribe_route.py

`subscribe(request, topic=[], since_seq=0, consumer_id="")`: `GET /subscribe`. SSE streaming + replay+push.

## scripts/eventbus/health_route.py

`health_check(request)`: `GET /health`.

## EventBroker Class

Located in `scripts/eventbus/broker.py`. Methods: `subscribe`, `unsubscribe`, `publish`, `shutdown`, `subscriber_count`, `max_queue_depth`, `slow_consumer_count`.

## _Subscriber Data Class

Located in `scripts/eventbus/broker.py`. Internal data structure holding subscriber information.

## offsets.py Functions

Located in `scripts/eventbus/offsets.py`. Functions: `read_offset`, `write_offset`.

## HTTP Endpoints

`/publish`(POST), `/replay`(GET), `/subscribe`(GET), `/health`(GET), `/dlq`(GET), `/dlq/{id}/requeue`(POST), `/events/{id}/ack`(POST), `/nack`(POST).

## Related Documents

- `06_eventbus_06_01_reference-api-core-modules.md`
- `06_eventbus_06_03_reference-api-broker-and-offsets.md`
