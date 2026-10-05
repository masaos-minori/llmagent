# Implementation Procedure: Update `eventbus_03_dlq_operations.md` — NACK response and ACK/NACK transition table

## Goal

State the final behavior for ACK followed by NACK (same consumer) and remove the pointer to the source Issue. REQ-007.

## Scope

Update the NACK response paragraph and the "ACK followed by NACK (same consumer)" table row in `docs/24_eventbus/eventbus_03_dlq_operations.md`.

## Assumptions

- The final behavior is: a NACK from a consumer that has already ACKed the event is rejected with HTTP 409 `event already acknowledged`.
- The source Issue path `issues/20261005-102244_eb002_eventbus-nack-accepted-after-per-consumer-ack.md` will be archived to `issues/done/` by this workflow.

## Design decisions

- Update the NACK response paragraph to state the 409 `event already acknowledged` case covering the per-consumer ACK.
- Update the "ACK followed by NACK (same consumer)" table row to reflect the final behavior.
- Remove the pointer to the source Issue from both locations.

## Alternatives considered

- Keeping the pointer to the source Issue: would leave stale references after the Issue is archived.

## Implementation

### Target file

`docs/24_eventbus/eventbus_03_dlq_operations.md`

### Procedure

1. Update the NACK response paragraph (line 132) to describe the 409 `event already acknowledged` case covering the per-consumer ACK.
2. Update the "ACK followed by NACK (same consumer)" table row (line 149) to reflect the final behavior.
3. Remove the pointer to the source Issue from both locations.

### Method

#### Change 1: NACK response paragraph (line 132)

Current text:
```
A 409 error indicates the event is already in the DLQ, or has `events.acked_at` set. A consumer's own ACK does not set `events.acked_at`, so a NACK sent by a consumer after its own ACK is currently accepted; this is tracked in `issues/20261005-102244_eb002_eventbus-nack-accepted-after-per-consumer-ack.md`.
```

Replace with:
```
A 409 error indicates the event is already in the DLQ, has `events.acked_at` set, or the requesting consumer has already ACKed the event.
```

#### Change 2: ACK followed by NACK (same consumer) table row (line 149)

Current text:
```
| ACK followed by NACK (same consumer) | `nack_event` checks only `events.acked_at` and `events.dlq_at`; the per-consumer ACK sets neither | 200 | `{event_id, delivery_failure_count}` | NACK succeeds and `delivery_failure_count` increases; tracked in `issues/20261005-102244_eb002_eventbus-nack-accepted-after-per-consumer-ack.md` | **Known Issue: Implementation fix required** |
```

Replace with:
```
| ACK followed by NACK (same consumer) | `nack_event` rejects when the requesting consumer has already ACKed the event | 409 | `event already acknowledged` | Counters unchanged | — |
```

### Details

- Current NACK response paragraph cites the source Issue (`grep` of the Issue file name).
- Current "ACK followed by NACK (same consumer)" table row cites the source Issue and marks it as "Known Issue: Implementation fix required".
- After the implementation, the NACK is rejected with HTTP 409 `event already acknowledged` and counters are unchanged.

## Compatibility considerations

- This is a documentation-only change; no behavioral impact.
- The updated text reflects the final behavior after the code changes.

## Security considerations

- Documentation change only; no security impact.

## Rollback considerations

- Revert the two text changes to restore the original documentation.

## Validation plan

- Run docs checkers named in `routing.md` Tools:
  - `uv run python tools/check_docs_quality.py`
  - `uv run python tools/check_docs_structure.py docs/24_eventbus/eventbus_03_dlq_operations.md`
  - `uv run python tools/check_docs_content_policy.py`
- Confirm no stale pointers to the source Issue remain.

## Completion criteria

- The NACK response paragraph states the 409 `event already acknowledged` case covering the per-consumer ACK.
- The "ACK followed by NACK (same consumer)" table row reflects the final behavior.
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
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261005-164838 | 20261005-164838 |  |
| 2 | Add or update tests per Validation plan | Completed | 20261005-164838 | 20261005-164838 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261005-164838 | 20261005-164838 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261005-164838 | 20261005-164838 |  |

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
- **Related target files**: docs/24_eventbus/eventbus_03_dlq_operations.md