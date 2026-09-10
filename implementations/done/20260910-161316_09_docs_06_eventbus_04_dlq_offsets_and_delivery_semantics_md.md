## Goal

Update `docs/06_eventbus_04_dlq_offsets_and_delivery_semantics.md` to replace the "If different clients use the same `consumer_id`, the last write wins... This is an intentional design choice" statement with the finalized one-connection-per-`consumer_id` policy, per REQ-007.

## Scope

- Replace the existing "Consumer ID Collision Risk" section.
- Add documentation for the disconnect-on-overflow mechanism.
- Update the "Delivery Guarantees" section to reflect the new reliability guarantees.

## Assumptions

- The Plan's architecture (disconnect-on-overflow + consumer-connection rejection) is approved.
- The doc's existing content about DLQ, offsets, and delivery semantics is still accurate.

## Design decisions

- **Preserve existing content**: Only update sections relevant to the new policies; do not rewrite the entire doc.
- **Clarify the gap being fixed**: Explicitly describe the one-connection-per-`consumer_id` policy and its effect on collision risk.
- **Document the disconnect-on-overflow mechanism**: Describe how overflow-triggered disconnections affect delivery guarantees.

## Alternatives considered

- **Rewrite the entire doc**: Would be more thorough but too disruptive for a focused change.
- **Create a new doc**: Would fragment the architectural history across multiple documents.

## Implementation

### Target file

`docs/06_eventbus_04_dlq_offsets_and_delivery_semantics.md`

### Procedure

1. Replace the existing "Consumer ID Collision Risk" section.
2. Add documentation for the disconnect-on-overflow mechanism.
3. Update the "Delivery Guarantees" section to reflect the new reliability guarantees.

### Method

#### Step 1: Replace Consumer ID Collision Risk section

Change lines 60-62:
```markdown
## Consumer ID Collision Risk

If different clients use the same `consumer_id`, the last write wins and the offset is overwritten. This is an intentional design choice but can lead to offset inconsistencies due to collisions.
```

to:
```markdown
## Consumer ID Collision Risk

With the one-connection-per-`consumer_id` policy, the collision scenario described above no longer applies. A second client attempting to connect with the same non-empty `consumer_id` receives HTTP 409 (Conflict), preventing concurrent connections and eliminating the "last write wins" offset overwrite risk. Anonymous connections (empty `consumer_id`) are exempt from this restriction.
```

#### Step 2: Add disconnect-on-overflow documentation

Add after the "Delivery Guarantees" section (after line 58):
```markdown
## Overflow Disconnection

When a subscriber's queue becomes full, the subscription is disconnected (SSE stream ends) instead of silently dropping the event. The client can reconnect using `since_seq`/`GET /replay` to resume from its last acknowledged position. This ensures that slow consumers never create undetected permanent gaps — the server terminates the affected subscription so the client can recover via reconnection.
```

#### Step 3: Update Delivery Guarantees section

Change lines 54-58:
```markdown
## Delivery Guarantees

At-least-once. Duplicate publishing is suppressed by the `event_id` UNIQUE constraint. Redelivery after crashes may occur. Ordering is guaranteed per topic.

**IMPORTANT:** Consumers MUST implement idempotent processing. Since multiple deliveries of the same event can occur, duplicate ACKs or duplicate processing for the same `event_id` must be safe.
```

to:
```markdown
## Delivery Guarantees

At-least-once. Duplicate publishing is suppressed by the `event_id` UNIQUE constraint. Redelivery after crashes may occur. Ordering is guaranteed per topic.

**IMPORTANT:** Consumers MUST implement idempotent processing. Since multiple deliveries of the same event can occur, duplicate ACKs or duplicate processing for the same `event_id` must be safe.

**Overflow guarantee:** When a subscriber's queue overflows, the subscription is disconnected rather than silently continuing. This prevents permanent event loss — the client can reconnect and resume from its last committed offset.
```

### Details

The key changes are:

1. **Consumer ID Collision Risk**: Replaced the "last write wins" language with the one-connection-per-`consumer_id` policy, explaining that the collision scenario no longer applies.

2. **Overflow Disconnection**: Added a new section describing the disconnect-on-overflow mechanism and its effect on delivery guarantees.

3. **Delivery Guarantees**: Updated the section to include the overflow guarantee — when a subscriber's queue overflows, the subscription is disconnected rather than silently continuing.

## Compatibility considerations

- The doc's existing content about DLQ, offsets, and delivery semantics is preserved.
- The new content is additive — it does not rewrite or remove existing sections.
- The "Consumer Offset" section is unchanged — no new rules needed.

## Security considerations

- No new authentication or authorization boundaries introduced.
- Table/column naming follows existing conventions.
- No user input flows directly into DDL generation — schema changes are code-only.

## Rollback considerations

- To rollback: revert the doc to its previous version.
- The rollback restores the pre-change architectural description.

## Validation plan

| Target | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `docs/06_eventbus_04_dlq_offsets_and_delivery_semantics.md` | Structural verification | Read file, confirm new sections present | Consumer ID Collision Risk updated; Overflow Disconnection added; Delivery Guarantees updated |

## Completion criteria

- Consumer ID Collision Risk reflects one-connection-per-`consumer_id` policy.
- Overflow Disconnection section is added.
- Delivery Guarantees includes the overflow guarantee.
- ADR-006 INV-10/INV-11 reference is included.

## Out of scope

- Modifying the doc's existing content about DLQ, offsets, and delivery semantics — not affected by this change.
- Adding DDL to schema files — covered by separate procedure documents.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Replace Consumer ID Collision Risk section | Completed | — | — | One-connection-per-consumer policy documented |
| 2 | Add Overflow Disconnection section | Completed | — | — | Overflow disconnection mechanism documented |
| 3 | Update Delivery Guarantees section | Completed | — | — | Overflow guarantee added |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability

- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-007
- **Source issue**: issues/20260907-125042_eb_h02_backpressure_duplicate_consumer_connection.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260909-095501_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260910-161316
- **Related target files**: docs/06_eventbus_04_dlq_offsets_and_delivery_semantics.md
