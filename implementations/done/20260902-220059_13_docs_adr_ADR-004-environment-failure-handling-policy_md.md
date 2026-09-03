## Goal

Update ADR-004 to reflect the new strict-default behavior and its alignment with Fail-Fast requirements.

## Scope

Modify `docs/adr/ADR-004-environment-failure-handling-policy.md` only. Update the document to reference REQ-001's fix and its alignment with INV-01/INV-02's Fail-Fast requirements.

## Assumptions

- REQ-001's fix (making `load_all()` strict by default) is applied first.
- The existing ADR-004 structure supports adding a new section referencing the fix.
- ADR-004 currently covers environment failure handling policy but does not mention the strict-default behavior.

## Design decisions

- Add a new "Alignment with INV-01/INV-02" section to ADR-004 that references the strict-default change.
- Keep the existing content intact; only append new information.

## Alternatives considered

- Creating a new ADR. Rejected because this is an update to an existing ADR, not a new architectural decision.
- Modifying existing sections. Rejected because it risks altering the original intent of the ADR.

## Implementation

### Target file

`docs/adr/ADR-004-environment-failure-handling-policy.md`

### Procedure

Add a new section to ADR-004 documenting the alignment of REQ-001's strict-default change with INV-01/INV-02's Fail-Fast requirements.

### Method

1. After applying REQ-001's fix, read `docs/adr/ADR-004-environment-failure-handling-policy.md` to find the appropriate location for the new section.
2. Add a new section titled "Alignment with INV-01/INV-02" after the existing sections.

### Details

1. Read `docs/adr/ADR-004-environment-failure-handling-policy.md` around lines 50-100 to find the end of the existing sections.
2. Add the following section:

```markdown
## Alignment with INV-01/INV-02

With REQ-001's fix (strict-default behavior), the Fail-Fast requirements of INV-01/INV-02 are now enforced at startup time. Specifically:

1. **INV-01**: Missing required config files cause immediate process termination (no silent-continue).
2. **INV-02**: All processes enforce fail-closed behavior regardless of environment.
3. **No environment-based relaxation**: The strict-default applies uniformly across all environments.
```

## Compatibility considerations

- Existing ADR content remains unchanged. New section adds context without altering original intent.

## Security considerations

- This documentation update reinforces the security-relevant aspects of ADR-004's Fail-Fast requirements.

## Rollback considerations

- Remove the new section if REQ-001 is rolled back. No other rollback needed.

## Validation plan

Review the updated ADR-004 to ensure the new section accurately reflects the strict-default behavior and its alignment with INV-01/INV-02's Fail-Fast requirements.

## Completion criteria

- New "Alignment with INV-01/INV-02" section added to ADR-004
- Section accurately describes the strict-default's alignment with Fail-Fast requirements
- Existing ADR content remains intact

## Out of scope

- Changes to other ADRs (handled by their respective documents)
- Unknown-key rejection documentation (REQ-004, handled separately)

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | — | Added "Alignment with INV-01/INV-02" section to ADR-004 |
| 2 | Add or update tests per Validation plan | N/A | — | — | Documentation task; no tests needed |
| 3 | Run the validation sequence (`rules/toolchain.md`) | N/A | — | — | No code changes; manual review sufficient |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | — | Section added to ADR-004 |

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
- **Requirement ID**: REQ-001
- **Source issue**: issues/20260902-101452_h02_config_loader_fail_closed_gap.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260902-191443_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260902-220059
- **Related target files**: docs/adr/ADR-004-environment-failure-handling-policy.md
