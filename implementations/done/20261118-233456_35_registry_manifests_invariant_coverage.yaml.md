## Goal

Refresh the generated invariant-coverage manifest so its evidence entries match the post-change ADR
matrix and test files (REQ-009, REQ-011).

## Scope
**Release unit**: boundary-and-adr-record

## Assumptions
- `registry/manifests/invariant_coverage.yaml:23-29` is the ADR-001 INV-11 evidence entry citing
  `tests/agent/test_tool_audit.py`, which Plan row 18 modifies but whose INV-11 test survives.
- The manifest is generated from `docs/10_adr/adr_01_index.md` (row 31) by `tools/generate_reference_table.py:471`.

## Design decisions
N/A: regeneration only; the manifest's content is decided by the matrix edited in row 31.

## Alternatives considered
Hand-editing the evidence entry — prohibited; the matrix is the source.

## Implementation
### Target file
`registry/manifests/invariant_coverage.yaml`
### Procedure
Run `uv run python tools/generate_reference_table.py --manifests` after rows 18/27/31 land, and commit the
regenerated manifest unchanged.
### Method
Generator invocation only.
### Details
N/A: no hand edits.

## Compatibility considerations
Must land in the same release unit as the ADR matrix edit (row 31) and the audit test change (row 18).

## Security considerations
N/A: generated manifest.

## Rollback considerations
Revert the whole unit commit (see row 27).

## Validation plan
- `uv run python tools/check_adr_invariant_matrix.py`
- `uv run python tools/generate_reference_table.py --check`

## Completion criteria
Every evidence path in the manifest exists and passes, ADR-014 INV-03 shows an automated gate, and drift is
zero (AC-009, AC-011).

## Out of Scope
The matrix (row 31), the ADR bodies (rows 27/28/29/30).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Run the generator and commit the regenerated manifest | Completed | 20261119-081925 | 20261119-081925 | Regenerated in the same `--manifests` run as rows 33/34 after rows 18/27/31 landed: ADR-014 INV-03 entry now gate `Unit Test`, timing `CI`, status `Confirmed`, citing `tests/agent/test_orchestrator.py::TestNoServerSideSafetyReimplementation` + the posture-contract files; ADR-001 INV-11 entry unchanged citing `TestAuditApprovalInv11` (verified existing and passing). No hand edits |
| 3 | Run the ADR and manifest checkers (`routing.md` Tools) | Completed | 20261119-081925 | 20261119-081925 | check_adr_invariant_matrix: no issues; generate_reference_table --check: no drift |

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
- **Requirement ID**: `REQ-009` (invariant evidence), `REQ-011` (generated artifacts)
- **Source issue**: `issues/20261117-123003_adrchk003_agent-approval-policy.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261118-224457_adrchk003_agent-approval-policy.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261118-233456
- **Related target files**: `registry/manifests/invariant_coverage.yaml`
