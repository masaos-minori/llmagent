# Design: EventBus Known Issues Doc Update — Reflect Current State

## Goal

Update `06_eventbus_90_inconsistencies_and_known_issues.md` to accurately reflect current active issues, resolved items, and safe interpretations based on all previous Event Bus require processing.

The known-issues doc is stale in several ways: it has incorrect terminology (retry_count instead of delivery_failure_count), references a resolved polling-based model that no longer applies, and is missing numerous active issues discovered across the 10 requires processed so far. This update consolidates everything into a single authoritative source of truth.

## Scope

**In-Scope**:
- Fix stale entries: retry_count → delivery_failure_count, remove polling-based /subscribe description
- Add all active issues discovered in previous requires (9 items)
- Add resolved items from previous requires (4 items)
- Add needs-confirmation items (FastAPI thread pool worker usage and any new items discovered during update)
- Standardize format: each item has Item description, Safe interpretation, Recommended action

**Out-of-Scope**:
- Fixing underlying runtime behavior unless covered by dependent issues
- Rewriting the full Event Bus documentation set
- Adding tests for the documented issues

## Assumptions

1. The known-issues doc should be a single source of truth for Event Bus inconsistencies
2. Items that have been resolved by previous require processing should be marked as resolved
3. New items discovered during require processing should be added as active or needs-confirmation
4. The format standardization (Item description, Safe interpretation, Recommended action) applies uniformly to all sections

## Implementation

### Phase 1: Fix stale entries in Schema vs implementation differences table

**Target file**: `docs/06_eventbus_90_inconsistencies_and_known_issues.md`

#### 1.1 Fix retry_count → delivery_failure_count

**Current line 8**:
```
| `retry_count` | INTEGER DEFAULT 0 | Incremented only on DLQ requeue; not incremented during normal delivery | By design |
```

**After edit**:
```
| `delivery_failure_count` | INTEGER DEFAULT 0 | Incremented only on DLQ requeue; not incremented during normal delivery | By design |
```

**Rationale**: The field is named `delivery_failure_count` in the actual schema (DDL). `retry_count` is a stale reference from earlier drafts. Safe interpretation: this counter tracks delivery failures, not retries. Recommended action: no action needed — the counter behavior is correct; only the doc terminology needs fixing.

#### 1.2 Remove polling-based /subscribe entry

**Current line 9**:
```
| `/subscribe` | SSE endpoint | Polling-based internally (not push) | By design; documented |
```

**After edit**: Move this row to Resolved Items section below. Remove from Schema vs implementation differences table entirely.

**Rationale**: The /subscribe endpoint uses a hybrid model: replay from SQLite followed by live EventBroker push. The "polling-based" description is incorrect and was already resolved by the `/subscribe` require. Recommended action: mark as resolved in Resolved Items section with reference to the require that fixed it.

### Phase 2: Add active issues from previous requires

**Target file**: `docs/06_eventbus_90_inconsistencies_and_known_issues.md`

Add a new "Active Issues" section after the Schema vs implementation differences table. Each entry follows the format: Item | Safe interpretation | Recommended action.

#### 2.1 ack-only offset vs disconnect offset write mismatch (require 10)

| Item | Safe interpretation | Recommended action |
|---|---|---|
| ack-only offset writes only on consumer disconnect — not on every ack — creates a gap where an unacked event may be lost if the consumer crashes before disconnect | The offset is written lazily on disconnect, not eagerly on each ack. If the consumer crashes without a clean disconnect, the last offset is not persisted and the next consumer will redeliver events from the previous ack point. This is by design for at-least-once semantics but means event loss during crash scenarios is possible. | Document the crash-recovery semantics explicitly. Consider whether an ack-based offset write (on every ack) is needed for consumers that need exactly-once guarantees. |

#### 2.2 Missing ack endpoint documentation (require 9)

| Item | Safe interpretation | Recommended action |
|---|---|---|
| The `/ack` endpoint exists in the implementation but has no documentation entry in the API reference or HTTP API docs | The ack endpoint is a real runtime feature that consumers use to confirm delivery. Its absence from docs means operators have no way to discover it through documentation. | Add `/ack` endpoint documentation to the HTTP API doc (06_eventbus_02_http_api_and_runtime.md) and reference API doc (06_eventbus_06_reference_api.md). |

