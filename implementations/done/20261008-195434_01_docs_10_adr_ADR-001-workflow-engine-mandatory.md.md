## Goal
Name the load-failure fallback as prohibited in ADR-001 Decision item 4, record the Orchestrator-level abort in the Implementation Notes, and record the decision change (REQ-001 to REQ-004 of the Plan).

## Scope
- Only `docs/10_adr/ADR-001-workflow-engine-mandatory.md`; no other file is modified by this procedure.

## Assumptions
- UNK-02 resolved: `TestWorkflowLoadFailureIsFatal` passes (4 passed); the Verification entries for INV-01 and INV-05 are generic startup-failure tests, so the cited test is recorded only in the Implementation Notes.
- User decision (2026-10-08): a `Decision Change` line is added (UNK-01). The memo2.md paragraph citing AGENT-003 is not used because AGENT-003 no longer exists (UNK-03).

## Design decisions
- Decision numbering is unchanged; the Known Deviations section stays "No confirmed deviations."

## Alternatives considered
- Writing the memo2.md Implementation Notes paragraph: rejected; it would describe a deviation that no longer exists.

## Implementation
### Target file
docs/10_adr/ADR-001-workflow-engine-mandatory.md

### Procedure
1. Extend Decision Details item 4 with the load-failure fallback wording.
2. Add the Orchestrator-level abort entry and its test to the Implementation Notes.
3. Add the `Decision Change` line to the Approval Record.
4. Run the documentation checkers and the cited test.

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
- The documentation checkers (quality, structure, content_policy, known_deviation_sync, adr_invariant_matrix, adr_structure, adr_reference, `check_docs_consistency.py --domain agent`); `uv run pytest tests/agent/test_orchestrator.py -k WorkflowLoadFailureIsFatal`; `rg` finds no AGENT-003 in the ADR.

## Completion criteria
- The edits are in place, the cited test passes and the checkers pass (REQ-001 to REQ-004).

## Out of scope
- Any file other than `docs/10_adr/ADR-001-workflow-engine-mandatory.md`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Apply the change in Implementation > Procedure | Completed | 20261008-195434 | 20261008-195434 |  |
| 2 | Run the validation in the Validation plan | Completed | 20261008-195434 | 20261008-195434 |  |

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
- **Requirement ID**: REQ-001, REQ-002, REQ-003, REQ-004
- **Source issue**: issues/done/20261008-094447_adr001fix_align-adr-001-implementation-notes-with-agent-003-and-number-decisions.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261008-195059_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261008-195434
- **Related target files**: docs/10_adr/ADR-001-workflow-engine-mandatory.md