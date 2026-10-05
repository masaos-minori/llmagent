# Implementation Procedure: Update `eventbus_06_dlq_offsets_and_delivery_semantics.md` — Prohibited transitions and NACK semantics

## Goal

State that a NACK after the same consumer's ACK is rejected with 409 and remove the pointer to the source Issue. REQ-007.

## Scope

Update the prohibited-transitions section and the `nack_event` events-level-only description in `docs/24_eventbus/eventbus_06_dlq_offsets_and_delivery_semantics.md`.

## Assumptions

- The final behavior is: a NACK from a consumer that has already ACKed the event is rejected with HTTP 409 `event already acknowledged`.
- The source Issue path `issues/20261005-102244_eb002_eventbus-nack-accepted-after-per-consumer-ack.md` will be archived to `issues/done/` by this workflow.

## Design decisions

- Update the "ACK followed by NACK" passage to reflect the final behavior.
- Update the prohibited transitions section to reflect the final behavior.
- Remove the pointer to the source Issue from both locations.

## Alternatives considered

- Keeping the pointer to the source Issue: would leave stale references after the Issue is archived.

## Implementation

### Target file

`docs/24_eventbus/eventbus_06_dlq_offsets_and_delivery_semantics.md`

### Procedure

1. Update the "ACK followed by NACK" passage (line 109) to reflect the final behavior.
2. Update the prohibited transitions section (line 271) to reflect the final behavior.
3. Remove the pointer to the source Issue from both locations.

### Method

#### Change 1: ACK followed by NACK passage (line 109)

Current text:
```
`nack_event` checks only `events.acked_at` and `events.dlq_at`, and the per-consumer ACK sets neither, so a NACK from a consumer that has already ACKed the event succeeds and `delivery_failure_count` increases — **Implementation fix required**, tracked in `issues/20261005-102244_eb002_eventbus-nack-accepted-after-per-consumer-ack.md`.
```

Replace with:
```
A NACK from a consumer that has already ACKed the event is rejected with HTTP 409 `event already acknowledged`; counters are unchanged.
```

#### Change 2: Prohibited transitions section (line 271)

Current text:
```
ACKed ✗ NACK → HTTP 409 "event already acknowledged" (applies when `events.acked_at` is set; a NACK after the same consumer's own ACK is not yet rejected, see `issues/20261005-102244_eb002_eventbus-nack-accepted-after-per-consumer-ack.md`)
```

Replace with:
```
ACKed ✗ NACK → HTTP 409 "event already acknowledged" (applies when either `events.acked_at` is set or the requesting consumer has already ACKed the event)
```

### Details

- Current "ACK followed by NACK" passage cites the source Issue and marks it as "Implementation fix required".
- Current prohibited transitions section cites the source Issue with a caveat about the per-consumer ACK not being rejected.
- After the implementation, both passages reflect the final behavior.

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
  - `uv run python tools/check_docs_structure.py docs/24_eventbus/eventbus_06_dlq_offsets_and_delivery_semantics.md`
  - `uv run python tools/check_docs_content_policy.py`
- Confirm no stale pointers to the source Issue remain.

## Completion criteria

- The "ACK followed by NACK" passage states the final behavior.
- The prohibited transitions section reflects the final behavior.
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
- **Related target files**: docs/24_eventbus/eventbus_06_dlq_offsets_and_delivery_semantics.md