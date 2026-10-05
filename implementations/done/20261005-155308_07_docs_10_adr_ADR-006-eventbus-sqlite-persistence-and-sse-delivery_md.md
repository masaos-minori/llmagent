# Implementation Procedure: Update ADR-006 Known Deviations bullet EVENTBUS-011

## Goal

Remove the pointer to the source Issue and keep the bullet consistent with the final NACK behavior; no Decision text changes. REQ-007.

## Scope

Update the EVENTBUS-011 Known Deviations bullet in `docs/10_adr/ADR-006-eventbus-sqlite-persistence-and-sse-delivery.md`.

## Assumptions

- The final behavior is: a NACK from a consumer that has already ACKed the event is rejected with HTTP 409 `event already acknowledged`.
- The source Issue path `issues/20261005-102244_eb002_eventbus-nack-accepted-after-per-consumer-ack.md` will be archived to `issues/done/` by this workflow.
- Only the stale pointer needs removal; the EVENTBUS-011 bullet's other claims (the race condition on 409) remain valid.

## Design decisions

- Remove the pointer to the source Issue from the EVENTBUS-011 bullet.
- Keep the EVENTBUS-011 bullet's description of the race condition (spurious 409 when event deleted between NACK call and status check) unchanged.
- No Decision text changes — the ADR's core decision remains valid.

## Alternatives considered

- Removing the entire EVENTBUS-011 bullet: would lose the race condition claim which is still valid.
- Updating the bullet to reflect the new behavior: the EVENTBUS-011 bullet describes a different issue (the race condition), not the per-consumer ACK gap.

## Implementation

### Target file

`docs/10_adr/ADR-006-eventbus-sqlite-persistence-and-sse-delivery.md`

### Procedure

1. Update the EVENTBUS-011 Known Deviations bullet (line 386) to remove the pointer to the source Issue.
2. Keep the EVENTBUS-011 bullet's description of the race condition unchanged.

### Method

#### Change: EVENTBUS-011 Known Deviations bullet (line 386)

Current text:
```
- **Known Issue**: EVENTBUS-011 — `nack_event()` now returns `(-2,-2)` for invalid transitions (already ACKed or DLQ'd), and `ack_route.py` converts this to HTTP 409. However, the caller (`_nack_and_promote()`) checks `failure_count == -2` but does not verify whether the event is actually in the database before raising 409 — if the event was deleted between the NACK call and the status check, a spurious 409 could be returned (the intended response is 404). Separately, a NACK after a same-consumer ACK is currently accepted rather than rejected with 409, because the per-consumer ACK path does not set `events.acked_at`; see `issues/20261005-102244_eb002_eventbus-nack-accepted-after-per-consumer-ack.md`.
```

Replace with:
```
- **Known Issue**: EVENTBUS-011 — `nack_event()` now returns `(-2,-2)` for invalid transitions (already ACKed or DLQ'd), and `ack_route.py` converts this to HTTP 409. However, the caller (`_nack_and_promote()`) checks `failure_count == -2` but does not verify whether the event is actually in the database before raising 409 — if the event was deleted between the NACK call and the status check, a spurious 409 could be returned (the intended response is 404).
```

### Details

- Current EVENTBUS-011 bullet cites the source Issue for the per-consumer ACK gap.
- The EVENTBUS-011 bullet's primary claim (the race condition on 409) remains valid and should be preserved.
- The per-consumer ACK gap is now resolved by the implementation, so the pointer is no longer needed.

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
  - `uv run python tools/check_docs_structure.py docs/10_adr/ADR-006-eventbus-sqlite-persistence-and-sse-delivery.md`
  - `uv run python tools/check_docs_content_policy.py`
  - `uv run python tools/check_known_deviation_sync.py`
- Confirm no stale pointers to the source Issue remain.

## Completion criteria

- The EVENTBUS-011 bullet no longer references the source Issue.
- The EVENTBUS-011 bullet's description of the race condition is preserved.
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
- **Related target files**: docs/10_adr/ADR-006-eventbus-sqlite-persistence-and-sse-delivery.md