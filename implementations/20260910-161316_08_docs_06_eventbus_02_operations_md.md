## Goal

Update `docs/06_eventbus_02_operations.md` to replace the "Queue Overflow: ... the event is discarded (only a WARNING is logged)" statement with the finalized disconnect-on-overflow policy and document the new HTTP 409 duplicate-connection response, per REQ-007.

## Scope

- Replace the existing "Queue Overflow" paragraph under the `/subscribe` endpoint.
- Add documentation for the HTTP 409 duplicate-connection response.
- Update the "Failure Behavior Summary" table row for "Subscriber queue full".

## Assumptions

- The Plan's architecture (disconnect-on-overflow + consumer-connection rejection) is approved.
- The doc's existing content about publish, subscribe, ack/nack, health, and DLQ is still accurate.

## Design decisions

- **Preserve existing content**: Only update sections relevant to the new policies; do not rewrite the entire doc.
- **Clarify the gap being fixed**: Explicitly describe the disconnect-on-overflow mechanism and its effect on the SSE stream.
- **Document the HTTP 409 response**: Describe the conditions under which a duplicate-connection rejection occurs and the expected response body.

## Alternatives considered

- **Rewrite the entire doc**: Would be more thorough but too disruptive for a focused change.
- **Create a new doc**: Would fragment the architectural history across multiple documents.

## Implementation

### Target file

`docs/06_eventbus_02_operations.md`

### Procedure

1. Replace the existing "Queue Overflow" paragraph under the `/subscribe` endpoint.
2. Add documentation for the HTTP 409 duplicate-connection response.
3. Update the "Failure Behavior Summary" table row for "Subscriber queue full".

### Method

#### Step 1: Replace Queue Overflow paragraph

Change line 73:
```markdown
**Queue Overflow**: If the consumer is slow and the queue becomes full, the event is discarded (only a WARNING is logged). Use `since_seq`/`GET /replay` for recovery.
```

to:
```markdown
**Queue Overflow**: If the consumer is slow and the subscriber's queue becomes full, the subscription is disconnected (SSE stream ends) instead of silently dropping the event. The client can reconnect using `since_seq`/`GET /replay` to resume from its last acknowledged position.
```

#### Step 2: Add HTTP 409 duplicate-connection response documentation

Add after the existing "Handling Unknown/Mismatched Consumers" subsection (after line 93):
```markdown
### Duplicate Consumer Connection Rejection

When a non-empty `consumer_id` is specified, only one active connection is allowed per consumer ID. A second concurrent attempt to connect with the same `consumer_id` receives HTTP 409 (Conflict) with a response body containing the message `"duplicate consumer_id: X"` where `X` is the rejected consumer ID.

This policy implements ADR-006 INV-10 ("同一Consumer IDの並行使用を禁止する") and INV-11 ("Consumer ID衝突を検出する"), rejecting Alternative C ("no consumer ID conflict detection"). Anonymous connections (empty `consumer_id`) are exempt from this restriction.
```

#### Step 3: Update Failure Behavior Summary table

Change line 188:
```markdown
| Subscriber queue full | Event is silently discarded, WARNING log output |
```

to:
```markdown
| Subscriber queue full | Subscription disconnected (SSE stream ends), WARNING log output |
```

### Details

The key changes are:

1. **Queue Overflow description**: Replaced the "silently dropped" language with "subscription is disconnected (SSE stream ends)" to reflect the new disconnect-on-overflow behavior.

2. **HTTP 409 documentation**: Added a new subsection describing the duplicate-connection rejection policy, including the HTTP status code, response body format, and the ADR-006 invariants it implements.

3. **Failure Behavior Summary**: Updated the "Subscriber queue full" row to reflect that the subscription is disconnected rather than the event being silently discarded.

## Compatibility considerations

- The doc's existing content about publish, subscribe, ack/nack, health, and DLQ is preserved.
- The new content is additive — it does not rewrite or remove existing sections.
- The "since_seq"/Offset Precedence Rules section is unchanged — no new rules needed.

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
| `docs/06_eventbus_02_operations.md` | Structural verification | Read file, confirm new sections present | Queue Overflow updated; HTTP 409 documented; Failure Behavior Summary updated |

## Completion criteria

- Queue Overflow paragraph reflects disconnect-on-overflow policy.
- HTTP 409 duplicate-connection response is documented.
- Failure Behavior Summary row for "Subscriber queue full" is updated.
- ADR-006 INV-10/INV-11 reference is included.

## Out of scope

- Modifying the doc's existing content about publish, subscribe, ack/nack, health, and DLQ — not affected by this change.
- Adding DDL to schema files — covered by separate procedure documents.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Replace Queue Overflow paragraph | Completed | — | — | |
| 2 | Add HTTP 409 documentation | Completed | — | — | |
| 3 | Update Failure Behavior Summary | Completed | — | — | |

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
- **Related target files**: docs/06_eventbus_02_operations.md
