## Goal

Record the DT-05 Option A decision in ADR-014: state that INV-03 now has automated evidence, and keep the
responsibility-boundary text aligned with the verified Agent/server split (REQ-004, REQ-009).

## Scope
**Release unit**: boundary-and-adr-record

## Assumptions
- INV-03 text at `docs/10_adr/adr_02_02_014_agent-control-plane-responsibility-boundaries.md:132` stays
  normative; only the verification claims change.
- Line 163 currently says "INV-01 and INV-03 have no automated tests and depend only on code review
  (Manual Review)" — the automated evidence arrives in Plan row 36 (`tests/agent/test_orchestrator.py`).
- The matrix row lives in `docs/10_adr/adr_01_index.md:209` (row 31), not in this document.

## Design decisions
- INV-01 stays Manual Review; only INV-03's evidence statement changes, so the ADR must not overstate
  coverage.
- INV-03's wording is not weakened or narrowed: `check_adr_preservation.py` must see an intended edit
  only in the verification statements.

## Alternatives considered
N/A: DT-05 Option A fixes the outcome; the ADR text change is its record.

## Implementation
### Target file
`docs/10_adr/adr_02_02_014_agent-control-plane-responsibility-boundaries.md`
### Procedure
1. Rewrite the `:163` sentence: INV-01 remains code-review-only; INV-03 is now gated by a named test in
   `tests/agent/test_orchestrator.py`.
2. Update the `## Verification` bullet that routes INV-03 to code review so it names the automated gate
   and keeps the review trigger for new server-side safety duplication.
3. Leave the three invariant statements (`:130-132`) untouched.
### Method
Verification-section edits only.
### Details
- Name the test class/method added in row 36 once that row lands, so the ADR and the matrix cite the same
  identifier.

## Compatibility considerations
Row 31 must mirror this change in the invariant matrix; `registry/manifests/invariant_coverage.yaml`
(row 35) is then regenerated from that matrix.

## Security considerations
Weakening INV-03 would permit Agent-side re-implementation of server safety checks; the edit adds
evidence, not latitude.

## Rollback considerations
Revert the whole unit commit with rows 07/28/30/31/36 and the regeneration (rows 31/33/34/35).

## Validation plan
- `uv run python tools/check_adr_preservation.py`, `uv run python tools/check_adr_structure.py`,
  `uv run python tools/check_adr_reference.py`, `uv run python tools/check_adr_invariant_matrix.py`.

## Completion criteria
The ADR states INV-03's automated evidence and the matrix and manifest agree with it (AC-009, AC-011).

## Out of Scope
The gate test itself (row 36), the matrix row (row 31), ADR-012 (row 28).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update the verification statements per Procedure | Pending | — | — | Phase 5, DT-05 Option A approved 2026-11-18 |
| 3 | Run the ADR checkers (`routing.md` Tools) | Pending | — | — | |

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
- **Requirement ID**: `REQ-004` (DT-05 decision), `REQ-009` (boundary record)
- **Source issue**: `issues/20261117-123003_adrchk003_agent-approval-policy.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261118-224457_adrchk003_agent-approval-policy.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261118-233456
- **Related target files**: `docs/10_adr/adr_02_02_014_agent-control-plane-responsibility-boundaries.md`
