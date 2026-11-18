## Goal
Make ADR-003 describe startup behavior in one way and in ADR-004 terms (`REQ-005`), and show Decisions #15, #16, #17 as pending approval (`REQ-006`), without writing approval text.

## Scope
**Release unit**: N/A: not part of a release unit
- In scope: Decision Detail #15 wording, the Verification row, the Startup Validation bullet, `Fail-Fast Conditions` and `Fallback Policy`, `Data Ownership and Persistence`, and `### Approval Record`.

## Assumptions
- Procedure 01 has landed: AAL-021, AAL-022, AAL-023 exist in `governance_03` Part 5 (ledger ids must exist before the bullets cite them).
- No ADR in `docs/10_adr/` has a Fail-Closed subsection, so the classification is stated in `Fallback Policy` (UNK-02 resolved).
- The Decision #15 severity correction is treated as an amendment and gets a pending bullet (UNK-04); the maintainer may withdraw it.
- The current file is 27196 bytes; the limit is 32768.

## Design decisions
- Decision #15: replace "warns after the fact about the validity of" with wording that startup aborts when Drift is detected (ADR-004 INV-02) while the check still does not change Routing; keep the rest of the sentence.
- Pending bullets use the form of ADR-004: `- **Current Decision Approval (pending)**: ... awaits maintainer approval; it is tracked by AAL-0NN.`

## Alternatives considered
- Adding a `Fail-Closed Conditions` heading: rejected, no ADR has one and the structure checker's heading list does not include it.

## Implementation
### Target file
`docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md`

### Procedure
1. Decision Detail #15: severity wording as in Design decisions.
2. `Verification > Startup Validation`: change the Security Posture bullet to say a posture failure aborts startup through `check_readiness()` regardless of the server's `required` value (as Decision Detail #16 and ADR-004 state); keep the Discovery bullet.
3. `Verification > Automated Tests`, Drift row: keep "startup is aborted on drift" (already the chosen severity).
4. `Failure Policy > Fail-Fast Conditions`: remove "An unregistered Tool is requested for Routing"; in `Fallback Policy` add that an unregistered Tool is rejected at runtime (Fail-Closed, ADR-004 Decision Group 5 item 15; `ToolRouteResolver.resolve()` raises `ValueError`, INV-02).
5. `Data Ownership and Persistence`: replace `**Derived Data**: ToolRegistry (for tests and documentation generation)` with a static-reference-data statement: `ToolRegistry` is populated from the tool constants, is not derived from `RuntimeToolRegistry`, and serves tests, documentation generation, and startup Drift validation.
6. `### Approval Record`: after the existing records add three pending bullets, one each for Decision Detail #15 (severity correction, AAL-021), #16 (AAL-022), #17 (AAL-023), in the ADR-004 form; write no `Approved By` or `Approval Date`.

### Method
- Match the existing bullet style and the English wording used in ADR-004's pending bullets.
- Do not edit generated or guarded blocks.

### Details
- Run `uv run python tools/check_adr_structure.py` after step 6: it requires every pending bullet to cite an existing ledger id.

## Compatibility considerations
- Text-only; no Decision's behavior changes beyond making the stated severity match the code.

## Security considerations
- No approval statement is written or simulated (AGENTS.md and governance_01/05).

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_adr_structure.py`, `tools/check_adr_preservation.py`, `tools/check_adr_invariant_matrix.py`, `tools/check_docs_structure.py`, and the other checkers `routing.md` Tools lists for a `docs/` edit.

## Completion criteria
- Decision Detail #15, the Verification text, and the Startup Validation bullets use one severity; the unregistered-tool condition is not under Fail-Fast; `ToolRegistry` is not called Derived Data; three pending bullets cite existing ids; all checkers pass.

## Out of Scope
- Approval text, ADR-004 wording, `governance_03` (procedure 01).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Apply the wording and approval-record edits (Implementation > Procedure) | Pending | — | — | |
| 2 | Run the ADR and documentation checkers (Validation plan) | Pending | — | — | |

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
- **Requirement ID**: REQ-005, REQ-006
- **Source issue**: issues/20261117-123005_adrchk005_startup-fail-closed.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261118-134945_adrchk005_startup-fail-closed.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261118-135645
- **Related target files**: `docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md`
