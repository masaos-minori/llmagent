## Goal

Update `GV-008` in `docs/00_governance_04_documentation-checks.md`'s Governance Verification Matrix: broaden its Rule description from "Known Issue required fields" to cover the full vocabulary/template/referential-integrity scope this Plan implements, change `Tool/Review` from `check_docs_quality.py` to `check_issue_inventory_conformance.py`, change `Status` from `Missing` to `Existing`, and update its Follow-up Work Needed list entry accordingly — do not add a second, overlapping Rule ID.

## Scope

- Update the GV-008 row in the Governance Verification Matrix table.
- Update the corresponding Follow-up Work Needed item in the Follow-up Work Needed section.
- Do not add a second Rule ID — reconcile with the pre-existing GV-008 slot to avoid duplicate-tracking-slot problems.

## Assumptions

- GV-008 currently reads approximately as recorded in Repository Evidence:
  ```markdown
  | GV-008 | Known Issue required fields | Iss | Auto | check_docs_quality.py | PR | Blocking | Missing | Implement |
  ```
- The Follow-up Work Needed item 5 reads approximately as recorded in Repository Evidence.
- The source issue's intent is to update GV-008 in place rather than adding a new Rule ID.

## Design decisions

- Broaden the Rule description to reflect the full scope: vocabulary conformance, template field-count, orphaned bullets, closing-summary consistency, and referential integrity.
- Change the tool reference from `check_docs_quality.py` to `check_issue_inventory_conformance.py`.
- Change status from `Missing` to `Existing` since the checker will exist after implementation.
- Update the Follow-up Work Needed item to reflect the completed work.

## Alternatives considered

- Adding a new Rule ID (e.g., GV-013) — rejected because the Plan's intent is to update GV-008 in place to avoid duplicate-tracking-slot problems, consistent with GV-011/GV-012's anti-duplication principle.

## Implementation
### Target file

`docs/00_governance_04_documentation-checks.md`

### Procedure

1. Locate the GV-008 row in the Governance Verification Matrix table (approximately line 318 based on Reference Files evidence).
2. Update the following columns in the GV-008 row:
   - Rule: Change from "Known Issue required fields" to "Issue inventory conformance: vocabulary, template, referential integrity"
   - Tool/Review: Change from "check_docs_quality.py" to "check_issue_inventory_conformance.py"
   - Status: Change from "Missing" to "Existing"
   - Follow-up Work Needed: Update the item to reflect the completed work
3. Locate the corresponding Follow-up Work Needed item (item 5, approximately line 341 based on Reference Files evidence).
4. Update the item text to reflect that GV-008 has been broadened to cover the full conformance scope.

### Method

Current state: GV-008 row reads approximately:
```markdown
| GV-008 | Known Issue required fields | Iss | Auto | check_docs_quality.py | PR | Blocking | Missing | Implement |
```

Required replacement:
```markdown
| GV-008 | Issue inventory conformance: vocabulary, template, referential integrity | Iss | Auto | check_issue_inventory_conformance.py | PR | Blocking | Existing | Implement |
```

The exact column values may vary slightly depending on the current table structure — verify against the live document at implementation time.

### Details

The updated GV-008 row should use the same column alignment as existing rows. The Follow-up Work Needed item should be updated to reflect that the checker now covers the full conformance scope rather than just "Known Issue required fields."

## Compatibility considerations

- This is a documentation-only change — no code compatibility impact.
- The updated GV-008 row cross-references the new conformance checker — proper ownership routing via the Governance Verification Matrix.

## Security considerations

- No security impact — documentation-only change.

## Rollback considerations

- If the GV-008 update is found to duplicate an existing convention, simply revert it. No behavioral rollback needed since there is none.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `docs/00_governance_04_documentation-checks.md` | Documentation structural check | `uv run python tools/check_docs_quality.py docs/00_governance_04_documentation-checks.md` | Passes with no new findings |

## Completion criteria

- GV-008's Rule description reflects the full conformance scope (vocabulary, template, referential integrity).
- GV-008's Tool/Review references `check_issue_inventory_conformance.py`.
- GV-008's Status is `Existing`.
- The Follow-up Work Needed item is updated to reflect the completed work.
- `uv run python tools/check_docs_quality.py docs/00_governance_04_documentation-checks.md` passes clean.

## Out of scope

- Fixing the vocabulary violations themselves — tracked by the single-status-vocabulary Plan (`plans/20260916-150416_plan.md`).
- Adding a second Rule ID — reconciled with GV-008 in place.
- Reviewing other Governance Verification Matrix entries.

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
- **Requirement ID**: REQ-004
- **Source issue**: issues/20260915-200449_gov03_add-conformance-and-referential-integrity-checks-for-the-issue-inventory.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260916-151710_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260916-151710
- **Related target files**: docs/00_governance_04_documentation-checks.md
