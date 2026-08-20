# Implementation Procedure: Add NACK-Side Transition Rows to Nack-Health-DLQ Doc

## Goal
Extend `docs/06_eventbus_02_03_nack-health-dlq.md` with NACK-side rows of the ACK/NACK transition table (first NACK, duplicate NACK, NACK-after-ACK, unknown event ID) under the existing `POST /nack` section, explicitly stating `nack_event`'s lack of idempotency.

## Scope
- Target file: `docs/06_eventbus_02_03_nack-health-dlq.md`
- Add NACK-side transition rows to the existing `POST /nack` section
- Explicitly state `nack_event`'s lack of idempotency
- Cross-reference ACK-side rows in `docs/06_eventbus_02_02_subscribe-ack.md`

## Assumptions
- The current code behavior (as verified in `scripts/eventbus/db.py`, `ack_route.py`) is the ground truth
- The `run_with_db_lock` serializes concurrent ACK/NACK operations
- Classification of non-idempotent NACK as "Implementation fix required" per `rules/coding.md`

## Design decisions
- Place the NACK-side rows directly under the existing `POST /nack` section
- Use the same table format as the ACK-side table in the subscribe-ack doc
- Explicitly label duplicate NACK and NACK-after-ACK as "Implementation fix required"

## Alternatives considered
- Create a separate transition table section: Rejected — integrating with existing `POST /nack` section keeps context together
- Omit "Implementation fix required" classification: Rejected — per `rules/coding.md` must classify honestly

## Implementation
### Target file
`docs/06_eventbus_02_03_nack-health-dlq.md`

### Procedure
1. Read the current file content
2. Add NACK-side transition rows after the existing `POST /nack` section (around line 31)
3. Add cross-reference to ACK-side rows in `docs/06_eventbus_02_02_subscribe-ack.md`

### Method
Direct Markdown editing with exact section placement

### Details
**NACK-Side Transition Rows (to add under `POST /nack` section):**

| Scenario | Current code behavior | HTTP status | Response body | Persistence side effect |
|---|---|---|---|---|
| First NACK | `nack_event` increments `delivery_failure_count` from 0 to 1 (or higher) | 200 | `{event_id, delivery_failure_count}` | Increments `delivery_failure_count`; promotes to DLQ if `>= max_retry` |
| Duplicate NACK | `nack_event` has no idempotency guard; every call increments `delivery_failure_count` again | 200 | `{event_id, delivery_failure_count}` | Counter keeps incrementing; DLQ promotion can trigger on later duplicate call — **Implementation fix required** |
| NACK after ACK | `nack_event` has no `acked_at` check | 200 | `{event_id, delivery_failure_count}` | NACK "succeeds" (increments `delivery_failure_count`) even though already acked — **Implementation fix required** |
| Unknown event ID (NACK) | `nack_event` returns `-1` | 404 | `ERR_EVENT_NOT_FOUND` | None |

**Cross-reference note to add:**
> See `docs/06_eventbus_02_02_subscribe-ack.md` for the ACK-side transition rows (first ACK, duplicate ACK, ACK-after-NACK, unknown event ID ACK, concurrent ACK/NACK, consumer mismatch).

## Compatibility considerations
- Documentation-only change, no code impact
- Cross-references to ACK-side rows must be maintained

## Security considerations
- None — documentation only

## Rollback considerations
- Git revert of this file if issues arise

## Validation plan
- Manual review: all 4 NACK-side scenarios present with correct status/body/side-effect
- `git diff` + re-read `ack_route.py` to verify behavior matches code
- Cross-reference to subscribe-ack doc resolves correctly

## Out of scope
- Changes to `scripts/eventbus/` code (Global Rule 8)
- Changes to other `06_eventbus_*.md` files not listed in the plan

## Traceability
- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: requires/done/20260818-220838_require.md
- Source plan: plans/20260819-173619_plan.md
- Source implementation procedure: N/A
- Generated at: 20260820-133400
- Related target files: docs/06_eventbus_02_03_nack-health-dlq.md