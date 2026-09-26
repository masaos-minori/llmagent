# Implementation Procedure: Promote GV-021 check to default-on

## Goal

Promote the GV-021 documentation check to default-on after corpus compliance, as tracked in `docs/00_governance/governance_04_documentation-checks.md`.

## Scope

- Update GV-021 row in `governance_04_documentation-checks.md` to promote the check to default-on
- Verify GV-021 status is already "Existing" before promotion

## Assumptions

- All default-value restatement violations identified by `check_docs_content_policy.py` have been remediated
- The corpus is now compliant with the docs content policy
- GV-021 status is already "Existing" with "None" for follow-up work needed (confirmed by repository evidence)

## Design decisions

- Update the GV-021 row's Follow-up column from "None" to reflect the promotion action
- Keep the check as "Auto" since it remains automated via `check_docs_content_policy.py`

## Alternatives considered

- **Keep GV-021 as-is**: Would leave the check in its current state without promoting it to default-on
- **Add additional checks before promotion**: Would delay the promotion unnecessarily
- **Create a new governance item for the promotion**: Unnecessary complexity for a simple status update

## Implementation

### Target file

`docs/00_governance/governance_04_documentation-checks.md`

### Procedure

1. Locate the GV-021 row in the Governance Verification Matrix table
2. Verify the current status is "Existing" with "None" for follow-up work needed
3. Update the Follow-up column to reflect the promotion to default-on
4. Verify the resulting document still accurately describes the check status

### Method

**GV-021 row**: Currently shows:
```
| GV-021 | Docs content policy violation (implementation detail in docs/*.md) | Chk | Auto | `check_docs_content_policy.py` | PR | Warning | Existing | None |
```

Update the Follow-up column from "None" to indicate the promotion action:

```markdown
| GV-021 | Docs content policy violation (implementation detail in docs/*.md) | Chk | Auto | `check_docs_content_policy.py` | PR | Warning | Existing | Promoted to default-on after corpus compliance |
```

### Details

The key change is updating the Follow-up column to reflect that the check has been promoted to default-on. This indicates that the corpus is now compliant and the check can be enabled by default.

## Compatibility considerations

- The GV-021 entry remains semantically accurate after the promotion
- No downstream dependencies on the specific Follow-up phrasing
- The check itself remains unchanged — only the status tracking is updated

## Security considerations

- No security impact; this is a documentation status update

## Rollback considerations

- If the promotion was premature, revert the Follow-up column to "None" and investigate remaining violations

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| docs/00_governance/governance_04_documentation-checks.md | Manual: verify GV-021 row shows "Existing" with promotion note | Manual review of governance doc | Status = "Existing", Follow-up = "Promoted to default-on after corpus compliance" |

## Completion criteria

- GV-021 row's Follow-up column reflects the promotion to default-on
- The GV-021 status remains "Existing" (no change required)
- The document accurately describes the check's current state

## Out of scope

- Modifying the `check_docs_content_policy.py` tool itself
- Running the corpus scan again (assumes prior remediation completed)
- Modifying other governance items that may have similar issues

## Execution Status

### Execution Status

| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: REQ-008
- **Source issue**: issues/20260926-071110_default-value-restatement-violations-in-docs.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260926-085903_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260926-095333
- **Related target files**: docs/00_governance/governance_04_documentation-checks.md
