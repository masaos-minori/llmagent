---
title: "Event Bus: Document Guide"
area: eventbus
tags:
  - eventbus
  - document-guide
related:
  - eventbus_01_system-overview.md
  - eventbus_02_api-reference-index.md
  - eventbus_03_dlq_operations.md
  - eventbus_04_dlq_endpoint.md
  - eventbus_10_publish_durability.md
  - eventbus_11_health_endpoint.md
  - eventbus_12_replay_endpoint.md
  - eventbus_13_ack_nack_endpoints.md
  - eventbus_06_persistence_schema_and_replay.md
  - eventbus_05_dlq_offsets_and_delivery_semantics.md
  - eventbus_07_validation_status.md
  - eventbus_08_configuration-and-operations.md
  - eventbus_09_reference_api.md
---
# Event Bus: Document Guide

## Purpose

These documents describe the implementation of `scripts/eventbus/`. Use them when implementing, debugging, or extending the Event Bus functionality.

## Reading Order

| Category | File |
|---|---|
| Overview & Architecture | `eventbus_01_system-overview.md` |
| Publish, subscribe and DLQ promotion | `eventbus_03_dlq_operations.md` |
| Publish durability | `eventbus_10_publish_durability.md` |
| HTTP API index and authentication model | `eventbus_02_api-reference-index.md` |
| Endpoint references: DLQ, health, replay, ACK/NACK | `eventbus_04_dlq_endpoint.md`, `eventbus_11_health_endpoint.md`, `eventbus_12_replay_endpoint.md`, `eventbus_13_ack_nack_endpoints.md` |
| Persistence & Schema | `eventbus_06_persistence_schema_and_replay.md` |
| Delivery Semantics & Consumer Responsibilities | `eventbus_05_dlq_offsets_and_delivery_semantics.md` |
| Configuration, Security Constraints & Operations | `eventbus_08_configuration-and-operations.md` |
| Validation Status | `eventbus_07_validation_status.md` |
| Reference API (for detailed verification) | `eventbus_09_reference_api.md` |
| Known Issues & Pending Items | `governance_03_issue-and-uncertainty-management.md` (Part 1, Area: EventBus) |

## AI Query Routing

| Question | Rule |
|---|---|
| Event Bus design intent & architecture | `eventbus_01` |
| Publishing / subscribing, DLQ promotion | `eventbus_03` |
| Publish durability | `eventbus_10` |
| Replay endpoint | `eventbus_12` |
| ACK / NACK endpoints and state transitions | `eventbus_13` |
| DLQ list / requeue endpoints | `eventbus_04` |
| Health endpoint | `eventbus_11` |
| API index, roles and authentication | `eventbus_02` |
| Persistence layer & canonical data | `eventbus_06` |
| Delivery semantics & consumer responsibilities | `eventbus_05` |
| Configuration, bind address, health checks & operations | `eventbus_08` |
| API details, types & schemas | `eventbus_09` |
| Known issues & specification inconsistencies | `governance_03_issue-and-uncertainty-management.md` (Part 1, Area: EventBus) |

## Canonical Source Rule

See EventBus runtime-behavior and EventBus persistence-schema in the Canonical Source Registry.

## Known Issues / Deferred Items

Known limitations, specification gaps, and pending items are centrally managed in `governance_03_issue-and-uncertainty-management.md` (Part 1, Area: EventBus). Do not duplicate them in individual chapters.

## Reference API

`eventbus_09_*` files are Reference APIs containing detailed API specifications (type definitions, schemas, endpoint specifications). Refer to them as needed after verifying design decisions, but they are separate from the core design documentation.

## Governance

Cross-cutting documentation rules and policies:

- [Documentation Policy](../00_governance/governance_01_documentation-policy.md)
- [Documentation Metadata](../00_governance/governance_02_documentation-metadata.md)
- [Issue and Uncertainty Management](../00_governance/governance_03_issue-and-uncertainty-management.md)
- [Documentation Checks](../00_governance/governance_04_documentation-checks.md)

## Related ADRs

- [ADR-006](../10_adr/ADR-006-eventbus-sqlite-persistence-and-sse-delivery.md) — EventBus SQLite Persistence and SSE Delivery
- [ADR-008](../10_adr/ADR-008-sqlite-4db-separation.md) — Separating SQLite into Four Databases

## Keywords

- eventbus
- document-guide
