## Goal

Resolve the EventBus Known Issues tracked in
`docs/00_governance/governance_03_issue-and-uncertainty-management.md` — EVENTBUS-011,
012, 014 — once their backing code changes are committed (`REQ-006`).

## Scope

Modifies `docs/00_governance/governance_03_issue-and-uncertainty-management.md` only.
Coordinates with `docs/10_adr/ADR-006...` (must agree on resolution status) and the
code rows (`delivery_repo.py`, `ack_route.py`, `schema.sql`, `schema_sql.py`,
`_constants.py`, `dlq.py`). See Design decisions.

## Assumptions

- Known Issues are resolved only when implementation and design agree (per the doc's
  own rule, line 414). Do not mark EVENTBUS-011/012/014 resolved before the matching
  code commits land.
- Resolution follows the doc's field schema (line 21): record Resolution, Observed
  Implementation after fix, Impact, etc.

## Current state (adversarial verification)

- Inventory table lines 66-69 list EVENTBUS-011, 012, 014 as `open`.
- Detailed entries lines 232-310 describe the current buggy behavior:
  - EVENTBUS-011 (247): `ack_route.py` re-reads `acked_at`/`dlq_at` in a separate
    `run_with_db_lock()` → 409.
  - EVENTBUS-012 (265-267): `nack_event()` increments counters on every duplicate
    NACK; no per-consumer guard.
  - EVENTBUS-014 (305-310): `ack_event()`, the only writer of `events.acked_at`, has
    no caller.

## Design decisions

- For each resolved issue: set Status to `resolved`, fill the Resolution and Observed
  Implementation-after-fix fields with a pointer to the resolving REQ/code, and keep
  the historical entry (do not delete — the inventory preserves history).
- Ensure the inventory table (lines 66-69) and the detailed entries (232-310) agree.
- Ensure ADR-006's Known Issues block (lines 390-394) reports the same resolution.
- EVENTBUS-012's resolution should note the `last_nack_attempt` idempotency guard
  (`REQ-001`); EVENTBUS-011 the atomic NACK (`REQ-003`); EVENTBUS-014 the
  `events.acked_at` removal (`REQ-004`).

## Implementation

### Target file

`docs/00_governance/governance_03_issue-and-uncertainty-management.md`

### Procedure

1. In the inventory table (lines 66-69), set EVENTBUS-011/012/014 Status to
   `resolved` and add a Resolution pointer (REQ + commit) once committed.
2. In the detailed entries (232-310), fill Resolution and Observed
   Implementation-after-fix for each; preserve the original Observed Implementation as
   history.
3. Cross-check consistency with ADR-006 (lines 390-394) and the code.

### Method

- Open the doc; locate the inventory (66-69) and detailed entries (232-310).
- Update Status and add Resolution/Observed-Implementation fields per the doc's schema.
- Do not rewrite unrelated sections.

### Details

- If a code change for one issue is still pending (e.g. the `REQ-002` DLQ-unit
  decision unresolved), leave that issue `open` and note the blocker rather than
  marking it resolved prematurely.

## Compatibility considerations

- Documentation only; no code impact.

## Security considerations

- None beyond accurate issue tracking.

## Rollback considerations

- Revert via version control; restore Status to `open` if a resolution is reverted.

## Validation plan

- Documentation review: EVENTBUS-011/012/014 Status is `resolved` with a resolution
  pointer in both the inventory and detailed entries; consistent with ADR-006 and the
  committed code.
- Any still-open issue is correctly marked open with its blocker noted.

## Completion criteria

- EVENTBUS-011/012/014 marked resolved with resolution pointers where the code lands.
- Inventory and detailed entries agree; ADR-006 agrees.

## Out of scope

- `ADR-006` and `eventbus_12` updates (their own rows) — coordinate status.
- Code/schema changes.

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
- **Related target files**: `docs/00_governance/governance_03_issue-and-uncertainty-management.md`
