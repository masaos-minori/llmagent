# Implementation Procedure: Convert EventBus Known Issues to 17-Field Format

## Goal
Convert `docs/06_eventbus_90_inconsistencies_and_known_issues.md`'s EVENTBUS-001 through EVENTBUS-007 entries from section/table format to individual 17-field entries per common template, preserving IDs and all content including "保留中"/"スキーマと実装の差異" narrative.

## Scope
- Target file: `docs/06_eventbus_90_inconsistencies_and_known_issues.md`
- Convert EVENTBUS-001 through EVENTBUS-007 to individual 17-field entries
- Preserve IDs and all content including "保留中"/"スキーマと実装の差異" content
- EVENTBUS-005/006/007 (currently combined) separated into three individual entries
- "スキーマと実装の差異" section's 4 field names represented as closing note or informational entry

## Assumptions
- Current format uses section-based grouping ("対応が必要な項目", "ドキュメント対応のみ", "保留中") with table-based format
- EVENTBUS-005/006/007 currently combined in single "保留中" mention
- "スキーマと実装の差異" section's 4 field names (`acked_at`, `delivery_failure_count`, `dlq_requeue_count`, `dlq_at`) are documentation only (all in active use, no discrepancy)

## Design decisions
- Each EVENTBUS-00N becomes individual 17-field entry block
- EVENTBUS-005/006/007 separated into three entries, each `Status: deferred`, `Type: design-gap` (or `operational-gap`), preserving "Agent 統合は意図的に未実装" rationale
- "スキーマと実装の差異" section's 4 field names represented as closing note or single informational entry (not a Known Issue since no inconsistency exists)
- Japanese section groupings preserved as informative subheadings if desired

## Implementation
### Target file
`docs/06_eventbus_90_inconsistencies_and_known_issues.md`

### Procedure
1. Read the current file
2. Convert each EVENTBUS-00N to 17-field entry
3. Separate EVENTBUS-005/006/007 into three entries
4. Handle "スキーマと実装の差異" content appropriately
5. Replace section/table format with individual entry blocks

### Method
Direct Markdown editing with structural rewrite

### Details
**Entry Template (17 fields):**
```markdown
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
```

**EVENTBUS-002 (similar structure):**
```markdown
### EVENTBUS-002: /replay?format=json ページネーション形式

- **ID**: EVENTBUS-002
- **Title**: /replay?format=json ページネーション形式
- **Status**: open
- **Severity**: Low
- **Type**: documentation-gap
- **Component**: eventbus/replay endpoint
- **Description**: `{total, limit, offset, items}` を返す。ドキュメントに明記必要。
...
```

**EVENTBUS-003/004 (similar):**
```markdown
### EVENTBUS-003: DLQ promotion の2経路

### EVENTBUS-004: promote_to_dlq() デッドコード
```

**EVENTBUS-005/006/007 (separated):**
```markdown
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

### EVENTBUS-007: Agent トピック
```
(Same structure for 006/007 with appropriate titles/descriptions)

**"スキーマと実装の差異" Handling:**
```markdown
### Note: スキーマと実装の差異 (Informational)

The following fields are documented in the schema and are all currently in active use — no discrepancy exists:
- `acked_at` (冪等)
- `delivery_failure_count` (nack時増加)
- `dlq_requeue_count` (requeue時増加)
- `dlq_at` (DLQ昇格時)

This section is retained for documentation completeness; no inconsistency exists.
```

## Compatibility considerations
- Documentation-only rewrite
- All IDs and content preserved
- EVENTBUS-005/006/007 separated but content preserved
- "スキーマと実装の差異" content preserved as informational note

## Security considerations
- None — documentation only

## Rollback considerations
- Git revert of this file

## Validation plan
- Manual diff: each EVENTBUS-001..007 has 17 fields
- ID set unchanged (001..007)
- "保留中"/"スキーマと実装の差異" content preserved without loss
- `git diff` shows structural change only

## Out of scope
- Resolving any EVENTBUS issue
- Adding new entries

## Traceability
- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: requires/done/20260818-221756_require.md
- Source plan: plans/20260819-175514_plan.md
- Source implementation procedure: N/A
- Generated at: 20260820-134538
- Related target files: docs/06_eventbus_90_inconsistencies_and_known_issues.md