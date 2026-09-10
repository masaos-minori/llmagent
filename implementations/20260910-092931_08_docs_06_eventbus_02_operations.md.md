## Goal
Replace the "Queue Overflow: ... the event is discarded (only a WARNING is logged)"
statement with the finalized disconnect-on-overflow policy; document the new HTTP 409
duplicate-connection response (REQ-007; Documentation Impact).

## Scope
In scope: the "Queue Overflow" bullet under "## GET /subscribe" (line ~73) and the
"Subscriber queue full" row of the "## Failure Behavior Summary" table (line ~188).
Out of scope: "POST /publish", "GET /replay", "POST /events/{event_id}/ack", "POST
/nack", "GET /health", "GET /dlq", "POST /dlq/{event_id}/requeue", "DLQ Background
Loop" sections — unrelated to this Plan.

## Assumptions
- Both locations describing today's silent-discard behavior must be updated together —
  leaving one stale while updating the other would reintroduce the exact
  doc-vs-code contradiction this Plan closes.

## Design decisions
Replace "Queue Overflow: If the consumer is slow and the queue becomes full, the event
is discarded (only a WARNING is logged). Use `since_seq`/`GET /replay` for recovery."
with a statement that an overflowing subscriber's SSE connection is disconnected
(not silently continued past the gap), and the client must reconnect using its last
committed `consumer_id`/offset via `since_seq`/`GET /replay` — the client-facing
recovery mechanism (`since_seq`/replay) is unchanged, only the trigger changes from
"silent drop, keep going" to "disconnect, client reconnects". Update the "Subscriber
queue full" failure-summary row from "Event is silently discarded, WARNING log output"
to describe the disconnect. Also document the new HTTP 409 response under "## GET
/subscribe": a second concurrent connection with the same non-empty `consumer_id`
receives 409.

## Alternatives considered
Adding an entirely new "## Duplicate Consumer Connections" heading was considered;
adding the 409 documentation as a subsection under the existing "## GET /subscribe"
heading is preferred, since 409 is a `/subscribe`-specific response, consistent with
how this document already organizes per-endpoint behavior under its endpoint headings.

## Implementation
### Target file
`docs/06_eventbus_02_operations.md`

### Procedure
1. Under "## GET /subscribe", replace the "Queue Overflow" bullet's text to describe
   disconnect-on-overflow instead of silent-discard.
2. Under the same heading, add a short subsection or bullet documenting the new HTTP
   409 duplicate-`consumer_id` response.
3. Update the "Subscriber queue full" row in "## Failure Behavior Summary" to match
   the new bullet's description.

### Method
Prose edit within existing sections; no restructuring of the document's per-endpoint
heading organization.

### Details
Example replacement (adapt wording to match surrounding document style — normative,
short sentences per `skills/DESIGN.md` Output language):
- Before: "**Queue Overflow**: If the consumer is slow and the queue becomes full, the
  event is discarded (only a WARNING is logged). Use `since_seq`/`GET /replay` for
  recovery."
- After: state that an overflowing subscriber's SSE connection is disconnected by the
  server; the client must reconnect (using the same `consumer_id`) to resume from its
  last committed offset via `since_seq`/replay, since no further events are delivered
  on the disconnected connection.

Add: state that a second concurrent `/subscribe` connection using the same non-empty
`consumer_id` as an already-active connection receives HTTP 409, and that the first
connection remains unaffected.

Update the "Subscriber queue full" failure-summary row from "Event is silently
discarded, WARNING log output" to describe the disconnect (e.g. "Subscriber
disconnected; client must reconnect using its last committed offset").

## Compatibility considerations
This document must remain consistent with row 09 (the DLQ/offsets doc's "Consumer ID
Collision Risk" section) and the sibling Plan's rows 12-14 (ADR-006 and the DB
architecture doc) — none should describe silent-discard or last-write-wins as current
behavior once both Plans land.

## Security considerations
N/A: documentation only.

## Rollback considerations
Revert this file's diff; no other document's correctness depends on this file's exact
wording beyond the cross-reference consistency noted above.

## Validation plan
- `uv run python tools/check_docs_quality.py docs/06_eventbus_02_operations.md`
- `uv run python tools/check_docs_structure.py docs/06_eventbus_02_operations.md`
- `uv run python tools/check_docs_consistency.py --domain overview`

## Completion criteria
"Queue Overflow" and "Failure Behavior Summary" describe disconnect-on-overflow as
current behavior; "GET /subscribe" documents the HTTP 409 duplicate-connection
response — no remaining text describes silent-discard as current, accepted behavior.

## Out of scope
Any other endpoint section in this document.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Replace "Queue Overflow" bullet with disconnect-on-overflow description | Pending | — | — | |
| 2 | Add HTTP 409 duplicate-connection documentation under GET /subscribe | Pending | — | — | |
| 3 | Update "Subscriber queue full" row in Failure Behavior Summary | Pending | — | — | |
| 4 | Run `check_docs_quality.py`/`check_docs_structure.py`/`check_docs_consistency.py` | Pending | — | — | |

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
- **Generated at**: 20260910-092931
- **Related target files**: docs/06_eventbus_02_operations.md
