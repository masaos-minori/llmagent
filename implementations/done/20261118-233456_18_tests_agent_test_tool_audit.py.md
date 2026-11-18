## Goal

Remove the orphan-path tests from the audit suite while preserving the ADR-001 INV-11 evidence this
Plan must keep intact (REQ-007, REQ-009).

## Scope
**Release unit**: approval-event-cleanup

## Assumptions
- `TestAuditApprovalInv11` (`:111` docstring) is the INV-11 evidence cited by
  `registry/manifests/invariant_coverage.yaml:23-29`; it exercises `audit_approval()` only and must
  survive byte-for-byte.
- Orphan references to delete: imports `:21`, `:25`; `TestLogApprovalDecision` (`:79-107`, live
  `TestAuditApprovalInv11` starts at `:110`); the
  `("decision", "log_approval_decision", "write_file")` entry in `_SKIP_WRITERS` (`:410-416`) and its
  `_call_audit_writer` arm (`:424-433`).

## Design decisions
- The workflow-id-precondition parametrization keeps its remaining branches (`approval`, `exec`); only
  the `decision` branch is removed, so the invariant it tests stays covered by two writers.
- No new INV-11 test is added here: the existing one already covers the live event (row 29 keeps the
  ADR wording aligned).

## Alternatives considered
Marking the orphan tests skipped — rejected; a skipped test for a deleted symbol is dead weight and
AC-007 requires no orphan symbol coverage to remain.

## Implementation
### Target file
`tests/agent/test_tool_audit.py`
### Procedure
1. Delete `TestLogApprovalDecision` (`:79-107`) and the `log_approval_decision` / `ApprovalOutcome`
   imports (`:21`, `:25`).
2. Delete the `decision` entry from `_SKIP_WRITERS` and the `elif branch == "decision"` arm of
   `_call_audit_writer()`.
3. Leave `TestAuditApprovalInv11` and all `audit_approval()` tests unchanged.
### Method
Pure deletion; no assertion changes on the live path.
### Details
- After the edit `rg "log_approval_decision|ApprovalOutcome" tests/agent/test_tool_audit.py` must be
  empty.
- Same commit as Plan rows 04/05/06/17/19 and the regenerated artifacts (rows 33/34).

## Compatibility considerations
`invariant_coverage.yaml` re-renders from `docs/10_adr/adr_01_index.md` in Phase 6 (rows 31/35); the
INV-11 evidence path does not change, only its content.

## Security considerations
Audit evidence for INV-11 is preserved; removing dead coverage does not weaken the gate.

## Rollback considerations
Revert the whole unit commit (see row 04 procedure).

## Validation plan
- `uv run pytest tests/agent/test_tool_audit.py -q`
- `uv run python tools/check_adr_invariant_matrix.py` and `uv run python tools/check_adr_preservation.py`
  in the same release unit.

## Completion criteria
No reference to the removed symbols remains; `TestAuditApprovalInv11` passes unchanged (AC-007).

## Out of Scope
`docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md` (row 29), artifact regeneration (rows 31/33/34/35).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Delete the orphan tests and the `decision` branch per Procedure | Completed | 20261119-072943 | 20261119-072943 | Imports :21/:25, `TestLogApprovalDecision` :79-107, `decision` entry + `elif` arm removed; `TestAuditApprovalInv11` byte-identical; docstring "three"→"two" writers |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261119-072943 | 20261119-072943 | pytest passes (309); check_adr_invariant_matrix + check_adr_preservation: no issues |

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
- **Requirement ID**: `REQ-007` (orphan path removal), `REQ-009` (INV-11 evidence preserved)
- **Source issue**: `issues/20261117-123003_adrchk003_agent-approval-policy.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261118-224457_adrchk003_agent-approval-policy.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261118-233456
- **Related target files**: `tests/agent/test_tool_audit.py`
