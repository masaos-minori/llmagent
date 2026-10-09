## Goal

Update `docs/10_adr/ADR-006-eventbus-sqlite-persistence-and-sse-delivery.md` so its
schema/table descriptions and Known Issues reflect the implemented ACK/NACK state
management (`REQ-001`–`REQ-005`) and record the per-event vs per-consumer DLQ-unit
decision required by `REQ-002` (`REQ-006`).

## Scope

Modifies `docs/10_adr/ADR-006-eventbus-sqlite-persistence-and-sse-delivery.md` only.
Coordinates with `docs/00_governance/governance_03_issue-and-uncertainty-management.md`
(the Known Issue source of truth) and the code rows (`delivery_repo.py`, `ack_route.py`,
`schema.sql`, `schema_sql.py`, `_constants.py`, `dlq.py`). See Design decisions.

## Assumptions

- This ADR is a living record; edits go through the normal ADR change process (see the
  existing "Decision Change" entries).
- Documentation updates happen AFTER the implementation they describe. Do not claim a
  Known Issue is resolved until the code change is committed.
- The per-event vs per-consumer DLQ-unit decision (`REQ-002`) must be recorded here
  before the `dlq.py` row is implemented.

## Current state (adversarial verification)

- Lines 390-394 list Known Issues EVENTBUS-011, 012, 014 as "tracked in
  governance_03 Part 1" (open).
- Lines 446-447 describe the `events` table including `acked_at` ("not written by the
  ACK route") and `consumer_delivery` with `acked_at`.
- Line 385 documents `ack_event_for_consumer()` updating both tables atomically.

## Design decisions

- Record the `REQ-002` DLQ-unit decision (per event vs per consumer) in the ADR's
  Decision History / Known Deviations section; this is the ADR-006 deliverable for
  `REQ-002`.
- After `REQ-004`, remove the `events.acked_at` mention from the table description
  (line 446); ACK state lives solely in `consumer_delivery.acked_at`.
- Mark EVENTBUS-011, 012, 014 resolved (or cross-reference their resolution) once the
  matching code commits land and `governance_03` reflects them. Keep the historical
  record — do not delete prior Decision Change entries.

## Implementation

### Target file

`docs/10_adr/ADR-006-eventbus-sqlite-persistence-and-sse-delivery.md`

### Procedure

1. Add a Decision Change entry recording the per-event vs per-consumer DLQ-unit
   decision (`REQ-002`), dated, following the style of the existing 2026-10-08 entry.
2. Update the `events`/`consumer_delivery` table description (lines 446-447): drop the
   `events.acked_at` column reference; keep `consumer_delivery.acked_at`.
3. Update the Known Issues block (lines 390-394): mark EVENTBUS-011, 012, 014 as
   resolved with the resolution date and a pointer to the resolving code/issue, or
   change "tracked in governance_03" to "resolved" once governance_03 is updated.
4. Ensure the INV-10 / ACK-NACK invariant language (lines 234, 377, 468) stays
   consistent with the per-consumer model.

### Method

- Open the ADR; locate the sections above via the grep markers.
- Write concise, present-tense updates; preserve prior Decision Change history.
- Cross-check every claim against the committed implementation before marking a Known
  Issue resolved.

### Details

- Do not alter invariants or their IDs; only update descriptions and issue status.
- Keep the ADR internally consistent with `governance_03` (both must agree on the
  resolution status of EVENTBUS-011/012/014).

## Compatibility considerations

- This is documentation only; no code/schema impact.

## Security considerations

- None beyond accurate issue tracking.

## Rollback considerations

- Revert to the prior ADR text via version control if the recorded decision changes.

## Validation plan

- Documentation review: ADR table description has no `events.acked_at`; Known Issues
  EVENTBUS-011/012/014 status matches governance_03 and the committed code; the
  DLQ-unit decision is recorded.
- Confirm no stale "never written but still read" language remains.

## Completion criteria

- `events.acked_at` removed from the ADR table description.
- EVENTBUS-011/012/014 status reflects resolution (or explicit pending pointer).
- The per-event vs per-consumer DLQ-unit decision is recorded in the ADR.

## Out of scope

- `governance_03` updates (its own row) — coordinate status.
- Code/schema changes described by this ADR.

## Execution Status

| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261009-232009 | 20261009-232009 | Post-implementation doc update |
| 2 | Add or update tests per Validation plan | N/A | — | — | Documentation change |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261009-232009 | 20261009-232009 | Docs review applies |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261009-232009 | 20261009-232009 | This row |

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
- **Related target files**: `docs/10_adr/ADR-006-eventbus-sqlite-persistence-and-sse-delivery.md`
