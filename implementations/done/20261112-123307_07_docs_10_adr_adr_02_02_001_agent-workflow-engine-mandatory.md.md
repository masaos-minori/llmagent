## Goal
Change ADR-001's INV-02 verification row from Blocking `Yes` to Non-Blocking, because it is `Not verified` (`REQ-006`, `REQ-008` / `AC-6`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- The row (about line 190) reads `Regression | Yes | Not verified (no automated test asserts ...)`; the index states a `Not verified` row is Non-Blocking (checked).
- UNK-02 (maintainer may supply a test and keep the row Blocking) is open; this change is the default.
- Overlap: `adrrev017` removes amendment-history wording elsewhere in this ADR; the INV-02 row is a different region.

## Design decisions
- Flip the Blocking cell only; leave the invariant text and the `Not verified` explanation unchanged.

## Alternatives considered
N/A: the Plan fixes the approach for this row.

## Implementation
### Target file
`docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md`

### Procedure
1. Change the Blocking cell of the INV-02 row from `Yes` to `No`.
2. Append one `Current Decision Approval (pending)` line.

### Method
- Row after: `| Test that no external state-change path bypasses the Workflow Engine | INV-02 | Regression | No | Not verified (...) |`.
- Approval line: approver, date, scope 不明; tracked by adrrev012; mentions UNK-02.

### Details
- Each decision-text edit gets a clearly marked `Current Decision Approval (pending)` line in the ADR's Approval Record (approver, date, and scope `不明`), tracked by the approval-ledger Plan (adrrev012); none is written on a maintainer's behalf (UNK-04).
- A separate issue may add the test later (UNK-02); then the row can return to Blocking.

## Compatibility considerations
N/A: documentation-only change; no code, config, or schema impact.

## Security considerations
N/A: no authorization, secret, or trust-boundary change.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_adr_structure.py`, `check_adr_invariant_matrix.py`, `check_adr_preservation.py` (only the intended, explained changes).
- `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py --strict`, `check_docs_japanese.py` — pass.

## Completion criteria
- No ADR-001 table row is both Blocking and `Not verified`; a marked pending approval line exists.

## Out of Scope
- Adding an automated test for INV-02; the index (seq 08).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261112-171605 | 20261112-171605 | Changed: docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md (INV-02 row Blocking Yes -> No; only ADR-001 row that was Blocking and Not verified); pending approval line added without plan name, mentioning the maintainer's option to supply a test |
| 2 | Run the documentation checkers per Validation plan | Completed | 20261112-171605 | 20261112-171605 | ADR checkers, docs checkers pass; preservation reports only the Approval-section change (ERROR by design) |

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
- **Requirement ID**: `REQ-006` / `REQ-008` — no row both Blocking and `Not verified`; pending approval
- **Source issue**: issues/20261109-113220_adrrev015_adr-index-matrix.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261111-104147_adrrev015_adr-index-matrix.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261112-123307
- **Related target files**: `docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md`