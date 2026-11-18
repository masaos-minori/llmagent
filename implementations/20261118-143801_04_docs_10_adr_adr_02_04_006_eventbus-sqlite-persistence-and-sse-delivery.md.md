## Goal
State the no-event-loss claims of ADR-006 as holding under the ADR-008 schema-mismatch rule (`REQ-005`), record the missing retention as an accepted risk (`REQ-006`), update the ADR-008 title (`REQ-004`), and add the pending record (`REQ-008`).

## Scope
**Release unit**: N/A: not part of a release unit
- In scope: every sentence that claims events are not lost, the Data Ownership `Deletion Rule`, Related ADRs, and Approval Record.

## Assumptions
- Procedure 02 has landed: ADR-008 Decision Details #22 and #23 exist, and AAL-029 exists in the ledger.
- The no-loss claims are at the Summary line, Decision Detail 9, Rationale (Data Integrity), Positive Consequences, and INV-07 (checked in Step 3a with `rg -n loss`).

## Design decisions
- Wording: `duplicates are tolerated but losses are not, except for events not carried over when the database is archived and recreated under the ADR-008 schema-mismatch rule (Decision Detail #22)`; keep the sentence otherwise unchanged.

## Alternatives considered
N/A: the maintainer's decisions are recorded in the Plan's Design section.

## Implementation
### Target file
`docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md`

### Procedure
1. Apply the wording above to each no-loss claim found with `rg -n -i "loss"` (Summary, Decision Detail 9, INV-07, and the two Rationale/Consequences statements); do not touch the offset-monotonicity or alternative-rejection sentences.
2. `Data Ownership and Persistence`: after the `Deletion Rule` sentence add that no retention exists: `events`, `consumer_delivery`, and `dlq_outbox` rows are never deleted and grow without bound, an accepted risk (ADR-008 Decision Detail #23); the Review Trigger `Automatic event retention or pruning becomes necessary` stays.
3. `Related ADRs`: `ADR-008: Separating SQLite into Six Databases`.
4. `Approval Record`: add one pending bullet in the ADR-004 form for the conditional no-loss statements and the retention risk, tracked by AAL-029; write no approval text.

### Method
- Keep the existing pending and approval bullets unchanged.

### Details
- The ADR is 30005 bytes; the limit is 32768; the edits add under 0.8 KB.

## Compatibility considerations
N/A: documentation or comment text only.

## Security considerations
N/A: no approval statement is written or simulated; pending bullets only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_adr_structure.py`, `check_adr_reference.py`, `check_adr_preservation.py` (report), and the checkers `routing.md` Tools lists for a `docs/` edit (`uv run python tools/run_validation_gates.py` runs the ones the changed files trigger).

## Completion criteria
- Each no-loss claim carries the ADR-008 condition; the retention risk is stated; the title matches; the pending bullet cites AAL-029; the checkers report no finding.

## Out of Scope
- ADR-008 text (procedure 02), implementation of retention, approval text.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Edit the no-loss claims, Deletion Rule, Related ADRs, and approval bullet (Implementation > Procedure) | Pending | — | — | |
| 2 | Run the ADR and documentation checkers (Validation plan) | Pending | — | — | |

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
- **Requirement ID**: REQ-004, REQ-005, REQ-006, REQ-008
- **Source issue**: issues/20261117-123008_adrchk008_db-data-lifecycle.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261118-142957_adrchk008_db-data-lifecycle.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261118-143801
- **Related target files**: `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md`
