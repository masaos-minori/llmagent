## Goal

Update `docs/24_eventbus/eventbus_12_ack_nack_endpoints.md` so its NACK/ACK response
semantics and state-transition table match the implemented per-consumer ACK/NACK state
(`REQ-001`–`REQ-005`) (`REQ-006`).

## Scope

Modifies `docs/24_eventbus/eventbus_12_ack_nack_endpoints.md` only. Coordinates with
`docs/10_adr/ADR-006...` and `docs/00_governance/governance_03...`. See Design
decisions.

## Assumptions

- This doc describes runtime HTTP behavior; update it only after the implementation
  lands. Do not describe behavior that is not yet committed.
- The per-consumer DLQ-promotion source (`REQ-002`) is pending the ADR-006 decision;
  do not assert a promotion source that is not yet decided.

## Current state (adversarial verification)

- Line 193: HTTP 409 branch states it fires when `events.acked_at` is set — obsolete
  after `REQ-004`; it should reference `consumer_delivery.acked_at`.
- Line 245 "Duplicate NACK" row: states "No idempotency guard in `nack_event`; the
  counter increases on every call (EVENTBUS-012)". Superseded by `REQ-001`.
- Line 24: NACK prose says it "moves the event to the DLQ once it reaches `max_retry`"
  on the shared counter; superseded by `REQ-002` pending the ADR-006 decision.

## Design decisions

- Rewrite the "Duplicate NACK" row (line 245) to describe the `last_nack_attempt`
  idempotency guard: a re-sent NACK for the same delivery attempt is ignored (count
  once), per `REQ-001`.
- Correct the HTTP 409 description (line 193) to fire on `consumer_delivery.acked_at`
  (per-consumer already acknowledged) or DLQ membership — not `events.acked_at`.
- Update the state-transition table (lines 242-250) for ACK→NACK rejection and
  NACK idempotency.
- Leave the DLQ-promotion-counter wording either neutral or explicitly pending the
  ADR-006 decision; do not claim per-consumer promotion until decided.

## Implementation

### Target file

`docs/24_eventbus/eventbus_12_ack_nack_endpoints.md`

### Procedure

1. Rewrite the "Duplicate NACK" row (line 245) to reflect `REQ-001` idempotency.
2. Correct the HTTP 409 semantics (line 193) to `consumer_delivery.acked_at` + DLQ.
3. Update the state-transition table (lines 242-250) for NACK idempotency and
   ACK→NACK rejection.
4. Neutralize or mark pending the shared-counter promotion wording (line 24) per the
   ADR-006 decision.

### Method

- Open the doc; locate the rows via the grep markers (409/404, Duplicate NACK, state
  transition table).
- Keep the table's column structure and tone; only change factual rows.
- Cross-check each statement against the committed implementation.

### Details

- Do not restructure the document; edit rows in place.
- Preserve the 404 (not found) semantics unchanged.

## Compatibility considerations

- Documentation only; no code impact.

## Security considerations

- None beyond accurate issue tracking.

## Rollback considerations

- Revert via version control if the underlying behavior changes.

## Validation plan

- Documentation review: 409 no longer references `events.acked_at`; Duplicate NACK
  row reflects idempotency; state-transition table is consistent with the code.
- Consistency check against ADR-006 and governance_03.

## Completion criteria

- HTTP 409 description references `consumer_delivery.acked_at`, not `events.acked_at`.
- Duplicate-NACK row reflects the `REQ-001` idempotency guard.
- State-transition table matches the committed implementation.

## Out of scope

- `ADR-006` and `governance_03` updates (their own rows) — coordinate status.
- Code/schema changes.

## Execution Status

| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Post-implementation doc update |
| 2 | Add or update tests per Validation plan | N/A | — | — | Documentation change |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | Docs review applies |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | This row |

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
- **Requirement ID**: `REQ-006`
- **Source issue**: `issues/done/20261007-154016_ebnack01_fix-eventbus-ack-and-nack-state-management.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261008-160952_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261009-071937
- **Related target files**: `docs/24_eventbus/eventbus_12_ack_nack_endpoints.md`
