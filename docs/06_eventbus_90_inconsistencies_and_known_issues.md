---
title: "Event Bus: Known Inconsistencies and Issues"
category: eventbus
tags:
  - event-bus
  - known-issues
  - inconsistencies
  - spec-conflicts
  - deferred-items
  - ack-offset
  - monotonicity
related:
  - 06_eventbus_00_document-guide.md
  - 06_eventbus_01_system-overview.md
  - 06_eventbus_02_02_subscribe-ack.md
  - 06_eventbus_02_04_dlq-background-loop.md
  - 06_eventbus_04_dlq_offsets_and_delivery_semantics.md
source:
  - index.md
---

# Event Bus: Known Inconsistencies and Issues

### EVENTBUS-001: Ack オフセットの単調性欠如

- **ID**: EVENTBUS-001
- **Title**: Ack オフセットの単調性欠如
- **Status**: open
- **Severity**: High
- **Type**: implementation-bug
- **Component**: eventbus/offsets.py (write_offset)
- **Description**: write_offset() に max(current, new) チェックなし。再接続時に重複受信の可能性あり。サーバー側修正予定なし。
- **Root Cause**: write_offset() lacks monotonicity check (max(current, new)); reconnection can cause duplicate delivery.
- **Impact**: Consumers may receive duplicate events on reconnection; offset can regress.
- **Recommended Action**: Add monotonicity check to write_offset(); consider server-side fix if operator demand arises.
- **Workaround**: Consumer-side dedup using event_id; handle out-of-order delivery.
- **Status Detail**: Open — no server-side fix planned.
- **Severity Justification**: High — affects all consumers on reconnection; silent duplicate delivery.
- **Type Justification**: Implementation bug — missing monotonicity guarantee in offset tracking.
- **Component Justification**: write_offset() in eventbus/offsets.py is the sole offset writer.
- **Related Issues**: EVENTBUS-002 (replay pagination), EVENTBUS-003 (DLQ dual path)
- **Resolution Target**: No fix planned (operator workaround documented)
- **Blocking**: No
- **Evidence**: Explicit in code — write_offset() lacks max() check; docs/06_eventbus_02_02_subscribe-ack.md §単調性に関する注記 confirms.

### EVENTBUS-002: /replay?format=json ページネーション形式

- **ID**: EVENTBUS-002
- **Title**: /replay?format=json ページネーション形式
- **Status**: open
- **Severity**: Low
- **Type**: documentation-gap
- **Component**: eventbus/replay endpoint
- **Description**: `{total, limit, offset, items}` を返す。ドキュメントに明記必要。
- **Root Cause**: Pagination response format not documented in API reference.
- **Impact**: Clients may not know to expect paginated response structure.
- **Recommended Action**: Add pagination format to `docs/06_eventbus_02_01_publish-replay.md` and `docs/06_eventbus_06_01_reference-api-core-modules.md`.
- **Workaround**: Clients can infer from response body.
- **Status Detail**: Open — documentation update pending.
- **Severity Justification**: Low — functionality works, only documentation missing.
- **Type Justification**: Documentation gap — behavior correct but undocumented.
- **Component Justification**: Replay endpoint in eventbus server.
- **Related Issues**: EVENTBUS-001 (offset monotonicity)
- **Resolution Target**: Next documentation cycle
- **Blocking**: No
- **Evidence**: Explicit in code — replay endpoint returns paginated JSON; docs lack format specification.

### EVENTBUS-003: DLQ promotion の2経路