#### 2.3 DLQ requeue path mismatch — delivery_failure_count vs retry_count (require 7)

| Item | Safe interpretation | Recommended action |
|---|---|---|
| The DLQ requeue logic references `retry_count` in comments/docs but the actual schema column is `delivery_failure_count`. The DLQ requeue path increments `delivery_failure_count` and uses it to determine if an event should be requeued or permanently dead-lettered. | The DLQ requeue path is functionally correct — it reads/writes `delivery_failure_count` from the schema. The mismatch is purely a documentation terminology issue. Safe interpretation: the DLQ logic works as designed; only the doc comment is stale. | Update DLQ requeue comments and docs to use `delivery_failure_count` consistently. |

#### 2.4 Consumer ID stability ambiguity — PID in consumer ID generation (require 11)

| Item | Safe interpretation | Recommended action |
|---|---|---|
| The consumer ID generation includes the process PID, which changes on restart. This means a consumer that is restarted will get a new ID and be treated as a new consumer rather than reconnecting to its existing subscription. | The PID-based consumer ID is intentional for uniqueness but has an operational consequence: restarts create duplicate consumers. The EventBus does not have a mechanism to detect and merge duplicate consumers. | Document the consumer ID generation algorithm and its implications. Consider whether a stable identifier (e.g., configured name) should be added alongside the PID for better consumer identity management. |

#### 2.5 Host config ownership mismatch — TOML vs uvicorn CLI (require 8)

| Item | Safe interpretation | Recommended action |
|---|---|---|
| The TOML config has a `host` field but the uvicorn startup command uses `--host` CLI flag. If both are set, the CLI flag takes precedence, creating ambiguity about which is the source of truth. | The uvicorn `--host` flag overrides the TOML `host` value because it is passed as a runtime argument after config loading. The TOML `host` field is effectively ignored when the CLI flag is present. | Document the precedence rule (CLI flag > TOML) explicitly in the config/ops doc. Consider removing `host` from TOML if it is never used as the authoritative source. |

#### 2.6 SQLite thread-safety confirmation (require 6)

| Item | Safe interpretation | Recommended action |
|---|---|---|
| The EventBus uses SQLite with WAL mode for concurrent read/write access. It is unclear whether the current connection pooling and transaction handling is sufficient for the expected concurrency levels. | SQLite WAL mode supports concurrent readers and a single writer, which matches the EventBus pattern. However, connection pooling configuration (max_connections, timeout) has not been validated against the expected load. Safe interpretation: the architecture is sound but operational validation is needed. | Validate with load testing at expected concurrency levels. Document the assumed max concurrency and connection pool settings. |

#### 2.7 DLQ retry_count semantics — delivery_failure_count ownership (require 5)

| Item | Safe interpretation | Recommended action |
|---|---|---|
| The DLQ `delivery_failure_count` is incremented by the EventBus when moving events to the DLQ, but there is no documentation of who is responsible for resetting it when an event is requeued from the DLQ. | The `delivery_failure_count` is reset when an event is requeued from the DLQ back to the main queue. This is a reasonable design — each DLQ cycle resets the counter, allowing events to be retried multiple times across DLQ cycles. Safe interpretation: the behavior is correct but undocumented. | Document the DLQ requeue lifecycle including `delivery_failure_count` reset behavior. |

#### 2.8 Startup safety guard for public bind (require 4)

| Item | Safe interpretation | Recommended action |
|---|---|---|
| The EventBus binds to a public network interface by default without a startup guard or configuration check. This means it may be accessible on all network interfaces during development or container deployment. | The default bind is `0.0.0.0` (all interfaces). There is no startup validation that checks whether the host should be restricted. Safe interpretation: the EventBus will be publicly accessible unless the operator explicitly configures a specific host. | Add a startup guard that warns or errors if the host is `0.0.0.0` in non-development environments. Document the bind behavior clearly. |

#### 2.9 Deprecated config fields (poll_interval_ms, offset_checkpoint_interval) (require 3)

