## Goal

Remove the internal conflicts and stale boilerplate in ADR-006: the INV-06 verification
contradiction, the Alternative B rationale that contradicts Decision Detail 13, the missing
start-position condition on the At-Least-Once guarantee (as a pending amendment), and the
single-database and privileges-only-in-SQLite statements that no longer describe the repository.

## Scope
**Release unit**: N/A: not part of a release unit

- Only `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md` is modified.
- The `AAL-037` ledger entry itself is procedure `20261120-162706_02`.

## Assumptions

- ADR-008 (six per-process databases) and ADR-013 (EventBus HTTP authentication and authorization)
  are the current authority for the database and privilege model; both are already in this file's
  front matter `related` and Related ADRs lists, so naming them adds no new reference.
- The `since_seq` condition changes decision meaning, so it is recorded as a pending amendment;
  no approver or date is written anywhere in this procedure.

## Design decisions

- Keep the ADR-008 schema-mismatch exception as its own sentence rather than a trailing clause, so
  the guarantee condition and the exception are separable statements.
- State the condition in both places that carry the guarantee text (Decision Detail 9 and INV-07);
  leaving one unchanged would create a new internal conflict in the same file.

## Alternatives considered

- Record the `since_seq` condition as an approved change: rejected, `AGENTS.md` policy and
  `docs/00_governance/governance_01_documentation-policy.md` ADR Pending Amendment Form require
  pending form for decision-text changes with no recorded approver.

## Implementation
### Target file
`docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md`

### Procedure
Rewrite the Manual Review INV-06 bullet; narrow Alternative B; add the start-position condition to
Decision Detail 9 and INV-07; restate the Constraints, Assumptions and Security Consequences
boilerplate; append the pending-amendment bullet to the Approval Record.

### Method
Text-level edits in the hand-written sections. No AUTO-GENERATED block is touched.

### Details

- Manual Review: `INV-01 has no dedicated automated test (it is exercised indirectly by every
  persistence test); INV-06 has dedicated tests in the Automated Tests table and is bounded by the
  envelope schema's `event_id` format check in
  `tests/eventbus/test_eventbus_publish_contract.py::TestPublishEnvelopeSchemaContract``. This
  matches the Automated Tests rows `test_identical_content_retry_returns_same_seq` and
  `test_conflicting_content_retry_returns_409` in `tests/eventbus/test_eventbus_publish.py`.
- Alternative B: the Description no longer claims backward movement is needed for out-of-order
  ACKs; the Reason for Rejection adds "Out-of-order ACKs are already permitted without backward
  offset movement (Decision Detail 13)."
- Decision Detail 9 and INV-07: the guarantee "holds when the Consumer initiates delivery from a
  start position the Consumer itself selected, either a `since_seq` greater than zero or a
  `Last-Event-ID` header"; the ADR-008 schema-mismatch exception becomes a separate sentence.
  Matches `scripts/eventbus/subscribe_route.py` start-position precedence.
- Constraints: "EventBus events are managed in a dedicated SQLite database (`eventbus.sqlite`)
  under the ADR-008 per-process database separation".
- Assumptions: "Single host; the EventBus owns `eventbus.sqlite` among the six per-process SQLite
  databases defined by ADR-008"; "Privileges are enforced at the EventBus HTTP authentication layer
  defined by ADR-013, not within SQLite"; the re-evaluate line drops "multi-DB configuration".
- Security Consequences: "Trust boundary: privileges are enforced at the EventBus HTTP
  authentication layer defined by ADR-013, not within SQLite".
- Approval Record: append one `**Current Decision Approval (pending)**` bullet citing `AAL-037`,
  Approver and Date "Not recorded".
- The Completion Checklist gap lines are generic ("gaps: Verification > Manual Review") and name no
  invariant, so they need no edit.

## Compatibility considerations

- Verification wording only for INV-06; the cited tests already exist and are not modified.

## Security considerations

- N/A: no code path changes; the wording states where privileges are enforced
  (`scripts/eventbus/auth.py`).

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run python tools/check_adr_structure.py`, `check_docs_structure.py`,
  `check_docs_content_policy.py`, `check_adr_reference.py`, `check_adr_authority.py`.
- `uv run python tools/check_adr_preservation.py --base HEAD`: the Decision, Invariants and Approval
  findings are expected signals for the intended edits.
- `grep -n "only within SQLite" docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md`
  returns nothing.

## Completion criteria

- No statement in the file contradicts Decision Detail 11a, 11b, 13 or the Automated Tests table.
- The delivery guarantee states its start-position condition, and that change is tracked by a
  pending bullet and `AAL-037` with no approver or date recorded.
- No single-database or privileges-only-in-SQLite claim remains.

## Out of Scope

- Editing `tests/` or `scripts/`; changing any other ADR; recording an approval.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Apply the five wording changes listed in Implementation > Details | Completed | 20261120-163733 | 20261120-163733 | Completion Checklist needs no edit: its gap lines are generic |
| 2 | Append the pending-amendment bullet citing `AAL-037` | Completed | 20261120-163733 | 20261120-163733 | Placed after the `AAL-029` bullet, which covers the same two statements |
| 3 | Run the ADR and docs checkers in the Validation plan | Completed | 20261120-163733 | 20261120-163733 | `check_adr_structure.py`: only the pre-existing ADR-015 warning; preservation findings limited to the intended edits |

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
- **Requirement ID**: `REQ-001` (INV-06 verification conflict), `REQ-002` (Alternative B rationale),
  `REQ-003` (delivery-guarantee condition as a pending amendment), `REQ-005` (stale single-database
  statements), `REQ-006` (privileges statement)
- **Source issue**: issues/20261117-123016_adrchk016_adr006-boilerplate-fixes.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261120-155214_adrchk016_adr006-boilerplate-fixes.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261120-162706
- **Related target files**: `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md`