- **ID**: EVENTBUS-003
- **Title**: DLQ promotion の2経路
- **Status**: open
- **Severity**: Medium
- **Type**: documentation-gap
- **Component**: eventbus/nack handler, eventbus/dlq background loop
- **Description**: /nack インライン昇格 + バックグラウンドスweep の2経路で DLQ 昇格が発生。両経路をドキュメントに明記必要。
- **Root Cause**: Two independent code paths promote to DLQ (inline in nack handler + background sweep); only one was documented.
- **Impact**: Operators may not understand all DLQ entry origins.
- **Recommended Action**: Document both paths in `docs/06_eventbus_02_03_nack-health-dlq.md` and `docs/06_eventbus_02_04_dlq-background-loop.md`.
- **Workaround**: None — documentation only.
- **Status Detail**: Open — documentation update pending.
- **Severity Justification**: Medium — affects operational understanding of DLQ behavior.
- **Type Justification**: Documentation gap — both paths exist in code but only one documented.
- **Component Justification**: nack_event() in ack_route.py and promote_single() in dlq.py.
- **Related Issues**: EVENTBUS-004 (promote_to_dlq dead code)
- **Resolution Target**: Next documentation cycle
- **Blocking**: No
- **Evidence**: Explicit in code — nack_event() calls promote_single() inline; dlq.py has background sweep calling promote_single().

### EVENTBUS-004: promote_to_dlq() デッドコード

- **ID**: EVENTBUS-004
- **Title**: promote_to_dlq() デッドコード
- **Status**: open
- **Severity**: Low
- **Type**: dead-code
- **Component**: eventbus/dlq.py (promote_to_dlq function)
- **Description**: promote_to_dlq() は未呼び出し。sweep_orphans() / promote_single() のみ正規経路。
- **Root Cause**: Function added but never wired into any call path; superseded by promote_single().
- **Impact**: Dead code increases maintenance surface; potential confusion during audits.
- **Recommended Action**: Remove promote_to_dlq() or add deprecation marker with migration note.
- **Workaround**: None — code is inert.
- **Status Detail**: Open — removal or documentation pending.
- **Severity Justification**: Low — dead code not executed, no runtime impact.
- **Type Justification**: Dead code — function exists but zero callers.
- **Component Justification**: dlq.py module.
- **Related Issues**: EVENTBUS-003 (DLQ dual path)
- **Resolution Target**: Next cleanup cycle
- **Blocking**: No
- **Evidence**: Explicit in code — grep shows zero callers of promote_to_dlq() in scripts/.

### EVENTBUS-005: Agent publish

- **ID**: EVENTBUS-005
- **Title**: Agent publish
- **Status**: deferred
- **Severity**: Low
- **Type**: design-gap
- **Component**: agent/eventbus integration
- **Description**: Agent 統合は意図的に未実装。Agent から Event Bus への publish 機能が未実装。
- **Root Cause**: Intentional deferral — Agent integration not prioritized.
- **Impact**: Agent cannot publish events to Event Bus; limits Agent-driven workflows.
- **Recommended Action**: Implement Agent → Event Bus publish when integration prioritized.
- **Workaround**: Direct MCP tool calls from Agent.
- **Status Detail**: Deferred — intentional, not a bug.
- **Severity Justification**: Low — intentional deferral, not a defect.
- **Type Justification**: Design gap — feature intentionally omitted from current scope.
- **Component Justification**: Agent-EventBus integration layer.
- **Related Issues**: EVENTBUS-006 (Agent SSE), EVENTBUS-007 (Agent topics)
- **Resolution Target**: Future (when Agent integration prioritized)
- **Blocking**: No
- **Evidence**: Explicit in code — no Agent publish path in eventbus client; "Agent 統合は意図的に未実装" in known issues.

### EVENTBUS-006: Agent SSE

- **ID**: EVENTBUS-006
- **Title**: Agent SSE
- **Status**: deferred
- **Severity**: Low
- **Type**: design-gap
- **Component**: agent/eventbus integration
- **Description**: Agent 統合は意図的に未実装。Agent が Event Bus の SSE ストリームを購読する機能が未実装。
- **Root Cause**: Intentional deferral — Agent integration not prioritized.
- **Impact**: Agent cannot subscribe to Event Bus event streams; limits real-time Agent workflows.
- **Recommended Action**: Implement Agent SSE subscribe when integration prioritized.
- **Workaround**: Agent polls via /replay or uses MCP tools.
- **Status Detail**: Deferred — intentional, not a bug.
- **Severity Justification**: Low — intentional deferral, not a defect.
- **Type Justification**: Design gap — feature intentionally omitted from current scope.
- **Component Justification**: Agent-EventBus integration layer.
- **Related Issues**: EVENTBUS-005 (Agent publish), EVENTBUS-007 (Agent topics)
- **Resolution Target**: Future (when Agent integration prioritized)
- **Blocking**: No
- **Evidence**: Explicit in code — no Agent SSE client in eventbus client; "Agent 統合は意図的に未実装" in known issues.

