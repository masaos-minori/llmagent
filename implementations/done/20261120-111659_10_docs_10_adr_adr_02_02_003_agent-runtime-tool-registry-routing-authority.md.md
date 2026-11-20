## Goal

- Add the manual review that covers the Safety Tier part of ADR-003 INV-03, so the Index can record INV-03 as `Partial` (`REQ-003`, rows mirror the bodies).
- Gated: show the Blocking changes of the `Not verified` rows (INV-03 Safety Tier row, INV-04, INV-07) as pending amendments (`REQ-009`).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: `### Manual Review` (Plan step 3) and, gated, three table cells and pending bullets under `### Approval Record` (Plan step 11, UNK-02).
- Execute step 1 before the Index procedure; step 2 only after the owner resolves UNK-02. Step 2 belongs to the Plan's `pending-amendments` release unit together with the ledger procedure.

## Assumptions

- The manual review is verification text, not decision text, so it needs no approval record (Plan Assumption A4).
- The three `Not verified` rows are the ones with `Blocking` `Yes` in the table: INV-04 (no Fallback to the static ToolRegistry), INV-03 (Routing, approval and auditing reference the same Safety Tier), INV-07 (Circuit-Open server Tools stay visible); read from the table at execution time, not from this list.

## Design decisions

- The new Manual Review bullet names INV-03 and the reviewed code paths (Registry and approval code paths), in the style of the existing INV-05, INV-08 and INV-09 bullet.

## Alternatives considered

N/A: the Plan fixes the approach.

## Implementation
### Target file
`docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md`
### Procedure
1. Add to `### Manual Review` a bullet stating that the Safety Tier reference part of INV-03 has no dedicated automated test and is verified by review of the Registry, approval and audit code paths; keep the cadence and expected evidence the Index row will quote (the Index row carries `Cadence:`, `Expected evidence:` and `Owner:`).
2. (Gated on UNK-02) For each `Not verified` row with `Blocking` `Yes`, change the `Blocking` cell to `No` and add one `- **Current Decision Approval (pending)**:` bullet under `### Approval Record` per change, each citing its `AAL-NNN` entry, following the existing bullets.
### Method
- Direct edits; the pending bullets follow `governance_01` "ADR Pending Amendment Form".
### Details
- Do not change the other rows, the invariant text or the ADR Status.

## Compatibility considerations

N/A: step 1 adds verification text only; step 2 uses the governed pending form.

## Security considerations

- Step 2 must not state or imply an approval; the bullets record that approval is not recorded.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run python tools/check_adr_invariant_matrix.py`, `uv run python tools/check_adr_structure.py`, `uv run python tools/check_adr_preservation.py`.
- `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py`, `uv run python tools/check_docs_content_policy.py`, `uv run python tools/check_docs_japanese.py`.

## Completion criteria

- `### Manual Review` covers INV-03's Safety Tier part, and `uv run python tools/check_adr_invariant_matrix.py` exits 0 (AC-1).
- Gated: no `Not verified` row of this ADR is `Blocking`, and each pending bullet cites an existing ledger entry (AC-5).

## Out of Scope

- Invariant text and decisions, and any approval statement.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the INV-03 Safety Tier manual review (Plan step 3) | Completed | 20261120 | 20261120 | Manual Review bullet added naming the INV-03 Safety Tier part |
| 2 | Show the Blocking changes in the pending form (Plan step 11) | Completed | — | 20261120 | Gated: plans/20261120-095739_adrchk013_invariant-matrix-checks.md phase 11 - UNK-02 owner decision pending Owner resolved UNK-02 20261120: INV-03/INV-04/INV-07 Blocking set to No; 3 pending bullets cite AAL-033/034/035 |
| 3 | Run the documentation checkers named in `routing.md` Tools | Completed | — | 20261120 | All unit checkers exit 0; check_adr_preservation: 1 'Approval section text changed' ERROR = procedure-authorized pending bullets (UNK-02 approved) |

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
- **Requirement ID**: `REQ-003` (manual review for the Partial row), `REQ-009` (pending Blocking amendments, gated)
- **Source issue**: issues/20261117-123013_adrchk013_invariant-matrix-checks.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261120-095739_adrchk013_invariant-matrix-checks.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261120-111659
- **Related target files**: `docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md`