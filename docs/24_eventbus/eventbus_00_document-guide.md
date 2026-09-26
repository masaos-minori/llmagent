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
| Overview & Architecture | `eventbus_01_system-overview.md` |
| Primary Operations (publish/replay/subscribe/ack/nack/DLQ) | `eventbus_03_*`, `eventbus_04_*`, `eventbus_05_*` |
| Persistence & Schema | `eventbus_07_persistence_schema_and_replay.md` |
| Delivery Semantics & Consumer Responsibilities | `eventbus_06_dlq_offsets_and_delivery_semantics.md` |
| Configuration, Security Constraints & Operations | `eventbus_09_configuration-and-operations.md` |
| Validation Status | `eventbus_08_validation_status.md` |
| Reference API (for detailed verification) | `eventbus_10_reference_api.md` |
| Known Issues & Pending Items | `governance_03_issue-and-uncertainty-management.md` (Part 1, Area: EventBus) |

## AI Query Routing

| Question | Rule |
|---|---|
| Event Bus design intent & architecture | `eventbus_01` |
| Publishing / replaying / subscribing / acking / nacking / DLQ events | `eventbus_03`, `eventbus_04`, `eventbus_05` |
| Persistence layer & canonical data | `eventbus_07` |
| Delivery semantics & consumer responsibilities | `eventbus_06` |
| Configuration, bind address, health checks & operations | `eventbus_09` |
| API details, types & schemas | `eventbus_10` |
| Known issues & specification inconsistencies | `governance_03_issue-and-uncertainty-management.md` (Part 1, Area: EventBus) |

## Canonical Source Rule

See EventBus runtime-behavior and EventBus persistence-schema in the Canonical Source Registry.

## Known Issues / Deferred Items

Known limitations, specification gaps, and pending items are centrally managed in `governance_03_issue-and-uncertainty-management.md` (Part 1, Area: EventBus). Do not duplicate them in individual chapters.

## Reference API

`eventbus_10_*` files are Reference APIs containing detailed API specifications (type definitions, schemas, endpoint specifications). Refer to them as needed after verifying design decisions, but they are separate from the core design documentation.

## Governance

Cross-cutting documentation rules and policies:

- [Documentation Policy](../00_governance/governance_01_documentation-policy.md)
- [Documentation Metadata](../00_governance/governance_02_documentation-metadata.md)
- [Issue and Uncertainty Management](../00_governance/governance_03_issue-and-uncertainty-management.md)
- [Documentation Checks](../00_governance/governance_04_documentation-checks.md)

## Related ADRs

- [ADR-006](../10_adr/ADR-006-eventbus-sqlite-persistence-and-sse-delivery.md) — EventBusのSQLite永続化とSSE配信方式
- [ADR-008](../10_adr/ADR-008-sqlite-4db-separation.md) — SQLiteを4DBへ分離する

## Related Documents

- `eventbus_01_system-overview.md`
- `eventbus_07_persistence_schema_and_replay.md`
- `eventbus_06_dlq_offsets_and_delivery_semantics.md`
- `eventbus_09_configuration-and-operations.md`
- `eventbus_10_reference_api.md`
