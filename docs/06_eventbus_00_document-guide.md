---
title: "Event Bus: Document Guide"
category: eventbus
tags:
  - event-bus
  - documentation
  - guide
  - routing
  - file-index
related:
  - 06_eventbus_01_system-overview.md
  - 06_eventbus_02_publish-replay.md
  - 06_eventbus_02_subscribe-ack.md
  - 06_eventbus_02_nack-health-dlq.md
  - 06_eventbus_06_reference-api-core-modules.md
source:
  - index.md
---

# Event Bus: Document Guide

## Purpose

These documents describe the `scripts/eventbus/` implementation. Use them when implementing, debugging, or extending Event Bus features.

## Reading order

| File | When to read |
|---|---|
| `06_eventbus_01_system-overview.md` | Starting point: architecture, capabilities, security model |
| `06_eventbus_02_publish-replay.md` | POST /publish, GET /replay endpoints |
| `06_eventbus_02_subscribe-ack.md` | GET /subscribe, POST /events/{event_id}/ack |
| `06_eventbus_02_nack-health-dlq.md` | POST /nack, GET /health, DLQ management |
| `06_eventbus_02_dlq-background-loop.md` | DLQ sweep background loop |
| `06_eventbus_02_failure-behavior-summary.md` | Failure behavior summary table |
| `06_eventbus_03_persistence_schema_and_replay.md` | SQLite schema, WAL, JSONL archive, replay semantics |
| `06_eventbus_04_dlq_offsets_and_delivery_semantics.md` | DLQ promotion, consumer offsets, at-least-once guarantees |
| `06_eventbus_05_config-env-and-fields.md` | Environment variables + Config fields |
| `06_eventbus_05_bind-address-and-start.md` | Bind Address rules + Start command |
| `06_eventbus_05_health-endpoint-semantics.md` | Health endpoint semantics |
| `06_eventbus_05_consumer-id-stability.md` | Consumer ID stability |
| `06_eventbus_05_delivery-operations.md` | Verification, monitoring, reconnect recovery |
| `06_eventbus_05_dlq-operations.md` | DLQ operations |
| `06_eventbus_05_validation-status.md` | CI verification status |
| `06_eventbus_06_reference-api-core-modules.md` | Core module APIs (app.py, config.py, db.py, dlq.py) |
| `06_eventbus_06_reference-api-route-handlers.md` | Route handler APIs |
| `06_eventbus_06_reference-api-broker-and-offsets.md` | Broker and offset APIs |
| `06_eventbus_90_inconsistencies_and_known_issues.md` | Known schema/implementation gaps, unconfirmed items |

## AI routing

Load these docs for Event Bus tasks:

- Implementing or debugging `scripts/eventbus/*.py`: `01`, `02`, `03`, `04`
- Config/env/deployment: `05`
- Known issues: `90`
- Module API: `06`

## AI Query Routing Table

| Question | File |
|---|---|
| What is the Event Bus and how does it work? | `06_eventbus_01` |
| How do I publish or replay events? | `06_eventbus_02` (§Publish-Replay) |
| How do I subscribe or acknowledge events? | `06_eventbus_02` (§Subscribe-Ack) |
| How do I nack, check health, or manage DLQ? | `06_eventbus_02` (§Nack-Health-DLQ) |
| What is the DLQ background loop? | `06_eventbus_02` (§DLQ Background Loop) |
| What failure behaviors should I know about? | `06_eventbus_02` (§Failure Behavior Summary) |
| What are the config fields and env vars? | `06_eventbus_05` (§Config Env and Fields) |
| What bind address rules apply? | `06_eventbus_05` (§Bind Address and Start Command) |
| How does the health endpoint work? | `06_eventbus_05` (§Health Endpoint Semantics) |
| What is consumer ID stability? | `06_eventbus_05` (§Consumer ID Stability) |
| How do I verify delivery and monitor consumers? | `06_eventbus_05` (§Delivery Operations) |
| How do DLQ operations work? | `06_eventbus_05` (§DLQ Operations) |
| What is the CI validation status? | `06_eventbus_05` (§Validation Status) |
| What is the persistence layer? | `06_eventbus_03` |
| What are the DLQ, offset, and delivery semantics? | `06_eventbus_04` |
| Where is class X defined and what are its callers? | `06_eventbus_06` (§Reference API Core Modules / Route Handlers / Broker and Offsets) |
| What are the known issues and spec conflicts? | `06_eventbus_90` |

