# Implementation Procedure: Update `eventbus_15_ack_nack_endpoints.md` — NACK conflict responses

## Goal

Describe the 409 `event already acknowledged` as covering the per-consumer ACK and remove the pointer to the source Issue. REQ-007.

## Scope

Update the Conflict Responses section in `docs/24_eventbus/eventbus_15_ack_nack_endpoints.md`.

## Assumptions

- The final behavior is: a NACK from a consumer that has already ACKed the event is rejected with HTTP 409 `event already acknowledged`.
- The source Issue path `issues/20261005-102244_eb002_eventbus-nack-accepted-after-per-consumer-ack.md` will be archived to `issues/done/` by this workflow.

## Design decisions

- Update the Conflict Responses paragraph to state the 409 `event already acknowledged` case covering the per-consumer ACK.
- Remove the pointer to the source Issue.

## Alternatives considered

- Keeping the pointer to the source Issue: would leave stale references after the Issue is archived.

## Implementation

### Target file

`docs/24_eventbus/eventbus_15_ack_nack_endpoints.md`

### Procedure

1. Update the Conflict Responses paragraph (line 191) to describe the 409 `event already acknowledged` case covering the per-consumer ACK.
2. Remove the pointer to the source Issue.

### Method

#### Change: Conflict Responses paragraph (line 191)

Current text:
```
Returned when the event has `events.acked_at` set or is already in the DLQ. A NACK from a consumer after its own ACK is not currently rejected because the per-consumer ACK does not set `events.acked_at`; this is tracked in `issues/20261005-102244_eb002_eventbus-nack-accepted-after-per-consumer-ack.md`.
```

Replace with:
```
Returned when the event has `events.acked_at` set, is already in the DLQ, or the requesting consumer has already ACKed the event.
```

### Details

- Current Conflict Responses paragraph cites the source Issue.
- After the implementation, the 409 `event already acknowledged` covers the per-consumer ACK case.

## Compatibility considerations

- This is a documentation-only change; no behavioral impact.
- The updated text reflects the final behavior after the code changes.

## Security considerations

- Documentation change only; no security impact.

## Rollback considerations

- Revert the text change to restore the original documentation.

## Validation plan

- Run docs checkers named in `routing.md` Tools:
  - `uv run python tools/check_docs_quality.py`
  - `uv run python tools/check_docs_structure.py docs/24_eventbus/eventbus_15_ack_nack_endpoints.md`
  - `uv run python tools/check_docs_content_policy.py`
- Confirm no stale pointers to the source Issue remain.

## Completion criteria

- The Conflict Responses paragraph states the 409 `event already acknowledged` case covering the per-consumer ACK.
- No reference to the source Issue remains in this document.
- Docs checkers pass with no findings.

## Out of scope

- Modifying `nack_event()` in delivery_repo.py (handled in a separate procedure document).
- Modifying the `nack` route in ack_route.py (handled in a separate procedure document).
- Adding regression tests (handled in a separate procedure document).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Source issue**: issues/20261005-102244_eb002_eventbus-nack-accepted-after-per-consumer-ack.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261005-103619_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261005-155308
- **Related target files**: docs/24_eventbus/eventbus_15_ack_nack_endpoints.md