| Item | Safe interpretation | Recommended action |
|---|---|---|
| The TOML config still contains `poll_interval_ms` and `offset_checkpoint_interval` fields that are no-op (deprecated). These fields have no runtime effect but remain in the example config. | Both fields are deprecated and no-op: `poll_interval_ms` because subscribe delivery switched to push-mode, and `offset_checkpoint_interval` because offset checkpointing was replaced with ack-only model. They are retained for backward compatibility with existing configs. Safe interpretation: these fields can be safely ignored by operators; they have no effect on runtime behavior. | Remove from the active TOML config example (config/eventbus.toml). Add deprecation warnings when non-default values are set (requires code change in config.py). Document as deprecated in the config reference API doc. |

### Phase 3: Add resolved items from previous requires

**Target file**: `docs/06_eventbus_90_inconsistencies_and_known_issues.md`

Update the Resolved Items section to include all items resolved by previous require processing.

| Item | Resolution |
|---|---|
| `/subscribe` polling vs push documentation mismatch | **Resolved** — removed from Schema vs implementation differences table; /subscribe uses hybrid model (replay from SQLite + live EventBroker push). See require 1. |
| Consumer ID collision possibility | **Resolved** — hash-based stable IDs with collision detection. See require 11. |
| `/health` HTTP status on degraded state (200 vs 503) | **Resolved** — now returns HTTP 503 for non-ok states (fail-closed). See require 6. |
| SQLite/JSONL dual read path | **Resolved** — SQLite-only reads; JSONL is write-only. See require 1. |

### Phase 4: Add needs-confirmation items

**Target file**: `docs/06_eventbus_90_inconsistencies_and_known_issues.md`

Update the Unconfirmed items section. The FastAPI thread pool worker usage item remains unresolved.

| Item | How to confirm |
|---|---|
| FastAPI thread pool worker usage | Confirm from startup configuration — check whether uvicorn is configured with explicit worker count or relies on FastAPI default (1 worker). This affects concurrency behavior for SSE connections. |

### Phase 5: Format and structure

**Target file**: `docs/06_eventbus_90_inconsistencies_and_known_issues.md`

Restructure the document into the following sections in order:
1. Schema vs implementation differences (with only current stale entries, no resolved ones)
2. Active Issues (new section — all items from Phase 2)
3. Resolved Items (updated with all resolved items from Phases 1 and 3)
4. Unconfirmed items (updated with any remaining items from Phase 4)

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `06_eventbus_90_inconsistencies_and_known_issues.md` | Verify retry_count removed and delivery_failure_count present | `grep -n "retry_count\|delivery_failure_count" docs/06_eventbus_90_inconsistencies_and_known_issues.md` | No `retry_count` references; `delivery_failure_count` present in schema table |
| `06_eventbus_90_inconsistencies_and_known_issues.md` | Verify polling-based /subscribe removed | `grep -n "Polling-based\|polling" docs/06_eventbus_90_inconsistencies_and_known_issues.md` | No matches for "Polling-based" or "polling" in the doc |
| `06_eventbus_90_inconsistencies_and_known_issues.md` | Verify all 9 active issues present | Check for presence of each issue title/keyword in Active Issues section | All 9 items from Phase 2 documented |
| `06_eventbus_90_inconsistencies_and_known_issues.md` | Verify all 4 resolved items present | Check for presence of each resolved item in Resolved Items section | All 4 items from Phase 3 documented |
| `06_eventbus_90_inconsistencies_and_known_issues.md` | Verify document structure is correct | Manual review of section ordering and format consistency | Sections in order: Schema → Active → Resolved → Unconfirmed; each entry has consistent format |

## Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| Adding too many items may make the known-issues doc unwieldy | Low | Group related items by category within sections. Keep each entry concise with clear safe interpretation and recommended action. |
| Marking items as resolved may be premature if underlying implementation hasn't been fixed yet | Medium | Only mark as resolved if the documentation has been corrected to match runtime behavior. Do not mark implementation changes as resolved unless they've been verified. In this case, resolved items are doc corrections that have already been applied in previous requires. |
| Missing an active issue that was discovered in a require but not captured in the plan | Low | Cross-reference against all 10 require files during the update. The plan lists 9 active items — verify each against the original requires before completing. |