## File Index

| File | Description |
|---|---|
| [06_eventbus_00_document-guide.md](06_eventbus_00_document-guide.md) | Entry point |
| [06_eventbus_01_system-overview.md](06_eventbus_01_system-overview.md) | Architecture, capabilities, security model |
| [06_eventbus_02_publish-replay.md](06_eventbus_02_publish-replay.md) | POST /publish, GET /replay endpoints |
| [06_eventbus_02_subscribe-ack.md](06_eventbus_02_subscribe-ack.md) | GET /subscribe, POST /events/{event_id}/ack, POST /ack |
| [06_eventbus_02_nack-health-dlq.md](06_eventbus_02_nack-health-dlq.md) | POST /nack, GET /health, GET /dlq, POST /dlq/{event_id}/requeue |
| [06_eventbus_02_dlq-background-loop.md](06_eventbus_02_dlq-background-loop.md) | DLQ sweep background loop |
| [06_eventbus_02_failure-behavior-summary.md](06_eventbus_02_failure-behavior-summary.md) | Failure behavior summary table |
| [06_eventbus_03_persistence_schema_and_replay.md](06_eventbus_03_persistence_schema_and_replay.md) | SQLite schema, WAL, JSONL archive, replay semantics |
| [06_eventbus_04_dlq_offsets_and_delivery_semantics.md](06_eventbus_04_dlq_offsets_and_delivery_semantics.md) | DLQ promotion, consumer offsets, at-least-once guarantees |
| [06_eventbus_05_config-env-and-fields.md](06_eventbus_05_config-env-and-fields.md) | Environment variables + Config fields |
| [06_eventbus_05_bind-address-and-start.md](06_eventbus_05_bind-address-and-start.md) | Bind Address + Start command + TOML example |
| [06_eventbus_05_health-endpoint-semantics.md](06_eventbus_05_health-endpoint-semantics.md) | Health endpoint semantics |
| [06_eventbus_05_consumer-id-stability.md](06_eventbus_05_consumer-id-stability.md) | Consumer ID stability |
| [06_eventbus_05_delivery-operations.md](06_eventbus_05_delivery-operations.md) | Verification, monitoring, reconnect, subscriber count |
| [06_eventbus_05_dlq-operations.md](06_eventbus_05_dlq-operations.md) | DLQ file creation, background loop, requeue, monitoring |
| [06_eventbus_05_validation-status.md](06_eventbus_05_validation-status.md) | CI verification status |
| [06_eventbus_06_reference-api-core-modules.md](06_eventbus_06_reference-api-core-modules.md) | app.py, config.py, db.py, dlq.py module APIs |
| [06_eventbus_06_reference-api-route-handlers.md](06_eventbus_06_reference-api-route-handlers.md) | publish_route.py, ack_route.py, dlq_route.py, replay_route.py, subscribe_route.py, health_route.py |
| [06_eventbus_06_reference-api-broker-and-offsets.md](06_eventbus_06_reference-api-broker-and-offsets.md) | broker.py, offsets.py module APIs |
| [06_eventbus_90_inconsistencies_and_known_issues.md](06_eventbus_90_inconsistencies_and_known_issues.md) | Known bugs, spec conflicts, open questions, deferred items |

## Canonical source rule

The canonical source of truth for behavior is the **source code** (`scripts/eventbus/`), not these documents. When a document conflicts with the code, trust the code and update the document.

## Related Documents

- `06_eventbus_01_system-overview.md`
- `06_eventbus_03_persistence_schema_and_replay.md`
- `06_eventbus_04_dlq_offsets_and_delivery_semantics.md`
- `06_eventbus_05_config-env-and-fields.md`
- `06_eventbus_06_reference-api-core-modules.md`

## Keywords

event-bus
documentation
guide
routing
file-index
