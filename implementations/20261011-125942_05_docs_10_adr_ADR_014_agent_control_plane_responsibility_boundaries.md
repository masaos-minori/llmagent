# Implementation Procedure: docs/10_adr/ADR-014-agent-control-plane-responsibility-boundaries.md

## Goal

Update the INV-02 verification status in ADR-014 to reflect that the INV-02 regression test has been added.

## Scope

- `docs/10_adr/ADR-014-agent-control-plane-responsibility-boundaries.md`: Update INV-02 verification status.

## Assumptions

- ADR-014 INV-02 verification section currently states "no such test exists" (line 165).
- AGENT-002 is tracked as a Known Deviation in ADR-014 (line 199).
- The INV-02 regression test will be added as part of REQ-001.

## Design decisions

- Update the Automated Tests section to reflect that the INV-02 regression test now exists.
- Update the Known Deviations section to remove AGENT-002.
- Update the Completion Checklist to mark the INV-02 automation item as done.

## Alternatives considered

1. Leave the INV-02 verification status as-is since it already documents the gap — rejected because the gap is being closed by REQ-001.
2. Rewrite the entire Verification section — rejected because only specific items need updating.

## Implementation

### Target file

`docs/10_adr/ADR-014-agent-control-plane-responsibility-boundaries.md`

### Procedure

1. Review the INV-02 verification section in ADR-014.
2. Update the Automated Tests section to reflect the new regression test.
3. Remove AGENT-002 from Known Deviations.
4. Update the Completion Checklist to mark INV-02 automation as done.

### Method

Documentation modification — update the INV-02 verification status in ADR-014.

### Details

1. **Update INV-02 verification status (REQ-004)**:
   - Current code (line 165): "A regression test that Orchestrator does not hold an unused LlmTurnExecutor instance (no such test exists)"
   - Update to reflect that the regression test now exists (added as part of REQ-001).
   - Current code (line 199): "Known Issue: AGENT-002 — tracked in governance_03 Part 1 (no regression test for INV-02)"
   - Remove this Known Deviation entry since the regression test is being added.
   - Current code (line 253): "Automatable verification does not rely only on Manual Review (INV-01 and INV-03 rely only on Manual Review; INV-02 has no test yet)"
   - Update to reflect that INV-02 now has a test.

## Compatibility considerations

- Updating ADR-014 is a documentation-only change with no runtime impact.
- The INV-02 verification status update should be consistent with the governance_03 update (REQ-004).

## Security considerations

N/A — this is a documentation update, not a security boundary change.

## Rollback considerations

- Reverting the ADR-014 changes restores the previous INV-02 verification status.
- No production code change — rollback is safe (revert the documentation changes).

## Validation plan

| Target | Strategy | Tool / Command | Expected Outcome |
|--------|----------|----------------|------------------|
| ADR-014 | Documentation review: verify INV-02 verification status updated | Manual | INV-02 status updated |

## Completion criteria

- [ ] INV-02 verification status updated to reflect new regression test (REQ-004).
- [ ] AGENT-002 removed from Known Deviations.
- [ ] Documentation review confirms accuracy.

## Out of scope

- Changes to INV-01 or INV-03 verification status.
- Changes to other ADRs.
- Changes to the ADR structure or template.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | N/A | — | — | No test changes needed (documentation-only) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A | — | — | No docs/00_index.md mapping for this file |

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
- **Requirement ID**: REQ-004
- **Source issue**: `issues/20261007-154050_regtest01_add-inv-02-regression-test-and-keep-original-japanese-text-on-empty-normalization.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261008-164920_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261011-125942
- **Related target files**: `docs/10_adr/ADR-014-agent-control-plane-responsibility-boundaries.md`