### EVENTBUS-007: Agent トピック

- **ID**: EVENTBUS-007
- **Title**: Agent トピック
- **Status**: deferred
- **Severity**: Low
- **Type**: design-gap
- **Component**: agent/eventbus integration
- **Description**: Agent 統合は意図的に未実装。Agent が Event Bus トピックを管理・操作する機能が未実装。
- **Root Cause**: Intentional deferral — Agent integration not prioritized.
- **Impact**: Agent cannot manage Event Bus topics; limits administrative workflows.
- **Recommended Action**: Implement Agent topic management when integration prioritized.
- **Workaround**: Direct MCP tool calls for topic management.
- **Status Detail**: Deferred — intentional, not a bug.
- **Severity Justification**: Low — intentional deferral, not a defect.
- **Type Justification**: Design gap — feature intentionally omitted from current scope.
- **Component Justification**: Agent-EventBus integration layer.
- **Related Issues**: EVENTBUS-005 (Agent publish), EVENTBUS-006 (Agent SSE)
- **Resolution Target**: Future (when Agent integration prioritized)
- **Blocking**: No
- **Evidence**: Explicit in code — no Agent topic management in eventbus client; "Agent 統合は意図的に未実装" in known issues.

### EVENTBUS-008: No production authentication model

- **ID**: EVENTBUS-008
- **Title**: No production authentication model
- **Status**: open
- **Severity**: High
- **Type**: security-gap
- **Component**: eventbus/config.py, eventbus route handlers
- **Description**: Event Bus の HTTP API（`/publish`、`/subscribe`、`/events/{event_id}/ack`、`/nack`、`/health`、`/dlq`、`/replay`）に本番グレードの認証/認可が存在しない。現在は loopback-only バインドと `allow_public_bind=false` による制御のみで、`allow_public_bind=true` にすると完全にオープンになる。本番環境での運用には認証モデルの実装が必要。
- **Root Cause**: No authentication middleware implemented; only network-level binding restriction.
- **Impact**: If `allow_public_bind=true` is set, all endpoints are publicly accessible without authentication.
- **Recommended Action**: Implement static bearer token validation in EventBus process; add auth middleware to route handlers.
- **Workaround**: Keep `allow_public_bind=false` and bind to loopback only; use SSH tunnels for remote access.
- **Status Detail**: Open — design note recorded, implementation deferred to future requirement.
- **Severity Justification**: High — production deployment requires authentication; current state allows unauthenticated access if misconfigured.
- **Type Justification**: Security gap — missing authentication/authorization layer.
- **Component Justification**: Config validation in config.py; route handlers in ack_route.py, subscribe_route.py, publish_route.py.
- **Related Issues**: EVENTBUS-001 (offset monotonicity)
- **Resolution Target**: Future requirement (design note recorded as EVENTBUS-008)
- **Blocking**: No
- **Evidence**: Explicit in code — no auth middleware; only `allow_public_bind` gate in config.py.

### Note: スキーマと実装の差異 (Informational)

The following fields are documented in the schema and are all currently in active use — no discrepancy exists:
- `acked_at` (冪等)
- `delivery_failure_count` (nack時増加)
- `dlq_requeue_count` (requeue時増加)
- `dlq_at` (DLQ昇格時)

This section is retained for documentation completeness; no inconsistency exists.

## Related Documents

- `06_eventbus_00_document-guide.md`
- `06_eventbus_01_system-overview.md`
- `06_eventbus_02_02_subscribe-ack.md`
- `06_eventbus_02_04_dlq-background-loop.md`
- `06_eventbus_04_dlq_offsets_and_delivery_semantics.md`