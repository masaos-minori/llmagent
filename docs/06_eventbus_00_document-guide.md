# Event Bus: Document Guide

## Purpose

These documents describe the implementation of `scripts/eventbus/`. Use them when implementing, debugging, or extending the Event Bus functionality.

## Reading Order

| Category | File |
|---|---|
| Overview & Architecture | `06_eventbus_01_system-overview.md` |
| Primary Operations (publish/replay/subscribe/ack/nack/DLQ) | `06_eventbus_02_*` |
| Persistence & Schema | `06_eventbus_03_persistence_schema_and_replay.md` |
| Delivery Semantics & Consumer Responsibilities | `06_eventbus_04_dlq_offsets_and_delivery_semantics.md` |
| Configuration, Security Constraints & Operations | `06_eventbus_05_*` |
| Reference API (for detailed verification) | `06_eventbus_06_*` |
| Known Issues & Pending Items | `06_eventbus_90_inconsistencies_and_known_issues.md` |

## AI Query Routing

| Question | Rule |
|---|---|
| Event Bus design intent & architecture | `06_eventbus_01` |
| Publishing / replaying / subscribing / acking / nacking / DLQ events | `06_eventbus_02` |
| Persistence layer & canonical data | `06_eventbus_03` |
| Delivery semantics & consumer responsibilities | `06_eventbus_04` |
| Configuration, bind address, health checks & operations | `06_eventbus_05` |
| API details, types & schemas | `06_eventbus_06` |
| Known issues & specification inconsistencies | `06_eventbus_90` |

## Canonical Source Rule

The canonical source for behavior is the **source code** (`scripts/eventbus/`), not these documents. If there is a conflict between the documentation and the code, trust the code and update the documentation.

## Known Issues / Deferred Items

Known limitations, specification gaps, and pending items are centrally managed in `06_eventbus_90_inconsistencies_and_known_issues.md`. Do not duplicate them in individual chapters.

## Reference API

`06_eventbus_06_*` files are Reference APIs containing detailed API specifications (type definitions, schemas, endpoint specifications). Refer to them as needed after verifying design decisions, but they are separate from the core design documentation.

## Governance

Cross-cutting documentation rules and policies:

- [Documentation Governance](00_governance_01_documentation-governance.md)
- [Canonical Source Rule](00_governance_02_canonical-source-rule.md)
- [Evidence Labels](00_governance_03_evidence-labels.md)
- [Known Issues Template](00_governance_14_issue-and-uncertainty-management.md)
- [Deprecated Items](00_governance_14_issue-and-uncertainty-management.md)
- [AI Reading Metadata](00_governance_13_documentation-metadata.md)
- [Terminology Glossary](00_governance_13_documentation-metadata.md)

## Related ADRs

- [ADR-006](adr/ADR-006-eventbus-sqlite-persistence-and-sse-delivery.md) — EventBusのSQLite永続化とSSE配信方式
- [ADR-008](adr/ADR-008-sqlite-4db-separation.md) — SQLiteを4DBへ分離する

## Related Documents

- `06_eventbus_01_system-overview.md`
- `06_eventbus_03_persistence_schema_and_replay.md`
- `06_eventbus_04_dlq_offsets_and_delivery_semantics.md`
- `06_eventbus_05_01_config-env-and-fields.md`
- `06_eventbus_06_01_reference-api-core-modules.md`
