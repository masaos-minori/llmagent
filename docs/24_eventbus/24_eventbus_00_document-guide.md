---
title: "Event Bus: Document Guide"
area: eventbus
tags:
  - eventbus
  - document-guide
related:
---
# Event Bus: Document Guide

## Purpose

These documents describe the implementation of `scripts/eventbus/`. Use them when implementing, debugging, or extending the Event Bus functionality.

## Reading Order

| Category | File |
|---|---|
| Overview & Architecture | `24_eventbus_01_system-overview_00_document-guide.md` |
| Primary Operations (publish/replay/subscribe/ack/nack/DLQ) | `24_eventbus_03_*`, `24_eventbus_04_*`, `24_eventbus_05_*` |
| Persistence & Schema | `24_eventbus_07_persistence_schema_and_replay.md` |
| Delivery Semantics & Consumer Responsibilities | `24_eventbus_06_dlq_offsets_and_delivery_semantics.md` |
| Configuration, Security Constraints & Operations | `24_eventbus_09_configuration-and-operations.md` |
| Validation Status | `24_eventbus_08_validation_status.md` |
| Reference API (for detailed verification) | `24_eventbus_10_reference_api.md` |
| Known Issues & Pending Items | `governance_03_issue-and-uncertainty-management.md` (Part 1, Area: EventBus) |

## AI Query Routing

| Question | Rule |
|---|---|
| Event Bus design intent & architecture | `24_eventbus_01` |
| Publishing / replaying / subscribing / acking / nacking / DLQ events | `24_eventbus_03`, `24_eventbus_04`, `24_eventbus_05` |
| Persistence layer & canonical data | `24_eventbus_07` |
| Delivery semantics & consumer responsibilities | `24_eventbus_06` |
| Configuration, bind address, health checks & operations | `24_eventbus_09` |
| API details, types & schemas | `24_eventbus_10` |
| Known issues & specification inconsistencies | `governance_03_issue-and-uncertainty-management.md` (Part 1, Area: EventBus) |

## Canonical Source Rule

See [EventBus runtime-behavior](../config/documentation_canonical_sources.toml#eventbuscore-behavior) and [EventBus persistence-schema](../config/documentation_canonical_sources.toml#eventbuspersistence-schema) in the Canonical Source Registry.

## Known Issues / Deferred Items

Known limitations, specification gaps, and pending items are centrally managed in `governance_03_issue-and-uncertainty-management.md` (Part 1, Area: EventBus). Do not duplicate them in individual chapters.

## Reference API

`24_eventbus_10_*` files are Reference APIs containing detailed API specifications (type definitions, schemas, endpoint specifications). Refer to them as needed after verifying design decisions, but they are separate from the core design documentation.

## Governance

Cross-cutting documentation rules and policies:

- [Documentation Policy](governance_01_documentation-policy.md)
- [Documentation Metadata](governance_02_documentation-metadata.md)
- [Issue and Uncertainty Management](governance_03_issue-and-uncertainty-management.md)
- [Documentation Checks](governance_04_documentation-checks.md)

## Related ADRs

- [ADR-006](adr/ADR-006-eventbus-sqlite-persistence-and-sse-delivery.md) — EventBusのSQLite永続化とSSE配信方式
- [ADR-008](adr/ADR-008-sqlite-4db-separation.md) — SQLiteを4DBへ分離する

## Related Documents

- `24_eventbus_01_system-overview_00_document-guide.md`
- `24_eventbus_07_persistence_schema_and_replay.md`
- `24_eventbus_06_dlq_offsets_and_delivery_semantics.md`
- `24_eventbus_09_configuration-and-operations.md`
- `24_eventbus_10_reference_api.md`
