## Goal
Remove the INV-12 / INV-07 contradiction, state INV-10's real scope, align Known Deviations with the ledger and drop a duplicate Review Trigger (REQ-001 to REQ-006 of the Plan).

## Scope
- Only `docs/10_adr/ADR-006-eventbus-sqlite-persistence-and-sse-delivery.md`; no other file is modified by this procedure.

## Assumptions
- User decisions (2026-10-08): INV-12 is confirmed as "a failed ACK is not treated as success; the event stays eligible for redelivery"; a `Decision Change` line in the form used by ADR-007 is added (UNK-01, UNK-03).

## Design decisions
- Known Deviations parentheticals follow the ledger entries; EVENTBUS-013 uses the ledger's observed behavior (ACK/NACK check only the principal allowlist) rather than memo2.md's looser wording.
- The NACK route is `POST /nack` (Confirmed by repository evidence — `scripts/eventbus/app.py`), so 11b names that path instead of memo2.md's `/events/{event_id}/nack`.

## Alternatives considered
- Keeping "not redelivered": rejected by the user decision above because it contradicts INV-07.

## Implementation
### Target file
docs/10_adr/ADR-006-eventbus-sqlite-persistence-and-sse-delivery.md

### Procedure
1. Replace Decision item 11 with the labelled rules 11a to 11e.
2. Replace INV-10, INV-11 and INV-12.
3. Replace Known Deviations with the five entries and remove the EVENTBUS-013 Review Trigger.
4. Add the `Decision Change (2026-10-08)` line to the Approval Record.
5. Run the documentation checkers.

### Method
Exact-string replacements in one file.

### Details
Code claims keep their evidence labels; no line numbers or counts are added.

## Compatibility considerations
- Documentation only.

## Security considerations
- None.

## Rollback considerations
- Revert the commit.

## Validation plan
- `check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py`, `check_known_deviation_sync.py`, `check_adr_invariant_matrix.py`, `check_adr_structure.py`, `check_adr_reference.py`, `check_docs_consistency.py --domain agent`; `rg` finds no "not redelivered" phrase.

## Completion criteria
- The edits are in place and the checkers pass (REQ-001 to REQ-006).

## Out of scope
- Any file other than `docs/10_adr/ADR-006-eventbus-sqlite-persistence-and-sse-delivery.md`, including the governance ledger.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Apply the change in Implementation > Procedure | Completed | 20261008-182133 | 20261008-182133 |  |
| 2 | Run the validation in the Validation plan | Completed | 20261008-182133 | 20261008-182133 |  |

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
- **Requirement ID**: REQ-001, REQ-002, REQ-003, REQ-004, REQ-005, REQ-006
- **Source issue**: issues/done/20261008-094450_adr006fix_fix-adr-006-inv-12-contradiction-and-inv-10-scope.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261008-181901_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261008-182119
- **Related target files**: docs/10_adr/ADR-006-eventbus-sqlite-persistence-and-sse-delivery.md