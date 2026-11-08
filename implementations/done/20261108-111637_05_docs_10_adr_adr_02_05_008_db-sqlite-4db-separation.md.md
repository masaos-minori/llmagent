## Goal
Correct the ADR-008 INV-01 to INV-04 Verification mapping and update the INV-16 row to cite the new Dry Run test (REQ-005, REQ-007 size).

## Scope
**Release unit**: N/A: not part of a release unit
Edits the Verification section of `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md` only.

## Assumptions
- Runs after the adrdb001 ADR-008 procedure, which also brings the file under its size ceiling; this edit must not push it back over 34206 bytes (sequencing dependency on the same ADR, not a conflict).
- The new Dry Run test exists (seq 03).

## Design decisions
- Map each of INV-01 to INV-04 to evidence that matches the invariant wording as reworded by adrdb001; keep the remaining limit visible.

## Alternatives considered
N/A: wording update

## Implementation
### Target file
`docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md`

### Procedure
1. Replace the INV-01 to INV-04 evidence row with evidence matching each invariant (static separation check for ownership and file separation).
2. Update the INV-16 row to cite the new Dry Run byte-identity test and its limit.
3. Run `wc -c` and condense if the result exceeds 34206 bytes.

### Method
Documentation edit plus a size check.

### Details
- Do not remove any invariant, reference or evidence to meet the ceiling; if that is impossible, stop and report.

## Compatibility considerations
Documentation only.

## Security considerations
N/A: documentation-only change

## Rollback considerations
N/A: revert the commit

## Validation plan
- `uv run python tools/check_docs_structure.py`: no size finding
- `uv run python tools/check_docs_quality.py`, `check_docs_content_policy.py`: no findings
- `uv run python tools/check_adr_preservation.py`, `check_adr_invariant_matrix.py`, `check_adr_structure.py`: no new ERROR
- `uv run python tools/check_db_separation.py`: pass

## Completion criteria
- INV-01 to INV-04 rows map to matching evidence; INV-16 cites the new test; the file is at most 34206 bytes.

## Out of Scope
- Scope and approval wording (adrdb001).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Edit the document as described in Implementation > Procedure | Completed | 20261108-114043 | 20261108-114043 | Gated: plans/done/20261108-092007_adrdb001_clarify-adr-008-scope.md phase 4 - the ADR-008 wording and size reduction must be executed first |
| 2 | Run the documentation checkers named in the Validation plan | Completed | 20261108-114043 | 20261108-114043 | checkers and check_db_separation pass; file at 34186 bytes (ceiling 34206); preservation ERRORs are the intended INV-01, Approval and test-citation edits |

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
- **Requirement ID**: `REQ-005`, `REQ-007` (ADR-008 verification mapping and size)
- **Source issue**: issues/20261107-050705_adrver001_align-invariant-verification-claims.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261108-092352_adrver001_align-invariant-verification-claims.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261108-111637
- **Related target files**: `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md`
