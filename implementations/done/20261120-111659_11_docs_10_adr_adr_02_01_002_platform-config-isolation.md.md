## Goal

- Show the Blocking change of the two `Not verified` rows (INV-03, INV-04) as pending amendments (`REQ-009`, pending Blocking amendment).

## Scope
**Release unit**: pending-amendments

- Plan step 11 only, gated on UNK-02. The unit pairs this document with the `governance_03` ledger procedure (Plan step 10): a pending bullet without its ledger entry fails `tools/check_adr_structure.py`.
- Do not execute before the owner resolves UNK-02.

## Assumptions

- The rows are the ones now `Not verified (no automated test exists)` with `Blocking` `Yes` (INV-03, INV-04); read them from the table at execution time.
- The pending form is the governed one (`governance_01` "ADR Pending Amendment Form"); no approval text is written, and each bullet cites the ledger entry the `governance_03` procedure creates.

## Design decisions

- One pending bullet per changed invariant, citing its own ledger entry, as the ADR-014 bullet does for AAL-016.

## Alternatives considered

N/A: the Plan fixes the pending form.

## Implementation
### Target file
`docs/10_adr/adr_02_01_002_platform-config-isolation.md`
### Procedure
1. Change the `Blocking` cell of the INV-03 and INV-04 rows of `### Automated Tests` from `Yes` to `No`.
2. Under `## Approval` > `### Approval Record` add two `- **Current Decision Approval (pending)**:` bullets, each stating the changed row and citing its `AAL-NNN` entry; keep the Status `Accepted`.
### Method
- Direct edits following the existing pending bullets of other ADRs.
### Details
- Only these two cells and bullets change.

## Compatibility considerations

N/A: governed pending form; the decision change awaits the maintainer.

## Security considerations

- The bullets must not state or imply an approval; they record that approval is not recorded.

## Rollback considerations

N/A: revert the commit; the ledger procedure is reverted with it (release unit).

## Validation plan

- `uv run python tools/check_adr_invariant_matrix.py`, `uv run python tools/check_adr_structure.py`, `uv run python tools/check_adr_preservation.py`.
- `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py`, `uv run python tools/check_docs_content_policy.py`, `uv run python tools/check_docs_japanese.py`.

## Completion criteria

- No `Not verified` row of this ADR is `Blocking`, and each pending bullet cites an existing ledger entry (AC-5).

## Out of Scope

- Invariant text, the verification content, and any approval statement.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Show the INV-03 and INV-04 Blocking changes in the pending form (Plan step 11) | Completed | 20261120 | 20261120 | Gated: plans/20261120-095739_adrchk013_invariant-matrix-checks.md phase 11 - UNK-02 owner decision pending Owner resolved UNK-02 20261120: INV-03/INV-04 Blocking set to No; pending bullets cite AAL-031/032 |
| 2 | Run the documentation checkers named in `routing.md` Tools | Completed | — | 20261120 | All unit checkers exit 0; check_adr_preservation: 1 'Approval section text changed' ERROR = procedure-authorized pending bullets (UNK-02 approved) |

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
- **Requirement ID**: `REQ-009` (pending Blocking amendment, gated)
- **Source issue**: issues/20261117-123013_adrchk013_invariant-matrix-checks.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261120-095739_adrchk013_invariant-matrix-checks.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261120-111659
- **Related target files**: `docs/10_adr/adr_02_01_002_platform-config-isolation.md`