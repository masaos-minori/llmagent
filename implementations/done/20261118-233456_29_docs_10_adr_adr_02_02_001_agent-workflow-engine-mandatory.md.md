## Goal

Confirm that ADR-001 INV-11's evidence still points at a test that exists after the DT-04 Option A removal,
and align its wording with the surviving `tool_approval` audit path (REQ-007, REQ-009).

## Scope
**Release unit**: boundary-and-adr-record

## Assumptions
- INV-11 (`docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md:175`) is evidenced by
  `tests/agent/test_tool_audit.py::TestAuditApprovalInv11` (matrix row `docs/10_adr/adr_01_index.md:180`),
  which row 18 keeps intact.
- The removed orphan path (`log_approval_decision`, `approval_decision` event) is not part of INV-11's
  statement.

## Design decisions
- Expected outcome is verification, not rewriting: if the invariant already names only the
  `tool_approval` event, the only change needed is confirming the evidence path and, if the ADR mentions
  the orphan event, deleting that mention.

## Alternatives considered
Pointing INV-11 at a new test — unnecessary; the existing INV-11 test survives the removal (row 18).

## Implementation
### Target file
`docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md`
### Procedure
1. Read INV-11 (`:175`) and its Verification section; confirm no reference to `log_approval_decision` or
   the `approval_decision` event remains in the invariant or its evidence text.
2. If such a reference exists, delete it and state that the evidence is
   `tests/agent/test_tool_audit.py::TestAuditApprovalInv11`.
### Method
Verification with at most one wording edit; the invariant statement itself is not shortened.
### Details
N/A: nothing beyond the evidence alignment is not inferable from REQ-007.

## Compatibility considerations
`registry/manifests/invariant_coverage.yaml:23-29` (row 35) is regenerated from the matrix after this
document and row 18 land.

## Security considerations
INV-11 keeps its Blocking gate status; the change must not downgrade it.

## Rollback considerations
Revert the whole unit commit (see rows 04 and 27).

## Validation plan
- `uv run python tools/check_adr_preservation.py`, `uv run python tools/check_adr_invariant_matrix.py`,
  `uv run pytest tests/agent/test_tool_audit.py -q`.

## Completion criteria
INV-11's cited test exists and passes after Phase 4, and no ADR text references a removed symbol
(AC-007, AC-009).

## Out of Scope
The audit tests (row 18), the matrix and manifest (rows 31/35).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Verify and align INV-11 evidence per Procedure | Completed | 20261119-081019 | 20261119-081019 | Verification-only (expected outcome, no edit needed): INV-11 (`:175`), its Verification row (`:191`) and the Implementation Notes mention (`:224`) reference only the `tool_approval` event; grep confirms no `log_approval_decision`/`approval_decision` reference anywhere in the ADR. Cited test `TestAuditApprovalInv11` exists (test_tool_audit.py:77) and passes after the row 18 removals |
| 3 | Run the ADR checkers (`routing.md` Tools) | Completed | 20261119-081019 | 20261119-081019 | check_adr_preservation and check_adr_invariant_matrix pass; 42 test_tool_audit tests pass; INV-11 keeps Blocking=Yes in the Verification row |

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
- **Requirement ID**: `REQ-007` (orphan path removal), `REQ-009` (invariant evidence preserved)
- **Source issue**: `issues/20261117-123003_adrchk003_agent-approval-policy.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261118-224457_adrchk003_agent-approval-policy.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261118-233456
- **Related target files**: `docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md`
