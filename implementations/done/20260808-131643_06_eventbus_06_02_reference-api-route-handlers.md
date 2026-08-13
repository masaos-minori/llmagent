## Goal

Rebuild the shared/reference API chapter by compressing or removing implementation details such as complete module-by-module API enumeration, function signature tables, and per-route handler response field tables while explicitly preserving: minimal implementation reference index only (core: app/config/db/dlq, routes: publish/replay/subscribe/ack/nack/dlq/health, broker: EventBroker, offsets: read/write offset).

## Scope

**In-Scope**: 
- `docs/06_eventbus_06_02_reference-api-route-handlers.md` structure change
- `docs/06_eventbus_06_03_reference-api-broker-and-offsets.md` structure change

**Out-of-Scope**: Other eventbus related chapters (`docs/06_eventbus_*.md`), source code changes, tests.

## Assumptions

- This chapter should be maintained as the authoritative reference for API routing.
- This chapter focuses on design intent, not implementation details.
- Existing internal links and cross-references must remain valid after editing.

## Design decisions

- Compress complete function signature tables into high-level route category references.
- Replace exhaustive response field tables with "response includes event_id, status fields" statements.
- Retain explicit route listing as minimal index.

## Alternatives considered

- Full removal of all API details: rejected because routing source of truth becomes unclear without any concrete anchors.
- Keeping full function signatures and response field tables: rejected because they drift from reality as APIs evolve and add noise to the overview.

## Implementation

### Target files

- `docs/06_eventbus_06_02_reference-api-route-handlers.md`
- `docs/06_eventbus_06_03_reference-api-broker-and-offsets.md`

### Procedure

1. Read current chapter contents.
2. For each route handler module, replace complete function signature table with "route handlers exist for X purpose".
3. Compress/remove complete response field tables — retain only primary response fields (event_id, delivery_failure_count, etc.).
4. Compress/remove error response field tables — retain only HTTP status codes and conditions.
5. Compress/remove EventBroker method signature tables — replace with "methods: subscribe, unsubscribe, publish, shutdown, subscriber_count, max_queue_depth, slow_consumer_count".
6. Compress/remove offsets.py function signature tables — replace with "functions: read_offset, write_offset".
7. Verify preservation of minimal implementation reference index: core modules (app/config/db/dlq), routes (publish/replay/subscribe/ack/nack/dlq/health), broker (EventBroker), offsets (read/write offset).
8. Validate all internal Markdown links and cross-references.
9. Confirm compliance with `memo-doc-eventbus-review.md` §「修正後の章構成テンプレート」.

### Method

Document compression via selective deletion of exhaustive API documentation while retaining structural routing ownership declarations that point to source modules.

### Details

- **Preserve**: Minimal implementation reference index — core modules (app/config/db/dlq), routes (publish/replay/subscribe/ack/nack/dlq/health), broker (EventBroker), offsets (read/write offset); route handler existence (publish_route, ack_route, dlq_route, replay_route, subscribe_route, health_route); EventBroker class existence; _Subscriber internal dataclass existence; read_offset/write_offset functions existence.
- **Compress/remove**: Complete function signature tables → replace with "route handlers exist for X purpose"; complete response field tables → replace with "response includes event_id, status fields"; error response field tables → replace with "error responses use standard HTTP status codes"; EventBroker method signature tables → replace with "methods: subscribe, unsubscribe, publish, shutdown, subscriber_count, max_queue_depth, slow_consumer_count"; offsets.py function signature tables → replace with "functions: read_offset, write_offset".
- **Verify**: Cross-reference to scripts/eventbus/app.py exists; minimal implementation reference index clear; internal Markdown links valid; template compliance.

## Compatibility considerations

N/A — document-only phase.

## Security considerations

N/A — document-only phase.

## Rollback considerations

N/A — document-only phase.

## Validation plan

| Check | Tool | Target |
|---|---|---|
| Minimal Implementation Reference Index Only | Manual | Explicitly preserved |
| Core Modules Listed As Minimal Index | Manual | Explicitly preserved |
| Routes Listed As Minimal Index | Manual | Explicitly preserved |
| Broker Listed As Minimal Index | Manual | Explicitly preserved |
| Offset Listed As Minimal Index | Manual | Explicitly preserved |
| Internal Links | Manual | All cross-references valid |
| Template Compliance | Manual | Follows `memo-doc-eventbus-review.md` §「修正後の章構成テンプレート」 |

## Out of scope

Other eventbus related chapters, source code changes, tests.

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260807-234605_plan.md
- Source implementation procedure: N/A
- Generated at: 20260808-131643
- Related target files: 06_eventbus_06_02_reference-api-route-handlers.md, 06_eventbus_06_03_reference-api-broker-and-offsets.md
