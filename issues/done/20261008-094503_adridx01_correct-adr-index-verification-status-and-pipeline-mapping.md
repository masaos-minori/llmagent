# Correct adr-index verification status and pipeline mapping

## Priority
High

## Summary
Fix adr-index so the Invariant Verification Matrix and Pipeline Mapping Summary agree with registered Known Issues, add the missing circular references and the ADR-012 to ADR-007 dependency edge, and explain the ADR-011 gap.

## Background
Source: local investigation notes (memo2.md, adr-index section; review findings H05, G10). Overlaps in part with the existing kiledger01 issue, which also asks to remove false "Confirmed" rows.

## Problem
- Verification Status is "Confirmed" for invariants that have open Known Issues.
- Pipeline Mapping Summary disagrees with the Matrix.
- ADR-002 is described as covering "environments" (should be processes).
- The intentional circular references list is incomplete.
- Nothing explains why ADR-011 is missing.

## Reason for Change
A wrong "Confirmed" status is especially risky because security decisions rely on it.

## Implementation Intent
- Apply the ADR-011 note, the revised Intentional Circular References, the ADR-012 to ADR-007 edge, the replaced Matrix rows, and the revised Pipeline Mapping Summary from memo2.md.
- Correct the ADR-002 description.

## Target Files or Areas
- `docs/10_adr/adr-index.md`

## Required Changes
- Apply every adr-index change listed in memo2.md.
- Update the ADR-004 Decision numbering references in adr-index (see the adr004fix issue).

## Constraints
- Each "Partial" or "Not verified" row must cite a registered Known Issue ID.
- Test paths cited must exist.

## Acceptance Criteria
- adr-index has no "Confirmed" row contradicting a registered Known Issue.
- Matrix and Pipeline Mapping Summary agree.
- Doc checkers pass.

## Testing Expectations
Run the doc checkers listed in `routing.md` (ADR structure, Known Deviation sync). Confirm cited test files exist.

## Documentation Impact
Documentation only: adr-index.

## Out of Scope
- Editing the individual ADRs.

## Dependencies
- Depends on the kiupd01 issue (MCP-005 must be registered).
- Overlaps with `issues/20261007-154111_kiledger01_align-known-issue-ledger-adr-known-deviations-adr-index.md`; coordinate so each row is changed once.

## Unresolved Questions
- N/A: none recorded in memo2.md.

## AI Implementation Instruction
Edit only adr-index. Verify that each cited test and Known Issue exists before writing the row. Run the doc checkers before finishing.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261008-094503
- **Related target files**: `docs/10_adr/adr-index.md`
