## Goal

Update the governance documentation to reflect the new requirements introduced by this change set — specifically, documenting the immutable discovery-time visibility field, the atomic registry swap invariant, and the preflight gate additions. (REQ-001 through REQ-005; "Document the new requirements in `docs/00_governance_03_issue-and-uncertainty-management.md`")

## Scope

- Add Known Issues entries for the new requirements if they introduce new discrepancies between documentation and implementation.
- Update existing Known Issues entries if they reference the old behavior.
- Ensure the governance documentation accurately reflects the new architectural decisions.

## Assumptions

- The `llm_visibility_base` field exists on `RuntimeTool` (covered by a separate document — this row depends on its completion).
- The `apply_policy()` formula has been rewritten to use the immutable base field (covered by a separate document — this row depends on its completion).
- The `check_preflight()` calls have been added to `_cmd_diff()` and `_execute_mdq()` (covered by separate documents — this row depends on their completion).

## Design decisions

- **Known Issue creation**: Create new Known Issues entries for any new discrepancies introduced by the change set.
- **Existing entry updates**: Update existing Known Issues entries if they reference the old behavior.
- **No source document modification**: Per governance policy, do not modify source documents during extraction — this document is read-only relative to sources.

## Alternatives considered

- **Adding a new section to the governance document**: Rejected — the existing Known Issues structure is sufficient for tracking new discrepancies.
- **Creating a separate governance document**: Rejected — consolidating into the existing document maintains consistency.

## Implementation

### Target file

`docs/00_governance_03_issue-and-uncertainty-management.md`

### Procedure

1. Review existing Known Issues entries for references to the old behavior.
2. Create new Known Issues entries for any new discrepancies introduced by the change set.
3. Update existing entries if they reference the old behavior.

### Method

Add entries to the Active Items section of the Known Issues part. No new imports or dependencies.

### Details

**Step 1: Review existing entries**

Review the existing Known Issues entries in `docs/00_governance_03_issue-and-uncertainty-management.md` for references to the old behavior:
- CI-003: References the old `requires_approval` removal — update to reflect the new `llm_visibility_base` field.
- CI-010: References the old routing authority — verify it still applies.

**Step 2: Create new Known Issues entries**

Create new Known Issues entries for any new discrepancies introduced by the change set:
- New entry for the immutable base field requirement.
- New entry for the atomic swap invariant.
- New entry for the preflight gate additions.

**Step 3: Update existing entries**

Update existing entries if they reference the old behavior:
- CI-003: Update to reflect the new `llm_visibility_base` field.

## Compatibility considerations

- **No signature change**: The governance document follows the existing structure.
- **Entry format**: Uses the existing 16-field template for Known Issues entries.

## Security considerations

This documentation update validates a security property: that tools hidden from the LLM are correctly denied during direct execution via the `/diff` command, preventing unauthorized access to restricted tools.

## Rollback considerations

If the documentation update fails due to incorrect assumptions about the governance process, revert to the previous documentation state and adjust accordingly.

## Validation plan

- Review the updated governance document: `cat docs/00_governance_03_issue-and-uncertainty-management.md`
- Verify all entries follow the existing format.
- Verify all entries are accurate and up-to-date.

## Completion criteria

- All Known Issues entries are accurate and up-to-date.
- All new entries follow the existing format.
- All existing entries are updated to reflect the new behavior.

## Out of scope

- Tests for the disable-then-re-enable sequence in `apply_policy()` (covered by a separate document).
- Tests for the `/diff` bypass (covered by a separate document).
- Tests for the MDQ bypass (covered by a separate document).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Review existing entries | Pending | — | — | |
| 2 | Create new entries | Pending | — | — | |
| 3 | Update existing entries | Pending | — | — | |
| 4 | Validate all entries | Pending | — | — | |

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
- **Requirement ID**: REQ-001 through REQ-005
- **Source issue**: issues/20260914-103138_mcpagent04_runtime-policy-reload-reversibility.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260916-122227_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260916-202817
- **Related target files**: docs/00_governance_03_issue-and-uncertainty-management.md
